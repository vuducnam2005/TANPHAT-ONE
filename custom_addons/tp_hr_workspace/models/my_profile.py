"""Self-service personal profile API strictly scoped to the logged-in user's employee."""
import base64
import binascii

from markupsafe import Markup

from odoo import api, fields, models
from odoo.exceptions import AccessError, ValidationError
from odoo.tools.mail import html_to_inner_content

from .hr_history import extract_history_item

MAX_AVATAR_BYTES = 5 * 1024 * 1024

SELF_EDITABLE_SCALAR_FIELDS = {
    'image_1920': 'Ảnh đại diện',
    'work_email': 'Email công việc',
    'work_phone': 'Điện thoại công ty',
    'mobile_phone': 'Di động',
    'private_email': 'Email cá nhân',
    'private_phone': 'Điện thoại cá nhân',
    'private_street': 'Địa chỉ (Số nhà, đường)',
    'private_street2': 'Phường / Xã',
    'private_city': 'Quận / Huyện / Thành phố',
    'private_zip': 'Mã bưu chính',
    'birthday': 'Ngày sinh',
    'birthday_public_display': 'Hiển thị ngày sinh nội bộ',
    'sex': 'Giới tính',
    'place_of_birth': 'Nơi sinh',
    'identification_id': 'Số CCCD / CMND',
    'passport_id': 'Số hộ chiếu',
    'passport_expiration_date': 'Ngày hết hạn hộ chiếu',
    'emergency_contact': 'Người liên hệ khẩn cấp',
    'emergency_phone': 'Số điện thoại khẩn cấp',
    'tp_personal_defaults_confirmed': 'Xác nhận thông tin gia đình & khoảng cách',
    'marital': 'Tình trạng hôn nhân',
    'spouse_complete_name': 'Họ tên vợ/chồng',
    'spouse_birthdate': 'Ngày sinh vợ/chồng',
    'children': 'Số con phụ thuộc',
    'distance_home_work': 'Khoảng cách đi làm (km)',
    'certificate': 'Trình độ học vấn',
    'study_field': 'Chuyên ngành đào tạo',
    'additional_note': 'Ghi chú cá nhân',
}

SELF_EDITABLE_MANY2ONE_FIELDS = {
    'country_id': ('res.country', 'Quốc tịch'),
    'country_of_birth': ('res.country', 'Quốc gia nơi sinh'),
    'private_country_id': ('res.country', 'Quốc gia địa chỉ riêng'),
    'private_state_id': ('res.country.state', 'Tỉnh / Thành phố'),
}

FAMILY_FIELDS = {'marital', 'spouse_complete_name', 'spouse_birthdate', 'children', 'distance_home_work'}
DATE_FIELDS = {'birthday', 'passport_expiration_date', 'spouse_birthdate'}
INT_FIELDS = {'children', 'distance_home_work'}
BOOL_FIELDS = {'birthday_public_display', 'tp_personal_defaults_confirmed'}
SELECTION_FIELDS = {'sex', 'marital', 'certificate'}


def _selection_label(record, field_name, default=''):
    value = record[field_name]
    if not value:
        return default
    selection = dict(record._fields[field_name]._description_selection(record.env))
    return selection.get(value, default)


def _format_dt_vn(env, dt_val):
    if not dt_val:
        return ''
    if isinstance(dt_val, str):
        dt_val = fields.Datetime.from_string(dt_val)
    tz_name = env.context.get('tz') or env.user.tz or 'Asia/Ho_Chi_Minh'
    local_dt = fields.Datetime.context_timestamp(env.user.with_context(tz=tz_name), dt_val)
    return local_dt.strftime('%d/%m/%Y %H:%M')


def _clean_image_b64(env, value):
    if value in (False, None, ''):
        return False
    if not isinstance(value, str):
        raise ValidationError(env._('Định dạng ảnh đại diện không hợp lệ.'))
    payload = value.split(',', 1)[1] if value.startswith('data:') and ',' in value else value
    payload = payload.strip()
    try:
        raw = base64.b64decode(payload, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValidationError(env._('Dữ liệu ảnh đại diện không hợp lệ.')) from exc
    if len(raw) > MAX_AVATAR_BYTES:
        raise ValidationError(env._('Ảnh đại diện vượt quá giới hạn 5 MB.'))
    if not (
        raw.startswith((b'\xff\xd8\xff', b'\x89PNG\r\n\x1a\n', b'GIF87a', b'GIF89a'))
        or (raw.startswith(b'RIFF') and raw[8:12] == b'WEBP')
    ):
        raise ValidationError(env._('Chỉ hỗ trợ ảnh PNG, JPG, GIF hoặc WebP.'))
    return payload


class ResUsersSelfProfile(models.Model):
    _inherit = 'res.users'

    @api.model
    def _tp_require_my_employee(self):
        employee = self.env.user._tp_main_employee()
        if not employee:
            raise ValidationError(self.env._('Tài khoản hiện tại chưa được gắn với hồ sơ nhân viên trong công ty đang chọn.'))
        return employee

    @api.model
    def tp_get_my_profile(self):
        """Return the logged-in user's own profile (strictly read via self.env.user)."""
        user = self.env.user
        partner = user.partner_id.sudo()
        avatar_url = (
            f'/web/image?model=res.partner&id={partner.id}&field=avatar_128&unique={partner.write_date}'
            if partner else ''
        )
        employee = user._tp_main_employee()
        if not employee:
            return {
                'has_employee': False,
                'user': {
                    'id': user.id,
                    'name': user.name,
                    'login': user.login,
                    'email': user.email or '',
                    'company_name': self.env.company.name,
                    'avatar_url': avatar_url,
                },
            }

        emp = employee.sudo().with_context(bin_size=False)
        version = emp.current_version_id or emp.version_id

        contract_docs = self.env['tp.hr.contract.document'].sudo().search(
            [('employee_id', '=', emp.id)], order='id desc',
        )
        resume_lines = self.env['hr.resume.line'].sudo().search(
            [('employee_id', '=', emp.id)], order='line_type_id, date_start desc, id desc',
        )
        emp_skills = self.env['hr.employee.skill'].sudo().search(
            [('employee_id', '=', emp.id)], order='skill_type_id, skill_level_id desc, id desc',
        )
        messages = self.env['mail.message'].sudo().search(
            [('model', '=', 'hr.employee'), ('res_id', '=', emp.id),
             ('message_type', 'in', ('tracking', 'notification', 'comment'))],
            order='date desc, id desc',
            limit=50,
        )

        countries = [{'id': c.id, 'name': c.name} for c in self.env['res.country'].search([], order='name, id')]
        state_domain = [('country_id', '=', emp.private_country_id.id)] if emp.private_country_id else []
        states = [
            {'id': s.id, 'name': s.name, 'country_id': s.country_id.id}
            for s in (self.env['res.country.state'].search(state_domain, order='name, id') if state_domain else ())
        ]

        def sel_options(field_name):
            return [
                {'value': k, 'label': v}
                for k, v in emp._fields[field_name]._description_selection(self.env)
            ]

        editable_values = {
            'has_image': bool(emp.image_1920),
            'work_email': emp.work_email or '',
            'work_phone': emp.work_phone or '',
            'mobile_phone': emp.mobile_phone or '',
            'private_email': emp.private_email or '',
            'private_phone': emp.private_phone or '',
            'private_street': emp.private_street or '',
            'private_street2': emp.private_street2 or '',
            'private_city': emp.private_city or '',
            'private_zip': emp.private_zip or '',
            'private_country_id': emp.private_country_id.id or False,
            'private_country_name': emp.private_country_id.name or '',
            'private_state_id': emp.private_state_id.id or False,
            'private_state_name': emp.private_state_id.name or '',
            'birthday': fields.Date.to_string(emp.birthday) if emp.birthday else '',
            'birthday_public_display': bool(emp.birthday_public_display),
            'sex': emp.sex or '',
            'place_of_birth': emp.place_of_birth or '',
            'country_of_birth': emp.country_of_birth.id or False,
            'country_of_birth_name': emp.country_of_birth.name or '',
            'country_id': emp.country_id.id or False,
            'country_name': emp.country_id.name or '',
            'identification_id': emp.identification_id or '',
            'passport_id': emp.passport_id or '',
            'passport_expiration_date': (
                fields.Date.to_string(emp.passport_expiration_date) if emp.passport_expiration_date else ''
            ),
            'emergency_contact': emp.emergency_contact or '',
            'emergency_phone': emp.emergency_phone or '',
            'tp_personal_defaults_confirmed': bool(emp.tp_personal_defaults_confirmed),
            'marital': emp.marital or '',
            'spouse_complete_name': emp.spouse_complete_name or '',
            'spouse_birthdate': fields.Date.to_string(emp.spouse_birthdate) if emp.spouse_birthdate else '',
            'children': emp.children or 0,
            'distance_home_work': emp.distance_home_work or 0,
            'certificate': emp.certificate or '',
            'study_field': emp.study_field or '',
            'additional_note': emp.additional_note or '',
        }

        return {
            'has_employee': True,
            'header': {
                'id': emp.id,
                'name': emp.name,
                'code': emp.tp_employee_code or 'Chưa cấp mã',
                'department_name': emp.department_id.name or 'Chưa khai báo',
                'job_name': emp.job_id.name or 'Chưa khai báo',
                'job_title': emp.job_title or '',
                'account_status': emp.tp_account_status,
                'account_status_label': dict(emp._fields['tp_account_status'].selection).get(emp.tp_account_status, ''),
                'avatar_url': avatar_url,
                'user_login': emp.tp_user_login or user.login,
                'business_role': emp.tp_business_role or '',
                'role_scope': emp.tp_role_scope or '',
                'company_name': emp.company_id.name or self.env.company.name,
                'parent_name': emp.parent_id.name or 'Chưa khai báo',
                'work_location_name': emp.work_location_id.name or 'Chưa khai báo',
                'employment_kind': emp.tp_employment_kind or '',
                'employment_kind_label': _selection_label(emp, 'tp_employment_kind', 'Chưa khai báo'),
            },
            'values': editable_values,
            'options': {
                'sex': sel_options('sex'),
                'marital': sel_options('marital'),
                'certificate': sel_options('certificate'),
                'countries': countries,
                'states': states,
            },
            'contracts': {
                'employment_kind': emp.tp_employment_kind or '',
                'employment_kind_label': _selection_label(emp, 'tp_employment_kind', 'Chưa khai báo'),
                'version_name': version.name if version else '',
                'date_version': fields.Date.to_string(version.date_version) if version and version.date_version else '',
                'contract_date_start': (
                    fields.Date.to_string(emp.contract_date_start) if emp.contract_date_start else ''
                ),
                'contract_date_end': fields.Date.to_string(emp.contract_date_end) if emp.contract_date_end else '',
                'fixed_term': bool(emp.fixed_term),
                'current_document_id': emp.tp_contract_document_id.id or False,
                'documents': [
                    {
                        'id': doc.id,
                        'number': doc.number or '',
                        'name': doc.name or '',
                        'kind': doc.kind,
                        'kind_label': _selection_label(doc, 'kind', doc.kind or ''),
                        'signed_date': fields.Date.to_string(doc.signed_date) if doc.signed_date else '',
                        'service_start': fields.Date.to_string(doc.service_start) if doc.service_start else '',
                        'service_end': fields.Date.to_string(doc.service_end) if doc.service_end else '',
                        'note': doc.note or '',
                        'has_file': bool(doc.file),
                        'filename': doc.filename or 'HopDong.pdf',
                        'has_appendix': bool(doc.appendix),
                        'appendix_filename': doc.appendix_filename or 'PhuLuc.pdf',
                    }
                    for doc in contract_docs
                ],
            },
            'resume': {
                'lines': [
                    {
                        'id': line.id,
                        'name': line.name or '',
                        'line_type_id': line.line_type_id.id or False,
                        'line_type_name': line.line_type_id.name or 'Khác',
                        'date_start': fields.Date.to_string(line.date_start) if line.date_start else '',
                        'date_end': fields.Date.to_string(line.date_end) if line.date_end else '',
                        'description': html_to_inner_content(line.description or ''),
                    }
                    for line in resume_lines
                ],
                'resume_types': [
                    {'id': rt.id, 'name': rt.name}
                    for rt in self.env['hr.resume.line.type'].search([], order='sequence, id')
                ],
                'skills': [
                    {
                        'id': sk.id,
                        'skill_type_id': sk.skill_type_id.id,
                        'skill_type_name': sk.skill_type_id.name or '',
                        'skill_id': sk.skill_id.id,
                        'skill_name': sk.skill_id.name or '',
                        'skill_level_id': sk.skill_level_id.id,
                        'skill_level_name': sk.skill_level_id.name or '',
                        'level_progress': sk.level_progress or 0,
                        'is_certification': bool(sk.is_certification),
                    }
                    for sk in emp_skills
                ],
                'skill_types': [
                    {'id': st.id, 'name': st.name, 'is_certification': bool(st.is_certification)}
                    for st in self.env['hr.skill.type'].search([], order='sequence, id')
                ],
                'skills_catalog': [
                    {'id': s.id, 'name': s.name, 'skill_type_id': s.skill_type_id.id}
                    for s in self.env['hr.skill'].search([], order='sequence, id')
                ],
                'skill_levels': [
                    {'id': lv.id, 'name': lv.name, 'skill_type_id': lv.skill_type_id.id, 'progress': lv.level_progress}
                    for lv in self.env['hr.skill.level'].search([], order='level_progress, id')
                ],
            },
            'history': [
                item
                for msg in messages
                if (item := extract_history_item(self.env, msg, _format_dt_vn))
            ][:25],
        }

    @api.model
    def tp_save_my_profile(self, vals):
        """Update only explicit self-editable fields on the user's own hr.employee."""
        if not isinstance(vals, dict):
            raise ValidationError(self.env._('Dữ liệu cập nhật hồ sơ không hợp lệ.'))
        allowed_keys = set(SELF_EDITABLE_SCALAR_FIELDS) | set(SELF_EDITABLE_MANY2ONE_FIELDS)
        forbidden = set(vals) - allowed_keys
        if forbidden:
            raise AccessError(self.env._(
                'Bạn không có quyền tự chỉnh sửa trường do HR/Quản trị quản lý: %s.',
                ', '.join(sorted(forbidden)),
            ))

        employee = self._tp_require_my_employee()
        emp = employee.sudo().with_context(bin_size=False, tracking_disable=False)

        clean_vals = {}
        changed_labels = []

        for key, raw in vals.items():
            if key in SELF_EDITABLE_MANY2ONE_FIELDS:
                model_name, label = SELF_EDITABLE_MANY2ONE_FIELDS[key]
                if raw in (False, None, '', 0):
                    new_id = False
                else:
                    if isinstance(raw, bool):
                        raise ValidationError(self.env._('%s không hợp lệ.', label))
                    try:
                        rec_id = int(raw)
                    except (TypeError, ValueError) as exc:
                        raise ValidationError(self.env._('%s không hợp lệ.', label)) from exc
                    rec = self.env[model_name].browse(rec_id).exists()
                    if not rec:
                        raise ValidationError(self.env._('%s không tồn tại.', label))
                    new_id = rec.id
                if (emp[key].id or False) != new_id:
                    clean_vals[key] = new_id
                    changed_labels.append(label)
                continue

            label = SELF_EDITABLE_SCALAR_FIELDS[key]
            if key == 'image_1920':
                cleaned_img = _clean_image_b64(self.env, raw)
                old_img = emp.image_1920.to_base64() if emp.image_1920 else False
                if (cleaned_img or False) != (old_img or False):
                    clean_vals['image_1920'] = cleaned_img
                    changed_labels.append(label)
            elif key in DATE_FIELDS:
                if raw in (False, None, ''):
                    new_date = False
                else:
                    try:
                        new_date = fields.Date.to_date(raw)
                    except (TypeError, ValueError) as exc:
                        raise ValidationError(self.env._('%s không đúng định dạng ngày.', label)) from exc
                    if not new_date:
                        raise ValidationError(self.env._('%s không đúng định dạng ngày.', label))
                if (emp[key] or False) != new_date:
                    clean_vals[key] = new_date
                    changed_labels.append(label)
            elif key in INT_FIELDS:
                if raw in (False, None, ''):
                    new_int = 0
                else:
                    if isinstance(raw, bool):
                        raise ValidationError(self.env._('%s phải là số nguyên không âm.', label))
                    try:
                        new_int = int(raw)
                    except (TypeError, ValueError) as exc:
                        raise ValidationError(self.env._('%s phải là số nguyên không âm.', label)) from exc
                    if new_int < 0 or (key == 'children' and new_int > 30) or (key == 'distance_home_work' and new_int > 2000):
                        raise ValidationError(self.env._('%s nằm ngoài giới hạn hợp lệ.', label))
                if (emp[key] or 0) != new_int:
                    clean_vals[key] = new_int
                    changed_labels.append(label)
            elif key in BOOL_FIELDS:
                new_bool = bool(raw)
                if bool(emp[key]) != new_bool:
                    clean_vals[key] = new_bool
                    changed_labels.append(label)
            elif key in SELECTION_FIELDS:
                allowed = {opt_k for opt_k, _ in emp._fields[key]._description_selection(self.env)}
                new_sel = False if raw in (False, None, '') else str(raw)
                if new_sel and new_sel not in allowed:
                    raise ValidationError(self.env._('Giá trị %s không hợp lệ.', label))
                if (emp[key] or False) != new_sel:
                    clean_vals[key] = new_sel
                    changed_labels.append(label)
            else:
                new_str = '' if raw in (False, None) else str(raw).strip()
                if len(new_str) > (2000 if key == 'additional_note' else 255):
                    raise ValidationError(self.env._('%s quá dài.', label))
                new_val = new_str or False
                if (emp[key] or False) != new_val:
                    clean_vals[key] = new_val
                    changed_labels.append(label)

        if any(k in clean_vals for k in FAMILY_FIELDS) and not emp.tp_personal_defaults_confirmed:
            clean_vals.setdefault('tp_personal_defaults_confirmed', True)

        if clean_vals:
            emp.write(clean_vals)
            emp.message_post(
                body=Markup('<p>%s</p>') % (
                    self.env._('Nhân viên tự cập nhật thông tin cá nhân: %s.', ', '.join(changed_labels))
                ),
                message_type='notification',
                subtype_xmlid='mail.mt_note',
            )

        return self.tp_get_my_profile()

    @api.model
    def tp_save_my_resume_line(self, line_id, vals):
        """Create or update a resume line belonging strictly to the logged-in user."""
        if not isinstance(vals, dict):
            raise ValidationError(self.env._('Dữ liệu kinh nghiệm không hợp lệ.'))
        if set(vals) - {'name', 'line_type_id', 'date_start', 'date_end', 'description'}:
            raise AccessError(self.env._('Chỉ được cập nhật tiêu đề, loại, thời gian và mô tả kinh nghiệm.'))
        employee = self._tp_require_my_employee()
        name = (vals.get('name') or '').strip()
        if not name:
            raise ValidationError(self.env._('Vui lòng nhập tiêu đề mục hồ sơ năng lực.'))
        if not vals.get('date_start'):
            raise ValidationError(self.env._('Vui lòng chọn ngày bắt đầu.'))
        date_start = fields.Date.to_date(vals['date_start'])
        date_end = fields.Date.to_date(vals['date_end']) if vals.get('date_end') else False
        if date_end and date_start and date_end < date_start:
            raise ValidationError(self.env._('Ngày kết thúc phải lớn hơn hoặc bằng ngày bắt đầu.'))
        line_type_id = int(vals['line_type_id']) if vals.get('line_type_id') else False
        if line_type_id and not self.env['hr.resume.line.type'].browse(line_type_id).exists():
            raise ValidationError(self.env._('Loại mục hồ sơ năng lực không tồn tại.'))
        payload = {
            'name': name,
            'line_type_id': line_type_id,
            'date_start': date_start,
            'date_end': date_end,
            'description': (vals.get('description') or '').strip(),
        }
        ResumeLine = self.env['hr.resume.line']
        if line_id:
            line = ResumeLine.sudo().browse(int(line_id)).exists()
            if not line or line.employee_id.id != employee.id:
                raise AccessError(self.env._('Không có quyền sửa mục hồ sơ của nhân viên khác.'))
            line.write(payload)
            action_label = 'cập nhật'
        else:
            payload['employee_id'] = employee.id
            ResumeLine.sudo().create(payload)
            action_label = 'bổ sung'
        employee.sudo().message_post(
            body=Markup('<p>%s</p>') % self.env._('Nhân viên tự %s mục hồ sơ năng lực: %s.', action_label, name),
            message_type='notification',
            subtype_xmlid='mail.mt_note',
        )
        return self.tp_get_my_profile()

    @api.model
    def tp_delete_my_resume_line(self, line_id):
        employee = self._tp_require_my_employee()
        line = self.env['hr.resume.line'].sudo().browse(int(line_id)).exists()
        if not line or line.employee_id.id != employee.id:
            raise AccessError(self.env._('Không có quyền xóa mục hồ sơ của nhân viên khác.'))
        title = line.name
        line.unlink()
        employee.sudo().message_post(
            body=Markup('<p>%s</p>') % self.env._('Nhân viên tự xóa mục hồ sơ năng lực: %s.', title),
            message_type='notification',
            subtype_xmlid='mail.mt_note',
        )
        return self.tp_get_my_profile()

    @api.model
    def tp_save_my_skill(self, skill_rec_id, vals):
        """Create or update an employee skill belonging strictly to the logged-in user."""
        if not isinstance(vals, dict):
            raise ValidationError(self.env._('Dữ liệu kỹ năng không hợp lệ.'))
        if set(vals) - {'skill_type_id', 'skill_id', 'skill_level_id'}:
            raise AccessError(self.env._('Chỉ được cập nhật loại kỹ năng, kỹ năng và mức độ.'))
        employee = self._tp_require_my_employee()
        try:
            skill_type_id = int(vals.get('skill_type_id'))
            skill_id = int(vals.get('skill_id'))
            skill_level_id = int(vals.get('skill_level_id'))
        except (TypeError, ValueError) as exc:
            raise ValidationError(self.env._('Vui lòng chọn đầy đủ Loại kỹ năng, Kỹ năng và Mức độ.')) from exc
        skill = self.env['hr.skill'].browse(skill_id).exists()
        level = self.env['hr.skill.level'].browse(skill_level_id).exists()
        if not skill or not level or skill.skill_type_id.id != skill_type_id or level.skill_type_id.id != skill_type_id:
            raise ValidationError(self.env._('Kỹ năng hoặc mức độ không khớp với loại kỹ năng đã chọn.'))
        payload = {
            'skill_type_id': skill_type_id,
            'skill_id': skill_id,
            'skill_level_id': skill_level_id,
        }
        EmpSkill = self.env['hr.employee.skill']
        if skill_rec_id:
            rec = EmpSkill.sudo().browse(int(skill_rec_id)).exists()
            if not rec or rec.employee_id.id != employee.id:
                raise AccessError(self.env._('Không có quyền sửa kỹ năng của nhân viên khác.'))
            rec.write(payload)
        else:
            existing = EmpSkill.sudo().search([
                ('employee_id', '=', employee.id),
                ('skill_id', '=', skill_id),
            ], limit=1)
            if existing:
                existing.write(payload)
            else:
                payload['employee_id'] = employee.id
                EmpSkill.sudo().create(payload)
        employee.sudo().message_post(
            body=Markup('<p>%s</p>') % self.env._('Nhân viên tự cập nhật kỹ năng: %s (%s).', skill.name, level.name),
            message_type='notification',
            subtype_xmlid='mail.mt_note',
        )
        return self.tp_get_my_profile()

    @api.model
    def tp_delete_my_skill(self, skill_rec_id):
        employee = self._tp_require_my_employee()
        rec = self.env['hr.employee.skill'].sudo().browse(int(skill_rec_id)).exists()
        if not rec or rec.employee_id.id != employee.id:
            raise AccessError(self.env._('Không có quyền xóa kỹ năng của nhân viên khác.'))
        label = rec.skill_id.name
        rec.unlink()
        employee.sudo().message_post(
            body=Markup('<p>%s</p>') % self.env._('Nhân viên tự xóa kỹ năng: %s.', label),
            message_type='notification',
            subtype_xmlid='mail.mt_note',
        )
        return self.tp_get_my_profile()
