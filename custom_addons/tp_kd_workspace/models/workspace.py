from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

DOMAINS = [
    (k, v)
    for k, v in [
        ("opportunity", "Hồ sơ dự án"),
        ("allocation", "Giao khoán"),
        ("production", "Sản lượng"),
        ("acceptance", "Nghiệm thu"),
        ("payment", "Đề nghị thanh toán"),
        ("plan", "Kế hoạch"),
        ("credential", "Năng lực"),
        ("obligation", "Nghĩa vụ"),
    ]
]
_INTERNAL = object()


def child_context(env):
    # A project form's context must not select its view or inject defaults into
    # a different model. Keep session/company context and explicit child defaults.
    return {
        key: value for key, value in env.context.items()
        if not key.endswith("_view_ref")
        and not key.startswith(("default_", "search_default_"))
        and key not in {"active_id", "active_ids", "active_model", "tp_kd_leaf"}
    }


# KD-UI-003: sidebar leaf (menu XMLID) for actions opened from KH-KD helpers. Presentation hint only:
# the client highlights this leaf; it never selects records, views or rights.
LEAF_BY_MODEL = {
    "project.project": "menu_projects",
    "tp.bid.package": "menu_opportunities",
    "tp.bid.package.amount": "menu_opportunities",
    "tp.project.participation": "menu_governance",
    "crm.lead": "menu_opportunities",
    "project.task": "menu_tasks",
    "tp.contract": "menu_contracts",
    "tp.contract.revision": "menu_contracts",
    "tp.allocation": "menu_allocations",
    "tp.production": "menu_productions",
    "tp.acceptance": "menu_acceptances",
    "tp.payment.request": "menu_payments",
    "tp.periodic.plan": "menu_plans",
    "tp.credential": "menu_credentials",
    "tp.obligation": "menu_obligations",
}


def kd_leaf(model):
    leaf = LEAF_BY_MODEL.get(model)
    return {"tp_kd_leaf": f"tp_kd_workspace.{leaf}"} if leaf else {}


ACTION_XMLID_BY_MODEL = {
    "project.project": "tp_kd_workspace.action_projects",
    "tp.bid.package": "tp_kd_workspace.action_packages",
    "crm.lead": "tp_kd_workspace.action_opportunities",
    "project.task": "tp_kd_workspace.action_tasks",
    "tp.contract": "tp_contract.action_tp_contracts_list",
    "tp.contract.revision": "tp_contract.action_tp_contract_revisions",
    "tp.allocation": "tp_kd_workspace.action_allocations",
    "tp.production": "tp_kd_workspace.action_productions",
    "tp.acceptance": "tp_kd_workspace.action_acceptances",
    "tp.payment.request": "tp_kd_workspace.action_payments",
    "tp.periodic.plan": "tp_kd_workspace.action_plans",
    "tp.credential": "tp_kd_workspace.action_credentials",
    "tp.obligation": "tp_kd_workspace.action_obligations",
}


def open_records(env, model, domain, name, context=None):
    env[model].check_access("read")
    views = {}
    if model == "project.task":
        views["views"] = [
            (env.ref("tp_kd_workspace.kd_task_list").id, "list"),
            (env.ref("tp_kd_workspace.kd_task_form").id, "form"),
        ]
    if model == "crm.lead":
        views["search_view_id"] = env.ref("tp_kd_workspace.opportunity_search").id
        views["views"] = [
            (env.ref("tp_kd_workspace.opportunity_list").id, "list"),
            (env.ref("tp_kd_workspace.opportunity_form").id, "form"),
        ]
    if model == "project.project":
        views["views"] = [
            (env.ref("tp_kd_workspace.kd_project_list").id, "list"),
            (env.ref("tp_kd_workspace.project_governance_form").id, "form"),
        ]
    base_action = {}
    xmlid = ACTION_XMLID_BY_MODEL.get(model)
    if xmlid and env.ref(xmlid, raise_if_not_found=False):
        base_action = env["ir.actions.actions"]._for_xml_id(xmlid)
    merged_ctx = {**child_context(env), **(context or {}), **kd_leaf(model)}
    if model == "tp.contract":
        merged_ctx.setdefault(
            "tp_can_create_contract",
            env["tp.contract"].get_kd_ui_permissions()["can_create_contract"],
        )
    base_action.update({
        **views,
        "type": "ir.actions.act_window",
        "name": name,
        "res_model": model,
        "view_mode": "list,form",
        "domain": domain,
        "context": merged_ctx,
    })
    return base_action


class KdGrant(models.Model):
    _name = "tp.kd.grant"
    _description = "KD synthetic-scope capability; Q2 not authorized for real users"
    _check_company_auto = True

    project_id = fields.Many2one(
        "project.project",
        required=True,
        ondelete="restrict",
        check_company=True,
    )
    company_id = fields.Many2one(related="project_id.company_id", store=True)
    department_id = fields.Many2one(
        "hr.department",
        required=True,
        check_company=True,
        ondelete="restrict",
    )
    user_id = fields.Many2one("res.users", required=True, ondelete="restrict")
    domain = fields.Selection(DOMAINS, required=True)
    capability = fields.Selection(
        [("prepare", "Lập/sửa"), ("submit", "Gửi"), ("review", "Rà soát")],
        required=True,
    )
    date_end = fields.Date()
    active = fields.Boolean(default=True)
    reason = fields.Text(required=True)

    _unique_grant = models.UniqueIndex(
        "(project_id, user_id, domain, capability) WHERE active IS TRUE",
        "Quyền đang hoạt động đã có.",
    )

    def _invalidate_opportunity_access(self):
        self.env.flush_all()
        self.env['crm.lead']._kd_invalidate_security()

    @api.model_create_multi
    def create(self, vals_list):
        result = super().create(vals_list)
        self._invalidate_opportunity_access()
        return result

    def write(self, vals):
        result = super().write(vals)
        self._invalidate_opportunity_access()
        return result

    def unlink(self):
        result = super().unlink()
        self._invalidate_opportunity_access()
        return result

    @api.constrains("project_id", "department_id", "user_id", "reason")
    def _check_scope(self):
        for grant in self:
            if (
                not grant.project_id.tp_managed
                or grant.department_id != grant.project_id.tp_department_id
                or grant.company_id not in grant.user_id.company_ids
                or not grant.user_id.has_group("tp_core.group_user")
                or not (grant.reason or "").strip()
            ):
                msg = (
                    "Quyền cần dự án TANPHAT, đúng phòng/công ty, người dùng và lý do."
                )
                raise ValidationError(
                    msg,
                )

    @api.model
    def _has(self, project, domain, capability, user=None):
        user = user or self.env.user
        if (domain not in self._fields['domain'].get_values(self.env)
                or capability not in self._fields['capability'].get_values(self.env)):
            return False
        if (
            not project.with_user(user).has_access("read")
            or project.company_id not in user.company_ids
        ):
            return False
        if project._tp_head_allowed(user):
            return True
        if (
            not self.env["tp.project.assignment"]
            .sudo()
            .search_count(
                [
                    ("project_id", "=", project.id),
                    ("user_id", "=", user.id),
                    ("active", "=", True),
                ],
                limit=1,
            )
        ):
            return False
        return bool(
            self.sudo().search_count(
                [
                    ("project_id", "=", project.id),
                    ("department_id", "=", project.tp_department_id.id),
                    ("user_id", "=", user.id),
                    ("domain", "=", domain),
                    ("capability", "=", capability),
                    ("active", "=", True),
                    "|",
                    ("date_end", "=", False),
                    ("date_end", ">=", fields.Date.context_today(self)),
                ],
                limit=1,
            ),
        )


class Project(models.Model):
    _inherit = "project.project"

    kd_scope = fields.Text(string="Phạm vi / đầu ra")
    kd_deadline = fields.Date(string="Mốc bàn giao dự kiến")

    def action_kd_opportunities(self):
        self.ensure_one()
        self.check_access("read")
        return open_records(
            self.env,
            "crm.lead",
            [("tp_project_id", "=", self.id)],
            "Hồ sơ dự án và hồ sơ thầu",
            {
                "default_tp_project_id": self.id,
                "default_partner_id": self.partner_id.id,
                "default_company_id": self.company_id.id,
                "default_type": "opportunity",
            },
        )

    def action_kd_contracts(self):
        self.ensure_one()
        self.check_access("read")
        action = self.env["ir.actions.actions"]._for_xml_id(
            "tp_contract.action_tp_contracts_list",
        )
        can_create = "contract_draft_edit" in self.env[
            "tp.contract.workflow"
        ]._tp_capabilities(self, self.tp_department_id)
        action.update(
            domain=[("project_id", "=", self.id)],
            context=dict(
                child_context(self.env),
                default_project_id=self.id,
                tp_can_create_contract=can_create,
                **kd_leaf("tp.contract"),
            ),
        )
        return action

    def action_kd_tasks(self):
        self.ensure_one()
        self.check_access("read")
        return open_records(
            self.env,
            "project.task",
            [("project_id", "=", self.id)],
            "Kế hoạch và công việc",
            {"default_project_id": self.id},
        )


class Task(models.Model):
    _inherit = "project.task"

    kd_responsible_id = fields.Many2one("res.users", string="Chịu trách nhiệm chính")
    kd_assignee_ids = fields.Many2many("res.users", compute="_compute_kd_assignees")
    kd_task_can_write = fields.Boolean(compute="_compute_kd_assignees")

    @api.depends_context("uid")
    @api.depends("project_id")
    def _compute_kd_assignees(self):
        for task in self:
            task.kd_task_can_write = self.env.user.has_group("tp_core.group_manager")
            task.kd_assignee_ids = (
                self.env["tp.project.assignment"]
                .sudo()
                .search(
                    [("project_id", "=", task.project_id.id), ("active", "=", True)],
                )
                .user_id
                if task.project_id.has_access("read")
                else self.env["res.users"]
            )

    @api.model
    def get_kd_ui_permissions(self):
        self.check_access("read")
        return {
            "create": self.env.user.has_group("tp_core.group_manager")
            and self.has_access("create"),
        }

    @api.constrains("project_id", "parent_id", "kd_responsible_id", "user_ids")
    def _kd_check_wbs(self):
        for task in self:
            if task.project_id.tp_managed and (
                (task.parent_id and task.parent_id.project_id != task.project_id)
                or (
                    task.kd_responsible_id
                    and (
                        task.kd_responsible_id not in task.user_ids
                        or not task.project_id._tp_scope_allowed(user=task.kd_responsible_id)
                    )
                )
            ):
                raise ValidationError(
                    self.env._(
                        "WBS phải cùng dự án cha; người chịu trách nhiệm phải được phân công và nằm trong người thực hiện.",
                    ),
                )

    def action_kd_subtasks(self):
        self.ensure_one()
        self.check_access("read")
        return open_records(
            self.env,
            "project.task",
            [("parent_id", "=", self.id)],
            "Công việc con",
            {
                "default_project_id": self.project_id.id,
                "default_parent_id": self.id,
                "default_kd_contract_id": self.kd_contract_id.id,
                "form_view_ref": "tp_kd_workspace.kd_task_form",
            },
        )

    kd_contract_id = fields.Many2one(
        "tp.contract",
        string="Hợp đồng nguồn",
        check_company=True,
        ondelete="restrict",
    )
    kd_deliverable = fields.Char(string="Đầu ra bàn giao")

    def _kd_check_target(self, vals):
        if vals.get("kd_contract_id"):
            self.env["tp.contract"].browse(vals["kd_contract_id"]).check_access("read")

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._kd_check_target(dict(self.default_get(["kd_contract_id"]), **vals))
        return super().create(vals_list)

    def write(self, vals):
        self._kd_check_target(vals)
        return super().write(vals)

    @api.constrains("project_id", "kd_contract_id")
    def _kd_contract_scope(self):
        for task in self.filtered("kd_contract_id"):
            if task.kd_contract_id.project_id != task.project_id:
                msg = "Công việc và hợp đồng phải cùng dự án."
                raise ValidationError(msg)


class Opportunity(models.Model):
    _inherit = "crm.lead"

    kd_route = fields.Selection(
        [("bid", "Đấu thầu"), ("direct", "Giao trực tiếp")],
        default="bid",
        string="Hình thức",
    )
    kd_source = fields.Char(string="Nguồn thông tin")
    kd_scope = fields.Text(string="Phạm vi / gói thầu")
    kd_checklist = fields.Text(string="Checklist hồ sơ")
    kd_deadline = fields.Date(string="Hạn chuẩn bị / nộp")
    kd_bid_state = fields.Selection(
        [
            ("identified", "Đang tìm hiểu"),
            ("preparation", "Đang chuẩn bị"),
            ("submitted", "Đã khai báo nộp — chưa xác minh"),
        ],
        default="identified",
        readonly=True,
        copy=False,
        tracking=True,
        string="Hồ sơ thầu",
    )
    kd_can_prepare = fields.Boolean(compute="_compute_kd_can_prepare")

    @api.depends_context("uid")
    @api.depends("tp_project_id")
    def _compute_kd_can_prepare(self):
        for lead in self:
            lead.kd_can_prepare = bool(
                lead.tp_project_id
                and self.env["tp.kd.grant"]._has(
                    lead.tp_project_id,
                    "opportunity",
                    "prepare",
                ),
            )

    kd_receipt = fields.Char(string="Căn cứ khai báo nộp (nội bộ)")

    def _kd_require(self):
        self.check_access("write")
        for lead in self:
            if not lead.tp_project_id or not self.env["tp.kd.grant"]._has(
                lead.tp_project_id,
                "opportunity",
                "prepare",
            ):
                msg = "Cần quyền lập hồ sơ hồ sơ dự án trong dự án được phân công."
                raise AccessError(
                    msg,
                )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("kd_bid_state", "identified") != "identified":
                msg = "Trạng thái hồ sơ thầu phải qua thao tác backend."
                raise UserError(msg)
            project_id = vals.get("tp_project_id") or self.env.context.get(
                "default_tp_project_id",
            )
            if (
                project_id
                and not self.env.su
                and not self.env["tp.kd.grant"]._has(
                    self.env["project.project"].browse(project_id),
                    "opportunity",
                    "prepare",
                )
            ):
                msg = "Chưa có quyền lập hồ sơ dự án trong dự án này."
                raise AccessError(msg)
        return super().create(vals_list)

    def write(self, vals):
        if (
            "kd_bid_state" in vals
            and self.env.context.get("_kd_internal") is not _INTERNAL
        ):
            msg = "Dùng nút chuẩn bị hoặc khai báo nộp hồ sơ."
            raise UserError(msg)
        if not self.env.su and self.env.context.get('_kd_internal') is not _INTERNAL and (
            any(self.mapped("tp_project_id")) or any(k.startswith("kd_") for k in vals)
        ):
            self._kd_require()
            if vals.get("tp_project_id") and not self.env["tp.kd.grant"]._has(
                self.env["project.project"].browse(vals["tp_project_id"]),
                "opportunity",
                "prepare",
            ):
                msg = "Dự án đích ngoài quyền lập hồ sơ."
                raise AccessError(msg)
        return super().write(vals)

    def action_kd_prepare(self):
        self.ensure_one()
        self._kd_require()
        if self.kd_bid_state == "preparation":
            return True
        if self.kd_bid_state != "identified" or not all(
            [self.kd_source, self.kd_scope, self.kd_deadline, self.kd_checklist],
        ):
            msg = "Điền nguồn, phạm vi, hạn và checklist trước khi chuẩn bị."
            raise UserError(msg)
        self.with_context(_kd_internal=_INTERNAL).write({"kd_bid_state": "preparation"})
        return {"type": "ir.actions.client", "tag": "reload"}

    def action_kd_record_submission(self):
        self.ensure_one()
        self._kd_require('submit')
        if self.kd_bid_state == "submitted":
            return True
        if (
            self.kd_route != "bid"
            or self.kd_bid_state != "preparation"
            or not self.kd_receipt
        ):
            msg = "Hồ sơ đấu thầu cần ở bước chuẩn bị và có căn cứ khai báo nộp. Giao trực tiếp không cần khai báo nộp thầu."
            raise UserError(
                msg,
            )
        self.with_context(_kd_internal=_INTERNAL).write({"kd_bid_state": "submitted"})
        return {"type": "ir.actions.client", "tag": "reload"}


class Overview(models.TransientModel):
    _name = "tp.kd.overview"
    _description = "Tổng quan Kế hoạch Kinh doanh"

    name = fields.Char(default="Tổng quan KH-KD", readonly=True)

    project_id = fields.Many2one(
        "project.project",
        string="Dự án",
        domain="[('tp_managed', '=', True)]",
    )
    owner_id = fields.Many2one("res.users", string="Người phụ trách")
    date_from = fields.Date(string="Từ ngày")
    date_to = fields.Date(string="Đến ngày")

    def _domain(
        self,
        model,
        project_field="project_id",
        owner_field="owner_id",
        date_field="date",
    ):
        self.ensure_one()
        projects = self.env["project.project"].search([("tp_managed", "=", True)])
        if self.project_id:
            projects &= self.project_id
        domain = [(project_field, "in", projects.ids)]
        if model == 'crm.lead' and not self.project_id:
            domain = ['|', (project_field, 'in', projects.ids), (project_field, '=', False)]
        if self.owner_id and owner_field:
            domain.append((owner_field, "=", self.owner_id.id))
        if date_field:
            if self.date_from:
                domain.append((date_field, ">=", self.date_from))
            if self.date_to:
                domain.append((date_field, "<=", self.date_to))
        if self.date_from and self.date_to and self.date_to < self.date_from:
            msg = "Đến ngày phải từ ngày bắt đầu trở đi."
            raise UserError(msg)
        return domain

    def action_projects(self):
        self.ensure_one()
        return open_records(
            self.env,
            "project.project",
            [("tp_managed", "=", True)]
            + ([("id", "=", self.project_id.id)] if self.project_id else []),
            "Hồ sơ dự án",
            {
                "form_view_ref": "tp_kd_workspace.project_governance_form",
                "default_tp_managed": True,
            },
        )

    def action_opportunities(self):
        return open_records(
            self.env,
            "crm.lead",
            self._domain("crm.lead", "tp_project_id", "user_id", "kd_deadline"),
            "Hồ sơ dự án và hồ sơ thầu",
            {"form_view_ref": "tp_kd_workspace.opportunity_form"},
        )

    def action_contracts(self):
        action = self.env["ir.actions.actions"]._for_xml_id(
            "tp_contract.action_tp_contracts_list",
        )
        action.update(
            domain=self._domain(
                "tp.contract",
                owner_field="create_uid",
                date_field=False,
            ),
            context=dict(
                child_context(self.env),
                tp_can_create_contract=any(
                    "contract_draft_edit"
                    in self.env["tp.contract.workflow"]._tp_capabilities(
                        p,
                        p.tp_department_id,
                    )
                    for p in self.env["project.project"].search(
                        [("tp_managed", "=", True)],
                    )
                ),
                **kd_leaf("tp.contract"),
            ),
        )
        return action

    def action_tasks(self):
        return open_records(
            self.env,
            "project.task",
            self._domain(
                "project.task",
                owner_field="user_ids",
                date_field="date_deadline",
            ),
            "Kế hoạch và công việc",
        )
