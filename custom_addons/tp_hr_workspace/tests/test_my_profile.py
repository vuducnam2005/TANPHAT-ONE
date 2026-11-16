import base64
import io
import json

from markupsafe import Markup
from PIL import Image

from odoo import Command
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import HttpCase, tagged


def _make_test_png():
    buf = io.BytesIO()
    Image.new('RGB', (4, 4), (37, 99, 235)).save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode('ascii')


TINY_PNG = _make_test_png()


@tagged('post_install', '-at_install')
class TestHrSelfProfile(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env['res.company'].create({'name': 'Synthetic SelfProfile Co'})
        cls.env.ref('base.user_admin').write({'company_ids': [Command.link(cls.company.id)]})
        cls.hr_user = cls.env['res.users'].create({
            'name': 'Synthetic SP HR',
            'login': 'sp.test.hr',
            'password': 'sp.test.hr.pw',
            'company_id': cls.company.id,
            'company_ids': [Command.set(cls.company.ids)],
            'group_ids': [Command.set([cls.env.ref('hr.group_hr_user').id])],
        })
        cls.staff = cls.env['res.users'].create({
            'name': 'Nguyen Self Staff',
            'login': 'sp.test.staff',
            'password': 'sp.test.staff.pw',
            'company_id': cls.company.id,
            'company_ids': [Command.set(cls.company.ids)],
            'group_ids': [Command.set([cls.env.ref('tp_kd_workspace.group_scoped_staff').id])],
        })
        cls.other_user = cls.env['res.users'].create({
            'name': 'Other Self Staff',
            'login': 'sp.test.other',
            'password': 'sp.test.other.pw',
            'company_id': cls.company.id,
            'company_ids': [Command.set(cls.company.ids)],
            'group_ids': [Command.set([cls.env.ref('base.group_user').id])],
        })
        cls.unlinked_user = cls.env['res.users'].create({
            'name': 'Unlinked Account',
            'login': 'sp.test.unlinked',
            'company_id': cls.company.id,
            'company_ids': [Command.set(cls.company.ids)],
            'group_ids': [Command.set([cls.env.ref('base.group_user').id])],
        })
        cls.department = cls.env['hr.department'].with_company(cls.company).create({
            'name': 'Synthetic SP Dept',
            'company_id': cls.company.id,
        })
        cls.job = cls.env['hr.job'].with_company(cls.company).create({
            'name': 'Synthetic SP Engineer',
            'company_id': cls.company.id,
        })
        cls.employee = cls.env['hr.employee'].with_company(cls.company).create({
            'name': 'Nguyen Self Staff',
            'user_id': cls.staff.id,
            'work_contact_id': cls.staff.partner_id.id,
            'company_id': cls.company.id,
            'department_id': cls.department.id,
            'job_id': cls.job.id,
            'date_version': '2026-01-01',
            'contract_date_start': '2026-01-01',
            'contract_date_end': '2027-01-01',
            'tp_employment_kind': 'long_term',
        })
        cls.other_employee = cls.env['hr.employee'].with_company(cls.company).create({
            'name': 'Other Self Staff',
            'user_id': cls.other_user.id,
            'work_contact_id': cls.other_user.partner_id.id,
            'company_id': cls.company.id,
            'date_version': '2026-01-01',
        })
        cls.staff_doc = cls.env['tp.hr.contract.document'].with_user(cls.hr_user).with_company(cls.company).create({
            'employee_id': cls.employee.id,
            'kind': 'labor',
            'number': 'HD-SP-001',
            'name': 'Hop dong lao dong chuan',
            'file': base64.b64encode(b'%PDF-1.4\nmy-contract').decode('ascii'),
            'filename': 'hd-self.pdf',
        })
        cls.other_doc = cls.env['tp.hr.contract.document'].with_user(cls.hr_user).with_company(cls.company).create({
            'employee_id': cls.other_employee.id,
            'kind': 'labor',
            'number': 'HD-OTHER-999',
            'name': 'Hop dong nguoi khac',
            'file': base64.b64encode(b'%PDF-1.4\nsecret-other').decode('ascii'),
            'filename': 'hd-other.pdf',
        })

    def _staff_users(self, actor=None):
        return self.env['res.users'].with_user(actor or self.staff).with_context(allowed_company_ids=self.company.ids)

    def test_self_profile_read_update_syncs_and_preserves_hr_acls(self):
        # Non-HR user still cannot directly read private HR fields, write hr.employee, or read contracts.
        with self.assertRaises(AccessError):
            self.env['hr.employee'].with_user(self.staff).browse(self.employee.id).read(['identification_id'])
        with self.assertRaises(AccessError):
            self.env['hr.employee'].with_user(self.staff).browse(self.employee.id).write({'mobile_phone': '0999'})
        with self.assertRaises(AccessError):
            self.env['tp.hr.contract.document'].with_user(self.staff).browse(self.staff_doc.id).read(['name'])

        profile = self._staff_users().tp_get_my_profile()
        self.assertTrue(profile['has_employee'])
        self.assertEqual(profile['header']['name'], 'Nguyen Self Staff')
        self.assertEqual(profile['header']['department_name'], 'Synthetic SP Dept')
        self.assertEqual(profile['contracts']['employment_kind'], 'long_term')
        self.assertEqual(profile['contracts']['contract_date_start'], '2026-01-01')
        doc_numbers = [d['number'] for d in profile['contracts']['documents']]
        self.assertIn('HD-SP-001', doc_numbers)
        self.assertNotIn('HD-OTHER-999', doc_numbers)

        # Updating permitted personal fields writes straight through to HR Admin's hr.employee record.
        updated = self._staff_users().tp_save_my_profile({
            'mobile_phone': '0912345678',
            'private_email': 'thuyanh.private@example.com',
            'private_street': '123 Duong Le Loi',
            'birthday': '1995-05-20',
            'identification_id': '079095001234',
            'emergency_contact': 'Nguyen Van A',
            'emergency_phone': '0988776655',
            'children': 2,
            'distance_home_work': 12,
            'image_1920': TINY_PNG,
        })
        self.employee.invalidate_recordset()
        hr_view = self.employee.with_user(self.hr_user).with_context(allowed_company_ids=self.company.ids)
        self.assertEqual(hr_view.mobile_phone, '0912345678')
        self.assertEqual(hr_view.private_email, 'thuyanh.private@example.com')
        self.assertEqual(hr_view.private_street, '123 Duong Le Loi')
        self.assertEqual(str(hr_view.birthday), '1995-05-20')
        self.assertEqual(hr_view.identification_id, '079095001234')
        self.assertEqual(hr_view.children, 2)
        self.assertTrue(hr_view.tp_personal_defaults_confirmed)
        self.assertTrue(bool(hr_view.with_context(bin_size=False).image_1920))
        self.assertTrue(bool(self.staff.partner_id.with_context(bin_size=False).image_1920))
        self.assertTrue(any('Nhân viên tự cập nhật thông tin cá nhân' in item['body'] for item in updated['history']))

    def test_self_profile_blocks_forbidden_hr_and_contract_fields(self):
        for forbidden_payload in (
            {'name': 'Tu Doi Ten'},
            {'department_id': False},
            {'job_id': False},
            {'tp_employee_code': 'TP19999'},
            {'tp_employment_kind': 'outsourced'},
            {'contract_date_start': '2020-01-01'},
            {'user_id': self.other_user.id},
        ):
            with self.assertRaises(AccessError):
                self._staff_users().tp_save_my_profile(forbidden_payload)

        with self.assertRaises(ValidationError):
            self._staff_users().tp_save_my_profile({'image_1920': 'not-a-valid-image'})

    def test_self_service_resume_and_skills_scoped_to_own_employee(self):
        resume_type = self.env['hr.resume.line.type'].create({'name': 'Kinh nghiem test'})
        updated = self._staff_users().tp_save_my_resume_line(None, {
            'name': 'Ky su cau duong',
            'line_type_id': resume_type.id,
            'date_start': '2022-01-01',
            'date_end': '2025-12-31',
            'description': 'Thiet ke ket cau nhip chinh',
        })
        self.assertEqual(len(updated['resume']['lines']), 1)
        line_id = updated['resume']['lines'][0]['id']

        other_line = self.env['hr.resume.line'].sudo().create({
            'employee_id': self.other_employee.id,
            'name': 'Other line',
            'line_type_id': resume_type.id,
            'date_start': '2021-01-01',
        })
        with self.assertRaises(AccessError):
            self._staff_users().tp_save_my_resume_line(other_line.id, {'name': 'Hacked', 'date_start': '2021-01-01'})
        with self.assertRaises(AccessError):
            self._staff_users().tp_delete_my_resume_line(other_line.id)

        after_del = self._staff_users().tp_delete_my_resume_line(line_id)
        self.assertEqual(len(after_del['resume']['lines']), 0)

    def test_contract_file_route_allows_own_and_blocks_other(self):
        self.authenticate('sp.test.staff', 'sp.test.staff.pw')
        own_res = self.url_open(f'/tp_hr/my_contract/{self.staff_doc.id}/file')
        self.assertEqual(own_res.status_code, 200)
        self.assertIn(b'my-contract', own_res.content)
        self.assertIn('attachment', own_res.headers.get('Content-Disposition', ''))

        other_res = self.url_open(f'/tp_hr/my_contract/{self.other_doc.id}/file')
        self.assertEqual(other_res.status_code, 403)

    def test_unlinked_user_profile_fallback(self):
        profile = self._staff_users(self.unlinked_user).tp_get_my_profile()
        self.assertFalse(profile['has_employee'])
        self.assertEqual(profile['user']['login'], 'sp.test.unlinked')
        with self.assertRaises(ValidationError):
            self._staff_users(self.unlinked_user).tp_save_my_profile({'mobile_phone': '0900000000'})

    def test_history_hides_raw_json_localizes_tracking_and_cleans_legacy_entries(self):
        emp_sudo = self.employee.sudo()
        # Simulate historical messages already stored in production-like DBs.
        role_msg = emp_sudo.message_post(
            body=Markup('<p>{"before": {"user": %d, "groups": [1], "implied_groups": [1, 2]}, "after": {"user": %d, "groups": [1]}}</p>')
            % (self.staff.id, self.staff.id),
            message_type='notification',
            subtype_xmlid='mail.mt_note',
        )
        transfer_msg = emp_sudo.message_post(
            body=Markup('<p>%s</p>') % json.dumps({
                'action': 'department_transfer',
                'actor': self.hr_user.id,
                'reason': 'Dieu dong du an',
                'preview': 'PHÒNG BAN: Phòng A → Kế hoạch Kinh doanh.\nTHU HỒI: quyền cũ.',
                'before': {'department': self.department.id},
                'after': {'department': self.department.id},
            }, ensure_ascii=False),
            message_type='notification',
            subtype_xmlid='mail.mt_note',
        )
        tracking_msg = emp_sudo.message_post(
            body=Markup(
                '<b>As of Nov 11, 2026</b>'
                '<div>Invited → <b>Confirmed</b> <i>(User Status)</i><br/>'
                'None → <b>Female</b> <i>(Sex)</i><br/>'
                'Trưởng phòng → <b>Nhân viên</b> <i>(Job)</i></div>',
            ),
            message_type='tracking',
            subtype_xmlid='mail.mt_note',
        )
        onboarding_msg = emp_sudo.message_post(
            body=Markup('<span><b>Congratulations!</b> May I recommend you to setup an onboarding plan?</span>'),
            message_type='notification',
            subtype_xmlid='mail.mt_note',
        )

        # HR Chatter serializer hides raw JSON and localizes English fragments without mutating DB rows.
        self.assertNotIn('"implied_groups"', str(role_msg._tp_hr_display_body()))
        self.assertIn('nhật ký kiểm toán', str(role_msg._tp_hr_display_body()))
        self.assertIn('Chuyển phòng ban:', str(transfer_msg._tp_hr_display_body()))
        self.assertNotIn('"department_transfer"', str(transfer_msg._tp_hr_display_body()))
        formatted_tracking = str(tracking_msg._tp_hr_display_body())
        self.assertIn('Có hiệu lực từ 11 thg 11, 2026', formatted_tracking)
        self.assertIn('Đã gửi lời mời →', formatted_tracking)
        self.assertIn('(Trạng thái tài khoản)', formatted_tracking)
        self.assertIn('(Giới tính)', formatted_tracking)
        self.assertIn('(Chức vụ)', formatted_tracking)
        self.assertNotIn('Congratulations!', str(onboarding_msg._tp_hr_display_body()))

        # Self-service My Profile history filters out redundant JSON role snapshots & HR onboarding banners.
        profile = self._staff_users().tp_get_my_profile()
        history = profile['history']
        history_ids = {item['id'] for item in history}
        self.assertNotIn(role_msg.id, history_ids)
        self.assertNotIn(onboarding_msg.id, history_ids)

        transfer_item = next(item for item in history if item['id'] == transfer_msg.id)
        self.assertEqual(transfer_item['category'], 'transfer')
        self.assertNotIn('{', transfer_item['body'])
        self.assertIn('Kế hoạch Kinh doanh', transfer_item['body'])

        tracking_item = next(item for item in history if item['id'] == tracking_msg.id)
        self.assertEqual(tracking_item['effective_date'], '11 thg 11, 2026')
        self.assertEqual(
            tracking_item['changes'],
            [
                {'field': 'Trạng thái tài khoản', 'old_value': 'Đã gửi lời mời', 'new_value': 'Đã kích hoạt'},
                {'field': 'Giới tính', 'old_value': 'Chưa thiết lập', 'new_value': 'Nữ'},
                {'field': 'Chức vụ', 'old_value': 'Trưởng phòng', 'new_value': 'Nhân viên'},
            ],
        )

        # Department transfer wizard posts readable Vietnamese business text and stores JSON in audit table only.
        other_dept = self.env['hr.department'].with_company(self.company).create({
            'name': 'Phòng Đích Test',
            'company_id': self.company.id,
        })
        wiz = self.env['tp.hr.role.wizard'].with_user(self.env.ref('base.user_admin')).with_company(self.company).create({
            'employee_id': self.employee.id,
            'change_kind': 'transfer',
            'target_department_id': other_dept.id,
            'reason': 'Dieu chuyen test',
        })
        wiz.action_preview()
        wiz.action_apply()
        latest_transfer_msg = self.env['mail.message'].sudo().search(
            [('model', '=', 'hr.employee'), ('res_id', '=', self.employee.id), ('message_type', '=', 'notification')],
            order='id desc', limit=1,
        )
        self.assertIn('Chuyển phòng ban:', latest_transfer_msg.body)
        self.assertNotIn('"department_transfer"', latest_transfer_msg.body)
        audit = self.env['tp.hr.employee.audit'].sudo().search(
            [('action', '=', 'department_transfer'), ('employee_ref', '=', self.employee.id)],
            limit=1,
        )
        self.assertTrue(audit)
