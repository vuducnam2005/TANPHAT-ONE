"""A stored source workbook is private immutable evidence, including direct attachment APIs."""
from odoo import api, models
from odoo.exceptions import AccessError

from .attendance_common import require


class AttendanceSourceAttachment(models.Model):
    _inherit = 'ir.attachment'

    def _tp_source_edit(self, batch_ids):
        batches = self.env['tp.hr.attendance.batch'].browse(batch_ids).exists()
        batches.check_access('read')
        for batch in batches:
            require(self.env, 'import', batch.company_id)
            batch._lock()
            if batch.state != 'draft':
                raise AccessError(self.env._('Tệp nguồn đã lưu là bất biến; tải tệp mới thành một lô riêng.'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('res_model') == 'tp.hr.attendance.batch':
                if vals.get('public') or vals.get('access_token'):
                    raise AccessError(self.env._('Tệp chấm công không được công khai hoặc dùng token chia sẻ.'))
                if vals.get('res_id'):
                    self._tp_source_edit([vals['res_id']])
        return super().create(vals_list)

    def write(self, vals):
        protected = self.sudo().filtered(lambda item: item.res_model == 'tp.hr.attendance.batch')
        if protected:
            if vals.get('public') or vals.get('access_token') or set(vals) & {'res_model', 'res_id', 'res_field'}:
                raise AccessError(self.env._('Không công khai, chuyển hoặc đổi liên kết tệp chấm công.'))
            self._tp_source_edit(protected.mapped('res_id'))
        if vals.get('res_model') == 'tp.hr.attendance.batch':
            if vals.get('public') or vals.get('access_token') or any(item.public or item.access_token for item in self.sudo()):
                raise AccessError(self.env._('Tệp chấm công không được công khai hoặc có token.'))
            if vals.get('res_id'):
                self._tp_source_edit([vals['res_id']])
        return super().write(vals)

    def unlink(self):
        protected = self.sudo().filtered(lambda item: item.res_model == 'tp.hr.attendance.batch')
        if protected:
            self._tp_source_edit(protected.mapped('res_id'))
        return super().unlink()

    def generate_access_token(self):
        if any(item.res_model == 'tp.hr.attendance.batch' for item in self.sudo()):
            raise AccessError(self.env._('Tệp chấm công không được tạo token chia sẻ.'))
        return super().generate_access_token()


class AttendanceSnapshotPersonAccess(models.Model):
    _inherit = 'tp.hr.attendance.snapshot.person'

    def check_access(self, operation):
        if not self.env.su:
            require(self.env, 'import', self.env.company)
            self.sudo().batch_id.with_user(self.env.user).check_access(operation)
        return super().check_access(operation)


class AttendanceSnapshotCellAccess(models.Model):
    _inherit = 'tp.hr.attendance.snapshot.cell'

    def check_access(self, operation):
        if not self.env.su:
            require(self.env, 'import', self.env.company)
            self.sudo().batch_id.with_user(self.env.user).check_access(operation)
        return super().check_access(operation)


class AttendanceLineAccess(models.Model):
    _inherit = 'tp.hr.attendance.line'

    def check_access(self, operation):
        if not self.env.su:
            require(self.env, 'import', self.env.company)
            self.sudo().batch_id.with_user(self.env.user).check_access('read')
        return super().check_access(operation)


class AttendanceLateAccess(models.Model):
    _inherit = 'tp.hr.attendance.late'

    def check_access(self, operation):
        if not self.env.su:
            require(self.env, 'import', self.env.company)
            self.sudo().batch_id.with_user(self.env.user).check_access('read')
        return super().check_access(operation)
