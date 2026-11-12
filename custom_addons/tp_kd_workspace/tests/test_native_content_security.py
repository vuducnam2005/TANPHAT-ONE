"""Regression for native sudo/ownership paths, using synthetic content only."""

from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged

from .test_opportunity_access import TestOpportunityAccess


@tagged("post_install", "-at_install")
class TestNativeContentSecurity(TestOpportunityAccess):
    def test_direct_message_create_and_message_attachment_respect_parent(self):
        lead = self.make()
        message = self.env["mail.message"].create(
            {
                "model": "crm.lead",
                "res_id": lead.id,
                "message_type": "comment",
                "body": "Synthetic draft",
            },
        )
        with self.assertRaises((AccessError, UserError)), self.env.cr.savepoint():
            self.env["mail.message"].with_user(self.support).create(
                {
                    "model": "crm.lead",
                    "res_id": lead.id,
                    "body": "Synthetic denied",
                    "message_type": "comment",
                },
            )
        attachment = self.env["ir.attachment"].create(
            {
                "name": "Synthetic message file",
                "res_model": "mail.message",
                "res_id": message.id,
                "raw": b"Synthetic private",
            },
        )
        with self.assertRaises((AccessError, UserError)):
            attachment.with_user(self.support).read(["raw"])
        self.assertFalse(
            attachment.with_user(self.support)._has_attachments_ownership([None]),
        )
        with self.assertRaises((AccessError, UserError)), self.env.cr.savepoint():
            self.env["ir.attachment"].with_user(self.support).create(
                {
                    "name": "Synthetic denied",
                    "res_model": "mail.message",
                    "res_id": message.id,
                    "type": "url",
                    "url": "https://example.invalid/synthetic",
                },
            )
        self.env["tp.kd.grant"].create(
            {
                "project_id": self.projects[0].id,
                "department_id": self.department.id,
                "user_id": self.owner.id,
                "domain": "opportunity",
                "capability": "submit",
                "reason": "Synthetic submit",
            },
        )
        lead.action_kd_prepare()
        lead.action_kd_record_submission()
        with self.assertRaises((AccessError, UserError)), self.env.cr.savepoint():
            self.env["mail.message"].with_user(self.owner).create(
                {
                    "model": "crm.lead",
                    "res_id": lead.id,
                    "body": "Synthetic denied submitted",
                    "message_type": "comment",
                },
            )
        with self.assertRaises((AccessError, UserError)), self.env.cr.savepoint():
            self.env["ir.attachment"].with_user(self.owner).sudo().create(
                {
                    "name": "Synthetic denied submitted",
                    "res_model": "mail.message",
                    "res_id": message.id,
                    "raw": b"Synthetic denied",
                },
            )

    def test_context_sharing_defaults_and_external_binary_access_are_denied(self):
        lead = self.make()
        message = self.env["mail.message"].create(
            {
                "model": "crm.lead",
                "res_id": lead.id,
                "message_type": "comment",
                "body": "Synthetic draft",
            },
        )
        for model, record_id in (("crm.lead", lead.id), ("mail.message", message.id)):
            values = {
                "name": "Synthetic context file",
                "res_model": model,
                "res_id": record_id,
                "raw": b"SYNTHETIC_PRIVATE_DEFAULTS",
            }
            for context in (
                {"default_public": True},
                {"default_access_token": "SYNTHETIC-TOKEN"},
            ):
                with self.subTest(model=model, context=context):
                    with self.assertRaises(AccessError), self.env.cr.savepoint():
                        self.env["ir.attachment"].with_user(
                            self.owner,
                        ).sudo().with_context(**context).create(values)
            allowed = (
                self.env["ir.attachment"]
                .with_user(self.owner)
                .with_context(
                    default_public=True,
                    default_access_token="SYNTHETIC-TOKEN",
                )
                .create({**values, "public": False, "access_token": False})
            )
            self.assertFalse(allowed.public)
            self.assertFalse(allowed.access_token)
            # Legacy technical attachments cannot expose CRM through a public flag or token either.
            legacy = self.env["ir.attachment"].create(
                {
                    **values,
                    "public": True,
                    "access_token": "SYNTHETIC-LEGACY-TOKEN",
                },
            )
            for token in (None, "SYNTHETIC-LEGACY-TOKEN"):
                with self.assertRaises(AccessError):
                    self.env["ir.binary"].with_user(
                        self.env.ref("base.public_user"),
                    )._find_record(
                        res_id=legacy.id,
                        access_token=token,
                    )

    def test_f1_ownership_does_not_replace_financial_read(self):
        lead = self.make()
        attachment = self.env["ir.attachment"].create(
            {
                "name": "Synthetic confidential.pdf",
                "res_model": "crm.lead",
                "res_id": lead.id,
                "raw": b"SYNTHETIC_PRIVATE_912345",
            },
        )
        self.assertFalse(
            attachment.with_user(self.support)._has_attachments_ownership([None]),
        )
        self.assertTrue(
            attachment.with_user(self.owner)._has_attachments_ownership([None]),
        )
        self.money.active = False
        self.assertFalse(
            attachment.with_user(self.owner)._has_attachments_ownership([None]),
        )

    def test_f2_native_sudo_actor_cannot_upload_submitted_evidence(self):
        lead = self.make()
        self.env["tp.kd.grant"].create(
            {
                "project_id": self.projects[0].id,
                "department_id": self.department.id,
                "user_id": self.owner.id,
                "domain": "opportunity",
                "capability": "submit",
                "reason": "Synthetic submit",
            },
        )
        lead.action_kd_prepare()
        lead.action_kd_record_submission()
        before = self.env["ir.attachment"].search_count(
            [("res_model", "=", "crm.lead"), ("res_id", "=", lead.id)],
        )
        with self.assertRaises((AccessError, UserError)), self.env.cr.savepoint():
            self.env["ir.attachment"].with_user(self.owner).sudo().create(
                {
                    "name": "Synthetic denied",
                    "res_model": "crm.lead",
                    "res_id": lead.id,
                    "raw": b"SYNTHETIC_DENIED",
                },
            )
        self.assertEqual(
            before,
            self.env["ir.attachment"].search_count(
                [("res_model", "=", "crm.lead"), ("res_id", "=", lead.id)],
            ),
        )

    def test_f3_author_fallback_cannot_return_hidden_body(self):
        lead = self.make()
        message = self.env["mail.message"].create(
            {
                "model": "crm.lead",
                "res_id": lead.id,
                "author_id": self.support.partner_id.id,
                "message_type": "comment",
                "body": "SYNTHETIC_PRIVATE_912345",
            },
        )
        hidden = message.with_user(self.support).sudo()._get_with_access(mode="write")
        self.assertFalse(hidden)
        with self.assertRaises((AccessError, UserError)), self.env.cr.savepoint():
            lead.with_user(self.support).sudo().message_post(
                body="SYNTHETIC_DENIED",
                message_type="comment",
                subtype_xmlid="mail.mt_note",
            )

    def test_native_owner_draft_and_other_models_still_work(self):
        lead = self.make()
        attachment = (
            self.env["ir.attachment"]
            .with_user(self.owner)
            .sudo()
            .create(
                {
                    "name": "Synthetic allowed",
                    "res_model": "crm.lead",
                    "res_id": lead.id,
                    "raw": b"allowed",
                },
            )
        )
        attachment.with_user(self.owner).sudo().unlink()
        lead.message_post(
            body="Synthetic allowed",
            message_type="comment",
            subtype_xmlid="mail.mt_note",
        )
        partner = self.env["res.partner"].create({"name": "Synthetic other model"})
        partner.message_post(
            body="Synthetic ordinary mail",
            message_type="comment",
            subtype_xmlid="mail.mt_note",
        )
