"""Company consistency for equipment links, independently of enabled-company access."""
from odoo import _, api, models
from odoo.exceptions import ValidationError

PARENT_FIELDS = {
    "tp.equipment.move.line": "move_id",
    "tp.equipment.receipt.line": "receipt_id",
    "tp.equipment.proposal.line": "proposal_id",
    "tp.equipment.software": "equipment_id",
    "tp.equipment.meter": "equipment_id",
}
CHILD_FIELDS = {
    "maintenance.equipment": ("tp_software_ids", "tp_meter_ids"),
    "tp.equipment.move": ("line_ids",),
    "tp.equipment.receipt": ("line_ids",),
    "tp.equipment.proposal": ("line_ids",),
}
EXCLUDED_MODELS = {"res.users", "res.company", "res.currency"}


def _constraint_fields(model):
    return [name for name, field in model._fields.items()
            if field.type == "many2one" and field.comodel_name not in EXCLUDED_MODELS] + [
                name for name in ("company_id",) + CHILD_FIELDS.get(model._name, ()) if name in model._fields]


def _record_company(record):
    if "company_id" in record._fields:
        return record.company_id
    parent = PARENT_FIELDS.get(record._name)
    return _record_company(record[parent]) if parent and record[parent] else record.env["res.company"]


def _check_company_links(records, expected_company=None):
    for record in records:
        company = _record_company(record)
        if not company or company not in record.env.companies:
            raise ValidationError(_("Hồ sơ thiết bị phải thuộc công ty đang được phép thao tác."))
        if expected_company and company != expected_company:
            raise ValidationError(_("Dòng thiết bị phải cùng công ty với hồ sơ cha."))
        for name in _constraint_fields(record):
            field = record._fields[name]
            if field.type != "many2one" or field.comodel_name in EXCLUDED_MODELS:
                continue
            target = record[name]
            if not target:
                continue
            target_company = _record_company(target)
            if target_company and target_company != company:
                # Do not put the target's name or company in a cross-scope error.
                raise ValidationError(_("Trường %(field)s phải liên kết cùng công ty với hồ sơ hoặc dữ liệu dùng chung.",
                                        field=field.string))
        for child_field in CHILD_FIELDS.get(record._name, ()):
            _check_company_links(record[child_field], expected_company=company)


class EquipmentCompanyScope(models.Model):
    _inherit = "maintenance.equipment"

    @api.constrains(_constraint_fields)
    def _tp_check_company_links(self):
        _check_company_links(self)


class MoveCompanyScope(models.Model):
    _inherit = "tp.equipment.move"

    @api.constrains(_constraint_fields)
    def _tp_check_company_links(self):
        _check_company_links(self)


class MoveLineCompanyScope(models.Model):
    _inherit = "tp.equipment.move.line"

    @api.constrains(_constraint_fields)
    def _tp_check_company_links(self):
        _check_company_links(self)


class ReceiptCompanyScope(models.Model):
    _inherit = "tp.equipment.receipt"

    @api.constrains(_constraint_fields)
    def _tp_check_company_links(self):
        _check_company_links(self)


class ReceiptLineCompanyScope(models.Model):
    _inherit = "tp.equipment.receipt.line"

    @api.constrains(_constraint_fields)
    def _tp_check_company_links(self):
        _check_company_links(self)


class ProposalCompanyScope(models.Model):
    _inherit = "tp.equipment.proposal"

    @api.constrains(_constraint_fields)
    def _tp_check_company_links(self):
        _check_company_links(self)


class ProposalLineCompanyScope(models.Model):
    _inherit = "tp.equipment.proposal.line"

    @api.constrains(_constraint_fields)
    def _tp_check_company_links(self):
        _check_company_links(self)


class SoftwareCompanyScope(models.Model):
    _inherit = "tp.equipment.software"

    @api.constrains(_constraint_fields)
    def _tp_check_company_links(self):
        _check_company_links(self)


class MeterCompanyScope(models.Model):
    _inherit = "tp.equipment.meter"

    @api.constrains(_constraint_fields)
    def _tp_check_company_links(self):
        _check_company_links(self)
