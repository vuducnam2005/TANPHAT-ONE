# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
"""K1: Survey Equipment Calibration Tracking & Expired/Broken Issuance Block (Mandatory Case #13)."""
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from odoo.addons.tp_equipment.models import quick_action as eq_quick_action
from odoo.addons.tp_equipment.models.common import check_admin, fold_text, is_admin


def _survey_free_domain_tail(env):
    """Exclude survey equipment whose calibration is missing ('unset') or past due ('expired')."""
    today = fields.Date.context_today(env['maintenance.equipment'])
    return [
        '|',
        ('tp_is_survey_gear', '=', False),
        '&',
        '&',
        ('tp_calibration_state', 'not in', ('expired', 'unset')),
        ('tp_calibration_due_date', '!=', False),
        ('tp_calibration_due_date', '>=', today),
    ]


if not getattr(eq_quick_action.free_domain, '_tp_survey_calibration_wrapped', False):
    _orig_free_domain = eq_quick_action.free_domain

    def _survey_guarded_free_domain(env):
        return _orig_free_domain(env) + _survey_free_domain_tail(env)

    _survey_guarded_free_domain._tp_survey_calibration_wrapped = True
    eq_quick_action.free_domain = _survey_guarded_free_domain


class MaintenanceEquipmentSurveyExtension(models.Model):
    _inherit = 'maintenance.equipment'

    tp_is_survey_gear = fields.Boolean(
        string='Thiết bị đo đạc / khảo sát hiện trường',
        default=False,
        index=True,
        help='Tách riêng thiết bị khảo sát cần theo dõi hạn kiểm định/hiệu chuẩn; không làm phức tạp Kho thiết bị văn phòng.',
    )
    tp_calibration_date = fields.Date(string='Ngày kiểm định / hiệu chuẩn gần nhất')
    tp_calibration_due_date = fields.Date(string='Hạn kiểm định tiếp theo', index=True)
    tp_calibration_cert_no = fields.Char(string='Số giấy chứng nhận kiểm định')
    tp_calibration_org = fields.Char(string='Đơn vị kiểm định')
    tp_calibration_state = fields.Selection(
        [
            ('not_applicable', 'Thiết bị văn phòng (không yêu cầu kiểm định)'),
            ('valid', 'Đạt chuẩn / Còn hạn kiểm định'),
            ('expiring_soon', 'Sắp hết hạn kiểm định (≤ 30 ngày)'),
            ('expired', 'Quá hạn kiểm định — Chặn xuất dùng'),
            ('unset', 'Chưa khai hạn kiểm định — Chặn xuất dùng'),
        ],
        compute='_compute_tp_calibration_state',
        store=True,
        string='Tình trạng kiểm định',
    )

    @api.depends('tp_is_survey_gear', 'tp_calibration_due_date')
    def _compute_tp_calibration_state(self):
        today = fields.Date.context_today(self)
        soon = today + timedelta(days=30)
        for eq in self:
            if not eq.tp_is_survey_gear:
                eq.tp_calibration_state = 'not_applicable'
            elif not eq.tp_calibration_due_date:
                eq.tp_calibration_state = 'unset'
            elif eq.tp_calibration_due_date < today:
                eq.tp_calibration_state = 'expired'
            elif eq.tp_calibration_due_date <= soon:
                eq.tp_calibration_state = 'expiring_soon'
            else:
                eq.tp_calibration_state = 'valid'

    @api.model
    def free_domain(self):
        """Model-level entry point mirroring tp_equipment.models.quick_action.free_domain with survey guard."""
        return eq_quick_action.free_domain(self.env)

    @api.depends('tp_is_survey_gear', 'tp_calibration_due_date', 'tp_calibration_state')
    def _compute_tp_quick_flags(self):
        return super()._compute_tp_quick_flags()

    def _tp_assign_problem(self):
        problem = super()._tp_assign_problem()
        if problem:
            return problem
        if self.tp_is_survey_gear:
            today = fields.Date.context_today(self)
            if not self.tp_calibration_due_date or self.tp_calibration_state == 'unset':
                return _(
                    '%(name)s là thiết bị khảo sát chưa khai hạn kiểm định/hiệu chuẩn, không được cấp phát.',
                    name=self.display_name,
                )
            if self.tp_calibration_due_date < today or self.tp_calibration_state == 'expired':
                return _(
                    '%(name)s là thiết bị khảo sát đã quá hạn kiểm định (%(due)s), không được cấp phát.',
                    name=self.display_name,
                    due=self.tp_calibration_due_date.strftime('%d/%m/%Y'),
                )
        return False

    @api.model
    def tp_survey_workspace_data(self, params=None):
        """Permission-scoped list, KPI summary & pagination for /app/thiet-bi/khao-sat (DEC-044)."""
        self.browse().check_access('read')
        params = params or {}
        base_dom = [
            ('tp_is_survey_gear', '=', True),
            ('company_id', 'in', self.env.companies.ids),
        ]
        all_gear = self.search(base_dom, order='tp_code asc, id desc')
        today = fields.Date.context_today(self)
        soon = today + timedelta(days=30)

        def _live_state(rec):
            if not rec.tp_calibration_due_date:
                return 'unset'
            if rec.tp_calibration_due_date < today:
                return 'expired'
            if rec.tp_calibration_due_date <= soon:
                return 'expiring_soon'
            return 'valid'

        kpis = {'total': len(all_gear), 'valid': 0, 'expiring_soon': 0, 'expired': 0, 'unset': 0}
        for rec in all_gear:
            st = _live_state(rec)
            kpis[st] = kpis.get(st, 0) + 1

        q = (params.get('search') or '').strip()
        state_filter = (params.get('calibration_state') or 'all').strip()

        filtered = all_gear
        if state_filter in ('valid', 'expiring_soon', 'expired', 'unset'):
            filtered = filtered.filtered(lambda r: _live_state(r) == state_filter)

        if q:
            needle = fold_text(q)
            q_low = q.lower()
            filtered = filtered.filtered(
                lambda r: any(
                    q_low in (val or '').lower() or (needle and needle in fold_text(val or ''))
                    for val in (r.name, r.tp_code, r.serial_no)
                ),
            )

        try:
            page_size = int(params.get('page_size') or 20)
        except (TypeError, ValueError):
            page_size = 20
        if page_size not in (10, 20, 50, 100):
            page_size = 20
        try:
            page = max(1, int(params.get('page') or 1))
        except (TypeError, ValueError):
            page = 1

        total_filtered = len(filtered)
        max_page = max(1, (total_filtered + page_size - 1) // page_size)
        if page > max_page:
            page = max_page
        offset = (page - 1) * page_size
        page_records = filtered[offset: offset + page_size]

        items = [{
            'id': r.id,
            'tp_code': r.tp_code or f'#{r.id}',
            'name': r.name or '',
            'serial_no': r.serial_no or '',
            'tp_technical_state': r.tp_technical_state,
            'tp_custody': r.tp_custody,
            'tp_calibration_date': r.tp_calibration_date.isoformat() if r.tp_calibration_date else '',
            'tp_calibration_date_vn': r.tp_calibration_date.strftime('%d/%m/%Y') if r.tp_calibration_date else '',
            'tp_calibration_due_date': r.tp_calibration_due_date.isoformat() if r.tp_calibration_due_date else '',
            'tp_calibration_due_date_vn': r.tp_calibration_due_date.strftime('%d/%m/%Y') if r.tp_calibration_due_date else '',
            'tp_calibration_cert_no': r.tp_calibration_cert_no or '',
            'tp_calibration_org': r.tp_calibration_org or '',
            'tp_calibration_state': _live_state(r),
        } for r in page_records]

        return {
            'items': items,
            'total_filtered': total_filtered,
            'page': page,
            'page_size': page_size,
            'total_pages': max_page,
            'kpis': kpis,
            'can_manage': bool(is_admin(self.env)),
        }

    @api.model
    def tp_save_survey_calibration(self, equipment_id, payload=None):
        """Guarded calibration update modal RPC for equipment administrators."""
        eq = self.browse(int(equipment_id or 0)).exists()
        if not eq:
            raise UserError(_('Không tìm thấy thiết bị khảo sát cần cập nhật.'))
        check_admin(self.env, eq)
        payload = payload or {}

        due_raw = (payload.get('tp_calibration_due_date') or '').strip()
        date_raw = (payload.get('tp_calibration_date') or '').strip()
        if not due_raw:
            raise ValidationError(_('Vui lòng nhập Hạn kiểm định tiếp theo.'))
        try:
            due_dt = fields.Date.to_date(due_raw)
        except Exception as exc:
            raise ValidationError(_('Hạn kiểm định tiếp theo không đúng định dạng ngày.')) from exc

        cal_dt = False
        if date_raw:
            try:
                cal_dt = fields.Date.to_date(date_raw)
            except Exception as exc:
                raise ValidationError(_('Ngày kiểm định gần nhất không đúng định dạng ngày.')) from exc
            if due_dt < cal_dt:
                raise ValidationError(_('Hạn kiểm định tiếp theo phải lớn hơn hoặc bằng Ngày kiểm định gần nhất.'))

        eq.write({
            'tp_is_survey_gear': True,
            'tp_calibration_date': cal_dt,
            'tp_calibration_due_date': due_dt,
            'tp_calibration_cert_no': (payload.get('tp_calibration_cert_no') or '').strip() or False,
            'tp_calibration_org': (payload.get('tp_calibration_org') or '').strip() or False,
        })
        return {
            'id': eq.id,
            'tp_calibration_state': eq.tp_calibration_state,
            'tp_can_assign': eq.tp_can_assign,
        }


class TpEquipmentMoveSurveyGuard(models.Model):
    _inherit = 'tp.equipment.move'

    def _tp_check(self, strict=False):
        """Block issuing/assigning/loaning survey equipment that is broken or has expired calibration (Mandatory Case #13)."""
        issues = super()._tp_check(strict=False)
        to_custody = self._tp_target_custody()
        today = fields.Date.context_today(self)

        if self.move_type not in ('opening', 'adjust', 'reversal') and to_custody in ('employee', 'loan', 'department', 'location'):
            for line in self.line_ids.filtered('equipment_id'):
                eq = line.equipment_id
                if eq.tp_is_survey_gear:
                    if not eq.tp_calibration_due_date:
                        issues.append((
                            'error',
                            line,
                            _('%(name)s là thiết bị khảo sát chưa có hạn kiểm định/hiệu chuẩn hợp lệ, không được xuất dùng.', name=eq.display_name),
                        ))
                    elif eq.tp_calibration_due_date < today:
                        issues.append((
                            'error',
                            line,
                            _(
                                '%(name)s là thiết bị khảo sát đã quá hạn kiểm định (%(due)s), không được bàn giao / cho mượn hiện trường.',
                                name=eq.display_name,
                                due=eq.tp_calibration_due_date.strftime('%d/%m/%Y'),
                            ),
                        ))

        if strict and any(level == 'error' for level, _l, _m in issues):
            raise UserError('\n'.join(msg for level, _l, msg in issues if level == 'error'))
        return issues
