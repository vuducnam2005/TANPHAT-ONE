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
    can,
    can_manage_enti_images,
    deny_direct,
    internal,
    is_correction_admin,
    is_internal,
    local_today,
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
_SYSTEM_FIELDS = {
    'last_success_at',
    'last_error_at',
    'last_error',
    'watermark',
    'latest_event_at',
    'live_enabled',
    'last_image_sync_at',
    'last_image_sync_state',
    'last_image_sync_message',
}
IMAGE_SYNC_STATES = [
    ('idle', 'Chưa đồng bộ'),
    ('success', 'Đã đồng bộ'),
    ('partial', 'Hoàn tất (Có ảnh lỗi)'),
    ('error', 'Lỗi đồng bộ'),
]


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
    prefer_manual_image = fields.Boolean(
        'Ưu tiên ảnh thủ công',
        default=False,
        help='Khi bật, đồng bộ ảnh ENTI sẽ không ghi đè ảnh đã được tải lên thủ công trong Odoo.',
    )
    last_image_sync_at = fields.Datetime('Đồng bộ ảnh gần nhất', readonly=True)
    last_image_sync_state = fields.Selection(
        IMAGE_SYNC_STATES,
        'Trạng thái đồng bộ ảnh',
        default='idle',
        readonly=True,
    )
    last_image_sync_message = fields.Char('Thông báo đồng bộ ảnh gần nhất', readonly=True)
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
            if not can_manage_enti_images(self.env, self.company_id[:1] if self else self.env.company):
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
        """Administration: connection health, pending mapping, bounded sync log and export scope.

        Existing backend rights and canonical attendance calculations remain authoritative.
        """
        company = self.env.company
        if not is_correction_admin(self.env, company):
            require(self.env, 'import', company)
        Day = self.env['tp.hr.attendance.day']
        sources = self.sudo().search([('company_id', '=', company.id)])
        Event = self.env['tp.hr.attendance.event'].sudo()
        Mapping = self.env['tp.hr.attendance.enti.mapping'].sudo()
        EntiDay = self.env['tp.hr.attendance.enti.day'].sudo()
        enti_sources = sources.filtered(lambda s: s.kind == 'enti_api')
        tz_name = enti_sources[:1].timezone if enti_sources else DEFAULT_TZ
        tz_env = Day.with_context(tz=tz_name or DEFAULT_TZ)

        def stamp(value):
            return fields.Datetime.context_timestamp(tz_env, value).strftime('%d/%m/%Y %H:%M') if value else ''

        def day(value):
            return value.strftime('%d/%m/%Y') if value else ''

        states = dict(self._fields['state'].selection)
        live_active = any(s.live_enabled for s in sources)
        mapped_count = Mapping.search_count([('company_id', '=', company.id), ('state', '=', 'mapped')])
        unmapped_count = Mapping.search_count([('company_id', '=', company.id), ('state', '!=', 'mapped')])
        enti_days_count = EntiDay.search_count([('company_id', '=', company.id)])
        enti_latest_day = EntiDay.search([('company_id', '=', company.id)], order='work_date desc', limit=1)
        mapping_states = dict(Mapping._fields['state'].selection)
        unmapped_people = [{
            'id': row.id, 'code': row.ma_nv or '', 'name': row.ten_nv or '', 'department': row.ten_bp or '',
            'state': row.state, 'state_label': mapping_states.get(row.state, ''), 'reason': row.match_reason or '',
            'candidate': row.employee_id.name or '',
        } for row in Mapping.search([('company_id', '=', company.id), ('state', '!=', 'mapped')], order='state desc, ten_nv, id', limit=30)]

        today = local_today(DEFAULT_TZ)
        strip = Day._tp_source_strip(company, today)
        health = strip['health']
        cron_active = strip.get('cron_active', True)

        api_label = 'Chưa cấu hình'
        if enti_sources:
            first_enti = enti_sources[0]
            if health == 'ok':
                api_label = 'Đang hoạt động (Trực tiếp)'
            elif health == 'error':
                api_label = 'Cần kiểm tra đồng bộ'
            elif health == 'stale':
                api_label = 'Đồng bộ đang chậm' if first_enti.last_success_at else 'Chờ đồng bộ thành công'
            elif not cron_active or not first_enti.live_enabled or first_enti.state == 'paused':
                api_label = 'Đồng bộ tự động đang tắt'
            else:
                api_label = states.get(first_enti.state, 'Chưa kết nối')
        elif sources:
            api_label = f'{len(sources)} nguồn đã khai báo'

        # The administration preview uses the same company and read ACLs as the full native log.
        Log = self.env['tp.hr.attendance.enti.sync.log']
        sync_logs = []
        last_duration_seconds = 0.0
        if Log.has_access('read'):
            recent_logs = Log.search([('company_id', '=', company.id)], order='synced_at desc, id desc', limit=5)
            if recent_logs:
                last_duration_seconds = round(recent_logs[0].duration_seconds or 0.0, 2)
            for log in recent_logs:
                has_img_warn = bool(log.message and ' lỗi,' in log.message and ' 0 lỗi,' not in log.message)
                is_warn = log.state == 'success' and (bool(log.kept_count) or has_img_warn)
                dur = round(log.duration_seconds or 0.0, 2)
                sync_logs.append({
                    'id': log.id,
                    'at': stamp(log.synced_at),
                    'status': 'partial' if is_warn else log.state,
                    'status_label': (
                        'Hoàn tất (Có lưu ý)' if is_warn
                        else ('Thành công' if log.state == 'success' else 'Chưa thành công')
                    ),
                    'days_received': log.days_received,
                    'days_applied': log.days_applied,
                    'changed_count': log.changed_count,
                    'kept_count': log.kept_count,
                    'unmapped': log.unmapped_count,
                    'duration_seconds': dur,
                    'has_warning': is_warn,
                    'from': day(log.start_date),
                    'to': day(log.end_date),
                })
        can_manage_img = can_manage_enti_images(self.env, company)
        image_sync = self._tp_build_image_sync_overview(company, enti_sources, tz_env, params=params)

        return {
            'today': today.isoformat(),
            'departments': Day._tp_departments(company),
            'health': health,
            'cron_active': cron_active,
            'mapping': {
                'suggested': Mapping.search_count([('company_id', '=', company.id), ('state', '=', 'suggested')]),
                'unmapped': Mapping.search_count([('company_id', '=', company.id), ('state', '=', 'unmapped')]),
            },
            'sync_logs': sync_logs,
            'image_sync': image_sync,
            'can_view_logs': Log.has_access('read'),
            'can_review': is_correction_admin(self.env, company),
            'can_lock': can(self.env, 'lock', company),
            'can_export': Day._tp_can_export_shared(company),
            'api': {'label': api_label, 'live': live_active and cron_active,
                    'events': Event.search_count([('company_id', '=', company.id)]),
                    'unmapped': Event.search_count([('company_id', '=', company.id), ('state', '=', 'unmapped')]),
                    'enti': {
                        'configured': bool(enti_sources),
                        'live': bool(enti_sources and enti_sources[0].live_enabled and cron_active),
                        'cron_active': cron_active,
                        'state': enti_sources[:1].state if enti_sources else 'not_configured',
                        'last_success_at': stamp(enti_sources[:1].last_success_at) if enti_sources else '',
                        'last_error': enti_sources[:1].last_error or '' if enti_sources else '',
                        'last_duration_seconds': last_duration_seconds,
                        'mapped_count': mapped_count,
                        'unmapped_count': unmapped_count,
                        'days_count': enti_days_count,
                        'data_to': day(enti_latest_day.work_date) if enti_latest_day else '',
                        'unmapped_people': unmapped_people,
                    },
                    'sources': [{'id': source.id, 'name': source.name, 'namespace': source.namespace, 'state': source.state,
                                 'state_label': states[source.state], 'vendor': source.vendor or '', 'model': source.device_model or '',
                                 'last_success_at': stamp(source.last_success_at), 'latest_event_at': stamp(source.latest_event_at),
                                 'last_error': source.last_error or '', 'codes': len(source.code_ids)} for source in sources]},
            'checklist': [{'key': key, 'label': label} for key, label in VENDOR_CHECKLIST],
            'can_configure': can_manage_img,
            'reference_hours': (self.env['ir.config_parameter'].sudo().get_str('tp_hr_attendance.reference_hours') or '08:30-17:00'),
        }

    @api.model
    def tp_enti_image_logs(self, params=None):
        """Return filtered ENTI employee image sync overview and rows for the Admin UI."""
        company = self.env.company
        if not is_correction_admin(self.env, company):
            require(self.env, 'import', company)
        Day = self.env['tp.hr.attendance.day']
        enti_sources = self.sudo().search([('company_id', '=', company.id), ('kind', '=', 'enti_api')])
        tz_name = enti_sources[:1].timezone if enti_sources else DEFAULT_TZ
        tz_env = Day.with_context(tz=tz_name or DEFAULT_TZ)
        return self._tp_build_image_sync_overview(company, enti_sources, tz_env, params=params)

    @api.model
    def _tp_build_image_sync_overview(self, company, enti_sources, tz_env, params=None):
        def stamp(value):
            return fields.Datetime.context_timestamp(tz_env, value).strftime('%d/%m/%Y %H:%M') if value else ''

        ImageModel = self.env['tp.hr.attendance.enti.employee.image'].sudo()
        Mapping = self.env['tp.hr.attendance.enti.mapping'].sudo()
        first_enti = enti_sources[:1]
        sync_states = dict(IMAGE_SYNC_STATES)
        sync_state = first_enti.last_image_sync_state if first_enti else 'idle'

        total_mappings = Mapping.search_count([('company_id', '=', company.id)])
        total_images = ImageModel.search_count([('company_id', '=', company.id)])
        total_employees = max(total_mappings, total_images)
        synced_count = ImageModel.search_count([
            ('company_id', '=', company.id),
            ('mapping_state', '=', 'mapped'),
            ('state', 'in', ('downloaded', 'unchanged')),
        ])
        downloaded_count = ImageModel.search_count([
            ('company_id', '=', company.id),
            ('mapping_state', '=', 'mapped'),
            ('state', '=', 'downloaded'),
        ])
        unchanged_count = ImageModel.search_count([
            ('company_id', '=', company.id),
            ('mapping_state', '=', 'mapped'),
            ('state', '=', 'unchanged'),
        ])
        no_image_count = ImageModel.search_count([
            ('company_id', '=', company.id),
            ('state', '=', 'no_image'),
        ])
        failed_count = ImageModel.search_count([
            ('company_id', '=', company.id),
            ('state', '=', 'failed'),
        ])
        unmapped_count = Mapping.search_count([
            ('company_id', '=', company.id),
            ('state', '!=', 'mapped'),
        ])

        p = params or {}
        filter_state = str(p.get('image_state') or p.get('state') or '').strip()
        filter_dept = p.get('image_department_id') or p.get('department_id') or ''
        filter_search = str(p.get('image_search') or p.get('search') or '').strip()

        domain = [('company_id', '=', company.id)]
        if filter_state == 'unmapped':
            domain.append(('mapping_state', '!=', 'mapped'))
        elif filter_state == 'synced':
            domain.extend([('mapping_state', '=', 'mapped'), ('state', 'in', ('downloaded', 'unchanged'))])
        elif filter_state in ('downloaded', 'unchanged', 'no_image', 'failed', 'pending'):
            domain.append(('state', '=', filter_state))

        if filter_dept not in ('', None, False, 'all'):
            try:
                domain.append(('department_id', '=', int(filter_dept)))
            except (TypeError, ValueError):
                pass

        if filter_search:
            domain.extend([
                '|', '|', '|', '|',
                ('ten_nv', 'ilike', filter_search),
                ('ma_nv', 'ilike', filter_search),
                ('employee_id.name', 'ilike', filter_search),
                ('employee_id.tp_employee_code', 'ilike', filter_search),
                ('ten_bp', 'ilike', filter_search),
            ])

        records = ImageModel.search(domain, order='state asc, ten_nv asc, id asc', limit=200)
        rows = [{
            'id': rec.id,
            'mapping_id': rec.mapping_id.id or False,
            'key_nv': rec.key_nv or '',
            'ma_nv': rec.ma_nv or '',
            'ten_nv': rec.ten_nv or '',
            'ten_bp': rec.ten_bp or '',
            'employee_id': rec.employee_id.id or False,
            'employee_name': rec.employee_id.name or '',
            'employee_code': rec.employee_code or '',
            'department_id': rec.department_id.id or False,
            'department_name': rec.department_id.name or rec.ten_bp or '',
            'mapping_state': rec.mapping_state or 'unmapped',
            'state': rec.state,
            'status_label': rec.status_label,
            'image_source': rec.image_source or 'none',
            'image_mime': rec.image_mime or '',
            'image_size': rec.image_size or 0,
            'downloaded_at': stamp(rec.downloaded_at),
            'last_seen_at': stamp(rec.last_seen_at),
            'error_message': rec.error_message or '',
            'has_enti_image': bool(rec.with_context(bin_size=True).enti_image_1920),
            'has_odoo_image': bool(rec.employee_id),
        } for rec in records]

        return {
            'state': sync_state,
            'state_label': sync_states.get(sync_state, 'Chưa đồng bộ'),
            'last_sync_at': stamp(first_enti.last_image_sync_at) if first_enti else '',
            'message': (first_enti.last_image_sync_message or '') if first_enti else '',
            'prefer_manual_image': bool(first_enti.prefer_manual_image) if first_enti else False,
            'total_employees': total_employees,
            'synced_count': synced_count,
            'downloaded_count': downloaded_count,
            'unchanged_count': unchanged_count,
            'no_image_count': no_image_count,
            'failed_count': failed_count,
            'unmapped_count': unmapped_count,
            'total_rows': len(rows),
            'rows': rows,
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
