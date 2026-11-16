"""Shared reporting catalogs; loaded before reporting so new columns can default to them."""
from odoo import api, fields, models

COLORS = [('muted', 'Xám'), ('info', 'Xanh dương'), ('success', 'Xanh lá'), ('warning', 'Cam'), ('danger', 'Đỏ')]


class Priority(models.Model):
    _name = 'tp.report.priority'
    _description = 'Danh mục mức ưu tiên dùng chung'
    _order = 'sequence, id'
    name = fields.Char(required=True)
    code = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    color = fields.Selection(COLORS, default='muted', required=True)
    is_default = fields.Boolean()
    active = fields.Boolean(default=True)
    _code_unique = models.Constraint('UNIQUE(code)', 'Mã ưu tiên đã tồn tại.')

    @api.model
    def _default_record(self):
        return self.search([('is_default', '=', True)], limit=1) or self.search([], limit=1)


class Rating(models.Model):
    _name = 'tp.report.rating'
    _description = 'Danh mục mức đánh giá của cấp trên'
    _order = 'sequence, id'
    name = fields.Char(required=True)
    code = fields.Char(required=True)
    sequence = fields.Integer(default=10)
    color = fields.Selection(COLORS, default='muted', required=True)
    description = fields.Text()
    active = fields.Boolean(default=True)
    _code_unique = models.Constraint('UNIQUE(code)', 'Mã mức đánh giá đã tồn tại.')
