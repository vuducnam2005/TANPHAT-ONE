"""Live, permission-scoped presentation of the two connected sample dashboards.

No stored totals, sudo business reads, new groups, or business transitions.
"""
# Odoo messages are operator-facing Vietnamese strings, like the existing privacy guard.
# ruff: noqa: EM101
import json
from datetime import datetime, time, timedelta
from decimal import Decimal

import pytz

from odoo import fields, models
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import format_amount, format_datetime, formatLang

NAMESPACE = 'tp_native_data002_20261102'
KINDS = {'finance': 'dashboard_finance_draft', 'coordination': 'dashboard_coordination'}
STATES = [('draft', 'Đang soạn'), ('submitted', 'Chờ duyệt'), ('approved', 'Đã duyệt')]
# NATIVE-STABILIZE-001: the metric itself must say it is not cash paid; same scope as STATES above.
EXPENSE_SCOPE = 'Gồm Đang soạn, Chờ duyệt, Đã duyệt; không gồm Đã ghi sổ, Đang/Đã thanh toán, Bị từ chối.'


class DashboardReport(models.Model):
    _inherit = 'spreadsheet.dashboard'

    def _tp_config(self):
        self.ensure_one()
        self.check_access('read')
        config = json.loads(self.spreadsheet_data or '{}').get('settings', {}).get('tpDashboard')
        if not config:
            return None
        kind = config.get('kind')
        bound = self.env.ref(f'{NAMESPACE}.{KINDS.get(kind, "missing")}', raise_if_not_found=False)
        if not bound or bound != self or config.get('version') != 1:
            raise ValidationError('Cấu hình bảng tổng hợp TANPHAT ONE không hợp lệ.')
        return config

    def _get_serialized_readonly_dashboard(self):
        result = json.loads(super()._get_serialized_readonly_dashboard())
        config = self._tp_config()
        # Read only the restricted privacy flag, following the existing share guard.
        # Never elevate the actor for any report source or project lookup.
        result['tp_dashboard'] = {'kind': config['kind'] if config else None,
                                  'internal': bool(self.sudo().tp_internal_only)}
        return json.dumps(result)

    def _tp_filter(self, config, filters):
        filters = filters or {}
        if not isinstance(filters, dict) or set(filters) - {'project_id', 'date_from', 'date_to'}:
            raise ValidationError('Bộ lọc không hợp lệ.')
        company = self.env['res.company'].browse(config['company_id'])
        if company not in self.env.companies:
            raise AccessError('Không đủ quyền xem công ty của bảng tổng hợp.')
        projects = self.env['project.project'].search([
            ('id', 'in', config['project_ids']), ('company_id', '=', company.id),
        ], order='tp_code, id')
        project_id = filters.get('project_id')
        if project_id and (type(project_id) is not int or project_id not in projects.ids):
            raise AccessError('Không đủ quyền xem dự án đã chọn.')
        dates = []
        for key in ('date_from', 'date_to'):
            value = filters.get(key)
            try:
                dates.append(datetime.strptime(value, '%Y-%m-%d').date() if value else None)
            except (TypeError, ValueError) as exc:
                raise ValidationError('Ngày lọc phải có định dạng YYYY-MM-DD.') from exc
        if dates[0] and dates[1] and dates[0] > dates[1]:
            raise ValidationError('Ngày bắt đầu phải trước hoặc bằng ngày kết thúc.')
        selected = projects.filtered(lambda p: not project_id or p.id == project_id)
        return company, projects, selected, dates

    def _tp_date_domain(self, field, dates, *, timestamp=False):
        domain = []
        tz = pytz.timezone(self.env.user.tz or 'UTC')
        for index, value in enumerate(dates):
            if value:
                if timestamp:
                    day = value + timedelta(days=index)
                    value = tz.localize(datetime.combine(day, time.min)).astimezone(pytz.UTC).replace(tzinfo=None)
                domain.append((field, '>=' if index == 0 else '<' if timestamp else '<=', value))
        return domain

    def _tp_parts(self, distribution, projects):
        """A combined analytic key is one percentage, never one full amount per ID."""
        by_account = {p.account_id.id: p.id for p in projects if p.account_id}
        if len(by_account) != len(projects.filtered('account_id')):
            raise UserError('Nhiều dự án dùng chung tài khoản analytic; cần xác minh quan hệ trước khi tổng hợp.')
        result = {}
        for key, percentage in (distribution or {}).items():
            if Decimal(str(percentage)) < 0:
                raise UserError('Phân bổ âm không được hỗ trợ; cần kiểm tra chứng từ nguồn.')
            matches = {by_account[int(a)] for a in key.split(',') if int(a) in by_account}
            if len(matches) > 1:
                raise UserError('Một nhánh phân bổ có nhiều dự án; cần kiểm tra phân bổ nguồn trước khi tổng hợp.')
            if matches and Decimal(str(percentage)):
                pid = matches.pop()
                result[pid] = result.get(pid, Decimal(0)) + Decimal(str(percentage)) / 100
        if sum(result.values()) > Decimal('1.000001'):
            raise UserError('Tỷ lệ phân bổ dự án vượt 100%; cần kiểm tra chứng từ nguồn.')
        return result

    def _tp_allocations(self, amount, distribution, projects, currency):
        parts = self._tp_parts(distribution, projects)
        result = {pid: Decimal(str(currency.round(float(Decimal(str(amount)) * ratio))))
                  for pid, ratio in parts.items()}
        if result:
            target = Decimal(str(currency.round(float(Decimal(str(amount)) * sum(parts.values())))))
            # Stable residual assignment prevents rounded splits from duplicating cents.
            result[max(result)] += target - sum(result.values())
        return result

    def _tp_finance(self, config, company, projects, dates):
        currency = company.currency_id
        all_projects = self.env['project.project'].search([
            ('id', 'in', config['project_ids']), ('company_id', '=', company.id),
        ])
        invoices = self.env['account.move'].search([
            ('id', 'in', config['invoice_ids']), ('company_id', '=', company.id),
            ('state', '=', 'draft'), ('move_type', '=', 'out_invoice'),
            *self._tp_date_domain('invoice_date', dates),
        ])
        expenses = self.env['hr.expense'].search([
            ('id', 'in', config['expense_ids']), ('company_id', '=', company.id),
            ('state', 'in', [s for s, _ in STATES]), *self._tp_date_domain('date', dates),
        ])
        rows = {p.id: {'id': p.id, 'code': p.tp_code, 'name': p.name,
                        'invoice_ids': set(), 'expense_ids': set(), 'invoice': Decimal(0),
                        'untaxed': Decimal(0), **{s: Decimal(0) for s, _ in STATES},
                        **{s + '_ids': set() for s, _ in STATES}} for p in projects}
        for invoice in invoices:
            if invoice.currency_id != currency:
                raise UserError('Hóa đơn khác tiền tệ công ty; chưa có quy tắc quy đổi cho bảng này.')
            for line in invoice.invoice_line_ids.filtered(lambda line: line.display_type == 'product'):
                allocated = self._tp_allocations(line.price_total, line.analytic_distribution, all_projects, currency)
                untaxed = self._tp_allocations(line.price_subtotal, line.analytic_distribution, all_projects, currency)
                for pid, amount in allocated.items():
                    if pid in rows:
                        row = rows[pid]
                        row['invoice'] += amount
                        row['untaxed'] += untaxed[pid]
                        row['invoice_ids'].add(invoice.id)
        for expense in expenses:
            for pid, amount in self._tp_allocations(expense.total_amount, expense.analytic_distribution, all_projects, currency).items():
                if pid in rows:
                    row = rows[pid]
                    row[expense.state] += amount
                    row['expense_ids'].add(expense.id)
                    row[expense.state + '_ids'].add(expense.id)
        totals = {'invoice': Decimal(0), 'untaxed': Decimal(0), **{s: Decimal(0) for s, _ in STATES}}
        invoice_ids, expense_ids = set(), set()
        state_ids = {s: set() for s, _ in STATES}
        for row in rows.values():
            for key in totals:
                totals[key] += row[key]
            invoice_ids.update(row['invoice_ids'])
            expense_ids.update(row['expense_ids'])
            for state, _ in STATES:
                state_ids[state].update(row[state + '_ids'])

        def money(amount):
            return format_amount(self.env, float(amount), currency)
        metrics = [
            {'label': 'Số hóa đơn nháp', 'display': str(len(invoice_ids)), 'unit': 'hóa đơn', 'source': 'invoices'},
            {'label': 'Giá trị hóa đơn nháp gồm thuế', 'display': money(totals['invoice']), 'source': 'invoices',
             'detail': 'Chưa thuế: ' + money(totals['untaxed'])},
            {'label': 'Số đề nghị chi phí trong phạm vi', 'display': str(len(expense_ids)), 'unit': 'đề nghị', 'source': 'expenses',
             'detail': EXPENSE_SCOPE},
            {'label': 'Tổng giá trị đề nghị chi phí', 'display': money(sum(totals[s] for s, _ in STATES)), 'source': 'expenses',
             'detail': 'Chưa phải số đã chi. ' + EXPENSE_SCOPE},
        ]
        charts = [
            {'title': 'Hóa đơn nháp theo dự án', 'unit': 'Triệu đồng', 'items': [
                {'label': r['name'], 'code': r['code'], 'value': r['invoice'], 'exact': money(r['invoice']),
                 'project_id': r['id'], 'source': 'invoices'} for r in rows.values()]},
            {'title': 'Chi phí theo trạng thái', 'unit': 'Triệu đồng', 'note': 'Đã duyệt chưa đồng nghĩa đã thanh toán.',
             'items': [{'label': label, 'value': totals[state], 'exact': money(totals[state]),
                        'state': state, 'source': 'expenses'} for state, label in STATES]},
        ]
        for row in rows.values():
            row['cells'] = [{'display': str(len(row['invoice_ids'])), 'source': 'invoices'},
                            {'display': money(row['invoice']), 'source': 'invoices'},
                            *[{'display': money(row[s]), 'source': 'expenses', 'state': s} for s, _ in STATES]]
        raw = {k: float(v) for k, v in totals.items()}
        raw.update(invoice_count=len(invoice_ids), expense_count=len(expense_ids))
        return {'metrics': metrics, 'charts': charts, 'rows': list(rows.values()), 'raw': raw,
                'headers': ['Hóa đơn nháp', 'Giá trị gồm thuế', 'Đang soạn', 'Chờ duyệt', 'Đã duyệt'],
                'empty': not invoice_ids and not expense_ids}, {
                    'invoices': invoice_ids, 'expenses': expense_ids, **state_ids,
                }

    def _tp_coordination(self, config, company, projects, dates):
        tasks = self.env['project.task'].search([
            ('project_id', 'in', projects.ids), ('company_id', '=', company.id),
            *self._tp_date_domain('create_date', dates, timestamp=True),
        ])
        lines = self.env['account.analytic.line'].search([
            ('project_id', 'in', projects.ids), ('company_id', '=', company.id),
            *self._tp_date_domain('date', dates),
        ])
        rows = []
        for project in projects:
            pt = tasks.filtered(lambda t: t.project_id == project)
            pl = lines.filtered(lambda line: line.project_id == project)
            done = pt.filtered(lambda t: t.state == '1_done')
            hours = sum(Decimal(str(line.unit_amount)) for line in pl)
            rows.append({'id': project.id, 'code': project.tp_code, 'name': project.name,
                         'tasks': len(pt), 'done': len(done), 'hours': hours,
                         'task_ids': set(pt.ids), 'done_ids': set(done.ids), 'line_ids': set(pl.ids),
                         'cells': [{'display': str(len(pt)), 'source': 'tasks'},
                                   {'display': str(len(done)), 'source': 'done'},
                                   {'display': formatLang(self.env, float(hours), digits=2), 'source': 'hours'},
                                   {'display': str(len(pl)), 'source': 'hours'}]})
        total_hours = sum(Decimal(str(line.unit_amount)) for line in lines)
        done = tasks.filtered(lambda t: t.state == '1_done')
        metrics = [
            {'label': 'Dự án có dữ liệu', 'display': str(sum(bool(r['tasks'] or r['line_ids']) for r in rows)), 'unit': 'dự án'},
            {'label': 'Số công việc', 'display': str(len(tasks)), 'unit': 'công việc', 'source': 'tasks'},
            {'label': 'Công việc hoàn tất', 'display': str(len(done)), 'unit': 'công việc', 'source': 'done'},
            {'label': 'Giờ làm đã ghi nhận', 'display': formatLang(self.env, float(total_hours), digits=2), 'unit': 'giờ', 'source': 'hours'},
        ]
        charts = [{'title': title, 'unit': unit, 'items': [
            {'label': r['name'], 'code': r['code'], 'value': r[field], 'project_id': r['id'],
             'exact': formatLang(self.env, float(r[field]), digits=2 if field == 'hours' else 0) + ' ' + unit,
             'source': source} for r in rows]} for title, unit, field, source in (
                 ('Công việc theo dự án', 'Công việc', 'tasks', 'tasks'),
                 ('Giờ làm theo dự án', 'Giờ', 'hours', 'hours'))]
        return {'metrics': metrics, 'charts': charts, 'rows': rows,
                'raw': {'tasks': len(tasks), 'done': len(done), 'hours': float(total_hours)},
                'headers': ['Công việc', 'Hoàn tất', 'Giờ làm', 'Dòng giờ làm'],
                'empty': not tasks and not lines}, {'tasks': set(tasks.ids), 'done': set(done.ids), 'hours': set(lines.ids)}

    def _tp_report(self, filters):
        config = self._tp_config()
        if not config:
            raise AccessError('Bảng này không thuộc phạm vi TANPHAT ONE.')
        company, projects, selected, dates = self._tp_filter(config, filters)
        if config['kind'] == 'finance':
            report, ids = self._tp_finance(config, company, selected, dates)
        else:
            report, ids = self._tp_coordination(config, company, selected, dates)
        return report, ids, projects, config

    def tp_dashboard_report(self, filters=None):
        report, _ids, projects, config = self._tp_report(filters)
        for chart in report['charts']:
            maximum = max([abs(i['value']) for i in chart['items']] or [0])
            if any(i['value'] < 0 for i in chart['items']):
                raise UserError('Có giá trị âm; cần kiểm tra nguồn trước khi trình bày bằng biểu đồ thanh từ 0.')
            divisor = Decimal(1000000) if config['kind'] == 'finance' else Decimal(1)
            chart['maximum'] = formatLang(self.env, float(maximum / divisor), digits=2)
            for item in chart['items']:
                item['width'] = float(item['value'] / maximum * 100) if maximum else 0
                item['scale'] = formatLang(self.env, float(item['value'] / divisor), digits=2)
                item['value'] = float(item['value'])
        # Sets/Decimals are private calculation state, never RPC payload/cache.
        report['rows'] = [{k: v for k, v in row.items() if k in ('id', 'code', 'name', 'cells')}
                          for row in report['rows']]
        report.update(kind=config['kind'], projects=[{'id': p.id, 'code': p.tp_code, 'name': p.name} for p in projects],
                      fetched_at=format_datetime(self.env, fields.Datetime.now(), dt_format='dd/MM/yyyy HH:mm:ss'),
                      company=self.env['res.company'].browse(config['company_id']).name)
        return report

    def tp_dashboard_action(self, source, filters=None, project_id=None, state=None):
        if (not isinstance(source, str) or (state and not isinstance(state, str))
                or (filters is not None and not isinstance(filters, dict))):
            raise ValidationError('Bộ lọc hoặc nguồn chi tiết không hợp lệ.')
        scoped = dict(filters or {})
        if project_id:
            if scoped.get('project_id') and scoped['project_id'] != project_id:
                raise ValidationError('Dự án mở chi tiết khác bộ lọc hiện tại.')
            scoped['project_id'] = project_id
        _report, ids, _projects, _config = self._tp_report(scoped)
        if source not in ids or source in ('draft', 'submitted', 'approved'):
            raise ValidationError('Nguồn chi tiết không hợp lệ.')
        record_ids = ids[source]
        if state:
            if source != 'expenses' or state not in dict(STATES):
                raise ValidationError('Trạng thái chi tiết không hợp lệ.')
            record_ids = ids[state]
        model = {'invoices': 'account.move', 'expenses': 'hr.expense', 'tasks': 'project.task',
                 'done': 'project.task', 'hours': 'account.analytic.line'}[source]
        return {'type': 'ir.actions.act_window', 'name': 'Chứng từ nguồn trong phạm vi đang xem',
                'res_model': model, 'views': [(False, 'list'), (False, 'form')],
                'domain': [('id', 'in', sorted(record_ids))], 'context': {'create': False}, 'target': 'current'}
