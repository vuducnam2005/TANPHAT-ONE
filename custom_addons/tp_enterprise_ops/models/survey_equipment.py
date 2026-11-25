# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
"""K1: Survey Equipment Calibration Tracking & Expired/Broken Issuance Block (Mandatory Case #13)."""
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class MaintenanceEquipmentSurveyExtension(models.Model):
    _inherit = 'maintenance.equipment'

    tp_is_survey_gear = fields.Boolean(
        string='Thiết bị đo đạc / khảo sát hiện trường',
        default=False,
        index=True,
        help='Tách riêng thiết bị khảo sát cần theo dõi hạn kiểm định/hiệu chuẩn; không làm phức tạp Kho thiết bị văn phòng.',
    )
    tp_calibration_date = fields.Date(string='Ngày kiểm định / hiệu chuẩn gần nhất')
    tp_calibration_due_date = fields.Date(string='Hạn kiểm định tiếp theo', index=True)
    tp_calibration_cert_no = fields.Char(string='Số giấy chứng nhận kiểm định')
    tp_calibration_org = fields.Char(string='Đơn vị kiểm định')
    tp_calibration_state = fields.Selection(
        [
            ('not_applicable', 'Thiết bị văn phòng (không yêu cầu kiểm định)'),
            ('valid', 'Còn hạn kiểm định'),
            ('expiring_soon', 'Sắp hết hạn kiểm định (≤ 30 ngày)'),
            ('expired', 'Quá hạn kiểm định — Chặn xuất dùng'),
        ],
        compute='_compute_tp_calibration_state',
        store=True,
        string='Tình trạng kiểm định',
    )

    @api.depends('tp_is_survey_gear', 'tp_calibration_due_date')
    def _compute_tp_calibration_state(self):
        today = fields.Date.context_today(self)
        soon = today + timedelta(days=30)
        for eq in self:
            if not eq.tp_is_survey_gear:
                eq.tp_calibration_state = 'not_applicable'
            elif not eq.tp_calibration_due_date:
                eq.tp_calibration_state = 'expired'
            elif eq.tp_calibration_due_date < today:
                eq.tp_calibration_state = 'expired'
            elif eq.tp_calibration_due_date <= soon:
                eq.tp_calibration_state = 'expiring_soon'
            else:
                eq.tp_calibration_state = 'valid'


class TpEquipmentMoveSurveyGuard(models.Model):
    _inherit = 'tp.equipment.move'

    def _tp_check(self, strict=False):
        """Block issuing/assigning/loaning survey equipment that is broken or has expired calibration (Mandatory Case #13)."""
        issues = super()._tp_check(strict=False)
        to_custody = self._tp_target_custody()
        today = fields.Date.context_today(self)

        if self.move_type not in ('opening', 'adjust', 'reversal') and to_custody in ('employee', 'loan', 'department', 'location'):
            for line in self.line_ids.filtered('equipment_id'):
                eq = line.equipment_id
                if eq.tp_is_survey_gear:
                    if not eq.tp_calibration_due_date:
                        issues.append((
                            'error',
                            line,
                            _('%(name)s là thiết bị khảo sát chưa có hạn kiểm định/hiệu chuẩn hợp lệ, không được xuất dùng.', name=eq.display_name),
                        ))
                    elif eq.tp_calibration_due_date < today:
                        issues.append((
                            'error',
                            line,
                            _(
                                '%(name)s là thiết bị khảo sát đã quá hạn kiểm định (%(due)s), không được bàn giao / cho mượn hiện trường.',
                                name=eq.display_name,
                                due=eq.tp_calibration_due_date.strftime('%d/%m/%Y'),
                            ),
                        ))

        if strict and any(level == 'error' for level, _l, _m in issues):
            raise UserError('\n'.join(msg for level, _l, msg in issues if level == 'error'))
        return issues
