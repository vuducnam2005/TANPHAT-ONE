# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
"""Automated tests for tp_enterprise_governance: True CPM, Weighted Progress, Baselines, Mandatory Cases #6, #10, #14, and 11 Separated Financial Metrics."""
import base64
from datetime import date, timedelta

from psycopg2 import IntegrityError

from odoo import Command, fields
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import HttpCase, TransactionCase, tagged
from odoo.tools import mute_logger


@tagged('post_install', '-at_install')
class TestEnterpriseGovernance(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        employee_model = cls.env['hr.employee']
        sequence = employee_model._tp_code_sequence()
        cls.env.cr.execute('SELECT last_value, is_called FROM ir_sequence_%03d' % sequence.id)
        cls.addClassCleanup(cls._restore_sequence, sequence.id, *cls.env.cr.fetchone())
        employee_model._tp_reset_code_sequence(employee_model._tp_code_floor())

        cls.company = cls.env.company
        cls.admin = cls.env.ref('base.user_admin')
        cls.env['tp.admin.delegation']._migrate_admin_full_001()

        cls.dept_bridge = cls.env['hr.department'].create({
            'name': 'Phòng Cầu Hầm (Gov Test)',
            'company_id': cls.company.id,
        })
        base_group = cls.env.ref('base.group_user')
        mgr_group = cls.env.ref('tp_core.group_manager')
        fin_group = cls.env.ref('tp_reporting.group_reporting_finance')

        cls.user_pm = cls._make_user('gov.pm', 'Chủ nhiệm Dự án Cầu (Gov)', [base_group.id, mgr_group.id])
        cls.user_fin = cls._make_user('gov.fin', 'Cán bộ Tài chính (Gov)', [base_group.id, fin_group.id])
        cls.user_outsider = cls._make_user('gov.out', 'Nhân viên Ngoài Dự Án (Gov)', [base_group.id])

        cls._make_employee(cls.user_pm, cls.dept_bridge)
        cls._make_employee(cls.user_fin, cls.dept_bridge)
        cls._make_employee(cls.user_outsider, cls.dept_bridge)

        cls.project = cls.env['project.project'].with_user(cls.user_pm).create({
            'name': 'Dự án Cầu dây văng Cửa Đại 2',
            'company_id': cls.company.id,
            'tp_managed': True,
            'tp_code': 'DA-GOV-2026-01',
            'tp_department_id': cls.dept_bridge.id,
        })
        cls.env['tp.project.assignment'].sudo().create({
            'project_id': cls.project.id,
            'user_id': cls.user_pm.id,
            'role': 'coordinator',
            'active': True,
        })

    @classmethod
    def _restore_sequence(cls, sequence_id, last_value, is_called):
        with cls.registry.cursor() as cr:
            cr.execute('SELECT setval(%s, %s, %s)', ['ir_sequence_%03d' % sequence_id, last_value, is_called])

    @classmethod
    def _make_user(cls, login, name, group_ids):
        return cls.env['res.users'].with_context(no_reset_password=True).create({
            'name': name,
            'login': login,
            'company_id': cls.company.id,
            'company_ids': [Command.set(cls.company.ids)],
            'group_ids': [Command.set(group_ids)],
        })

    @classmethod
    def _make_employee(cls, user, dept):
        return cls.env['hr.employee'].create({
            'name': user.name,
            'company_id': cls.company.id,
            'department_id': dept.id,
            'user_id': user.id,
            'date_version': fields.Date.today(),
        })

    def test_01_true_cpm_dag_cycle_weighted_progress_and_mandatory_case_06(self):
        """True CPM forward/backward pass + DAG cycle guard + weighted progress + Case #6 (Task Done != Volume Accepted)."""
        Task = self.env['project.task'].sudo()
        # Diamond DAG: A(10d) -> B(20d, weight=80) -> D(5d, weight=10) AND A(10d, weight=0) -> C(5d, weight=10) -> D(5d)
        t_a = Task.create({
            'project_id': self.project.id,
            'name': 'A. Khảo sát địa hình',
            'tp_wbs_code': '1.1',
            'tp_planned_duration_days': 10.0,
            'tp_weight_factor': 0.0,
        })
        t_b = Task.create({
            'project_id': self.project.id,
            'name': 'B. Thiết kế kết cấu nhịp chính',
            'tp_wbs_code': '1.2',
            'tp_planned_duration_days': 20.0,
            'tp_weight_factor': 80.0,
            'tp_predecessor_ids': [Command.set([t_a.id])],
        })
        t_c = Task.create({
            'project_id': self.project.id,
            'name': 'C. Thiết kế hệ thống chiếu sáng (nhánh phụ)',
            'tp_wbs_code': '1.3',
            'tp_planned_duration_days': 5.0,
            'tp_weight_factor': 10.0,
            'tp_predecessor_ids': [Command.set([t_a.id])],
        })
        t_d = Task.create({
            'project_id': self.project.id,
            'name': 'D. Thẩm tra & Tổng hợp hồ sơ',
            'tp_wbs_code': '1.4',
            'tp_planned_duration_days': 5.0,
            'tp_weight_factor': 10.0,
            'tp_predecessor_ids': [Command.set([t_b.id, t_c.id])],
        })

        # Cycle check: A depending on D must raise ValidationError!
        with self.assertRaises(ValidationError):
            t_a.write({'tp_predecessor_ids': [Command.set([t_d.id])]})

        cpm = self.project.with_user(self.user_pm).action_recompute_cpm()
        self.assertTrue(cpm['ready'])
        self.assertEqual(cpm['project_duration_days'], 35.0)
        self.assertTrue(t_a.tp_is_critical_path)
        self.assertTrue(t_b.tp_is_critical_path)
        self.assertFalse(t_c.tp_is_critical_path)
        self.assertEqual(t_c.tp_total_float_days, 15.0)
        self.assertTrue(t_d.tp_is_critical_path)

        # Mandatory Case #6: Completing C (weight 10, 100%) and 50% of B (weight 80) -> weighted progress = (50*80 + 100*10)/100 = 50%
        # AND completing C MUST NOT set tp_state_volume_accepted = True!
        t_c.action_update_wbs_progress(100.0)
        t_b.action_update_wbs_progress(50.0)
        self.project.invalidate_recordset(['tp_weighted_progress_pct'])
        self.assertEqual(self.project.tp_weighted_progress_pct, 50.0)
        self.assertTrue(t_c.tp_state_exec_reported)
        self.assertFalse(t_c.tp_state_volume_accepted)

        # Baseline freeze + mandatory milestone adjustment reason
        bl = self.project.with_user(self.user_pm).action_capture_baseline('Baseline ký HĐ', 'Chốt tiến độ gốc')
        self.assertEqual(bl['version'], 1)
        with self.assertRaises(UserError):
            self.project.with_user(self.user_pm).action_adjust_milestone(t_b.id, date.today() + timedelta(days=30), '  ')
        self.project.with_user(self.user_pm).action_adjust_milestone(
            t_b.id, date.today() + timedelta(days=30), 'Bổ sung mặt cắt địa chất trụ T4',
        )
        self.assertEqual(len(self.project.tp_milestone_log_ids), 1)

    def test_02_mandatory_cases_10_and_14_nas_folder_idempotency_and_dossier_acl(self):
        """Case #10: Signing 2nd contract never duplicates project NAS root; Case #14: Outsider blocked from dossier."""
        partner = self.env['res.partner'].create({'name': 'Ban QLDA Giao thông (Test)', 'company_id': self.company.id})
        c1 = self.env['tp.contract'].sudo().create({
            'code': 'HD-GOV-2026-01',
            'name': 'Hợp đồng Tư vấn Khảo sát & TKKT',
            'project_id': self.project.id,
            'partner_id': partner.id,
            'contract_type': 'owner',
        })
        c2 = self.env['tp.contract'].sudo().create({
            'code': 'HD-GOV-2026-02',
            'name': 'Hợp đồng Phụ lục TKBVTC',
            'project_id': self.project.id,
            'partner_id': partner.id,
            'contract_type': 'owner',
        })

        NasJob = self.env['tp.nas.folder.job'].with_user(self.user_pm)
        j1 = NasJob.tp_enqueue_project_nas_structure(self.project.id, c1.id)
        j2 = NasJob.tp_enqueue_project_nas_structure(self.project.id, c2.id)
        self.assertTrue(j1['created_new_root'])
        self.assertFalse(j2['created_new_root'])
        self.assertEqual(j1['job_id'], j2['job_id'])
        self.assertEqual(j2['root_folder_path'], 'PROJECTS/DA-GOV-2026-01')
        self.assertEqual(len(j2['contract_subfolders']), 2)
        self.assertEqual(
            self.env['tp.nas.folder.job'].sudo().search_count([('project_id', '=', self.project.id)]),
            1,
        )

        # Case #14: Dossier versioning & outsider access denial
        with self.assertRaises(AccessError):
            self.env['tp.project.dossier'].with_user(self.user_outsider).create({
                'project_id': self.project.id,
                'phase_stage': 'tkkt',
                'name': 'Hồ sơ trái phép',
            })

        dossier = self.env['tp.project.dossier'].with_user(self.user_pm).create({
            'project_id': self.project.id,
            'phase_stage': 'tkkt',
            'name': 'Bản vẽ kết cấu trụ tháp chính',
        })
        v1 = dossier.with_user(self.user_pm).action_upload_new_version(
            'Tru_Thap_v1.pdf', base64.b64encode(b'%PDF-1.4 v1 content').decode('ascii'),
        )
        v2 = dossier.with_user(self.user_pm).action_upload_new_version(
            'Tru_Thap_v2.pdf', base64.b64encode(b'%PDF-1.4 v2 revised').decode('ascii'),
        )
        self.assertEqual(v1['version_no'], 1)
        self.assertEqual(v2['version_no'], 2)
        self.assertEqual(dossier.current_version_no, 2)

        with self.assertRaises(AccessError):
            dossier.with_user(self.user_outsider)._tp_check_project_read()

    def test_03_eleven_separated_financial_metrics_never_fake_zero(self):
        """Executive finance strictly separates 11 metrics, blocks regular staff, and shows 'Chưa đủ dữ liệu' when missing."""
        Fin = self.env['tp.financial.summary.entry']
        with self.assertRaises(AccessError):
            Fin.with_user(self.user_outsider).tp_get_executive_dashboard_data('2026-11')

        # Record ONLY contract_value for period 2026-11
        res = Fin.with_user(self.user_fin).tp_record_financial_entry({
            'project_id': self.project.id,
            'period_label': '2026-11',
            'metric_kind': 'contract_value',
            'amount': 12500000000,
            'data_state': 'confirmed',
            'source_ref': 'HĐ-GOV-2026-01',
        })
        self.assertTrue(res['ok'])

        dash = Fin.with_user(self.admin).tp_get_executive_dashboard_data('2026-11')
        by_key = {c['key']: c for c in dash['financial_cards']}
        self.assertTrue(by_key['contract_value']['has_data'])
        self.assertEqual(by_key['contract_value']['value'], 12500000000.0)
        # Accepted value, accounting revenue, cash_in MUST NOT be faked as 0 or copied from contract_value!
        for other_key in ('internal_allocated_value', 'subcontract_value', 'accepted_value', 'accounting_revenue', 'cash_in', 'cash_out'):
            self.assertFalse(by_key[other_key]['has_data'])
            self.assertIsNone(by_key[other_key]['value'])
            self.assertEqual(by_key[other_key]['display_value'], 'Chưa đủ dữ liệu')

        # Cross-period guard: recording an earlier period 2026-10 MUST NOT sum into default latest period 2026-11
        Fin.with_user(self.user_fin).tp_record_financial_entry({
            'project_id': self.project.id,
            'period_label': '2026-10',
            'metric_kind': 'contract_value',
            'amount': 5000000000,
            'data_state': 'confirmed',
            'source_ref': 'HĐ-GOV-2026-00',
        })
        default_dash = Fin.with_user(self.admin).tp_get_executive_dashboard_data('')
        self.assertEqual(default_dash['active_period'], '2026-11')
        default_by_key = {c['key']: c for c in default_dash['financial_cards']}
        self.assertEqual(default_by_key['contract_value']['value'], 12500000000.0)

    def test_04_dossier_orm_guards_workflow_and_unique_version(self):
        """F-A07-0004 & F-A06-0016: Dossier write/unlink guards, sequential upload FOR UPDATE, UniqueIndex, and state transitions."""
        user_reader = self._make_user(
            'gov.reader',
            'Kỹ sư Xem Dự án (Gov)',
            [self.env.ref('base.group_user').id, self.env.ref('tp_core.group_user').id],
        )
        self._make_employee(user_reader, self.dept_bridge)
        self.env['tp.project.assignment'].sudo().create({
            'project_id': self.project.id,
            'user_id': user_reader.id,
            'role': 'reader',
            'active': True,
        })

        dossier = self.env['tp.project.dossier'].with_user(self.user_pm).create({
            'project_id': self.project.id,
            'phase_stage': 'tkkt',
            'name': 'Hồ sơ TKKT Cầu dẫn phía Bắc',
        })
        # Direct external write on system fields must be blocked even for PM
        for forbidden_vals in (
            {'state': 'issued'},
            {'current_version_no': 99},
            {'nas_relative_path': 'HACKED/PATH'},
            {'code': 'FORGED-01'},
        ):
            with self.assertRaises(AccessError), self.env.cr.savepoint():
                dossier.with_user(self.user_pm).write(forbidden_vals)

        # Non-owner reader cannot mutate metadata or upload versions
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            dossier.with_user(user_reader).write({'name': 'Sửa trái phép'})
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            dossier.with_user(user_reader).action_upload_new_version(
                'Reader.pdf', base64.b64encode(b'%PDF-1.4 x').decode('ascii'),
            )

        # Cannot submit without uploaded version
        with self.assertRaises(UserError), self.env.cr.savepoint():
            dossier.with_user(self.user_pm).action_submit_review()

        # Sequential version upload & DB UniqueIndex on (dossier_id, version_no)
        v1 = dossier.with_user(self.user_pm).action_upload_new_version(
            'Cau_Dan_v1.pdf', base64.b64encode(b'%PDF-1.4 v1').decode('ascii'),
        )
        v2 = dossier.with_user(self.user_pm).action_upload_new_version(
            'Cau_Dan_v2.pdf', base64.b64encode(b'%PDF-1.4 v2').decode('ascii'),
        )
        self.assertEqual((v1['version_no'], v2['version_no'], dossier.current_version_no), (1, 2, 2))

        ver1_rec = self.env['tp.project.dossier.version'].sudo().browse(v1['version_id'])
        with self.assertRaises(IntegrityError), self.env.cr.savepoint(), mute_logger('odoo.sql_db'):
            self.env['tp.project.dossier.version'].sudo().create({
                'dossier_id': dossier.id,
                'version_no': 1,
                'attachment_id': ver1_rec.attachment_id.id,
                'file_name': 'Duplicate_v1.pdf',
            })

        # Dossier with versions cannot be physically deleted
        with self.assertRaises(UserError), self.env.cr.savepoint():
            dossier.with_user(self.user_pm).unlink()

        # Workflow transitions: draft -> in_review -> approved -> issued
        dossier.with_user(self.user_pm).action_submit_review()
        self.assertEqual(dossier.state, 'in_review')
        dossier.with_user(self.user_pm).action_approve_technical()
        self.assertEqual(dossier.state, 'approved')
        dossier.with_user(self.user_pm).action_issue_dossier()
        self.assertEqual(dossier.state, 'issued')

        # Issued dossier locks metadata, new uploads, and unlink
        with self.assertRaises(UserError), self.env.cr.savepoint():
            dossier.with_user(self.user_pm).write({'name': 'Đổi tên sau ban hành'})
        with self.assertRaises(UserError), self.env.cr.savepoint():
            dossier.with_user(self.user_pm).action_upload_new_version(
                'Cau_Dan_v3.pdf', base64.b64encode(b'%PDF-1.4 v3').decode('ascii'),
            )
        with self.assertRaises(UserError), self.env.cr.savepoint():
            dossier.with_user(self.user_pm).unlink()


@tagged('post_install', '-at_install')
class TestDossierDownloadHttpAcl(HttpCase):
    def test_dossier_http_download_blocks_outsider_enumeration(self):
        """Mandatory Case #14 HTTP check: Outsider guessing /tp/dossier/download/<id> receives 403 Forbidden."""
        company = self.env.company
        admin = self.env.ref('base.user_admin')
        base_group = self.env.ref('base.group_user')
        self.env['res.users'].with_context(no_reset_password=True).create({
            'name': 'HTTP Outsider Test',
            'login': 'http.dossier.outsider',
            'password': 'TestPassword!123',
            'company_id': company.id,
            'company_ids': [Command.set(company.ids)],
            'group_ids': [Command.set([base_group.id])],
        })
        proj = self.env['project.project'].with_user(admin).create({
            'name': 'Dự án Bảo mật Hồ sơ HTTP',
            'company_id': company.id,
            'tp_managed': True,
            'tp_code': 'DA-HTTP-ACL-01',
        })
        dossier = self.env['tp.project.dossier'].with_user(admin).create({
            'project_id': proj.id,
            'phase_stage': 'tkbvtc',
            'name': 'Bản vẽ mật nội bộ dự án',
        })
        ver = dossier.with_user(admin).action_upload_new_version(
            'Mat_Cat_Cau.pdf', base64.b64encode(b'%PDF-1.4 secret drawing').decode('ascii'),
        )
        self.authenticate('http.dossier.outsider', 'TestPassword!123')
        resp = self.url_open(f"/tp/dossier/download/{ver['version_id']}")
        self.assertIn(resp.status_code, (403, 404))
        self.assertNotIn(b'secret drawing', resp.content)
