"""BANK-002: accounts people declared themselves no longer wait for HR verification.

Self-declared accounts (catalogue bank set, linked to an employee profile or owned by a user's
own contact) that are still unverified become ready for payroll, the same as a new save does
now. Only counts are logged, never numbers or names.
"""
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    # install_mode: the account module lets the superuser mark accounts trusted only during upgrades.
    env = api.Environment(cr, SUPERUSER_ID, {'install_mode': True, 'active_test': False})
    linked = env['hr.employee'].search([]).bank_account_ids
    user_partners = env['res.users'].search([]).partner_id
    accounts = env['res.partner.bank'].search([
        ('active', '=', True), ('tp_bank_id', '!=', False), ('allow_out_payment', '=', False),
        '|', ('id', 'in', linked.ids), ('partner_id', 'in', user_partners.ids),
    ])
    accounts.write({'allow_out_payment': True})
    _logger.info('BANK-002: %s self-declared bank account(s) now ready for payroll without HR verification',
                 len(accounts))
