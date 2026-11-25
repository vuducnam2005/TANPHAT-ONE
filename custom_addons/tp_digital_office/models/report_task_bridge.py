# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
"""H: Clean _inherit bridge between Plans (Year->Quarter->Month->Week), Tasks, and Frozen Report Snapshots."""
from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

from odoo.addons.tp_request.models.request_common import is_live_admin_user


class TpReportWorkflowMixinEnterprise(models.AbstractModel):
    _inherit = 'tp.report.workflow.mixin'

    period_type = fields.Selection(
        selection_add=[('year', 'Năm')],
        ondelete={'year': 'cascade'},
    )

    @api.constrains('date_start', 'date_end', 'period_type')
    def _check_period(self):
        non_year = self.filtered(lambda r: r.period_type != 'year')
        if non_year:
            super(TpReportWorkflowMixinEnterprise, non_year)._check_period()
        for rec in self - non_year:
            start, end = rec.date_start, rec.date_end
            valid = (
                bool(start and end)
                and start.year == end.year
                and start.month == 1 and start.day == 1
                and end.month == 12 and end.day == 31
            )
            if not valid:
                raise ValidationError(_('Kế hoạch Năm phải bắt đầu 01/01 và kết thúc 31/12 cùng năm.'))


class TpReportPlanEnterpriseBridge(models.Model):
    _inherit = 'tp.report.plan'

    period_type = fields.Selection(
        selection_add=[('year', 'Năm')],
        ondelete={'year': 'cascade'},
    )

    def _has_valid_parent(self, parent):
        self.ensure_one()
        if self.period_type == 'quarter' and parent.period_type == 'year':
            dates = parent.date_start <= self.date_start <= self.date_end <= parent.date_end
            return (
                parent.company_id == self.company_id
                and dates
                and (not parent.department_id or parent.department_id == self.department_id)
                and self.unit == parent.unit
            )
        return super()._has_valid_parent(parent)

    @api.constrains('parent_id', 'period_type', 'company_id', 'date_start', 'date_end', 'unit', 'target')
    def _check_parent(self):
        for rec in self:
            if rec.target < 0:
                raise ValidationError(_('Mục tiêu không âm.'))
            parent = rec.parent_id
            if not parent:
                if rec.period_type not in ('year', 'quarter'):
                    raise ValidationError(_('Tháng/tuần phải có kế hoạch cha.'))
                continue
            if not rec._has_valid_parent(parent):
                raise ValidationError(_('Cha phải đúng công ty, cấp kỳ, phạm vi, đơn vị và khoảng ngày.'))
            chain = parent
            while chain:
                if chain == rec:
                    raise ValidationError(_('Không tạo chu trình kế hoạch.'))
                chain = chain.parent_id


class TpReportDocumentTaskBridge(models.Model):
    _inherit = 'tp.report.document'

    def tp_load_tasks_into_draft(self, task_ids=None):
        """Pull caller's permitted project.task results into draft/returned report lines without mutating snapshots.

        Mandatory Cases #7 & #8:
        - Never uses sudo() to pull tasks outside caller's read scope.
        - Idempotent via contribution_key = 'task:<id>'.
        - Cannot run on submitted/finalized reports; frozen tp.report.snapshot stays 100% immutable when tasks change later.
        """
        self.ensure_one()
        self.check_access('read')
        if self.state not in ('draft', 'returned'):
            raise UserError(_('Chỉ nạp công việc vào báo cáo đang ở trạng thái Nháp hoặc Yêu cầu bổ sung.'))
        if self.owner_id != self.env.user:
            raise AccessError(_('Chỉ người lập báo cáo mới được nạp công việc vào bản nháp của chính mình.'))

        TaskUser = self.env['project.task'].with_user(self.owner_id)
        if task_ids:
            clean_ids = [int(x) for x in task_ids if int(x or 0) > 0]
            tasks = TaskUser.browse(clean_ids).exists()
            tasks.check_access('read')
        else:
            dom = [
                ('user_ids', 'in', [self.owner_id.id]),
                '|',
                ('date_deadline', '=', False),
                '&',
                ('date_deadline', '>=', self.date_start),
                ('date_deadline', '<=', self.date_end),
            ]
            tasks = TaskUser.search(dom, order='date_deadline asc, id asc', limit=100)

        Line = self.env['tp.report.line'].with_user(self.env.user)
        existing_by_key = {ln.contribution_key: ln for ln in self.line_ids if ln.contribution_key}
        loaded_count = 0
        updated_count = 0

        for t in tasks:
            ckey = f'task:{t.id}'
            t_deadline = t.date_deadline.date() if hasattr(t.date_deadline, 'date') and t.date_deadline else t.date_deadline
            if t_deadline and self.date_start <= t_deadline <= self.date_end:
                wdate = t_deadline
            else:
                wdate = self.date_end

            is_done = t.state == '1_done'
            exec_rep = getattr(t, 'tp_exec_report_state', 'working')
            status_txt = (
                'Đã xác nhận hoàn thành'
                if is_done
                else ('Đã báo hoàn thành (chờ xác nhận)' if exec_rep == 'reported_done' else 'Đang thực hiện')
            )
            deliverable = getattr(t, 'tp_deliverable', '') or ''
            result_summary = f'{status_txt}' + (f' — Sản phẩm: {deliverable}' if deliverable else '')

            line_vals = {
                'name': t.name,
                'project_id': t.project_id.id or False,
                'task_id': t.id,
                'work_date': wdate,
                'quantity': 1.0 if is_done else 0.0,
                'quantity_known': bool(is_done),
                'unit': 'đầu việc',
                'contribution_key': ckey,
                'result': result_summary,
            }
            if ckey in existing_by_key:
                self.invalidate_recordset(['version'])
                existing_by_key[ckey].with_context(tp_reporting_expected_version=self.version).write(line_vals)
                updated_count += 1
            else:
                Line.create({**line_vals, 'document_id': self.id})
                loaded_count += 1

        return {
            'loaded_count': loaded_count,
            'updated_count': updated_count,
            'total_lines': len(self.line_ids),
        }


class TpTaskWorkloadBridge(models.Model):
    _inherit = 'project.task'

    @api.model
    def tp_get_honest_workload_summary(self, department_id=0, standard_weekly_hours=40.0):
        """Return honest workload summary per employee — NEVER deducing overload from raw task count without hour estimates."""
        company = self.env.company
        user = self.env.user
        is_admin = is_live_admin_user(user, company=company)

        emp_dom = [('company_id', '=', company.id), ('user_id', '!=', False)]
        if int(department_id or 0) > 0:
            emp_dom.append(('department_id', 'child_of', [int(department_id)]))
        if not is_admin:
            managed_depts = self.env['hr.department'].sudo().search([
                ('company_id', '=', company.id),
                ('manager_id.user_id', '=', user.id),
            ])
            if managed_depts:
                emp_dom.append(('department_id', 'child_of', managed_depts.ids))
            else:
                emp_dom.append(('user_id', '=', user.id))

        employees = self.env['hr.employee'].sudo().search(emp_dom, order='name')
        rows = []
        has_alloc_field = 'allocated_hours' in self._fields

        for emp in employees:
            # Count ONLY official assigned work tasks (never spy on employee's private 'self' To-Dos!)
            tasks = self.sudo().search([
                ('user_ids', 'in', [emp.user_id.id]),
                ('state', 'not in', ('1_done', '1_canceled')),
                '|',
                ('project_id', '!=', False),
                ('tp_source_kind', 'in', ('project', 'meeting', 'request', 'chat')),
            ])
            open_count = len(tasks)
            overdue_count = sum(
                1 for t in tasks
                if t.date_deadline and (
                    (t.date_deadline.date() if hasattr(t.date_deadline, 'date') else t.date_deadline)
                    < fields.Date.context_today(self)
                )
            )
            with_hours = [t for t in tasks if has_alloc_field and (t.allocated_hours or 0.0) > 0]
            total_hours = sum((t.allocated_hours or 0.0) for t in with_hours) if has_alloc_field else 0.0

            if open_count == 0:
                status = 'available'
                label = 'Không có đầu việc mở'
            elif len(with_hours) < open_count:
                status = 'insufficient_data'
                label = 'Chưa đủ dữ liệu định mức giờ'
            elif total_hours > float(standard_weekly_hours):
                status = 'high_load'
                label = f'Tải giờ cao ({total_hours:g}/{standard_weekly_hours:g}h)'
            else:
                status = 'balanced'
                label = f'Trong định mức ({total_hours:g}/{standard_weekly_hours:g}h)'

            rows.append({
                'employee_id': emp.id,
                'user_id': emp.user_id.id,
                'name': emp.name,
                'department_name': emp.department_id.name if emp.department_id else '—',
                'open_task_count': open_count,
                'overdue_task_count': overdue_count,
                'tasks_with_hours': len(with_hours),
                'allocated_hours_total': round(total_hours, 2) if status != 'insufficient_data' else None,
                'workload_status': status,
                'workload_label': label,
            })
        return {
            'standard_weekly_hours': standard_weekly_hours,
            'rows': rows,
        }
