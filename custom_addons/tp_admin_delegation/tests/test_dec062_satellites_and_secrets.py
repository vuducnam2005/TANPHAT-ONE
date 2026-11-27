"""Regression tests for DEC-062 HR satellite model isolation (F-A07-0003),
ENTI config parameter secret protection (F-A07-0005), and UI XML layout fixes
(F-A03-0002, F-A03-0013).
"""
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from lxml import etree

from odoo import Command, fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged

from .test_delegation import DelegationCase, pick_free_employee_codes


@tagged('post_install', '-at_install', 'tp_admin_account_policy')
class TestDec062SatellitesAndSecrets(DelegationCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create dedicated Original Admin target following tp_hr_workspace's mandatory order:
        # 1) Create hr.employee first (without user_id), 2) Provision account via tp.hr.account.wizard,
        # 3) Grant Original Admin + System groups via existing Original Admin.
        orig_code = pick_free_employee_codes(cls.env, 1)[0]
        cls.original_employee = cls.env['hr.employee'].with_user(cls.admin).create({
            'name': 'Synthetic Protected Original Admin',
            'company_id': cls.company.id,
            'department_id': cls.departments[2].id,
            'tp_employee_code': orig_code,
            'date_version': fields.Date.today(),
        })
        wizard = cls.env['tp.hr.account.wizard'].with_user(cls.admin).create({
            'employee_id': cls.original_employee.id,
            'expected_user_id': False,
            'new_user_login': 'synthetic.protected.original.admin',
        })
        with patch.object(type(wizard), '_require_recent_identity', return_value=None):
            wizard.action_create_user(
                password='Synthetic-Orig-Pass-2026!',
                confirmation='Synthetic-Orig-Pass-2026!',
            )
        cls.original_target_user = cls.original_employee.user_id
        orig_group = cls.env.ref('tp_admin_delegation.group_original_admin')
        sys_group = cls.env.ref('base.group_system')
        hr_mgr_group = cls.env.ref('hr.group_hr_manager')
        cls.admin.write({'group_ids': [Command.link(hr_mgr_group.id)]})
        cls.original_target_user.with_user(cls.admin).write({
            'group_ids': [Command.link(orig_group.id), Command.link(sys_group.id), Command.link(hr_mgr_group.id)],
        })

        # Shared skill & resume catalog fixtures (Odoo 20 hr.skill.type requires inline skill_ids & skill_level_ids).
        cls.resume_type = cls.env['hr.resume.line.type'].with_user(cls.admin).create({
            'name': 'Synthetic Experience Type',
        })
        cls.skill_type = cls.env['hr.skill.type'].with_user(cls.admin).create({
            'name': 'Synthetic Skill Type',
            'skill_ids': [
                Command.create({'name': 'Synthetic Bridge Engineering'}),
                Command.create({'name': 'Synthetic Road Survey'}),
            ],
            'skill_level_ids': [
                Command.create({'name': 'Synthetic Senior', 'level_progress': 85, 'default_level': True}),
                Command.create({'name': 'Synthetic Expert', 'level_progress': 95}),
            ],
        })
        cls.skill, cls.skill_alt = cls.skill_type.skill_ids[0], cls.skill_type.skill_ids[1]
        cls.skill_level = cls.skill_type.skill_level_ids[0]

    def setUp(self):
        super().setUp()
        self.grant(self.users[0])
        self.grant(self.users[1])
        self.actor_user, self.peer, self.normal = self.users
        self.own_employee, self.peer_employee, self.normal_employee = self.employees
        self.assertTrue(self.original_target_user._tp_is_original_admin())

    def _assert_denied(self, callback):
        with self.assertRaises((AccessError, UserError, ValidationError)), self.env.cr.savepoint():
            callback()

    def _seed_target_satellites(self, employee, partner, suffix_digit):
        bank = self.env['res.partner.bank'].with_user(self.admin).create({
            'account_number': f'998877{employee.id:04d}{suffix_digit}',
            'partner_id': partner.id,
        })
        employee.with_user(self.admin).write({'bank_account_ids': [Command.link(bank.id)]})
        contract = self.env['tp.hr.contract.document'].with_user(self.admin).create({
            'name': f'Synthetic Contract {suffix_digit}',
            'number': f'HD-{employee.id}-{suffix_digit}',
            'employee_id': employee.id,
            'kind': 'labor',
        })
        resume = self.env['hr.resume.line'].with_user(self.admin).create({
            'employee_id': employee.id,
            'name': f'Synthetic Resume {suffix_digit}',
            'line_type_id': self.resume_type.id,
            'date_start': fields.Date.today(),
        })
        skill_rec = self.env['hr.employee.skill'].with_user(self.admin).create({
            'employee_id': employee.id,
            'skill_type_id': self.skill_type.id,
            'skill_id': self.skill.id,
            'skill_level_id': self.skill_level.id,
        })
        return bank, contract, resume, skill_rec

    def test_dec062_blocks_peer_and_original_satellites_including_locked_and_sudo(self):
        orig_partner = self.original_employee.work_contact_id
        orig_records = self._seed_target_satellites(self.original_employee, orig_partner, '1')
        peer_records = self._seed_target_satellites(
            self.peer_employee, self.peer_employee.work_contact_id, '2',
        )
        normal_bank, normal_contract, normal_resume, normal_skill = self._seed_target_satellites(
            self.normal_employee, self.normal_employee.work_contact_id, '3',
        )

        targets = [
            ('original', self.original_employee, orig_partner, orig_records, False),
            ('peer_active', self.peer_employee, self.peer_employee.work_contact_id, peer_records, False),
            ('peer_locked', self.peer_employee, self.peer_employee.work_contact_id, peer_records, True),
        ]

        for label, target_emp, target_partner, (bank, contract, resume, skill_rec), lock_peer in targets:
            if lock_peer:
                self.peer.with_user(self.admin)._tp_set_account_lock(True, 'Synthetic DEC-062 locked peer')
            for use_sudo in (False, True):
                def env_for(model_name):
                    m = self.env[model_name].with_user(self.actor_user).with_context(active_test=False)
                    return m.sudo() if use_sudo else m

                with self.subTest(target=label, sudo=use_sudo):
                    # 1. res.partner.bank: create, default_partner_id, write, relink, unlink, M2M link
                    self._assert_denied(lambda: env_for('res.partner.bank').create({
                        'account_number': f'111222{target_emp.id:04d}{int(use_sudo)}',
                        'partner_id': target_partner.id,
                    }))
                    self._assert_denied(lambda: env_for('res.partner.bank').with_context(
                        default_partner_id=target_partner.id,
                    ).create({'account_number': f'333444{target_emp.id:04d}{int(use_sudo)}'}))
                    self._assert_denied(lambda: env_for('res.partner.bank').browse(bank.id).write({
                        'holder_name': 'FORBIDDEN HOLDER',
                    }))
                    self._assert_denied(lambda: env_for('res.partner.bank').browse(bank.id).write({
                        'partner_id': self.normal_employee.work_contact_id.id,
                    }))
                    self._assert_denied(lambda: env_for('res.partner.bank').browse(normal_bank.id).write({
                        'partner_id': target_partner.id,
                    }))
                    self._assert_denied(lambda: env_for('res.partner.bank').browse(bank.id).unlink())
                    self._assert_denied(lambda: env_for('hr.employee').browse(self.normal_employee.id).write({
                        'bank_account_ids': [Command.link(bank.id)],
                    }))

                    # 2. tp.hr.contract.document: create, default_employee_id, write, relink, unlink
                    self._assert_denied(lambda: env_for('tp.hr.contract.document').create({
                        'name': 'Forbidden Contract',
                        'employee_id': target_emp.id,
                        'kind': 'labor',
                    }))
                    self._assert_denied(lambda: env_for('tp.hr.contract.document').with_context(
                        default_employee_id=target_emp.id,
                    ).create({'name': 'Forbidden Default Contract', 'kind': 'labor'}))
                    self._assert_denied(lambda: env_for('tp.hr.contract.document').browse(contract.id).write({
                        'note': 'Forbidden contract mutation',
                    }))
                    self._assert_denied(lambda: env_for('tp.hr.contract.document').browse(normal_contract.id).write({
                        'employee_id': target_emp.id,
                    }))
                    self._assert_denied(lambda: env_for('tp.hr.contract.document').browse(contract.id).unlink())

                    # 3. hr.resume.line: create, default_employee_id, write, relink, unlink
                    self._assert_denied(lambda: env_for('hr.resume.line').create({
                        'employee_id': target_emp.id,
                        'name': 'Forbidden Resume',
                        'line_type_id': self.resume_type.id,
                        'date_start': fields.Date.today(),
                    }))
                    self._assert_denied(lambda: env_for('hr.resume.line').with_context(
                        default_employee_id=target_emp.id,
                    ).create({'name': 'Forbidden Default Resume', 'date_start': fields.Date.today()}))
                    self._assert_denied(lambda: env_for('hr.resume.line').browse(resume.id).write({
                        'name': 'Tampered Resume',
                    }))
                    self._assert_denied(lambda: env_for('hr.resume.line').browse(normal_resume.id).write({
                        'employee_id': target_emp.id,
                    }))
                    self._assert_denied(lambda: env_for('hr.resume.line').browse(resume.id).unlink())

                    # 4. hr.employee.skill: create, default_employee_id, write, relink, unlink
                    self._assert_denied(lambda: env_for('hr.employee.skill').create({
                        'employee_id': target_emp.id,
                        'skill_type_id': self.skill_type.id,
                        'skill_id': self.skill_alt.id,
                        'skill_level_id': self.skill_level.id,
                    }))
                    self._assert_denied(lambda: env_for('hr.employee.skill').browse(skill_rec.id).write({
                        'skill_id': self.skill_alt.id,
                    }))
                    self._assert_denied(lambda: env_for('hr.employee.skill').browse(normal_skill.id).write({
                        'employee_id': target_emp.id,
                    }))
                    self._assert_denied(lambda: env_for('hr.employee.skill').browse(skill_rec.id).unlink())

                    # 5. Atomic batch rollback: mixed (normal | protected) writes leave normal untouched
                    before_resume_name = normal_resume.name
                    self._assert_denied(lambda: (
                        env_for('hr.resume.line').browse([normal_resume.id, resume.id]).write({'name': 'Batch Tamper'})
                    ))
                    normal_resume.invalidate_recordset(['name'])
                    self.assertEqual(normal_resume.name, before_resume_name)

        self.peer.with_user(self.admin)._tp_set_account_lock(False, 'Restore peer after DEC-062 check')

    def test_dec062_allows_original_admin_normal_employee_and_legitimate_self_service(self):
        # 1. Original Admin manages Peer Granted Admin satellites freely
        # (Note: Odoo 20 grants only `cru` — never `d` — to non-superuser groups on `res.partner.bank`,
        # so UI/HR users archive via `active=False` while server-side `unlink()` runs under `.sudo()`,
        # where `ProtectedPartnerBank.unlink()` still enforces `account_actor_uid` DEC-062 boundaries.)
        peer_bank = self.env['res.partner.bank'].with_user(self.admin).create({
            'account_number': '555666777888',
            'partner_id': self.peer_employee.work_contact_id.id,
        })
        peer_bank.with_user(self.admin).write({'holder_name': 'ORIGINAL ADMIN UPDATED', 'active': False})
        peer_bank.with_user(self.admin).sudo().unlink()

        peer_doc = self.env['tp.hr.contract.document'].with_user(self.admin).create({
            'name': 'Original Managed Peer Contract',
            'employee_id': self.peer_employee.id,
            'kind': 'labor',
        })
        peer_doc.with_user(self.admin).write({'note': 'Reviewed by Original Admin'})

        # 2. Granted Admin manages Normal Employee across all 4 models
        norm_bank = self.env['res.partner.bank'].with_user(self.actor_user).create({
            'account_number': '123456789012',
            'partner_id': self.normal_employee.work_contact_id.id,
        })
        norm_bank.with_user(self.actor_user).write({'holder_name': 'NORMAL STAFF HOLDER', 'active': False})
        norm_bank.with_user(self.actor_user).sudo().unlink()

        norm_doc = self.env['tp.hr.contract.document'].with_user(self.actor_user).create({
            'name': 'Normal Staff Contract',
            'employee_id': self.normal_employee.id,
            'kind': 'labor',
        })
        norm_doc.with_user(self.actor_user).write({'note': 'Managed by Granted Admin'})

        norm_resume = self.env['hr.resume.line'].with_user(self.actor_user).create({
            'employee_id': self.normal_employee.id,
            'name': 'Normal Staff Experience',
            'line_type_id': self.resume_type.id,
            'date_start': fields.Date.today(),
        })
        norm_resume.with_user(self.actor_user).write({'name': 'Normal Staff Experience Updated'})

        norm_skill = self.env['hr.employee.skill'].with_user(self.actor_user).create({
            'employee_id': self.normal_employee.id,
            'skill_type_id': self.skill_type.id,
            'skill_id': self.skill.id,
            'skill_level_id': self.skill_level.id,
        })
        norm_skill.with_user(self.actor_user).write({'skill_id': self.skill_alt.id})

        # Granted Admin cannot hijack a normal employee's resume/skill/bank by relinking to self
        self._assert_denied(lambda: norm_resume.with_user(self.actor_user).write({
            'employee_id': self.own_employee.id,
        }))
        self._assert_denied(lambda: norm_skill.with_user(self.actor_user).write({
            'employee_id': self.own_employee.id,
        }))
        norm_resume.with_user(self.actor_user).unlink()
        norm_skill.with_user(self.actor_user).unlink()

        # 3. Granted Admin CAN self-edit own personal resume, skill, and bank, but NOT own HR contract document
        svc = self.env['res.users'].with_user(self.actor_user)
        profile = svc.tp_save_my_resume_line(False, {
            'name': 'Own Self-Service Project Lead',
            'line_type_id': self.resume_type.id,
            'date_start': str(fields.Date.today()),
            'description': 'Self-service resume entry',
        })
        own_line_ids = [row['id'] for row in profile['resume']['lines']]
        self.assertTrue(own_line_ids)
        svc.tp_delete_my_resume_line(own_line_ids[0])

        profile = svc.tp_save_my_skill(False, {
            'skill_type_id': self.skill_type.id,
            'skill_id': self.skill.id,
            'skill_level_id': self.skill_level.id,
        })
        own_skill_ids = [row['id'] for row in profile['resume']['skills']]
        self.assertTrue(own_skill_ids)
        svc.tp_delete_my_skill(own_skill_ids[0])

        if 'tp.bank' in self.env:
            vcb = self.env.ref('tp_hr_bank.tp_bank_vcb')
            profile = svc.tp_save_my_bank_account(False, {
                'bank_id': vcb.id,
                'account_number': '666777888999',
                'holder_name': 'GRANTED ADMIN SELF',
            })
            own_bank_ids = [row['id'] for row in profile['bank']['accounts']]
            self.assertTrue(own_bank_ids)
            svc.tp_remove_my_bank_account(own_bank_ids[0])
        else:
            own_bank = self.env['res.partner.bank'].with_user(self.actor_user).create({
                'account_number': '666777888999',
                'partner_id': self.own_employee.work_contact_id.id,
            })
            own_bank.with_user(self.actor_user).write({'holder_name': 'GRANTED ADMIN SELF', 'active': False})
            own_bank.with_user(self.actor_user).sudo().unlink()

        self._assert_denied(lambda: self.env['tp.hr.contract.document'].with_user(self.actor_user).create({
            'name': 'Forbidden Self Contract',
            'employee_id': self.own_employee.id,
            'kind': 'labor',
        }))

    def test_enti_config_parameter_protected_for_granted_admin_but_allowed_for_backend_sudo_and_original(self):
        secret_value = 'Synthetic-Enti-Secret-2026!'
        ParamAdmin = self.env['ir.config_parameter'].with_user(self.admin)
        ParamAdmin.set_str('tp_hr_attendance.enti_phone', '0900111222')
        ParamAdmin.set_str('tp_hr_attendance.enti_password', secret_value)
        ParamAdmin.set_str('tp_hr_attendance.enti_app_key', 'synth-app-key-99')
        ParamAdmin.set_str('tp_hr_attendance.enti_token', 'synth-token-99')
        ParamAdmin.set_str('tp_hr_attendance.enti_secret', 'synth-secret-99')
        pw_rec = ParamAdmin.search([('key', '=', 'tp_hr_attendance.enti_password')], limit=1)
        app_rec = ParamAdmin.search([('key', '=', 'tp_hr_attendance.enti_app_key')], limit=1)
        tok_rec = ParamAdmin.search([('key', '=', 'tp_hr_attendance.enti_token')], limit=1)
        self.assertTrue(pw_rec and app_rec and tok_rec)

        fake_http_req = SimpleNamespace(session=SimpleNamespace(uid=self.actor_user.id))
        with patch('odoo.addons.tp_admin_delegation.models.guards.request', fake_http_req):
            ParamGranted = self.env['ir.config_parameter'].with_user(self.actor_user)

            # Direct ORM / HTTP RPC reads by Granted Admin must NOT expose any ENTI secret keys
            for secret_key in (
                'tp_hr_attendance.enti_password',
                'tp_hr_attendance.enti_app_key',
                'tp_hr_attendance.enti_token',
                'tp_hr_attendance.enti_secret',
            ):
                self.assertEqual(
                    ParamGranted.search_read([('key', '=', secret_key)], ['key', 'value']),
                    [],
                )
                with self.assertRaises(AccessError), self.env.cr.savepoint():
                    ParamGranted.get_str(secret_key)
                with self.assertRaises(AccessError), self.env.cr.savepoint():
                    ParamGranted.get_param(secret_key)

            self.assertEqual(
                ParamGranted.search_count([('value', 'ilike', 'Synthetic-Enti-Secret')]),
                0,
            )
            with self.assertRaises(AccessError), self.env.cr.savepoint():
                ParamGranted.browse(pw_rec.id).read(['key', 'value'])
            with self.assertRaises(AccessError), self.env.cr.savepoint():
                ParamGranted.browse(pw_rec.id).export_data(['value'])
            # Direct HTTP RPC unlink (`env.su=False`) is still strictly forbidden!
            with self.assertRaises(AccessError), self.env.cr.savepoint():
                ParamGranted.browse(pw_rec.id).unlink()
            with self.assertRaises(AccessError), self.env.cr.savepoint():
                ParamGranted.browse(app_rec.id).unlink()

            # Granted Admin cannot create or overwrite secret ENTI parameters (even via sudo)
            for writer in (ParamGranted, ParamGranted.sudo()):
                for secret_key in (
                    'tp_hr_attendance.enti_password',
                    'tp_hr_attendance.enti_app_key',
                    'tp_hr_attendance.enti_token',
                    'tp_hr_attendance.enti_secret',
                ):
                    with self.assertRaises(AccessError), self.env.cr.savepoint():
                        writer.set_str(secret_key, 'Tampered!')
                with self.assertRaises(AccessError), self.env.cr.savepoint():
                    writer.browse(pw_rec.id).write({'value': 'Tampered!'})
                with self.assertRaises(AccessError), self.env.cr.savepoint():
                    writer.browse(tok_rec.id).unlink()

            # Non-secret ENTI config/sync metadata (`enti_phone`, `enti_base_url`, `enti_last_*`)
            # MUST work under backend `.sudo()` (`env.su=True`) for HR Manager / Granted Admin!
            ParamGranted.sudo().set_str('tp_hr_attendance.enti_phone', '0988777666')
            ParamGranted.sudo().set_str('tp_hr_attendance.enti_base_url', 'https://enti.vn')
            ParamGranted.sudo().set_str('tp_hr_attendance.enti_last_sync_at', '2026-11-27T23:30:00')
            self.assertEqual(ParamGranted.get_str('tp_hr_attendance.enti_phone'), '0988777666')

            # Backend cron / sync helper reading under `.sudo()` MUST continue working seamlessly!
            self.assertEqual(
                ParamGranted.sudo().get_str('tp_hr_attendance.enti_password'),
                secret_value,
            )
            self.assertEqual(
                ParamGranted.sudo().get_param('tp_hr_attendance.enti_password'),
                secret_value,
            )

            # Backend `.sudo()` (`env.su=True`) IS allowed to purge legacy plaintext `enti_password`
            # and `enti_app_key` when saving credentials to `.local/enti_secrets.json` (F-A04-0003)!
            ParamGranted.sudo().search([
                ('key', 'in', ['tp_hr_attendance.enti_password', 'tp_hr_attendance.enti_app_key']),
            ]).unlink()
            self.assertFalse(
                ParamAdmin.search_count([
                    ('key', 'in', ['tp_hr_attendance.enti_password', 'tp_hr_attendance.enti_app_key']),
                ]),
            )

        # Original Admin retains full read/write capability
        ParamAdmin.set_str('tp_hr_attendance.enti_password', secret_value)
        orig_req = SimpleNamespace(session=SimpleNamespace(uid=self.admin.id))
        with patch('odoo.addons.tp_admin_delegation.models.guards.request', orig_req):
            self.assertEqual(ParamAdmin.get_str('tp_hr_attendance.enti_password'), secret_value)
            rows = ParamAdmin.search_read([('key', '=', 'tp_hr_attendance.enti_password')], ['key', 'value'])
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['value'], secret_value)

    def test_account_wizard_row_icon_and_my_profile_card_padding_xml(self):
        # F-A03-0002: 3-column grid row (icon + label + field) on tp.hr.account.wizard
        wizard_view = self.env['tp.hr.account.wizard'].get_view(view_type='form')
        arch = etree.fromstring(wizard_view['arch'])
        kind_rows = arch.xpath("//div[contains(@class, 'o_tp_hr_account_row')][field[@name='account_kind']]")
        self.assertEqual(len(kind_rows), 1)
        children = list(kind_rows[0])
        self.assertGreaterEqual(len(children), 3)
        self.assertEqual(children[0].tag, 'i')
        self.assertEqual(children[0].get('data-icon'), 'verified_user')
        self.assertEqual(children[1].tag, 'label')
        self.assertEqual(children[2].get('name'), 'account_kind')

        # F-A03-0013: p-3 wrapper inside MyProfile admin card
        qweb_path = Path(__file__).resolve().parents[1] / 'static' / 'src' / 'my_profile.xml'
        qweb = etree.fromstring(qweb_path.read_bytes())
        wrappers = qweb.xpath("//section[contains(@class, 'o_tp_hr_card')]/div[@class='p-3']")
        self.assertEqual(len(wrappers), 1)
        self.assertTrue(wrappers[0].xpath("./span[contains(@class, 'badge')]"))
        self.assertTrue(wrappers[0].xpath("./p"))
