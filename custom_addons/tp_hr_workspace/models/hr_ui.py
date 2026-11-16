"""Read-only presentation counts use the same visible, active population as drill-downs."""
from odoo import api, fields, models


def employee_domain(records, field):
    return [(field, 'in', records.ids), ('active', '=', True),
            ('company_id', 'in', records.env.companies.ids)]


def count_employees(records, field):
    employees = records.env['hr.employee'].with_context(active_test=False)
    counts = dict(employees._read_group(employee_domain(records, field), [field], ['__count']))
    for record in records:
        record.tp_visible_employee_count = counts.get(record, 0)


def open_employees(record, field):
    record.ensure_one()
    record.check_access('read')
    action = record.env['ir.actions.actions']._for_xml_id('tp_hr_workspace.action_employees')
    action.update(domain=employee_domain(record, field), context={
        'active_test': False, 'default_' + field: [(6, 0, record.ids)] if field == 'category_ids' else record.id,
        'tp_hr_leaf': 'tp_hr_workspace.menu_employees',
    })
    return action


class Department(models.Model):
    _inherit = 'hr.department'

    tp_visible_employee_count = fields.Integer(string='Số nhân viên', compute='_compute_tp_visible_employee_count', groups='hr.group_hr_user')
    tp_manager_label = fields.Char(string='Người quản lý', compute='_compute_tp_manager_label', groups='hr.group_hr_user')

    @api.depends('member_ids.active', 'member_ids.department_id')
    @api.depends_context('uid', 'allowed_company_ids')
    def _compute_tp_visible_employee_count(self):
        count_employees(self, 'department_id')

    @api.depends('manager_id.name')
    def _compute_tp_manager_label(self):
        for department in self:
            department.tp_manager_label = department.manager_id.name or self.env._('Chưa khai báo')

    def action_tp_employees(self):
        return open_employees(self, 'department_id')


class Job(models.Model):
    _inherit = 'hr.job'

    tp_visible_employee_count = fields.Integer(string='Số nhân viên', compute='_compute_tp_visible_employee_count', groups='hr.group_hr_user')

    @api.depends('employee_ids.active', 'employee_ids.job_id')
    @api.depends_context('uid', 'allowed_company_ids')
    def _compute_tp_visible_employee_count(self):
        count_employees(self, 'job_id')

    def action_tp_employees(self):
        return open_employees(self, 'job_id')


class EmployeeCategory(models.Model):
    _inherit = 'hr.employee.category'

    tp_visible_employee_count = fields.Integer(string='Số nhân viên', compute='_compute_tp_visible_employee_count', groups='hr.group_hr_user')

    @api.depends('employee_ids.active', 'employee_ids.category_ids')
    @api.depends_context('uid', 'allowed_company_ids')
    def _compute_tp_visible_employee_count(self):
        employees = self.env['hr.employee'].with_context(active_test=False)
        # Many-to-many grouping is not supported by _read_group; search each small catalog item.
        for category in self:
            category.tp_visible_employee_count = employees.search_count(employee_domain(category, 'category_ids'))

    def action_tp_employees(self):
        return open_employees(self, 'category_ids')


class ImportBatch(models.Model):
    _inherit = 'tp.hr.import.batch'

    tp_create_count = fields.Integer(compute='_compute_tp_line_counts', string='Tạo mới')
    tp_update_count = fields.Integer(compute='_compute_tp_line_counts', string='Cập nhật')
    tp_skip_count = fields.Integer(compute='_compute_tp_line_counts', string='Bỏ qua')
    tp_conflict_count = fields.Integer(compute='_compute_tp_line_counts', string='Xung đột')

    @api.depends('line_ids.action')
    def _compute_tp_line_counts(self):
        groups = self.env['tp.hr.import.line']._read_group([('batch_id', 'in', self.ids)], ['batch_id', 'action'], ['__count'])
        counts = {(batch.id, action): count for batch, action, count in groups}
        for batch in self:
            for action in ('create', 'update', 'skip', 'conflict'):
                batch['tp_' + action + '_count'] = counts.get((batch.id, action), 0)


_EXEC_DEPARTMENT_NAMES = frozenset({'ban giám đốc', 'ban giam doc', 'ban lãnh đạo', 'ban lanh dao'})


def is_executive_department(department):
    while department:
        if (department.name or '').strip().casefold() in _EXEC_DEPARTMENT_NAMES:
            return True
        department = department.parent_id
    return False


def _tp_role_rank(job_name, exec_dept):
    title = (job_name or '').strip().casefold()
    for token, tier, subrank in (
        ('chủ tịch', 0, 0),
        ('chu tich', 0, 0),
        ('phó tổng giám đốc', 0, 2),
        ('pho tong giam doc', 0, 2),
        ('tổng giám đốc', 0, 1),
        ('tong giam doc', 0, 1),
    ):
        if token in title:
            return tier, subrank
    if exec_dept:
        return 0, 3
    for token, tier, subrank in (
        ('phó giám đốc', 1, 4),
        ('pho giam doc', 1, 4),
        ('giám đốc', 1, 3),
        ('giam doc', 1, 3),
        ('trưởng phòng', 2, 5),
        ('truong phong', 2, 5),
        ('phó phòng', 2, 6),
        ('pho phong', 2, 6),
        ('kế toán trưởng', 2, 7),
        ('ke toan truong', 2, 7),
    ):
        if token in title:
            return tier, subrank
    return 3, 999999


class HrVersion(models.Model):
    _inherit = 'hr.version'

    # Odoo 20 hr/hr_version defines several personal fields with English-only strings/helps.
    country_id = fields.Many2one(string='Quốc tịch')
    identification_id = fields.Char(
        string='Số CCCD / CMND',
        help='Số Căn cước công dân hoặc Chứng minh nhân dân do cơ quan nhà nước cấp, phục vụ lưu trữ hồ sơ và thủ tục pháp lý.',
    )
    passport_id = fields.Char(string='Số hộ chiếu')
    passport_expiration_date = fields.Date(string='Ngày hết hạn hộ chiếu')
    sex = fields.Selection(
        [('male', 'Nam'), ('female', 'Nữ')],
        string='Giới tính',
        groups='hr.group_hr_user',
        tracking=1,
        help='Giới tính theo giấy tờ pháp lý phục vụ hồ sơ nhân sự và bảo hiểm.',
    )
    private_street = fields.Char(string='Số nhà, đường')
    private_street2 = fields.Char(string='Phường / Xã')
    private_city = fields.Char(string='Quận / Huyện / Thành phố')
    private_state_id = fields.Many2one(string='Tỉnh / Thành phố')
    private_zip = fields.Char(string='Mã bưu chính')
    private_country_id = fields.Many2one(string='Quốc gia')
    distance_home_work = fields.Integer(string='Khoảng cách đi làm')
    distance_home_work_unit = fields.Selection(
        [('kilometers', 'km'), ('miles', 'dặm')],
        string='Đơn vị khoảng cách',
    )
    marital = fields.Selection(string='Tình trạng hôn nhân')
    spouse_complete_name = fields.Char(string='Họ tên vợ / chồng')
    spouse_birthdate = fields.Date(string='Ngày sinh vợ / chồng')
    children = fields.Integer(string='Số con phụ thuộc')

    def _get_marital_status_selection(self):
        return [
            ('single', 'Độc thân'),
            ('married', 'Đã kết hôn'),
            ('cohabitant', 'Sống chung hợp pháp'),
            ('widower', 'Góa'),
            ('divorced', 'Đã ly hôn'),
        ]


class Employee(models.Model):
    _inherit = 'hr.employee'

    legal_name = fields.Char(
        string='Họ tên pháp lý',
        help='Họ và tên chính thức theo giấy tờ tùy thân hoặc hồ sơ pháp lý.',
    )
    private_phone = fields.Char(string='Điện thoại cá nhân')
    private_email = fields.Char(string='Email cá nhân')
    place_of_birth = fields.Char(string='Nơi sinh')
    country_of_birth = fields.Many2one(string='Quốc gia nơi sinh')
    birthday = fields.Date(string='Ngày sinh')
    birthday_public_display = fields.Boolean(
        string='Hiển thị ngày sinh nội bộ',
        help='Cho phép đồng nghiệp xem ngày sinh trong không gian nội bộ.',
    )
    bank_account_ids = fields.Many2many(
        string='Tài khoản ngân hàng',
        help='Tài khoản ngân hàng dùng để chi trả lương cho nhân viên.',
    )
    permit_no = fields.Char(string='Số giấy phép lao động')
    visa_no = fields.Char(string='Số thị thực (Visa)')
    visa_expire = fields.Date(string='Ngày hết hạn thị thực')
    work_permit_expiration_date = fields.Date(string='Ngày hết hạn giấy phép lao động')
    has_work_permit = fields.Binary(string='Tệp giấy phép lao động')
    certificate = fields.Selection(string='Trình độ học vấn')
    study_field = fields.Char(string='Chuyên ngành đào tạo')
    emergency_contact = fields.Char(string='Người liên hệ khẩn cấp')
    emergency_phone = fields.Char(string='Điện thoại khẩn cấp')
    id_card = fields.Binary(string='Bản sao CCCD / CMND')
    driving_license = fields.Binary(string='Giấy phép lái xe')

    def _get_certificate_selection(self):
        return [
            ('graduate', 'Tốt nghiệp'),
            ('bachelor', 'Cử nhân / Đại học'),
            ('master', 'Thạc sĩ'),
            ('doctor', 'Tiến sĩ'),
            ('other', 'Khác'),
        ]

    def _tp_hierarchy_sort_key(self):
        self.ensure_one()
        exec_dept = is_executive_department(self.department_id)
        job_seq = self.job_id.sequence if self.job_id else 999999
        tier, subrank = _tp_role_rank(self.job_id.name if self.job_id else '', exec_dept)
        return (
            tier,
            subrank,
            job_seq,
            0 if self.child_ids else 1,
            0 if self.department_id else 1,
            (self.name or '').casefold(),
            self.id,
        )

    def _tp_sort_hierarchy_rows(self, rows):
        if not rows or not self.env.context.get('tp_hr_hierarchy'):
            return rows
        records = self.browse([row['id'] for row in rows])
        rank_by_id = {employee.id: employee._tp_hierarchy_sort_key() for employee in records}
        return sorted(rows, key=lambda row: rank_by_id.get(row['id'], (2, 999999, 1, 1, '', row['id'])))

    @api.model
    def hierarchy_read(self, domain, specification, parent_field, child_field=None, order=None):
        result = super().hierarchy_read(domain, specification, parent_field, child_field=child_field, order=order)
        return self._tp_sort_hierarchy_rows(result)

    @api.model
    def web_search_read(self, domain, specification, offset=0, limit=None, order=None, count_limit=None):
        result = super().web_search_read(
            domain, specification, offset=offset, limit=limit, order=order, count_limit=count_limit,
        )
        if result.get('records') and limit is None and not offset:
            result['records'] = self._tp_sort_hierarchy_rows(result['records'])
        return result

    def action_tp_profile(self):
        self.ensure_one()
        self.check_access('read')
        return {'type': 'ir.actions.act_window', 'name': self.env._('Hồ sơ nhân viên'),
                'res_model': self._name, 'res_id': self.id, 'view_mode': 'form',
                'views': [(self.env.ref('tp_hr_workspace.employee_form').id, 'form')]}
