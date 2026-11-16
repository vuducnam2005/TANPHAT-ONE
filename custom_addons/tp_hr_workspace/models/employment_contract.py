"""HR paper metadata; native hr.version remains the source of labor dates."""
from odoo import api, fields, models
from odoo.exceptions import AccessError, ValidationError

EMPLOYMENT_KINDS = [('short_term', 'Ngắn hạn'), ('long_term', 'Dài hạn'), ('outsourced', 'Thuê khoán')]


class HrContractDocument(models.Model):
    _name = 'tp.hr.contract.document'
    _description = 'Hồ sơ hợp đồng nhân sự'
    _inherit = ['mail.thread']
    _check_company_auto = True
    _order = 'id desc'

    name = fields.Char('Tên / trích yếu', required=True, tracking=True)
    number = fields.Char('Số hợp đồng', tracking=True)
    employee_id = fields.Many2one('hr.employee', string='Nhân viên', required=True, ondelete='restrict', check_company=True, tracking=True)
    company_id = fields.Many2one(related='employee_id.company_id', store=True, readonly=True)
    kind = fields.Selection([('labor', 'Hợp đồng lao động'), ('outsourced', 'Hợp đồng thuê khoán')], string='Loại giấy tờ', required=True, tracking=True)
    signed_date = fields.Date('Ngày ký (có căn cứ)', tracking=True)
    service_start = fields.Date('Ngày bắt đầu thuê khoán', tracking=True)
    service_end = fields.Date('Ngày kết thúc thuê khoán', tracking=True)
    note = fields.Text('Ghi chú', tracking=True)
    file = fields.Binary('Tệp hợp đồng', attachment=True)
    filename = fields.Char('Tên tệp hợp đồng')
    appendix = fields.Binary('Tệp phụ lục', attachment=True)
    appendix_filename = fields.Char('Tên tệp phụ lục')
    version_ids = fields.One2many('hr.version', 'tp_contract_document_id', string='Phiên bản hồ sơ liên quan')

    @api.constrains('service_start', 'service_end', 'kind')
    def _check_service_dates(self):
        for doc in self:
            if doc.kind == 'labor' and (doc.service_start or doc.service_end):
                raise ValidationError(self.env._('Ngày hợp đồng lao động được lưu tại phiên bản hồ sơ, không nhập ngày thuê khoán.'))
            if doc.service_end and (not doc.service_start or doc.service_end < doc.service_start):
                raise ValidationError(self.env._('Ngày kết thúc thuê khoán phải từ ngày bắt đầu trở đi.'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            employee_id = vals.get('employee_id') or self.default_get(['employee_id']).get('employee_id')
            employee = self.env['hr.employee'].browse(employee_id)
            employee.check_access('write')
        documents = super().create(vals_list)
        version_id = self.env.context.get('tp_contract_version_id')
        if version_id:
            version = self.env['hr.version'].browse(version_id).exists()
            version.check_access('write')
            if len(documents) != 1 or not version or version.employee_id != documents.employee_id:
                raise ValidationError(self.env._('Phiên bản liên kết phải thuộc đúng nhân viên của giấy tờ.'))
            version.write({'tp_contract_document_id': documents.id})
        return documents

    def write(self, vals):
        self.employee_id.check_access('write')
        if set(vals) & {'employee_id', 'kind'} and any(
            (vals.get('employee_id', doc.employee_id.id) != doc.employee_id.id
             or vals.get('kind', doc.kind) != doc.kind) for doc in self
        ):
            raise ValidationError(self.env._('Không chuyển hồ sơ giấy tờ sang nhân viên hoặc loại giấy tờ khác. Hãy tạo hồ sơ mới.'))
        return super().write(vals)

    @api.ondelete(at_uninstall=False)
    def _keep_contract_evidence(self):
        raise AccessError(self.env._('Giữ hồ sơ hợp đồng và bằng chứng; không xóa vật lý hồ sơ giấy tờ.'))


class HrEmploymentVersion(models.Model):
    _inherit = 'hr.version'

    tp_employment_kind = fields.Selection(EMPLOYMENT_KINDS, string='Loại hình lao động', groups='hr.group_hr_user', tracking=True, index=True)
    tp_contract_document_id = fields.Many2one('tp.hr.contract.document', string='Hồ sơ giấy tờ đang xem', groups='hr.group_hr_user', ondelete='restrict', check_company=True, tracking=True, copy=False)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if set(vals) & {'tp_employment_kind', 'tp_contract_document_id'}:
                employee_id = vals.get('employee_id') or self.default_get(['employee_id']).get('employee_id')
                self.env['hr.employee'].browse(employee_id).check_access('write')
        return super().create(vals_list)

    def write(self, vals):
        if set(vals) & {'tp_employment_kind', 'tp_contract_document_id'}:
            self.employee_id.check_access('write')
        return super().write(vals)

    @api.constrains('tp_contract_document_id', 'employee_id', 'contract_date_start', 'contract_date_end')
    def _check_contract_document(self):
        for version in self.filtered('tp_contract_document_id'):
            doc = version.tp_contract_document_id
            if doc.employee_id != version.employee_id or doc.company_id != version.company_id:
                raise ValidationError(self.env._('Giấy tờ phải thuộc đúng nhân viên và công ty của phiên bản.'))
            if doc.kind == 'labor' and any(
                (v.contract_date_start, v.contract_date_end) != (version.contract_date_start, version.contract_date_end)
                for v in doc.version_ids.filtered('active')
            ):
                raise ValidationError(self.env._('Các phiên bản của cùng hồ sơ hợp đồng lao động phải dùng cùng thời hạn native.'))

    def action_open_version(self):
        self.ensure_one()
        self.check_access('read')
        action = super().action_open_version()
        action['views'] = [(self.env.ref('tp_hr_workspace.employee_form').id, 'form')]
        return action


class HrEmploymentEmployee(models.Model):
    _inherit = 'hr.employee'

    tp_employment_kind = fields.Selection(related='version_id.tp_employment_kind', inherited=True, readonly=False, groups='hr.group_hr_user')
    tp_contract_document_id = fields.Many2one(related='version_id.tp_contract_document_id', inherited=True, readonly=False, groups='hr.group_hr_user')
    tp_contract_document_ids = fields.One2many('tp.hr.contract.document', 'employee_id', string='Hồ sơ giấy tờ', groups='hr.group_hr_user')
    tp_missing_basic = fields.Char('Cần bổ sung', compute='_compute_tp_missing_basic', search='_search_tp_missing_basic', groups='hr.group_hr_user')
    tp_can_add_contract = fields.Boolean(compute='_compute_tp_can_add_contract', groups='hr.group_hr_user')

    @api.depends_context('uid', 'allowed_company_ids')
    def _compute_tp_can_add_contract(self):
        for employee in self:
            employee.tp_can_add_contract = employee.has_access('write') and self.env['tp.hr.contract.document'].has_access('create')

    def create_version(self, values):
        self.ensure_one()
        if not values.get('date_version'):
            return super().create_version(values)
        version_date = fields.Date.to_date(values.get('date_version'))
        version = self._get_version(version_date)
        if not version:
            version = self.env['hr.version'].search([('employee_id', '=', self.id), ('active', '=', True)], limit=1)
        doc = version.tp_contract_document_id
        if doc and 'tp_contract_document_id' not in values:
            start = values.get('contract_date_start', self.sudo()._get_contract_dates(version_date)[0])
            if doc.kind != 'labor' or fields.Date.to_date(start) == version.contract_date_start:
                # Native creates the copy before applying values; link only after its dates exist.
                values = {**values, 'tp_contract_document_id': doc.id}
        return super().create_version(values)

    @api.model
    def _tp_missing_domain(self):
        return ['|', '|', ('tp_employee_code', '=', False), ('department_id', '=', False),
                '&', ('tp_source_title', '=', False), ('job_id', '=', False)]

    @api.depends('tp_employee_code', 'department_id', 'job_id', 'tp_source_title')
    def _compute_tp_missing_basic(self):
        for employee in self:
            employee.tp_missing_basic = ' · '.join(label for missing, label in [
                (not employee.tp_employee_code, 'Thiếu mã nhân viên'),
                (not employee.department_id, 'Thiếu phòng ban'),
                (not employee.job_id and not employee.tp_source_title, 'Thiếu thông tin chức vụ'),
            ] if missing)

    def _search_tp_missing_basic(self, operator, value):
        if operator == '!=' and value is False:
            return self._tp_missing_domain()
        return NotImplemented

    def action_tp_contract_documents(self):
        self.ensure_one()
        self.check_access('read')
        if not self.env.user.has_group('hr.group_hr_user'):
            raise AccessError(self.env._('Chỉ HR được xem hồ sơ hợp đồng nhân sự.'))
        return {'type': 'ir.actions.act_window', 'name': self.env._('Hồ sơ hợp đồng nhân sự'),
                'res_model': 'tp.hr.contract.document', 'view_mode': 'list,form',
                'domain': [('employee_id', '=', self.id)],
                'context': {'default_employee_id': self.id,
                            'default_kind': 'outsourced' if self.tp_employment_kind == 'outsourced' else 'labor'}}

    def action_tp_add_contract_document(self):
        self.ensure_one()
        self.check_access('write')
        action = self.action_tp_contract_documents()
        self.version_id.check_access('write')
        action.update(view_mode='form', views=[(False, 'form')], target='new')
        action['context']['tp_contract_version_id'] = self.version_id.id
        return action

    def action_tp_complete_profile(self):
        self.ensure_one()
        self.check_access('write')
        return {'type': 'ir.actions.act_window', 'res_model': 'hr.employee', 'res_id': self.id,
                'views': [(self.env.ref('tp_hr_workspace.employee_form').id, 'form')],
                'context': {'form_view_initial_mode': 'edit'}}


class HrContractAttachment(models.Model):
    _inherit = 'ir.attachment'

    def _tp_contract_files(self):
        return self.filtered(lambda a: a.res_model == 'tp.hr.contract.document')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('res_model') == 'tp.hr.contract.document' and (vals.get('public') or vals.get('access_token')):
                raise AccessError(self.env._('Tệp hợp đồng nhân sự chỉ được truy cập qua quyền HR; không chia sẻ công khai.'))
        return super().create(vals_list)

    def write(self, vals):
        protected = self._tp_contract_files()
        if protected and (vals.get('public') or vals.get('access_token') or set(vals) & {'res_model', 'res_id', 'res_field'}):
            raise AccessError(self.env._('Không công khai hoặc chuyển tệp bằng chứng hợp đồng nhân sự.'))
        if vals.get('res_model') == 'tp.hr.contract.document' and (vals.get('public') or vals.get('access_token') or any(a.public or a.access_token for a in self)):
            raise AccessError(self.env._('Tệp hợp đồng nhân sự không được public hoặc có token.'))
        return super().write(vals)

    def generate_access_token(self):
        if self._tp_contract_files():
            raise AccessError(self.env._('Không tạo token công khai cho tệp hợp đồng nhân sự.'))
        return super().generate_access_token()
