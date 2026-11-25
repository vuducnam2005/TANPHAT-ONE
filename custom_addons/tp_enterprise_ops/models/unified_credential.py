# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
"""J2: Unified Practicing Certificate on canonical hr.employee.skill + 1-click link to tp.credential Bid Packages."""
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class HrEmployeeSkillPracticingCert(models.Model):
    _inherit = 'hr.employee.skill'

    tp_certificate_no = fields.Char(string='Số hiệu chứng chỉ hành nghề', index=True)
    tp_issuer_org = fields.Char(string='Cơ quan cấp chứng chỉ')
    tp_scope_of_practice = fields.Char(string='Lĩnh vực & Hạng hành nghề (Hạng I / II / III)')
    tp_valid_from = fields.Date(string='Ngày cấp')
    tp_valid_to = fields.Date(string='Ngày hết hạn', index=True)
    tp_expiry_state = fields.Selection(
        [
            ('unlimited', 'Không thời hạn / Chưa khai hạn'),
            ('valid', 'Còn hiệu lực'),
            ('expiring_soon', 'Sắp hết hạn (≤ 45 ngày)'),
            ('expired', 'Đã hết hạn'),
        ],
        compute='_compute_tp_expiry_state',
        store=True,
        string='Tình trạng hiệu lực',
    )
    tp_attachment_id = fields.Many2one('ir.attachment', string='Tệp scan chứng chỉ (ACL)', ondelete='set null')

    @api.depends('tp_valid_to')
    def _compute_tp_expiry_state(self):
        today = fields.Date.context_today(self)
        soon = today + timedelta(days=45)
        for rec in self:
            if not rec.tp_valid_to:
                rec.tp_expiry_state = 'unlimited'
            elif rec.tp_valid_to < today:
                rec.tp_expiry_state = 'expired'
            elif rec.tp_valid_to <= soon:
                rec.tp_expiry_state = 'expiring_soon'
            else:
                rec.tp_expiry_state = 'valid'


class TpCredentialHrBridge(models.Model):
    """Links KD Bid Package tp.credential directly to HR's canonical hr.employee.skill — zero duplicate certificate table."""
    _inherit = 'tp.credential'

    tp_employee_skill_id = fields.Many2one(
        'hr.employee.skill',
        string='Chứng chỉ gốc từ Hồ sơ Nhân sự',
        ondelete='set null',
        index=True,
    )
    tp_employee_id = fields.Many2one(
        'hr.employee',
        related='tp_employee_skill_id.employee_id',
        store=True,
        string='Nhân sự sở hữu chứng chỉ',
    )

    def action_sync_from_hr_skill(self):
        for rec in self:
            sk = rec.tp_employee_skill_id.sudo()
            if not sk:
                raise UserError(_('Vui lòng chọn Chứng chỉ gốc từ Hồ sơ Nhân sự trước khi đồng bộ.'))
            if not sk.tp_valid_from or not sk.tp_valid_to:
                raise UserError(_('Chứng chỉ nhân sự cần có đầy đủ Ngày cấp và Ngày hết hạn để đưa vào hồ sơ năng lực dự thầu.'))
            partner = sk.employee_id.work_contact_id or sk.employee_id.user_id.partner_id
            vals = {
                'subject_kind': 'person',
                'credential_kind': f"{sk.skill_id.name} ({sk.tp_scope_of_practice or sk.skill_level_id.name})",
                'valid_from': sk.tp_valid_from,
                'valid_to': sk.tp_valid_to,
                'source_note': f"Đồng bộ từ Hồ sơ HR #{sk.employee_id.id} — Số CC: {sk.tp_certificate_no or 'N/A'} — Cấp bởi: {sk.tp_issuer_org or 'N/A'}",
            }
            if partner:
                vals['subject_id'] = partner.id
            rec.write(vals)
        return True
