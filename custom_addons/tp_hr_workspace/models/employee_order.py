"""Department-scoped custom ordering for TP HR Employee List (HR-EMPLOYEE-ORDER)."""
from odoo import SUPERUSER_ID, api, fields, models
from odoo.exceptions import AccessError, ValidationError

_TP_REORDER = object()
ADVISORY_LOCK_NS_EMP_ORDER = 761101


def is_trusted_employee_reorder(env, vals: dict | None = None) -> bool:
    """Return True only when called inside tp_reorder_in_department / internal sequence assignment."""
    if env.context.get('_tp_employee_reorder') is not _TP_REORDER:
        return False
    return not (vals is not None and set(vals) - {'sequence'})


def backfill_employee_department_sequence(cr) -> int:
    """Idempotently initialize distinct 10, 20, 30... sequence values per (company, department, active).

    Preserves existing custom order when sequences are already distinct, and falls back to
    (tp_employee_code ASC NULLS LAST, id ASC) when rows still share the default sequence.
    """
    cr.execute(
        """
        WITH partitions_needing_init AS (
            SELECT e.company_id,
                   COALESCE(v.department_id, 0) AS dept_key,
                   e.active
              FROM hr_employee e
              LEFT JOIN hr_version v ON v.id = e.current_version_id
             GROUP BY e.company_id, COALESCE(v.department_id, 0), e.active
            HAVING BOOL_OR(e.sequence IS NULL)
                OR (COUNT(*) > 1 AND COUNT(DISTINCT e.sequence) < COUNT(*))
        ),
        ranked AS (
            SELECT e.id,
                   ROW_NUMBER() OVER (
                       PARTITION BY e.company_id, COALESCE(v.department_id, 0), e.active
                       ORDER BY COALESCE(e.sequence, 10) ASC,
                                e.tp_employee_code ASC NULLS LAST,
                                e.id ASC
                   ) * 10 AS new_seq
              FROM hr_employee e
              LEFT JOIN hr_version v ON v.id = e.current_version_id
              JOIN partitions_needing_init p
                ON p.company_id = e.company_id
               AND p.dept_key = COALESCE(v.department_id, 0)
               AND p.active = e.active
        )
        UPDATE hr_employee emp
           SET sequence = ranked.new_seq
          FROM ranked
         WHERE emp.id = ranked.id
           AND emp.sequence IS DISTINCT FROM ranked.new_seq
        """,
    )
    return cr.rowcount


def compute_reordered_department_ids(
    full_dept_ids: list[int],
    employee_id: int,
    before_id: int | None = None,
    after_id: int | None = None,
) -> list[int]:
    """Pure pagination-safe helper: reposition employee_id relative to before_id/after_id across full_dept_ids."""
    if employee_id not in full_dept_ids:
        msg = 'Moved employee is not in the target department list.'
        raise ValueError(msg)
    if not before_id and not after_id:
        msg = 'At least one of before_id or after_id is required.'
        raise ValueError(msg)
    if before_id == employee_id or after_id == employee_id:
        msg = 'Reference employee cannot equal moved employee.'
        raise ValueError(msg)

    remaining = [eid for eid in full_dept_ids if eid != employee_id]
    if before_id is not None and before_id not in remaining:
        msg = 'before_id does not belong to the same department.'
        raise ValueError(msg)
    if after_id is not None and after_id not in remaining:
        msg = 'after_id does not belong to the same department.'
        raise ValueError(msg)

    if before_id is not None and after_id is not None:
        idx_after = remaining.index(after_id)
        idx_before = remaining.index(before_id)
        if idx_after + 1 != idx_before:
            msg = 'Inconsistent before_id and after_id anchors.'
            raise ValueError(msg)

    if before_id is not None:
        insert_at = remaining.index(before_id)
    else:
        insert_at = remaining.index(after_id) + 1

    return [*remaining[:insert_at], employee_id, *remaining[insert_at:]]


class HrEmployeeOrder(models.Model):
    _inherit = 'hr.employee'
    _order = 'sequence, id'

    sequence = fields.Integer(
        string='Thứ tự trong phòng',
        default=10,
        index=True,
        copy=False,
    )

    @api.model
    def _tp_can_reorder_employees(self) -> bool:
        if self.env.su or self.env.uid == SUPERUSER_ID:
            return True
        user = self.env.user
        if not user or not user.active or user.share:
            return False
        if not (user.has_group('base.group_system') or user.has_group('hr.group_hr_user')):
            return False
        return bool(self.env['hr.employee'].has_access('write'))

    @api.model
    def _tp_parse_positive_id(self, raw_val, label: str, *, allow_empty: bool = False) -> int | None:
        if raw_val in (None, False, '', 0, '0'):
            if allow_empty:
                return None
            raise ValidationError(self.env._('%s không hợp lệ.', label))
        if isinstance(raw_val, bool):
            raise ValidationError(self.env._('%s không hợp lệ.', label))
        try:
            parsed = int(raw_val)
        except (TypeError, ValueError) as exc:
            raise ValidationError(self.env._('%s không hợp lệ.', label)) from exc
        if parsed <= 0 or str(parsed) != str(raw_val).strip():
            raise ValidationError(self.env._('%s không hợp lệ.', label))
        return parsed

    @api.model
    def _tp_lock_employee_order(self, company_ids):
        # A real MVCC update makes stale Repeatable Read transactions retry, including phantoms.
        for company_id in sorted(set(company_ids)):
            self.env.cr.execute(
                'SELECT pg_advisory_xact_lock(%s, %s)',
                (ADVISORY_LOCK_NS_EMP_ORDER, company_id),
            )
            self.env.cr.execute('UPDATE res_company SET id = id WHERE id = %s', (company_id,))

    @api.model
    def _tp_next_department_sequence(self, company_id: int | None, dept_id: int | None, *, active: bool = True) -> int:
        if not company_id:
            return 10
        self._tp_lock_employee_order([company_id])
        self.env.flush_all()
        self.env.cr.execute(
            """
            SELECT COALESCE(MAX(e.sequence), 0) + 10
              FROM hr_employee e
              LEFT JOIN hr_version v ON v.id = e.current_version_id
             WHERE e.company_id = %s
               AND COALESCE(v.department_id, 0) = %s
               AND e.active = %s
            """,
            (int(company_id), int(dept_id or 0), bool(active)),
        )
        row = self.env.cr.fetchone()
        return int(row[0]) if row and row[0] else 10

    @api.model_create_multi
    def create(self, vals_list):
        if any('sequence' in vals for vals in vals_list) and not is_trusted_employee_reorder(self.env):
            raise AccessError(self.env._('Thứ tự được tự động cấp khi tạo nhân viên.'))
        companies = [vals.get('company_id') or self.env.company.id for vals in vals_list]
        self._tp_lock_employee_order(companies)
        records = super().create(vals_list)
        for rec in records:
            dept_id = rec.sudo().current_version_id.department_id.id or 0
            next_seq = self._tp_next_department_sequence(rec.company_id.id, dept_id, active=bool(rec.active))
            rec.with_context(_tp_employee_reorder=_TP_REORDER).sudo().write({'sequence': next_seq})
        return records

    def write(self, vals):
        if (
            'sequence' in vals
            and self.env.context.get('_tp_employee_reorder') is not _TP_REORDER
        ):
            raise AccessError(
                self.env._('Thứ tự nhân viên chỉ được cập nhật bằng thao tác sắp xếp trong cùng phòng ban.'),
            )
        if set(vals) & {'department_id', 'company_id', 'active', 'current_version_id'}:
            self._tp_lock_employee_order(self.sudo().company_id.ids + ([vals['company_id']] if vals.get('company_id') else []))
        return super().write(vals)

    def unlink(self):
        self._tp_lock_employee_order(self.sudo().company_id.ids)
        return super().unlink()

    @api.model
    def tp_reorder_in_department(
        self,
        employee_id,
        department_id=False,
        before_id=None,
        after_id=None,
    ) -> dict:
        """Atomically reorder one active employee within their current department."""
        if not self._tp_can_reorder_employees():
            raise AccessError(self.env._('Bạn không có quyền sắp xếp thứ tự nhân viên.'))

        emp_id = self._tp_parse_positive_id(employee_id, 'Nhân viên')
        dept_id = self._tp_parse_positive_id(department_id, 'Phòng ban', allow_empty=True) or 0
        before_emp_id = self._tp_parse_positive_id(before_id, 'Vị trí trước', allow_empty=True)
        after_emp_id = self._tp_parse_positive_id(after_id, 'Vị trí sau', allow_empty=True)

        if before_emp_id is None and after_emp_id is None:
            raise ValidationError(self.env._('Cần cung cấp vị trí thả hợp lệ trong cùng phòng ban.'))
        if before_emp_id == emp_id or after_emp_id == emp_id:
            raise ValidationError(self.env._('Vị trí tham chiếu không được trùng với nhân viên đang kéo.'))

        probe = self.sudo().with_context(active_test=False).browse(emp_id).exists()
        if not probe or not probe.active:
            raise ValidationError(self.env._('Hồ sơ nhân viên không tồn tại hoặc đã lưu trữ.'))
        company_id = probe.company_id.id
        if company_id not in self.env.companies.ids:
            raise AccessError(self.env._('Nhân viên nằm ngoài công ty đang làm việc.'))

        self._tp_lock_employee_order([company_id])
        self.env.flush_all()
        self.env.cr.execute(
            """
            SELECT e.id, COALESCE(e.sequence, 10)
              FROM hr_employee e
              LEFT JOIN hr_version v ON v.id = e.current_version_id
             WHERE e.company_id = %s
               AND COALESCE(v.department_id, 0) = %s
               AND e.active = TRUE
             ORDER BY COALESCE(e.sequence, 10) ASC, e.id ASC
               FOR UPDATE OF e
            """,
            (company_id, dept_id),
        )
        locked_rows = self.env.cr.fetchall()
        self.env.invalidate_all()

        moved = self.with_context(version_id=False).browse(emp_id).exists()
        if not moved or not moved.active:
            raise ValidationError(self.env._('Hồ sơ nhân viên không còn hoạt động hoặc bạn không có quyền xem.'))
        moved.check_access('read')
        moved.check_access('write')

        actual_dept_id = moved.sudo().current_version_id.department_id.id or 0
        if actual_dept_id != dept_id or moved.company_id.id != company_id:
            raise ValidationError(
                self.env._('Chỉ được sắp xếp nhân viên trong cùng phòng ban hiện tại; không thể thả sang phòng ban khác.'),
            )

        for anchor_id in (before_emp_id, after_emp_id):
            if anchor_id is None:
                continue
            anchor = self.sudo().with_context(active_test=False).browse(anchor_id).exists()
            if not anchor or not anchor.active or anchor.company_id.id != company_id:
                raise ValidationError(self.env._('Nhân viên tham chiếu vị trí không hợp lệ.'))
            anchor_dept_id = anchor.current_version_id.department_id.id or 0
            if anchor_dept_id != actual_dept_id:
                raise ValidationError(
                    self.env._('Không thể thả nhân viên vào phòng ban khác.'),
                )

        full_dept_ids = [int(r[0]) for r in locked_rows]
        current_seq_by_id = {int(r[0]): int(r[1]) for r in locked_rows}

        # Ensure caller's record rules can see every active employee in this department
        visible_records = self.with_context(version_id=False).search([
            ('company_id', '=', company_id),
            ('department_id', '=', actual_dept_id or False),
            ('active', '=', True),
        ])
        if set(visible_records.ids) != set(full_dept_ids):
            raise AccessError(
                self.env._('Bạn không có quyền xem đầy đủ nhân viên trong phòng ban này để thay đổi thứ tự chung.'),
            )
        visible_records.check_access('write')

        try:
            new_order = compute_reordered_department_ids(
                full_dept_ids,
                emp_id,
                before_id=before_emp_id,
                after_id=after_emp_id,
            )
        except ValueError as exc:
            raise ValidationError(
                self.env._('Vị trí sắp xếp không hợp lệ hoặc dữ liệu vừa thay đổi. Vui lòng tải lại danh sách.'),
            ) from exc

        reorder_env = self.with_context(_tp_employee_reorder=_TP_REORDER)
        for idx, eid in enumerate(new_order, start=1):
            target_seq = idx * 10
            if current_seq_by_id.get(eid) != target_seq:
                reorder_env.browse(eid).write({'sequence': target_seq})

        return {
            'ok': True,
            'employee_id': emp_id,
            'department_id': actual_dept_id or False,
            'ordered_ids': new_order,
        }


class HrEmployeePublicOrder(models.Model):
    _inherit = 'hr.employee.public'
    _order = 'sequence, id'

    sequence = fields.Integer(string='Thứ tự trong phòng', readonly=True)


class IrHttpEmployeeOrder(models.AbstractModel):
    _inherit = 'ir.http'

    def session_info(self):
        result = super().session_info()
        if self.env.user._is_internal():
            result['tp_hr_can_reorder'] = bool(self.env['hr.employee']._tp_can_reorder_employees())
        return result
