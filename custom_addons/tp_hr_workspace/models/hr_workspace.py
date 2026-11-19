"""One permission-scoped population for HR charts, drill-down and work-directory XLSX."""
import io
from datetime import date, datetime
from itertools import groupby
from math import ceil

import xlsxwriter

from odoo import api, fields, models
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.fields import Domain

# Business fields only: binaries, credentials and payroll are deliberately absent.
EMPLOYEE_EXPORT_COLUMNS = [
    ('tp_employee_code', 'Mã nhân viên', 17), ('name', 'Họ và tên', 30),
    ('department_id', 'Phòng ban', 30), ('job_id', 'Chức vụ', 25),
    ('tp_employment_kind', 'Loại hình lao động', 20), ('mobile_phone', 'Số điện thoại', 19),
    ('work_email', 'Email công việc', 32), ('tp_user_login', 'Tên đăng nhập', 23),
    ('tp_account_status', 'Tình trạng tài khoản', 21), ('active', 'Tình trạng hồ sơ', 20),
    ('work_phone', 'Điện thoại công việc', 20), ('company_id', 'Công ty', 30),
    ('job_title', 'Chức danh mô tả', 25), ('tp_source_title', 'Chức vụ nguồn', 25),
    ('parent_id', 'Quản lý trực tiếp', 28), ('coach_id', 'Người hướng dẫn', 28),
    ('work_location_id', 'Nơi làm việc', 28), ('address_id', 'Địa chỉ làm việc', 30),
    ('resource_calendar_id', 'Lịch làm việc', 26), ('category_ids', 'Nhãn nhân viên', 28),
    ('legal_name', 'Họ tên pháp lý', 30), ('birthday', 'Ngày sinh', 15),
    ('sex', 'Giới tính', 15), ('country_id', 'Quốc tịch', 20),
    ('place_of_birth', 'Nơi sinh', 25), ('country_of_birth', 'Quốc gia nơi sinh', 23),
    ('private_phone', 'Điện thoại cá nhân', 20), ('private_email', 'Email cá nhân', 32),
    ('private_street', 'Địa chỉ cá nhân', 35), ('private_street2', 'Phường / Xã', 25),
    ('private_city', 'Quận / Huyện', 25), ('private_state_id', 'Tỉnh / Thành phố', 25),
    ('private_zip', 'Mã bưu chính', 17), ('private_country_id', 'Quốc gia cư trú', 23),
    ('identification_id', 'Số CCCD / CMND', 23), ('passport_id', 'Số hộ chiếu', 23),
    ('passport_expiration_date', 'Hạn hộ chiếu', 17), ('permit_no', 'Số giấy phép lao động', 25),
    ('work_permit_expiration_date', 'Hạn giấy phép lao động', 22),
    ('visa_no', 'Số thị thực', 23), ('visa_expire', 'Hạn thị thực', 17),
    ('marital', 'Tình trạng hôn nhân', 23), ('spouse_complete_name', 'Họ tên vợ / chồng', 28),
    ('spouse_birthdate', 'Ngày sinh vợ / chồng', 20), ('children', 'Số con phụ thuộc', 18),
    ('certificate', 'Trình độ học vấn', 23), ('study_field', 'Chuyên ngành', 28),
    ('emergency_contact', 'Liên hệ khẩn cấp', 28),
    ('emergency_phone', 'Điện thoại khẩn cấp', 22),
    ('date_version', 'Ngày hiệu lực hồ sơ', 20), ('contract_date_start', 'Ngày bắt đầu hợp đồng hiện tại', 24),
    ('contract_date_end', 'Ngày kết thúc hợp đồng hiện tại', 24), ('trial_date_end', 'Ngày hết thử việc', 20),
    ('departure_date', 'Ngày nghỉ việc', 18), ('tp_missing_basic', 'Thông tin cần bổ sung', 40),
    ('additional_note', 'Ghi chú', 48),
]
EXPORT_SCOPE_LABELS = {
    'filtered': 'Toàn bộ kết quả theo bộ lọc đang áp dụng',
    'all': 'Toàn bộ nhân viên trong quyền quản lý (kể cả lưu trữ)',
    'selected': 'Các nhân viên đã chọn trong kết quả lọc',
}


def employee_export_order_key(employee):
    department = employee.department_id
    return (not bool(department), department.tp_sequence if department else 0,
            department.id or 0, employee.sequence, employee.id)


class HrWorkspace(models.AbstractModel):
    _name = 'tp.hr.workspace'
    _description = 'TP HR overview and reports'

    @api.model
    def _tp_population_source(self):
        """Employee model and fixed row scope; a scoped adapter may narrow rows."""
        if not self.env.user.has_group('hr.group_hr_user'):
            raise AccessError(self.env._('Chỉ nhân sự được giao mới được xem báo cáo HR.'))
        employees = self.env['hr.employee'].with_context(active_test=False)
        employees.check_access('read')
        return employees, []

    @api.model
    def _tp_action_domain(self, employees, domain, extra_domain):
        return domain + (extra_domain or [])

    @api.model
    def _population(self, filters=None):
        employees, scope = self._tp_population_source()
        filters = filters or {}
        if not isinstance(filters, dict) or set(filters) - {'department_id', 'job_id', 'status', 'employment_kind', 'missing_basic'}:
            raise ValidationError(self.env._('Bộ lọc HR không hợp lệ.'))
        status = filters.get('status') or 'active'
        if status not in ('active', 'archived', 'all'):
            raise ValidationError(self.env._('Trạng thái hồ sơ không hợp lệ.'))
        domain = [('company_id', '=', self.env.company.id)] + scope
        if status != 'all':
            domain.append(('active', '=', status == 'active'))
        for field, model, label in [('department_id', 'hr.department', 'Đơn vị'), ('job_id', 'hr.job', 'Chức vụ')]:
            value = filters.get(field)
            if value in (None, False, ''):
                continue
            try:
                if isinstance(value, bool) or str(int(value)) != str(value) or int(value) <= 0:
                    raise ValueError  # noqa: TRY301 - one localized filter validation
                value = int(value)
            except (ValueError, TypeError) as exc:
                raise ValidationError(self.env._('%s không hợp lệ.', label)) from exc
            record = self.env[model].with_context(active_test=False).browse(value).exists()
            record.check_access('read')
            if not record or record.company_id not in (self.env.company, self.env['res.company']):
                raise AccessError(self.env._('%s nằm ngoài công ty đang xem.', label))
            domain.append((field, '=', value))
        kind = filters.get('employment_kind')
        if kind:
            if kind not in ('short_term', 'long_term', 'outsourced', 'unknown'):
                raise ValidationError(self.env._('Loại hình lao động không hợp lệ.'))
            domain.append(('tp_employment_kind', '=', False if kind == 'unknown' else kind))
        if filters.get('missing_basic') not in (None, False, True, '', '1'):
            raise ValidationError(self.env._('Bộ lọc hồ sơ cần bổ sung không hợp lệ.'))
        if filters.get('missing_basic'):
            domain += self.env['hr.employee']._tp_missing_domain()
        return employees, domain, status

    @api.model
    def get_overview(self, filters=None):
        employees, domain, _status = self._population(filters)
        total = employees.search_count(domain)
        groups = employees._read_group(domain, ['department_id'], ['__count'])
        departments = [
            {'id': department.id or 0, 'name': department.name if department else 'Chưa khai báo đơn vị',
             'count': count, 'percent': count / total * 100 if total else 0}
            for department, count in groups
        ]
        departments.sort(key=lambda row: row['name'].casefold())
        missing_domain = employees._tp_missing_domain()
        missing = employees.search_count(domain + missing_domain)
        linked = employees.search_count(domain + [('user_id', '!=', False)])
        job_groups = employees._read_group(domain, ['job_id'], ['__count'])
        jobs = [{'id': job.id or 0, 'name': job.name if job else 'Chưa khai báo chức vụ',
                 'count': count, 'percent': count / total * 100 if total else 0} for job, count in job_groups]
        jobs.sort(key=lambda row: (-row['count'], row['name'].casefold(), row['id']))
        linked_by_unit = dict(employees._read_group(domain + [('user_id', '!=', False)], ['department_id'], ['__count']))
        missing_by_unit = dict(employees._read_group(domain + missing_domain, ['department_id'], ['__count']))
        for row in departments:
            department = self.env['hr.department'].browse(row['id'])
            row.update(linked=linked_by_unit.get(department, 0), missing=missing_by_unit.get(department, 0))
            row['pending'] = row['count'] - row['linked']
        catalog_scope = [('company_id', 'in', [False, self.env.company.id])]

        def catalog(model):
            return [{'id': record.id, 'name': record.name} for record in
                    self.env[model].with_context(active_test=False).search(catalog_scope, order='name, id')]
        return {
            'total': total, 'units': sum(bool(row['id']) for row in departments),
            'departments': departments, 'missing_basic': missing, 'complete_basic': total - missing,
            'linked': linked, 'pending': total - linked, 'domain': domain,
            'jobs': jobs, 'catalog_departments': catalog('hr.department'), 'catalog_jobs': catalog('hr.job'),
            'can_create': self.env['hr.employee'].has_access('create'), 'employee_form_id': self.env.ref('tp_hr_workspace.employee_form').id,
            'missing_domain': employees._tp_missing_domain(),
            'missing_code': employees.search_count(domain + [('tp_employee_code', '=', False)]),
            'missing_department': employees.search_count(domain + [('department_id', '=', False)]),
            'locked': employees.search_count(domain + [('tp_account_status', '=', 'disabled')]),
            'missing_job': employees.search_count(domain + [('job_id', '=', False)]),
            'missing_contact': employees.search_count(domain + [('work_email', '=', False), ('work_phone', '=', False), ('mobile_phone', '=', False)]),
            'updated_at': fields.Datetime.context_timestamp(
                self.with_context(tz=self.env.context.get('tz') or self.env.user.tz or 'Asia/Ho_Chi_Minh'),
                fields.Datetime.now(),
            ).strftime('%d/%m/%Y %H:%M %Z'),
        }

    @api.model
    def action_employees(self, filters=None, extra_domain=None):
        employees, domain, _status = self._population(filters)
        if extra_domain is not None and not isinstance(extra_domain, list):
            raise ValidationError(self.env._('Bộ lọc danh sách không hợp lệ.'))
        action = self.env['ir.actions.actions']._for_xml_id('tp_hr_workspace.action_employees')
        action.update(domain=self._tp_action_domain(employees, domain, extra_domain), context={
            'active_test': False, 'tp_hr_leaf': 'tp_hr_workspace.menu_employees',
            'tp_hr_missing': [tuple(item) if isinstance(item, list) else item for item in (extra_domain or [])] == employees._tp_missing_domain(),
        })
        return action

    @api.model
    def _employee_export_records(self, options=None):
        if not self.env.user.has_group('hr.group_hr_user'):
            raise AccessError(self.env._('Chỉ nhân sự được giao mới được xuất danh sách nhân viên.'))
        options = {} if options is None else options
        allowed = {'scope', 'domain', 'selected_ids', 'selection_all', 'active_test', 'filter_label'}
        if not isinstance(options, dict) or set(options) - allowed:
            raise ValidationError(self.env._('Phạm vi xuất không hợp lệ.'))
        scope = options.get('scope', 'filtered')
        if scope not in EXPORT_SCOPE_LABELS:
            raise ValidationError(self.env._('Phạm vi xuất không hợp lệ.'))
        if not isinstance(options.get('active_test', True), bool) or not isinstance(options.get('selection_all', False), bool):
            raise ValidationError(self.env._('Phạm vi xuất không hợp lệ.'))
        label = options.get('filter_label', '')
        if not isinstance(label, str) or len(label) > 4000:
            raise ValidationError(self.env._('Mô tả bộ lọc không hợp lệ.'))
        # Reuse the workspace scope, but never an elevated projection from an adapter.
        source, fixed_scope = self._tp_population_source()
        employees = source.sudo(False).with_context(active_test=False, version_id=False)
        raw_domain = options.get('domain', [])
        if not isinstance(raw_domain, list):
            raise ValidationError(self.env._('Bộ lọc danh sách không hợp lệ.'))
        try:
            domain = Domain(raw_domain)
            self._check_export_domain(employees, domain)
            domain.validate(employees)
        except (ValueError, TypeError, KeyError) as exc:
            raise ValidationError(self.env._('Bộ lọc danh sách không hợp lệ.')) from exc
        mandatory = Domain.AND([Domain(fixed_scope), Domain('company_id', 'in', self.env.companies.ids)])
        if scope != 'all':
            mandatory &= domain
        if scope == 'selected' and not options.get('selection_all', False):
            ids = options.get('selected_ids', [])
            if not isinstance(ids, list) or any(type(value) is not int or value <= 0 for value in ids):
                raise ValidationError(self.env._('Danh sách nhân viên đã chọn không hợp lệ.'))
            mandatory &= Domain('id', 'in', ids)
        employees = employees.with_context(active_test=scope != 'all' and options.get('active_test', True))
        records = employees.search(mandatory, order='sequence, id')
        records = records.sorted(key=employee_export_order_key)
        return records, scope, label if scope != 'all' else ''

    @api.model
    def _check_export_domain(self, model, domain):
        for condition in domain.iter_conditions():
            target = model
            for part in condition.field_expr.split('.'):
                field = target._fields.get(part)
                if not field or field.type == 'binary' or (target._name == 'res.users' and part not in {'id', 'name', 'login', 'active'}):
                    raise ValidationError(self.env._('Trường lọc không được phép xuất.'))
                target.check_field_access(field, 'read')
                if field.relational:
                    target = self.env[field.comodel_name]
                    target.check_access('read')
                else:
                    # Odoo validates suffixes such as birthday.month_number itself.
                    break
            if condition.operator in ('any!', 'not any!'):
                raise ValidationError(self.env._('Toán tử lọc không được phép.'))
            if condition.operator in ('any', 'not any'):
                self._check_export_domain(target, Domain(condition.value))

    @api.model
    def get_employee_export_summary(self, options=None):
        records, scope, label = self._employee_export_records(options)
        return {'count': len(records), 'scope': scope, 'label': EXPORT_SCOPE_LABELS[scope],
                'filter_label': label, 'departments': len(records.department_id)}

    @api.model
    def _export_cell_value(self, record, name):
        value = record[name]
        field = record._fields[name]
        if name == 'active':
            return 'Đang quản lý' if value else 'Lưu trữ'
        if field.type == 'selection':
            return dict(field._description_selection(self.env)).get(value, 'Chưa khai báo')
        if field.relational:
            value.check_access('read')
            return ', '.join(value.mapped('display_name'))
        return value

    @api.model
    def _build_xlsx(self, filters=None, options=None):
        if filters is not None:
            _employees, domain, status = self._population(filters)
            options = {'scope': 'filtered', 'domain': domain, 'active_test': False,
                       'filter_label': {'active': 'Hồ sơ đang quản lý', 'archived': 'Hồ sơ lưu trữ', 'all': 'Tất cả hồ sơ'}[status]}
        records, scope, filter_label = self._employee_export_records(options)
        columns = [col for col in EMPLOYEE_EXPORT_COLUMNS if col[0] in records._fields
                   and records._has_field_access(records._fields[col[0]], 'read')]
        main_columns = [col for col in columns if col[0] in {col[0] for col in EMPLOYEE_EXPORT_COLUMNS[:9]}]
        stream = io.BytesIO()
        book = xlsxwriter.Workbook(stream, {'in_memory': True, 'strings_to_formulas': False, 'strings_to_urls': False})
        book.set_properties({'title': 'TANPHAT ONE — DANH SÁCH NHÂN VIÊN', 'author': 'TANPHAT ONE'})
        base = {'font_name': 'Calibri', 'font_size': 11, 'valign': 'vcenter', 'border': 1, 'border_color': '#DCE4ED', 'text_wrap': True}
        header = book.add_format({**base, 'bold': True, 'font_color': '#FFFFFF', 'bg_color': '#173A54'})
        title = book.add_format({'font_name': 'Calibri', 'bold': True, 'font_size': 19, 'font_color': '#173A54', 'valign': 'vcenter'})
        meta = book.add_format({'font_name': 'Calibri', 'font_size': 11, 'font_color': '#475569', 'text_wrap': True, 'valign': 'vcenter'})
        department_format = book.add_format({**base, 'bold': True, 'bg_color': '#E4F1FA', 'font_color': '#173A54'})
        formats = {}
        for alternate in (False, True):
            bg = '#F5F8FC' if alternate else '#FFFFFF'
            for kind, extra in {'text': {'num_format': '@'}, 'number': {'num_format': '0'}, 'date': {'num_format': 'dd/mm/yyyy'},
                                'Mở': {'font_color': '#16703A', 'bg_color': '#EAF6EE', 'bold': True},
                                'Khóa': {'font_color': '#B54708', 'bg_color': '#FFF1E7', 'bold': True},
                                'Chưa có tài khoản': {'font_color': '#64748B', 'bg_color': '#F1F5F9'}}.items():
                formats[alternate, kind] = book.add_format({**base, 'bg_color': bg, **extra})
        exported_at = fields.Datetime.context_timestamp(
            self.with_context(tz=self.env.context.get('tz') or self.env.user.tz or 'Asia/Ho_Chi_Minh'), fields.Datetime.now(),
        ).strftime('%d/%m/%Y %H:%M %Z')
        description = EXPORT_SCOPE_LABELS[scope] + (f' — {filter_label}' if filter_label else '')

        def new_sheet(name, schema, presentation=False):
            sheet = book.add_worksheet(name)
            end = len(schema)
            sheet.hide_gridlines(2)
            sheet.set_tab_color('#173A54' if presentation else '#3395A5')
            sheet.merge_range(0, 0, 0, min(end, 9), 'TANPHAT ONE — DANH SÁCH NHÂN VIÊN', title)
            sheet.set_row(0, 36)
            sheet.merge_range(1, 0, 1, min(end, 9), f"{', '.join(self.env.companies.mapped('name'))} | Xuất lúc {exported_at}", meta)
            sheet.set_row(1, 30)
            sheet.merge_range(2, 0, 2, min(end, 9), description, meta)
            sheet.set_row(2, 42)
            sheet.merge_range(3, 0, 3, min(end, 9), f'Tổng số nhân viên: {len(records)} | Thứ tự phòng ban và nhân viên đã lưu', meta)
            sheet.set_row(3, 24)
            sheet.write_row(5, 0, ['STT', *[col[1] for col in schema]], header)
            sheet.set_row(5, 38)
            sheet.set_column(0, 0, 7)
            for index, col in enumerate(schema, 1):
                sheet.set_column(index, index, col[2])
            sheet.freeze_panes(6, 3)
            sheet.set_landscape()
            sheet.set_paper(8 if presentation else 9)  # A3 presentation, A4 detail panels at readable scale.
            if presentation:
                sheet.fit_to_pages(1, 0)
            else:
                sheet.set_print_scale(85)
            sheet.repeat_rows(0, 5)
            sheet.set_margins(0.25, 0.25, 0.35, 0.4)
            sheet.set_footer('&LTANPHAT ONE&RTrang &P / &N')
            return sheet

        def write_value(sheet, row, col, value, alternate, field_name=''):
            kind = 'text'
            if isinstance(value, datetime):
                value = value.replace(tzinfo=None)
                kind = 'date'
            elif isinstance(value, date):
                kind = 'date'
            elif type(value) in (int, float):
                kind = 'number'
            elif field_name == 'tp_account_status' and value in ('Mở', 'Khóa', 'Chưa có tài khoản'):
                kind = value
            fmt = formats[alternate, kind]
            if value is None or value is False or (isinstance(value, str) and not value):
                sheet.write_blank(row, col, None, fmt)
            elif kind == 'date':
                sheet.write_datetime(row, col, value, fmt)
            elif kind == 'number':
                sheet.write_number(row, col, value, fmt)
            else:
                sheet.write_string(row, col, str(value), fmt)

        def row_height(values, schema):
            lines = max((sum(max(1, ceil(len(line) / max(8, width - 2))) for line in str(value or '').split('\n'))
                         for value, (_name, _label, width) in zip(values, schema, strict=True)), default=1)
            return min(409, max(36, lines * 16 + 6))

        # Read once, using the caller's field and record permissions, for identical sheet order.
        rows = [(employee, {col[0]: self._export_cell_value(employee, col[0]) for col in columns}) for employee in records]
        main = new_sheet('Danh sách nhân viên', main_columns, True)
        row = 6
        number = 0
        for department, members in groupby(rows, key=lambda item: item[0].department_id):
            members = list(members)
            main.merge_range(row, 0, row, len(main_columns),
                             f"{department.name if department else 'Chưa khai báo phòng ban'} — {len(members)} nhân viên", department_format)
            main.set_row(row, 26)
            row += 1
            for _employee, values in members:
                number += 1
                main.set_row(row, row_height([values[col[0]] for col in main_columns], main_columns))
                write_value(main, row, 0, number, number % 2 == 0)
                for col, (name, _label, _width) in enumerate(main_columns, 1):
                    write_value(main, row, col, values[name], number % 2 == 0, name)
                row += 1
        if not rows:
            main.merge_range(row, 0, row, len(main_columns), 'Không có nhân viên trong phạm vi xuất.', meta)
        main.print_area(0, 0, max(row, 6), len(main_columns))
        detail = new_sheet('Dữ liệu chi tiết', columns)
        for row_index, (_employee, values) in enumerate(rows, 6):
            detail.set_row(row_index, row_height([values[col[0]] for col in columns], columns))
            write_value(detail, row_index, 0, row_index - 5, row_index % 2 == 0)
            for col, (name, _label, _width) in enumerate(columns, 1):
                write_value(detail, row_index, col, values[name], row_index % 2 == 0, name)
        detail.autofilter(5, 0, max(5, 5 + len(rows)), len(columns))
        detail.print_area(0, 0, max(6, 5 + len(rows)), len(columns))
        self._write_export_contracts(records, new_sheet, write_value, row_height)
        book.close()
        return stream.getvalue()

    @api.model
    def _write_export_contracts(self, records, new_sheet, write_value, row_height):
        documents = self.env['tp.hr.contract.document'].with_context(active_test=False)
        versions = self.env['hr.version'].with_context(active_test=False)
        if not documents.has_access('read') or not versions.has_access('read'):
            return
        document_columns = [('number', 'Số hợp đồng', 23), ('name', 'Tên / trích yếu', 35),
                            ('kind', 'Loại giấy tờ', 23), ('signed_date', 'Ngày ký', 17),
                            ('service_start', 'Ngày bắt đầu thuê khoán', 24),
                            ('service_end', 'Ngày kết thúc thuê khoán', 24), ('note', 'Ghi chú hợp đồng', 48)]
        document_columns = [col for col in document_columns if documents._has_field_access(documents._fields[col[0]], 'read')]
        date_columns = [('contract_date_start', 'Ngày bắt đầu hợp đồng', 24),
                        ('contract_date_end', 'Ngày kết thúc hợp đồng', 24)]
        date_columns = [col for col in date_columns if versions._has_field_access(versions._fields[col[0]], 'read')]
        if not documents._has_field_access(documents._fields['employee_id'], 'read') or not date_columns:
            return
        domain = [('employee_id', 'in', records.ids), ('company_id', 'in', self.env.companies.ids)]
        contracts = documents.search(domain, order='id')
        version_rows = versions.search(domain, order='date_version, id')
        schema = [('tp_employee_code', 'Mã nhân viên', 17), ('name', 'Họ và tên', 30),
                  ('department_id', 'Phòng ban', 30), *document_columns, *date_columns]
        by_employee = contracts.grouped('employee_id')
        by_document = version_rows.filtered('tp_contract_document_id').grouped('tp_contract_document_id')
        native = version_rows.filtered(lambda v: not v.tp_contract_document_id and v.contract_date_start).grouped('employee_id')
        if not contracts and not native:
            return
        sheet = new_sheet('Hợp đồng lao động', schema)
        row = 6
        for employee in records:
            entries = []
            for contract in by_employee.get(employee, documents):
                related = by_document.get(contract, versions)
                values = [self._export_cell_value(contract, col[0]) for col in document_columns]
                values += [related[-1][col[0]] if related else False for col in date_columns]
                entries.append(values)
            seen_dates = set()
            for version in native.get(employee, versions):
                period = (version.contract_date_start, version.contract_date_end)
                if period not in seen_dates:
                    seen_dates.add(period)
                    entries.append([False] * len(document_columns) + [version[col[0]] for col in date_columns])
            for values in entries:
                values = [employee.tp_employee_code, employee.name, employee.department_id.name, *values]
                write_value(sheet, row, 0, row - 5, row % 2 == 0)
                for col, value in enumerate(values, 1):
                    write_value(sheet, row, col, value, row % 2 == 0)
                sheet.set_row(row, row_height(values, schema))
                row += 1
        sheet.autofilter(5, 0, row - 1, len(schema))
        sheet.print_area(0, 0, row - 1, len(schema))


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    tp_user_login = fields.Char(
        string='Tên đăng nhập',
        related='user_id.login',
        store=True,
        readonly=True,
        index=True,
        groups='hr.group_hr_user,base.group_system',
    )
    tp_account_status = fields.Selection(
        [
            ('unlinked', 'Chưa có tài khoản'),
            ('active', 'Mở'),
            ('disabled', 'Khóa'),
        ],
        string='Tình trạng',
        compute='_compute_tp_account_status',
        store=True,
        index=True,
        groups='hr.group_hr_user,base.group_system',
    )

    @api.depends('user_id', 'user_id.active', 'user_id.tp_hr_locked')
    def _compute_tp_account_status(self):
        for rec in self:
            if not rec.user_id:
                rec.tp_account_status = 'unlinked'
            elif rec.user_id.active and not rec.user_id.tp_hr_locked:
                rec.tp_account_status = 'active'
            else:
                rec.tp_account_status = 'disabled'

    def write(self, vals):
        if 'user_id' in vals and not self.env.su and not self.env.user.has_group('base.group_system'):
            raise AccessError(self.env._('Chỉ Quản trị viên hệ thống mới có quyền liên kết hoặc thay đổi tài khoản người dùng.'))
        return super().write(vals)

    def action_open_account_dialog(self):
        self.ensure_one()
        self.check_access('read')
        wizard = self.env['tp.hr.account.wizard'].create({
            'employee_id': self.id,
            'current_user_id': self.user_id.id if self.user_id else False,
            'expected_user_id': self.user_id.id if self.user_id else False,
        })
        if not self.user_id and self.env.user.has_group('base.group_system'):
            return wizard.action_prepare_credentials()
        return {
            'type': 'ir.actions.act_window',
            'name': self.env._('Tài khoản nhân viên — %s', self.name),
            'res_model': 'tp.hr.account.wizard',
            'res_id': wizard.id,
            'view_mode': 'form',
            'target': 'new',
            'views': [(self.env.ref('tp_hr_workspace.view_tp_hr_account_wizard_form').id, 'form')],
        }

    def action_reset_user_password(self):
        self._tp_account_admin(existing=True)
        wizard = self.env['tp.hr.account.wizard'].create({'employee_id': self.id, 'expected_user_id': self.user_id.id})
        return wizard.action_prepare_credentials(reset=True)

    def action_open_versions(self):
        self.ensure_one()
        self.check_access('read')
        action = super().action_open_versions()
        # Native wage analytics aggregate technical defaults before wages are confirmed.
        action.update(view_mode='list', views=[(self.env.ref('tp_hr_workspace.version_list').id, 'list')])
        action['name'] = self.env._('Phiên bản hồ sơ — %s', self.name)
        return action

    def action_tp_credentials(self):
        self.ensure_one()
        self.check_access('read')
        if not self.env.user.has_group('hr.group_hr_user'):
            raise AccessError(self.env._('Chỉ nhân sự được giao mới được xem liên kết hồ sơ.'))
        if 'tp.credential' not in self.env:
            raise UserError(self.env._('Chưa có sổ chứng chỉ tổng hợp. Dùng kỹ năng và hồ sơ cá nhân được giao.'))
        credentials = self.env['tp.credential']
        if not credentials.has_access('read'):
            raise AccessError(self.env._('Bạn chưa được giao quyền đọc sổ chứng chỉ. Liên kết HR không cấp thêm quyền KH-KD.'))
        # No name matching: the native work contact is the only verified identity key.
        domain = [('subject_kind', '=', 'person'), ('subject_id', '=', self.work_contact_id.id), ('company_id', '=', self.company_id.id)]
        return {'type': 'ir.actions.act_window', 'name': self.env._('Chứng chỉ cá nhân có quyền xem'),
                'res_model': 'tp.credential', 'view_mode': 'list,form', 'domain': domain,
                'context': {'create': False, 'edit': False, 'delete': False}}


class ResourceResource(models.Model):
    _inherit = 'resource.resource'

    def write(self, vals):
        if 'user_id' in vals and not self.env.su and not self.env.user.has_group('base.group_system'):
            employees = self.env['hr.employee'].sudo().with_context(active_test=False).search([('resource_id', 'in', self.ids)])
            if employees:
                raise AccessError(self.env._('Chỉ Quản trị viên hệ thống mới có quyền thay đổi tài khoản người dùng gắn với nhân viên.'))
        return super().write(vals)


class HrImportBatch(models.Model):
    _inherit = 'tp.hr.import.batch'

    def action_open_lines(self):
        self.ensure_one()
        self._manager()
        return {'type': 'ir.actions.act_window', 'name': self.env._('Bảng đối chiếu nguồn'),
                'res_model': 'tp.hr.import.line', 'view_mode': 'list',
                'views': [(self.env.ref('tp_hr_workspace.import_lines').id, 'list')],
                'domain': [('batch_id', '=', self.id)],
                'context': {'create': False, 'delete': False, 'edit': self.state == 'preview'}}
