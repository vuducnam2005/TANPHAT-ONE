"""KD-UI-002/004 read-only Overview report helpers.

Every helper runs in the caller's environment (record rules + KD grants), accepts only
whitelisted filter keys/enums/ids and rebuilds domains from the existing `_domain` /
`_inbox_domain` helpers. The client never sends a model, field or domain. Nothing here
writes business data; filters live on an in-memory `new()` record.
"""

from datetime import date, timedelta

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError
from odoo.tools.misc import formatLang

from .reporting import QUERIES, SOURCES
from .workspace import child_context, kd_leaf, open_records

TYPED = ("allocation", "production", "acceptance", "payment", "plan", "credential", "obligation")
STATES = ("draft", "in_review", "returned")
INBOX = TYPED + ("contract",)
DUE = ("allocation", "production", "acceptance", "payment", "credential", "obligation", "task", "opportunity")
OWNER = {"task": "user_ids", "opportunity": "user_id"}  # typed models: owner_id
DEADLINE = {"task": "date_deadline", "opportunity": "kd_deadline"}  # typed models: date_due
TABS = ("review", "returned", "due")
ORDERS = {"name": "name", "code": "tp_code", "partner": "partner_id", "user": "user_id", "deadline": "kd_deadline"}
PERIODS = ("month", "quarter", "year")
TASK_BUCKETS = ("all", "done", "overdue", "open")
CRED_BUCKETS = ("expired", "soon", "later")
ROUTES = ("bid", "direct")
BID_STATES = ("identified", "preparation", "submitted")
PAGE_MAX = 100
MERGE_MAX = 500
CREATE_LABELS = {
    "opportunity": "Hồ sơ dự án / hồ sơ thầu",
    "contract": "Nháp hợp đồng (TP Contracts)",
    "task": "Công việc / WBS",
    "allocation": "Giao khoán / thầu phụ",
    "production": "Sản lượng theo kỳ",
    "acceptance": "Hồ sơ nghiệm thu nội bộ",
    "payment": "Đề nghị thanh toán",
    "plan": "Kế hoạch định kỳ",
    "credential": "Năng lực / chứng chỉ",
    "obligation": "Nghĩa vụ / hồ sơ thiếu",
}
LIST_MODELS = {"projects": "project.project", "opportunities": "crm.lead", "contracts": "tp.contract",
               "revisions": "tp.contract.revision", "tasks": "project.task"}
# Per-project shortcuts in the Overview table: existing project.project methods (they re-check access).
PROJECT_ACTIONS = (
    ("action_kd_opportunities", "opportunity", "Hồ sơ dự án / hồ sơ thầu"),
    ("action_kd_contracts", "contract", "Hợp đồng"),
    ("action_kd_tasks", "task", "Kế hoạch / WBS"),
    ("action_kd_allocations", "allocation", "Giao khoán"),
    ("action_kd_productions", "production", "Sản lượng"),
    ("action_kd_acceptances", "acceptance", "Nghiệm thu nội bộ"),
    ("action_kd_payments", "payment", "Đề nghị thanh toán"),
    ("action_kd_plans", "plan", "Kế hoạch định kỳ"),
    ("action_kd_obligations", "obligation", "Nghĩa vụ / hồ sơ thiếu"),
)


def _int(value):
    if value in (None, False, ""):
        return False
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        msg = "Tham số không hợp lệ."
        raise UserError(msg)
    return value


def _date(value):
    if value in (None, False, ""):
        return False
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as error:
        msg = "Ngày lọc không hợp lệ."
        raise UserError(msg) from error


class Overview(models.TransientModel):
    _inherit = "tp.kd.overview"

    # ------------------------------------------------------------------ filters
    @api.model
    def _kd_filter(self, filters):
        filters = filters or {}
        if not isinstance(filters, dict) or set(filters) - {"project_id", "owner_id", "date_from", "date_to"}:
            raise UserError(self.env._("Bộ lọc không hợp lệ."))
        project_id = _int(filters.get("project_id"))
        owner_id = _int(filters.get("owner_id"))
        values = {"date_from": _date(filters.get("date_from")), "date_to": _date(filters.get("date_to"))}
        if project_id:
            project = self.env["project.project"].search([("tp_managed", "=", True), ("id", "=", project_id)])
            if not project:
                raise UserError(self.env._("Dự án không có trong phạm vi được xem."))
            values["project_id"] = project.id
        if owner_id:
            owner = self.env["res.users"].search([("id", "=", owner_id)])
            if not owner:
                raise UserError(self.env._("Người phụ trách không hợp lệ."))
            values["owner_id"] = owner.id
        record = self.new(values)
        record._domain("project.project", owner_field=False, date_field=False)  # validates the date range
        return record

    def _kd_model(self, prefix):
        return SOURCES[prefix][0]

    def _kd_today(self):
        return fields.Date.context_today(self)

    def _kd_count(self, model, domain):
        if not self.env[model].has_access("read"):
            return 0
        return self.env[model].search_count(domain)

    def _kd_mine(self, prefix, tab):
        """My-work domain: existing inbox domain; due tab = overdue + due of the current owner."""
        model = self._kd_model(prefix)
        if tab in ("review", "returned"):
            return self._inbox_domain(model, tab)
        today = self._kd_today()
        deadline = DEADLINE.get(prefix, "date_due")
        domain = self._inbox_domain(model, "all") + [
            (deadline, "!=", False),
            (deadline, "<", today + timedelta(days=4)),
            (OWNER.get(prefix, "owner_id"), "in", [self.env.uid]),
        ]
        if prefix == "task":
            domain.append(("is_closed", "=", False))
        elif prefix == "opportunity":
            domain.append(("kd_bid_state", "!=", "submitted"))
        return domain

    def _kd_task_domain(self, bucket, project_id=False):
        domain = self._inbox_domain("project.task", "all")
        if project_id:
            domain.append(("project_id", "=", project_id))
        if bucket == "done":
            domain.append(("is_closed", "=", True))
        elif bucket == "overdue":
            domain += [("is_closed", "=", False), ("date_deadline", "!=", False),
                       ("date_deadline", "<", self._kd_today())]
        elif bucket == "open":
            domain += [("is_closed", "=", False), "|", ("date_deadline", "=", False),
                       ("date_deadline", ">=", self._kd_today())]
        return domain

    def _kd_credential_domain(self, bucket):
        today = self._kd_today()
        domain = self._domain("tp.credential", date_field="valid_to")
        return domain + {
            "expired": [("valid_to", "<", today)],
            "soon": [("valid_to", ">=", today), ("valid_to", "<=", today + timedelta(days=30))],
            "later": [("valid_to", ">", today + timedelta(days=30))],
        }[bucket]

    def _kd_lead_domain(self, route, bid_state=False):
        domain = self._inbox_domain("crm.lead", "all")
        if route:
            domain.append(("kd_route", "=", route))
        if bid_state:
            domain.append(("kd_bid_state", "=", bid_state))
        return domain

    # ------------------------------------------------------------------ create
    def _kd_create_kinds(self):
        kinds = []
        projects = self.env["project.project"].search([("tp_managed", "=", True)])
        grant = self.env["tp.kd.grant"]
        if self.env["crm.lead"].has_access("create") and any(grant._has(p, "opportunity", "prepare") for p in projects):
            kinds.append("opportunity")
        workflow = self.env["tp.contract.workflow"]
        if any("contract_draft_edit" in workflow._tp_capabilities(p, p.tp_department_id) for p in projects):
            kinds.append("contract")
        if any(project._kd_has("wbs") for project in projects):
            kinds.append("task")
        for prefix in TYPED:
            model = self.env[self._kd_model(prefix)]
            try:
                allowed = model.has_access("create") and model.get_kd_ui_permissions()["create"]
            except AccessError:
                allowed = False
            if allowed:
                kinds.append(prefix)
        return kinds

    @api.model
    def action_kd_create(self, kind, project_id=False):
        if kind not in CREATE_LABELS or kind not in self._kd_create_kinds():
            raise AccessError(self.env._("Bạn chưa có quyền tạo loại hồ sơ này."))
        project = self._kd_filter({"project_id": project_id}).project_id if project_id else False
        context = child_context(self.env)
        if kind == "contract":
            action = self.env["ir.actions.actions"]._for_xml_id("tp_contract.action_native_draft")
            action["context"] = dict(context, **({"default_project_id": project.id} if project else {}),
                                     **kd_leaf("tp.contract"))
            return action
        if kind == "opportunity":
            model, view = "crm.lead", self.env.ref("tp_kd_workspace.opportunity_form").id
            context.update(default_type="opportunity", **({"default_tp_project_id": project.id} if project else {}))
        elif kind == "task":
            if not project:
                raise UserError(self.env._("Chọn Dự án trên Tổng quan trước khi thêm công việc / WBS."))
            return project.action_kd_new_task()
        else:
            model, view = self._kd_model(kind), False
            context.update(**({"default_project_id": project.id} if project else {}))
        context.update(kd_leaf(model))
        return {"type": "ir.actions.act_window", "name": CREATE_LABELS[kind], "res_model": model,
                "views": [(view, "form")], "target": "current", "context": context}

    # ------------------------------------------------------------------ dashboard
    @api.model
    def get_kd_dashboard(self, filters=None):
        rec = self._kd_filter(filters)
        today = rec._kd_today()
        now = fields.Datetime.context_timestamp(self, fields.Datetime.now())
        mine = {
            tab: {p: rec._kd_count(rec._kd_model(p), rec._kd_mine(p, tab))
                  for p in (INBOX if tab != "due" else DUE)}
            for tab in TABS
        }
        overdue = sum(
            rec._kd_count(rec._kd_model(p), rec._kd_mine(p, "due") + [(DEADLINE.get(p, "date_due"), "<", today)])
            for p in DUE
        )
        contracts = rec._kd_count("tp.contract", rec._domain("tp.contract", owner_field="create_uid", date_field=False))
        revisions = rec._kd_count("tp.contract.revision", rec._inbox_domain("tp.contract.revision", "all"))
        projects = rec._kd_count("project.project", [("tp_managed", "=", True)]
                                 + ([("id", "=", rec.project_id.id)] if rec.project_id else []))
        g01 = []
        for prefix in TYPED:
            model = rec._kd_model(prefix)
            counts = dict.fromkeys(STATES, 0)
            if self.env[model].has_access("read"):
                for state, count in self.env[model]._read_group(
                    rec._inbox_domain(model, "all") + [("state", "in", STATES)], ["state"], ["__count"],
                ):
                    counts[state] = count
            g01.append({"source": prefix, "label": SOURCES[prefix][1], **counts, "total": sum(counts.values()),
                        "available": self.env[model].has_access("read")})
        # Read rights decide which drill-down buttons the client shows (the server re-checks anyway).
        readable = {p: self.env[model].has_access("read") for p, (model, _label) in SOURCES.items()}
        readable.update({name: self.env[model].has_access("read") for name, model in LIST_MODELS.items()})
        return {
            "updated_at": now.strftime("%H:%M %d/%m/%Y"),
            "today": fields.Date.to_string(today),
            "filters": {"project_id": rec.project_id.id or False, "owner_id": rec.owner_id.id or False,
                        "date_from": fields.Date.to_string(rec.date_from) or False,
                        "date_to": fields.Date.to_string(rec.date_to) or False},
            "options": self._kd_filter_options(),
            "kpis": {
                "review": sum(mine["review"].values()), "returned": sum(mine["returned"].values()),
                "overdue": overdue, "due": sum(mine["due"].values()) - overdue,
                # `due` = deadline in [today, today + 3] after overdue is split out (`_kd_mine` < today + 4).
                "due_window": {"from": fields.Date.to_string(today),
                               "to": fields.Date.to_string(today + timedelta(days=3))},
                "contracts": contracts, "revisions": revisions, "projects": projects,
                "breakdown": {tab: {p: c for p, c in counts.items() if c} for tab, counts in mine.items()},
            },
            "g01": {"rows": g01, "totals": {s: sum(r[s] for r in g01) for s in (*STATES, "total")}},
            "g02": rec._kd_g02(),
            "g03": rec._kd_g03(),
            "create": [{"kind": k, "label": CREATE_LABELS[k]} for k in self._kd_create_kinds()],
            "project_actions": [{"method": m, "label": label} for m, source, label in PROJECT_ACTIONS
                                if self.env["tp.contract" if source == "contract" else SOURCES[source][0]].has_access("read")],
            "labels": {p: SOURCES[p][1] for p in SOURCES},
            "readable": readable,
        }

    @api.model
    def _kd_filter_options(self):
        projects = self.env["project.project"].search([("tp_managed", "=", True)], order="tp_code, name", limit=200)
        users = self.env["res.users"].search([("share", "=", False)], order="name", limit=200)
        return {
            "projects": [{"id": p.id, "label": " · ".join(filter(None, [p.tp_code, p.name]))} for p in projects],
            "owners": [{"id": u.id, "label": u.name} for u in users],
        }

    def _kd_g02(self):
        task = self.env["project.task"]
        if not task.has_access("read"):
            return {"available": False, "rows": [], "no_deadline": 0,
                    "totals": dict.fromkeys(("done", "overdue", "open", "total"), 0)}
        counts = {}
        for bucket in ("all", "done", "overdue"):
            for project, count in task._read_group(self._kd_task_domain(bucket), ["project_id"], ["__count"]):
                counts.setdefault(project, dict.fromkeys(("all", "done", "overdue"), 0))[bucket] = count
        rows = []
        for project, value in counts.items():
            if not project:
                continue
            rows.append({
                "project_id": project.id, "code": project.tp_code or "", "name": project.name,
                "done": value["done"], "overdue": value["overdue"],
                "open": value["all"] - value["done"] - value["overdue"], "total": value["all"],
            })
        rows.sort(key=lambda r: (-r["overdue"], -(r["open"] + r["overdue"]), r["code"], r["project_id"]))
        no_deadline = task.search_count(self._kd_task_domain("open") + [("date_deadline", "=", False)])
        return {"available": True, "rows": rows, "no_deadline": no_deadline,
                "totals": {k: sum(r[k] for r in rows) for k in ("done", "overdue", "open", "total")}}

    def _kd_g03(self):
        lead = self.env["crm.lead"]
        bid = dict.fromkeys(BID_STATES, 0)
        direct = 0
        available = lead.has_access("read")
        if available:
            for route, state, count in lead._read_group(
                self._kd_lead_domain(False), ["kd_route", "kd_bid_state"], ["__count"],
            ):
                if route == "direct":
                    direct += count
                elif route == "bid" and state in bid:
                    bid[state] += count
        return {"available": available, "bid": bid, "direct": direct, "total": sum(bid.values()) + direct}

    # ------------------------------------------------------------------ lazy details
    @api.model
    def get_kd_plan_compare(self, filters=None, period_kind="month"):
        if period_kind not in PERIODS:
            raise UserError(self.env._("Loại kỳ không hợp lệ."))
        rec = self._kd_filter(filters)
        plan = self.env["tp.periodic.plan"]
        if not plan.has_access("read"):
            return {"available": False, "period_kind": period_kind, "rows": [], "in_scope": 0, "excluded": 0, "more": 0}
        plans = plan.search(rec._domain("tp.periodic.plan", date_field="period_from")
                            + [("period_kind", "=", period_kind)], order="period_from desc, id desc")
        allowed = plans.filtered(lambda p: p._kd_money_allowed())
        rows = []
        for item in allowed[:12]:
            line = item.amount_ids.filtered(lambda a: a.measure == "production")[:1]
            status = line.source_status if line else "no_data"
            target = line.value if line and line.amount_state == "confirmed" else None
            source = line.source_value if line and status == "comparable" else None
            rows.append({
                "plan_id": item.id, "code": item.code, "name": item.name,
                "project": item.project_id.tp_code or item.project_id.name,
                "period": self._kd_period_label(item),
                "target": target, "source": source,
                "target_text": formatLang(self.env, target, currency_obj=line.currency_id) if target is not None else None,
                "source_text": formatLang(self.env, source, currency_obj=line.currency_id) if source is not None else None,
                "target_state": "confirmed" if target is not None else ("unconfirmed" if line else "missing"),
                # Unit of this row only: rows are never added or compared across currencies/tax bases.
                "currency": line.currency_id.name if line else None,
                "basis_label": dict(line._fields["tax_basis"]._description_selection(self.env)).get(line.tax_basis)
                if line else None,
                "status": status,
                "status_label": dict(line._fields["source_status"]._description_selection(self.env)).get(status)
                if line else "Chưa có mục tiêu sản lượng",
                "ratio": round(source * 100 / target, 1) if target and source is not None else None,
            })
        peak = max([v for r in rows for v in (r["target"], r["source"]) if v] or [0])
        for row in rows:
            for key in ("target", "source"):
                row[f"{key}_bar"] = round(row[key] * 100 / peak, 2) if peak and row[key] else 0
                row.pop(key)  # raw floats stay server side; client renders server-formatted text
        rows.reverse()
        return {"available": True, "period_kind": period_kind, "rows": rows, "in_scope": len(plans),
                "excluded": len(plans) - len(allowed), "more": max(len(allowed) - 12, 0)}

    def _kd_period_label(self, plan):
        start = plan.period_from
        if plan.period_kind == "month":
            return f"T{start.month}/{start.year}"
        if plan.period_kind == "quarter":
            return f"Q{(start.month - 1) // 3 + 1}/{start.year}"
        return str(start.year)

    @api.model
    def get_kd_credential_expiry(self, filters=None):
        rec = self._kd_filter(filters)
        cred = self.env["tp.credential"]
        today = rec._kd_today()
        # Bucket edges of `_kd_credential_domain` in the user's timezone (display only).
        bounds = {"today": fields.Date.to_string(today), "soon_until": fields.Date.to_string(today + timedelta(days=30))}
        if not cred.has_access("read"):
            return {"available": False, "buckets": dict.fromkeys(CRED_BUCKETS, 0), "soon": [], "bounds": bounds}
        soon = cred.search(rec._kd_credential_domain("soon"), order="valid_to, id", limit=5)
        return {
            "available": True,
            "bounds": bounds,
            "buckets": {b: cred.search_count(rec._kd_credential_domain(b)) for b in CRED_BUCKETS},
            "soon": [{"id": c.id, "code": c.code, "name": c.name, "valid_to": fields.Date.to_string(c.valid_to)}
                     for c in soon],
        }

    @api.model
    def get_kd_source_table(self, filters=None):
        rec = self._kd_filter(filters)
        rows = [{"source": p, "label": label,
                 **{q: rec._kd_count(model, rec._inbox_domain(model, q))
                    for q in ("all", "review", "returned", "overdue", "due")}}
                for p, (model, label) in SOURCES.items()]
        extras = {
            "expiring": rec._kd_count("tp.credential", rec._inbox_domain("tp.credential", "expiring")),
            "contract_draft": rec._kd_count("tp.contract.revision", rec._inbox_domain("tp.contract.revision", "draft")),
            "contract_effective": rec._kd_count("tp.contract.revision",
                                                rec._inbox_domain("tp.contract.revision", "effective")),
        }
        return {"rows": rows, "extras": extras}

    # ------------------------------------------------------------------ project table
    @api.model
    def get_kd_project_rows(self, filters=None, search="", order="code", offset=0, limit=10):
        rec = self._kd_filter(filters)
        field, _, direction = (order or "code").partition(" ")
        if field not in ORDERS or direction not in ("", "asc", "desc") or not isinstance(search, str):
            raise UserError(self.env._("Sắp xếp hoặc tìm kiếm không hợp lệ."))
        offset, limit = int(offset or 0), int(limit or 10)
        if offset < 0 or not 0 < limit <= PAGE_MAX:
            raise UserError(self.env._("Phân trang không hợp lệ."))
        domain = [("tp_managed", "=", True)] + ([("id", "=", rec.project_id.id)] if rec.project_id else [])
        if search.strip():
            text = search.strip()[:80]
            domain += ["|", "|", ("name", "ilike", text), ("tp_code", "ilike", text), ("partner_id.name", "ilike", text)]
        project = self.env["project.project"]
        total = project.search_count(domain)
        sort = f"{ORDERS[field]} {direction or 'asc'}, id"
        page = project.search(domain, order=sort, offset=offset, limit=limit)
        tasks = {}
        if self.env["project.task"].has_access("read"):
            for bucket in ("all", "done", "overdue"):
                grouped = self.env["project.task"]._read_group(
                    rec._kd_task_domain(bucket) + [("project_id", "in", page.ids)], ["project_id"], ["__count"])
                for proj, count in grouped:
                    tasks.setdefault(proj.id, dict.fromkeys(("all", "done", "overdue"), 0))[bucket] = count
        queue = {"review": {}, "returned": {}}
        for tab, counts in queue.items():
            for prefix in INBOX:
                model = rec._kd_model(prefix)
                if not self.env[model].has_access("read"):
                    continue
                for proj, count in self.env[model]._read_group(
                    rec._kd_mine(prefix, tab) + [("project_id", "in", page.ids)], ["project_id"], ["__count"]):
                    counts[proj.id] = counts.get(proj.id, 0) + count
        rows = []
        for item in page:
            task = tasks.get(item.id, dict.fromkeys(("all", "done", "overdue"), 0))
            rows.append({
                "id": item.id, "code": item.tp_code or "", "name": item.name,
                "partner": item.partner_id.display_name or "", "user": item.user_id.name or "",
                "department": item.tp_department_id.display_name or "",
                "deadline": fields.Date.to_string(item.kd_deadline) or False,
                "deadline_late": bool(item.kd_deadline and item.kd_deadline < rec._kd_today()),
                "task_open": task["all"] - task["done"], "task_overdue": task["overdue"],
                "review": queue["review"].get(item.id, 0), "returned": queue["returned"].get(item.id, 0),
            })
        return {"rows": rows, "total": total, "offset": offset, "limit": limit, "order": f"{field} {direction or 'asc'}"}

    # ------------------------------------------------------------------ my work
    @api.model
    def get_kd_my_work(self, filters=None, tab="review", offset=0, limit=10):
        if tab not in TABS:
            raise UserError(self.env._("Nhóm việc không hợp lệ."))
        rec = self._kd_filter(filters)
        offset, limit = int(offset or 0), int(limit or 10)
        if offset < 0 or not 0 < limit <= PAGE_MAX or offset + limit > MERGE_MAX:
            raise UserError(self.env._("Phân trang không hợp lệ."))
        counts, rows = {}, []
        for prefix in (INBOX if tab != "due" else DUE):
            model = self.env[rec._kd_model(prefix)]
            if not model.has_access("read"):
                continue
            domain = rec._kd_mine(prefix, tab)
            counts[prefix] = model.search_count(domain)
            if not counts[prefix]:
                continue
            deadline = DEADLINE.get(prefix, "date_due") if prefix != "contract" else False
            order = f"{deadline} asc, id asc" if deadline else "id asc"
            records = model.search(domain, order=order, limit=offset + limit)
            rows += [rec._kd_work_row(prefix, r, DUE.index(prefix) if prefix in DUE else INBOX.index(prefix))
                     for r in records]
        # Same key as each per-model fetch (deadline asc NULLS LAST, id), so merged pages are stable.
        rows.sort(key=lambda r: r.pop("_sort"))
        return {"tab": tab, "total": sum(counts.values()), "counts": {k: v for k, v in counts.items() if v},
                "rows": rows[offset:offset + limit], "offset": offset, "limit": limit}

    def _kd_work_row(self, prefix, record, rank):
        today = self._kd_today()
        if prefix == "contract":
            state_field, deadline, code = "review_state", False, record.contract_id.code
            owner = record.create_uid.name
            project = record.project_id
        elif prefix == "task":
            state_field, deadline, code = "state", record.date_deadline and record.date_deadline.date(), ""
            owner = ", ".join(record.user_ids.mapped("name"))
            project = record.project_id
        elif prefix == "opportunity":
            state_field, deadline, code = "kd_bid_state", record.kd_deadline, ""
            owner, project = record.user_id.name, record.tp_project_id
        else:
            state_field, deadline, code = "state", record.date_due, record.code
            owner, project = record.owner_id.name, record.project_id
        labels = dict(record._fields[state_field]._description_selection(self.env))
        return {
            "source": prefix, "type": SOURCES[prefix][1], "id": record.id, "code": code or "",
            "name": record.name, "project": project.tp_code or project.name or "",
            "owner": owner or "", "state": record[state_field], "state_label": labels.get(record[state_field], ""),
            "deadline": fields.Date.to_string(deadline) or False,
            "overdue": bool(deadline and deadline < today),
            "_sort": (deadline or date.max, rank, str(record.date_deadline) if prefix == "task" else "", record.id),
        }

    # ------------------------------------------------------------------ drilldown
    @api.model
    def action_kd_open(self, key, filters=None, params=None):
        rec = self._kd_filter(filters)
        params = params or {}
        if not isinstance(params, dict):
            raise UserError(self.env._("Tham số không hợp lệ."))
        source = params.get("source")
        if key == "source":
            query = params.get("query", "all")
            if source not in SOURCES or query not in QUERIES:
                raise UserError(self.env._("Nguồn hoặc bộ lọc không hợp lệ."))
            model = rec._kd_model(source)
            return open_records(self.env, model, rec._inbox_domain(model, query), SOURCES[source][1])
        if key == "g01":
            state = params.get("state")
            if source not in TYPED or state not in STATES:
                raise UserError(self.env._("Nguồn hoặc trạng thái không hợp lệ."))
            model = rec._kd_model(source)
            return open_records(self.env, model, rec._inbox_domain(model, "all") + [("state", "=", state)],
                                SOURCES[source][1])
        if key == "mine":
            tab = params.get("tab")
            if tab not in TABS or source not in (INBOX if tab != "due" else DUE):
                raise UserError(self.env._("Nhóm việc không hợp lệ."))
            return open_records(self.env, rec._kd_model(source), rec._kd_mine(source, tab), SOURCES[source][1])
        if key == "task":
            bucket = params.get("bucket", "all")
            project_id = _int(params.get("project_id"))
            if bucket not in TASK_BUCKETS:
                raise UserError(self.env._("Nhóm công việc không hợp lệ."))
            return open_records(self.env, "project.task", rec._kd_task_domain(bucket, project_id),
                                "Kế hoạch và công việc")
        if key == "lead":
            route, bid_state = params.get("route") or False, params.get("bid_state") or False
            if (route and route not in ROUTES) or (bid_state and bid_state not in BID_STATES):
                raise UserError(self.env._("Nhóm hồ sơ dự án không hợp lệ."))
            return open_records(self.env, "crm.lead", rec._kd_lead_domain(route, bid_state), "Hồ sơ dự án và hồ sơ thầu",
                                {"form_view_ref": "tp_kd_workspace.opportunity_form"})
        if key == "credential":
            bucket = params.get("bucket")
            if bucket not in CRED_BUCKETS:
                raise UserError(self.env._("Nhóm hạn không hợp lệ."))
            return open_records(self.env, "tp.credential", rec._kd_credential_domain(bucket), "Năng lực và chứng chỉ")
        if key in ("plan", "plan_sources"):
            plan = self.env["tp.periodic.plan"].search(
                rec._domain("tp.periodic.plan", date_field=False) + [("id", "=", _int(params.get("plan_id")))])
            if not plan:
                raise UserError(self.env._("Kế hoạch không có trong phạm vi được xem."))
            if key == "plan_sources":
                return plan.action_source_productions()
            return rec._kd_form("plan", plan)
        if key == "record":
            if source not in SOURCES and source != "project":
                raise UserError(self.env._("Nguồn không hợp lệ."))
            model = "project.project" if source == "project" else rec._kd_model(source)
            record = self.env[model].search([("id", "=", _int(params.get("res_id")))])
            if not record:
                raise UserError(self.env._("Hồ sơ không có trong phạm vi được xem."))
            return rec._kd_form(source, record)
        if key == "list":
            name = params.get("name")
            if name in ("projects", "contracts", "opportunities", "tasks"):
                return getattr(rec, f"action_{name}")()
            if name == "revisions":
                return open_records(self.env, "tp.contract.revision",
                                    rec._inbox_domain("tp.contract.revision", "all"), SOURCES["contract"][1])
            if name in TYPED:
                model = rec._kd_model(name)
                return open_records(self.env, model, rec._inbox_domain(model, "all"), SOURCES[name][1])
        raise UserError(self.env._("Thao tác không hợp lệ."))

    def _kd_form(self, source, record):
        record.check_access("read")
        context = child_context(self.env)
        view = False
        if source == "project":
            view = self.env.ref("tp_kd_workspace.project_governance_form").id
        elif source == "task":
            view = self.env.ref("tp_kd_workspace.kd_task_form").id
        elif source == "opportunity":
            view = self.env.ref("tp_kd_workspace.opportunity_form").id
        context.update(kd_leaf(record._name))
        return {"type": "ir.actions.act_window", "res_model": record._name, "res_id": record.id,
                "views": [(view, "form")], "target": "current", "context": context,
                "name": record.display_name}
