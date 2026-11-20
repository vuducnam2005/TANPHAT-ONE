import hashlib
import json

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError

from .code_format import code_aliases
from .hr_employee import _ROSTER_WRITE
from .roster_parser import employee_code, parse_roster

_INTERNAL = object()
_DEPARTMENT_CONFLICT = 'Nhiều phòng ban trùng tên nguồn. Hãy chọn phòng ban cụ thể.'
_LEGACY_DEPARTMENT_CONFLICT = 'Multiple departments match the source name. Select an explicit department.'


def _tp_code(source):
    """Three-digit TP code of a source number, or ``False`` when it is outside 1-999."""
    try:
        return employee_code(source)
    except ValueError:
        return False


class HrImportBatch(models.Model):
    _name = 'tp.hr.import.batch'
    _description = 'TP HR roster import'
    _order = 'id desc'
    _check_company_auto = True

    name = fields.Char(default='Nhập danh sách nhân sự', required=True)
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    file_data = fields.Binary(attachment=False)
    file_name = fields.Char()
    checksum = fields.Char(readonly=True, copy=False)
    state = fields.Selection([('draft', 'Chọn file'), ('preview', 'Xem trước'), ('applied', 'Đã áp dụng')], default='draft', readonly=True, required=True)
    line_ids = fields.One2many('tp.hr.import.line', 'batch_id', readonly=True)
    row_count = fields.Integer(readonly=True)
    result = fields.Text(readonly=True)
    applied_by = fields.Many2one('res.users', readonly=True)
    applied_at = fields.Datetime(readonly=True)

    def _manager(self):
        if not self.env.user.has_group('hr.group_hr_manager'):
            msg = self.env._('Nhập danh sách nhân sự cần quyền quản lý nhân sự.')
            raise AccessError(msg)
        self.check_access('write')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if set(vals) & {'checksum', 'line_ids', 'result', 'applied_by', 'applied_at', 'row_count'} or vals.get('state', 'draft') != 'draft':
                msg = self.env._('Kết quả nhập chỉ được hệ thống cập nhật.')
                raise AccessError(msg)
        return super().create(vals_list)

    def write(self, vals):
        if self.env.context.get('_tp_import_internal') is not _INTERNAL:
            if set(vals) - {'name', 'file_data', 'file_name', 'company_id'}:
                msg = self.env._('Kết quả nhập chỉ được hệ thống cập nhật.')
                raise AccessError(msg)
            if any(batch.state != 'draft' for batch in self) and set(vals) - {'name'}:
                msg = self.env._('Tạo lô nhập mới để thay file nguồn đã xem trước.')
                raise UserError(msg)
        return super().write(vals)

    def unlink(self):
        if any(batch.state != 'draft' for batch in self):
            msg = self.env._('Không được xóa lịch sử nhập danh sách.')
            raise UserError(msg)
        return super().unlink()

    def _internal(self):
        return self.with_context(_tp_import_internal=_INTERNAL)

    def _lock(self):
        self.ensure_one()
        self.env.cr.execute('SELECT id FROM tp_hr_import_batch WHERE id=%s FOR UPDATE', [self.id])
        self.invalidate_recordset()
        self.env.cr.execute('SELECT pg_advisory_xact_lock(%s, %s)', [761101, self.company_id.id])

    def _removed_identity(self, code):
        """Reconciliation note when ``code`` belongs to a permanently deleted profile."""
        tp_code = _tp_code(code)
        # A profile deleted under the former code TP1nnnn is the same identity as TPnnn.
        removed = self.env['tp.hr.employee.audit']._tp_removed_identities(self.company_id.id, [code], code_aliases(tp_code) if tp_code else [])
        if not removed:
            return ''
        # ``source`` is the positional name of Environment._(); use another placeholder.
        return self.env._('Mã nguồn %(source_code)s (mã %(code)s) thuộc hồ sơ đã xóa vĩnh viễn ngày %(date)s. Không tự tạo lại; cần đối chiếu với người phụ trách nhân sự.',
                          source_code=code, code=removed[0].employee_code or tp_code or '-', date=removed[0].create_date.strftime('%d/%m/%Y'))

    def _out_of_range(self, code):
        return self.env._('Mã nguồn %(source_code)s vượt dải TP001–TP999. Không tự cấp số khác; cần đối chiếu với người phụ trách nhân sự.', source_code=code)

    def action_preview(self):
        self.ensure_one()
        self._manager()
        self._lock()
        if self.state != 'draft':
            return True
        try:
            data = self.file_data.content if self.file_data else b''
            parsed = parse_roster(data)
        except (ValueError, TypeError) as exc:
            raise UserError(str(exc)) from exc
        lines = []
        employees = self.env['hr.employee'].with_context(active_test=False)
        for row in parsed['rows']:
            match = employees.search([('company_id', '=', self.company_id.id), ('tp_source_code', '=', row['source_code'])])
            tp_code = _tp_code(row['source_code'])
            collision = employees.search([('company_id', '=', self.company_id.id), ('tp_employee_code', 'in', code_aliases(tp_code))]) if tp_code else employees.browse()
            department = self.env['hr.department'].with_context(active_test=False).search([
                ('company_id', '=', self.company_id.id), ('name', '=', row['source_department'])], limit=2)
            if match and (match.tp_source_snapshot or {}).get('source_department') == row['source_department']:
                department = match.department_id
            action, detail = 'create', ''
            if not tp_code:
                action, detail = 'conflict', self._out_of_range(row['source_code'])
            elif collision and collision != match:
                action, detail = 'conflict', self.env._('Mã TP đã thuộc về một danh tính khác. Cần đối chiếu, không tự gộp.')
            elif not match and self._removed_identity(row['source_code']):
                action, detail = 'conflict', self._removed_identity(row['source_code'])
            elif match:
                action = 'skip' if {k: v for k, v in (match.tp_source_snapshot or {}).items() if not k.startswith('_')} == row else 'update'
                detail = '' if action == 'skip' else json.dumps({'before': match.tp_source_snapshot, 'after': row}, ensure_ascii=False)
            if len(department) > 1 and action != 'conflict':
                action, detail = 'conflict', _DEPARTMENT_CONFLICT
            lines.append((0, 0, dict(row, source_cells=parsed['locations'].get(row['source_code']), employee_id=match.id, department_id=department.id if len(department) == 1 else False, action=action, detail=detail)))
        for error in parsed['errors']:
            lines.append((0, 0, {'source_code': error.get('source_code'), 'action': 'conflict', 'detail': json.dumps(error, ensure_ascii=False), 'source_cells': [{'sheet': error['sheet'], 'row': error['row']}]}))
        self._internal().write({'checksum': hashlib.sha256(data).hexdigest(), 'state': 'preview', 'row_count': parsed['row_count'], 'line_ids': lines})
        return True

    def action_apply(self):
        self.ensure_one()
        self._manager()
        self._lock()
        if self.state == 'applied':
            return True
        if self.state != 'preview':
            msg = self.env._('Hãy xem trước file nguồn trước khi áp dụng.')
            raise UserError(msg)
        counts = {'create': 0, 'update': 0, 'skip': 0, 'conflict': 0}
        employees = self.env['hr.employee'].with_context(active_test=False)
        for line in self.line_ids:
            action, detail = line.action, line.detail or ''
            if action == 'conflict' and detail in (_DEPARTMENT_CONFLICT, _LEGACY_DEPARTMENT_CONFLICT) and line.department_id:
                action, detail = 'create', ''
            row = {key: line[key] or '' for key in ('source_code', 'name', 'source_department', 'source_title')}
            current = employees.browse()
            if action != 'conflict':
                current = employees.search([('company_id', '=', self.company_id.id), ('tp_source_code', '=', line.source_code)])
                if current:
                    self.env.cr.execute('SELECT id FROM hr_employee WHERE id=%s FOR UPDATE', [current.id])
                    current.invalidate_recordset()
                if current and {k: v for k, v in (current.tp_source_snapshot or {}).items() if not k.startswith('_')} == row:
                    action = 'skip'
                elif current:
                    old = current.tp_source_snapshot or {}
                    manually_changed = current.name != old.get('name') or current.tp_source_department != old.get('source_department') or current.tp_source_title != old.get('source_title') or current.department_id.id != old.get('_department_id')
                    if not line.review_update or manually_changed:
                        action, detail = 'conflict', self.env._('Thay đổi từ nguồn cần rà soát; các chỉnh sửa thủ công trên hồ sơ được giữ nguyên.')
                    else:
                        action = 'update'
                elif not _tp_code(line.source_code):
                    action, detail = 'conflict', self._out_of_range(line.source_code)
                elif employees.search_count([('company_id', '=', self.company_id.id), ('tp_employee_code', 'in', code_aliases(_tp_code(line.source_code)))]):
                    action, detail = 'conflict', self.env._('Trùng mã TP với hồ sơ khác; cần đối chiếu danh tính trước khi nhập.')
                elif self._removed_identity(line.source_code):
                    action, detail = 'conflict', self._removed_identity(line.source_code)
                else:
                    action = 'create'
                if action in ('create', 'update'):
                    department = line.department_id
                    if department and department.company_id != self.company_id:
                        msg = self.env._('Phòng ban ánh xạ phải thuộc công ty của lô nhập.')
                        raise UserError(msg)
                    if not department and current and (current.tp_source_snapshot or {}).get('source_department') == line.source_department:
                        department = current.department_id
                    if not department:
                        matches = self.env['hr.department'].with_context(active_test=False).search([('company_id', '=', self.company_id.id), ('name', '=', line.source_department)], limit=2)
                        if len(matches) > 1:
                            line.with_context(_tp_import_internal=_INTERNAL).write({'action': 'conflict', 'detail': _DEPARTMENT_CONFLICT})
                            counts['conflict'] += 1
                            continue
                        department = matches
                    if not department:
                        department = self.env['hr.department'].create({'name': line.source_department, 'company_id': self.company_id.id})
                    vals = {'name': line.name, 'department_id': department.id, 'tp_source_department': line.source_department,
                            'tp_source_title': line.source_title, 'tp_source_snapshot': dict(row, _department_id=department.id), 'tp_import_batch_id': self.id}
                    if action == 'create':
                        vals.update(company_id=self.company_id.id, tp_source_code=line.source_code, tp_employee_code=employee_code(line.source_code))
                        current = employees.with_context(_tp_roster_write=_ROSTER_WRITE).create(vals)
                    else:
                        current.with_context(_tp_roster_write=_ROSTER_WRITE).write(vals)
                    line.with_context(_tp_import_internal=_INTERNAL).write({'employee_id': current.id, 'department_id': department.id})
            final = {'action': action, 'detail': detail}
            if current:
                final['employee_id'] = current.id
            line.with_context(_tp_import_internal=_INTERNAL).write(final)
            counts[action] += 1
        self._internal().write({'state': 'applied', 'result': json.dumps(counts), 'applied_by': self.env.user.id, 'applied_at': fields.Datetime.now()})
        return True


class HrImportLine(models.Model):
    _name = 'tp.hr.import.line'
    _description = 'TP HR roster preview row'
    _check_company_auto = True

    batch_id = fields.Many2one('tp.hr.import.batch', required=True, ondelete='cascade')
    company_id = fields.Many2one(related='batch_id.company_id', store=True)
    source_code = fields.Char()
    name = fields.Char()
    source_department = fields.Char()
    source_title = fields.Char()
    employee_id = fields.Many2one('hr.employee', check_company=True)
    department_id = fields.Many2one('hr.department', check_company=True)
    action = fields.Selection([('create', 'Tạo'), ('update', 'Thay đổi nguồn'), ('skip', 'Bỏ qua'), ('conflict', 'Cần đối chiếu')])
    detail = fields.Text()
    source_cells = fields.Json(readonly=True)
    review_update = fields.Boolean(string='Đã rà soát thay đổi nguồn')

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get('_tp_import_internal') is not _INTERNAL:
            msg = self.env._('Dòng xem trước chỉ được tạo bởi bộ đọc file.')
            raise AccessError(msg)
        return super().create(vals_list)

    def write(self, vals):
        if self.env.context.get('_tp_import_internal') is not _INTERNAL:
            if set(vals) - {'department_id', 'review_update'} or any(line.batch_id.state != 'preview' for line in self):
                msg = self.env._('Chỉ được sửa ánh xạ phòng ban và xác nhận rà soát nguồn.')
                raise AccessError(msg)
            batches = self.batch_id
            batches._manager()
            for batch in batches.sorted('id'):
                batch._lock()
            self.invalidate_recordset()
            if any(line.batch_id.state != 'preview' for line in self):
                msg = self.env._('Lô nhập đã áp dụng; không thể đổi ánh xạ xem trước.')
                raise AccessError(msg)
        return super().write(vals)

    def unlink(self):
        if self.env.context.get('_tp_import_internal') is not _INTERNAL:
            msg = self.env._('Không được xóa trực tiếp dòng xem trước hoặc lịch sử nhập.')
            raise AccessError(msg)
        return super().unlink()
