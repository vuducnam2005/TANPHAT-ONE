# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
"""Idempotency log for write operations across TANPHAT ONE Personal Tools.

Prevents duplicate task, calendar event, or shared message creation on double-click
or lost-response network retries while verifying payload fingerprint integrity.
"""

import hashlib
import json

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class TpPersonalOperationLog(models.Model):
    _name = "tp.personal.operation.log"
    _description = "Nhật ký chống lặp thao tác Công cụ cá nhân"
    _order = "id desc"

    actor_id = fields.Many2one(
        "res.users",
        required=True,
        readonly=True,
        index=True,
        ondelete="cascade",
        default=lambda self: self.env.uid,
    )
    operation = fields.Char(required=True, readonly=True, index=True)
    token = fields.Char(required=True, readonly=True, index=True)
    fingerprint = fields.Char(required=True, readonly=True)
    target_model = fields.Char(readonly=True)
    target_id = fields.Integer(readonly=True)

    _tp_personal_op_unique = models.UniqueIndex("(actor_id, operation, token)")

    @api.model
    def compute_fingerprint(self, payload):
        raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @api.model
    def acquire_or_replay(self, operation, token, payload):
        """Serialize same-(actor, operation, token) calls via advisory transaction lock.

        Returns `(existing_record_or_None, cleaned_token, fingerprint)`.
        """
        clean_token = str(token or "").strip()[:128]
        fp = self.compute_fingerprint(payload)
        if not clean_token:
            return None, "", fp

        lock_key_bytes = hashlib.sha256(
            f"tp_personal_op:{self.env.uid}:{operation}:{clean_token}".encode("utf-8")
        ).digest()[:8]
        lock_id = int.from_bytes(lock_key_bytes, byteorder="big", signed=True)
        self.env.cr.execute("SELECT pg_advisory_xact_lock(%s)", (lock_id,))

        existing = self.sudo().search(
            [
                ("actor_id", "=", self.env.uid),
                ("operation", "=", operation),
                ("token", "=", clean_token),
            ],
            limit=1,
        )
        if existing:
            if existing.fingerprint != fp:
                raise ValidationError(
                    self.env._(
                        "Mã thao tác này đã được sử dụng cho một nội dung khác. Vui lòng thử lại."
                    )
                )
            if existing.target_model and existing.target_id:
                rec = self.env[existing.target_model].browse(existing.target_id).exists()
                if rec and rec.has_access("read"):
                    return rec, clean_token, fp
        return None, clean_token, fp

    @api.model
    def record_success(self, operation, clean_token, fingerprint, target):
        if not clean_token or not target:
            return
        self.sudo().create(
            {
                "actor_id": self.env.uid,
                "operation": operation,
                "token": clean_token,
                "fingerprint": fingerprint,
                "target_model": target._name,
                "target_id": target.id,
            }
        )
