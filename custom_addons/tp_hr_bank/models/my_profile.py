"""Self-service bank accounts in "Thông tin cá nhân" (BANK-001).

Every account works on its own records only: an employee on the accounts linked to their
employee profile in the current company (the ones HR and payroll use), an account without an
employee profile on the bank accounts of its own contact. Writes run under a scoped sudo after
the ownership check; the user never gets write access to ``res.partner.bank`` itself.

BANK-002: no HR verification step. A complete, valid account the owner saves is ready for
payroll at once (``allow_out_payment`` set); every add/change/removal is logged on the
employee with the last four digits only.
"""
import re

from markupsafe import Markup

from odoo import Command, api, models
from odoo.exceptions import AccessError, ValidationError
from odoo.tools import remove_accents

MAX_ACCOUNTS = 5
BANK_KEYS = frozenset({'bank_id', 'account_number', 'holder_name'})
NUMBER_RE = re.compile(r'[0-9]{6,20}')
HOLDER_RE = re.compile(r"[A-Z][A-Z .'-]{1,119}")


def holder_ascii(value):
    """Bank style holder name: no diacritics, upper case, single spaces (NGUYEN VAN AN)."""
    value = (value or '').replace('đ', 'd').replace('Đ', 'D')
    return re.sub(r'\s+', ' ', remove_accents(value)).strip().upper()


def mask_number(number):
    number = number or ''
    return '••••' + number[-4:] if len(number) > 4 else number


class ResUsersBankProfile(models.Model):
    _inherit = 'res.users'

    # ------------------------------------------------------------------ owner & reading
    @api.model
    def _tp_bank_owner(self, strict=True):
        """Return ``(employee, partner)`` owning the current user's bank accounts (both sudo).

        ``employee`` is empty for an account without an employee profile in the current company.
        """
        user = self.env.user
        employee = user._tp_main_employee()
        if employee:
            employee = employee.sudo()
            partner = employee.work_contact_id
            if not partner and strict:
                raise ValidationError(self.env._(
                    'Hồ sơ nhân viên của bạn chưa có liên hệ công việc nên chưa khai báo được tài khoản ngân hàng. '
                    'Vui lòng báo bộ phận Nhân sự.'
                ))
            return employee, partner
        return self.env['hr.employee'].sudo(), user.partner_id.sudo()

    @api.model
    def _tp_bank_accounts(self, employee, partner):
        if employee:
            return employee.bank_account_ids
        return self.env['res.partner.bank'].sudo().search([('partner_id', '=', partner.id)])

    @api.model
    def _tp_bank_account_card(self, account, primary):
        bank = account.tp_bank_id
        return {
            'id': account.id,
            'bank': bank._tp_card() if bank else None,
            'bank_label': bank.short_name if bank else (account.bank_name or self.env._('Chưa chọn ngân hàng')),
            'account_number': account.account_number,
            'holder_name': account.holder_name or '',
            'trusted': bool(account.allow_out_payment),
            'primary': account == primary,
        }

    @api.model
    def _tp_bank_payload(self):
        employee, partner = self._tp_bank_owner(strict=False)
        payload = {
            'available': bool(partner),
            'owner': 'employee' if employee else 'user',
            'banks': self.env['tp.bank'].tp_bank_catalog(),
            'accounts': [],
            'default_holder': holder_ascii(employee.name if employee else self.env.user.name),
            'max_accounts': MAX_ACCOUNTS,
        }
        if not partner:
            payload['message'] = self.env._(
                'Hồ sơ nhân viên chưa có liên hệ công việc nên chưa khai báo được tài khoản ngân hàng. '
                'Vui lòng báo bộ phận Nhân sự.'
            )
            return payload
        accounts = self._tp_bank_accounts(employee, partner)
        primary = employee.primary_bank_account_id if employee else accounts[:1]
        payload['accounts'] = [self._tp_bank_account_card(account, primary) for account in accounts]
        return payload

    @api.model
    def tp_get_my_profile(self):
        payload = super().tp_get_my_profile()
        payload['bank'] = self._tp_bank_payload()
        return payload

    # ------------------------------------------------------------------ validation helpers
    @api.model
    def _tp_own_bank_account(self, account_id, accounts):
        if isinstance(account_id, bool):
            raise ValidationError(self.env._('Tài khoản ngân hàng không hợp lệ.'))
        try:
            account_id = int(account_id)
        except (TypeError, ValueError) as exc:
            raise ValidationError(self.env._('Tài khoản ngân hàng không hợp lệ.')) from exc
        if account_id not in accounts.ids:
            raise AccessError(self.env._('Không có quyền sửa tài khoản ngân hàng của người khác.'))
        return accounts.browse(account_id)

    @api.model
    def _tp_clean_bank(self, raw):
        if raw in (False, None, '', 0) or isinstance(raw, bool):
            raise ValidationError(self.env._('Vui lòng chọn ngân hàng trong danh sách.'))
        try:
            bank = self.env['tp.bank'].browse(int(raw)).exists()
        except (TypeError, ValueError) as exc:
            raise ValidationError(self.env._('Vui lòng chọn ngân hàng trong danh sách.')) from exc
        if not bank or not bank.active:
            raise ValidationError(self.env._('Vui lòng chọn ngân hàng trong danh sách.'))
        return bank

    @api.model
    def _tp_clean_number(self, raw):
        number = re.sub(r'[\s.\-]', '', '' if raw in (False, None) else str(raw))
        if not number:
            raise ValidationError(self.env._('Vui lòng nhập số tài khoản.'))
        if not NUMBER_RE.fullmatch(number):
            raise ValidationError(self.env._('Số tài khoản chỉ gồm chữ số, từ 6 đến 20 số.'))
        return number

    @api.model
    def _tp_clean_holder(self, raw, default):
        holder = holder_ascii('' if raw in (False, None) else str(raw)) or default
        if not HOLDER_RE.fullmatch(holder or ''):
            raise ValidationError(self.env._(
                'Tên chủ tài khoản chỉ gồm chữ cái không dấu và khoảng trắng, tối đa 120 ký tự.'
            ))
        return holder

    @api.model
    def _tp_bank_note(self, employee, message):
        if employee:
            employee.message_post(
                body=Markup('<p>%s</p>') % message,
                message_type='notification',
                subtype_xmlid='mail.mt_note',
            )

    # ------------------------------------------------------------------ public methods
    @api.model
    def tp_save_my_bank_account(self, account_id, vals):
        """Add (``account_id`` empty) or update one of the user's own bank accounts."""
        if not isinstance(vals, dict):
            raise ValidationError(self.env._('Dữ liệu tài khoản ngân hàng không hợp lệ.'))
        forbidden = set(vals) - BANK_KEYS
        if forbidden:
            raise AccessError(self.env._(
                'Bạn không có quyền tự chỉnh sửa trường do HR quản lý: %s.', ', '.join(sorted(forbidden)),
            ))
        employee, partner = self._tp_bank_owner()
        accounts = self._tp_bank_accounts(employee, partner)
        account = self._tp_own_bank_account(account_id, accounts) if account_id else accounts.browse()

        bank = self._tp_clean_bank(vals.get('bank_id'))
        number = self._tp_clean_number(vals.get('account_number'))
        holder = self._tp_clean_holder(
            vals.get('holder_name'), holder_ascii(employee.name if employee else self.env.user.name),
        )

        Account = self.env['res.partner.bank'].sudo().with_context(active_test=False)
        same_number = Account.search([
            ('partner_id', '=', partner.id), ('sanitized_account_number', '=', number), ('id', '!=', account.id),
        ], limit=1)
        if same_number and same_number.active and same_number in accounts:
            raise ValidationError(self.env._('Số tài khoản này đã có trong danh sách của bạn.'))

        if account:
            if same_number:
                raise ValidationError(self.env._(
                    'Số tài khoản này đã được khai báo trước đây. Hãy xóa dòng đang sửa rồi thêm lại số này.'
                ))
            changes = {}
            if account.tp_bank_id != bank:
                changes['tp_bank_id'] = bank.id
            if account.sanitized_account_number != number:
                changes['account_number'] = number
            if (account.holder_name or '') != holder:
                changes['holder_name'] = holder
            if not changes:
                return self.tp_get_my_profile()
            if not account.allow_out_payment:
                changes['allow_out_payment'] = True
            account.write(changes)
            message = self.env._('Nhân viên tự cập nhật tài khoản ngân hàng: %(bank)s %(number)s.',
                                 bank=bank.short_name, number=mask_number(number))
        else:
            if len(accounts) >= MAX_ACCOUNTS:
                raise ValidationError(self.env._('Mỗi người khai báo tối đa %s tài khoản ngân hàng.', MAX_ACCOUNTS))
            values = {'tp_bank_id': bank.id, 'account_number': number, 'holder_name': holder}
            if same_number:
                # Same number declared before (removed or not linked yet): reuse that record.
                account = same_number
                account.write(dict(values, active=True, allow_out_payment=True))
            else:
                account = Account.create(dict(values, partner_id=partner.id, allow_out_payment=True))
            if employee:
                employee.write({'bank_account_ids': [Command.link(account.id)]})
            message = self.env._('Nhân viên tự thêm tài khoản ngân hàng: %(bank)s %(number)s.',
                                 bank=bank.short_name, number=mask_number(number))
        self._tp_bank_note(employee, message)
        return self.tp_get_my_profile()

    @api.model
    def tp_remove_my_bank_account(self, account_id):
        """Remove one of the user's own bank accounts: unlink it and archive it (no hard delete)."""
        employee, partner = self._tp_bank_owner()
        accounts = self._tp_bank_accounts(employee, partner)
        account = self._tp_own_bank_account(account_id, accounts)
        label = f'{account.tp_bank_id.short_name or account.bank_name or ""} {mask_number(account.sanitized_account_number)}'.strip()
        if employee:
            employee.write({'bank_account_ids': [Command.unlink(account.id)]})
            still_used = self.env['hr.employee'].sudo().with_context(active_test=False).search_count(
                [('bank_account_ids', 'in', account.ids)],
            )
        else:
            still_used = 0
        if not still_used:
            account.write({'active': False, 'allow_out_payment': False})
        self._tp_bank_note(employee, self.env._('Nhân viên tự gỡ tài khoản ngân hàng: %s.', label))
        return self.tp_get_my_profile()
