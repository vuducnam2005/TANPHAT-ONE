"""HR-DELETE-010: dependency plan and guarded permanent deletion of employees.

Every stored link to the selected employees (and to the records created with
them) is classified as:

* deleted with the employee: owned rows (versions, skills, resume lines, ...),
  their chatter, followers, activities, files and xmlids, the own resource;
* kept: roster import lines (set to NULL, source data stays), the import batch
  and its file, the work contact while it is still used elsewhere;
* blocking: independent business data. Nothing is reassigned or unlinked; the
  admin resolves it first or archives instead.

Accounts and the password re-verification live in ``tp_hr_workspace``. This
module offers the plan, the locks and the final guarded unlink.
"""
import hashlib
import json

from psycopg2 import IntegrityError

from odoo import api, models
from odoo.exceptions import AccessError, UserError

from .hr_employee import _TP_DELETE

# Rows owned by one employee: ``employee_id`` with ondelete cascade.
OWNED_MODELS = {
    'hr.version': 'Phiên bản hồ sơ (lịch sử công tác)',
    'hr.employee.skill': 'Kỹ năng',
    'hr.resume.line': 'Quá trình công tác/học tập',
    'hr.employee.location': 'Địa điểm làm việc theo ngày',
    'hr.employee.departure': 'Thông tin nghỉ việc',
}
# ``res_model``/``res_id`` rows removed through the ORM with their document.
CLEANUP_MODELS = {
    'mail.message': 'Trao đổi và lịch sử thay đổi',
    'mail.followers': 'Người theo dõi',
    'mail.activity': 'Hoạt động',
    'mail.scheduled.message': 'Tin nhắn hẹn gửi',
    'ir.attachment': 'Tệp đính kèm và ảnh',
    'ir.model.data': 'Mã định danh kỹ thuật',
}
# Links kept after deletion (the database sets them to NULL).
KEPT_REFERENCES = {
    ('tp.hr.import.line', 'employee_id'): 'Dòng nhập danh sách nhân sự: giữ mã nguồn, họ tên, phòng ban gốc; bỏ liên kết tới hồ sơ',
}
# How to resolve a known blocking link.
HINTS = {
    ('hr.employee', 'parent_id'): 'Đang là quản lý trực tiếp của nhân viên khác — đổi người quản lý ở các hồ sơ đó trước.',
    ('hr.employee', 'coach_id'): 'Đang là người hướng dẫn của nhân viên khác — đổi người hướng dẫn trước.',
    ('hr.department', 'manager_id'): 'Đang là quản lý phòng ban — đổi quản lý phòng ban trước.',
    ('hr.job', 'recruiter_id'): 'Đang phụ trách tuyển dụng vị trí — đổi người phụ trách trước.',
    ('account.analytic.line', 'employee_id'): 'Có dòng chấm công/chi phí phân tích — giữ lịch sử: dùng Lưu trữ.',
    ('account.analytic.line', 'manager_id'): 'Là người duyệt dòng chấm công — giữ lịch sử: dùng Lưu trữ.',
    ('hr.expense', 'employee_id'): 'Có chi phí nhân viên — giữ chứng từ: dùng Lưu trữ.',
    ('resource.calendar.leaves', 'resource_id'): 'Có lịch nghỉ/vắng mặt — xóa lịch đó trước hoặc dùng Lưu trữ.',
}
_GENERIC_HINT = 'Gỡ liên kết ở đó trước hoặc dùng Lưu trữ.'
_EMPTY = (-1,)


def _ids(values):
    return tuple(values) or _EMPTY


class HrEmployeePermanentDelete(models.Model):
    _inherit = 'hr.employee'

    # ------------------------------------------------------------------
    # Rights
    # ------------------------------------------------------------------
    def _tp_check_permanent_delete_rights(self):
        """System admin with HR manager rights, all records in the current company."""
        user = self.env.user
        if not (user.has_group('base.group_system') and user.has_group('hr.group_hr_manager')):
            raise AccessError(self.env._('Chỉ quản trị hệ thống có quyền quản lý nhân sự được xóa vĩnh viễn nhân viên. Hãy dùng Lưu trữ nếu chỉ cần ẩn hồ sơ.'))
        if not self:
            raise UserError(self.env._('Hãy chọn ít nhất một nhân viên.'))
        employees = self.sudo().with_context(active_test=False)
        if len(employees.exists()) != len(set(self.ids)):
            raise UserError(self.env._('Có hồ sơ đã bị xóa hoặc không còn tồn tại. Hãy tải lại danh sách.'))
        if employees.filtered(lambda employee: employee.company_id != self.env.company):
            raise AccessError(self.env._('Chỉ xóa hồ sơ thuộc công ty đang làm việc (%(company)s).', company=self.env.company.name))
        self.with_context(active_test=False).check_access('unlink')

    # ------------------------------------------------------------------
    # Plan
    # ------------------------------------------------------------------
    def _tp_label(self, model_name, field_name=None):
        env = self.env
        model = env['ir.model']._get(model_name)
        label = model.name if model else model_name
        if field_name and model_name in env:
            field = env[model_name]._fields.get(field_name)
            if field:
                label = f'{label} – {field._description_string(env)}'
        return label

    @api.model
    def _tp_stored_references(self, targets, exclude=None):
        """Count stored many2one/many2many rows pointing to ``targets``.

        ``targets`` maps a model to the ids that disappear. ``exclude`` maps a
        referencing model to SQL ``(condition, params)`` of rows that also
        disappear (they are not references). Returns
        ``[(model, field, {target_model: {target_id: count}})]``.
        """
        cr = self.env.cr
        exclude = exclude or {}
        own_relations = set()
        for model_name in targets:
            model = self.env[model_name]
            own_relations |= {field.relation for field in model._fields.values() if field.type == 'many2many' and field.store and field.relation}
        result = []
        Fields = self.env['ir.model.fields'].sudo()
        for info in Fields.search([('relation', 'in', list(targets)), ('ttype', 'in', ('many2one', 'many2many')), ('store', '=', True)], order='model, name'):
            model = self.env.get(info.model)
            field = model is not None and model._fields.get(info.name)
            if not field or not field.store or model._transient or model._abstract or not model._auto or field.comodel_name != info.relation:
                continue
            ids = targets[info.relation]
            if not ids:
                continue
            condition, params = exclude.get(info.model, ('TRUE', []))
            if field.type == 'many2one':
                if not field.column_type:
                    continue
                cr.execute(f'SELECT "{field.name}", count(*) FROM "{model._table}" WHERE "{field.name}" IN %s AND ({condition}) GROUP BY 1',
                           [tuple(ids), *params])
            else:
                if field.relation in own_relations:
                    continue  # the selected records' own m2m rows go with them
                row_condition = condition.replace('"id"', f'"{field.column1}"') if condition != 'TRUE' else 'TRUE'
                cr.execute(f'SELECT "{field.column2}", count(*) FROM "{field.relation}" WHERE "{field.column2}" IN %s AND ({row_condition}) GROUP BY 1',
                           [tuple(ids), *params])
            counts = dict(cr.fetchall())
            if counts:
                result.append((info.model, info.name, {info.relation: counts}))
        return result

    def _tp_doomed(self):
        """Records that disappear with these employees: ``{model: {id: employee_id}}``."""
        cr = self.env.cr
        employees = self.sudo().with_context(active_test=False)
        doomed = {'hr.employee': {employee.id: employee.id for employee in employees}}
        doomed['resource.resource'] = {employee.resource_id.id: employee.id for employee in employees if employee.resource_id}
        for model_name in OWNED_MODELS:
            if model_name not in self.env:
                continue
            model = self.env[model_name]
            cr.execute(f'SELECT id, employee_id FROM "{model._table}" WHERE employee_id IN %s', [_ids(employees.ids)])
            doomed[model_name] = dict(cr.fetchall())
        return doomed

    @api.model
    def _tp_doomed_exclusions(self, doomed):
        exclude = {}
        for model_name, rows in doomed.items():
            if rows:
                exclude[model_name] = ('"id" NOT IN %s', [_ids(rows)])
        return exclude

    @api.model
    def _tp_reference_fields(self):
        """Stored many2one_reference fields: ``[(model, field, model_field)]``."""
        result = []
        for info in self.env['ir.model.fields'].sudo().search([('ttype', '=', 'many2one_reference'), ('store', '=', True)], order='model, name'):
            model = self.env.get(info.model)
            field = model is not None and model._fields.get(info.name)
            if not field or model._abstract or not model._auto or model._transient:
                continue
            model_field = model._fields.get(field.model_field)
            if model_field and model_field.store and model_field.type in ('char', 'selection'):
                result.append((info.model, info.name, field.model_field))
        return result

    def _tp_document_links(self, doomed):
        """``res_model``/``res_id`` rows on doomed records.

        Returns ``(cleanup, blocking)``; each maps ``(model, field)`` to
        ``{employee_id: count}`` and ``cleanup`` also collects row ids.
        """
        cr = self.env.cr
        cleanup, blocking, cleanup_ids = {}, {}, {}
        for model_name, field_name, model_field in self._tp_reference_fields():
            model = self.env[model_name]
            for target, rows in doomed.items():
                if not rows:
                    continue
                cr.execute(f'SELECT id, "{field_name}" FROM "{model._table}" WHERE "{model_field}" = %s AND "{field_name}" IN %s',
                           [target, _ids(rows)])
                for row_id, res_id in cr.fetchall():
                    employee_id = rows.get(res_id)
                    bucket = cleanup if model_name in CLEANUP_MODELS else blocking
                    key = (model_name, field_name)
                    counts = bucket.setdefault(key, {})
                    counts[employee_id] = counts.get(employee_id, 0) + 1
                    if model_name in CLEANUP_MODELS:
                        cleanup_ids.setdefault(model_name, set()).add(row_id)
        return cleanup, blocking, cleanup_ids

    def _tp_partner_plan(self, doomed):
        """Decide whether each work contact is deleted or kept, with a reason."""
        cr = self.env.cr
        employees = self.sudo().with_context(active_test=False)
        partners = employees.mapped('work_contact_id')
        result = {}
        if not partners:
            return result
        Users = self.env['res.users'].sudo().with_context(active_test=False)
        others = self.env['hr.employee'].sudo().with_context(active_test=False).search([
            ('work_contact_id', 'in', partners.ids), ('id', 'not in', employees.ids)])
        candidates = []
        for partner in partners:
            if Users.search_count([('partner_id', '=', partner.id)]):
                result[partner.id] = {'delete': False, 'reason': 'Liên hệ của tài khoản đăng nhập — giữ cùng tài khoản.'}
            elif partner in others.mapped('work_contact_id'):
                result[partner.id] = {'delete': False, 'reason': 'Đang dùng cho hồ sơ nhân viên khác.'}
            else:
                candidates.append(partner.id)
        if not candidates:
            return result
        documents = [(model_name, tuple(rows)) for model_name, rows in doomed.items() if rows]
        documents.append(('res.partner', tuple(candidates)))
        clauses, params = [], []
        for model_name, ids in documents:
            clauses.append('(model = %s AND res_id IN %s)')
            params += [model_name, ids]
        cr.execute(f'SELECT id FROM mail_message WHERE {" OR ".join(clauses)}', params)
        messages = _ids(row[0] for row in cr.fetchall())
        exclude = self._tp_doomed_exclusions(doomed)
        exclude['res.partner'] = ('"id" NOT IN %s', [tuple(candidates)])
        exclude['mail.message'] = ('"id" NOT IN %s', [messages])
        exclude['mail.notification'] = ('"mail_message_id" NOT IN %s', [messages])
        follower_clauses = ' OR '.join(clause.replace('model', 'res_model') for clause in clauses)
        exclude['mail.followers'] = (f'NOT ({follower_clauses})', list(params))
        used = {partner_id: [] for partner_id in candidates}
        for model_name, field_name, counts in self._tp_stored_references({'res.partner': candidates}, exclude):
            for partner_id, count in counts['res.partner'].items():
                used[partner_id].append(f'{self._tp_label(model_name, field_name)} ({count})')
        for partner_id, places in used.items():
            if places:
                result[partner_id] = {'delete': False, 'reason': 'Còn được dùng ở: ' + ', '.join(places[:5]) + ('…' if len(places) > 5 else '')}
            else:
                result[partner_id] = {'delete': True, 'reason': 'Liên hệ công việc riêng của hồ sơ, không còn dùng ở nơi khác.'}
        return result

    def _tp_delete_plan(self):
        """Full plan of these employees; deterministic for the digest."""
        # The scan below reads the database directly: pending ORM writes first.
        self.env.flush_all()
        employees = self.sudo().with_context(active_test=False)
        doomed = self._tp_doomed()
        plan = {}
        for employee in employees:
            plan[employee.id] = {
                'id': employee.id,
                'name': employee.name,
                'code': employee.tp_employee_code or '',
                'source_code': employee.tp_source_code or '',
                'department': employee.department_id.display_name or '',
                'department_id': employee.department_id.id,
                'job': employee.job_id.display_name or '',
                'active': employee.active,
                'company_id': employee.company_id.id,
                'write_date': str(employee.write_date),
                'user_id': employee.user_id.id,
                'login': employee.user_id.login or '',
                'partner_id': employee.work_contact_id.id,
                'import_batch_id': employee.tp_import_batch_id.id,
                'delete': [],
                'keep': [],
                'block': [],
                'versions': sorted([version.id, str(version.write_date)] for version in employee.version_ids),
                'import_lines': [],
            }
        # Owned rows, the own resource and own many2many links.
        for model_name, label in OWNED_MODELS.items():
            rows = doomed.get(model_name) or {}
            for employee_id in plan:
                count = sum(1 for owner in rows.values() if owner == employee_id)
                if count:
                    plan[employee_id]['delete'].append([label, count])
        for employee in employees:
            if employee.resource_id:
                plan[employee.id]['delete'].append(['Tài nguyên lịch làm việc của hồ sơ', 1])
            for field in employee._fields.values():
                if field.type == 'many2many' and field.store and field.relation and employee[field.name]:
                    plan[employee.id]['delete'].append([f'Liên kết {field._description_string(self.env)} (giữ bản ghi gốc)', len(employee[field.name])])
        cleanup, blocking, cleanup_ids = self._tp_document_links(doomed)
        for (model_name, _field), counts in sorted(cleanup.items()):
            for employee_id, count in counts.items():
                plan[employee_id]['delete'].append([CLEANUP_MODELS[model_name], count])
        for (model_name, field_name), counts in sorted(blocking.items()):
            for employee_id, count in counts.items():
                plan[employee_id]['block'].append([self._tp_label(model_name, field_name), count, _GENERIC_HINT])
        # Stored links from other records.
        targets = {model_name: list(rows) for model_name, rows in doomed.items() if rows}
        for model_name, field_name, counts in self._tp_stored_references(targets, self._tp_doomed_exclusions(doomed)):
            for target, rows in counts.items():
                for record_id, count in rows.items():
                    employee_id = doomed[target].get(record_id)
                    key = (model_name, field_name)
                    if key in KEPT_REFERENCES:
                        plan[employee_id]['keep'].append([KEPT_REFERENCES[key], count])
                    else:
                        plan[employee_id]['block'].append([self._tp_label(model_name, field_name), count, HINTS.get(key, _GENERIC_HINT)])
        lines = self.env['tp.hr.import.line'].sudo().search([('employee_id', 'in', employees.ids)], order='id')
        for line in lines:
            plan[line.employee_id.id]['import_lines'].append([line.id, line.batch_id.id])
        for employee in employees:
            if employee.tp_import_batch_id:
                plan[employee.id]['keep'].append(['Lô nhập và file Excel gốc được giữ nguyên', 1])
        partners = self._tp_partner_plan(doomed)
        for employee in employees:
            decision = partners.get(employee.work_contact_id.id)
            if decision:
                entry = ['Liên hệ công việc ' + (employee.work_contact_id.display_name or ''), decision['reason']]
                plan[employee.id]['delete' if decision['delete'] else 'keep'].append(entry)
        for entry in plan.values():
            for key in ('delete', 'keep', 'block'):
                entry[key].sort(key=lambda item: [str(part) for part in item])
        return {
            'employees': plan,
            'partners': {str(partner_id): decision for partner_id, decision in sorted(partners.items())},
            'cleanup': {model_name: sorted(ids) for model_name, ids in sorted(cleanup_ids.items())},
            'doomed': {model_name: sorted(rows) for model_name, rows in sorted(doomed.items())},
        }

    @api.model
    def _tp_digest(self, value):
        return hashlib.sha256(json.dumps(value, sort_keys=True, default=str, ensure_ascii=False).encode()).hexdigest()

    # ------------------------------------------------------------------
    # Execution (caller verified rights, password, accounts and digest)
    # ------------------------------------------------------------------
    def _tp_delete_lock(self):
        """Serialize with creation, roster import and transfers; lock the rows."""
        employees = self.sudo().with_context(active_test=False)
        for company_id in sorted(set(employees.mapped('company_id').ids)):
            self.env.cr.execute('SELECT pg_advisory_xact_lock(%s, %s)', [761101, company_id])
        self.env.cr.execute('SELECT id FROM hr_employee WHERE id IN %s ORDER BY id FOR UPDATE', [_ids(self.ids)])
        locked = {row[0] for row in self.env.cr.fetchall()}
        if locked != set(self.ids):
            raise UserError(self.env._('Có hồ sơ vừa bị xóa bởi phiên khác. Hãy tải lại danh sách và xem trước lại.'))
        resources = employees.mapped('resource_id').ids
        if resources:
            self.env.cr.execute('SELECT id FROM resource_resource WHERE id IN %s ORDER BY id FOR UPDATE', [tuple(resources)])
        self.env.invalidate_all()

    def _tp_permanent_unlink(self, plan, audit_vals_list):
        """Delete the employees, sweep their document rows, then write the audit.

        Runs inside the caller's transaction: any error rolls everything back
        (audit included). Returns ``{partner_id: 'deleted' | reason}`` for
        work contacts; the outcome is also stored in each audit snapshot.
        """
        blocked = {employee_id: entry['block'] for employee_id, entry in plan['employees'].items() if entry['block']}
        if blocked:
            raise UserError(self.env._('Có hồ sơ đang bị chặn; không hồ sơ nào bị xóa.'))
        employees = self.sudo().with_context(active_test=False)
        employees.with_context(_tp_employee_delete=_TP_DELETE).unlink()
        # Rows deleted by database cascade bypass the ORM; remove their
        # chatter, followers, activities, files and xmlids through the ORM
        # (shared file blobs stay with Odoo's attachment garbage collector).
        cr = self.env.cr
        for model_name, rows in plan['doomed'].items():
            if model_name in ('hr.employee', 'resource.resource') or not rows:
                continue
            for cleanup_model in CLEANUP_MODELS:
                Cleanup = self.env[cleanup_model].sudo().with_context(active_test=False)
                model_field = 'model' if cleanup_model in ('mail.message', 'mail.scheduled.message', 'ir.model.data') else 'res_model'
                cr.execute(f'SELECT id FROM "{Cleanup._table}" WHERE "{model_field}" = %s AND res_id IN %s', [model_name, tuple(rows)])
                orphans = Cleanup.browse(row[0] for row in cr.fetchall())
                if orphans:
                    orphans.unlink()
        result = {}
        Partner = self.env['res.partner'].sudo().with_context(active_test=False)
        for partner_id, decision in plan['partners'].items():
            partner = Partner.browse(int(partner_id)).exists()
            if not decision['delete'] or not partner:
                result[partner_id] = decision['reason']
                continue
            try:
                with cr.savepoint():
                    partner.unlink()
                result[partner_id] = 'deleted'
            except (UserError, AccessError, IntegrityError):
                result[partner_id] = 'Giữ lại vì Odoo không cho xóa liên hệ này (còn dữ liệu liên quan).'
        self.env.invalidate_all()
        for vals in audit_vals_list:
            entry = plan['employees'][vals['employee_ref']]
            snapshot = dict(vals.get('snapshot') or {})
            # The import trace is always part of the audit, whoever calls the core.
            snapshot.setdefault('import_lines', entry['import_lines'])
            if entry['partner_id']:
                outcome = result.get(str(entry['partner_id']), '')
                snapshot['work_contact'] = 'Đã xóa' if outcome == 'deleted' else outcome
            vals['snapshot'] = snapshot
        self.env['tp.hr.employee.audit']._tp_record(audit_vals_list)
        return result
