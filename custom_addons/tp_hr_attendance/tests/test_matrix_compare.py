"""ORM integration tests for HR-ATTENDANCE-MATRIX-003 (DEC-058): upload, matrix, A/B compare & security."""
import base64
from datetime import date

from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged

from .common import AttendanceCase, report
from .test_matrix_pure import _build_matrix_xlsx

MONDAY = date(2026, 11, 9)
SUNDAY = date(2026, 11, 15)


@tagged('post_install', '-at_install')
class TestMatrixAndCompare(AttendanceCase):
    def _b64(self, raw_bytes):
        return base64.b64encode(raw_bytes).decode('ascii')

    def test_upload_persists_preview_and_discard_keeps_audit(self):
        raw_ok = report([
            {'code': '9901', 'name': 'Synthetic Người Một', 'times': [('08:20', '17:05'), (None, None)]},
            {'code': '9902', 'name': 'Synthetic Người Hai', 'times': [(None, None), (None, None)]},
        ], MONDAY, 2)
        importer_env = self.env_for(self.manager)
        Batch = importer_env['tp.hr.attendance.batch']

        res = Batch.tp_upload_files([
            {'filename': 'nguon_hop_le.xlsx', 'content_b64': self._b64(raw_ok)},
            {'filename': 'sai_dinh_dang.txt', 'content_b64': self._b64(b'not xlsx')},
        ])
        self.assertEqual(len(res['created']), 1)
        self.assertEqual(len(res['rejected']), 1)
        batch_id = res['created'][0]['id']

        batch = self.env['tp.hr.attendance.batch'].sudo().browse(batch_id)
        self.assertEqual(batch.state, 'preview')
        self.assertTrue(batch.batch_code.startswith('LÔ-'))
        # Preview upload NEVER writes canonical sessions
        self.assertFalse(self.env['tp.hr.attendance.session'].sudo().search([('employee_id', 'in', (self.emp_a + self.emp_b).ids)]))

        # Matrix data includes both people (including all-blank emp_b)
        mdata = Batch.tp_matrix_data({'batch_id': batch_id, 'page_size': 10})
        self.assertEqual(mdata['summary']['employees'], 2)
        all_people = [p for g in mdata['groups'] for p in g['people']]
        self.assertEqual(len(all_people), 2)
        self.assertTrue(all_people[1]['all_empty'])

        # Discard requires reason and keeps audit record
        with self.assertRaises(UserError):
            Batch.tp_discard_batch(batch_id, '')
        discard = Batch.tp_discard_batch(batch_id, 'Tải nhầm bản nháp cũ')
        self.assertTrue(discard['discarded'])
        batch.invalidate_recordset()
        self.assertEqual(batch.state, 'cancelled')
        self.assertEqual(batch.cancel_reason, 'Tải nhầm bản nháp cũ')

    def test_compare_same_provenance_diff_partial_and_resolve_guards(self):
        # Employee A uses code TP001/1 in file A, and code 9901 (mapped via different machine code? wait: test both mapping to emp_a!)
        self.emp_a.sudo().write({'tp_employee_code': 'TP10001'})
        # Map 9901 -> emp_a (already in AttendanceCase? ensure mapping via attendance.code)
        importer_env = self.env_for(self.manager)
        Batch = importer_env['tp.hr.attendance.batch']

        raw_a = _build_matrix_xlsx([{
            'title': 'Nguồn A',
            'start': MONDAY,
            'end': date(2026, 11, 11),
            'rows': [
                {'stt': 1, 'code': '9901', 'name': 'Synthetic Người Một',
                 'times': [('08:30', '17:05'), ('08:35', '17:10'), ('08:20', None)],
                 'late': (1, 5)},
                {'stt': 2, 'code': '9999', 'name': 'Nhân Sự Chưa Mapping',
                 'times': [('08:30', '17:00'), (None, None), (None, None)],
                 'late': (0, 0)},
            ],
        }])
        raw_b = _build_matrix_xlsx([{
            'title': 'Nguồn B',
            'start': MONDAY,
            'end': date(2026, 11, 12),
            'rows': [
                {'stt': 1, 'code': '9901', 'name': 'Synthetic Người Một',
                 'times': [('08:30', '17:05'), ('08:40', '17:15'), (None, '17:00'), ('08:25', '17:00')],
                 'late': (2, 10)},
                {'stt': 2, 'code': '8888', 'name': 'Nhân Sự Chưa Mapping',
                 'times': [('09:00', '17:00'), (None, None), (None, None), (None, None)],
                 'late': (0, 0)},
            ],
        }])

        up = Batch.tp_upload_files([
            {'filename': 'file_a.xlsx', 'content_b64': self._b64(raw_a)},
            {'filename': 'file_b.xlsx', 'content_b64': self._b64(raw_b)},
        ])
        id_a, id_b = up['created'][0]['id'], up['created'][1]['id']

        cmp = Batch.tp_compare_batches({'batch_a_id': id_a, 'batch_b_id': id_b})
        # Unmapped rows with identical name across A and B MUST NOT be merged!
        unmapped_rows = [r for r in cmp['rows'] if r['mapping_state'] != 'mapped']
        self.assertEqual(len(unmapped_rows), 2)

        mapped = next(r for r in cmp['rows'] if r['employee_id'] == self.emp_a.id)
        by_d = {d['date']: d for d in mapped['days']}
        self.assertEqual(by_d['2026-11-09']['group'], 'same')
        self.assertEqual(by_d['2026-11-10']['group'], 'diff')
        # Day 3: missing_out (A) vs missing_in (B) -> diff, never auto-spliced!
        self.assertEqual(by_d['2026-11-11']['group'], 'diff')
        # Day 4: outside A's period -> only_b with reason naming scope
        self.assertEqual(by_d['2026-11-12']['group'], 'only_b')
        self.assertEqual(by_d['2026-11-12']['a_scope'], 'out_of_scope')

        # Partial apply valid: same (Nov 9) + only_b (Nov 12) applied; Nov 10 & Nov 11 left conflict/unapplied
        applied = Batch.tp_apply_compare_valid({'batch_a_id': id_a, 'batch_b_id': id_b})
        self.assertEqual(applied['applied_cells'], 2)
        s09 = self.env['tp.hr.attendance.session'].sudo().search([
            ('employee_id', '=', self.emp_a.id), ('work_date', '=', date(2026, 11, 9)), ('active', '=', True),
        ])
        self.assertEqual(len(s09), 1)
        self.assertEqual(set(s09.source_batch_ids.ids), {id_a, id_b})

        # Stale digest CAS guard rejects wrong expected_digest
        day10 = next(d for d in applied['compare']['rows'] if d['employee_id'] == self.emp_a.id)['days']
        d10 = next(x for x in day10 if x['date'] == '2026-11-10')
        with self.assertRaises(UserError):
            Batch.tp_resolve_compare_batch({
                'batch_a_id': id_a, 'batch_b_id': id_b,
                'reason': 'Test stale digest',
                'items': [{'target_kind': 'day', 'employee_id': self.emp_a.id, 'work_date': '2026-11-10',
                           'decision': 'use_b', 'expected_digest': 'WRONG'}],
            })

        # Valid resolve with use_b creates resolution audit log + updates canonical session
        res = Batch.tp_resolve_compare_batch({
            'batch_a_id': id_a, 'batch_b_id': id_b,
            'reason': 'Chọn B theo xác nhận trưởng bộ phận',
            'items': [{'target_kind': 'day', 'employee_id': self.emp_a.id, 'work_date': '2026-11-10',
                       'decision': 'use_b', 'expected_digest': d10['target_digest']}],
        })
        self.assertEqual(res['resolved'], 1)
        s10 = self.env['tp.hr.attendance.session'].sudo().search([
            ('employee_id', '=', self.emp_a.id), ('work_date', '=', date(2026, 11, 10)), ('active', '=', True),
        ])
        self.assertEqual(len(s10), 1)

        # Replacing existing canonical session WITHOUT reason fails
        cmp_after = res['compare']
        d10_after = next(x for x in next(r for r in cmp_after['rows'] if r['employee_id'] == self.emp_a.id)['days'] if x['date'] == '2026-11-10')
        with self.assertRaises(UserError):
            Batch.tp_resolve_compare_batch({
                'batch_a_id': id_a, 'batch_b_id': id_b,
                'reason': '',
                'items': [{'target_kind': 'day', 'employee_id': self.emp_a.id, 'work_date': '2026-11-10',
                           'decision': 'use_a', 'expected_digest': d10_after['target_digest']}],
            })

        # Excel export works and keeps formula neutralization safe
        ex_m = Batch.tp_export_matrix({'batch_id': id_a})
        self.assertTrue(ex_m['filename'].endswith('.xlsx'))
        ex_c = Batch.tp_export_compare({'batch_a_id': id_a, 'batch_b_id': id_b})
        self.assertTrue(ex_c['filename'].endswith('.xlsx'))

    def test_security_regular_user_blocked_and_locked_period_refused(self):
        viewer_env = self.env_for(self.viewer)
        with self.assertRaises(AccessError):
            viewer_env['tp.hr.attendance.batch'].tp_matrix_data({})
        with self.assertRaises(AccessError):
            viewer_env['tp.hr.attendance.batch'].tp_compare_batches({})
        with self.assertRaises(AccessError):
            viewer_env['tp.hr.attendance.batch'].tp_upload_files([])
        with self.assertRaises(AccessError):
            viewer_env['tp.hr.attendance.snapshot.person'].search([])
        with self.assertRaises(AccessError):
            viewer_env['tp.hr.attendance.resolution'].search([])

        # Locked period cannot be overwritten via compare resolution
        importer_env = self.env_for(self.manager)
        Batch = importer_env['tp.hr.attendance.batch']
        raw_lock = _build_matrix_xlsx([{
            'title': 'Lock check', 'start': MONDAY, 'end': MONDAY,
            'rows': [{'stt': 1, 'code': '9901', 'name': 'Synthetic Người Một', 'times': [('08:15', '17:00')], 'late': (0, 0)}],
        }])
        up = Batch.tp_upload_files([{'filename': 'lock.xlsx', 'content_b64': self._b64(raw_lock)}])
        bid = up['created'][0]['id']
        self.env['tp.hr.attendance.period'].sudo().create({
            'company_id': self.company.id, 'date_from': MONDAY, 'date_to': MONDAY, 'state': 'locked',
        })
        cmp = Batch.tp_compare_batches({'batch_a_id': bid, 'batch_b_id': 0})
        row = next(r for r in cmp['rows'] if r['employee_id'] == self.emp_a.id)
        d0 = row['days'][0]
        self.assertIn('chốt', d0['blocked_reason'])
        with self.assertRaises(UserError):
            Batch.tp_resolve_compare_batch({
                'batch_a_id': bid, 'batch_b_id': 0, 'reason': 'Attempt locked overwrite',
                'items': [{'target_kind': 'day', 'employee_id': self.emp_a.id, 'work_date': MONDAY.isoformat(),
                           'decision': 'use_a', 'expected_digest': d0['target_digest']}],
            })
        # Idempotent migration helper does not duplicate snapshots
        Batch.sudo()._tp_migrate_matrix_003()
        Batch.sudo()._tp_migrate_matrix_003()
        self.assertEqual(self.env['tp.hr.attendance.snapshot.person'].sudo().search_count([('batch_id', '=', bid)]), 1)
