import re

from odoo import api, fields, models
from odoo.exceptions import ValidationError

HEX_COLOR = re.compile(r'^#[0-9A-Fa-f]{6}$')


def text_color_for(background):
    """Dark or white text, whichever reads better on the badge colour (WCAG relative luminance)."""
    if not background or not HEX_COLOR.match(background):
        return '#FFFFFF'

    def channel(value):
        value /= 255
        return value / 12.92 if value <= 0.03928 else ((value + 0.055) / 1.055) ** 2.4

    red, green, blue = (channel(int(background[i:i + 2], 16)) for i in (1, 3, 5))
    luminance = 0.2126 * red + 0.7152 * green + 0.0722 * blue
    # contrast with white = 1.05 / (L + 0.05); with near-black #111827 (L≈0.0137) = (L + 0.05) / 0.0637
    return '#FFFFFF' if 1.05 / (luminance + 0.05) >= (luminance + 0.05) / 0.0637 else '#111827'


class TpBank(models.Model):
    _name = 'tp.bank'
    _description = 'Ngân hàng (danh mục NAPAS/VietQR)'
    _order = 'sequence, id'
    _rec_name = 'short_name'
    _rec_names_search = ['short_name', 'name', 'code', 'bin']

    sequence = fields.Integer(string='Thứ tự', default=1000)
    active = fields.Boolean(string='Đang dùng', default=True)
    code = fields.Char(string='Mã ngân hàng', required=True, help='Mã ngân hàng theo danh sách VietQR/NAPAS.')
    bin = fields.Char(string='Mã BIN (NAPAS)', help='Mã định danh ngân hàng 6 chữ số dùng cho chuyển khoản nhanh/VietQR.')
    short_name = fields.Char(string='Tên viết tắt', required=True)
    name = fields.Char(string='Tên đầy đủ', required=True)
    swift = fields.Char(string='Mã SWIFT')
    badge = fields.Char(string='Chữ trên biểu tượng', size=5, required=True,
                        help='Tối đa 5 ký tự, hiển thị trên biểu tượng màu của ngân hàng.')
    color = fields.Char(string='Màu biểu tượng', required=True, default='#475569')
    text_color = fields.Char(string='Màu chữ biểu tượng', compute='_compute_text_color')
    kind = fields.Selection(
        [('bank', 'Ngân hàng'), ('wallet', 'Ví điện tử'), ('finance', 'Công ty tài chính')],
        string='Loại', required=True, default='bank',
    )
    napas_transfer = fields.Boolean(string='Hỗ trợ chuyển nhanh NAPAS')
    account_count = fields.Integer(string='Số tài khoản', compute='_compute_account_count')

    _code_unique = models.Constraint('UNIQUE(code)', 'Mã ngân hàng đã tồn tại trong danh mục.')
    _bin_unique = models.UniqueIndex('(bin) WHERE bin IS NOT NULL', 'Mã BIN đã thuộc một ngân hàng khác.')

    @api.depends('color')
    def _compute_text_color(self):
        for bank in self:
            bank.text_color = text_color_for(bank.color)

    def _compute_account_count(self):
        counts = dict(self.env['res.partner.bank'].sudo()._read_group(
            [('tp_bank_id', 'in', self.ids)], ['tp_bank_id'], ['__count'],
        ))
        for bank in self:
            bank.account_count = counts.get(bank, 0)

    @api.constrains('color', 'badge', 'bin')
    def _check_display_values(self):
        for bank in self:
            if not HEX_COLOR.match(bank.color or ''):
                raise ValidationError(self.env._('Màu biểu tượng phải có dạng #RRGGBB.'))
            if not (bank.badge or '').strip():
                raise ValidationError(self.env._('Chữ trên biểu tượng không được để trống.'))
            if bank.bin and not re.fullmatch(r'[0-9]{6}', bank.bin):
                raise ValidationError(self.env._('Mã BIN phải gồm đúng 6 chữ số.'))

    def _tp_card(self):
        """Public, non-sensitive catalogue values used by the profile and the picker."""
        self.ensure_one()
        return {
            'id': self.id,
            'code': self.code,
            'bin': self.bin or '',
            'short_name': self.short_name,
            'name': self.name,
            'badge': self.badge,
            'color': self.color,
            'text_color': self.text_color,
            'kind': self.kind,
        }

    @api.model
    def tp_bank_catalog(self):
        """Active banks for pickers, in catalogue order (most used banks first)."""
        return [bank._tp_card() for bank in self.search([])]
