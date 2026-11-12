"""Separate execution and commercial questions, queried under current ORM rights."""

from datetime import timedelta

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError

from .workspace import child_context, open_records

COMMERCIAL = {
    "contracts": ("tp.contract", "Hợp đồng và phụ lục", "create_uid", False),
    "allocations": ("tp.allocation", "Giao khoán và thầu phụ", "owner_id", "date_due"),
    "productions": ("tp.production", "Sản lượng theo kỳ", "owner_id", "date_due"),
    "acceptances": ("tp.acceptance", "Hồ sơ nghiệm thu", "owner_id", "date_due"),
    "plans": ("tp.periodic.plan", "Kế hoạch định kỳ", "owner_id", "date_due"),
    "payments": ("tp.payment.request", "Đề nghị thanh toán", "owner_id", "date_due"),
    "obligations": (
        "tp.obligation",
        "Nghĩa vụ và hồ sơ còn thiếu",
        "owner_id",
        "date_due",
    ),
}


class ProjectPerspective(models.TransientModel):
    _name = "tp.project.perspective"
    _description = "Tổng quan thực hiện và quản trị dự án"

    @api.model
    def _scope(self, project_id=False):
        if project_id and (
            isinstance(project_id, bool)
            or not isinstance(project_id, int)
            or project_id < 1
        ):
            raise UserError(self.env._("Mã dự án không hợp lệ."))
        projects = self.env["project.project"].search([("tp_managed", "=", True)])
        selected = (
            projects.filtered(lambda p: p.id == project_id) if project_id else projects
        )
        if project_id and not selected:
            raise AccessError(self.env._("Dự án không còn trong quyền."))
        return projects, selected

    @api.model
    def _task_domain(self, projects, bucket="all"):
        now = fields.Datetime.now()
        domain = [("project_id", "in", projects.ids)]
        if bucket == "done":
            domain += [("state", "=", "1_done")]
        elif bucket == "overdue":
            domain += [
                ("state", "not in", ("1_done", "1_canceled")),
                ("date_deadline", "<", now),
            ]
        elif bucket == "due":
            domain += [
                ("state", "not in", ("1_done", "1_canceled")),
                ("date_deadline", ">=", now),
                ("date_deadline", "<=", now + timedelta(days=3)),
            ]
        return domain

    @api.model
    def get_perspective(self, mode, project_id=False, limit=20, offset=0):
        self.check_access("read")
        if (
            mode not in ("management", "governance")
            or limit not in (10, 20, 50, 100)
            or isinstance(offset, bool)
            or not isinstance(offset, int)
            or offset < 0
        ):
            raise UserError(self.env._("Góc nhìn hoặc phân trang không hợp lệ."))
        projects, selected = self._scope(project_id)
        result = {
            "mode": mode,
            "projects": [
                {"id": p.id, "code": p.tp_code, "name": p.name} for p in projects
            ],
            "selected": project_id,
            "updated_at": fields.Datetime.to_string(fields.Datetime.now()),
            "project_count": len(selected),
            "rows": [],
            "counts": [],
        }
        if mode == "management":
            tasks = self.env["project.task"]
            for key, label in [
                ("all", "Công việc trong phạm vi"),
                ("done", "Công việc hoàn tất"),
                ("overdue", "Việc đang mở quá hạn"),
                ("due", "Đến hạn trong 3 ngày"),
            ]:
                result["counts"].append(
                    {
                        "key": key,
                        "label": label,
                        "count": tasks.search_count(self._task_domain(selected, key)),
                    },
                )
            domain = self._task_domain(selected)
            rows = tasks.search(
                domain,
                limit=limit,
                offset=offset,
                order="date_deadline asc,id asc",
            )
            result["total"] = tasks.search_count(domain)
            result["rows"] = [
                {
                    "id": t.id,
                    "name": t.name,
                    "project": t.project_id.display_name,
                    "parent": t.parent_id.display_name or "",
                    "owner": t.kd_responsible_id.display_name
                    or ", ".join(t.user_ids.mapped("display_name"))
                    or "Chưa giao",
                    "deadline": fields.Datetime.to_string(t.date_deadline) or "",
                    "state_key": t.state,
                    "state": dict(
                        t._fields["state"]._description_selection(self.env),
                    ).get(t.state, t.state),
                    "output": t.kd_deliverable or "Chưa có đầu ra",
                }
                for t in rows
            ]
        else:
            result["total"] = len(COMMERCIAL)
            for key, (model, label, owner, deadline) in COMMERCIAL.items():
                source = self.env[model]
                domain = [("project_id", "in", selected.ids)]
                total = source.search_count(domain)
                overdue = (
                    source.search_count(
                        domain + [(deadline, "<", fields.Date.context_today(self))],
                    )
                    if deadline
                    else None
                )
                result["rows"].append(
                    {
                        "key": key,
                        "label": label,
                        "total": total,
                        "overdue": overdue,
                        "missing": source.search_count(
                            domain + [("checklist_status", "=", "missing")],
                        )
                        if model == "tp.obligation"
                        else None,
                    },
                )
            packages = self.env["tp.bid.package"]
            result["counts"] = [
                {
                    "key": "packages",
                    "label": "Gói thầu trong phạm vi",
                    "count": packages.search_count(
                        [("project_id", "in", selected.ids)],
                    ),
                },
                {
                    "key": "reconcile",
                    "label": "Hồ sơ tham gia cần đối chiếu gói",
                    "count": self.env["crm.lead"].search_count(
                        [
                            ("tp_project_id", "in", selected.ids),
                            ("kd_route", "=", "bid"),
                            ("kd_package_id", "=", False),
                        ],
                    ),
                },
            ]
        return result

    @api.model
    def open_perspective_source(self, mode, key, project_id=False, record_id=False):
        self.check_access("read")
        _, projects = self._scope(project_id)
        if mode == "management":
            if key not in ("all", "done", "overdue", "due", "wbs", "task"):
                raise UserError(self.env._("Nguồn công việc không hợp lệ."))
            domain = self._task_domain(projects, key)
            action = open_records(
                self.env,
                "project.task",
                domain,
                "Hạng mục / WBS" if key == "wbs" else "Công việc và tiến độ",
                {"group_by": "parent_id" if key == "wbs" else "kd_responsible_id"}
                if key in ("wbs", "all")
                else {},
            )
            if record_id:
                task = self.env["project.task"].search(
                    [("id", "=", record_id), ("project_id", "in", projects.ids)],
                )
                if not task:
                    raise AccessError(self.env._("Công việc không còn trong quyền."))
                action.update(
                    res_id=task.id,
                    views=[(self.env.ref("tp_kd_workspace.kd_task_form").id, "form")],
                )
            return action
        if mode != "governance":
            raise UserError(self.env._("Góc nhìn không hợp lệ."))
        if key in COMMERCIAL:
            model, label, _, _ = COMMERCIAL[key]
            return open_records(
                self.env,
                model,
                [("project_id", "in", projects.ids)],
                label,
            )
        if key == "packages":
            return open_records(
                self.env,
                "tp.bid.package",
                [("project_id", "in", projects.ids)],
                "Đấu thầu",
            )
        if key == "reconcile":
            return open_records(
                self.env,
                "crm.lead",
                [
                    ("tp_project_id", "in", projects.ids),
                    ("kd_route", "=", "bid"),
                    ("kd_package_id", "=", False),
                ],
                "Hồ sơ cần đối chiếu gói",
            )
        raise UserError(self.env._("Nguồn quản trị không hợp lệ."))

    @api.model
    def switch_perspective(self, mode, project_id=False, detail=False):
        _, projects = self._scope(project_id)
        if mode not in ("management", "governance"):
            raise UserError(self.env._("Góc nhìn không hợp lệ."))
        if detail:
            if not project_id:
                raise UserError(self.env._("Chọn một dự án để mở chi tiết."))
            return projects._kd_perspective(mode)
        action = self.env["ir.actions.actions"]._for_xml_id(
            "tp_kd_workspace.action_" + mode,
        )
        action["context"] = {
            **child_context(self.env),
            "default_project_id": project_id,
            "tp_perspective": mode,
            "tp_kd_leaf": "tp_kd_workspace.menu_" + mode,
        }
        return action
