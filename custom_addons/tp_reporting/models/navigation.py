"""Reporting navigation follows effective assignments without widening business access."""
from copy import deepcopy

from odoo import api, fields, models
from odoo.fields import Domain


class ReportingNavigationUser(models.Model):
    _inherit = 'res.users'

    def _tp_report_plan_read_domain(self, companies=None):
        self.ensure_one()
        companies = self.env.companies.ids if companies is None else companies
        self.env['tp.report.plan'].flush_model(['owner_id', 'company_id', 'parent_id', 'state'])
        # Return only published ancestors of work already assigned to this user.
        self.env.cr.execute('''
            WITH RECURSIVE ancestors(id, parent_id) AS (
                SELECT id, parent_id FROM tp_report_plan
                WHERE owner_id=%s AND company_id=ANY(%s) AND state='issued'
                UNION
                SELECT p.id, p.parent_id FROM tp_report_plan p
                JOIN ancestors a ON p.id=a.parent_id
                WHERE p.company_id=ANY(%s) AND p.state='issued'
            ) SELECT id FROM ancestors
        ''', [self.id, companies, companies])
        ids = [row[0] for row in self.env.cr.fetchall()]
        return list(Domain.OR([self._tp_report_domain(companies=companies), [('id', 'in', ids)]]))


class ReportingNavigationMenus(models.Model):
    _inherit = 'ir.ui.menu'

    @api.model
    def load_menus(self, debug):
        # Apply after Odoo's cached menu tree so expiry/revocation takes effect per request.
        result = deepcopy(super().load_menus(debug))
        if not self.env.user.has_group('tp_reporting.group_reporting_user'):
            return result
        today = fields.Date.context_today(self)
        assignments = self.env['tp.report.assignment'].search([
            ('user_id', '=', self.env.uid), ('active', '=', True),
            ('company_id', 'in', self.env.companies.ids), ('date_start', '<=', today),
            '|', ('date_end', '=', False), ('date_end', '>=', today),
            ('capability', 'in', ['read', 'review', 'finalize', 'consolidate']),
        ])
        hidden = set()
        for level, xmlid in [('department', 'tp_reporting.menu_department'),
                             ('company', 'tp_reporting.menu_company')]:
            if not assignments.filtered(lambda a: a.level in ('all', level) and
                                         (level != 'company' or not a.department_id)):
                menu = self.env.ref(xmlid, raise_if_not_found=False)
                hidden.update(menu.ids)
        for menu_id in hidden:
            result.pop(menu_id, None)
        for entry in result.values():
            entry['children'] = [menu_id for menu_id in entry['children'] if menu_id not in hidden]
        return result
