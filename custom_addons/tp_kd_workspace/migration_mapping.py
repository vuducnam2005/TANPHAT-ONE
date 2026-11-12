"""Operator-only explicit-ID mapping. Call inside one ORM transaction; persist journal after commit."""

from odoo.exceptions import AccessError, UserError
from odoo.tools import SQL


def apply_mapping(env, rows, *, dry_run=True, journal=None):
    if not env.su:
        raise AccessError(
            env._("Explicit mapping requires the controlled operator environment."),
        )
    journal = journal if journal is not None else []
    result = []
    for row in rows:
        if (
            set(row) != {"lead_id", "project_id", "package_id", "source", "verified_by"}
            or not row["source"]
            or not row["verified_by"]
        ):
            raise UserError(
                env._(
                    "Mapping needs explicit IDs, evidence and verifier; names are not keys.",
                ),
            )
        lead = env["crm.lead"].browse(row["lead_id"]).exists()
        project = env["project.project"].browse(row["project_id"]).exists()
        package = env["tp.bid.package"].browse(row["package_id"]).exists()
        if (
            not lead
            or not project
            or not project.tp_managed
            or (row["package_id"] and not package)
            or (package and (package.project_id != project or lead.kd_route != "bid"))
        ):
            raise UserError(
                env._(
                    "Mapping requires an existing dossier, managed project and any supplied package in that project.",
                ),
            )
        if (
            not lead.partner_id
            or lead.company_id != project.company_id
            or (
                lead.partner_id.commercial_partner_id
                != project.partner_id.commercial_partner_id
            )
        ):
            raise UserError(
                env._(
                    "Mapping needs a verified commercial counterparty and must retain company semantics.",
                ),
            )
        if (lead.tp_project_id and lead.tp_project_id != project) or (
            lead.kd_package_id and lead.kd_package_id != package
        ):
            raise UserError(
                env._("Additive mapping cannot replace an existing explicit link."),
            )
        before = {
            "tp_project_id": lead.tp_project_id.id,
            "kd_package_id": lead.kd_package_id.id,
        }
        after = {"tp_project_id": project.id, "kd_package_id": package.id}
        delta = {key: value for key, value in after.items() if before[key] != value}
        result.append(
            {
                "lead_id": lead.id,
                "delta": delta,
                "source": row["source"],
                "verified_by": row["verified_by"],
            },
        )
        if delta and not dry_run:
            env.cr.execute(
                SQL("SELECT id FROM crm_lead WHERE id=%s FOR UPDATE", lead.id),
            )
            lead.invalidate_recordset()
            if any(lead[key].id != value for key, value in before.items()):
                raise UserError(env._("Mapping changed concurrently; re-run dry-run."))
            lead.with_context(tracking_disable=True, mail_notrack=True).write(delta)
            journal.append(
                {
                    "model": "crm.lead",
                    "id": lead.id,
                    "before": {key: before[key] for key in delta},
                    "after": delta,
                    "source": row["source"],
                    "verified_by": row["verified_by"],
                },
            )
    return result


def rollback_mapping(env, journal):
    if not env.su:
        raise AccessError(
            env._("Mapping rollback requires the controlled operator environment."),
        )
    for entry in reversed(journal):
        if entry["model"] != "crm.lead" or set(entry["before"]) - {
            "tp_project_id",
            "kd_package_id",
        }:
            raise UserError(env._("Unsupported journal entry."))
        lead = env["crm.lead"].browse(entry["id"]).exists()
        env.cr.execute(SQL("SELECT id FROM crm_lead WHERE id=%s FOR UPDATE", lead.id))
        lead.invalidate_recordset()
        current = {key: lead[key].id for key in entry["after"]}
        if current == entry["before"]:
            continue
        if current != entry["after"]:
            raise UserError(
                env._("Rollback refused: mapped fields changed after apply."),
            )
        lead.with_context(tracking_disable=True, mail_notrack=True).write(
            entry["before"],
        )
