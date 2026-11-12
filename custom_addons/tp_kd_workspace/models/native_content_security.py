"""Keep the original caller's CRM policy across native mail sudo fallbacks."""

from odoo import api, models
from odoo.exceptions import AccessError, UserError
from odoo.fields import Domain

from .workspace import _INTERNAL


def actor_leads(env, ids, mutate=False):
    actor = env["crm.lead"].sudo(False).browse(ids)
    if ids and not env.user.sudo(False)._is_internal():
        raise AccessError(env._("Không chia sẻ hồ sơ CRM cho truy cập bên ngoài."))
    if not actor._kd_scoped() or env.context.get("_kd_internal") is _INTERNAL:
        return
    actor.check_access("read")
    actor._kd_require_money()
    if mutate:
        actor._kd_require()
        for lead in actor.sorted("id"):
            lead._kd_lock_bid()
        actor._kd_require()
        actor._kd_require_money()
        if any(lead.kd_bid_state == "submitted" for lead in actor):
            raise UserError(
                env._(
                    "Không thay căn cứ hoặc trao đổi trên hồ sơ đã nộp. Dùng nhật ký bổ sung được phân quyền.",
                ),
            )


def attachment_parent_ids(env, model, record_id):
    if model == "crm.lead" and record_id:
        return [record_id]
    if model == "mail.message" and record_id:
        message = env["mail.message"].sudo().browse(record_id).exists()
        if message.model == "crm.lead" and message.res_id:
            return [message.res_id]
    return []


class Attachment(models.Model):
    _inherit = "ir.attachment"

    def _kd_native_parent(self, mutate=False):
        ids = []
        for row in self.sudo():
            ids += attachment_parent_ids(self.env, row.res_model, row.res_id)
        actor_leads(self.env, ids, mutate)

    def read(self, fields=None, load="_classic_read"):
        self._kd_native_parent()
        return super().read(fields=fields, load=load)

    def export_data(self, fields_to_export):
        self._kd_native_parent()
        return super().export_data(fields_to_export)

    def _search_kd_crm_accessible(self, operator, value):
        base = super()._search_kd_crm_accessible(operator, value)
        if base is NotImplemented:
            return base
        return base & (
            Domain("res_model", "!=", "mail.message")
            | Domain("res_id", "in", self.env["mail.message"]._search([]))
        )

    def _has_attachments_ownership(self, attachment_tokens):
        try:
            self._kd_native_parent()
        except (AccessError, UserError):
            return False
        return super()._has_attachments_ownership(attachment_tokens)

    @api.model_create_multi
    def create(self, vals_list):
        defaults = self.default_get(["res_model", "res_id", "public", "access_token"])
        for supplied in vals_list:
            vals = {**defaults, **supplied}
            ids = attachment_parent_ids(
                self.env,
                vals.get("res_model"),
                vals.get("res_id"),
            )
            actor_leads(self.env, ids, mutate=True)
            if (
                ids
                and self.env["crm.lead"].sudo(False)._kd_scoped()
                and (vals.get("public") or vals.get("access_token"))
            ):
                raise AccessError(self.env._("Không chia sẻ file CRM công khai."))
        return super().create(vals_list)

    def write(self, vals):
        self._kd_native_parent(mutate=True)
        for row in self.sudo():
            actor_leads(
                self.env,
                attachment_parent_ids(
                    self.env,
                    vals.get("res_model", row.res_model),
                    vals.get("res_id", row.res_id),
                ),
                mutate=True,
            )
        if self.env["crm.lead"].sudo(False)._kd_scoped():
            crm = vals.get("res_model") in ("crm.lead", "mail.message") or any(
                attachment_parent_ids(self.env, a.res_model, a.res_id)
                for a in self.sudo()
            )
            if crm and set(vals) & {
                "res_model",
                "res_id",
                "res_field",
                "public",
                "access_token",
            }:
                raise AccessError(
                    self.env._(
                        "Không đổi liên kết hoặc chia sẻ file CRM qua đường native.",
                    ),
                )
        return super().write(vals)

    def unlink(self):
        self._kd_native_parent(mutate=True)
        return super().unlink()


class Message(models.Model):
    _inherit = "mail.message"

    @api.model_create_multi
    def create(self, vals_list):
        defaults = self.default_get(["model", "res_id"])
        for supplied in vals_list:
            vals = {**defaults, **supplied}
            if vals.get("model") == "crm.lead" and vals.get("res_id"):
                actor_leads(self.env, [vals["res_id"]], mutate=True)
        return super().create(vals_list)

    def _get_with_access(self, mode="read", **kwargs):
        rows = self.sudo().filtered(lambda m: m.model == "crm.lead" and m.res_id)
        try:
            actor_leads(self.env, rows.mapped("res_id"), mutate=mode != "read")
        except (AccessError, UserError):
            return self.browse()
        return super()._get_with_access(mode=mode, **kwargs)

    def write(self, vals):
        if vals:
            rows = self.sudo().filtered(lambda m: m.model == "crm.lead" and m.res_id)
            actor_leads(self.env, rows.mapped("res_id"), mutate=True)
            for row in self.sudo():
                if vals.get("model", row.model) == "crm.lead" and vals.get(
                    "res_id",
                    row.res_id,
                ):
                    actor_leads(self.env, [vals.get("res_id", row.res_id)], mutate=True)
        return super().write(vals)

    def unlink(self):
        rows = self.sudo().filtered(lambda m: m.model == "crm.lead" and m.res_id)
        actor_leads(self.env, rows.mapped("res_id"), mutate=True)
        return super().unlink()


class Binary(models.AbstractModel):
    _inherit = "ir.binary"

    def _find_record(
        self,
        xmlid=None,
        res_model="ir.attachment",
        res_id=None,
        access_token=None,
        field=None,
    ):
        record = (
            self.env.ref(xmlid, False)
            if xmlid
            else (
                self.env[res_model].browse(res_id).exists()
                if res_id and res_model in self.env
                else None
            )
        )
        if record and record._name == "ir.attachment":
            record._kd_native_parent()
        return super()._find_record(xmlid, res_model, res_id, access_token, field)


class Opportunity(models.Model):
    _inherit = "crm.lead"

    def _message_log_batch(self, bodies, **kwargs):
        # Only the private server log path may record an already-authorized change.
        return super(
            Opportunity,
            self.with_context(_kd_internal=_INTERNAL),
        )._message_log_batch(bodies, **kwargs)

    @api.model_create_multi
    def create(self, vals_list):
        # Native creation's automatic chatter is not an actor-authored comment.
        if not self.sudo(False)._kd_scoped():
            return super().create(vals_list)
        records = super(Opportunity, self.with_context(mail_create_nolog=True)).create(
            vals_list,
        )
        return records.with_env(self.env)

    @api.model
    def _get_thread_with_access(self, thread_id, *, mode="read", **kwargs):
        try:
            actor_leads(self.env, [thread_id], mutate=mode != "read")
        except (AccessError, UserError):
            return self.browse()
        return super()._get_thread_with_access(thread_id, mode=mode, **kwargs)

    def message_post(self, **kwargs):
        actor_leads(self.env, self.ids, mutate=True)
        return super().message_post(**kwargs)

    def _message_update_content(self, message, /, **kwargs):
        actor_leads(self.env, self.ids, mutate=True)
        return super()._message_update_content(message, **kwargs)
