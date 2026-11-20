"""HR-EMPLOYEE-CODE-003: employee codes TP1nnnn -> TPnnn (TP + three digits).

Every employee of every company, active or archived, is mapped by the rule
TP10001-TP10999 -> number - 10000 (TP10060 -> TP060); three-digit codes are
kept. The whole mapping is checked first (duplicates in a company, codes
outside the rule, missing codes, retired numbers, roster source numbers) and
the upgrade stops before any write when one row conflicts. Only
``tp_employee_code`` changes: the record, its id, account, links, attendance
and history stay; one audit row and one chatter note record old and new code.
The sequence continues after the highest issued number. Running it again on
converted data changes nothing.
"""
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)
_REASON = ('HR-EMPLOYEE-CODE-003: chuyển mã nhân viên TP1nnnn sang TP + 3 chữ số (số - 10000), '
           'giữ nguyên ID hồ sơ, tài khoản và mọi liên kết.')


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {'active_test': False, 'lang': 'vi_VN'})
    result = env['hr.employee']._tp_code_format_apply(_REASON)
    _logger.info('HR-EMPLOYEE-CODE-003 plan %s: %s converted, %s kept, next number %s',
                 result['digest'], len(result['changed']), result['kept'], result['next'])
    for employee_id, old, new in result['changed']:
        _logger.info('HR-EMPLOYEE-CODE-003 employee id %s: %s -> %s', employee_id, old, new)
