"""HR-CORRECTION-008: personal accounts created by the TP HR wizard start in Vietnamese.

The wizard did not set ``lang``, so accounts it created kept the en_US default
although nobody chose English. Only those accounts (identified by the wizard's
own chatter log on the employee) are switched to vi_VN; every other account
keeps its language.
"""
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {'active_test': False})
    if 'vi_VN' not in dict(env['res.lang'].get_installed()):
        return
    cr.execute("""
        SELECT DISTINCT u.id, u.login
          FROM res_users u
          JOIN res_partner p ON p.id = u.partner_id
          JOIN hr_employee e ON e.user_id = u.id
          JOIN mail_message m ON m.model = 'hr.employee' AND m.res_id = e.id
         WHERE u.share IS NOT TRUE AND p.lang = 'en_US'
           AND m.body::text LIKE '%%Đã tạo tài khoản cá nhân ' || u.login || '%%'
         ORDER BY u.id
    """)
    rows = cr.fetchall()
    if rows:
        env['res.users'].browse([row[0] for row in rows]).write({'lang': 'vi_VN'})
    _logger.info('HR-CORRECTION-008 personal accounts switched to vi_VN: %s', [row[1] for row in rows] or 'none')
