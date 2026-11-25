# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
"""H7 & I2: Executive Dashboard & 11 Separated Management Financial Metrics (Never Faking 0 for Missing Data)."""
from odoo import _, api, fields, models
from odoo.exceptions import AccessError, ValidationError

from odoo.addons.tp_request.models.request_common import (
    format_dt_local,
    is_live_admin_user,
)

# Strictly separated 11+ financial concepts per Section I2 & Baseline Doc
FINANCIAL_METRIC_KINDS = [
    ('contract_value', '1. Giá trị hợp đồng đã ký'),
    ('allocated_value', '2. Giá trị giao khoán / thầu phụ'),
    ('executed_output', '3. Sản lượng thực hiện ước tính'),
    ('accepted_value', '4. Giá trị nghiệm thu xác nhận'),
    ('payment_request_value', '5. Giá trị đề nghị thanh toán'),
    ('invoiced_value', '6. Giá trị hóa đơn phát hành'),
    ('accounting_revenue', '7. Doanh thu kế toán ghi nhận'),
    ('cash_in', '8. Tiền về thực tế'),
    ('cash_out', '9. Tiền chi thực tế'),
    ('receivable_payable', '10. Công nợ phải thu / phải trả ròng'),
    ('estimated_cost', '11a. Chi phí dự kiến'),
    ('confirmed_cost', '11b. Chi phí đã xác nhận chứng từ'),
]

FIN_DATA_STATES = [
    ('unconfirmed', 'Tạm tính / Chưa xác nhận'),
    ('confirmed', 'Đã xác nhận nguồn chứng từ'),
]


class TpFinancialSummaryEntry(models.Model):
    _name = 'tp.financial.summary.entry'
    _description = 'Chỉ tiêu Tài chính Quản trị có nguồn chứng minh (11 khái niệm tách biệt)'
    _order = 'period_label desc, id desc'

    company_id = fields.Many2one('res.company', required=True, default=lambda s: s.env.company, index=True)
    project_id = fields.Many2one('project.project', string='Dự án', ondelete='restrict', index=True)
    department_id = fields.Many2one('hr.department', string='Đơn vị / Phòng ban', ondelete='restrict', index=True)
    contract_id = fields.Many2one('tp.contract', string='Hợp đồng liên quan', ondelete='set null')
    period_label = fields.Char(string='Kỳ dữ liệu (YYYY-MM / YYYY-Q#)', required=True, index=True)
    metric_kind = fields.Selection(FINANCIAL_METRIC_KINDS, string='Chỉ tiêu tài chính', required=True, index=True)
    currency_id = fields.Many2one('res.currency', required=True, default=lambda s: s.env.company.currency_id)
    amount = fields.Monetary(currency_field='currency_id', string='Giá trị (VNĐ)', required=True)
    data_state = fields.Selection(FIN_DATA_STATES, default='unconfirmed', required=True, index=True)
    source_ref = fields.Char(string='Nguồn / Chứng từ gốc', required=True)
    note = fields.Text(string='Ghi chú giải trình')
    recorded_by_id = fields.Many2one('res.users', default=lambda s: s.env.user, readonly=True)

    @api.constrains('period_label', 'source_ref')
    def _check_provenance(self):
        for rec in self:
            if not (rec.period_label or '').strip() or not (rec.source_ref or '').strip():
                raise ValidationError(_('Mọi chỉ tiêu tài chính quản trị bắt buộc phải có Kỳ dữ liệu và Nguồn chứng từ gốc.'))

    @api.model
    def _tp_can_read_executive_finance(self, user=None):
        user = user or self.env.user
        if is_live_admin_user(user, company=self.env.company):
            return True
        if user.has_group('tp_reporting.group_reporting_finance'):
            return True
        return False

    @api.model
    def tp_record_financial_entry(self, payload):
        if not self._tp_can_read_executive_finance(self.env.user):
            raise AccessError(_('Chỉ Ban Giám đốc (Admin) hoặc Cán bộ Tài chính được phân quyền mới được cập nhật chỉ tiêu tài chính quản trị.'))
        payload = payload or {}
        field_errors = []
        if not (payload.get('period_label') or '').strip():
            field_errors.append({
                'id': 'fin_period',
                'label': 'Kỳ dữ liệu',
                'location': 'Chỉ tiêu tài chính',
                'message': 'Vui lòng nhập Kỳ dữ liệu (ví dụ: 2026-11 hoặc 2026-Q4).',
            })
        if not (payload.get('source_ref') or '').strip():
            field_errors.append({
                'id': 'fin_source',
                'label': 'Nguồn chứng từ',
                'location': 'Chỉ tiêu tài chính',
                'message': 'Vui lòng nhập Nguồn chứng từ gốc (số hợp đồng, biên bản nghiệm thu, sổ kế toán...).',
            })
        if payload.get('amount') is None or str(payload.get('amount')).strip() == '':
            field_errors.append({
                'id': 'fin_amount',
                'label': 'Giá trị số tiền',
                'location': 'Chỉ tiêu tài chính',
                'message': 'Vui lòng nhập Giá trị hợp lệ.',
            })
        if field_errors:
            return {'ok': False, 'field_errors': field_errors}

        rec = self.create({
            'project_id': int(payload['project_id']) if int(payload.get('project_id') or 0) > 0 else False,
            'department_id': int(payload['department_id']) if int(payload.get('department_id') or 0) > 0 else False,
            'period_label': payload['period_label'].strip(),
            'metric_kind': payload.get('metric_kind') or 'contract_value',
            'amount': float(payload['amount']),
            'data_state': payload.get('data_state') or 'confirmed',
            'source_ref': payload['source_ref'].strip(),
            'note': (payload.get('note') or '').strip() or False,
        })
        return {'ok': True, 'id': rec.id}

    @api.model
    def tp_get_executive_dashboard_data(self, period_filter=''):
        """Executive Leadership Dashboard — real DB metrics, full tooltips, NEVER inventing 0 for missing finance."""
        company = self.env.company
        user = self.env.user
        is_admin = is_live_admin_user(user, company=company)
        can_finance = self._tp_can_read_executive_finance(user)
        if not (is_admin or can_finance or user.has_group('tp_core.group_manager')):
            raise AccessError(_('Màn hình Điều hành Lãnh đạo chỉ dành cho Ban Giám đốc và Quản lý được phân quyền.'))

        # 1. Project Portfolio & Critical Path Overview
        projs = self.env['project.project'].search([('company_id', '=', company.id)], limit=200)
        project_cards = []
        for p in projs[:15]:
            crit_count = self.env['project.task'].sudo().search_count([
                ('project_id', '=', p.id),
                ('tp_is_critical_path', '=', True),
                ('state', 'not in', ('1_done', '1_canceled')),
            ])
            project_cards.append({
                'id': p.id,
                'code': p.tp_code or f'PRJ-{p.id}',
                'name': p.name,
                'department_name': p.tp_department_id.sudo().name if p.tp_department_id else '—',
                'weighted_progress_pct': p.tp_weighted_progress_pct,
                'cpm_ready': p.tp_cpm_data_ready,
                'cpm_duration_days': p.tp_cpm_duration_days,
                'open_critical_tasks': crit_count,
                'drilldown_url': '/app/du-an/wbs-tien-do',
            })

        # 2. Operational Bottlenecks (Pending Requests, Overdue Requests, Unacked Announcements, Broken/Alert Gear)
        Req = self.env['tp.request'].sudo()
        pending_requests = Req.search_count([('company_id', '=', company.id), ('approval_state', '=', 'pending')])
        overdue_requests = Req.search_count([('company_id', '=', company.id), ('is_overdue', '=', True)])
        pending_settlement = Req.search_count([
            ('company_id', '=', company.id),
            ('approval_state', '=', 'approved'),
            ('financial_settlement_state', '=', 'pending_disbursement'),
        ])
        published_anns = self.env['tp.announcement'].sudo().search_count([
            ('company_id', '=', company.id), ('state', '=', 'published'),
        ])
        broken_equip = self.env['maintenance.equipment'].sudo().search_count([
            ('company_id', '=', company.id),
            ('tp_lifecycle', '=', 'active'),
            ('tp_technical_state', 'in', ('broken', 'repair_needed')),
        ])

        # 3. 11 Separated Financial Metrics (ONLY if caller has finance read permission; missing -> has_data=False, NEVER fake 0!)
        financial_cards = []
        if can_finance:
            fin_dom = [('company_id', '=', company.id)]
            clean_period = (period_filter or '').strip()
            if clean_period:
                fin_dom.append(('period_label', '=', clean_period))
            entries = self.search(fin_dom, order='write_date desc, id desc')

            for m_key, m_label in FINANCIAL_METRIC_KINDS:
                m_rows = entries.filtered(lambda e: e.metric_kind == m_key)
                if not m_rows:
                    financial_cards.append({
                        'key': m_key,
                        'label': m_label,
                        'has_data': False,
                        'value': None,
                        'display_value': 'Chưa đủ dữ liệu',
                        'unit': 'VNĐ',
                        'period': clean_period or 'Toàn kỳ ghi nhận',
                        'source': 'Chưa có bản ghi đối chiếu',
                        'updated_at': '—',
                        'state_label': 'Chưa ghi nhận',
                    })
                else:
                    confirmed_rows = m_rows.filtered(lambda e: e.data_state == 'confirmed')
                    active_set = confirmed_rows if confirmed_rows else m_rows
                    total_amt = sum(active_set.mapped('amount'))
                    latest = active_set[0]
                    financial_cards.append({
                        'key': m_key,
                        'label': m_label,
                        'has_data': True,
                        'value': total_amt,
                        'display_value': f"{total_amt:,.0f} ₫".replace(',', '.'),
                        'unit': 'VNĐ',
                        'period': clean_period or latest.period_label,
                        'source': latest.source_ref,
                        'updated_at': format_dt_local(latest.write_date),
                        'state_label': 'Đã xác nhận' if confirmed_rows else 'Tạm tính (chưa xác nhận)',
                    })

        # 4. Department Workload Honesty Summary
        workload = self.env['project.task'].tp_get_honest_workload_summary()

        return {
            'updated_at': format_dt_local(fields.Datetime.now()),
            'can_finance': can_finance,
            'kpis': {
                'total_projects': len(projs),
                'pending_requests': pending_requests,
                'overdue_requests': overdue_requests,
                'pending_settlement': pending_settlement,
                'published_announcements': published_anns,
                'broken_equipment': broken_equip,
            },
            'project_cards': project_cards,
            'financial_cards': financial_cards,
            'workload_rows': (workload.get('rows') or [])[:15],
            'metric_options': [{'key': k, 'label': v} for k, v in FINANCIAL_METRIC_KINDS],
        }
