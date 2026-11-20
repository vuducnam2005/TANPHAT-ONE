"""HR-DELETE-010: permanent employee deletion with admin password re-verification.

The dialog (``tp_hr_workspace.employee_delete`` client action) asks the server
for a preview, then sends the reason, the account choice, the preview digest,
a request id and the admin's freshly typed password in ONE final request. That
request re-checks rights and session, verifies the password with Odoo's native
``_check_credentials`` inside the native login throttle (never the 10-minute
identity-check reuse), locks, recomputes the plan, compares it with the preview
and with committed data, then locks/keeps accounts, deletes and audits in one
transaction. The password is never stored, logged or audited.
"""
import re

from odoo import Command, api, models
from odoo.exceptions import AccessDenied, AccessError, UserError
from odoo.http import request

_REQUEST_ID = re.compile(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}')
_PROTECTED_XMLIDS = ('base.user_root', 'base.user_admin', 'base.public_user', 'base.template_portal_user', 'base.default_user')
WRONG_PASSWORD = 'Mật khẩu chưa đúng. Hãy nhập lại mật khẩu của tài khoản quản trị đang đăng nhập. Chưa có hồ sơ nào bị xóa.'
COOLDOWN = 'Bạn đã nhập sai quá nhiều lần. Vui lòng chờ ít phút rồi thử lại. Chưa có hồ sơ nào bị xóa.'
VERIFIED = 'Mật khẩu quản trị đã được xác minh lại trong chính yêu cầu xóa.'


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # ------------------------------------------------------------------
    # Entry points
    # ------------------------------------------------------------------
    def action_tp_permanent_delete(self):
        """Open the confirmation dialog for the selected employees."""
        employees = self.with_context(active_test=False)
        employees._tp_check_permanent_delete_rights()
        return {
            'type': 'ir.actions.client',
            'tag': 'tp_hr_workspace.employee_delete',
            'name': self.env._('Xóa vĩnh viễn nhân viên'),
            'params': {'employeeIds': employees.ids},
        }

    def action_unlink_wizard(self):
        # hr_timesheet binds a generic "Delete" action; route it to the guarded flow.
        return self.action_tp_permanent_delete()

    def action_tp_delete_mistaken(self):
        # Former HR-CORRECTION-008 entry point (DEC-041), superseded by DEC-042.
        return self.action_tp_permanent_delete()

    # ------------------------------------------------------------------
    # Accounts
    # ------------------------------------------------------------------
    def _tp_protected_user_ids(self):
        protected = {self.env.uid}
        for xmlid in _PROTECTED_XMLIDS:
            record = self.env.ref(xmlid, raise_if_not_found=False)
            if record:
                protected.add(record.id)
        return protected

    def _tp_account_sources(self, user, company):
        empty = [('id', '=', 0)]
        scope = [('user_id', '=', user.id), ('active', '=', True), ('company_id', '=', company.id)] if user else empty
        return {
            'roles': self.env['tp.kd.department.role'].sudo().search(scope, order='id'),
            'assignments': self.env['tp.project.assignment'].sudo().search(scope, order='id'),
            'grants': self.env['tp.project.grant'].sudo().search(scope, order='id'),
            'kd_grants': self.env['tp.kd.grant'].sudo().search(scope, order='id'),
            'members': self.env['crm.team.member'].sudo().search(scope, order='id'),
        }

    def _tp_account_plan(self):
        """Account facts and blockers for both choices (keep / lock)."""
        employees = self.sudo().with_context(active_test=False)
        protected = self._tp_protected_user_ids()
        scoped = self.env.ref('tp_kd_workspace.group_scoped_staff', raise_if_not_found=False)
        accounts = {}
        for employee in employees:
            user = employee.user_id.sudo().with_context(active_test=False)
            if not user:
                continue
            sources = self._tp_account_sources(user, employee.company_id)
            other_employees = self.env['hr.employee'].sudo().with_context(active_test=False).search([
                ('user_id', '=', user.id), ('id', 'not in', employees.ids)])
            work = self.env['tp.hr.role.wizard'].sudo()._transfer_work(employee)
            pending = sum(len(rows) for rows in work.values())
            common, lock_block, keep_block = [], [], []
            if user.id == self.env.uid:
                common.append('Hồ sơ gắn với tài khoản bạn đang dùng — không tự xóa hồ sơ của chính mình.')
            if user.id in protected or user.share or user.has_group('base.group_system'):
                lock_block.append('Tài khoản quản trị/hệ thống được bảo vệ, không khóa từ luồng này — bỏ chọn khóa tài khoản.')
            if set(user.company_ids.ids) - set(self.env.companies.ids):
                lock_block.append('Tài khoản có công ty ngoài phạm vi đang quản lý — bỏ chọn khóa tài khoản.')
            if other_employees:
                lock_block.append('Tài khoản còn gắn hồ sơ khác: ' + ', '.join(other_employees.mapped('display_name')) + ' — xử lý hồ sơ đó trước.')
            live = [label for key, label in (('roles', 'trưởng phòng/ban'), ('assignments', 'phân công dự án'), ('grants', 'quyền dự án'),
                                             ('kd_grants', 'quyền KH-KD'), ('members', 'thành viên nhóm kinh doanh')) if sources[key]]
            if live:
                keep_block.append('Tài khoản còn ' + ', '.join(live) + ' — chọn "Xóa hồ sơ và khóa tài khoản" hoặc hạ quyền trước.')
            accounts[str(employee.id)] = {
                'user_id': user.id,
                'login': user.login,
                'name': user.name,
                'active': user.active,
                'locked': bool(user.tp_hr_locked),
                'revision': user.tp_lock_revision,
                'write_date': str(user.write_date),
                'groups': sorted(user.group_ids.ids),
                'companies': sorted(user.company_ids.ids),
                'scoped_staff': bool(scoped and scoped in user.group_ids),
                'sources': {key: [[record.id, str(record.write_date)] for record in records] for key, records in sources.items()},
                'live': live,
                'work': {model: [[row['id'], row['name'], str(row['write_date'])] for row in rows] for model, rows in sorted(work.items()) if rows},
                'pending': pending,
                'block': common,
                'lock_block': lock_block,
                'keep_block': keep_block,
            }
        return accounts

    def _tp_full_plan(self):
        plan = self._tp_delete_plan()
        plan['accounts'] = self._tp_account_plan()
        plan['company_id'] = self.env.company.id
        return plan

    # ------------------------------------------------------------------
    # RPC: preview
    # ------------------------------------------------------------------
    def tp_permanent_delete_preview(self):
        """Read-only preview for the dialog (no write, no password)."""
        employees = self.with_context(active_test=False)
        employees._tp_check_permanent_delete_rights()
        plan = employees._tp_full_plan()
        rows = []
        for employee_id in employees.ids:
            entry = plan['employees'][employee_id]
            account = plan['accounts'].get(str(employee_id))
            rows.append({
                'id': employee_id,
                'name': entry['name'],
                'code': entry['code'],
                'sourceCode': entry['source_code'],
                'department': entry['department'],
                'active': entry['active'],
                'login': account['login'] if account else '',
                'accountActive': account['active'] if account else False,
                'delete': [{'label': label, 'value': value} for label, value in entry['delete']],
                'keep': [{'label': label, 'value': value} for label, value in entry['keep']]
                + ([{'label': 'Tài khoản đăng nhập ' + account['login'], 'value': 'Giữ (mặc định); có thể chọn khóa'}] if account else [])
                + ([{'label': 'Công việc đang phụ trách cần bàn giao (không tự đổi người phụ trách)', 'value': account['pending']}] if account and account['pending'] else []),
                'block': [{'label': label, 'value': count, 'hint': hint} for label, count, hint in entry['block']]
                + ([{'label': text, 'value': '', 'hint': ''} for text in account['block']] if account else []),
                'lockBlock': account['lock_block'] if account else [],
                'keepBlock': account['keep_block'] if account else [],
                'assetsToReturn': entry.get('assets_to_return', []),
                'equipmentHistory': entry.get('equipment_history', []),
                'cancelledMoves': entry.get('cancelled_moves', []),
            })
        first_emp_id = employees.ids[0] if employees.ids else 0
        available_locs = plan.get('equipment_available_locations', {}).get(first_emp_id, [])
        default_loc_id = plan.get('equipment_default_location_id', {}).get(first_emp_id, False)
        return {
            'employees': rows,
            'count': len(rows),
            'accountCount': sum(1 for row in rows if row['login']),
            'digest': self._tp_digest(plan),
            'adminLogin': self.env.user.login,
            'availableLocations': available_locs,
            'defaultLocationId': default_loc_id,
            'hasAssetsToReturn': any(bool(row.get('assetsToReturn')) for row in rows),
        }

    # ------------------------------------------------------------------
    # RPC: execute
    # ------------------------------------------------------------------
    def _tp_verify_admin_password(self, password):
        """Native password check of the logged-in admin, inside the login throttle.

        Raises ``AccessDenied`` (wrong) or returns a cooldown message. Never
        touches ``identity-check-last`` and never stores the password.
        """
        user = self.env.user
        attempted = False
        try:
            with user._assert_can_auth(user=user.login):
                attempted = True
                user._check_credentials({'login': user.login, 'password': password, 'type': 'password'}, {'interactive': True})
        except AccessDenied:
            return WRONG_PASSWORD if attempted else COOLDOWN
        return ''

    def tp_permanent_delete_execute(self, password, reason, lock_accounts, digest, request_id, location_id=None):
        """Verify the admin password and delete permanently, all or nothing."""
        employees = self.with_context(active_test=False)
        # 1. Rights and session of the caller (never a client flag).
        if not (request and request.session.uid and request.session.uid == self.env.uid):
            raise AccessError(self.env._('Phiên đăng nhập không hợp lệ. Hãy đăng nhập lại rồi thử lại.'))
        if not isinstance(request_id, str) or not _REQUEST_ID.fullmatch(request_id):
            raise UserError(self.env._('Yêu cầu không hợp lệ. Hãy đóng hộp thoại và thử lại.'))
        done = self.env['tp.hr.employee.audit'].sudo().search([('request_id', '=', request_id)])
        if done and done.actor_id != self.env.user:
            raise AccessError(self.env._('Yêu cầu không hợp lệ.'))
        if not done:
            employees._tp_check_permanent_delete_rights()
        elif not (self.env.user.has_group('base.group_system') and self.env.user.has_group('hr.group_hr_manager')):
            raise AccessError(self.env._('Không có quyền xóa vĩnh viễn nhân viên.'))
        if not isinstance(reason, str) or not reason.strip():
            raise UserError(self.env._('Vui lòng nhập lý do xóa vĩnh viễn.'))
        if not isinstance(lock_accounts, bool) or not isinstance(digest, str):
            raise UserError(self.env._('Yêu cầu không hợp lệ. Hãy đóng hộp thoại và thử lại.'))
        if not isinstance(password, str) or not password:
            return {'ok': False, 'field': 'password', 'message': self.env._('Vui lòng nhập mật khẩu của bạn để xác nhận.')}
        # 2. Fresh password of THIS request (no reuse of an earlier verification).
        failure = self._tp_verify_admin_password(password)
        password = None
        if failure:
            return {'ok': False, 'field': 'password', 'message': failure}
        # 3. A retried/double-clicked request that already succeeded.
        if done:
            return {'ok': True, 'already': True, 'count': len(done), 'requestId': request_id}
        reason = reason.strip()
        # 4. Locks, then the plan must equal the preview and committed data.
        employees._tp_delete_lock()
        accounts = employees.mapped('user_id').sudo().with_context(active_test=False)
        if accounts:
            self.env.cr.execute('SELECT id FROM res_users WHERE id IN %s ORDER BY id FOR UPDATE', [tuple(accounts.ids)])
            self.env.invalidate_all()
        employees = employees.exists()
        if len(employees) != len(self):
            raise UserError(self.env._('Có hồ sơ vừa bị xóa bởi phiên khác. Hãy tải lại danh sách.'))
        plan = employees._tp_full_plan()
        stale = self.env._('Dữ liệu đã thay đổi sau khi xem trước (liên kết, tài khoản hoặc quyền mới). Không hồ sơ nào bị xóa. Hãy đóng và mở lại để xem trước.')
        if digest != self._tp_digest(plan):
            raise UserError(stale)
        with self.env.registry.cursor() as current_cr:
            current_cr.execute('SET TRANSACTION READ ONLY')
            current_env = api.Environment(current_cr, self.env.uid, dict(self.env.context))
            current = current_env['hr.employee'].browse(employees.ids).with_context(active_test=False).exists()
            if len(current) != len(employees) or self._tp_digest(current._tp_full_plan()) != digest:
                raise UserError(stale)
        # 5. Blockers of the chosen account option: nothing is deleted.
        problems = []
        for employee in employees.sudo():
            entry = plan['employees'][employee.id]
            account = plan['accounts'].get(str(employee.id)) or {}
            reasons = [f'{label} ({count}): {hint}' for label, count, hint in entry['block']]
            reasons += account.get('block', []) + account.get('lock_block' if lock_accounts else 'keep_block', [])
            if reasons:
                problems.append(f'• {employee.name} ({employee.tp_employee_code or "-"}): ' + ' '.join(reasons))
        if problems:
            raise UserError(self.env._('Không xóa được; không hồ sơ nào bị xóa.\n%(details)s', details='\n'.join(problems)))
        # 6. Accounts (lock and revoke, or keep unchanged).
        account_results = employees._tp_apply_account_choice(plan, lock_accounts, reason)
        # 7. Delete, sweep and audit in the same transaction.
        audit_vals = []
        for employee in employees.sudo():
            entry = plan['employees'][employee.id]
            account = plan['accounts'].get(str(employee.id))
            result = account_results.get(employee.id, {})
            audit_vals.append({
                'action': 'permanent_delete',
                'employee_ref': employee.id,
                'employee_name': employee.name,
                'employee_code': employee.tp_employee_code,
                'source_code': employee.tp_source_code,
                'company_id': employee.company_id.id,
                'reason': reason,
                'request_id': request_id,
                'account_action': result.get('action', 'none'),
                'account_ref': account['user_id'] if account else 0,
                'account_login': account['login'] if account else False,
                'verification': VERIFIED,
                'snapshot': {
                    'department': entry['department'],
                    'job': entry['job'],
                    'active': entry['active'],
                    'import_batch_id': entry['import_batch_id'],
                    'import_lines': entry['import_lines'],
                    'deleted': entry['delete'],
                    'kept': entry['keep'],
                    'revoked': result.get('revoked', {}),
                    'pending_work': account['work'] if account else {},
                    'batch_size': len(employees),
                    'digest': digest,
                },
            })
        employees_ctx = employees
        if location_id:
            employees_ctx = employees.with_context(tp_equipment_return_location_id=location_id)
        partner_results = employees_ctx._tp_permanent_unlink(plan, audit_vals)
        self.env['tp.kd.department.role']._invalidate_scope()
        self.env.transaction.invalidate_ormcache()
        kept_partners = sum(1 for outcome in partner_results.values() if outcome != 'deleted')
        return {'ok': True, 'count': len(audit_vals), 'requestId': request_id,
                'locked': sum(1 for result in account_results.values() if result.get('action') == 'locked'),
                'keptPartners': kept_partners}

    def _tp_apply_account_choice(self, plan, lock_accounts, reason):
        results = {}
        scoped = self.env.ref('tp_kd_workspace.group_scoped_staff', raise_if_not_found=False)
        for employee in self.sudo():
            account = plan['accounts'].get(str(employee.id))
            if not account:
                continue
            if not lock_accounts:
                results[employee.id] = {'action': 'kept'}
                continue
            user = self.env['res.users'].with_context(active_test=False).browse(account['user_id'])
            sources = self._tp_account_sources(user, employee.company_id)
            revoked = {key: records.ids for key, records in sources.items() if records}
            sources['roles'].write({'active': False, 'reason': reason})
            for key in ('assignments', 'grants', 'kd_grants', 'members'):
                sources[key].write({'active': False})
            if scoped and scoped in user.sudo().group_ids:
                user.sudo().write({'group_ids': [Command.unlink(scoped.id)]})
                revoked['groups'] = [scoped.id]
            if user.active:
                # Existing lock: inactive + HR lock + revision bump ends sessions.
                user._tp_set_account_lock(True, reason)
                action = 'locked'
            else:
                user.sudo().write({'tp_hr_locked': True, 'tp_lock_revision': user.sudo().tp_lock_revision + 1})
                action = 'already_locked'
            results[employee.id] = {'action': action, 'revoked': revoked}
        return results
