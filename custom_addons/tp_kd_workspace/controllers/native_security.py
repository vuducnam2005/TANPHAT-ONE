"""Check the original parent before native upload loses its pending thread link."""

from odoo import http
from odoo.http import request

from odoo.addons.mail.controllers.attachment import AttachmentController
from odoo.addons.tp_kd_workspace.models.native_content_security import actor_leads


class KdAttachmentController(AttachmentController):
    @http.route()
    def mail_attachment_upload(
        self,
        ufile,
        thread_id,
        thread_model,
        is_pending=False,
        **kwargs,
    ):
        if thread_model == "crm.lead":
            actor_leads(request.env, [int(thread_id)], mutate=True)
        return super().mail_attachment_upload(
            ufile,
            thread_id,
            thread_model,
            is_pending=is_pending,
            **kwargs,
        )

    @http.route()
    def mail_attachement_update_thumbnail(
        self,
        attachment_id,
        thumbnail=None,
        access_token=None,
    ):
        request.env["ir.attachment"].browse(int(attachment_id))._kd_native_parent(
            mutate=True,
        )
        return super().mail_attachement_update_thumbnail(
            attachment_id,
            thumbnail,
            access_token,
        )
