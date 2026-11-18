"""Machine late totals (Đi muộn: Lần / Phút) kept per employee + source period + import batch.

The machine reports one total for the whole period of the file; it is stored as given, never split per
day, never recomputed from clock times and never added to an overlapping period (DEC-056).
"""
from odoo import api, fields, models

from .attendance_common import HR_MANAGER, OFFICER, deny_direct
from .attendance_logic import late_cover

LATE_SOURCE_STATES = [
    ('ok', 'Số hợp lệ'), ('empty', 'Ô trống'), ('invalid', 'Không phải số nguyên không âm'),
    ('inconsistent', 'Lần và Phút không khớp nhau'),
]
LATE_STATES = [
    ('preview', 'Đang xem trước'), ('valid', 'Hợp lệ, sẽ ghi nhận'), ('duplicate', 'Trùng, bỏ qua'),
    ('conflict', 'Khác tổng đã nhập cùng kỳ'), ('unmapped', 'Chưa đối chiếu được nhân viên'),
    ('name_conflict', 'Mã máy khớp nhưng tên khác'), ('missing', 'Chưa có số liệu'), ('review', 'Cần kiểm tra'),
    ('locked', 'Kỳ đã chốt'), ('applied', 'Đã ghi nhận'), ('cancelled', 'Lô đã hủy'),
]
PROCESSOR_GROUPS = f'{HR_MANAGER},{OFFICER}'


class AttendanceLate(models.Model):
    _name = 'tp.hr.attendance.late'
    _description = 'Tổng đi muộn theo kỳ của máy chấm công'
    _order = 'date_from desc, employee_id, id desc'
    _check_company_auto = True

    batch_id = fields.Many2one('tp.hr.attendance.batch', 'Lô nhập', required=True, index=True, ondelete='cascade')
    company_id = fields.Many2one(related='batch_id.company_id', store=True, string='Công ty', index=True)
    sheet_name = fields.Char('Trang', readonly=True)
    sheet_index = fields.Integer(readonly=True)
    row_number = fields.Integer('Dòng', readonly=True)
    cell_ref = fields.Char('Ô nguồn', readonly=True)
    machine_code = fields.Char('Mã máy', readonly=True, index=True)
    source_name = fields.Char('Tên trong tệp', readonly=True)
    employee_id = fields.Many2one('hr.employee', 'Nhân viên', readonly=True, index=True)
    candidate_employee_id = fields.Many2one('hr.employee', 'Hồ sơ gợi ý', readonly=True)
    date_from = fields.Date('Từ ngày', required=True, readonly=True, index=True)
    date_to = fields.Date('Đến ngày', required=True, readonly=True, index=True)
    late_count = fields.Integer('Số lần đi muộn', readonly=True)
    late_minutes = fields.Integer('Tổng phút muộn', readonly=True)
    raw_count = fields.Char('Lần (nguồn)', readonly=True)
    raw_minutes = fields.Char('Phút (nguồn)', readonly=True)
    source_state = fields.Selection(LATE_SOURCE_STATES, 'Số trong tệp', required=True, readonly=True)
    state = fields.Selection(LATE_STATES, 'Kết quả', required=True, readonly=True, default='preview', index=True)
    message = fields.Char('Giải thích', readonly=True)

    _applied_unique = models.UniqueIndex('(company_id, employee_id, date_from, date_to) WHERE state = \'applied\'',
                                         'Mỗi nhân viên chỉ có một tổng đi muộn đã ghi nhận cho mỗi kỳ nguồn.')
    _period_valid = models.Constraint('CHECK(date_to >= date_from)', 'Kỳ nguồn không hợp lệ.')

    @api.model_create_multi
    def create(self, vals_list):
        deny_direct(self)
        return super().create(vals_list)

    def write(self, vals):
        deny_direct(self)
        return super().write(vals)

    def unlink(self):
        deny_direct(self)
        return super().unlink()

    @api.model
    def _tp_records(self, company, employee_ids, start, end):
        """``{employee_id: [record dicts]}`` of applied valid totals touching ``[start, end]`` (server-side, sudo)."""
        result = {}
        if not employee_ids:
            return result
        rows = self.sudo().search_read([
            ('company_id', '=', company.id), ('employee_id', 'in', list(employee_ids)), ('state', '=', 'applied'),
            ('date_from', '<=', end), ('date_to', '>=', start)], ['employee_id', 'date_from', 'date_to', 'late_count', 'late_minutes'])
        for row in rows:
            result.setdefault(row['employee_id'][0], []).append({
                'date_from': row['date_from'], 'date_to': row['date_to'], 'count': row['late_count'], 'minutes': row['late_minutes']})
        return result

    @api.model
    def _tp_cover(self, company, employee_ids, start, end):
        """``{employee_id: late_cover(...)}`` for every given employee; missing data stays ``state='none'``."""
        records = self._tp_records(company, employee_ids, start, end)
        return {employee_id: late_cover(records.get(employee_id, []), start, end) for employee_id in employee_ids}
