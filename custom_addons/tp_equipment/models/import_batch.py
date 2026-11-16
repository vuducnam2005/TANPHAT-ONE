"""Read-only XLSX preview. Source cells never execute formulas or create HR records."""
import base64
import hashlib
import io
import json
import math
import re
import unicodedata
import zipfile
from datetime import date, datetime

from openpyxl import load_workbook

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.tools import SQL

from .common import (
    ASSET_CLASS,
    INTERNAL,
    OWNERSHIP,
    TECH_STATE,
    check_admin,
    lock_records,
)


def _norm(value):
    text = unicodedata.normalize('NFKD', str(value or '')).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'\s+', ' ', text).strip()


_NETWORK = re.compile(r'(?i)(?:\b(?:\d{1,3}\.){3}\d{1,3}\b|\b(?:[0-9a-f]{2}[:-]){5}[0-9a-f]{2}\b)')


def _safe(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, str):
        return _NETWORK.sub('[địa chỉ mạng đã loại]', value)[:16000]
    return value if isinstance(value, (int, float, bool)) or value is None else str(value)


def _network_header(value):
    return bool(re.search(r'\b(ip|mac|ipv4|ipv6)\b', _norm(value)))


TARGETS = [('ignore', 'Bỏ qua'), ('name', 'Tên / thiết bị'), ('holder', 'Người / nơi giữ'),
           ('config', 'Cấu hình'), ('condition', 'Hiện trạng'), ('solution', 'Phương án'),
           ('amount', 'Thành tiền'), ('quantity', 'Số lượng'),
           # Source text kept verbatim on the record; confirmed values live on the line (EQUIP-DATA-001).
           ('source_code', 'Mã / STT nguồn'), ('category', 'Phân loại theo nguồn'), ('ownership', 'Sở hữu theo nguồn'),
           ('model', 'Hãng / model theo nguồn'), ('software', 'HĐH / phần mềm theo nguồn'),
           ('status', 'Trạng thái theo nguồn'), ('date', 'Ngày theo nguồn'), ('warranty', 'Bảo hành theo nguồn'),
           ('equipment_text', 'Thiết bị hiện có theo nguồn')]
PENDING = ('unknown', 'wait', 'missing')
APPLICABLE = ('equipment', 'service', 'proposal')
_LICENSE_MARKERS = [('licensed', ('co ban quyen',)), ('unknown', ('ko xac minh', 'khong xac minh')),
                    ('unlicensed', ('khong ban quyen', 'khong ban quye'))]


def _software_commands(text):
    """One declared OS / Office entry per source line; the marker is a declaration, never a license check."""
    commands = []
    for part in re.split(r'[\r\n]+', text or ''):
        name, _sep, marker = part.partition('—')
        name = name.strip(' -/')
        if not name:
            continue
        found = _norm(marker)
        declared = 'unknown'
        # "không bản quyền" contains "bản quyền": test the negative markers first.
        for value, words in reversed(_LICENSE_MARKERS):
            if any(word in found for word in words):
                declared = value
                break
        kind = 'office' if 'office' in _norm(name) else 'os' if re.match(r'(?i)win', name) else 'other'
        commands.append((0, 0, {'kind': kind, 'name': name, 'license_declared': declared, 'license_check': 'not_checked',
                                'note': ('Khai báo nguồn: %s' % marker.strip())[:250] if marker.strip() else 'Nguồn không ghi bản quyền'}))
    return commands


DISPOSITIONS = [('header', 'Tiêu đề cột'), ('section', 'Phân đoạn / dòng trống'), ('missing', 'Thiếu thông tin'), ('service', 'Dịch vụ'), ('na', 'N/a / không có máy'),
                ('unknown', 'Chưa phân loại'), ('wait', 'Chờ xác minh'), ('skip', 'Bỏ qua có lý do'),
                ('equipment', 'Tạo thiết bị nháp'), ('proposal', 'Dòng đề xuất nháp'), ('total', 'Tổng đối chiếu')]


class EquipmentImportBatch(models.Model):
    _name = 'tp.equipment.import.batch'
    _description = 'Nhập và đối chiếu nguồn thiết bị'
    _inherit = ['tp.equipment.secure.mixin']
    _order = 'id desc'

    name = fields.Char('Tên đợt nhập', required=True, default='/', readonly=True, copy=False)
    company_id = fields.Many2one('res.company', 'Công ty', required=True, default=lambda self: self.env.company)
    kind = fields.Selection([('equipment', 'Danh mục thiết bị'), ('proposal', 'Đề xuất')], string='Loại nguồn', required=True, default='equipment')
    file = fields.Binary('Tệp XLSX', store=False, attachment=False,
                         help='Chỉ đọc trong bộ nhớ; không lưu workbook gốc hoặc cột IP/MAC.')
    file_name = fields.Char('Tên tệp')
    file_hash = fields.Char('SHA-256', readonly=True, copy=False, index=True)
    state = fields.Selection([('draft', 'Chưa tải nguồn'), ('preview', 'Đối chiếu'),
                              ('partial', 'Đã áp dụng một phần — còn dòng chờ'), ('applied', 'Đã áp dụng')],
                             string='Trạng thái', default='draft', required=True, readonly=True, copy=False)
    proposal_title = fields.Char('Tiêu đề đề xuất xác nhận', help='Dùng cho hồ sơ đề xuất tạo từ nguồn; trống thì lấy tên đợt.')
    pending_count = fields.Integer('Dòng còn chờ', compute='_compute_pending_count')
    line_ids = fields.One2many('tp.equipment.import.line', 'batch_id', 'Mọi dòng nguồn')
    column_ids = fields.One2many('tp.equipment.import.column', 'batch_id', 'Ánh xạ cột')
    proposal_id = fields.Many2one('tp.equipment.proposal', 'Đề xuất đã tạo', readonly=True, ondelete='restrict', copy=False)
    note = fields.Text('Ghi chú / xác nhận thay đổi nguồn')
    previous_batch_id = fields.Many2one('tp.equipment.import.batch', 'Phiên bản nguồn trước', ondelete='restrict')
    identity_confirmed = fields.Boolean('Đã đối chiếu khác biệt với phiên bản trước')
    applied_by_id = fields.Many2one('res.users', 'Người áp dụng', readonly=True, copy=False)
    applied_date = fields.Datetime('Ngày áp dụng', readonly=True, copy=False)

    _source_unique = models.Constraint('UNIQUE(company_id, kind, file_hash)', 'Nguồn này đã có đợt nhập. Mở lại đợt hiện có để tiếp tục.')

    @api.depends('line_ids.disposition', 'line_ids.equipment_id', 'line_ids.proposal_line_id')
    def _compute_pending_count(self):
        for batch in self:
            batch.pending_count = len(batch.line_ids.filtered(lambda line: line.disposition in PENDING))

    @api.model_create_multi
    def create(self, vals_list):
        check_admin(self.env)
        uploads = []
        clean = []
        for values in vals_list:
            vals = dict(values)
            uploads.append(vals.pop('file', False))
            for key in ('state', 'file_hash', 'proposal_id', 'applied_by_id', 'applied_date', 'line_ids', 'column_ids'):
                vals.pop(key, None)
            vals['name'] = self.env['ir.sequence'].sudo().next_by_code('tp.equipment.import.batch') or '/'
            clean.append(vals)
        records = super().create(clean)
        for record, upload in zip(records, uploads):
            if upload:
                record._preview_bytes(upload)
        return records

    def write(self, vals):
        check_admin(self.env)
        upload = vals.get('file')
        values = dict(vals)
        values.pop('file', None)
        if set(values) & {'name', 'state', 'file_hash', 'proposal_id', 'applied_by_id', 'applied_date', 'line_ids', 'column_ids'}:
            raise UserError(_('Dữ liệu nguồn và trạng thái chỉ thay đổi qua thao tác nhập.'))
        if any(b.state == 'applied' for b in self):
            raise UserError(_('Đợt đã áp dụng được giữ nguyên để truy vết.'))
        if any(b.file_hash for b in self) and set(values) & {'kind', 'company_id'}:
            raise UserError(_('Không đổi loại hoặc công ty sau khi đọc nguồn.'))
        self._check_company_scope()
        result = super().write(values)
        if upload:
            self.ensure_one()
            self._preview_bytes(upload)
        return result

    def unlink(self):
        check_admin(self.env)
        if any(b.state != 'draft' for b in self):
            raise UserError(_('Giữ đợt đối chiếu và nguồn đã đọc để truy vết.'))
        return super().unlink()

    def _check_company_scope(self):
        check_admin(self.env)
        if any(batch.company_id not in self.env.companies for batch in self):
            raise UserError(_('Công ty ngoài phạm vi được phép.'))

    def _lock(self):
        check_admin(self.env)
        self.ensure_one()
        if self.company_id not in self.env.companies:
            raise UserError(_('Công ty ngoài phạm vi được phép.'))
        self.env.cr.execute(SQL('SELECT id FROM tp_equipment_import_batch WHERE id = %s FOR UPDATE', self.id))
        self.invalidate_recordset()

    def _preview_bytes(self, encoded):
        self._lock()
        if self.file_hash:
            raise UserError(_('Nguồn đã đọc là bất biến. Tạo đợt mới cho tệp thay đổi.'))
        try:
            raw = base64.b64decode(encoded, validate=True)
            if len(raw) > 15 * 1024 * 1024:
                raise ValueError('size')  # noqa: EM101, TRY301
            with zipfile.ZipFile(io.BytesIO(raw)) as archive:
                if sum(item.file_size for item in archive.infolist()) > 80 * 1024 * 1024:
                    raise ValueError('expanded size')  # noqa: EM101, TRY301
                if any('vbaproject' in item.filename.lower() for item in archive.infolist()):
                    raise ValueError('macros')  # noqa: EM101, TRY301
            digest = hashlib.sha256(raw).hexdigest()
            existing = self.search([('company_id', '=', self.company_id.id), ('kind', '=', self.kind),
                                    ('file_hash', '=', digest), ('id', '!=', self.id)], limit=1)
            if existing:
                raise UserError(_('Tệp này đã có trong đợt %s. Mở đợt đó để tiếp tục, không tạo lại.') % existing.display_name)  # noqa: TRY301
            formulas = load_workbook(io.BytesIO(raw), data_only=False, keep_links=False)
            cached = load_workbook(io.BytesIO(raw), data_only=True, keep_links=False)
        except UserError:
            raise
        except Exception as exc:
            raise UserError(_('Không đọc được XLSX hợp lệ (giới hạn 15 MB, không macro).')) from exc
        try:
            for sheet in formulas:
                if sheet.max_row > 20000 or sheet.max_column > 200:
                    raise UserError(_('Sheet vượt giới hạn 20.000 dòng / 200 cột.'))
                cache = cached[sheet.title]
                merged = {}
                for area in sheet.merged_cells.ranges:
                    for row in range(area.min_row, area.max_row + 1):
                        for column in range(area.min_col, area.max_col + 1):
                            merged[row, column] = (area.min_row, area.min_col)
                ignored = set()
                # Scan the full sheet before storing anything: later repeated IP/MAC headers also exclude the column.
                for row in sheet.iter_rows():
                    for cell in row:
                        if _network_header(cell.value):
                            ignored.add(cell.column)
                columns = {}
                for number in range(1, sheet.max_column + 1):
                    labels = [str(sheet.cell(row, number).value or '') for row in range(1, min(sheet.max_row, 20) + 1)]
                    label = next((v for v in labels if v.strip()), '')
                    text = _norm(' '.join(labels))
                    target = 'ignore'
                    for candidate, words in [('amount', ['thanh tien', 'du toan']), ('quantity', ['so luong']),
                                             ('holder', ['nguoi su dung', 'ho va ten', 'nhan vien']),
                                             ('config', ['cau hinh']), ('condition', ['hien trang', 'tinh trang']),
                                             ('solution', ['phuong an']), ('name', ['ten thiet bi', 'thiet bi', 'noi dung'])]:
                        if any(word in text for word in words):
                            target = candidate
                            break
                    columns[number] = self.env['tp.equipment.import.column'].with_context(tp_import_internal=INTERNAL).create({
                        'batch_id': self.id, 'sheet_name': sheet.title, 'column_number': number,
                        'source_label': '[IP/MAC đã loại]' if number in ignored else _safe(label),
                        'target_field': 'ignore' if number in ignored else target, 'network_excluded': number in ignored})
                for number in range(1, sheet.max_row + 1):
                    cells = []
                    texts = []
                    for column in range(1, sheet.max_column + 1):
                        if column in ignored:
                            continue
                        anchor = merged.get((number, column), (number, column))
                        cell = sheet.cell(*anchor)
                        value = cache.cell(*anchor).value if cell.data_type == 'f' else cell.value
                        cells.append({'cell': sheet.cell(number, column).coordinate, 'column': column,
                                      'raw': _safe(cell.value), 'cached': _safe(value),
                                      'merged_from': cell.coordinate if anchor != (number, column) else None,
                                      'formula': cell.data_type == 'f'})
                        if value is not None:
                            texts.append(str(value))
                    joined = _norm(' '.join(texts))
                    disposition = 'unknown'
                    if not joined:
                        disposition = 'section'
                    elif any(token in joined for token in ['tong cong', 'tong tien']):
                        disposition = 'total'
                    elif any(token in joined for token in ['ftth', 'internet', 'duong truyen']):
                        disposition = 'service'
                    elif 'thieu thong tin' in joined or 'chua ro' in joined:
                        disposition = 'missing'
                    elif joined in ('n/a', 'na') or 'chua co may' in joined or 'khong co may' in joined:
                        disposition = 'na'
                    elif any(token in joined for token in ['stt', 'ho va ten', 'ten thiet bi', 'nguoi lap', 'nguoi duyet']):
                        disposition = 'header'
                    self.env['tp.equipment.import.line'].with_context(tp_import_internal=INTERNAL).create({
                        'batch_id': self.id, 'sheet_name': sheet.title, 'row_number': number,
                        'disposition': disposition, 'source_json': json.dumps(cells, ensure_ascii=False)})
            super().write({'file_hash': digest, 'state': 'preview'})
        finally:
            formulas.close()
            cached.close()
        return True

    def action_preview(self):
        check_admin(self.env)
        self.ensure_one()
        if not self.file_hash:
            raise UserError(_('Tải và lưu tệp XLSX trước khi đối chiếu.'))
        return True

    def action_apply(self):
        """Apply confirmed lines. Pending lines with a reason stay on this batch (state partial) for a later run;
        lines already linked are never applied twice."""
        self._lock()
        if self.state == 'applied':
            return True
        if self.state not in ('preview', 'partial'):
            raise UserError(_('Đọc nguồn và đối chiếu trước khi áp dụng.'))
        if self.previous_batch_id and (not self.identity_confirmed or not self.note):
            raise UserError(_('Ghi nhận khác biệt và xác nhận định danh so với đợt trước. Không dùng STT làm định danh.'))
        prior = self.search([('company_id', '=', self.company_id.id), ('kind', '=', self.kind),
                             ('state', 'in', ('applied', 'partial')), ('id', '!=', self.id)], limit=1)
        if prior:
            if not self.identity_confirmed or not (self.note or '').strip():
                raise UserError(_('Đã có nguồn áp dụng: xác nhận đợt độc lập hoặc phiên bản mới và ghi lý do đối chiếu định danh.'))
            if self.previous_batch_id and (self.previous_batch_id.company_id != self.company_id or
                                           self.previous_batch_id.kind != self.kind or
                                           self.previous_batch_id.state not in ('applied', 'partial') or
                                           self.previous_batch_id == self):
                raise UserError(_('Đợt nguồn trước phải cùng công ty, cùng loại và đã áp dụng.'))
        unresolved = self.line_ids.filtered(lambda line: line.disposition in PENDING)
        if unresolved and self.kind == 'proposal':
            raise UserError(_('Đề xuất cần đối chiếu đủ mọi dòng với tổng nguồn: còn %s dòng chưa giải quyết.') % len(unresolved))
        unexplained = unresolved.filtered(lambda line: not (line.resolution_note or '').strip())
        if unexplained:
            raise UserError(_('Dòng %s chưa giải quyết: ghi lý do / việc cần bổ sung để giữ chờ, hoặc phân loại lại.')
                            % ', '.join(str(n) for n in unexplained.mapped('row_number')[:10]))
        done = self.line_ids.filtered(lambda line: line.equipment_id or line.proposal_line_id)
        applicable = self.line_ids.filtered(lambda line: line.disposition in APPLICABLE) - done
        if not applicable:
            if done:
                return True  # replay: nothing new to apply, nothing duplicated
            raise UserError(_('Không có dòng được xác nhận để áp dụng.'))
        matched_equipment = set()
        matched_proposals = set()
        for line in applicable:
            line._validate_resolution()
            if prior and (not line.identity_confirmed or not (line.resolution_note or '').strip()):
                raise UserError(_('Mọi dòng áp dụng từ nguồn sau cần xác nhận định danh và lý do: thiết bị/dòng đã có hoặc thực sự mới.'))
            if line.identity_resolution == 'existing':
                target = line.match_equipment_id if self.kind == 'equipment' else line.match_proposal_line_id
                if not target:
                    raise UserError(_('Chọn ID hiện có cho dòng đã xác nhận trùng định danh.'))
                company = target.company_id if self.kind == 'equipment' else target.proposal_id.company_id
                if company != self.company_id:
                    raise UserError(_('Định danh hiện có phải thuộc cùng công ty.'))
                seen = matched_equipment if self.kind == 'equipment' else matched_proposals
                if target.id in seen:
                    raise UserError(_('Hai dòng nguồn không được đối chiếu cùng một định danh.'))
                seen.add(target.id)
                if self.previous_batch_id:
                    previous_targets = (self.previous_batch_id.line_ids.equipment_id if self.kind == 'equipment'
                                        else self.previous_batch_id.line_ids.proposal_line_id)
                    if target not in previous_targets:
                        raise UserError(_('ID được chọn không thuộc nguồn trước. Chọn đúng phiên bản nguồn hoặc xác nhận là đợt độc lập.'))
            elif line.match_equipment_id or line.match_proposal_line_id:
                raise UserError(_('Dòng thực sự mới không được kèm ID đã có.'))
        new_lines = applicable.filtered(lambda line: line.identity_resolution == 'new')
        proposal = self.proposal_id
        if self.kind == 'proposal':
            if any(line.disposition != 'proposal' for line in applicable):
                raise UserError(_('Đợt đề xuất chỉ được tạo dòng đề xuất.'))
            totals = self.line_ids.filtered(lambda line: line.disposition == 'total' and line.amount_known)
            if len(totals) != 1 or any(not line.amount_known for line in applicable):
                raise UserError(_('Cần một tổng nguồn đã xác nhận và thành tiền đã biết cho mọi dòng đề xuất để đối chiếu.'))
            if self.company_id.currency_id.compare_amounts(sum(applicable.mapped('amount')), totals.amount) != 0:
                raise UserError(_('Tổng dòng đề xuất không khớp tổng nguồn đã xác nhận.'))
            if new_lines and not proposal:
                # The source has no document date: the required date is only the system record date.
                proposal = self.env['tp.equipment.proposal'].create({
                    'title': (self.proposal_title or '').strip() or self.name, 'company_id': self.company_id.id,
                    'source_ref': self.file_hash, 'date_known': False})
        elif any(line.disposition not in ('equipment', 'service') for line in applicable):
            raise UserError(_('Đợt danh mục chỉ được tạo thiết bị nháp.'))
        for line in applicable:
            if line.identity_resolution == 'existing':
                # Preserve the source revision on this batch; existing business data and its original provenance stay unchanged.
                target = line.match_equipment_id if self.kind == 'equipment' else line.match_proposal_line_id
                field = 'equipment_id' if self.kind == 'equipment' else 'proposal_line_id'
                super(EquipmentImportLine, line).write({field: target.id})
                continue
            source = f'{self.file_hash}:{line.sheet_name}:{line.row_number}'
            data = line._mapped_values()
            if proposal:
                target = self.env['tp.equipment.proposal.line'].create({
                    'proposal_id': proposal.id, 'description': line.name, 'kind': line.proposal_kind,
                    'current_state': data.get('condition'), 'desired_config': data.get('config'),
                    'equipment_text': data.get('equipment_text'), 'category_id': line.category_id.id,
                    'solution': data.get('solution'), 'quantity': line.quantity if line.quantity_known else 0,
                    'estimate_amount': line.amount, 'estimate_amount_known': line.amount_known, 'source_ref': source,
                    'target_employee_id': line.employee_id.id, 'target_department_id': line.department_id.id})
                super(EquipmentImportLine, line).write({'proposal_line_id': target.id})
            else:
                target = self.env['maintenance.equipment'].create(line._equipment_values(source, data))
                super(EquipmentImportLine, line).write({'equipment_id': target.id})
        remaining = self.line_ids.filtered(lambda line: line.disposition in PENDING)
        super().write({'state': 'partial' if remaining else 'applied', 'proposal_id': proposal.id if proposal else False,
                       'applied_by_id': self.env.uid, 'applied_date': fields.Datetime.now()})
        return True

    def action_open_pending(self):
        check_admin(self.env)
        self.ensure_one()
        return {'type': 'ir.actions.act_window', 'name': _('Dòng nguồn chờ bổ sung'),
                'res_model': 'tp.equipment.import.line', 'view_mode': 'list,form',
                'domain': [('batch_id', '=', self.id), ('disposition', 'in', list(PENDING))]}


class EquipmentImportColumn(models.Model):
    _name = 'tp.equipment.import.column'
    _description = 'Ánh xạ cột nguồn thiết bị'
    _order = 'sheet_name, column_number'

    batch_id = fields.Many2one('tp.equipment.import.batch', 'Đợt nhập', required=True, ondelete='cascade')
    sheet_name = fields.Char('Trang tính', required=True)
    column_number = fields.Integer('Số cột', required=True)
    source_label = fields.Char('Tiêu đề nguồn', readonly=True)
    target_field = fields.Selection(TARGETS, string='Trường đích', required=True, default='ignore')
    network_excluded = fields.Boolean('IP/MAC đã loại', readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        check_admin(self.env)
        if self.env.context.get('tp_import_internal') is not INTERNAL:
            raise UserError(_('Dòng nguồn chỉ được tạo từ bộ đọc XLSX.'))
        return super().create(vals_list)

    def write(self, vals):
        check_admin(self.env)
        for batch in self.mapped('batch_id').sorted('id'):
            batch._lock()
        if set(vals) - {'target_field'} or any(c.batch_id.state != 'preview' or c.network_excluded for c in self):
            raise UserError(_('Chỉ sửa ánh xạ cột an toàn khi đang đối chiếu.'))
        return super().write(vals)

    def unlink(self):
        raise UserError(_('Giữ cột nguồn để truy vết.'))


class EquipmentImportLine(models.Model):
    _name = 'tp.equipment.import.line'
    _description = 'Dòng đối chiếu nguồn thiết bị'
    _order = 'sheet_name, row_number, id'

    batch_id = fields.Many2one('tp.equipment.import.batch', 'Đợt nhập', required=True, ondelete='cascade')
    company_id = fields.Many2one(related='batch_id.company_id', string='Công ty')
    batch_kind = fields.Selection(related='batch_id.kind', string='Loại nguồn')
    currency_id = fields.Many2one(related='company_id.currency_id', string='Tiền tệ')
    sheet_name = fields.Char('Trang tính', required=True, readonly=True)
    row_number = fields.Integer('Dòng', required=True, readonly=True)
    source_json = fields.Text('Ô nguồn / cache / merge đã loại IP/MAC', readonly=True)
    disposition = fields.Selection(DISPOSITIONS, string='Phân loại dòng', required=True, default='unknown')
    name = fields.Char('Tên xác nhận')
    employee_id = fields.Many2one('hr.employee', 'Nhân viên xác nhận', ondelete='restrict')
    department_id = fields.Many2one('hr.department', 'Phòng ban xác nhận', ondelete='restrict')
    location_id = fields.Many2one('tp.equipment.location', 'Vị trí xác nhận', ondelete='restrict')
    mapping_confirmed = fields.Boolean('Admin đã xác nhận ID / nội dung')
    resolution_note = fields.Text('Lý do / giải quyết')
    equipment_id = fields.Many2one('maintenance.equipment', 'Thiết bị đã đối chiếu', readonly=True, ondelete='restrict')
    proposal_line_id = fields.Many2one('tp.equipment.proposal.line', 'Dòng đề xuất đã đối chiếu', readonly=True, ondelete='restrict')
    identity_resolution = fields.Selection([('new', 'Thực sự mới'), ('existing', 'Định danh đã có — giữ nguyên')],
                                           string='Xử lý định danh', default='new', required=True)
    identity_confirmed = fields.Boolean('Đã đối chiếu định danh', readonly=True)
    match_equipment_id = fields.Many2one('maintenance.equipment', 'ID thiết bị đã có', ondelete='restrict')
    match_proposal_line_id = fields.Many2one('tp.equipment.proposal.line', 'ID dòng đề xuất đã có', ondelete='restrict')
    proposal_kind = fields.Selection([('purchase', 'Mua mới'), ('repair', 'Sửa'), ('upgrade', 'Nâng cấp'),
                                     ('transfer', 'Điều chuyển'), ('dispose', 'Ngừng dùng')], string='Loại đề xuất', default='purchase', required=True)
    amount_known = fields.Boolean('Thành tiền đã xác nhận')
    amount = fields.Monetary('Thành tiền nguồn', currency_field='currency_id')
    quantity_known = fields.Boolean('Số lượng đã xác nhận')
    quantity = fields.Integer('Số lượng nguồn')
    suggestion = fields.Text('Gợi ý theo tên, không tự gán', compute='_compute_suggestion')
    # Values confirmed by the admin for the record to create; the source text itself stays verbatim on the record.
    category_id = fields.Many2one('maintenance.equipment.category', 'Phân loại xác nhận', ondelete='restrict')
    asset_class = fields.Selection(ASSET_CLASS, 'Loại quản lý xác nhận')
    ownership = fields.Selection(OWNERSHIP, 'Sở hữu xác nhận')
    custody_stock = fields.Boolean('Nhóm Kho theo nguồn (Trong kho)',
                                   help='Chỉ bật cho dòng thuộc nhóm Kho; dòng chưa rõ người giữ không được đưa vào kho.')
    technical_state = fields.Selection(TECH_STATE, 'Tình trạng kỹ thuật theo nguồn')
    replacement_needed = fields.Boolean('Nguồn ghi cần thay / nâng cấp')
    brand = fields.Char('Hãng xác nhận')
    cpu = fields.Char('CPU xác nhận')
    ram = fields.Char('RAM xác nhận')
    storage = fields.Char('Ổ lưu trữ xác nhận')
    gpu = fields.Char('Card đồ họa xác nhận')
    screen = fields.Char('Màn hình đi kèm theo nguồn')
    applied = fields.Boolean('Đã áp dụng', compute='_compute_applied', search='_search_applied')

    @api.depends('equipment_id', 'proposal_line_id')
    def _compute_applied(self):
        for line in self:
            line.applied = bool(line.equipment_id or line.proposal_line_id)

    def _search_applied(self, operator, value):
        if operator in ('in', 'not in'):
            values = {bool(v) for v in value}
            if len(values) != 1:
                return [(1, '=', 1)] if (operator == 'in') == bool(values) else [(0, '=', 1)]
            positive = (operator == 'in') == values.pop()
        elif operator in ('=', '!='):
            positive = (operator == '=') == bool(value)
        else:
            return NotImplemented
        linked = ['|', ('equipment_id', '!=', False), ('proposal_line_id', '!=', False)]
        unlinked = [('equipment_id', '=', False), ('proposal_line_id', '=', False)]
        return linked if positive else unlinked

    def _mapped_values(self):
        self.ensure_one()
        mapping = {c.column_number: c.target_field for c in self.batch_id.column_ids if c.sheet_name == self.sheet_name}
        result = {}
        for cell in json.loads(self.source_json or '[]'):
            target = mapping.get(cell['column'], 'ignore')
            if target != 'ignore' and cell.get('cached') is not None and str(cell['cached']).strip():
                result[target] = str(cell['cached']).strip()
        return result

    def _equipment_values(self, source, data):
        """Draft equipment from a confirmed line: confirmed values + verbatim source notes, nothing inferred."""
        self.ensure_one()
        status = '\n'.join(f'{label}: {data[key]}' for key, label in (('status', 'Trạng thái nguồn'),
                                                                        ('condition', 'Tình trạng / bảo trì nguồn'))
                           if data.get(key))
        provenance = [_('Nguồn %(sheet)s dòng %(row)s', sheet=self.sheet_name, row=self.row_number)]
        if data.get('source_code'):
            provenance.append(_('STT nguồn %s (không là mã định danh)', data['source_code']))
        if data.get('holder'):
            provenance.append(_('người / nơi sử dụng theo nguồn: %s', data['holder']))
        if data.get('category'):
            provenance.append(_('phân loại nguồn: %s', data['category']))
        values = {
            'name': self.name, 'company_id': self.company_id.id, 'category_id': self.category_id.id,
            'tp_asset_class': self.asset_class or ('service' if self.disposition == 'service' else
                                                   self.category_id.tp_asset_class or 'device'),
            'tp_ownership': self.ownership or 'unknown', 'tp_owner_note': data.get('ownership'),
            'tp_brand': self.brand, 'model': data.get('model'), 'tp_cpu': self.cpu, 'tp_ram': self.ram,
            'tp_storage': self.storage, 'tp_gpu': self.gpu, 'tp_screen': self.screen,
            'tp_lifecycle': 'draft', 'tp_verification': 'source', 'tp_technical_state': self.technical_state or 'unverified',
            'tp_replacement_needed': self.replacement_needed, 'tp_source_ref': source,
            'tp_config_note': data.get('config'),
            'tp_condition_note': status or False, 'tp_date_source': data.get('date'),
            'tp_warranty_source': data.get('warranty'),
            'note': '; '.join(provenance) + '.' + (_(' Ghi chú đối chiếu: %s', self.resolution_note.strip())
                                                   if (self.resolution_note or '').strip() else ''),
            'tp_software_ids': _software_commands(data.get('software')),
        }
        if self.employee_id:
            values.update(tp_custody='employee', tp_employee_id=self.employee_id.id)
        elif self.department_id:
            values.update(tp_custody='department', tp_holder_department_id=self.department_id.id)
        elif self.location_id:
            values.update(tp_custody='location', tp_location_id=self.location_id.id)
        else:
            values.update(tp_custody='stock')  # _validate_resolution only allows this for the confirmed Kho group
        return values

    @api.depends('source_json', 'batch_id.column_ids.target_field')
    def _compute_suggestion(self):
        for line in self:
            holder = line._mapped_values().get('holder', '')
            suggestions = []
            if holder:
                for model in ('hr.employee', 'hr.department', 'tp.equipment.location'):
                    companies = [False, line.company_id.id] if model == 'hr.department' else [line.company_id.id]
                    matches = self.env[model].search([('name', '=', holder), ('company_id', 'in', companies)], limit=5)
                    suggestions.extend(f'{model} #{record.id}: {record.name}' for record in matches)
            line.suggestion = '\n'.join(suggestions)

    def action_confirm_mapping(self):
        check_admin(self.env)
        for batch in self.mapped('batch_id').sorted('id'):
            batch._lock()
        for line in self:
            line.batch_id._check_company_scope()
            if line.batch_id.state not in ('preview', 'partial') or line.equipment_id or line.proposal_line_id:
                raise UserError(_('Chỉ xác nhận khi đang đối chiếu.'))
            super(EquipmentImportLine, line).write({'mapping_confirmed': True, 'identity_confirmed': True})
            line._validate_resolution()
        return True

    def action_apply_alias(self):
        check_admin(self.env)
        for line in self:
            holder = line._mapped_values().get('holder', '')
            alias = self.env['tp.equipment.import.alias'].search([
                ('company_id', '=', line.company_id.id), ('source_text', '=', holder), ('confirmed', '=', True)], limit=1)
            if not alias:
                raise UserError(_('Không có alias đã xác nhận cho tên nguồn này.'))
            line.write({'employee_id': alias.employee_id.id, 'department_id': alias.department_id.id,
                        'location_id': alias.location_id.id})
        return True

    def _validate_resolution(self):
        self.ensure_one()
        if not self.mapping_confirmed or not (self.name or '').strip():
            raise UserError(_('Dòng %s cần tên và xác nhận nội dung / ID từ admin.') % self.row_number)
        if sum(bool(record) for record in (self.employee_id, self.department_id, self.location_id)) > 1:
            raise UserError(_('Chỉ xác nhận một đối tượng giữ trên mỗi dòng.'))
        if self.identity_resolution == 'existing' and not (self.match_equipment_id or self.match_proposal_line_id):
            raise UserError(_('Chọn ID hiện có trước khi xác nhận định danh.'))
        if (self.batch_id.kind == 'equipment' and self.match_proposal_line_id) or (self.batch_id.kind == 'proposal' and self.match_equipment_id):
            raise UserError(_('Chọn loại ID khớp loại nguồn.'))
        for record in (self.employee_id, self.department_id, self.location_id):
            if record and ((record.company_id != self.company_id and not (record._name == 'hr.department' and not record.company_id)) or ('active' in record._fields and not record.active)):
                raise UserError(_('Đối tượng mapping phải đang hoạt động và thuộc cùng công ty.'))
        if self.disposition in ('equipment', 'service'):
            holders = sum(bool(record) for record in (self.employee_id, self.department_id, self.location_id))
            if holders and self.custody_stock:
                raise UserError(_('Dòng %s: chọn người / nơi giữ hoặc nhóm Kho, không chọn cả hai.') % self.row_number)
            if not holders and not self.custody_stock:
                raise UserError(_('Dòng %s chưa rõ người / nơi giữ: giữ chờ, không mặc định đưa vào kho.') % self.row_number)
            if not self.category_id:
                raise UserError(_('Dòng %s cần phân loại xác nhận.') % self.row_number)
            if self.category_id.company_id and self.category_id.company_id != self.company_id:
                raise UserError(_('Phân loại phải thuộc cùng công ty.'))
        if self.quantity_known and self.quantity <= 0:
            raise UserError(_('Số lượng đã xác nhận phải lớn hơn 0.'))
        if self.amount_known and self.amount < 0:
            raise UserError(_('Thành tiền âm cần xử lý riêng, không áp nguồn tự động.'))

    @api.model_create_multi
    def create(self, vals_list):
        check_admin(self.env)
        if self.env.context.get('tp_import_internal') is not INTERNAL:
            raise UserError(_('Dòng nguồn chỉ được tạo từ bộ đọc XLSX.'))
        return super().create(vals_list)

    def write(self, vals):
        check_admin(self.env)
        for batch in self.mapped('batch_id').sorted('id'):
            batch._lock()
        if set(vals) & {'batch_id', 'source_json', 'sheet_name', 'row_number', 'equipment_id', 'proposal_line_id', 'identity_confirmed'}:
            raise UserError(_('Nguồn và liên kết đã áp là bất biến.'))
        if any(line.batch_id.state not in ('preview', 'partial') for line in self):
            raise UserError(_('Chỉ sửa resolution khi đang đối chiếu.'))
        if any(line.equipment_id or line.proposal_line_id for line in self):
            raise UserError(_('Dòng đã áp dụng được giữ nguyên; sửa trên hồ sơ đã tạo.'))
        if set(vals) & {'employee_id', 'department_id', 'location_id', 'name', 'disposition', 'identity_resolution',
                        'match_equipment_id', 'match_proposal_line_id', 'category_id', 'asset_class', 'ownership',
                        'custody_stock', 'technical_state', 'replacement_needed', 'brand', 'cpu', 'ram', 'storage',
                        'gpu', 'screen', 'amount', 'amount_known', 'quantity', 'quantity_known', 'proposal_kind'}:
            vals = dict(vals, mapping_confirmed=False, identity_confirmed=False)
        if vals.get('disposition') == 'skip' and not (vals.get('resolution_note') or all(line.resolution_note for line in self)):
            raise UserError(_('Bỏ qua cần lý do.'))
        return super().write(vals)

    def unlink(self):
        raise UserError(_('Giữ mọi dòng nguồn, dùng disposition và lý do để bỏ qua.'))


class EquipmentImportAlias(models.Model):
    _name = 'tp.equipment.import.alias'
    _description = 'Tên nguồn đã xác nhận theo ID'

    source_text = fields.Char('Tên theo nguồn', required=True)
    company_id = fields.Many2one('res.company', 'Công ty', default=lambda self: self.env.company, required=True)
    employee_id = fields.Many2one('hr.employee', 'Nhân viên xác nhận', ondelete='restrict')
    department_id = fields.Many2one('hr.department', 'Phòng ban xác nhận', ondelete='restrict')
    location_id = fields.Many2one('tp.equipment.location', 'Vị trí xác nhận', ondelete='restrict')
    confirmed = fields.Boolean('Đã xác nhận', readonly=True)
    confirmed_by_id = fields.Many2one('res.users', 'Người xác nhận', readonly=True)
    confirmed_date = fields.Datetime('Ngày xác nhận', readonly=True)

    _source_unique = models.Constraint('UNIQUE(company_id, source_text)', 'Tên nguồn đã có mapping trong công ty.')

    @api.model_create_multi
    def create(self, vals_list):
        check_admin(self.env)
        return super().create([dict(vals, confirmed=False, confirmed_by_id=False, confirmed_date=False) for vals in vals_list])

    def write(self, vals):
        check_admin(self.env)
        lock_records(self)
        vals = dict(vals)
        for field in ('confirmed', 'confirmed_by_id', 'confirmed_date'):
            vals.pop(field, None)
        vals.update(confirmed=False, confirmed_by_id=False, confirmed_date=False)
        return super().write(vals)

    def action_confirm(self):
        check_admin(self.env)
        lock_records(self)
        for alias in self:
            if alias.company_id not in self.env.companies:
                raise UserError(_('Công ty ngoài phạm vi được phép.'))
            selected = [record for record in (alias.employee_id, alias.department_id, alias.location_id) if record]
            if len(selected) != 1 or (selected[0].company_id != alias.company_id and not (selected[0]._name == 'hr.department' and not selected[0].company_id)) or ('active' in selected[0]._fields and not selected[0].active):
                raise ValidationError(_('Chọn đúng một ID đang hoạt động cùng công ty.'))
            super(EquipmentImportAlias, alias).write({'confirmed': True, 'confirmed_by_id': self.env.uid,
                                                    'confirmed_date': fields.Datetime.now()})
        return True
