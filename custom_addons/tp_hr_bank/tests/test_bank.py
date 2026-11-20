"""BANK-001 on synthetic data only: bank catalogue and self-service bank accounts."""
import json
import os
import shutil
import subprocess
from pathlib import Path

from odoo import Command
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import HttpCase, tagged

from odoo.addons.tp_hr_bank.models.tp_bank import text_color_for

STAFF_PASSWORD = 'bank.test.staff.pw'
OTHER_PASSWORD = 'bank.test.other.pw'
LONE_PASSWORD = 'bank.test.lone.pw'


@tagged('post_install', '-at_install')
class TestTpHrBank(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env['res.company'].create({'name': 'Synthetic Bank Co'})
        cls.env.ref('base.user_admin').write({'company_ids': [Command.link(cls.company.id)]})
        user_group = cls.env.ref('base.group_user')

        def make_user(name, login, password, groups=user_group):
            return cls.env['res.users'].create({
                'name': name, 'login': login, 'password': password,
                'company_id': cls.company.id, 'company_ids': [Command.set(cls.company.ids)],
                'group_ids': [Command.set(groups.ids)],
            })

        cls.staff = make_user('Synthetic Bank Staff', 'bank.test.staff', STAFF_PASSWORD)
        cls.other = make_user('Synthetic Bank Other', 'bank.test.other', OTHER_PASSWORD)
        cls.lone = make_user('Synthetic Lone Account', 'bank.test.lone', LONE_PASSWORD)
        cls.hr_user = make_user('Synthetic Bank HR', 'bank.test.hr', 'bank.test.hr.pw', cls.env.ref('hr.group_hr_user'))
        Employee = cls.env['hr.employee'].with_company(cls.company)
        cls.staff_employee = Employee.create({'name': 'Đặng Thị Synthetic', 'user_id': cls.staff.id, 'company_id': cls.company.id})
        cls.other_employee = Employee.create({'name': 'Other Synthetic', 'user_id': cls.other.id, 'company_id': cls.company.id})
        cls.vcb = cls.env.ref('tp_hr_bank.tp_bank_vcb')
        cls.bidv = cls.env.ref('tp_hr_bank.tp_bank_bidv')
        cls.momo = cls.env.ref('tp_hr_bank.tp_bank_momo')

    # ------------------------------------------------------------------ helpers
    def as_user(self, records, user):
        # Only the synthetic company: the test env's own company list would hide the real check.
        return records.with_user(user).with_context(allowed_company_ids=self.company.ids)

    def call(self, user, method, *args):
        return getattr(self.as_user(self.env['res.users'], user), method)(*args)

    def rpc(self, method, *args):
        self.env.flush_all()
        response = self.url_open(f'/web/dataset/call_kw/res.users/{method}', json={
            'jsonrpc': '2.0', 'method': 'call', 'id': 1,
            'params': {'model': 'res.users', 'method': method, 'args': list(args),
                       'kwargs': {'context': {'allowed_company_ids': [self.company.id]}}},
        })
        self.assertEqual(response.status_code, 200)
        self.env.invalidate_all()
        return response.json()

    def rpc_ok(self, method, *args):
        result = self.rpc(method, *args)
        self.assertNotIn('error', result, result.get('error'))
        return result['result']

    def notes(self, employee):
        return self.env['mail.message'].sudo().search([
            ('model', '=', 'hr.employee'), ('res_id', '=', employee.id), ('body', 'ilike', 'tài khoản ngân hàng'),
        ])

    # ------------------------------------------------------------------ catalogue
    def test_catalogue_is_the_napas_list(self):
        Bank = self.env['tp.bank'].with_context(active_test=False)
        banks = Bank.search([])
        self.assertEqual(len(banks), 76)
        self.assertEqual(len(set(banks.mapped('bin'))), 76)
        self.assertEqual((self.vcb.bin, self.vcb.short_name, self.vcb.code), ('970436', 'Vietcombank', 'VCB'))
        self.assertFalse(self.momo.active)
        self.assertEqual(self.momo.kind, 'wallet')
        catalog = self.env['tp.bank'].with_user(self.staff).tp_bank_catalog()
        self.assertEqual(catalog[0]['short_name'], 'VietinBank')
        self.assertNotIn(self.momo.id, [bank['id'] for bank in catalog])
        self.assertTrue(all(bank['badge'] and len(bank['badge']) <= 5 for bank in catalog))
        # Readable badge text on light and dark brand colours.
        self.assertEqual(text_color_for('#FFB300'), '#111827')
        self.assertEqual(text_color_for('#007B40'), '#FFFFFF')
        with self.assertRaises(AccessError):
            self.as_user(self.vcb, self.staff).write({'color': '#000000'})

    # ------------------------------------------------------------------ self service over HTTP
    def test_employee_adds_updates_and_removes_own_account(self):
        self.authenticate(self.staff.login, STAFF_PASSWORD)
        profile = self.rpc_ok('tp_get_my_profile')
        self.assertTrue(profile['has_employee'])
        self.assertTrue(profile['bank']['available'])
        self.assertEqual(profile['bank']['accounts'], [])
        self.assertEqual(profile['bank']['default_holder'], 'DANG THI SYNTHETIC')

        profile = self.rpc_ok('tp_save_my_bank_account', False, {
            'bank_id': self.vcb.id, 'account_number': '0123 456.789', 'holder_name': 'Đặng  thị synthetic',
        })
        [card] = profile['bank']['accounts']
        self.assertEqual((card['account_number'], card['holder_name'], card['trusted']), ('0123456789', 'DANG THI SYNTHETIC', False))
        self.assertEqual(card['bank']['short_name'], 'Vietcombank')
        account = self.env['res.partner.bank'].browse(card['id'])
        self.assertEqual(account.partner_id, self.staff_employee.work_contact_id)
        self.assertEqual(self.staff_employee.bank_account_ids, account)
        self.assertEqual((account.bank_name, account.bank_bic), ('Vietcombank', '970436'))

        account.allow_out_payment = True  # HR verifies
        profile = self.rpc_ok('tp_save_my_bank_account', account.id, {
            'bank_id': self.vcb.id, 'account_number': '0123456789', 'holder_name': 'DANG THI SYNTHETIC A',
        })
        self.assertTrue(account.allow_out_payment, 'holder name only: stays verified')
        self.rpc_ok('tp_save_my_bank_account', account.id, {
            'bank_id': self.bidv.id, 'account_number': '0123456789', 'holder_name': 'DANG THI SYNTHETIC A',
        })
        self.assertFalse(account.allow_out_payment, 'bank changed: HR verifies again')
        self.assertEqual((account.bank_name, account.bank_bic), ('BIDV', '970418'))

        bodies = ' '.join(self.notes(self.staff_employee).mapped('body'))
        self.assertIn('••••6789', bodies)
        self.assertNotIn('0123456789', bodies)

        profile = self.rpc_ok('tp_remove_my_bank_account', account.id)
        self.assertEqual(profile['bank']['accounts'], [])
        self.assertFalse(self.staff_employee.bank_account_ids)
        self.assertTrue(account.exists())
        self.assertFalse(account.active)

        profile = self.rpc_ok('tp_save_my_bank_account', False, {
            'bank_id': self.vcb.id, 'account_number': '0123456789', 'holder_name': '',
        })
        self.assertEqual(profile['bank']['accounts'][0]['id'], account.id, 'same number reuses the archived record')
        self.assertTrue(account.active)
        self.assertFalse(account.allow_out_payment)
        self.assertEqual(self.staff_employee.bank_account_ids, account)

    def test_account_without_employee_profile(self):
        self.authenticate(self.lone.login, LONE_PASSWORD)
        profile = self.rpc_ok('tp_get_my_profile')
        self.assertFalse(profile['has_employee'])
        self.assertEqual(profile['bank']['owner'], 'user')
        profile = self.rpc_ok('tp_save_my_bank_account', False, {
            'bank_id': self.vcb.id, 'account_number': '99887766', 'holder_name': 'Synthetic Lone',
        })
        [card] = profile['bank']['accounts']
        account = self.env['res.partner.bank'].browse(card['id'])
        self.assertEqual(account.partner_id, self.lone.partner_id)
        self.rpc_ok('tp_remove_my_bank_account', account.id)
        self.assertFalse(account.active)

    def test_other_people_accounts_are_refused(self):
        self.call(self.other, 'tp_save_my_bank_account', False, {
            'bank_id': self.vcb.id, 'account_number': '55556666', 'holder_name': 'OTHER SYNTHETIC',
        })
        foreign = self.other_employee.bank_account_ids
        self.assertTrue(foreign)
        self.authenticate(self.staff.login, STAFF_PASSWORD)
        for method, args in (
            ('tp_save_my_bank_account', (foreign.id, {'bank_id': self.vcb.id, 'account_number': '11112222', 'holder_name': 'X Y'})),
            ('tp_remove_my_bank_account', (foreign.id,)),
        ):
            denied = self.rpc(method, *args)
            self.assertIn('AccessError', denied['error']['data']['name'])
        forged = self.rpc('tp_save_my_bank_account', False, {
            'bank_id': self.vcb.id, 'account_number': '11112222', 'holder_name': 'X Y', 'allow_out_payment': True,
        })
        self.assertIn('AccessError', forged['error']['data']['name'])
        self.assertEqual(foreign.account_number, '55556666')
        self.assertTrue(foreign.active)
        self.assertFalse(self.staff_employee.bank_account_ids)

    # ------------------------------------------------------------------ validation and access
    def test_validation_rules(self):
        def save(vals, account_id=False):
            base = {'bank_id': self.vcb.id, 'account_number': '12345678', 'holder_name': 'SYNTHETIC'}
            return self.call(self.staff, 'tp_save_my_bank_account', account_id, dict(base, **vals))

        for vals in ({'bank_id': False}, {'bank_id': self.momo.id}, {'bank_id': 999999}, {'bank_id': True},
                     {'account_number': ''}, {'account_number': '12345'}, {'account_number': '12AB5678'},
                     {'account_number': '1' * 21}, {'holder_name': 'NGUYEN 123'}, {'holder_name': 'A' * 121}):
            with self.subTest(vals=vals), self.assertRaises(ValidationError):
                save(vals)
        with self.assertRaises(ValidationError):
            self.call(self.staff, 'tp_save_my_bank_account', False, 'not a dict')
        save({})
        with self.assertRaises(ValidationError):
            save({'account_number': '1234-5678'})  # same number, different spelling
        for index in range(4):
            save({'account_number': f'2000000{index}'})
        with self.assertRaises(ValidationError):
            save({'account_number': '30000000'})
        self.assertEqual(len(self.staff_employee.bank_account_ids), 5)

    def test_access_rules_on_bank_accounts(self):
        self.call(self.staff, 'tp_save_my_bank_account', False, {
            'bank_id': self.vcb.id, 'account_number': '12345678', 'holder_name': 'SYNTHETIC',
        })
        self.call(self.other, 'tp_save_my_bank_account', False, {
            'bank_id': self.vcb.id, 'account_number': '87654321', 'holder_name': 'OTHER',
        })
        own = self.staff_employee.bank_account_ids
        foreign = self.other_employee.bank_account_ids
        self.as_user(own, self.staff).check_access('read')
        with self.assertRaises(AccessError):
            self.as_user(foreign, self.staff).check_access('read')
        with self.assertRaises(AccessError):
            self.as_user(own, self.staff).write({'account_number': '99999999'})
        with self.assertRaises(UserError):  # base: only trusted roles may verify accounts
            self.as_user(own, self.staff).write({'allow_out_payment': True})
        self.as_user(own | foreign, self.hr_user).check_access('read')
        # The profile guard still refuses other HR fields on the user's own employee, even via sudo.
        with self.assertRaises(AccessError):
            self.as_user(self.staff_employee, self.staff).sudo().write({'barcode': 'SYN-BANK-001'})
        self.assertIn('bank_account_ids', self.env['hr.employee']._tp_self_service_fields())
        self.assertNotIn('barcode', self.env['hr.employee']._tp_self_service_fields())

    def test_web_styles_compile(self):
        """A SCSS error here would put the whole database on the "style compilation failed" fallback."""
        bundle = self.env['ir.qweb']._get_asset_bundle('web.assets_web', css=True, js=False)
        bundle.preprocess_css()
        self.assertEqual(bundle.css_errors, [])

    def test_profile_bank_card_in_browser(self):
        """Card, badge, masked number and bank search render in "Hồ sơ của tôi" on desktop and mobile.

        Runs the project's Playwright runner (scripts/tests/test_hr_bank_profile.cjs); the browser only
        opens the modal and cancels, so nothing is saved from the UI.
        """
        holder = 'DANG THI SYNTHETIC'
        # Half-filled synthetic profile: the screen shows both real values and empty placeholders.
        self.staff_employee.write({
            'private_email': 'synthetic.staff@example.invalid', 'private_phone': '0900000000',
            'birthday': '1990-05-12', 'country_id': self.env.ref('base.vn').id, 'private_city': 'Synthetic City',
        })
        self.call(self.staff, 'tp_save_my_bank_account', False, {
            'bank_id': self.vcb.id, 'account_number': '0123456789', 'holder_name': holder,
        })
        root = Path(__file__).resolve().parents[3]
        while not (root / 'scripts/tests/test_hr_bank_profile.cjs').is_file():
            if root == root.parent:
                self.skipTest('Playwright runner scripts/tests/test_hr_bank_profile.cjs is not available')
            root = root.parent
        if not shutil.which('node') or not (root / 'frontend/node_modules/playwright').is_dir():
            self.skipTest('node or frontend/node_modules/playwright is not installed')
        output = root / '.local/hr-bank001/browser'
        output.mkdir(parents=True, exist_ok=True)
        fixture_path = output / 'fixture-private.json'
        self.authenticate(self.staff.login, STAFF_PASSWORD, session_extra={'context': {'lang': 'vi_VN'}})
        try:
            with self.allow_requests():
                fixture_path.write_text(json.dumps({
                    'base': self.base_url(), 'output': str(output), 'holderName': holder, 'cookies': [
                        {'name': 'session_id', 'value': self.session.sid, 'url': self.base_url(), 'httpOnly': True},
                        {'name': 'test_request_key', 'value': self.http_request_key, 'url': self.base_url()},
                    ],
                }), encoding='utf-8')
                result = subprocess.run(['node', str(root / 'scripts/tests/test_hr_bank_profile.cjs')],
                    env={**os.environ, 'TP_HR_BANK_FIXTURE': str(fixture_path)},
                    capture_output=True, text=True, encoding='utf-8', timeout=240, check=False)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        finally:
            fixture_path.unlink(missing_ok=True)
        # The UI cancelled the modal: still exactly the one account saved above.
        self.assertEqual(len(self.staff_employee.bank_account_ids), 1)

    def test_hr_form_syncs_bank_fields(self):
        Account = self.as_user(self.env['res.partner.bank'], self.hr_user)
        account = Account.create({
            'partner_id': self.other_employee.work_contact_id.id, 'account_number': '44445555', 'tp_bank_id': self.bidv.id,
        })
        self.assertEqual((account.bank_name, account.bank_bic), ('BIDV', '970418'))
        account.write({'tp_bank_id': self.vcb.id})
        self.assertEqual((account.bank_name, account.bank_bic), ('Vietcombank', '970436'))
        arch = Account.get_views([(False, 'form')])['views']['form']['arch']
        self.assertIn('tp_bank_picker', arch)
