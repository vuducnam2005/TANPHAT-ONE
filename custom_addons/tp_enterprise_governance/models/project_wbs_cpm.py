# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
"""E1-E6: Project WBS, DAG Critical Path Method (CPM), Weighted Progress Rollup, Baselines, and Allocation Settlement."""
from collections import defaultdict, deque
import json

from odoo import Command, _, api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError

from odoo.addons.tp_request.models.request_common import (
    format_date_vn,
    format_dt_local,
    is_live_admin_user,
)

ENGINEERING_TEMPLATES = {
    'bridge_road': [
        ('1.0', 'Khảo sát địa hình - địa chất - thủy văn', 15.0, 20.0),
        ('2.0', 'Báo cáo nghiên cứu khả thi (BCNCKT) / Thiết kế cơ sở', 20.0, 25.0),
        ('3.0', 'Thiết kế kỹ thuật (TKKT) & Dự toán', 30.0, 30.0),
        ('4.0', 'Thiết kế bản vẽ thi công (TKBVTC)', 25.0, 25.0),
        ('5.0', 'Thẩm tra, trình duyệt & Giám sát tác giả (GSTG)', 10.0, 15.0),
    ],
    'survey_standalone': [
        ('1.0', 'Lập phương án kỹ thuật khảo sát & Chuẩn bị thiết bị', 15.0, 5.0),
        ('2.0', 'Đo đạc hiện trường & Khoan khảo sát địa chất', 50.0, 15.0),
        ('3.0', 'Thí nghiệm trong phòng & Lập báo cáo kết quả khảo sát', 35.0, 10.0),
    ],
}


class ProjectEnterpriseWbs(models.Model):
    _inherit = 'project.project'

    tp_stage_template_kind = fields.Selection(
        [
            ('none', 'Không áp dụng mẫu sẵn'),
            ('bridge_road', 'Tư vấn Thiết kế Cầu Đường (KS → BCNCKT → TKKT → TKBVTC → GSTG)'),
            ('survey_standalone', 'Khảo sát Địa hình / Địa chất độc lập'),
        ],
        default='none',
        string='Mẫu WBS gợi ý',
    )
    tp_weighted_progress_pct = fields.Float(
        string='Tiến độ trọng số dự án (%)',
        compute='_compute_tp_weighted_progress',
        store=True,
        digits=(6, 2),
    )
    tp_cpm_duration_days = fields.Float(string='Tổng thời lượng đường găng (ngày)', readonly=True, default=0.0)
    tp_cpm_data_ready = fields.Boolean(string='Đủ dữ liệu tính CPM', readonly=True, default=False)
    tp_baseline_ids = fields.One2many('tp.project.baseline', 'project_id', string='Các mốc Baseline tiến độ')
    tp_milestone_log_ids = fields.One2many('tp.project.milestone.log', 'project_id', string='Nhật ký điều chỉnh mốc tiến độ')

    @api.depends('task_ids.tp_progress_pct', 'task_ids.tp_weight_factor', 'task_ids.active', 'task_ids.parent_id')
    def _compute_tp_weighted_progress(self):
        for proj in self:
            # Roll up leaf WBS tasks by weight_factor (NEVER unweighted simple average!)
            active_tasks = proj.sudo().task_ids.filtered(lambda t: t.active)
            parent_ids = set(active_tasks.mapped('parent_id').ids)
            leaves = active_tasks.filtered(lambda t: t.id not in parent_ids)
            total_w = sum(max(t.tp_weight_factor or 0.0, 0.0) for t in leaves)
            if total_w > 0:
                weighted_sum = sum(
                    max(min(t.tp_progress_pct or 0.0, 100.0), 0.0) * max(t.tp_weight_factor or 0.0, 0.0)
                    for t in leaves
                )
                proj.tp_weighted_progress_pct = round(weighted_sum / total_w, 2)
            else:
                proj.tp_weighted_progress_pct = 0.0

    def _tp_check_pm_or_admin(self):
        self.ensure_one()
        user = self.env.user
        if is_live_admin_user(user, company=self.company_id) or user.has_group('tp_core.group_manager'):
            return True
        if self._tp_head_allowed(user):
            return True
        pm_assigned = self.env['tp.project.assignment'].sudo().search_count([
            ('project_id', '=', self.id),
            ('user_id', '=', user.id),
            ('role', '=', 'coordinator'),
            ('active', '=', True),
        ])
        if pm_assigned:
            return True
        raise AccessError(_('Chỉ Chủ nhiệm dự án (PM), Trưởng đơn vị chủ trì hoặc Admin mới thực hiện thao tác quản trị tiến độ này.'))

    def action_apply_engineering_wbs_template(self, template_kind='bridge_road'):
        """Optional WBS template generator — NEVER forced automatically on project creation."""
        self.ensure_one()
        self._tp_check_pm_or_admin()
        phases = ENGINEERING_TEMPLATES.get(template_kind)
        if not phases:
            raise UserError(_('Mẫu WBS không hợp lệ.'))

        Task = self.env['project.task'].sudo()
        existing_codes = set(Task.search([('project_id', '=', self.id)]).mapped('tp_wbs_code'))
        prev_task = False
        created = 0
        for code, title, weight, duration in phases:
            if code in existing_codes:
                continue
            vals = {
                'project_id': self.id,
                'name': title,
                'tp_wbs_code': code,
                'tp_wbs_level': 1,
                'tp_weight_factor': weight,
                'tp_planned_duration_days': duration,
                'tp_source_kind': 'project',
            }
            if prev_task:
                vals['tp_predecessor_ids'] = [Command.set([prev_task.id])]
            prev_task = Task.create(vals)
            created += 1

        self.sudo().write({'tp_stage_template_kind': template_kind})
        if created:
            self.action_recompute_cpm()
        return {'created_count': created}

    def action_recompute_cpm(self):
        """True Critical Path Method (CPM): forward ES/EF, backward LS/LF, total float, critical path.

        NEVER colors overdue tasks as critical path when duration/dependency data is missing!
        """
        self.ensure_one()
        self.check_access('read')
        tasks = self.env['project.task'].sudo().search([
            ('project_id', '=', self.id),
            ('active', '=', True),
        ], order='tp_wbs_code asc, id asc')

        task_map = {t.id: t for t in tasks}
        has_durations = any((t.tp_planned_duration_days or 0.0) > 0 for t in tasks)
        if not tasks or not has_durations:
            for t in tasks:
                t.write({
                    'tp_es_days': 0.0, 'tp_ef_days': 0.0,
                    'tp_ls_days': 0.0, 'tp_lf_days': 0.0,
                    'tp_total_float_days': 0.0, 'tp_is_critical_path': False,
                })
            self.sudo().write({'tp_cpm_duration_days': 0.0, 'tp_cpm_data_ready': False})
            return {'ready': False, 'project_duration_days': 0.0, 'critical_task_ids': []}

        # Build DAG inside project
        preds = defaultdict(list)
        succs = defaultdict(list)
        in_degree = {tid: 0 for tid in task_map}
        for tid, t in task_map.items():
            for p in t.tp_predecessor_ids:
                if p.id in task_map:
                    preds[tid].append(p.id)
                    succs[p.id].append(tid)
                    in_degree[tid] += 1

        # Kahn's topological sort + cycle guard
        queue = deque([tid for tid, deg in in_degree.items() if deg == 0])
        topo_order = []
        while queue:
            u = queue.popleft()
            topo_order.append(u)
            for v in succs[u]:
                in_degree[v] -= 1
                if in_degree[v] == 0:
                    queue.append(v)

        if len(topo_order) != len(task_map):
            raise ValidationError(_('Phát hiện chu trình phụ thuộc (vòng lặp DAG) trong bảng WBS dự án.'))

        # Forward pass (ES, EF)
        es = {}
        ef = {}
        for u in topo_order:
            dur = max(float(task_map[u].tp_planned_duration_days or 0.0), 0.0)
            es[u] = max((ef[p] for p in preds[u]), default=0.0)
            ef[u] = round(es[u] + dur, 2)

        project_duration = max(ef.values(), default=0.0)

        # Backward pass (LF, LS)
        lf = {}
        ls = {}
        for u in reversed(topo_order):
            dur = max(float(task_map[u].tp_planned_duration_days or 0.0), 0.0)
            lf[u] = min((ls[s] for s in succs[u]), default=project_duration)
            ls[u] = round(lf[u] - dur, 2)

        critical_ids = []
        for u, t in task_map.items():
            dur = max(float(t.tp_planned_duration_days or 0.0), 0.0)
            flt = round(ls[u] - es[u], 2)
            is_crit = bool(project_duration > 0 and dur > 0 and abs(flt) <= 0.001)
            if is_crit:
                critical_ids.append(u)
            t.write({
                'tp_es_days': es[u],
                'tp_ef_days': ef[u],
                'tp_ls_days': ls[u],
                'tp_lf_days': lf[u],
                'tp_total_float_days': flt,
                'tp_is_critical_path': is_crit,
            })

        self.sudo().write({
            'tp_cpm_duration_days': round(project_duration, 2),
            'tp_cpm_data_ready': True,
        })
        return {
            'ready': True,
            'project_duration_days': round(project_duration, 2),
            'critical_task_ids': critical_ids,
        }

    def action_capture_baseline(self, baseline_name='', reason=''):
        """Freeze a WBS schedule baseline snapshot."""
        self.ensure_one()
        self._tp_check_pm_or_admin()
        self.action_recompute_cpm()
        next_ver = len(self.tp_baseline_ids) + 1
        tasks = self.env['project.task'].sudo().search([('project_id', '=', self.id), ('active', '=', True)], order='tp_wbs_code, id')
        snap_items = [{
            'task_id': t.id,
            'wbs_code': t.tp_wbs_code or '',
            'name': t.name,
            'planned_start': t.tp_planned_start.isoformat() if t.tp_planned_start else '',
            'planned_end': t.tp_planned_end.isoformat() if t.tp_planned_end else '',
            'duration_days': t.tp_planned_duration_days or 0.0,
            'weight_factor': t.tp_weight_factor or 0.0,
            'is_critical_path': bool(t.tp_is_critical_path),
        } for t in tasks]
        bl = self.env['tp.project.baseline'].sudo().create({
            'project_id': self.id,
            'version': next_ver,
            'name': (baseline_name or '').strip() or f'Baseline v{next_ver}',
            'reason': (reason or '').strip() or 'Chốt kế hoạch gốc dự án',
            'captured_by_id': self.env.uid,
            'cpm_duration_days': self.tp_cpm_duration_days,
            'snapshot_json': json.dumps(snap_items, ensure_ascii=False),
        })
        return {'baseline_id': bl.id, 'version': next_ver}

    def action_adjust_milestone(self, task_id, new_planned_end, reason):
        """Adjust a baselined task's planned end date with mandatory audit reason."""
        self.ensure_one()
        self._tp_check_pm_or_admin()
        clean_reason = (reason or '').strip()
        if not clean_reason:
            raise UserError(_('Bắt buộc nhập Lý do điều chỉnh mốc tiến độ sau khi đã lập kế hoạch.'))
        task = self.env['project.task'].sudo().browse(int(task_id or 0)).exists()
        if not task or task.project_id.id != self.id:
            raise UserError(_('Không tìm thấy hạng mục WBS thuộc dự án này.'))
        old_end = task.tp_planned_end
        parsed_end = fields.Date.to_date(new_planned_end)
        task.write({'tp_planned_end': parsed_end, 'date_deadline': parsed_end})
        self.env['tp.project.milestone.log'].sudo().create({
            'project_id': self.id,
            'task_id': task.id,
            'old_date': old_end,
            'new_date': parsed_end,
            'reason': clean_reason,
            'changed_by_id': self.env.uid,
        })
        return True

    @api.model
    def tp_wbs_workspace_data(self, project_id=0):
        projs = self.search([('company_id', '=', self.env.company.id)], order='tp_code asc, name asc', limit=100)
        selected = projs.filtered(lambda p: p.id == int(project_id or 0))[:1] or projs[:1]
        if not selected:
            return {'projects': [], 'selected_project': None, 'tasks': [], 'baselines': [], 'logs': []}

        tasks = self.env['project.task'].search([('project_id', '=', selected.id)], order='tp_wbs_code asc, sequence asc, id asc')
        task_rows = []
        for t in tasks:
            task_rows.append({
                'id': t.id,
                'wbs_code': t.tp_wbs_code or '—',
                'name': t.name,
                'assignee_names': ', '.join(t.user_ids.sudo().mapped('name')) or 'Chưa giao',
                'planned_start': format_date_vn(t.tp_planned_start),
                'planned_end': format_date_vn(t.tp_planned_end),
                'planned_end_iso': t.tp_planned_end.isoformat() if t.tp_planned_end else '',
                'duration_days': t.tp_planned_duration_days or 0.0,
                'weight_factor': t.tp_weight_factor or 0.0,
                'progress_pct': t.tp_progress_pct or 0.0,
                'predecessor_codes': [p.tp_wbs_code or f'#{p.id}' for p in t.tp_predecessor_ids],
                'es': t.tp_es_days,
                'ef': t.tp_ef_days,
                'ls': t.tp_ls_days,
                'lf': t.tp_lf_days,
                'total_float': t.tp_total_float_days,
                'is_critical': bool(t.tp_is_critical_path),
                'exec_reported': bool(t.tp_state_exec_reported),
                'result_verified': bool(t.tp_state_result_verified),
                'dossier_issued': bool(t.tp_state_dossier_issued),
                'volume_accepted': bool(t.tp_state_volume_accepted),
            })

        baselines = [{
            'id': b.id,
            'version': b.version,
            'name': b.name,
            'reason': b.reason,
            'cpm_duration_days': b.cpm_duration_days,
            'captured_at': format_dt_local(b.create_date),
            'captured_by': b.captured_by_id.sudo().name,
        } for b in selected.tp_baseline_ids]

        logs = [{
            'id': lg.id,
            'task_name': lg.task_id.sudo().name,
            'old_date': format_date_vn(lg.old_date),
            'new_date': format_date_vn(lg.new_date),
            'reason': lg.reason,
            'changed_by': lg.changed_by_id.sudo().name,
            'changed_at': format_dt_local(lg.create_date),
        } for lg in selected.tp_milestone_log_ids[:20]]

        return {
            'projects': [{'id': p.id, 'name': f"{p.tp_code + ' · ' if p.tp_code else ''}{p.name}"} for p in projs],
            'selected_project': {
                'id': selected.id,
                'code': selected.tp_code or '',
                'name': selected.name,
                'weighted_progress_pct': selected.tp_weighted_progress_pct,
                'cpm_duration_days': selected.tp_cpm_duration_days,
                'cpm_data_ready': selected.tp_cpm_data_ready,
            },
            'tasks': task_rows,
            'baselines': baselines,
            'logs': logs,
        }


class ProjectTaskWbsCpm(models.Model):
    _inherit = 'project.task'

    tp_wbs_code = fields.Char(string='Mã WBS', index=True)
    tp_wbs_level = fields.Integer(string='Cấp WBS', default=1)
    tp_planned_start = fields.Date(string='Bắt đầu kế hoạch')
    tp_planned_end = fields.Date(string='Kết thúc kế hoạch')
    tp_planned_duration_days = fields.Float(string='Thời lượng kế hoạch (ngày)', default=0.0)
    tp_weight_factor = fields.Float(string='Trọng số WBS', default=1.0)
    tp_progress_pct = fields.Float(string='Tiến độ hoàn thành (%)', default=0.0)

    tp_predecessor_ids = fields.Many2many(
        'project.task', 'tp_task_cpm_dep_rel', 'task_id', 'predecessor_id',
        string='Hạng mục tiền nhiệm (DAG)',
    )
    tp_successor_ids = fields.Many2many(
        'project.task', 'tp_task_cpm_dep_rel', 'predecessor_id', 'task_id',
        string='Hạng mục kế tiếp',
    )
    tp_es_days = fields.Float(string='ES (ngày)', readonly=True, default=0.0)
    tp_ef_days = fields.Float(string='EF (ngày)', readonly=True, default=0.0)
    tp_ls_days = fields.Float(string='LS (ngày)', readonly=True, default=0.0)
    tp_lf_days = fields.Float(string='LF (ngày)', readonly=True, default=0.0)
    tp_total_float_days = fields.Float(string='Dự trữ toàn phần Float (ngày)', readonly=True, default=0.0)
    tp_is_critical_path = fields.Boolean(string='Thuộc đường găng (CPM)', readonly=True, default=False, index=True)

    # 4 Strictly Separated Deliverable States (Mandatory Case #6: Task Done != Volume Accepted / Payment!)
    tp_state_exec_reported = fields.Boolean(string='1. Đã báo xong thực hiện', default=False)
    tp_state_result_verified = fields.Boolean(string='2. Đã xác nhận kết quả', default=False)
    tp_state_dossier_issued = fields.Boolean(string='3. Đã phát hành hồ sơ', default=False)
    tp_state_volume_accepted = fields.Boolean(string='4. Đã nghiệm thu khối lượng', default=False)

    @api.constrains('tp_predecessor_ids')
    def _check_no_dependency_cycle(self):
        for task in self:
            visited = set()
            stack = list(task.tp_predecessor_ids.ids)
            while stack:
                curr_id = stack.pop()
                if curr_id == task.id:
                    raise ValidationError(_('Không thể tạo phụ thuộc vòng lặp (chu trình DAG) giữa các hạng mục WBS.'))
                if curr_id not in visited:
                    visited.add(curr_id)
                    preds = self.sudo().browse(curr_id).tp_predecessor_ids.ids
                    stack.extend(preds)

    def action_update_wbs_progress(self, progress_pct, exec_reported=None):
        """Update execution progress — NEVER auto-marks volume_accepted or triggers payment (Mandatory Case #6)."""
        self.ensure_one()
        self.check_access('read')
        if self.env.user not in self.sudo().user_ids:
            if self.project_id:
                self.project_id._tp_check_pm_or_admin()
            else:
                self.check_access('write')
        pct = max(min(float(progress_pct or 0.0), 100.0), 0.0)
        vals = {'tp_progress_pct': pct}
        if exec_reported is not None:
            vals['tp_state_exec_reported'] = bool(exec_reported)
        elif pct >= 100.0:
            vals['tp_state_exec_reported'] = True
        self.sudo().write(vals)
        return {
            'progress_pct': self.tp_progress_pct,
            'exec_reported': self.tp_state_exec_reported,
            'volume_accepted': self.tp_state_volume_accepted,
        }


class TpProjectBaseline(models.Model):
    _name = 'tp.project.baseline'
    _description = 'Snapshot Baseline Kế hoạch & Đường găng Dự án'
    _order = 'version desc, id desc'

    project_id = fields.Many2one('project.project', required=True, ondelete='cascade', index=True)
    company_id = fields.Many2one(related='project_id.company_id', store=True, index=True)
    version = fields.Integer(string='Phiên bản Baseline', required=True, readonly=True)
    name = fields.Char(string='Tên Baseline', required=True, readonly=True)
    reason = fields.Text(string='Ghi chú / căn cứ chốt', readonly=True)
    captured_by_id = fields.Many2one('res.users', string='Người chốt', readonly=True)
    cpm_duration_days = fields.Float(string='Thời lượng đường găng lúc chốt', readonly=True)
    snapshot_json = fields.Text(string='Dữ liệu WBS đóng băng (JSON)', readonly=True)


class TpProjectMilestoneLog(models.Model):
    _name = 'tp.project.milestone.log'
    _description = 'Nhật ký điều chỉnh mốc tiến độ dự án'
    _order = 'create_date desc, id desc'

    project_id = fields.Many2one('project.project', required=True, ondelete='cascade', index=True)
    company_id = fields.Many2one(related='project_id.company_id', store=True, index=True)
    task_id = fields.Many2one('project.task', required=True, ondelete='cascade')
    old_date = fields.Date(string='Mốc cũ', readonly=True)
    new_date = fields.Date(string='Mốc mới', readonly=True)
    reason = fields.Text(string='Lý do điều chỉnh', required=True, readonly=True)
    changed_by_id = fields.Many2one('res.users', string='Người điều chỉnh', readonly=True)


class TpAllocationEnterpriseSettlement(models.Model):
    """E4 Thầu phụ & E5 Giao khoán nội bộ: advance, retention, settlement & handover tracking."""
    _inherit = 'tp.allocation'

    tp_currency_id = fields.Many2one('res.currency', default=lambda s: s.env.company.currency_id)
    tp_advance_amount = fields.Monetary(currency_field='tp_currency_id', string='Tạm ứng đã đối chiếu', default=0.0)
    tp_settled_amount = fields.Monetary(currency_field='tp_currency_id', string='Giá trị quyết toán xác nhận', default=0.0)
    tp_retention_amount = fields.Monetary(currency_field='tp_currency_id', string='Giá trị giữ lại bảo hành', default=0.0)
    tp_handover_ref = fields.Char(string='Biên bản bàn giao / nghiệm thu đầu ra')
