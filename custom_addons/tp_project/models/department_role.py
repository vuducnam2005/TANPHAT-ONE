"""Explicit, live department responsibility; this role never grants Settings access."""

import json

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.fields import Domain


class DepartmentRole(models.Model):
    _name = 'tp.kd.department.role'
    _description = 'KH-KD Department Head Responsibility'
    _check_company_auto = True

    user_id = fields.Many2one('res.users', required=True, ondelete='restrict', index=True)
    company_id = fields.Many2one('res.company', required=True, ondelete='restrict', index=True)
    department_id = fields.Many2one('hr.department', required=True, ondelete='restrict', check_company=True, index=True)
    active = fields.Boolean(default=True)
    date_start = fields.Date(required=True, default=fields.Date.context_today)
    date_end = fields.Date()
    reason = fields.Text(required=True)
    provisioned_by_id = fields.Many2one('res.users', required=True, default=lambda self: self.env.user, ondelete='restrict')

    _unique_active_role = models.UniqueIndex(
        '(user_id, company_id, department_id) WHERE active IS TRUE',
        'The user already holds an active responsibility for this department.',
    )

    @api.constrains('user_id', 'company_id', 'department_id', 'date_start', 'date_end', 'reason')
    def _check_scope(self):
        for role in self:
            if (role.department_id.company_id != role.company_id
                    or role.company_id not in role.user_id.company_ids
                    or not role.user_id.has_group('tp_core.group_user')
                    or not (role.reason or '').strip()
                    or (role.date_end and role.date_end < role.date_start)):
                raise ValidationError(self.env._('HEAD responsibility needs a platform user, matching company/department, valid dates and a reason.'))

    def _snapshot(self):
        self.ensure_one()
        return {key: (self[key].id if self._fields[key].type == 'many2one' else self[key])
                for key in ('user_id', 'company_id', 'department_id', 'active', 'date_start', 'date_end', 'reason', 'provisioned_by_id')}

    def _audit(self, before=None):
        for role in self:
            self.env['tp.kd.department.role.event'].sudo().create({
                'role_id': role.id, 'actor_id': self.env.uid,
                'before': json.dumps((before or {}).get(role.id), default=str, ensure_ascii=False),
                'after': json.dumps(role._snapshot(), default=str, ensure_ascii=False),
                'reason': role.reason,
            })

    def _invalidate_scope(self):
        self.env.flush_all()
        self.env.invalidate_all()
        self.env.transaction.invalidate_access_cache()

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.su:
            raise AccessError(self.env._('Only an authorized superuser operation may provision HEAD responsibility.'))
        roles = super().create(vals_list)
        roles._audit()
        roles._invalidate_scope()
        return roles

    def write(self, vals):
        if not self.env.su:
            raise AccessError(self.env._('Only an authorized superuser operation may change HEAD responsibility.'))
        if set(vals) & {'user_id', 'company_id', 'department_id', 'provisioned_by_id'}:
            raise UserError(self.env._('Revoke the existing responsibility and provision a new scope; do not rewrite its identity.'))
        if not (vals.get('reason') or '').strip():
            raise ValidationError(self.env._('Changing or revoking HEAD responsibility requires a reason.'))
        before = {role.id: role._snapshot() for role in self}
        result = super().write(vals)
        self._audit(before)
        self._invalidate_scope()
        return result

    def unlink(self):
        raise UserError(self.env._('HEAD responsibility and its history are retained; revoke it with a reason.'))

    @api.model
    def _live_domain(self, user=None):
        user = user or self.env.user
        today = fields.Date.context_today(self)
        if not user.active or not user.has_group('tp_core.group_user'):
            return Domain.FALSE
        companies = user.company_ids
        if user.id == self.env.uid:
            companies &= self.env.companies
        return Domain([
            ('user_id', '=', user.id), ('company_id', 'in', companies.ids),
            ('active', '=', True), ('date_start', '<=', today),
        ]) & (Domain('date_end', '=', False) | Domain('date_end', '>=', today))

    @api.model
    def _roles(self, user=None):
        return self.sudo().search(self._live_domain(user))

    @api.model
    def _is_head(self, project=None, department=None, company=None, user=None):
        if project:
            project = project.sudo()
            if not project.tp_managed or not project.tp_department_id:
                return False
            if (department and department != project.tp_department_id) or (company and company != project.company_id):
                return False
            department, company = project.tp_department_id, project.company_id
        roles = self._roles(user)
        return any((not department or role.department_id == department)
                   and (not company or role.company_id == company) for role in roles)

    @api.model
    def _project_ids(self, user=None):
        roles = self._roles(user)
        scope = Domain.OR(Domain([('tp_department_id', '=', role.department_id.id), ('company_id', '=', role.company_id.id)])
                          for role in roles)
        return self.env['project.project'].sudo().with_context(active_test=False).search(Domain('tp_managed', '=', True) & scope).ids

    @api.model
    def _team_ids(self, user=None):
        # CRM extends this hook; tp_project also works without the KH-KD addon.
        return []

    @api.model
    def _head_users(self, project):
        project = project.sudo()
        if not project.tp_managed or not project.tp_department_id:
            return self.env['res.users'].browse()
        roles = self.sudo().search([
            ('company_id', '=', project.company_id.id), ('department_id', '=', project.tp_department_id.id),
        ])
        return roles.user_id.filtered(lambda user: self._is_head(project=project, user=user))


class DepartmentRoleEvent(models.Model):
    _name = 'tp.kd.department.role.event'
    _description = 'Department Responsibility Provisioning History'
    _order = 'id'

    role_id = fields.Many2one('tp.kd.department.role', required=True, ondelete='restrict', index=True)
    actor_id = fields.Many2one('res.users', required=True, ondelete='restrict')
    acted_at = fields.Datetime(required=True, default=fields.Datetime.now)
    before = fields.Text(required=True)
    after = fields.Text(required=True)
    reason = fields.Text(required=True)

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.su:
            raise AccessError(self.env._('Responsibility history is written by provisioning operations.'))
        return super().create(vals_list)

    def write(self, vals):
        raise UserError(self.env._('Responsibility history is append-only.'))

    def unlink(self):
        raise UserError(self.env._('Responsibility history is append-only.'))
