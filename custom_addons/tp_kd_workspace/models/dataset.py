from odoo import api, fields, models
from odoo.exceptions import AccessError, ValidationError


class Dataset(models.Model):
    _name = "tp.kd.dataset"
    _description = "Synthetic dataset provenance; technical operators only"
    name = fields.Char(required=True, readonly=True)
    database = fields.Char(required=True, readonly=True)
    namespace = fields.Char(required=True, readonly=True)
    entry_ids = fields.One2many("tp.kd.dataset.entry", "dataset_id")
    anchor_date = fields.Date(required=True, readonly=True)
    _name_unique = models.Constraint("UNIQUE(name)", "Dataset đã tồn tại.")

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.su:
            raise AccessError(self.env._("Registry chỉ dành cho công cụ vận hành."))
        return super().create(vals_list)

    def write(self, vals):
        raise AccessError(self.env._("Giữ nguyên danh tính dataset."))

    def unlink(self):
        raise AccessError(self.env._("Giữ provenance kể cả khi bản ghi đã được dọn."))


class DatasetEntry(models.Model):
    _name = "tp.kd.dataset.entry"
    _description = "Durable ownership registry; no business record deletion bypass"
    dataset_id = fields.Many2one("tp.kd.dataset", required=True, ondelete="restrict")
    key = fields.Char(required=True, readonly=True)
    model = fields.Char(required=True, readonly=True)
    res_id = fields.Integer(required=True, readonly=True)
    external_id = fields.Char(required=True, readonly=True)
    owned = fields.Boolean(readonly=True)
    category = fields.Char(readonly=True)
    checksum = fields.Char(readonly=True)
    status = fields.Selection(
        [("present", "Present"), ("unlinked", "Unlinked")],
        default="present",
        required=True,
    )
    _key_unique = models.Constraint(
        "UNIQUE(dataset_id,key)", "Khóa dataset đã tồn tại.",
    )
    _record_unique = models.Constraint(
        "UNIQUE(dataset_id,model,res_id)", "Bản ghi đã có trong registry.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        if not self.env.su:
            raise AccessError(self.env._("Không được nhận ownership dữ liệu qua RPC."))
        for vals in vals_list:
            if (
                vals.get("model") not in self.env
                or not self.env[vals["model"]].browse(vals.get("res_id")).exists()
            ):
                raise ValidationError(self.env._("Registry cần bản ghi tồn tại."))
        return super().create(vals_list)

    def write(self, vals):
        if not self.env.su or set(vals) - {"checksum", "status"}:
            raise AccessError(
                self.env._("Không đổi ownership/khóa/model của registry."),
            )
        return super().write(vals)

    def unlink(self):
        raise AccessError(self.env._("Giữ registry cho provenance và cleanup audit."))
