"""Keep unclassified contact details and personal resumes out of the directory."""
from odoo import api, fields, models
from odoo.exceptions import AccessError

from odoo.addons.tp_hr_workspace.models.workspace_directory import is_hr_officer


class HrEmployeeDirectoryPrivacy(models.Model):
    _inherit = 'hr.employee'

    mobile_phone = fields.Char(groups='hr.group_hr_user')
    mobile_phone_sanitized = fields.Char(groups='hr.group_hr_user', compute='_tp_compute_mobile_companions')
    mobile_phone_formatted = fields.Char(groups='hr.group_hr_user', compute='_tp_compute_mobile_companions')
    phone_sanitized = fields.Char(groups='hr.group_hr_user')
    phone_formatted = fields.Char(groups='hr.group_hr_user')
    phone = fields.Char(groups='hr.group_hr_user')
    email = fields.Char(groups='hr.group_hr_user')

    @api.depends(lambda self: ['work_phone'] + self._phone_get_sanitize_triggers())
    def _compute_phone_companion_fields(self):
        # Reading the shared work number must not read the restricted mobile number.
        self._phone_update_companion_fields(('work_phone',))

    @api.depends(lambda self: ['mobile_phone'] + self._phone_get_sanitize_triggers())
    def _tp_compute_mobile_companions(self):
        self._phone_update_companion_fields(('mobile_phone',))

    def export_data(self, fields_to_export):
        # hr.employee's native fetch proxy otherwise bypasses the public-model guard.
        if not is_hr_officer(self.env):
            raise AccessError(self.env._('Danh bạ nhân viên chỉ xem; chỉ nhân sự được giao mới được xuất danh sách.'))
        return super().export_data(fields_to_export)


class HrEmployeePublicDirectoryPrivacy(models.Model):
    _inherit = 'hr.employee.public'

    mobile_phone = fields.Char(groups='hr.group_hr_user')
    mobile_phone_sanitized = fields.Char(groups='hr.group_hr_user')
    mobile_phone_formatted = fields.Char(groups='hr.group_hr_user')
    phone_sanitized = fields.Char(groups='hr.group_hr_user')
    phone_formatted = fields.Char(groups='hr.group_hr_user')
    phone = fields.Char(groups='hr.group_hr_user')
    email = fields.Char(groups='hr.group_hr_user')
