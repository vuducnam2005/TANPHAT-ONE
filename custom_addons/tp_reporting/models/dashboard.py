"""The dashboard uses the same record rules and domains as its drill-downs."""
from decimal import Decimal

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ReportDashboard(models.AbstractModel):
    _name = 'tp.report.dashboard'
    _description = 'Tổng quan Trung tâm Báo cáo'

    @api.model
    def get_data(self, date_start, date_end, period_type='quarter', department_id=False):
        start, end = fields.Date.to_date(date_start), fields.Date.to_date(date_end)
        if not start or not end or end < start or (end - start).days > 1096:
            raise ValidationError(self.env._('Chọn khoảng ngày hợp lệ, tối đa ba năm.'))
        if period_type not in {'week', 'month', 'quarter', 'cumulative'}:
            raise ValidationError(self.env._('Loại kỳ không hợp lệ.'))
        documents = self.env['tp.report.document']
        documents.check_access('read')
        period = [('date_start', '<=', end.isoformat()), ('date_end', '>=', start.isoformat())]
        if department_id:
            if not isinstance(department_id, int) or isinstance(department_id, bool):
                raise ValidationError(self.env._('Phòng ban không hợp lệ.'))
            period += [('department_id', '=', department_id)]
        now = fields.Datetime.now()
        obligations = self.env['tp.report.obligation']
        # Obligation state is the reporting denominator, rather than active employee count.
        rows = obligations.search(period)
        submitted_ids = rows._submission_ids()
        groups = [
            ('submitted', 'Đã nộp', '#2563EB'),
            ('pending', 'Chưa nộp', '#D97706'),
            ('exempt', 'Được miễn', '#94A3B8'),
        ]
        buckets = {key: [] for key, _label, _color in groups}
        for obligation in rows:
            if obligation.state == 'exempt':
                key = 'exempt'
            elif obligation.id in submitted_ids:
                key = 'submitted'
            else:
                key = 'pending'
            buckets[key].append(obligation.id)
        items = [{'key': key, 'label': label, 'count': len(buckets[key]), 'color': color,
                  'model': 'tp.report.obligation', 'domain': [('id', 'in', buckets[key])]}
                 for key, label, color in groups]
        review = period + [('state', 'in', ['submitted', 'in_review']), ('reviewer_id', '=', self.env.uid)]
        open_directives = [('state', 'in', ['open', 'in_progress'])]
        if department_id:
            open_directives += [('department_id', '=', department_id)]
        overdue = open_directives + [('deadline', '<', fields.Datetime.to_string(now))]
        directives = self.env['tp.report.directive']
        directive_rows = directives.search(open_directives, limit=6, order='deadline,id')
        kpis = [
            {'key': 'submitted', 'label': 'Nghĩa vụ đã nộp', 'value': len(buckets['submitted']),
             'model': 'tp.report.obligation', 'domain': [('id', 'in', buckets['submitted'])]},
            {'key': 'review', 'label': 'Cần rà soát', 'value': documents.search_count(review),
             'model': 'tp.report.document', 'domain': review},
            {'key': 'overdue', 'label': 'Chỉ đạo quá hạn', 'value': directives.search_count(overdue),
             'model': 'tp.report.directive', 'domain': overdue},
            {'key': 'directives', 'label': 'Chỉ đạo cần xử lý',
             'value': directives.search_count(open_directives),
             'model': 'tp.report.directive', 'domain': open_directives},
        ]
        plans = self.env['tp.report.plan'].search(period + [('period_type', '=', period_type), ('state', '=', 'issued')],
                                                order='deadline,id', limit=8)
        bars = []
        for plan in plans:
            if plan.kind != 'quantitative':
                continue
            actuals = plan._report_actual(start, end)
            compatible = [x for x in actuals if x['unit'] == plan.unit]
            actual = float(sum((Decimal(str(x['quantity'])) for x in compatible), Decimal(0))) if compatible else None
            bars.append({'id': plan.id, 'label': plan.name, 'unit': plan.unit,
                         'plan': plan.target, 'actual': actual, 'model': 'tp.report.plan',
                         'domain': [('id', '=', plan.id)]})
        return {
            'period': {'date_start': start.isoformat(), 'date_end': end.isoformat(),
                       'period_type': period_type, 'label': f'{start:%d/%m/%Y} – {end:%d/%m/%Y}'},
            'submission': {'total': len(rows), 'items': items}, 'plan_actual': bars,
            'kpis': kpis, 'decisions': [
                {'id': row.id, 'name': row.name, 'owner': row.owner_id.display_name,
                 'deadline': fields.Datetime.to_string(row.deadline), 'state': row.state,
                 'model': 'tp.report.directive'} for row in directive_rows
            ],
            'scope_label': 'Trong phạm vi được cấp',
            'scopes': [{'id': d.id, 'name': d.display_name}
                       for d in (rows.department_id | plans.department_id)],
            'notes': ['Từ hệ thống • Hiện hành; số kết quả lấy từ phiên bản đã gửi trong quyền.',
                      'Nghĩa vụ gồm đã nộp, chưa nộp và được miễn; quá hạn là nhãn riêng.',
                      'Biểu đồ mục tiêu hiển thị tối đa 8 mục tiêu đã ban hành; mở danh sách để xem đầy đủ.',
                      'Lịch mặc định thử T2–CN, Asia/Saigon; chưa là nội quy công ty.'],
            'updated_at': fields.Datetime.to_string(fields.Datetime.now()),
            'milestones': [{'id': p.id, 'name': p.name, 'deadline': fields.Datetime.to_string(p.deadline),
                            'output': p.output, 'model': 'tp.report.plan'} for p in plans if p.kind == 'qualitative'],
        }
