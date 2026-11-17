"""Delegated Reporting read scope outside the actor's own departments.

Every row must trace to a known company, department and owner outside the
actor's protected departments. Plans open only as whole trees; a report opens
only when its current lines, every immutable snapshot payload, carried/rolled-up
lines and dependencies trace to sources that are themselves open. Drafts stay
private to their author as in the baseline. Writes, review, finalize, finance,
obligations management and reporting assignments keep their baseline rules.
"""
from odoo import api, models
from odoo.exceptions import AccessError
from odoo.fields import Domain

from .business_scope import other_domain

READ_MODELS = frozenset({
    'tp.report.document', 'tp.report.plan', 'tp.report.line', 'tp.report.snapshot',
    'tp.report.obligation', 'tp.report.directive', 'tp.report.review', 'tp.report.event',
})
SOURCE_FIELDS = frozenset({'company_id', 'department_id', 'owner_id', 'document_id', 'plan_id', 'parent_id'})
# A valid scope with no rows yet must stay distinct from "no delegation" (Domain.FALSE),
# so entry points show an empty list instead of an AccessError.
EMPTY = [0]
DELEGATED_LABEL = 'Quản trị được ủy quyền: chỉ xem nguồn đã xác định ở phòng khác'
DELEGATED_NOTE = ('Quản trị được ủy quyền: số thực hiện chỉ cộng báo cáo đã gửi có nguồn mở cho bạn; '
                  'báo cáo nháp hoặc nguồn chung với phòng của bạn không được tính.')

# Lines and signed payload facts must point at open plans/projects/tasks.
UNTRACED_SOURCE_SQL = '''
    SELECT l.document_id FROM tp_report_line l
     WHERE l.document_id = ANY(%(docs)s) AND (
           (l.plan_id IS NOT NULL AND NOT (l.plan_id = ANY(%(plans)s)))
        OR (l.project_id IS NOT NULL AND NOT (l.project_id = ANY(%(projects)s)))
        OR (l.task_id IS NOT NULL AND NOT EXISTS (
                SELECT 1 FROM project_task t WHERE t.id = l.task_id AND t.project_id = ANY(%(projects)s))))
    UNION
    SELECT s.document_id FROM tp_report_snapshot s
      JOIN tp_report_document d ON d.id = s.document_id
     WHERE s.document_id = ANY(%(docs)s) AND (
           (s.payload::jsonb ->> 'company_id') IS DISTINCT FROM d.company_id::text
        OR (s.payload::jsonb ->> 'department_id') IS DISTINCT FROM d.department_id::text
        OR (s.payload::jsonb ->> 'owner_id') IS DISTINCT FROM d.owner_id::text)
    UNION
    SELECT s.document_id FROM tp_report_snapshot s
     CROSS JOIN LATERAL jsonb_array_elements(CASE WHEN jsonb_typeof(s.payload::jsonb -> 'lines') = 'array'
                                                  THEN s.payload::jsonb -> 'lines' ELSE '[]'::jsonb END) f
     WHERE s.document_id = ANY(%(docs)s) AND (
           (jsonb_typeof(f -> 'plan_id') = 'number' AND NOT ((f ->> 'plan_id')::int = ANY(%(plans)s)))
        OR (jsonb_typeof(f -> 'project_id') = 'number' AND NOT ((f ->> 'project_id')::int = ANY(%(projects)s)))
        OR (jsonb_typeof(f -> 'task_id') = 'number' AND NOT EXISTS (
                SELECT 1 FROM project_task t
                 WHERE t.id = (f ->> 'task_id')::int AND t.project_id = ANY(%(projects)s))))
'''
# (document, source document) edges; a NULL source means the origin cannot be traced.
SOURCE_EDGE_SQL = '''
    SELECT l.document_id, o.document_id FROM tp_report_line l
      LEFT JOIN tp_report_line o ON o.id = l.origin_line_id
     WHERE l.document_id = ANY(%(docs)s) AND (l.origin_line_id IS NOT NULL OR l.rollup_source IS TRUE)
    UNION
    SELECT r.document_id, s.document_id FROM tp_report_document_dependency_rel r
      LEFT JOIN tp_report_snapshot s ON s.id = r.snapshot_id
     WHERE r.document_id = ANY(%(docs)s)
    UNION
    SELECT s.document_id, dep.document_id FROM tp_report_snapshot s
     CROSS JOIN LATERAL jsonb_array_elements(CASE WHEN jsonb_typeof(s.payload::jsonb -> 'dependencies') = 'array'
                                                  THEN s.payload::jsonb -> 'dependencies' ELSE '[]'::jsonb END) f
      LEFT JOIN tp_report_snapshot dep ON dep.id = CASE WHEN jsonb_typeof(f -> 'id') = 'number'
                                                        THEN (f ->> 'id')::int END
     WHERE s.document_id = ANY(%(docs)s)
'''
PLAN_TREE_SQL = '''
    WITH RECURSIVE tree(id, root) AS (
        SELECT id, id FROM tp_report_plan WHERE parent_id IS NULL AND company_id = ANY(%s)
        UNION
        SELECT p.id, t.root FROM tp_report_plan p JOIN tree t ON p.parent_id = t.id
    ) SELECT id, root FROM tree
'''


class ReportScope(models.AbstractModel):
    _inherit = 'tp.report.scope.mixin'

    def _tp_delegated_owner_domain(self, field='owner_id'):
        """Owner is a current employee of a known department outside the actor's own ones."""
        permitted = []
        for company in self.env.companies:
            if not self.env.user._tp_has_admin_delegation(company):
                continue
            own, complete = self.env.user._tp_delegation_scope(company)
            if not complete:
                continue
            employees = self.env['hr.employee'].sudo().with_context(active_test=False)
            known = employees._search([
                ('company_id', '=', company.id), ('current_version_id.department_id', '!=', False),
                ('current_version_id.department_id', 'not in', own.ids),
            ])
            # Any linked employee without a department or inside the actor's own ones blocks the owner.
            blocked = employees._search([
                ('company_id', '=', company.id), '|', ('current_version_id.department_id', '=', False),
                ('current_version_id.department_id', 'in', own.ids),
            ])
            permitted.append(Domain('company_id', '=', company.id)
                             & Domain(field, 'in', known.subselect(known.table.user_id))
                             & ~Domain(field, 'in', blocked.subselect(blocked.table.user_id)))
        return Domain.OR(permitted) & Domain(field, '!=', self.env.uid)

    def _tp_delegated_base(self, department_fields=('department_id',)):
        domain = other_domain(self.env, 'company_id', list(department_fields))
        return domain if domain.is_false() else domain & self._tp_delegated_owner_domain()

    def _tp_delegated_project_ids(self):
        projects = self.env['project.project']
        domain = projects._tp_delegated_domain()
        return [] if domain.is_false() else projects.sudo().with_context(active_test=False).search(domain).ids

    def _tp_delegated_plan_ids(self, projects):
        node = self._tp_delegated_base()
        if node.is_false():
            return None
        node &= (Domain('project_id', '=', False) | Domain('project_id', 'in', projects)) & (
            Domain('task_id', '=', False) | Domain('task_id.project_id', 'in', projects))
        plans = self.env['tp.report.plan'].sudo().with_context(active_test=False)
        good = set(plans.search(node).ids)
        if not good:
            return []
        plans.flush_model(['parent_id', 'company_id'])
        self.env.cr.execute(PLAN_TREE_SQL, [self.env.companies.ids])
        rows = self.env.cr.fetchall()
        # One node in an own, unknown or other-company branch closes the whole tree.
        bad = {root for plan, root in rows if plan not in good}
        return sorted(plan for plan, root in rows if plan in good and root not in bad)

    def _tp_delegated_document_ids(self, plans, projects):
        base = self._tp_delegated_base()
        if base.is_false():
            return None
        documents = self.env['tp.report.document'].sudo().with_context(active_test=False)
        domain = base & Domain('value_ids', '=', False) & (
            Domain('project_id', '=', False) | Domain('project_id', 'in', projects)) & (
            (Domain('level', '=', 'personal') & Domain('state', 'not in', ['draft', 'returned']))
            | Domain('level', '=', 'department'))
        docs = set(documents.search(domain).ids)
        if not docs:
            return []
        for model in ('tp.report.document', 'tp.report.line', 'tp.report.snapshot'):
            self.env[model].flush_model()
        params = {'docs': sorted(docs), 'plans': plans or EMPTY, 'projects': projects or EMPTY}
        self.env.cr.execute(UNTRACED_SOURCE_SQL, params)
        docs -= {row[0] for row in self.env.cr.fetchall()}
        if not docs:
            return []
        self.env.cr.execute(SOURCE_EDGE_SQL, dict(params, docs=sorted(docs)))
        edges = self.env.cr.fetchall()
        while True:
            closed = {doc for doc, source in edges if doc in docs and source not in docs}
            if not closed:
                return sorted(docs)
            docs -= closed

    def _tp_delegated_report_domain(self, name=None):
        if self._tp_delegated_base().is_false():
            return Domain.FALSE
        name = name or self._name
        if name == 'tp.report.obligation':
            return self._tp_delegated_base()
        projects = self._tp_delegated_project_ids()
        open_projects = projects or EMPTY
        if name == 'tp.report.directive':
            return (self._tp_delegated_base(('department_id', 'document_id.department_id'))
                    & self._tp_delegated_owner_domain('document_id.owner_id')
                    & (Domain('project_id', '=', False) | Domain('project_id', 'in', open_projects))
                    & (Domain('task_id', '=', False) | Domain('task_id.project_id', 'in', open_projects)))
        plans = self._tp_delegated_plan_ids(projects) or []
        if name == 'tp.report.plan':
            return Domain('id', 'in', plans or EMPTY)
        docs = self._tp_delegated_document_ids(plans, projects) or EMPTY
        if name == 'tp.report.document':
            return Domain('id', 'in', docs)
        if name in ('tp.report.line', 'tp.report.snapshot', 'tp.report.section.content'):
            return Domain('document_id', 'in', docs)
        if name == 'tp.report.review':
            # Internal reviewer notes stay with the assigned reviewer.
            return Domain('audience', '=', 'published') & Domain('document_id', 'in', docs)
        if name == 'tp.report.event':
            return Domain('document_id', 'in', docs) | Domain('plan_id', 'in', plans or EMPTY)
        return Domain.FALSE

    def _access_domain(self, operation):
        baseline = super()._access_domain(operation)
        if operation == 'read' and self._name in READ_MODELS:
            return baseline | self._tp_delegated_report_domain()
        return baseline

    def write(self, vals):
        if set(vals) & SOURCE_FIELDS:
            for record in self:
                source = record.sudo()
                if self.env.user._tp_delegated_other_department(source.company_id, source.department_id, lock=True):
                    raise AccessError(self.env._('Chuyển nguồn hoặc phạm vi báo cáo cần quản trị chính.'))
        return super().write(vals)


class ReportSectionContent(models.Model):
    _inherit = 'tp.report.section.content'

    def _access_domain(self, operation):
        # Section text follows its document; only a live delegation adds rows, other users keep the baseline.
        baseline = super()._access_domain(operation)
        if operation != 'read':
            return baseline
        return baseline | self.env['tp.report.document']._tp_delegated_report_domain(self._name)


class ReportDashboard(models.AbstractModel):
    _inherit = 'tp.report.dashboard'

    @api.model
    def get_data(self, date_start, date_end, period_type='quarter', department_id=False):
        result = super().get_data(date_start, date_end, period_type, department_id)
        if not self.env['tp.report.document']._tp_delegated_base().is_false():
            result['scope_label'] = '%s · %s' % (result['scope_label'], DELEGATED_LABEL)
            result['delegated_scope'] = DELEGATED_LABEL
            result['notes'] = [*result['notes'], DELEGATED_NOTE]
        return result
