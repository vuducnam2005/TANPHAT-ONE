from collections import defaultdict
from decimal import Decimal

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError
from odoo.tools.misc import format_amount

from odoo.addons.tp_demo_workspace import demo_catalog as catalog

VIEWER_GROUP = 'tp_demo_workspace.group_demo_viewer'
BUSINESS_GROUP = 'tp_demo_workspace.group_demo_business'
DEMO_TASK_DOMAIN = [('project_id.tp_managed', '=', True), ('project_id.tp_code', '=like', 'DEMO-%')]
REVIEW_CYCLE_STATES = ['draft', 'in_review', 'returned']
AMOUNT_STATUS_LABELS = {
    'confirmed': 'Đã xác nhận',
    'incomplete': 'Chưa đủ số tiền xác nhận',
    'mixed_basis': 'Lẫn cơ sở thuế, không cộng',
    'empty': 'Chưa có dòng phạm vi',
}
TAX_BASIS_LABELS = {
    'excluding_tax': 'Chưa thuế',
    'including_tax': 'Gồm thuế',
    'unknown': 'Chưa xác định cơ sở thuế',
    'mixed': 'Lẫn cơ sở thuế',
}


class TpDemoWorkspace(models.AbstractModel):
    """Read projection behind the UI-DEMO-001 client actions.

    Every method reads through the caller's own environment, so company,
    project assignment and financial.read rules of the canonical models decide
    what comes back. Results are allowlisted dictionaries; money leaves the
    server only as strings formatted by Odoo for the record currency.
    """

    _name = 'tp.demo.workspace'
    _description = 'TANPHAT ONE Demo Workspace Projection'

    # ------------------------------------------------------------------ public

    @api.model
    @api.readonly
    def get_dashboard(self):
        self._check_viewer()
        business = self._is_business()
        projects = self._projects()
        Task = self.env['project.task']
        Revision = self.env['tp.contract.revision']
        now = fields.Datetime.to_string(fields.Datetime.now())

        kpis = [
            self._kpi('projects', 'Dự án đang theo dõi', 'project.project', catalog.PROJECT_DOMAIN,
                      'tp_demo_workspace.action_demo_projects', 'Dự án DEMO bạn được giao'),
            self._kpi('open_tasks', 'Công việc đang mở', 'project.task', DEMO_TASK_DOMAIN + [('is_closed', '=', False)],
                      'tp_demo_workspace.action_demo_tasks', 'Chưa ở giai đoạn hoàn thành'),
            self._kpi('overdue_tasks', 'Công việc quá hạn', 'project.task',
                      DEMO_TASK_DOMAIN + [('is_closed', '=', False), ('date_deadline', '<', now)],
                      'tp_demo_workspace.action_demo_tasks', 'Hạn đã qua, chưa hoàn thành', attention=True),
            self._kpi('reviews', 'Phiên bản HĐ đang rà soát', 'tp.contract.revision',
                      [('project_id.tp_code', '=like', 'DEMO-%'), ('review_state', 'in', REVIEW_CYCLE_STATES)],
                      'tp_demo_workspace.action_demo_revisions', 'Nháp, chờ rà soát hoặc bị trả lại'),
            self._kpi('documents', 'Tài liệu hồ sơ', 'tp.contract.document', [('project_id.tp_code', '=like', 'DEMO-%')],
                      'tp_demo_workspace.action_demo_documents', 'Chỉ đếm tài liệu bạn được xem'),
        ]
        if business:
            kpis.append(self._kpi('opportunities', 'Cơ hội đang mở', 'crm.lead',
                                  [('type', '=', 'opportunity'), ('name', 'ilike', '(DEMO)'), ('stage_id.is_won', '=', False)],
                                  'tp_demo_workspace.action_demo_crm', 'Phễu kinh doanh CRM'))

        chains = []
        for project in projects:
            project_domain = [('project_id', '=', project.id)]
            nodes = []
            if business and project.partner_id:
                nodes.append(self._node('opportunity', 'Cơ hội cùng khách hàng', 'crm.lead',
                                        [('type', '=', 'opportunity'), ('partner_id', '=', project.partner_id.id)],
                                        'tp_demo_workspace.action_demo_crm', nature='illustrative',
                                        note='Liên kết minh họa theo cùng khách hàng, chưa có liên kết dữ liệu'))
            nodes.append({'key': 'project', 'label': 'Dự án', 'count': None, 'nature': 'real', 'overview': project.id})
            nodes.append(self._node('contracts', 'Hợp đồng', 'tp.contract', project_domain,
                                    'tp_demo_workspace.action_demo_contracts'))
            nodes.append(self._node('tasks', 'Công việc mở', 'project.task', project_domain + [('is_closed', '=', False)],
                                    'tp_demo_workspace.action_demo_tasks'))
            nodes.append(self._node('documents', 'Tài liệu', 'tp.contract.document', project_domain,
                                    'tp_demo_workspace.action_demo_documents'))
            chains.append({
                'id': project.id,
                'code': project.tp_code,
                'name': project.name,
                'partner': project.partner_id.display_name or '',
                'department': project.tp_department_id.display_name or '',
                'nodes': nodes,
            })

        attention = []
        for revision in Revision.search([('project_id', 'in', projects.ids), ('review_state', '=', 'returned')]):
            submission = revision.submission_ids.sorted('id')[-1:]
            attention.append({
                'key': f'returned-{revision.id}',
                'severity': 'warning',
                'title': f'{revision.contract_id.code} bị trả lại để sửa',
                'detail': submission.return_reason or 'Chưa ghi lý do',
                'project': revision.project_id.tp_code,
                'res_model': 'tp.contract.revision',
                'res_id': revision.id,
            })
        for revision in Revision.search([('project_id', 'in', projects.ids), ('review_state', '=', 'in_review')]):
            attention.append({
                'key': f'review-{revision.id}',
                'severity': 'info',
                'title': f'{revision.contract_id.code} đang chờ rà soát thương mại',
                'detail': revision.name,
                'project': revision.project_id.tp_code,
                'res_model': 'tp.contract.revision',
                'res_id': revision.id,
            })
        today = fields.Date.context_today(self)
        overdue = Task.search(DEMO_TASK_DOMAIN + [('is_closed', '=', False), ('date_deadline', '<', now)],
                              order='date_deadline', limit=4)
        for task in overdue:
            days = (today - fields.Date.context_today(self, task.date_deadline)).days
            attention.append({
                'key': f'task-{task.id}',
                'severity': 'warning',
                'title': f'Quá hạn {days} ngày: {task.name}',
                'detail': ', '.join(task.user_ids.mapped('name')) or 'Chưa giao người phụ trách',
                'project': task.project_id.tp_code,
                'res_model': 'project.task',
                'res_id': task.id,
            })
        unassigned = Task.search_count(DEMO_TASK_DOMAIN + [('is_closed', '=', False), ('user_ids', '=', False)])
        if unassigned:
            attention.append({
                'key': 'unassigned',
                'severity': 'info',
                'title': f'{unassigned} công việc chưa giao người phụ trách',
                'detail': 'Mở danh sách để phân công trong TP Tasks',
                'project': '',
                'action': 'tp_demo_workspace.action_demo_tasks',
                'domain': DEMO_TASK_DOMAIN + [('is_closed', '=', False), ('user_ids', '=', False)],
            })

        return {
            'viewer': {
                'name': self.env.user.name,
                'project_count': len(projects),
                'financial_project_count': len(projects.filtered('tp_financial_read_granted')),
                'business': business,
            },
            'labels': {'environment': catalog.ENVIRONMENT_LABEL, 'illustrative': catalog.ILLUSTRATIVE_LABEL},
            'lenses': [
                {'key': lens['key'], 'label': lens['label'], 'order': lens['order']}
                for lens in catalog.LENSES if business or not lens.get('business')
            ],
            'kpis': kpis,
            'chains': chains,
            'attention': attention,
            'lanes': self._lanes(business),
        }

    @api.model
    @api.readonly
    def get_project_overview(self, project_id=None):
        self._check_viewer()
        business = self._is_business()
        projects = self._projects()
        picker = [{'id': p.id, 'code': p.tp_code, 'name': p.name} for p in projects]
        project = projects.filtered(lambda p: p.id == project_id) if project_id else projects[:1]
        if not project:
            return {'projects': picker, 'project': None, 'denied': bool(project_id)}

        granted = project.tp_financial_read_granted
        project_domain = [('project_id', '=', project.id)]
        contracts = []
        for contract in self.env['tp.contract'].search(project_domain, order='code'):
            revision = contract.revision_ids.sorted('sequence')[-1:]
            contracts.append({
                'id': contract.id,
                'code': contract.code,
                'name': contract.name,
                'partner': contract.partner_id.display_name or '',
                'contract_type': self._selection_label(contract, 'contract_type'),
                'lifecycle_state': contract.lifecycle_state,
                'lifecycle_label': self._selection_label(contract, 'lifecycle_state'),
                'legacy': contract.legacy_unverified,
                'revision': self._revision_summary(revision, granted) if revision else None,
            })

        Task = self.env['project.task']
        task_groups = Task._read_group(project_domain, ['stage_id'], ['__count'], order='stage_id')
        now = fields.Datetime.now()
        tasks = []
        for task in Task.search(project_domain + [('is_closed', '=', False)], order='date_deadline, id', limit=8):
            tasks.append({
                'id': task.id,
                'name': task.name,
                'stage': task.stage_id.name or '',
                'deadline': fields.Date.to_string(fields.Date.context_today(self, task.date_deadline)) if task.date_deadline else '',
                'overdue': bool(task.date_deadline and task.date_deadline < now),
                'assignees': ', '.join(task.user_ids.mapped('name')),
            })

        documents = [
            {
                'id': document.id,
                'name': document.name,
                'kind': self._selection_label(document, 'document_kind'),
                'confidentiality': document.confidentiality,
                'confidentiality_label': self._selection_label(document, 'confidentiality'),
                'contract': document.contract_id.code,
            }
            for document in self.env['tp.contract.document'].search(project_domain)
        ]

        opportunities = []
        if business and project.partner_id:
            opportunities = [
                {'id': lead.id, 'name': lead.name, 'stage': lead.stage_id.name or ''}
                for lead in self.env['crm.lead'].search(
                    [('type', '=', 'opportunity'), ('partner_id', '=', project.partner_id.id)], limit=5)
            ]

        illustrative = {
            screen: [
                {'key': row['key'], 'name': row['name'], 'status': row['status'][1]}
                for row in catalog.ROWS[screen] if row['project'] == project.tp_code
            ]
            for screen in ('survey', 'design')
        }

        return {
            'projects': picker,
            'denied': False,
            'project': {
                'id': project.id,
                'code': project.tp_code,
                'name': project.name,
                'partner': project.partner_id.display_name or '',
                'department': project.tp_department_id.display_name or '',
                'manager': project.user_id.name or '',
                'date_start': fields.Date.to_string(project.date_start) if project.date_start else '',
                'date_end': fields.Date.to_string(project.date) if project.date else '',
                'financial_read': granted,
            },
            'contracts': contracts,
            'task_stages': [{'stage': stage.name or 'Chưa có giai đoạn', 'count': count} for stage, count in task_groups],
            'tasks': tasks,
            'documents': documents,
            'opportunities': opportunities,
            'illustrative': illustrative,
            'actions': {
                'contracts': {'action': 'tp_demo_workspace.action_demo_contracts', 'domain': project_domain},
                'tasks': {'action': 'tp_demo_workspace.action_demo_tasks', 'domain': project_domain},
                'documents': {'action': 'tp_demo_workspace.action_demo_documents', 'domain': project_domain},
                'project': {'res_model': 'project.project', 'res_id': project.id},
            },
            'business': business,
        }

    @api.model
    @api.readonly
    def get_contract_flow(self):
        self._check_viewer()
        projects = self._projects()
        Revision = self.env['tp.contract.revision']
        Contract = self.env['tp.contract']
        scope = [('project_id', 'in', projects.ids)]
        review_counts = dict(Revision._read_group(scope, ['review_state'], ['__count']))
        lifecycle_counts = dict(Contract._read_group(scope, ['lifecycle_state'], ['__count']))
        review_labels = dict(Revision._fields['review_state']._description_selection(self.env))
        lifecycle_labels = dict(Contract._fields['lifecycle_state']._description_selection(self.env))

        revisions = []
        for revision in Revision.search(scope, order='project_id, contract_id, sequence'):
            submission = revision.submission_ids.sorted('id')[-1:]
            revisions.append({
                'id': revision.id,
                'contract': revision.contract_id.code,
                'project': revision.project_id.tp_code,
                'name': revision.name,
                'review_state': revision.review_state,
                'review_label': review_labels.get(revision.review_state, ''),
                'lifecycle_label': lifecycle_labels.get(revision.contract_id.lifecycle_state, ''),
                'legacy': revision.legacy_unverified,
                'submitted_by': submission.submitted_by_id.name or '',
                'reviewer': submission.reviewer_id.name or '',
                'return_reason': (submission.return_reason or '') if revision.review_state == 'returned' else '',
            })

        return {
            'review_states': [
                {'key': key, 'label': review_labels[key], 'count': review_counts.get(key, 0),
                 'in_demo': key in REVIEW_CYCLE_STATES}
                for key in ('draft', 'in_review', 'returned', 'review_complete', 'cancelled')
            ],
            'lifecycle_states': [
                {'key': key, 'label': label, 'count': lifecycle_counts.get(key, 0)}
                for key, label in lifecycle_labels.items()
            ],
            'transitions': [
                {'from': 'draft', 'to': 'in_review', 'action': 'Gửi rà soát', 'actor': 'Người lập: contract.submit + financial.read', 'in_demo': True},
                {'from': 'in_review', 'to': 'returned', 'action': 'Trả lại kèm lý do', 'actor': 'Người rà soát thương mại khác người gửi', 'in_demo': True},
                {'from': 'returned', 'to': 'draft', 'action': 'Mở lại để sửa', 'actor': 'Người lập: contract.draft_edit', 'in_demo': True},
                {'from': 'in_review', 'to': 'review_complete', 'action': 'Hoàn tất rà soát', 'actor': 'Chưa mở trong CTR-002a', 'in_demo': False},
            ],
            'layers': [
                {'title': 'Rà soát nội bộ TANPHAT ONE', 'state': 'Đang có trong demo',
                 'detail': 'Nháp → chờ rà soát → trả lại → sửa lại; trạng thái do action backend đổi, có lịch sử và kiểm phiên bản.'},
                {'title': 'Phê duyệt trên BASE', 'state': 'Ngoài phạm vi demo',
                 'detail': 'BASE vẫn là nơi duyệt chính thức; TANPHAT ONE chỉ ghi nhận kết quả và bằng chứng.'},
                {'title': 'Ký và hiệu lực', 'state': 'Ngoài phạm vi demo',
                 'detail': 'Ký, thẩm quyền ký và hiệu lực là trạng thái riêng, không suy ra từ rà soát hay BASE.'},
                {'title': 'Vòng đời hợp đồng', 'state': 'Chỉ đọc',
                 'detail': 'Hiệu lực, tạm dừng, hoàn thành, thanh lý: tách khỏi trạng thái rà soát phiên bản.'},
            ],
            'revisions': revisions,
            'action': 'tp_demo_workspace.action_demo_revisions',
        }

    @api.model
    @api.readonly
    def get_showcase(self, screen, project_id=None):
        self._check_viewer()
        meta = catalog.SCREENS.get(screen)
        if not meta:
            raise UserError(self.env._('Unknown demo screen.'))
        if screen == 'bid':
            self._check_viewer(business=True)
        projects = self._projects()
        by_code = {project.tp_code: project for project in projects}
        selected = projects.filtered(lambda p: p.id == project_id) if project_id else projects.browse()
        currency = self.env.company.currency_id

        rows = []
        for row in catalog.ROWS[screen]:
            project = by_code.get(row['project']) if row['project'] else None
            if row['project'] and not project:
                continue
            if selected and project != selected:
                continue
            columns = dict(row['columns'])
            if screen == 'request':
                if 'amount' not in row:
                    columns['amount'] = '—'
                elif project.tp_financial_read_granted:
                    columns['amount'] = format_amount(self.env, float(Decimal(row['amount'])), currency)
                else:
                    columns['amount'] = 'Cần quyền financial.read'
            rows.append({
                'key': row['key'],
                'name': row['name'],
                'project': project.tp_code if project else '',
                'project_name': project.name if project else '',
                'status': row['status'][0],
                'status_label': row['status'][1],
                'columns': columns,
                'sections': [dict(section) for section in row['sections']],
                'steps': [{'label': label, 'state': state} for label, state in row.get('steps', [])],
            })

        return {
            'screen': screen,
            'module': meta['module'],
            'title': meta['title'],
            'purpose': meta['purpose'],
            'columns': [{'key': key, 'label': label} for key, label in meta['columns']],
            'out_of_scope': list(meta['out_of_scope']),
            'label': catalog.ILLUSTRATIVE_LABEL,
            'projects': [] if screen == 'bid' else [{'id': p.id, 'code': p.tp_code, 'name': p.name} for p in projects],
            'selected_project_id': selected.id or False,
            'rows': rows,
        }

    @api.model
    @api.readonly
    def get_finance(self):
        self._check_viewer()
        projects = self._projects()
        result = []
        for project in projects:
            contracts = self.env['tp.contract'].search([('project_id', '=', project.id)], order='code')
            if not project.tp_financial_read_granted:
                result.append({
                    'id': project.id, 'code': project.tp_code, 'name': project.name,
                    'financial_read': False, 'contract_count': len(contracts), 'rows': [], 'totals': [],
                })
                continue
            rows = []
            totals = defaultdict(Decimal)
            for contract in contracts:
                revision = contract.revision_ids.sorted('sequence')[-1:]
                summary = revision._amount_summary() if revision else None
                currency = contract.currency_id
                illustration = catalog.FINANCE_ILLUSTRATION.get(contract.code, {})
                value = summary['value'] if summary else None
                if value is not None and revision.review_state == 'review_complete':
                    totals[currency] += value
                rows.append({
                    'id': contract.id,
                    'code': contract.code,
                    'name': contract.name,
                    'currency': currency.name,
                    'revision': revision.name if revision else '',
                    'review_label': self._selection_label(revision, 'review_state') if revision else '',
                    'reviewed': bool(revision) and revision.review_state == 'review_complete',
                    'value': self._money(value, currency),
                    'value_status': AMOUNT_STATUS_LABELS.get(summary['status'], '') if summary else 'Chưa có phiên bản',
                    'tax_basis': TAX_BASIS_LABELS.get(summary['tax_basis'], '') if summary else '',
                    'accepted': self._money(illustration.get('accepted'), currency),
                    'collected': self._money(illustration.get('collected'), currency),
                })
            result.append({
                'id': project.id, 'code': project.tp_code, 'name': project.name,
                'financial_read': True, 'contract_count': len(contracts), 'rows': rows,
                'totals': [{'currency': currency.name, 'value': self._money(value, currency)}
                           for currency, value in totals.items()],
            })
        return {
            'projects': result,
            'sources': [dict(source) for source in catalog.FINANCE_SOURCES],
            'label': catalog.ILLUSTRATIVE_LABEL,
        }

    # ----------------------------------------------------------------- helpers

    def _check_viewer(self, business=False):
        if not self.env.user.has_group(VIEWER_GROUP):
            raise AccessError(self.env._('The demo workspace is only available to demo viewers.'))
        if business and not self._is_business():
            raise AccessError(self.env._('This demo screen requires the demo business viewer group.'))

    def _is_business(self):
        return self.env.user.has_group(BUSINESS_GROUP)

    def _projects(self):
        return self.env['project.project'].search(catalog.PROJECT_DOMAIN, order='tp_code')

    def _kpi(self, key, label, model, domain, action, hint, attention=False):
        return {
            'key': key, 'label': label, 'hint': hint, 'attention': attention,
            'value': self.env[model].search_count(domain), 'action': action, 'domain': domain,
        }

    def _node(self, key, label, model, domain, action, nature='real', note=''):
        return {
            'key': key, 'label': label, 'nature': nature, 'note': note,
            'count': self.env[model].search_count(domain), 'action': action, 'domain': domain,
        }

    def _lanes(self, business):
        lanes = []
        for lane in catalog.LANES:
            modules = []
            for key in lane['modules']:
                module = catalog.MODULES[key]
                locked = bool(module.get('business')) and not business
                modules.append({
                    'key': key,
                    'name': module['name'],
                    'purpose': module['purpose'],
                    'nature': module['nature'],
                    'source': module['source'],
                    'locked': locked,
                    'action': False if locked else module['action'],
                })
            lanes.append({'key': lane['key'], 'label': lane['label'], 'modules': modules})
        return lanes

    def _revision_summary(self, revision, granted):
        summary = revision._amount_summary() if granted else None
        currency = revision.contract_id.currency_id
        return {
            'id': revision.id,
            'name': revision.name,
            'review_state': revision.review_state,
            'review_label': self._selection_label(revision, 'review_state'),
            'signature_label': self._selection_label(revision, 'signature_status'),
            'effectivity_label': self._selection_label(revision, 'effectivity_status'),
            'value': self._money(summary['value'], currency) if summary else None,
            'value_status': AMOUNT_STATUS_LABELS.get(summary['status'], '') if summary else '',
        }

    def _money(self, value, currency):
        if value is None:
            return None
        return format_amount(self.env, float(Decimal(value)), currency)

    def _selection_label(self, record, field_name):
        return dict(record._fields[field_name]._description_selection(self.env)).get(record[field_name], '')
