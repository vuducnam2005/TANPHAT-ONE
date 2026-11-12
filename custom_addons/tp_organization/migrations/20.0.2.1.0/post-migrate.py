"""HR-CORRECTION-008: repair the employee code sequence and wrong-band codes.

The sequence was created with ``number_next=20000`` in a ``noupdate`` file, so
manual employees received TP20000+ instead of the next TP1xxxx number. This
migration:

* maps manual codes issued by that sequence (numbers 20000 up to the
  sequence's last value) to the next free numbers of the TP10001-TP19999 band,
  only for records without roster source, personal account or references;
  each mapping keeps the employee id and writes an audit row and a chatter log;
* reports (log only, no change) any other TP2xxxx code;
* moves the sequence back into the band, right after the highest valid code.
"""
import logging

from odoo import SUPERUSER_ID, api

from odoo.addons.tp_organization.models.hr_employee import (
    _CODE_LOCK,
    _TP_CODE_CORRECTION,
    CODE_MAX,
    code_number,
)

_logger = logging.getLogger(__name__)
_LEGACY_START = 20000
_REASON = ('HR-CORRECTION-008: mã do cấu hình sequence cũ (bắt đầu 20000) cấp nhầm cho hồ sơ nhập tay; '
           'chuyển sang số kế tiếp sau mã hợp lệ cao nhất, giữ nguyên ID và liên kết.')


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {'active_test': False, 'lang': 'vi_VN'})
    Employee = env['hr.employee'].with_context(active_test=False)
    sequence = Employee._tp_code_sequence()
    cr.execute('SELECT pg_advisory_xact_lock(%s)', [_CODE_LOCK])
    legacy_next = Employee._tp_sequence_next(sequence)
    mapped, reported = [], []
    for employee in Employee.search([('tp_employee_code', '=like', 'TP%')], order='create_date, id'):
        number = code_number(employee.tp_employee_code)
        if not number or number <= CODE_MAX:
            continue
        reasons = []
        if not _LEGACY_START <= number < legacy_next:
            reasons.append('không thuộc khoảng sequence cũ đã cấp')
        if employee.tp_source_code or employee.tp_import_batch_id:
            reasons.append('mã từ danh sách nhân sự')
        if employee.user_id:
            reasons.append('đã cấp tài khoản')
        references = employee._tp_reference_counts()[employee.id]
        if references:
            reasons.append('đang được tham chiếu: ' + ', '.join(f'{label} ({count})' for label, count in references))
        if reasons:
            reported.append((employee.id, employee.tp_employee_code, '; '.join(reasons)))
            continue
        old_code = employee.tp_employee_code
        new_code = f'TP{Employee._tp_code_floor()}'
        employee.with_context(_tp_code_correction=_TP_CODE_CORRECTION).write({'tp_employee_code': new_code})
        env['tp.hr.employee.audit']._tp_record([{
            'action': 'code_correction', 'employee_ref': employee.id, 'employee_name': employee.name,
            'employee_code': old_code, 'new_code': new_code, 'company_id': employee.company_id.id, 'reason': _REASON,
            'snapshot': {'migration': 'tp_organization 20.0.2.1.0', 'legacy_sequence_next': legacy_next,
                         'create_date': str(employee.create_date), 'create_uid': employee.create_uid.id},
        }])
        employee._message_log(body=env._('Sửa mã nhân viên %(old)s → %(new)s (HR-CORRECTION-008, migration có nhật ký).',
                                         old=old_code, new=new_code))
        mapped.append((employee.id, old_code, new_code))
    floor = Employee._tp_code_floor()
    if not floor <= Employee._tp_sequence_next(sequence) <= CODE_MAX:
        Employee._tp_reset_code_sequence(floor)
    _logger.info('HR-CORRECTION-008 employee code mapping: %s', mapped or 'none')
    if reported:
        _logger.warning('HR-CORRECTION-008 TP codes outside the band kept for review: %s', reported)
    _logger.info('HR-CORRECTION-008 next employee code: TP%s', Employee._tp_sequence_next(sequence))
