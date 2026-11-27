# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
import uuid
from unittest.mock import MagicMock, patch

from odoo import fields
from odoo.http import Response
from odoo.tests import tagged

from odoo.addons.tp_equipment.controllers.main import TpEquipmentQr
from odoo.addons.tp_equipment.models.common import INTERNAL
from odoo.addons.tp_hr_workspace.tests.test_hr_workspace import BaseHrWorkspace


@tagged("post_install", "-at_install")
class TestEquipmentQrAndRepairs(BaseHrWorkspace):
    """T-0005 (F-0008, F-0009): Verify internal SVG QR endpoint + repair list empty-state config."""

    def test_qr_url_and_repair_action_config(self):
        eq = self.env["maintenance.equipment"].create({
            "name": "Máy in HP LaserJet Test",
            "company_id": self.company.id,
            "tp_custody": "stock",
            "tp_technical_state": "good",
            "tp_ownership": "company",
            "tp_asset_class": "device",
            "serial_no": f"SN-{uuid.uuid4().hex[:6].upper()}",
        })
        # Draft equipment has no QR image URL
        self.assertEqual(eq.tp_lifecycle, "draft")
        self.assertFalse(eq.tp_qr_image_url)

        # Active equipment points to internal authenticated SVG endpoint (never /report/barcode/)
        eq.with_context(tp_equipment_move=INTERNAL).write({
            "tp_lifecycle": "active",
            "tp_registered_date": fields.Datetime.now(),
            "tp_registered_by_id": self.admin.id,
        })
        eq.invalidate_recordset()
        self.assertTrue(eq.tp_qr_token)
        self.assertEqual(eq.tp_qr_image_url, f"/tp_equipment/qr_image/{eq.tp_qr_token}")
        self.assertNotIn("/report/barcode", eq.tp_qr_image_url)

        # Verify action_repairs has clean path & Vietnamese empty-state help
        act = self.env.ref("tp_equipment.action_repairs")
        self.assertEqual(act.path, "sua-chua-thiet-bi")
        self.assertIn("sửa chữa", (act.help or "").lower())

    def test_qr_svg_controller_access_and_rendering(self):
        eq = self.env["maintenance.equipment"].create({
            "name": "Laptop ThinkPad QR Test",
            "company_id": self.company.id,
            "tp_custody": "stock",
            "tp_technical_state": "good",
            "tp_ownership": "company",
            "tp_asset_class": "device",
            "serial_no": f"SN-{uuid.uuid4().hex[:6].upper()}",
        })
        eq.with_context(tp_equipment_move=INTERNAL).write({
            "tp_lifecycle": "active",
            "tp_registered_date": fields.Datetime.now(),
            "tp_registered_by_id": self.admin.id,
        })
        ctrl = TpEquipmentQr()

        def make_resp(body, headers=None, status=200):
            return Response(body, headers=headers, status=status)

        # Admin gets 200 image/svg+xml containing valid <svg>
        fake_req_admin = MagicMock()
        fake_req_admin.env = self.env(user=self.admin)
        fake_req_admin.make_response.side_effect = make_resp
        with patch("odoo.addons.tp_equipment.controllers.main.request", fake_req_admin):
            res_ok = ctrl.qr_image(eq.tp_qr_token)
            self.assertEqual(res_ok.status_code, 200)
            self.assertIn("image/svg+xml", res_ok.headers.get("Content-Type", ""))
            body_text = res_ok.get_data(as_text=True)
            self.assertIn("<svg", body_text)

            # Unknown token returns 404
            res_404 = ctrl.qr_image("0" * 32)
            self.assertEqual(res_404.status_code, 404)

        # Regular employee without system admin rights gets 403
        staff_user = self.env["res.users"].create({
            "name": "Nhân viên thường QR",
            "login": f"staff_qr_{uuid.uuid4().hex[:6]}",
            "company_id": self.company.id,
            "company_ids": [(6, 0, [self.company.id])],
            "group_ids": [(6, 0, [self.env.ref("base.group_user").id])],
        })
        fake_req_staff = MagicMock()
        fake_req_staff.env = self.env(user=staff_user)
        fake_req_staff.make_response.side_effect = make_resp
        with patch("odoo.addons.tp_equipment.controllers.main.request", fake_req_staff):
            res_403 = ctrl.qr_image(eq.tp_qr_token)
            self.assertEqual(res_403.status_code, 403)
