"""Small shared wizards: reason entry for return / cancel / not-executed actions."""
from odoo import _, fields, models
from odoo.exceptions import UserError

from .common import check_admin

REASON_MODELS = (
    "maintenance.request",
    "tp.equipment.proposal",
    "tp.equipment.proposal.line",
    "tp.equipment.inventory",
    "tp.equipment.import.batch",
)


class TpEquipmentReasonWizard(models.TransientModel):
    _name = "tp.equipment.reason.wizard"
    _description = "Kho thiết bị — nhập lý do"

    res_model = fields.Char(required=True, readonly=True)
    res_id = fields.Integer(required=True, readonly=True)
    action = fields.Char(required=True, readonly=True)
    record_name = fields.Char("Hồ sơ", readonly=True)
    hint = fields.Char(readonly=True)
    reason = fields.Text("Lý do", required=True)

    def _tp_open(self, record, action, title, hint=False):
        check_admin(self.env)
        record.ensure_one()
        if record._name not in REASON_MODELS:
            raise UserError(_("Thao tác không hợp lệ."))
        wizard = self.create({
            "res_model": record._name, "res_id": record.id, "action": action,
            "record_name": record.display_name, "hint": hint or False,
        })
        return {
            "type": "ir.actions.act_window",
            "name": title,
            "res_model": self._name,
            "res_id": wizard.id,
            "view_mode": "form",
            "views": [(self.env.ref("tp_equipment.reason_wizard_form").id, "form")],
            "target": "new",
        }

    def action_confirm(self):
        check_admin(self.env)
        self.ensure_one()
        if self.res_model not in REASON_MODELS:
            raise UserError(_("Thao tác không hợp lệ."))
        reason = (self.reason or "").strip()
        if not reason:
            raise UserError(_("Ghi lý do."))
        record = self.env[self.res_model].browse(self.res_id).exists()
        if not record:
            raise UserError(_("Hồ sơ không còn tồn tại."))
        result = record._tp_apply_reason(self.action, reason)
        return result if isinstance(result, dict) else {"type": "ir.actions.act_window_close"}
