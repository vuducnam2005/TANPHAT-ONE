"""API-ready foundation for a real attendance device (HR-ATTENDANCE-SIMPLE-002, DEC-055).

Nothing here talks to a device: there is no cron, no HTTP route, no token and the live adapter is off.
A future adapter calls ``tp.hr.attendance.source.tp_ingest`` from server code; raw events are stored
immutable in a small staging table, deduplicated by fingerprint, mapped to employees only through the
source namespace code table, and the watermark moves in the same transaction as the events.
"""
import re
from zoneinfo import ZoneInfo

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

from .attendance_common import (
    DEFAULT_TZ,
    HR_MANAGER,
    deny_direct,
    internal,
    is_internal,
    require,
)
from .attendance_logic import CODE_MAX, EventError, fingerprint, normalize_event

ADVISORY_KEY = 761121
INGEST_MAX = 5000
CREDENTIAL_RE = re.compile(r'^[A-Z][A-Z0-9_]{2,63}$')
SOURCE_STATES = [
    ('not_configured', 'Chưa cấu hình'),
    ('ready', 'Sẵn sàng'),
    ('connected', 'Đang kết nối'),
    ('paused', 'Tạm dừng'),
    ('error', 'Lỗi kết nối'),
]
DIRECTION_LABELS = [('IN', 'Vào'), ('OUT', 'Ra'), ('UNKNOWN', 'Chưa rõ chiều')]
# What HR must get from the device vendor before a real adapter can be written (shown on "Nguồn dữ liệu").
VENDOR_CHECKLIST = [
    ('model', 'Hãng và model máy, phiên bản firmware'),
    ('api', 'Có API/SDK hay chỉ xuất file; tài liệu kỹ thuật chính thức'),
    ('direction', 'Máy gửi chiều Vào/Ra hay chỉ lượt quẹt (cần quy ước)'),
    ('event_id', 'Mỗi lượt có mã sự kiện duy nhất / con trỏ (cursor) đọc tiếp không'),
    ('timezone', 'Múi giờ máy và định dạng thời điểm'),
    ('network', 'Máy ở mạng nào; Odoo kéo dữ liệu hay máy đẩy lên'),
    ('auth', 'Cách xác thực (tài khoản, khóa); lưu ở biến môi trường server, không lưu trong mã nguồn'),
    ('frequency', 'Tần suất đồng bộ cần thiết và giới hạn của máy'),
    ('shifts', 'Ca làm, ca qua đêm và cách máy chốt ngày công'),
]
_SYSTEM_FIELDS = {'last_success_at', 'last_error_at', 'last_error', 'watermark', 'latest_event_at', 'live_enabled'}


class DeviceAdapter:
    """Base of a vendor adapter. A real one needs the checklist above; until then nothing is fetched."""

    def fetch(self, source, cursor):
        msg = 'Chưa có adapter cho máy chấm công; cần thông tin API/SDK từ nhà cung cấp.'
        raise NotImplementedError(msg)


class AttendanceSource(models.Model):
    _name = 'tp.hr.attendance.source'
    _description = 'Nguồn dữ liệu chấm công (API máy)'
    _order = 'company_id, name'
    _check_company_auto = True

    name = fields.Char('Tên nguồn', required=True)
    company_id = fields.Many2one('res.company', 'Công ty', required=True, default=lambda self: self.env.company, index=True)
    kind = fields.Selection([('device_api', 'API máy chấm công'), ('enti_api', 'API chấm công ENTI')], 'Loại', required=True, default='device_api')
    namespace = fields.Char('Không gian mã', required=True,
                            help='Mã nhân viên trên máy chỉ có nghĩa trong không gian này (vd. may-van-phong-1).')
    state = fields.Selection(SOURCE_STATES, 'Trạng thái', required=True, default='not_configured')
    live_enabled = fields.Boolean('Kết nối trực tiếp', default=False,
                                  help='Bật kết nối trực tiếp khi adapter và cấu hình xác thực đã sẵn sàng.')
    vendor = fields.Char('Hãng máy')
    device_model = fields.Char('Model máy')
    timezone = fields.Char('Múi giờ máy', default=DEFAULT_TZ, required=True)
    credential_ref = fields.Char('Tên biến môi trường xác thực',
                                 help='Chỉ ghi TÊN biến môi trường trên server (vd. TP_ATT_DEVICE_TOKEN); không ghi token.')
    last_success_at = fields.Datetime('Nhận thành công lần cuối', readonly=True)
    last_error_at = fields.Datetime('Lỗi lần cuối', readonly=True)
    last_error = fields.Char('Lỗi gần nhất', readonly=True)
    watermark = fields.Char('Mốc đã nhận', readonly=True, help='Con trỏ/mốc của máy; chỉ tiến cùng giao dịch đã ghi sự kiện.')
    latest_event_at = fields.Datetime('Sự kiện mới nhất', readonly=True)
    code_ids = fields.One2many('tp.hr.attendance.source.code', 'source_id', 'Mã nhân viên trên máy')
    note = fields.Text('Ghi chú')

    _namespace_unique = models.Constraint('UNIQUE(company_id, namespace)', 'Không gian mã đã dùng cho nguồn khác của công ty.')

    @api.constrains('credential_ref', 'namespace', 'timezone')
    def _check_safe_values(self):
        for source in self:
            if source.credential_ref and not CREDENTIAL_RE.match(source.credential_ref):
                raise ValidationError(self.env._('Chỉ ghi tên biến môi trường (chữ in hoa, số, gạch dưới); không dán token hoặc mật khẩu.'))
            if not re.match(r'^[a-z0-9][a-z0-9._-]{1,63}$', source.namespace or ''):
                raise ValidationError(self.env._('Không gian mã chỉ gồm chữ thường, số, dấu chấm, gạch ngang hoặc gạch dưới.'))
            try:
                ZoneInfo(source.timezone)
            except (KeyError, ValueError):
                raise ValidationError(self.env._('Múi giờ không hợp lệ.')) from None

    def _tp_guard(self, vals):
        if not is_internal(self):
            if set(vals) & _SYSTEM_FIELDS:
                raise AccessError(self.env._('Trạng thái nhận dữ liệu chỉ được hệ thống cập nhật.'))
            if not self.env.user.has_group(HR_MANAGER):
                raise AccessError(self.env._('Chỉ quản lý nhân sự được khai báo nguồn dữ liệu chấm công.'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._tp_guard(vals)
        return super().create(vals_list)

    def write(self, vals):
        self._tp_guard(vals)
        return super().write(vals)

    def unlink(self):
        if self.env['tp.hr.attendance.event'].sudo().search_count([('source_id', 'in', self.ids)], limit=1):
            raise UserError(self.env._('Nguồn đã có sự kiện; chuyển sang Tạm dừng thay vì xóa.'))
        self._tp_guard({})
        return super().unlink()

    def _lock(self):
        self.ensure_one()
        self.env.cr.execute('SELECT id FROM tp_hr_attendance_source WHERE id=%s FOR UPDATE', [self.id])
        self.invalidate_recordset()
        self.env.cr.execute('SELECT pg_advisory_xact_lock(%s, %s)', [ADVISORY_KEY, self.id])

    def tp_ingest(self, events, watermark=None):
        """Store device events once; returns counts. Server-side entry point for a future adapter.

        Requires the import capability for the source company and a source in state ``ready``. Invalid
        events are reported, never guessed; the watermark only moves when this transaction commits.
        """
        self.ensure_one()
        require(self.env, 'import', self.company_id)
        if self.state != 'ready':
            raise UserError(self.env._('Nguồn dữ liệu chưa ở trạng thái sẵn sàng nhận.'))
        if not isinstance(events, (list, tuple)):
            raise UserError(self.env._('Dữ liệu sự kiện phải là danh sách.'))
        if len(events) > INGEST_MAX:
            raise UserError(self.env._('Mỗi lần nhận tối đa %(max)s sự kiện.', max=INGEST_MAX))
        self._lock()
        now = fields.Datetime.now()
        normalized, rejected = [], []
        for index, raw in enumerate(events):
            if not isinstance(raw, dict):
                rejected.append({'index': index, 'error': 'Sự kiện phải là đối tượng.'})
                continue
            try:
                event = normalize_event(raw, self.namespace, self.timezone or DEFAULT_TZ, now)
            except EventError as exc:
                rejected.append({'index': index, 'error': str(exc)})
                continue
            event['fingerprint'] = fingerprint(event)
            normalized.append(event)
        Event = self.env['tp.hr.attendance.event'].sudo()
        known = set(Event.search([('company_id', '=', self.company_id.id),
                                  ('fingerprint', 'in', list({event['fingerprint'] for event in normalized}))]).mapped('fingerprint'))
        mapping = {code.external_code: code.employee_id.id for code in self.sudo().code_ids if code.employee_id.active}
        fresh, duplicate = [], 0
        for event in normalized:
            if event['fingerprint'] in known:
                duplicate += 1
                continue
            known.add(event['fingerprint'])
            employee_id = mapping.get(event['external_code'])
            fresh.append(dict(event, source_id=self.id, employee_id=employee_id or False, state='mapped' if employee_id else 'unmapped'))
        internal(Event).create(fresh)
        vals = {'last_success_at': now}
        if watermark is not None:
            vals['watermark'] = str(watermark)[:128]
        latest = max((event['timestamp'] for event in fresh), default=None)
        if latest and (not self.latest_event_at or latest > self.latest_event_at):
            vals['latest_event_at'] = latest
        internal(self).write(vals)
        result = {'received': len(events), 'created': len(fresh), 'duplicate': duplicate, 'rejected': len(rejected),
                  'unmapped': sum(1 for event in fresh if event['state'] == 'unmapped'), 'errors': rejected[:50]}
        self.env['tp.hr.attendance.log']._tp_log(self, 'source_ingest', {key: value for key, value in result.items() if key != 'errors'})
        return result

    def _tp_record_error(self, message):
        """Adapter failures are recorded without moving the watermark."""
        internal(self).write({'last_error_at': fields.Datetime.now(), 'last_error': str(message)[:240]})

    def _tp_remap(self):
        """Map events that arrived before HR declared the device code (namespace + company only, never by name)."""
        for source in self:
            mapping = {code.external_code: code.employee_id.id for code in source.sudo().code_ids if code.employee_id.active}
            waiting = self.env['tp.hr.attendance.event'].sudo().search([('source_id', '=', source.id), ('state', '=', 'unmapped'),
                                                                       ('external_code', 'in', list(mapping))])
            for event in waiting:
                internal(event).write({'employee_id': mapping[event.external_code], 'state': 'mapped'})

    @api.model
    def tp_sources_overview(self, params=None):
        """"Nguồn dữ liệu" page (HR/import only): Excel in use, API state, vendor checklist, compact import history."""
        company = self.env.company
        require(self.env, 'import', company)
        Batch = self.env['tp.hr.attendance.batch'].sudo()
        Day = self.env['tp.hr.attendance.day']
        tz_env = Day.with_context(tz=self.env.user.tz or DEFAULT_TZ)

        def stamp(value):
            return fields.Datetime.context_timestamp(tz_env, value).strftime('%d/%m/%Y %H:%M') if value else ''

        def day(value):
            return value.strftime('%d/%m/%Y') if value else ''

        updated, applied = Day._tp_updated(company)
        states = dict(self._fields['state'].selection)
        history = []
        for batch in Batch.search([('company_id', '=', company.id), ('state', '!=', 'draft')], order='id desc', limit=20):
            if batch.state == 'applied':
                result = f'Ghi {batch.applied_count} ngày · {batch.late_applied_count} tổng muộn'
            elif batch.state == 'partial':
                result = f'Áp một phần ({batch.applied_count} ngày) · Còn khác biệt chờ chọn nguồn'
            elif batch.state == 'preview':
                result = 'Đã đọc/Lưu nguồn – Chưa áp dụng'
            else:
                result = 'Đã bỏ qua nguồn, không ghi'
            history.append({
                'id': batch.id, 'file': batch.file_name or batch.name or '', 'user': (batch.applied_by or batch.create_uid).name or '',
                'at': stamp(batch.applied_at or batch.create_date), 'period': (
                    f'{day(batch.period_from)} – {day(batch.period_to)}' if batch.period_from and batch.period_to else ''),
                'state': batch.state, 'state_label': dict(Batch._fields['state'].selection).get(batch.state, ''),
                'result': result, 'source': 'Excel máy chấm công',
                'attention': batch.conflict_count + batch.unmapped_count + batch.name_conflict_count + batch.review_count
                + batch.late_conflict_count + batch.late_unmapped_count + batch.late_review_count,
            })
        sources = self.sudo().search([('company_id', '=', company.id)])
        Event = self.env['tp.hr.attendance.event'].sudo()
        Mapping = self.env['tp.hr.attendance.enti.mapping'].sudo()
        EntiDay = self.env['tp.hr.attendance.enti.day'].sudo()
        enti_sources = sources.filtered(lambda s: s.kind == 'enti_api')
        live_active = any(s.live_enabled for s in sources)
        mapped_count = Mapping.search_count([('company_id', '=', company.id), ('state', '=', 'mapped')])
        unmapped_count = Mapping.search_count([('company_id', '=', company.id), ('state', '!=', 'mapped')])
        enti_days_count = EntiDay.search_count([('company_id', '=', company.id)])
        enti_latest_day = EntiDay.search([('company_id', '=', company.id)], order='work_date desc', limit=1)

        api_label = 'Chưa cấu hình'
        if enti_sources:
            first_enti = enti_sources[0]
            if first_enti.live_enabled and first_enti.state == 'ready':
                api_label = 'Đang hoạt động (Trực tiếp)'
            else:
                api_label = states.get(first_enti.state, 'Chưa kết nối')
        elif sources:
            api_label = f'{len(sources)} nguồn đã khai báo'

        return {
            'excel': {'in_use': bool(applied), 'batches': len(applied), 'file': applied[:1].file_name or '' if applied else '',
                      'updated_at': updated['at'] if updated else '', 'data_to': updated['to'] if updated else '',
                      'note': 'Mỗi lần nhập là ảnh chụp theo file; dữ liệu không tự cập nhật theo thời gian thực.'},
            'api': {'label': api_label, 'live': live_active,
                    'events': Event.search_count([('company_id', '=', company.id)]),
                    'unmapped': Event.search_count([('company_id', '=', company.id), ('state', '=', 'unmapped')]),
                    'enti': {
                        'configured': bool(enti_sources),
                        'live': bool(enti_sources and enti_sources[0].live_enabled),
                        'state': enti_sources[:1].state if enti_sources else 'not_configured',
                        'last_success_at': stamp(enti_sources[:1].last_success_at) if enti_sources else '',
                        'last_error': enti_sources[:1].last_error or '' if enti_sources else '',
                        'mapped_count': mapped_count,
                        'unmapped_count': unmapped_count,
                        'days_count': enti_days_count,
                        'data_to': day(enti_latest_day.work_date) if enti_latest_day else '',
                    },
                    'sources': [{'id': source.id, 'name': source.name, 'namespace': source.namespace, 'state': source.state,
                                 'state_label': states[source.state], 'vendor': source.vendor or '', 'model': source.device_model or '',
                                 'last_success_at': stamp(source.last_success_at), 'latest_event_at': stamp(source.latest_event_at),
                                 'last_error': source.last_error or '', 'codes': len(source.code_ids)} for source in sources]},
            'checklist': [{'key': key, 'label': label} for key, label in VENDOR_CHECKLIST],
            'history': history,
            'can_configure': self.env.user.has_group(HR_MANAGER),
            'reference_hours': (self.env['ir.config_parameter'].sudo().get_str('tp_hr_attendance.reference_hours') or '08:30-17:00'),
        }


class AttendanceSourceCode(models.Model):
    _name = 'tp.hr.attendance.source.code'
    _description = 'Mã nhân viên trên nguồn API'
    _order = 'source_id, external_code'
    _check_company_auto = True

    source_id = fields.Many2one('tp.hr.attendance.source', 'Nguồn', required=True, ondelete='cascade', index=True)
    company_id = fields.Many2one(related='source_id.company_id', store=True, string='Công ty')
    external_code = fields.Char('Mã trên máy', required=True, help='Giữ nguyên dạng chuỗi, kể cả số 0 ở đầu.')
    employee_id = fields.Many2one('hr.employee', 'Nhân viên', required=True, check_company=True, index=True)
    note = fields.Char('Ghi chú')

    _code_unique = models.Constraint('UNIQUE(source_id, external_code)', 'Mã này đã gắn nhân viên trong cùng nguồn.')

    @api.constrains('external_code')
    def _check_code(self):
        for code in self:
            value = code.external_code or ''
            if not value or len(value) > CODE_MAX or any(ch.isspace() for ch in value):
                raise ValidationError(self.env._('Mã trên máy không được trống, quá dài hoặc có khoảng trắng.'))

    def _tp_guard(self):
        if not is_internal(self) and not self.env.user.has_group(HR_MANAGER):
            raise AccessError(self.env._('Chỉ quản lý nhân sự được gắn mã máy với nhân viên.'))

    @api.model_create_multi
    def create(self, vals_list):
        self._tp_guard()
        records = super().create(vals_list)
        records.source_id._tp_remap()
        return records

    def write(self, vals):
        self._tp_guard()
        if 'external_code' in vals or 'employee_id' in vals or 'source_id' in vals:
            used = self.env['tp.hr.attendance.event'].sudo().search_count([
                ('source_id', 'in', self.source_id.ids), ('external_code', 'in', self.mapped('external_code')), ('state', '=', 'mapped')], limit=1)
            if used:
                raise UserError(self.env._('Mã đã dùng cho sự kiện; không đổi người hoặc mã, hãy khai báo mã mới.'))
        result = super().write(vals)
        self.source_id._tp_remap()
        return result

    def unlink(self):
        self._tp_guard()
        return super().unlink()


class AttendanceEvent(models.Model):
    _name = 'tp.hr.attendance.event'
    _description = 'Sự kiện chấm công thô (API máy)'
    _order = 'timestamp desc, id desc'
    _check_company_auto = True

    source_id = fields.Many2one('tp.hr.attendance.source', 'Nguồn', required=True, readonly=True, index=True, ondelete='restrict')
    company_id = fields.Many2one(related='source_id.company_id', store=True, string='Công ty', index=True)
    namespace = fields.Char('Không gian mã', required=True, readonly=True)
    source_event_id = fields.Char('Mã sự kiện của máy', readonly=True)
    external_code = fields.Char('Mã trên máy', required=True, readonly=True, index=True)
    employee_id = fields.Many2one('hr.employee', 'Nhân viên', readonly=True, index=True)
    timestamp = fields.Datetime('Thời điểm', required=True, readonly=True, index=True)
    tz = fields.Char('Múi giờ', required=True, readonly=True)
    local_date = fields.Date('Ngày theo múi giờ máy', required=True, readonly=True, index=True)
    direction = fields.Selection(DIRECTION_LABELS, 'Chiều', required=True, readonly=True)
    received_at = fields.Datetime('Nhận lúc', required=True, readonly=True)
    fingerprint = fields.Char('Dấu vân sự kiện', required=True, readonly=True)
    state = fields.Selection([('mapped', 'Đã gắn nhân viên'), ('unmapped', 'Chưa gắn nhân viên')], 'Đối chiếu',
                             required=True, readonly=True, index=True)

    _fingerprint_unique = models.UniqueIndex('(company_id, fingerprint)', 'Sự kiện đã được nhận.')

    @api.model_create_multi
    def create(self, vals_list):
        deny_direct(self)
        return super().create(vals_list)

    def write(self, vals):
        # Raw events are immutable; only the mapping step may attach an employee later.
        deny_direct(self)
        if set(vals) - {'employee_id', 'state'}:
            raise AccessError(self.env._('Sự kiện thô không được sửa.'))
        return super().write(vals)

    def unlink(self):
        raise AccessError(self.env._('Sự kiện thô không được xóa.'))
