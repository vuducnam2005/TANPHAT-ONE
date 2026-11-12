from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import UserError

from .workspace import open_records

SOURCES = {
    "allocation": ("tp.allocation", "Giao khoán"),
    "production": ("tp.production", "Sản lượng tự khai"),
    "acceptance": ("tp.acceptance", "Hồ sơ nghiệm thu nội bộ"),
    "payment": ("tp.payment.request", "Đề nghị thanh toán"),
    "plan": ("tp.periodic.plan", "Kế hoạch định kỳ"),
    "credential": ("tp.credential", "Năng lực / chứng chỉ"),
    "obligation": ("tp.obligation", "Nghĩa vụ / hồ sơ thiếu"),
    "opportunity": ("crm.lead", "Hồ sơ dự án / hồ sơ thầu"),
    "task": ("project.task", "Công việc / WBS"),
    "contract": ("tp.contract.revision", "Phiên bản hợp đồng"),
}
QUERIES = (
    "all",
    "review",
    "returned",
    "overdue",
    "due",
    "expiring",
    "draft",
    "effective",
)


class Overview(models.TransientModel):
    _inherit = "tp.kd.overview"
    allocation_all_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="allocation all",
    )
    allocation_review_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="allocation review",
    )
    allocation_returned_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="allocation returned",
    )
    allocation_overdue_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="allocation overdue",
    )
    allocation_due_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="allocation due",
    )
    allocation_expiring_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="allocation expiring",
    )
    allocation_draft_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="allocation draft",
    )
    allocation_effective_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="allocation effective",
    )
    production_all_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="production all",
    )
    production_review_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="production review",
    )
    production_returned_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="production returned",
    )
    production_overdue_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="production overdue",
    )
    production_due_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="production due",
    )
    production_expiring_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="production expiring",
    )
    production_draft_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="production draft",
    )
    production_effective_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="production effective",
    )
    acceptance_all_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="acceptance all",
    )
    acceptance_review_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="acceptance review",
    )
    acceptance_returned_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="acceptance returned",
    )
    acceptance_overdue_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="acceptance overdue",
    )
    acceptance_due_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="acceptance due",
    )
    acceptance_expiring_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="acceptance expiring",
    )
    acceptance_draft_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="acceptance draft",
    )
    acceptance_effective_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="acceptance effective",
    )
    payment_all_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="payment all",
    )
    payment_review_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="payment review",
    )
    payment_returned_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="payment returned",
    )
    payment_overdue_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="payment overdue",
    )
    payment_due_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="payment due",
    )
    payment_expiring_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="payment expiring",
    )
    payment_draft_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="payment draft",
    )
    payment_effective_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="payment effective",
    )
    plan_all_count = fields.Integer(compute="_compute_inbox_counts", string="plan all")
    plan_review_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="plan review",
    )
    plan_returned_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="plan returned",
    )
    plan_overdue_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="plan overdue",
    )
    plan_due_count = fields.Integer(compute="_compute_inbox_counts", string="plan due")
    plan_expiring_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="plan expiring",
    )
    plan_draft_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="plan draft",
    )
    plan_effective_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="plan effective",
    )
    credential_all_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="credential all",
    )
    credential_review_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="credential review",
    )
    credential_returned_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="credential returned",
    )
    credential_overdue_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="credential overdue",
    )
    credential_due_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="credential due",
    )
    credential_expiring_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="credential expiring",
    )
    credential_draft_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="credential draft",
    )
    credential_effective_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="credential effective",
    )
    obligation_all_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="obligation all",
    )
    obligation_review_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="obligation review",
    )
    obligation_returned_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="obligation returned",
    )
    obligation_overdue_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="obligation overdue",
    )
    obligation_due_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="obligation due",
    )
    obligation_expiring_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="obligation expiring",
    )
    obligation_draft_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="obligation draft",
    )
    obligation_effective_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="obligation effective",
    )
    opportunity_all_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="opportunity all",
    )
    opportunity_review_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="opportunity review",
    )
    opportunity_returned_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="opportunity returned",
    )
    opportunity_overdue_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="opportunity overdue",
    )
    opportunity_due_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="opportunity due",
    )
    opportunity_expiring_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="opportunity expiring",
    )
    opportunity_draft_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="opportunity draft",
    )
    opportunity_effective_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="opportunity effective",
    )
    task_all_count = fields.Integer(compute="_compute_inbox_counts", string="task all")
    task_review_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="task review",
    )
    task_returned_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="task returned",
    )
    task_overdue_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="task overdue",
    )
    task_due_count = fields.Integer(compute="_compute_inbox_counts", string="task due")
    task_expiring_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="task expiring",
    )
    task_draft_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="task draft",
    )
    task_effective_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="task effective",
    )
    contract_all_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="contract all",
    )
    contract_review_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="contract review",
    )
    contract_returned_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="contract returned",
    )
    contract_overdue_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="contract overdue",
    )
    contract_due_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="contract due",
    )
    contract_expiring_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="contract expiring",
    )
    contract_draft_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="contract draft",
    )
    contract_effective_count = fields.Integer(
        compute="_compute_inbox_counts",
        string="contract effective",
    )

    def _inbox_domain(self, model, query="all"):
        self.ensure_one()
        if model not in {item[0] for item in SOURCES.values()} or query not in QUERIES:
            raise UserError(self.env._("Nguồn hoặc bộ lọc không hợp lệ."))
        if model == "crm.lead":
            domain = self._domain(model, "tp_project_id", "user_id", "kd_deadline")
            state, owner, deadline = "kd_bid_state", "user_id", "kd_deadline"
        elif model == "project.task":
            domain = self._domain(
                model,
                owner_field="user_ids",
                date_field="date_deadline",
            )
            state, owner, deadline = "state", "user_ids", "date_deadline"
        elif model == "tp.contract.revision":
            domain = self._domain(model, owner_field=False, date_field="recorded_at")
            state, owner, deadline = "review_state", False, False
        else:
            domain = self._domain(
                model,
                date_field="period_from"
                if model == "tp.periodic.plan"
                else "valid_to"
                if model == "tp.credential"
                else "date",
            )
            state, owner, deadline = "state", "owner_id", "date_due"
        today = fields.Date.context_today(self)
        if query == "review":
            if model == "tp.contract.revision":
                domain += [
                    ("review_state", "=", "in_review"),
                    (
                        "submission_ids",
                        "any",
                        [
                            ("outcome", "=", "pending"),
                            "|", ("assigned_reviewer_id", "=", self.env.uid),
                            "&", ("assigned_reviewer_id", "=", False), ("reviewer_id", "=", self.env.uid),
                        ],
                    ),
                ]
            elif model in ("crm.lead", "project.task"):
                domain += [("id", "=", 0)]
            else:
                kd_domain = self.env[model]._kd_domain
                projects = self.env["project.project"].search(
                    [("tp_managed", "=", True)],
                )
                eligible = projects.filtered(
                    lambda p: self.env["tp.kd.grant"]._has(p, kd_domain, "review"),
                )
                domain += [
                    ("project_id", "in", eligible.ids),
                    ("state", "=", "in_review"),
                    ("reviewer_id", "=", self.env.uid),
                ]
        elif query == "returned":
            if model == "tp.contract.revision":
                domain += [
                    ("review_state", "=", "returned"),
                    (
                        "submission_ids",
                        "any",
                        [
                            ("outcome", "=", "returned"),
                            ("submitted_by_id", "=", self.env.uid),
                            ("rework_started_by_id", "=", False),
                        ],
                    ),
                ]
            elif model in ("crm.lead", "project.task"):
                domain += [("id", "=", 0)]
            else:
                domain += [(state, "=", "returned"), (owner, "=", self.env.uid)]
        elif query in ("overdue", "due"):
            if not deadline or model == "tp.periodic.plan":
                domain += [("id", "=", 0)]
            else:
                domain += [(deadline, "!=", False)]
                if query == "overdue":
                    domain += [(deadline, "<", today)]
                else:
                    domain += [
                        (deadline, ">=", today),
                        (deadline, "<", today + timedelta(days=4)),
                    ]
                if model == "project.task":
                    domain += [("is_closed", "=", False)]
                elif model == "crm.lead":
                    domain += [("kd_bid_state", "!=", "submitted")]
        elif query == "expiring":
            domain += (
                [
                    ("valid_to", ">=", today),
                    ("valid_to", "<=", today + timedelta(days=30)),
                ]
                if model == "tp.credential"
                else [("id", "=", 0)]
            )
        elif query == "draft":
            domain += (
                [(state, "=", "draft")]
                if model not in ("crm.lead", "project.task")
                else [("id", "=", 0)]
            )
        elif query == "effective":
            domain += (
                [("effectivity_status", "=", "effective_recorded")]
                if model == "tp.contract.revision"
                else [("id", "=", 0)]
            )
        return domain

    @api.depends_context("uid")
    @api.depends("project_id", "owner_id", "date_from", "date_to")
    def _compute_inbox_counts(self):
        for rec in self:
            for prefix, (model, label) in SOURCES.items():
                for query in QUERIES:
                    rec[f"{prefix}_{query}_count"] = (
                        self.env[model].search_count(rec._inbox_domain(model, query))
                        if self.env[model].has_access("read")
                        else 0
                    )

    def action_inbox(self):
        self.ensure_one()
        model = self.env.context.get("kd_source")
        query = self.env.context.get("kd_query", "all")
        name = next((label for m, label in SOURCES.values() if m == model), None)
        if not name:
            raise UserError(self.env._("Chọn nguồn hồ sơ hợp lệ."))
        return open_records(self.env, model, self._inbox_domain(model, query), name)
