"""Configuration models: machine codes, work rules, assignments, periods and the audit log."""
import hashlib
import json

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

from .attendance_common import HR_MANAGER, OFFICER, can, deny_direct, internal, require
from .attendance_import import ADVISORY_KEY


class AttendanceCode(models.Model):
    _name = 'tp.hr.attendance.code'
    _description = 'Mã máy chấm công'
    _order = 'company_id, machine_code'
    _check_company_auto = True
    _rec_name = 'machine_code'

    machine_code = fields.Char('Mã máy', required=True, index=True)
    employee_id = fields.Many2one('hr.employee', 'Nhân viên', required=True, check_company=True, ondelete='restrict')
    company_id = fields.Many2one('res.company', 'Công ty', required=True, default=lambda self: self.env.company)
    source = fields.Selection([('auto', 'Tự đối chiếu khi nhập'), ('manual', 'HR khai báo')], 'Nguồn', default='manual', required=True)
    note = fields.Char('Ghi chú')

    _machine_code_unique = models.Constraint('UNIQUE(company_id, machine_code)', 'Mã máy đã được gán cho nhân viên khác.')

    @api.constrains('machine_code')
    def _check_machine_code(self):
        for code in self:
            if not (code.machine_code or '').strip().isdigit():
                raise ValidationError(self.env._('Mã máy chấm công là cột ID dạng số trong báo cáo máy.'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('machine_code'):
                vals['machine_code'] = str(int(str(vals['machine_code']).strip())) if str(vals['machine_code']).strip().isdigit() else vals['machine_code']
        records = super().create(vals_list)
        for record in records:
            self.env['tp.hr.attendance.log']._tp_log(record, 'code_create', {'machine_code': record.machine_code, 'employee_id': record.employee_id.id, 'source': record.source})
        return records

    def write(self, vals):
        result = super().write(vals)
        for record in self:
            self.env['tp.hr.attendance.log']._tp_log(record, 'code_write', {key: vals[key] for key in vals if key in ('machine_code', 'employee_id', 'source')})
        return result


class AttendanceRule(models.Model):
    _name = 'tp.hr.attendance.rule'
    _description = 'Quy tắc tính công'
    _order = 'company_id, date_from desc, id desc'
    _check_company_auto = True

    name = fields.Char('Tên quy tắc', required=True)
    company_id = fields.Many2one('res.company', 'Công ty', required=True, default=lambda self: self.env.company)
    date_from = fields.Date('Áp dụng từ', required=True)
    date_to = fields.Date('Đến ngày')
    department_ids = fields.Many2many('hr.department', string='Phòng áp dụng', check_company=True, help='Để trống = toàn công ty.')
    mon = fields.Boolean('Thứ 2', default=True)
    tue = fields.Boolean('Thứ 3', default=True)
    wed = fields.Boolean('Thứ 4', default=True)
    thu = fields.Boolean('Thứ 5', default=True)
    fri = fields.Boolean('Thứ 6', default=True)
    sat = fields.Boolean('Thứ 7')
    sun = fields.Boolean('Chủ nhật')
    start_hour = fields.Float('Giờ bắt đầu', default=8.0)
    end_hour = fields.Float('Giờ kết thúc', default=17.0)
    break_start = fields.Float('Nghỉ trưa từ', default=12.0)
    break_end = fields.Float('Nghỉ trưa đến', default=13.0)
    standard_hours = fields.Float('Giờ chuẩn một công', default=8.0)
    state = fields.Selection([('draft', 'Nháp'), ('confirmed', 'Đã xác nhận')], 'Trạng thái', default='draft', required=True, readonly=True)
    confirmed_by = fields.Many2one('res.users', 'Người xác nhận', readonly=True)
    confirmed_at = fields.Datetime('Thời điểm xác nhận', readonly=True)
    note = fields.Text('Căn cứ / ghi chú')

    _hours_valid = models.Constraint(
        'CHECK(start_hour >= 0 AND end_hour <= 24 AND start_hour < end_hour AND standard_hours > 0 '
        'AND break_start <= break_end)', 'Khung giờ hoặc giờ chuẩn không hợp lệ.')

    @api.constrains('date_from', 'date_to')
    def _check_dates(self):
        for rule in self:
            if rule.date_to and rule.date_to < rule.date_from:
                raise ValidationError(self.env._('Ngày kết thúc phải sau ngày bắt đầu.'))

    def _weekday_on(self, day):
        return self[('mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun')[day.weekday()]]

    def covers(self, day, department):
        self.ensure_one()
        return (self.date_from <= day and (not self.date_to or day <= self.date_to)
                and (not self.department_ids or (department and department in self.department_ids)))

    def write(self, vals):
        if any(rule.state == 'confirmed' for rule in self) and set(vals) - {'note'} and not self.env.context.get('_tp_rule_reset'):
            raise UserError(self.env._('Quy tắc đã xác nhận; đưa về nháp trước khi sửa.'))
        return super().write(vals)

    def unlink(self):
        if any(rule.state == 'confirmed' for rule in self):
            raise UserError(self.env._('Không xóa quy tắc đã xác nhận; đưa về nháp trước.'))
        return super().unlink()

    def _affected_days(self):
        days = self.env['tp.hr.attendance.day'].sudo()
        for rule in self:
            domain = [('company_id', '=', rule.company_id.id), ('work_date', '>=', rule.date_from)]
            if rule.date_to:
                domain.append(('work_date', '<=', rule.date_to))
            days |= days.search(domain)
        return days

    def action_confirm(self):
        if not self.env.user.has_group(HR_MANAGER):
            raise AccessError(self.env._('Chỉ quản lý nhân sự được xác nhận quy tắc tính công.'))
        for rule in self.filtered(lambda r: r.state == 'draft'):
            rule.with_context(_tp_rule_reset=True).write({'state': 'confirmed', 'confirmed_by': self.env.user.id, 'confirmed_at': fields.Datetime.now()})
            self.env['tp.hr.attendance.log']._tp_log(rule, 'rule_confirm', {'name': rule.name})
        self._affected_days()._tp_recompute()
        return True

    def action_reset(self):
        if not self.env.user.has_group(HR_MANAGER):
            raise AccessError(self.env._('Chỉ quản lý nhân sự được đổi quy tắc tính công.'))
        days = self._affected_days()
        for rule in self.filtered(lambda r: r.state == 'confirmed'):
            rule.with_context(_tp_rule_reset=True).write({'state': 'draft', 'confirmed_by': False, 'confirmed_at': False})
            self.env['tp.hr.attendance.log']._tp_log(rule, 'rule_reset', {'name': rule.name})
        days._tp_recompute()
        return True


class AttendanceAssignment(models.Model):
    _name = 'tp.hr.attendance.assignment'
    _description = 'Phân công xử lý công'
    _order = 'company_id, user_id'
    _check_company_auto = True
    _rec_name = 'user_id'

    user_id = fields.Many2one('res.users', 'Người phụ trách', required=True, domain=[('share', '=', False)], ondelete='cascade')
    company_id = fields.Many2one('res.company', 'Công ty', required=True, default=lambda self: self.env.company)
    department_ids = fields.Many2many('hr.department', string='Phạm vi phòng', check_company=True, help='Để trống = toàn công ty.')
    can_import = fields.Boolean('Nhập dữ liệu công', help='Chỉ hiệu lực khi phạm vi là toàn công ty.')
    # Kept for stored data and shared exports; corrections are approved by admins only (CHG-20261119-005/-012).
    can_review = fields.Boolean('Xuất bảng công trong phạm vi',
                                help='Chỉ mở quyền xuất bảng công chung của các phòng trong phạm vi. Duyệt / trả điều chỉnh công '
                                     'do admin (admin gốc hoặc admin được ủy quyền) thực hiện, không theo phân công này.')
    can_lock = fields.Boolean('Chốt / mở kỳ')
    active = fields.Boolean(default=True)
    note = fields.Char('Căn cứ phân công')

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            self.env['tp.hr.attendance.log']._tp_log(record, 'assignment_create', record._tp_snapshot())
        self._tp_sync_officers()
        self.env['tp.hr.attendance.correction']._tp_refresh_reviewers(records.company_id)
        return records

    def write(self, vals):
        companies = self.company_id
        result = super().write(vals)
        for record in self:
            self.env['tp.hr.attendance.log']._tp_log(record, 'assignment_write', record._tp_snapshot())
        self._tp_sync_officers()
        self.env['tp.hr.attendance.correction']._tp_refresh_reviewers(companies | self.company_id)
        return result

    def unlink(self):
        companies = self.company_id
        for record in self:
            self.env['tp.hr.attendance.log']._tp_log(record, 'assignment_unlink', record._tp_snapshot())
        result = super().unlink()
        self._tp_sync_officers()
        self.env['tp.hr.attendance.correction']._tp_refresh_reviewers(companies)
        return result

    def _tp_snapshot(self):
        return {'user_id': self.user_id.id, 'departments': self.department_ids.ids, 'import': self.can_import,
                'review': self.can_review, 'lock': self.can_lock, 'active': self.active}

    @api.model
    def _tp_sync_officers(self):
        """The officer group only opens read ACLs on staging/log; it mirrors active assignments exactly."""
        group = self.env.ref(OFFICER).sudo()
        wanted = self.sudo().search([('active', '=', True)]).user_id
        if set(group.user_ids.ids) != set(wanted.ids):
            group.write({'user_ids': [(6, 0, wanted.ids)]})


class AttendancePeriod(models.Model):
    _name = 'tp.hr.attendance.period'
    _description = 'Kỳ công'
    _order = 'date_from desc'
    _check_company_auto = True

    name = fields.Char('Kỳ công', required=True)
    company_id = fields.Many2one('res.company', 'Công ty', required=True, default=lambda self: self.env.company)
    date_from = fields.Date('Từ ngày', required=True)
    date_to = fields.Date('Đến ngày', required=True)
    state = fields.Selection([('open', 'Đang mở'), ('locked', 'Đã chốt')], 'Trạng thái', default='open', required=True, readonly=True)
    locked_by = fields.Many2one('res.users', 'Người chốt', readonly=True)
    locked_at = fields.Datetime('Thời điểm chốt', readonly=True)
    version = fields.Integer('Phiên bản', default=1, readonly=True)
    day_count = fields.Integer('Ngày công trong kỳ', compute='_compute_tp_counts')
    ok_count = fields.Integer('Đủ dữ liệu', compute='_compute_tp_counts')
    missing_count = fields.Integer('Thiếu giờ vào/ra', compute='_compute_tp_counts')
    review_count = fields.Integer('Cần kiểm tra', compute='_compute_tp_counts')
    pending_count = fields.Integer('Đề nghị chờ duyệt', compute='_compute_tp_counts')
    amend_count = fields.Integer('Đính chính sau chốt', compute='_compute_tp_counts')
    can_lock = fields.Boolean('Được chốt/mở kỳ', compute='_compute_tp_counts')

    _dates_valid = models.Constraint('CHECK(date_from <= date_to)', 'Ngày kết thúc kỳ phải sau ngày bắt đầu.')

    @api.depends('company_id', 'date_from', 'date_to', 'state')
    @api.depends_context('uid')
    def _compute_tp_counts(self):
        Day = self.env['tp.hr.attendance.day'].sudo()
        Correction = self.env['tp.hr.attendance.correction'].sudo()
        for period in self:
            period.can_lock = bool(period.company_id) and can(self.env, 'lock', period.company_id)
            if not (period.company_id and period.date_from and period.date_to):
                period.update({'day_count': 0, 'ok_count': 0, 'missing_count': 0, 'review_count': 0, 'pending_count': 0, 'amend_count': 0})
                continue
            domain = [('company_id', '=', period.company_id.id), ('work_date', '>=', period.date_from), ('work_date', '<=', period.date_to)]
            counts = dict(Day._read_group(domain, ['data_state'], ['__count']))
            period.day_count = sum(counts.values())
            period.ok_count = counts.get('ok', 0)
            period.missing_count = counts.get('missing', 0)
            period.review_count = counts.get('review', 0)
            period.pending_count = Correction.search_count(domain + [('state', '=', 'submitted')])
            origin = period._origin.id
            period.amend_count = Correction.search_count([('period_id', '=', origin), ('is_amendment', '=', True)]) if origin else 0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('state', 'open') != 'open' or vals.get('locked_by') or vals.get('locked_at') or vals.get('version', 1) != 1:
                deny_direct(self)
        if not self.env.user.has_group(HR_MANAGER):
            for vals in vals_list:
                company = self.env['res.company'].browse(vals['company_id']) if vals.get('company_id') else self.env.company
                require(self.env, 'lock', company)
        return super().create(vals_list)

    @api.constrains('date_from', 'date_to', 'company_id')
    def _check_overlap(self):
        for period in self:
            if self.search_count([('id', '!=', period.id), ('company_id', '=', period.company_id.id),
                                  ('date_from', '<=', period.date_to), ('date_to', '>=', period.date_from)]):
                raise ValidationError(self.env._('Kỳ công bị chồng ngày với kỳ khác.'))

    def write(self, vals):
        if set(vals) & {'state', 'locked_by', 'locked_at', 'version'}:
            deny_direct(self)
        if any(period.state == 'locked' for period in self) and set(vals) & {'date_from', 'date_to', 'company_id'}:
            raise UserError(self.env._('Kỳ đã chốt; mở kỳ trước khi đổi ngày.'))
        return super().write(vals)

    def unlink(self):
        if any(period.state == 'locked' for period in self):
            raise UserError(self.env._('Không xóa kỳ đã chốt.'))
        return super().unlink()

    @api.model
    def _tp_locked_ranges(self, company_ids):
        periods = self.sudo().search([('company_id', 'in', list(company_ids)), ('state', '=', 'locked')])
        ranges = {}
        for period in periods:
            ranges.setdefault(period.company_id.id, []).append((period.date_from, period.date_to))
        return ranges

    @api.model
    def _tp_is_locked(self, company_id, day, ranges=None):
        ranges = self._tp_locked_ranges([company_id]) if ranges is None else ranges
        return any(start <= day <= end for start, end in ranges.get(company_id, []))

    # ------------------------------------------------------------ lock / unlock
    def _tp_take_lock(self):
        self.ensure_one()
        self.check_access('read')
        require(self.env, 'lock', self.company_id)
        self.env.cr.execute('SELECT pg_advisory_xact_lock(%s, %s)', [ADVISORY_KEY, self.company_id.id])
        self.env.cr.execute('SELECT id FROM tp_hr_attendance_period WHERE id=%s FOR UPDATE', [self.id])
        self.invalidate_recordset()

    def _tp_lock(self, reason=None):
        """Freeze the period: imports land as 'locked', changes only through an approved amendment."""
        self._tp_take_lock()
        reason = (reason or '').strip()
        if self.state == 'locked':
            raise UserError(self.env._('Kỳ %(name)s đã chốt.', name=self.name))
        if self.pending_count:
            raise UserError(self.env._('Còn %(count)s đề nghị điều chỉnh chờ duyệt trong kỳ; duyệt hoặc trả lại trước khi chốt.',
                                       count=self.pending_count))
        if (self.missing_count or self.review_count) and not reason:
            raise UserError(self.env._('Kỳ còn %(count)s ngày thiếu giờ hoặc cần kiểm tra; ghi chú lý do chốt để lưu vết.',
                                       count=self.missing_count + self.review_count))
        days = self.env['tp.hr.attendance.day'].sudo().search([
            ('company_id', '=', self.company_id.id), ('work_date', '>=', self.date_from), ('work_date', '<=', self.date_to)], order='id')
        digest = hashlib.sha256(','.join(f'{day.id}:{day.version}' for day in days).encode()).hexdigest()
        snapshot = {'reason': reason, 'days': len(days), 'ok': self.ok_count, 'missing': self.missing_count, 'review': self.review_count,
                    'digest': digest, 'from': self.date_from, 'to': self.date_to}
        internal(self).write({'state': 'locked', 'locked_by': self.env.user.id, 'locked_at': fields.Datetime.now(), 'version': self.version + 1})
        self.env['tp.hr.attendance.log']._tp_log(self, 'period_lock', dict(snapshot, version=self.version))
        return True

    def _tp_unlock(self, reason=None):
        self._tp_take_lock()
        reason = (reason or '').strip()
        if self.state != 'locked':
            raise UserError(self.env._('Kỳ %(name)s đang mở.', name=self.name))
        if not reason:
            raise UserError(self.env._('Nhập lý do mở lại kỳ đã chốt.'))
        previous = {'locked_by': self.locked_by.id, 'locked_at': self.locked_at}
        internal(self).write({'state': 'open', 'locked_by': False, 'locked_at': False, 'version': self.version + 1})
        self.env['tp.hr.attendance.log']._tp_log(self, 'period_unlock', dict(previous, reason=reason, version=self.version))
        return True

    def _tp_period_wizard(self, operation):
        self.ensure_one()
        require(self.env, 'lock', self.company_id)
        return {
            'type': 'ir.actions.act_window', 'res_model': 'tp.hr.attendance.period.wizard', 'view_mode': 'form',
            'views': [[False, 'form']], 'target': 'new',
            'name': self.env._('Chốt kỳ công') if operation == 'lock' else self.env._('Mở lại kỳ công'),
            'context': {'default_period_id': self.id, 'default_operation': operation},
        }

    def action_open_lock(self):
        return self._tp_period_wizard('lock')

    def action_open_unlock(self):
        return self._tp_period_wizard('unlock')

    def action_open_logs(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id('tp_hr_attendance.action_logs')
        action['domain'] = [('model', '=', self._name), ('res_id', '=', self.id)]
        action['display_name'] = self.env._('Nhật ký kỳ %(name)s', name=self.name)
        return action


class AttendanceLog(models.Model):
    _name = 'tp.hr.attendance.log'
    _description = 'Nhật ký chấm công'
    _order = 'id desc'
    _check_company_auto = True

    model = fields.Char('Đối tượng', readonly=True)
    res_id = fields.Integer('ID bản ghi', readonly=True)
    action = fields.Char('Thao tác', readonly=True, required=True)
    actor_id = fields.Many2one('res.users', 'Người thực hiện', readonly=True)
    company_id = fields.Many2one('res.company', 'Công ty', readonly=True)
    detail = fields.Text('Chi tiết', readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        deny_direct(self)
        return super().create(vals_list)

    def write(self, vals):
        raise AccessError(self.env._('Nhật ký chấm công không được sửa.'))

    def unlink(self):
        raise AccessError(self.env._('Nhật ký chấm công không được xóa.'))

    @api.model
    def _tp_log(self, record, action, detail=None):
        company = record.company_id if 'company_id' in record._fields else self.env.company
        return internal(self).create({
            'model': record._name, 'res_id': record.id, 'action': action, 'actor_id': self.env.user.id,
            'company_id': company.id, 'detail': json.dumps(detail or {}, ensure_ascii=False, default=str),
        })
