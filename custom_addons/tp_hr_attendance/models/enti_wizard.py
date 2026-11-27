"""Wizard for ENTI connection configuration, testing, and manual sync (ENTI-LIVE-001).

Restricted to HR Manager and Admin.
Never echoes the saved password back to the UI.
Only displays 'Đã cấu hình' / 'Chưa cấu hình'.
"""
from odoo import api, fields, models
from odoo.exceptions import UserError

from .attendance_common import DEFAULT_TZ, internal, local_today
from .enti_client import EntiClient
from .enti_image import check_enti_image_access
from .enti_sync import _get_enti_credentials, _save_enti_credentials


class AttendanceEntiConfigWizard(models.TransientModel):
    _name = "tp.hr.attendance.enti.config.wizard"
    _description = "Cấu hình kết nối chấm công ENTI"

    company_id = fields.Many2one(
        "res.company",
        "Công ty",
        required=True,
        default=lambda self: self.env.company,
    )
    phone = fields.Char("Số điện thoại tài khoản ENTI")
    password = fields.Char("Mật khẩu tài khoản ENTI")
    app_key = fields.Char("Khóa ứng dụng (Tùy chọn)")

    is_configured = fields.Boolean("Đã cấu hình", compute="_compute_status")
    status_display = fields.Char("Trạng thái cấu hình", compute="_compute_status")
    last_test_result = fields.Text("Kết quả kiểm tra kết nối", readonly=True)

    date_from = fields.Date(
        "Đồng bộ từ ngày",
        default=lambda self: local_today(DEFAULT_TZ).replace(day=1),
    )
    date_to = fields.Date(
        "Đồng bộ đến ngày",
        default=lambda self: local_today(DEFAULT_TZ),
    )

    @api.depends("company_id")
    def _compute_status(self):
        saved_phone, saved_pass, _app = _get_enti_credentials(self.env)
        for rec in self:
            rec.is_configured = bool(saved_phone and saved_pass)
            rec.status_display = "Đã cấu hình thông tin xác thực" if rec.is_configured else "Chưa cấu hình"

    def _check_permission(self):
        check_enti_image_access(self.env, self.company_id or self.env.company)

    def _scrub_password(self):
        if self.ids:
            self.sudo().write({"password": False})

    def action_test_connection(self):
        """Test authentication with ENTI without persisting credentials."""
        self.ensure_one()
        self._check_permission()

        test_phone = self.phone
        test_pass = self.password
        self._scrub_password()

        # If not typed in wizard, check existing saved credentials
        if not test_phone or not test_pass:
            saved_phone, saved_pass, _saved_app = _get_enti_credentials(self.env)
            test_phone = test_phone or saved_phone
            test_pass = test_pass or saved_pass

        if not test_phone or not test_pass:
            raise UserError(self.env._("Vui lòng nhập số điện thoại và mật khẩu ENTI để kiểm tra."))

        client = EntiClient()
        try:
            login_data = client.login(test_phone, test_pass)
            user_data = client.get_me()
            apps = client.get_apps()
            matched_app = client.find_app_for_company(self.company_id.name or "Tấn Phát")

            app_name = matched_app.get("name") if matched_app else "Chưa tìm thấy ứng dụng Tấn Phát"
            app_key = matched_app.get("app_key") or matched_app.get("key") or matched_app.get("id") if matched_app else ""

            msg = (
                f"✓ Đăng nhập ENTI thành công!\n"
                f"• Tài khoản: {user_data.get('data', {}).get('phone') or user_data.get('data', {}).get('name') or 'Hợp lệ'}\n"
                f"• Token hiệu lực: {login_data.get('expires_in', 900)} giây\n"
                f"• Số ứng dụng tìm thấy: {len(apps)}\n"
                f"• Ứng dụng công ty: {app_name} (khóa: {app_key})\n"
                f"Sẵn sàng lưu cấu hình và đồng bộ."
            )
            self.write({
                "last_test_result": msg,
                "app_key": app_key or self.app_key,
            })
            return {
                "type": "ir.actions.act_window",
                "res_model": self._name,
                "res_id": self.id,
                "view_mode": "form",
                "target": "new",
            }
        except Exception as exc:  # noqa: BLE001
            self.write({"last_test_result": f"✗ Lỗi kết nối ENTI: {exc}"})
            return {
                "type": "ir.actions.act_window",
                "res_model": self._name,
                "res_id": self.id,
                "view_mode": "form",
                "target": "new",
            }

    def action_save_credentials(self):
        """Save credentials securely and setup the ENTI source."""
        self.ensure_one()
        self._check_permission()

        raw_phone = self.phone
        raw_pass = self.password
        if not raw_phone or not raw_pass:
            raise UserError(self.env._("Vui lòng nhập đầy đủ số điện thoại và mật khẩu."))

        _save_enti_credentials(self.env, raw_phone, raw_pass, self.app_key)
        self._scrub_password()

        # Find or create ENTI Attendance Source record
        Source = internal(self.env["tp.hr.attendance.source"])
        source = Source.search([
            ("company_id", "=", self.company_id.id),
            ("kind", "=", "enti_api"),
        ], limit=1)

        vals = {
            "name": "API máy chấm công ENTI",
            "company_id": self.company_id.id,
            "kind": "enti_api",
            "namespace": "enti-tanphat",
            "vendor": "ENTI",
            "device_model": "Cloud API (enti.vn)",
            "timezone": DEFAULT_TZ,
            "state": "ready",
            "live_enabled": True,
        }
        if source:
            internal(source).write(vals)
        else:
            source = Source.create(vals)

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Cấu hình thành công",
                "message": "Thông tin xác thực ENTI đã được lưu bảo mật và nguồn kết nối đã sẵn sàng.",
                "type": "success",
                "sticky": False,
            },
        }

    def action_sync_now(self):
        """Trigger immediate sync for the specified date range."""
        self.ensure_one()
        self._check_permission()
        self._scrub_password()

        Source = internal(self.env["tp.hr.attendance.source"])
        source = Source.search([
            ("company_id", "=", self.company_id.id),
            ("kind", "=", "enti_api"),
        ], limit=1)

        if not source:
            # Auto-create if credentials exist
            phone, password, _app = _get_enti_credentials(self.env)
            if not phone or not password:
                raise UserError(self.env._("Vui lòng lưu thông tin xác thực trước khi đồng bộ."))
            source = Source.create({
                "name": "API máy chấm công ENTI",
                "company_id": self.company_id.id,
                "kind": "enti_api",
                "namespace": "enti-tanphat",
                "vendor": "ENTI",
                "device_model": "Cloud API (enti.vn)",
                "timezone": DEFAULT_TZ,
                "state": "ready",
                "live_enabled": True,
            })

        res = source.action_sync_enti_now(start_date=self.date_from, end_date=self.date_to)
        if not res.get("success"):
            raise UserError(self.env._(
                "%(msg)s Dữ liệu công đã có được giữ nguyên.",
                msg=res.get("message") or "Đồng bộ ENTI chưa thành công.",
            ))
        msg = (
            f"Đồng bộ ENTI thành công:\n"
            f"• Nhân viên ENTI: {res.get('employees')}\n"
            f"• Đã khớp Odoo: {res.get('mapped')}\n"
            f"• Chưa đối chiếu: {res.get('unmapped')}\n"
            f"• Ngày công áp dụng: {res.get('days_applied')}\n"
            f"• Thời gian: {res.get('duration')}s"
        )
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Đồng bộ hoàn tất",
                "message": msg,
                "type": "success",
                "sticky": True,
            },
        }
