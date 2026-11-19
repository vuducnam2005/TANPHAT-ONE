"""Full System Administrator provisioning with Original-Admin-only authority (DEC-053/054).

- Original Admin (`_tp_is_original_admin`): backed by `tp_admin_delegation.group_original_admin`
  (never implied by `base.group_system`), active, internal, and without an active grant ledger row.
  Only an Original Admin may grant or revoke admin rights or alter protected security sources.
- Granted Full Admin (`_tp_is_granted_admin`): holds an active `tp.admin.delegation` ledger row and
  receives the managed role group `tp_admin_delegation.group_full_admin`, granting full system and
  business administration across all departments (including their own department), without changing
  their HR job title or department, and without authority to grant or revoke admin rights.
"""
import logging

from odoo import Command, api, fields, models
from odoo.exceptions import AccessError, UserError
from odoo.fields import Domain

from odoo.addons.base.models.res_users import check_identity

_logger = logging.getLogger(__name__)

_LEDGER = object()
_MIGRATE = object()
_ADMIN_PROVISION = object()
LOCK_NAMESPACE = 761118

CORE_ADMIN_GROUP_XMLIDS = (
    'base.group_system',
    'tp_core.group_manager',
    'hr.group_hr_manager',
    'project.group_project_manager',
    'sales_team.group_sale_manager',
    'hr_timesheet.group_timesheet_manager',
    'maintenance.group_equipment_manager',
)
OPTIONAL_ADMIN_GROUP_XMLIDS = (
    'account.group_account_manager',
    'spreadsheet_dashboard.group_dashboard_manager',
    'hr_expense.group_hr_expense_manager',
    'product.group_product_manager',
)
SYSTEM_PROTECTED_USER_XMLIDS = (
    'base.user_root',
    'base.user_admin',
    'base.public_user',
    'base.template_portal_user',
    'base.template_portal_user_id',
    'base.default_user',
)

ORIGINAL_ADMIN_LABEL = 'Admin gốc'
GRANTED_ADMIN_LABEL = 'Admin ủy quyền'
BUSINESS_USER_LABEL = 'Nhân viên'
ORIGINAL_SCOPE_TEXT = (
    'Quản trị viên gốc toàn hệ thống: quản trị mọi phòng ban và ứng dụng; '
    'được cấp và thu hồi quyền quản trị viên.'
)
GRANTED_SCOPE_TEXT = (
    'Quản trị viên toàn hệ thống: toàn quyền quản trị mọi phòng ban (gồm cả phòng của chính mình) '
    'như quản trị hiện tại; giữ nguyên chức danh nhân sự; không được cấp hoặc thu hồi quyền quản trị viên.'
)


def _system_protected_users(env):
    users = env['res.users'].sudo().browse()
    for xmlid in SYSTEM_PROTECTED_USER_XMLIDS:
        ref = env.ref(xmlid, raise_if_not_found=False)
        if ref and ref._name == 'res.users':
            users |= ref.sudo()
    return users


def _sync_full_admin_group_profile(env):
    """Ensure `group_full_admin` implies all installed admin/manager groups of the current admin."""
    full_group = env.ref('tp_admin_delegation.group_full_admin', raise_if_not_found=False)
    if not full_group:
        return env['res.groups']
    full_group = full_group.sudo()
    target_groups = env['res.groups'].sudo().browse()
    for xmlid in CORE_ADMIN_GROUP_XMLIDS + OPTIONAL_ADMIN_GROUP_XMLIDS:
        grp = env.ref(xmlid, raise_if_not_found=False)
        if grp and grp._name == 'res.groups':
            target_groups |= grp.sudo()
    missing = target_groups - full_group.implied_ids
    if missing:
        full_group.with_context(_tp_admin_migrate=_MIGRATE).write({
            'implied_ids': [Command.link(gid) for gid in missing.ids],
        })
    orig_group = env.ref('tp_admin_delegation.group_original_admin', raise_if_not_found=False)
    import_mod_access = env.ref('base_import_module.access_base_import_module', raise_if_not_found=False)
    if orig_group and import_mod_access and import_mod_access._name == 'ir.access':
        if import_mod_access.sudo().group_id != orig_group.sudo():
            import_mod_access.sudo().with_context(_tp_admin_migrate=_MIGRATE).write({
                'group_id': orig_group.id,
            })
    return full_group


class DelegationUser(models.Model):
    _inherit = 'res.users'

    tp_admin_scope_revision = fields.Integer(default=0, readonly=True, copy=False)

    def _get_session_token_fields(self):
        # Granting or revoking full admin immediately invalidates pre-existing browser
        # sessions/tabs so stale session_info (isSystem / menus) cannot keep running.
        return super()._get_session_token_fields() | {'tp_admin_scope_revision'}

    def _tp_has_live_admin_grant(self, company=None, lock=False):
        """Read `tp_admin_delegation` directly via SQL, independent of `base.group_system`."""
        self.ensure_one()
        if lock and not self.env.cr.readonly:
            self._tp_admin_lock()
        if company is not None:
            if not company.ids:
                return False
            self.env.cr.execute(
                "SELECT 1 FROM tp_admin_delegation WHERE user_id=%s AND company_id IN %s AND state='active' LIMIT 1",
                [self.id, tuple(company.ids)],
            )
        else:
            self.env.cr.execute(
                "SELECT 1 FROM tp_admin_delegation WHERE user_id=%s AND state='active' LIMIT 1",
                [self.id],
            )
        return bool(self.env.cr.fetchone())

    def _tp_is_original_admin(self):
        """True only for an active internal Original Administrator (DEC-054)."""
        self.ensure_one()
        user = self.sudo().with_context(active_test=False)
        if not user.active or user.share or not user.has_group('base.group_system'):
            return False
        if user._tp_has_live_admin_grant():
            return False
        return user.has_group('tp_admin_delegation.group_original_admin')

    def _tp_is_granted_admin(self, company=None, lock=False):
        """True for an active internal user holding a live Full Admin grant."""
        self.ensure_one()
        user = self.sudo().with_context(active_test=False)
        if not user.active or user.share or not user.has_group('base.group_system'):
            return False
        allowed = user.company_ids & self.env.companies
        if company is not None:
            allowed &= company
        if not allowed:
            return False
        return user._tp_has_live_admin_grant(company=allowed, lock=lock)

    def _tp_is_main_admin(self):
        """Full system business administration (both Original Admin and Granted Full Admin)."""
        self.ensure_one()
        user = self.sudo().with_context(active_test=False)
        return bool(user.active and not user.share and user.has_group('base.group_system'))

    def _tp_admin_lock(self, exclusive=False):
        """Serialize grant/revoke and scope transitions across concurrent transactions."""
        self.ensure_one()
        function = 'pg_advisory_xact_lock' if exclusive else 'pg_advisory_xact_lock_shared'
        self.env.cr.execute(f'SELECT {function}(%s, %s)', [LOCK_NAMESPACE, self.id])
        if exclusive:
            self.env.cr.execute(
                'UPDATE res_users SET tp_admin_scope_revision=COALESCE(tp_admin_scope_revision, 0)+1 WHERE id=%s',
                [self.id],
            )
        self.env.cr.execute(
            'SELECT id FROM tp_admin_delegation WHERE user_id=%s ORDER BY id FOR SHARE',
            [self.id],
        )
        self.env.cr.execute('SELECT id FROM res_users WHERE id=%s FOR SHARE', [self.id])
        self.invalidate_recordset(['active', 'share', 'company_ids', 'group_ids', 'all_group_ids', 'tp_admin_scope_revision'])

    def _tp_has_admin_delegation(self, company=None, lock=False):
        """Legacy limited-department delegation is retired by DEC-053 (all grants are full admin)."""
        self.ensure_one()
        if lock and not self.env.cr.readonly:
            self._tp_admin_lock()
        return False

    def _tp_delegation_scope(self, company):
        self.ensure_one()
        return self.env['hr.department'].sudo().browse(), False

    def _tp_delegation_departments(self, company=None):
        self.ensure_one()
        return self.env['hr.department'].sudo().browse()

    def _tp_delegated_other_department(self, company, departments, lock=False):
        self.ensure_one()
        return False

    def _tp_delegation_domain(self, company_field='company_id', department_field='department_id'):
        self.ensure_one()
        return Domain.FALSE

    @api.model
    def get_tp_admin_capabilities(self):
        """Caller capability summary: separates full business admin from original-admin provisioning."""
        user = self.env['res.users'].browse(self.env.uid)
        original = user._tp_is_original_admin()
        granted = not original and user._tp_is_granted_admin()
        full_admin = user._tp_is_main_admin()
        return {
            'level': 'main' if original else 'delegated' if granted else 'business',
            'is_original_admin': original,
            'is_full_admin': full_admin,
            'can_manage_delegation': original,
            'delegated': False,
            'scope': ORIGINAL_SCOPE_TEXT if original else GRANTED_SCOPE_TEXT if granted else '',
            'department_ids': [],
        }


class AdminDelegation(models.Model):
    _name = 'tp.admin.delegation'
    _description = 'Sổ cấp và thu hồi quyền quản trị toàn hệ thống'
    _order = 'id desc'

    user_id = fields.Many2one('res.users', string='Tài khoản', required=True, ondelete='restrict', index=True, readonly=True)
    company_id = fields.Many2one('res.company', string='Công ty', required=True, ondelete='restrict', index=True, readonly=True)
    state = fields.Selection(
        [('active', 'Đang hiệu lực (Quản trị viên)'), ('revoked', 'Đã thu hồi')],
        string='Trạng thái',
        required=True,
        readonly=True,
    )
    granted_by_id = fields.Many2one('res.users', string='Người cấp quyền', required=True, ondelete='restrict', readonly=True)
    granted_at = fields.Datetime(string='Thời điểm cấp quyền', required=True, readonly=True)
    grant_reason = fields.Text(string='Lý do cấp quyền', required=True, readonly=True)
    migrated_at = fields.Datetime(string='Thời điểm chuẩn hóa toàn hệ thống', readonly=True)
    revoked_by_id = fields.Many2one('res.users', string='Người thu hồi', ondelete='restrict', readonly=True)
    revoked_at = fields.Datetime(string='Thời điểm thu hồi', readonly=True)
    revoke_reason = fields.Text(string='Lý do thu hồi', readonly=True)

    _one_live = models.UniqueIndex(
        '(user_id, company_id) WHERE state=\'active\'',
        'Tài khoản đã được cấp quyền quản trị tại công ty này.',
    )
    _reason_required = models.Constraint('CHECK(length(btrim(grant_reason)) > 0)', 'Cần lý do cấp quyền.')
    _revoked_audit = models.Constraint(
        "CHECK(state != 'revoked' OR (revoked_by_id IS NOT NULL AND revoked_at IS NOT NULL AND length(btrim(revoke_reason)) > 0))",
        'Thu hồi phải giữ người thực hiện, thời điểm và lý do.',
    )

    @api.model_create_multi
    def create(self, vals_list):
        if self.env.context.get('_tp_delegation_ledger') is not _LEDGER:
            raise AccessError(self.env._('Chỉ Quản trị gốc được cấp quyền quản trị qua thao tác đã xác thực.'))
        return super().create(vals_list)

    def write(self, vals):
        if (self.env.context.get('_tp_admin_migrate') is _MIGRATE
                and set(vals) == {'migrated_at'}
                and all(row.state == 'active' for row in self)):
            return super().write(vals)
        if (self.env.context.get('_tp_delegation_ledger') is not _LEDGER
                or set(vals) != {'state', 'revoked_by_id', 'revoked_at', 'revoke_reason'}
                or vals.get('state') != 'revoked'
                or any(row.state != 'active' for row in self)):
            raise AccessError(self.env._('Sổ cấp quyền quản trị không được sửa; chỉ Quản trị gốc được thu hồi qua thao tác đã xác thực.'))
        return super().write(vals)

    def unlink(self):
        raise AccessError(self.env._('Giữ nguyên lịch sử cấp và thu hồi quyền quản trị.'))

    @api.model
    def _invalidate_security_and_sessions(self):
        self.env.flush_all()
        self.env.invalidate_all()
        self.env['ir.access']._clear_caches()
        self.env.transaction.invalidate_access_cache()
        self.env.transaction.invalidate_ormcache()

    @api.model
    def _change(self, user, company, operation, reason):
        # Always authenticate the true caller (env.uid), never trusting env.su or client context.
        actor = self.env['res.users'].browse(self.env.uid)
        if not actor.exists() or not actor._tp_is_original_admin():
            raise AccessError(self.env._('Chỉ Quản trị gốc được cấp hoặc thu hồi quyền quản trị viên.'))
        if operation not in ('grant', 'revoke') or not isinstance(reason, str) or not reason.strip():
            raise UserError(self.env._('Chọn thao tác và nhập lý do.'))
        if not user or not company or len(user) != 1 or len(company) != 1:
            raise AccessError(self.env._('Tài khoản hoặc công ty không hợp lệ.'))

        # Lock actor and target in deterministic order, then re-verify actor authority inside the transaction.
        for locked_uid in sorted({actor.id, user.id}):
            self.env['res.users'].browse(locked_uid)._tp_admin_lock(exclusive=(locked_uid == user.id))
        self.env.cr.execute(
            'SELECT id FROM res_users WHERE id IN %s ORDER BY id FOR UPDATE',
            [tuple(sorted({actor.id, user.id}))],
        )
        self.env.cr.execute(
            'SELECT id FROM tp_admin_delegation WHERE user_id=%s ORDER BY id FOR UPDATE',
            [user.id],
        )
        actor.invalidate_recordset()
        user.invalidate_recordset()
        if not actor._tp_is_original_admin():
            raise AccessError(self.env._('Quyền Quản trị gốc của bạn không còn hiệu lực.'))

        target = user.sudo().with_context(active_test=False)
        actor_companies = actor.sudo().company_ids & self.env.companies
        if company not in actor_companies or company not in target.company_ids:
            raise AccessError(self.env._('Tài khoản hoặc công ty không thuộc phạm vi quản lý.'))
        if set(target.company_ids.ids) - set(actor.sudo().company_ids.ids):
            raise AccessError(self.env._('Tài khoản đích có công ty ngoài phạm vi của bạn.'))

        protected = _system_protected_users(self.env)
        if target.id == actor.id or target in protected or target._tp_is_original_admin():
            raise AccessError(self.env._('Không áp dụng cấp/thu quản trị viên lên tài khoản hệ thống hoặc Quản trị gốc.'))

        full_group = _sync_full_admin_group_profile(self.env)
        orig_group = self.env.ref('tp_admin_delegation.group_original_admin').sudo()
        group_system = self.env.ref('base.group_system').sudo()
        group_erp = self.env.ref('base.group_erp_manager').sudo()

        ledger = self.sudo().with_context(_tp_delegation_ledger=_LEDGER)
        current = ledger.search([
            ('user_id', '=', target.id),
            ('company_id', '=', company.id),
            ('state', '=', 'active'),
        ])
        now = fields.Datetime.now()
        clean_reason = reason.strip()

        if operation == 'grant':
            if current:
                raise UserError(self.env._('Tài khoản đã đang giữ quyền quản trị viên.'))
            if target.share or not target.active or not target.has_group('base.group_user'):
                raise AccessError(self.env._('Chỉ cấp quyền quản trị cho tài khoản nhân sự nội bộ đang mở.'))
            if (group_system in target.all_group_ids or group_erp in target.all_group_ids) and full_group not in target.group_ids:
                raise UserError(self.env._('Tài khoản đang có quyền quản trị hệ thống từ nguồn nhóm khác; hãy kiểm tra lại trước khi cấp.'))
            ledger.create({
                'user_id': target.id,
                'company_id': company.id,
                'state': 'active',
                'granted_by_id': actor.id,
                'granted_at': now,
                'migrated_at': now,
                'grant_reason': clean_reason,
            })
            if full_group not in target.group_ids:
                target.with_context(_tp_admin_provision=_ADMIN_PROVISION).write({
                    'group_ids': [Command.link(full_group.id)],
                })
        else:
            if not current:
                raise UserError(self.env._('Không có quyền quản trị viên đang hiệu lực để thu hồi.'))
            current.write({
                'state': 'revoked',
                'revoked_by_id': actor.id,
                'revoked_at': now,
                'revoke_reason': clean_reason,
            })
            remaining_live = ledger.search_count([
                ('user_id', '=', target.id),
                ('state', '=', 'active'),
            ])
            if not remaining_live and full_group in target.group_ids:
                target.with_context(_tp_admin_provision=_ADMIN_PROVISION).write({
                    'group_ids': [Command.unlink(full_group.id)],
                })
            self._invalidate_security_and_sessions()
            target.invalidate_recordset()
            # Never report a successful revocation if the user still retains admin privileges
            # from another group or active grant.
            still_admin = (
                target.has_group('base.group_system')
                or target.has_group('base.group_erp_manager')
                or orig_group in target.all_group_ids
                or full_group in target.all_group_ids
            )
            if still_admin:
                remaining_sources = (target.group_ids.filtered(
                    lambda g: bool(g.all_implied_ids & (group_system | group_erp | orig_group | full_group)),
                )).mapped('display_name')
                if remaining_live:
                    raise UserError(self.env._(
                        'Tài khoản vẫn còn quyền quản trị hiệu lực ở công ty khác; chưa thể hoàn tất thu hồi toàn hệ thống.',
                    ))
                raise UserError(self.env._(
                    'Không thể xác nhận thu hồi vì tài khoản vẫn còn quyền quản trị từ nhóm: %(groups)s. '
                    'Vui lòng gỡ nguồn nhóm quản trị trực tiếp trước.',
                    groups=', '.join(remaining_sources) or 'base.group_system',
                ))

        self._invalidate_security_and_sessions()
        _logger.info(
            'ADMIN-FULL-001 %s executed by original_admin uid=%s on target uid=%s company=%s',
            operation, actor.id, target.id, company.id,
        )
        return True

    @api.model
    def _migrate_admin_full_001(self):
        """Idempotently seed Original Admin and upgrade active grants to Full System Admin."""
        full_group = _sync_full_admin_group_profile(self.env)
        orig_group = self.env.ref('tp_admin_delegation.group_original_admin', raise_if_not_found=False)
        group_system = self.env.ref('base.group_system', raise_if_not_found=False)
        if not full_group or not orig_group or not group_system:
            return {}
        orig_group = orig_group.sudo()
        group_system = group_system.sudo()

        # 1. Seed group_original_admin on base.user_admin and any pre-existing active non-share
        #    system admin that was never created through tp.admin.delegation.
        non_human = self.env['res.users'].sudo().browse()
        for xmlid in ('base.user_root', 'base.public_user', 'base.template_portal_user',
                      'base.template_portal_user_id', 'base.default_user'):
            ref = self.env.ref(xmlid, raise_if_not_found=False)
            if ref and ref._name == 'res.users':
                non_human |= ref.sudo()

        self.env.cr.execute('SELECT DISTINCT user_id FROM tp_admin_delegation')
        ever_delegated_uids = {row[0] for row in self.env.cr.fetchall()}

        candidates = self.env['res.users'].sudo().with_context(active_test=False).browse()
        user_admin = self.env.ref('base.user_admin', raise_if_not_found=False)
        if user_admin and not user_admin.sudo().share and user_admin.id not in ever_delegated_uids:
            candidates |= user_admin.sudo()
        existing_sys_users = self.env['res.users'].sudo().search([
            ('active', '=', True),
            ('share', '=', False),
            ('id', 'not in', list(ever_delegated_uids | set(non_human.ids))),
        ])
        for sys_user in existing_sys_users:
            if group_system in sys_user.all_group_ids and full_group not in sys_user.group_ids:
                candidates |= sys_user

        for orig_user in candidates:
            if orig_group not in orig_user.group_ids:
                orig_user.with_context(_tp_admin_migrate=_MIGRATE).write({
                    'group_ids': [Command.link(orig_group.id)],
                })

        # 2. Upgrade every active grant of an active internal non-original-admin user to group_full_admin.
        active_rows = self.sudo().search([('state', '=', 'active')], order='id')
        now = fields.Datetime.now()
        migrated_uids = []
        already_uids = []
        skipped_uids = []
        protected = _system_protected_users(self.env)

        for target in active_rows.mapped('user_id'):
            target_sudo = target.sudo().with_context(active_test=False)
            if (not target_sudo.active or target_sudo.share or not target_sudo.has_group('base.group_user')
                    or target_sudo in protected or orig_group in target_sudo.group_ids):
                skipped_uids.append(target_sudo.id)
                continue
            user_rows = active_rows.filtered(lambda r: r.user_id.id == target_sudo.id)
            changed = False
            if full_group not in target_sudo.group_ids:
                target_sudo.with_context(_tp_admin_provision=_ADMIN_PROVISION).write({
                    'group_ids': [Command.link(full_group.id)],
                })
                self.env.cr.execute(
                    'UPDATE res_users SET tp_admin_scope_revision=COALESCE(tp_admin_scope_revision, 0)+1 WHERE id=%s',
                    [target_sudo.id],
                )
                migrated_uids.append(target_sudo.id)
                changed = True
            else:
                already_uids.append(target_sudo.id)
            unmarked = user_rows.filtered(lambda r: not r.migrated_at)
            if unmarked:
                unmarked.with_context(_tp_admin_migrate=_MIGRATE).write({'migrated_at': now})
                changed = True
            if changed:
                _logger.info('ADMIN-FULL-001 migrated active grant user uid=%s to group_full_admin', target_sudo.id)

        self._invalidate_security_and_sessions()
        return {
            'original_admin_ids': sorted(candidates.ids),
            'migrated_user_ids': sorted(migrated_uids),
            'already_full_user_ids': sorted(already_uids),
            'skipped_user_ids': sorted(skipped_uids),
        }


class AdminEmployee(models.Model):
    _inherit = 'hr.employee'

    tp_admin_level = fields.Selection(
        [
            ('business', BUSINESS_USER_LABEL),
            ('delegated', GRANTED_ADMIN_LABEL),
            ('main', ORIGINAL_ADMIN_LABEL),
        ],
        compute='_compute_tp_admin_level',
        string='Loại tài khoản',
    )
    tp_admin_scope = fields.Text(compute='_compute_tp_admin_level', string='Phạm vi quản trị')
    tp_can_manage_delegation = fields.Boolean(compute='_compute_tp_admin_level')

    @api.depends('user_id', 'company_id')
    @api.depends_context('uid', 'allowed_company_ids')
    def _compute_tp_admin_level(self):
        from .guards import (  # noqa: PLC0415 - guard imports delegation sentinels
            account_actor_uid,
            account_target_kind,
        )

        caller = self.env['res.users'].browse(account_actor_uid(self.env))
        can_manage = bool(caller.exists() and caller._tp_is_original_admin())
        for employee in self:
            user = employee.sudo().with_context(active_test=False).user_id
            kind = account_target_kind(user) if user else 'employee'
            if kind == 'original_admin':
                employee.tp_admin_level = 'main'
                employee.tp_admin_scope = ORIGINAL_SCOPE_TEXT
            elif kind == 'granted_admin':
                employee.tp_admin_level = 'delegated'
                employee.tp_admin_scope = GRANTED_SCOPE_TEXT
            else:
                employee.tp_admin_level = 'business'
                employee.tp_admin_scope = 'Theo vai trò và phân công nghiệp vụ.'
            employee.tp_can_manage_delegation = can_manage

    def _tp_admin_wizard_action(self, operation):
        self.ensure_one()
        caller = self.env['res.users'].browse(self.env.uid)
        if not caller.exists() or not caller._tp_is_original_admin():
            raise AccessError(self.env._('Chỉ Quản trị gốc được cấp hoặc thu hồi quyền quản trị viên.'))
        self.check_access('read')
        if not self.user_id:
            raise UserError(self.env._('Cần tạo tài khoản cá nhân trước khi cấp quyền quản trị viên.'))
        wizard = self.env['tp.admin.delegation.wizard'].create({'employee_id': self.id, 'operation': operation})
        return {
            'type': 'ir.actions.act_window',
            'res_model': wizard._name,
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
            'name': 'Cấp quyền quản trị viên' if operation == 'grant' else 'Thu hồi quyền quản trị viên',
        }

    def action_tp_grant_admin(self):
        return self._tp_admin_wizard_action('grant')

    def action_tp_revoke_admin(self):
        return self._tp_admin_wizard_action('revoke')


class AdminDelegationWizard(models.TransientModel):
    _name = 'tp.admin.delegation.wizard'
    _description = 'Cấp hoặc thu hồi quyền quản trị viên toàn hệ thống'

    employee_id = fields.Many2one('hr.employee', required=True, readonly=True, string='Nhân viên')
    user_id = fields.Many2one(related='employee_id.user_id', readonly=True, string='Tài khoản')
    expected_user_id = fields.Many2one('res.users', readonly=True)
    company_id = fields.Many2one(related='employee_id.company_id', readonly=True, string='Công ty')
    operation = fields.Selection(
        [('grant', 'Cấp quyền quản trị viên'), ('revoke', 'Thu hồi quyền quản trị viên')],
        required=True,
        string='Thao tác',
    )
    reason = fields.Text(string='Lý do')
    scope_preview = fields.Text(compute='_compute_preview', string='Phạm vi áp dụng')

    @api.model_create_multi
    def create(self, vals_list):
        caller = self.env['res.users'].browse(self.env.uid)
        if not caller.exists() or not caller._tp_is_original_admin():
            raise AccessError(self.env._('Chỉ Quản trị gốc được cấp hoặc thu hồi quyền quản trị viên.'))
        for vals in vals_list:
            employee = self.env['hr.employee'].browse(vals.get('employee_id')).exists()
            employee.check_access('read')
            vals['expected_user_id'] = employee.user_id.id
        return super().create(vals_list)

    def write(self, vals):
        caller = self.env['res.users'].browse(self.env.uid)
        if not caller.exists() or not caller._tp_is_original_admin():
            raise AccessError(self.env._('Chỉ Quản trị gốc được cấp hoặc thu hồi quyền quản trị viên.'))
        if set(vals) & {'employee_id', 'expected_user_id', 'operation'}:
            raise AccessError(self.env._('Tài khoản đích và thao tác đã chốt khi mở hộp thoại; hãy mở lại để chọn lại.'))
        return super().write(vals)

    @api.depends('employee_id', 'operation')
    def _compute_preview(self):
        for wizard in self:
            emp = wizard.employee_id.sudo()
            dept_name = emp.department_id.name or 'Chưa khai báo'
            job_name = emp.job_id.name or emp.job_title or 'Chưa khai báo'
            if wizard.operation == 'grant':
                wizard.scope_preview = (
                    f'Hồ sơ hiện tại: {dept_name} — {job_name} (giữ nguyên phòng ban và chức vụ nhân sự).\n'
                    'Quyền sau khi cấp: Quản trị viên toàn hệ thống trên mọi phòng ban (gồm cả phòng của chính mình), '
                    'nhân sự, KH-KD, dự án, Kho, Báo cáo, chấm công, Cài đặt và Ứng dụng như quản trị hiện tại.\n'
                    'Ngoại lệ (DEC-054): không được cấp hoặc thu hồi quyền quản trị viên cho bất kỳ ai.'
                )
            else:
                wizard.scope_preview = (
                    f'Hồ sơ hiện tại: {dept_name} — {job_name} (giữ nguyên phòng ban, chức vụ và vai trò nghiệp vụ hợp lệ).\n'
                    'Quyền sau khi thu hồi: gỡ hoàn toàn nhóm Quản trị viên toàn hệ thống và các quyền quản trị kế thừa; '
                    'các phiên đăng nhập và tab đang mở của tài khoản này sẽ bị kiểm tra lại ngay lập tức.'
                )

    @check_identity
    def action_apply(self):
        self.ensure_one()
        caller = self.env['res.users'].browse(self.env.uid)
        if not caller.exists() or not caller._tp_is_original_admin():
            raise AccessError(self.env._('Chỉ Quản trị gốc được cấp hoặc thu hồi quyền quản trị viên.'))
        if not (self.reason or '').strip():
            raise UserError(self.env._('Nhập lý do cấp hoặc thu hồi quyền quản trị viên.'))
        self.employee_id.check_access('read')
        self.env.cr.execute('SELECT id FROM hr_employee WHERE id=%s FOR UPDATE', [self.employee_id.id])
        self.employee_id.invalidate_recordset(['user_id', 'company_id'])
        self.invalidate_recordset(['user_id', 'company_id'])
        if not self.user_id or self.user_id != self.expected_user_id:
            raise UserError(self.env._('Tài khoản đã đổi. Vui lòng mở lại hộp thoại.'))
        with self.env.cr.savepoint():
            self.env['tp.admin.delegation']._change(self.user_id, self.company_id, self.operation, self.reason)
            self.employee_id.message_post(
                body=self.env._(
                    '%(action)s cho %(login)s. Lý do: %(reason)s',
                    action=(
                        'Đã cấp quyền Quản trị viên toàn hệ thống'
                        if self.operation == 'grant'
                        else 'Đã thu hồi quyền Quản trị viên toàn hệ thống'
                    ),
                    login=self.user_id.login,
                    reason=self.reason.strip(),
                ),
            )
        return {'type': 'ir.actions.act_window_close'}
