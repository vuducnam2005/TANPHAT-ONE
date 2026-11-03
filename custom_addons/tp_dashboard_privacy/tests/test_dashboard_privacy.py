from werkzeug.exceptions import Forbidden

from odoo import Command
from odoo.exceptions import AccessError
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged('post_install', '-at_install')
class TestDashboardPrivacy(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.reader = new_test_user(cls.env, login='dashboard_reader', groups='base.group_user')
        cls.outside = new_test_user(cls.env, login='dashboard_outside', groups='base.group_user')
        group = cls.env['spreadsheet.dashboard.group'].create({'name': 'Internal fictional reports'})
        cls.dashboard = cls.env['spreadsheet.dashboard'].create({
            'name': 'Private fictional money', 'dashboard_group_id': group.id,
            'group_ids': [Command.clear()], 'allowed_user_ids': [Command.set([cls.reader.id])],
            'company_ids': [Command.set([cls.env.company.id])], 'tp_internal_only': True,
        })

    def test_authorized_read_but_no_public_snapshot(self):
        self.assertTrue(self.dashboard.with_user(self.reader).read(['name']))
        with self.assertRaises(AccessError), self.cr.savepoint():
            self.env['spreadsheet.dashboard.share'].with_user(self.reader).action_get_share_url({
                'dashboard_id': self.dashboard.id, 'name': 'Forbidden public copy',
            })

    def test_outsider_data_share_and_repoint_denied(self):
        with self.assertRaises(AccessError), self.cr.savepoint():
            self.dashboard.with_user(self.outside).read(['spreadsheet_data'])
        native = self.dashboard.copy({'tp_internal_only': False})
        share = self.env['spreadsheet.dashboard.share'].with_user(self.reader).create({'dashboard_id': native.id})
        with self.assertRaises(AccessError), self.cr.savepoint():
            share.write({'dashboard_id': self.dashboard.id})

    def test_existing_token_revoked_and_native_preserved(self):
        native = self.dashboard.copy({'tp_internal_only': False})
        share = self.env['spreadsheet.dashboard.share'].with_user(self.reader).create({'dashboard_id': native.id})
        share._check_dashboard_access(share.access_token)
        native.tp_internal_only = True
        with self.assertRaises(Forbidden):
            share._check_dashboard_access(share.access_token)
