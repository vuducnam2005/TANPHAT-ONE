"""Clean Vietnamese formatting and audit categorization for HR history."""
import json
import re

from lxml import html
from markupsafe import Markup, escape

from odoo import fields, models
from odoo.tools.mail import html_to_inner_content

_EN_MONTHS = {
    'Jan': 'thg 1', 'Feb': 'thg 2', 'Mar': 'thg 3', 'Apr': 'thg 4',
    'May': 'thg 5', 'Jun': 'thg 6', 'Jul': 'thg 7', 'Aug': 'thg 8',
    'Sep': 'thg 9', 'Oct': 'thg 10', 'Nov': 'thg 11', 'Dec': 'thg 12',
}
_AS_OF_EN_DATE_RE = re.compile(
    r'\b(' + '|'.join(_EN_MONTHS) + r')\s+(\d{1,2}),\s*(\d{4})\b',
)
_LEGACY_TRACKING_LINE_RE = re.compile(r'^(.*?)\s*→\s*(.*?)\s*\(([^()]+)\)\s*$')

_FIELD_LABEL_MAP = {
    'User Status': 'Trạng thái tài khoản',
    'Job': 'Chức vụ',
    'Job Title': 'Chức danh',
    'Sex': 'Giới tính',
    'Timezone': 'Múi giờ',
    'Current Date Employee Record': 'Ngày hiệu lực hồ sơ',
    'Employee Record': 'Hồ sơ nhân viên',
    'Department': 'Phòng ban',
    'Manager': 'Quản lý trực tiếp',
    'Work Location': 'Nơi làm việc',
    'Company': 'Công ty',
    'Private Email': 'Email cá nhân',
    'Private Phone': 'Điện thoại cá nhân',
    'Work Email': 'Email công việc',
    'Work Phone': 'Điện thoại công ty',
    'Mobile': 'Di động',
    'Work Mobile': 'Di động',
    'Nationality': 'Quốc tịch',
    'Nationality (Country)': 'Quốc tịch',
    'Country': 'Quốc gia',
    'Identification No': 'Số CCCD / CMND',
    'Số CMND': 'Số CCCD / CMND',
    'Passport No': 'Số hộ chiếu',
    'Birthday': 'Ngày sinh',
    'Date of Birth': 'Ngày sinh',
    'Place of Birth': 'Nơi sinh',
    'Country of Birth': 'Quốc gia nơi sinh',
    'Nơi sinh (quốc gia)': 'Quốc gia nơi sinh',
    'Marital Status': 'Tình trạng hôn nhân',
    'Certificate Level': 'Trình độ học vấn',
    'Field of Study': 'Chuyên ngành đào tạo',
    'Emergency Contact': 'Người liên hệ khẩn cấp',
    'Emergency Phone': 'Số điện thoại khẩn cấp',
    'Contract Start Date': 'Ngày bắt đầu hợp đồng',
    'Contract End Date': 'Ngày kết thúc hợp đồng',
    'Employment Type': 'Loại hình lao động',
    'User': 'Tài khoản',
    'Login': 'Tên đăng nhập',
    'Active': 'Đang hoạt động',
    'Hồ sơ giấy tờ đang xem': 'Hồ sơ hợp đồng',
}

_VALUE_LABEL_MAP = {
    'None': 'Chưa thiết lập',
    'False': 'Chưa thiết lập',
    'Yes': 'Có',
    'No': 'Không',
    'Invited': 'Đã gửi lời mời',
    'Confirmed': 'Đã kích hoạt',
    'Never Connected': 'Chưa đăng nhập',
    'Male': 'Nam',
    'Female': 'Nữ',
    'Single': 'Độc thân',
    'Married': 'Đã kết hôn',
    'Legal Cohabitant': 'Sống chung hợp pháp',
    'Widower': 'Góa',
    'Divorced': 'Đã ly hôn',
    'Graduate': 'Tốt nghiệp',
    'Bachelor': 'Cử nhân / Đại học',
    'Master': 'Thạc sĩ',
    'Doctor': 'Tiến sĩ',
    'Other': 'Khác',
}

_CATEGORY_META = {
    'role': ('Thay đổi vai trò', 'role', 'indigo'),
    'transfer': ('Chuyển phòng ban', 'role', 'amber'),
    'account': ('Tài khoản & Mật khẩu', 'account', 'teal'),
    'resume': ('Hồ sơ & Năng lực', 'profile', 'blue'),
    'contract': ('Hợp đồng lao động', 'contract', 'green'),
    'profile': ('Cập nhật hồ sơ', 'profile', 'slate'),
    'system': ('Hệ thống', 'other', 'muted'),
}


def _translate_as_of_text(text):
    if not text or not text.startswith('As of'):
        return text
    out = text.replace('As of', 'Có hiệu lực từ', 1).replace(' to ', ' đến ')
    return _AS_OF_EN_DATE_RE.sub(lambda m: f'{m.group(2)} {_EN_MONTHS[m.group(1)]}, {m.group(3)}', out)


def _translate_field_label(label):
    cleaned = (label or '').strip()
    return _FIELD_LABEL_MAP.get(cleaned, cleaned or 'Trường dữ liệu')


def _translate_tracking_value(value):
    cleaned = (value or '').strip()
    if not cleaned:
        return 'Chưa thiết lập'
    return _VALUE_LABEL_MAP.get(cleaned, cleaned)


def _translate_inline_tracking_text(text):
    if not text:
        return text
    stripped = text.strip()
    if stripped in _VALUE_LABEL_MAP:
        return text.replace(stripped, _VALUE_LABEL_MAP[stripped], 1)
    if '→' in text:
        left, right = text.split('→', 1)
        left_clean = left.strip()
        right_clean = right.strip()
        if left_clean in _VALUE_LABEL_MAP:
            left = left.replace(left_clean, _VALUE_LABEL_MAP[left_clean], 1)
        if right_clean in _VALUE_LABEL_MAP:
            right = right.replace(right_clean, _VALUE_LABEL_MAP[right_clean], 1)
        return f'{left}→{right}'
    return text


def _classify_legacy_body(message, text):
    """Identify raw JSON or English system envelopes without altering DB rows."""
    stripped = (text or '').strip()
    if not stripped:
        return None, None
    if message.model == 'hr.employee' and message.message_type in ('notification', 'tracking'):
        if stripped.startswith('Đối chiếu danh tính theo ID: ') and len(stripped) <= 20000:
            prefix = 'Đối chiếu danh tính theo ID: '
            try:
                evidence, end = json.JSONDecoder().raw_decode(stripped[len(prefix):])
                keys = {'employee', 'code', 'resource', 'user', 'partner', 'work_contact', 'name',
                        'user_name', 'employee_image', 'user_image'}
                tail = stripped[len(prefix) + end:]
                if isinstance(evidence, dict) and set(evidence) == keys and evidence['employee'] == message.res_id:
                    marker = '. Lý do: '
                    if marker in tail:
                        return 'identity_legacy', {'reason': tail.split(marker, 1)[1].strip()}
            except (ValueError, TypeError):
                pass

        if stripped.startswith('{') and stripped.endswith('}') and len(stripped) <= 30000:
            try:
                payload = json.loads(stripped)
            except (ValueError, TypeError):
                payload = None
            if isinstance(payload, dict):
                if payload.get('action') == 'department_transfer' and ('before' in payload or 'preview' in payload):
                    return 'transfer_legacy', payload
                if set(payload) == {'before', 'after'} and isinstance(payload.get('before'), dict):
                    return 'role_snapshot_legacy', payload

    if 'Congratulations! May I recommend you to setup an' in stripped or 'onboarding plan' in stripped.lower():
        return 'onboarding_legacy', {}
    if stripped in ('Employee Record created', 'Employee Record được tạo'):
        return 'created_legacy', {}
    return None, None


def _render_transfer_legacy_html(env, payload):
    lines = []
    before_dept = ''
    after_dept = ''
    preview_text = (payload.get('preview') or '').strip()
    for raw_line in preview_text.splitlines():
        line = raw_line.strip()
        if line.startswith('PHÒNG BAN:'):
            lines.append('Chuyển phòng ban: ' + line[len('PHÒNG BAN:'):].strip().rstrip('.'))
            break
    if not lines:
        dept_model = env['hr.department'].sudo()
        b_id = (payload.get('before') or {}).get('department')
        a_id = (payload.get('after') or {}).get('department')
        before_dept = dept_model.browse(b_id).name if b_id else ''
        after_dept = dept_model.browse(a_id).name if a_id else ''
        if before_dept or after_dept:
            lines.append(f"Chuyển phòng ban: {before_dept or 'Chưa thiết lập'} → {after_dept or 'Chưa thiết lập'}")
        else:
            lines.append('Chuyển phòng ban nhân sự')

    actor_name = ''
    actor_id = payload.get('actor')
    if actor_id:
        actor = env['res.users'].sudo().browse(actor_id).exists()
        actor_name = actor.name if actor else ''
    reason = (payload.get('reason') or '').strip()
    meta_parts = []
    if actor_name:
        meta_parts.append(f'Người thực hiện: {actor_name}')
    if reason:
        meta_parts.append(f'Lý do: {reason}')
    if meta_parts:
        lines.append('. '.join(meta_parts) + '.')
    return Markup('').join(Markup('<p>%s</p>') % escape(part) for part in lines)


def format_hr_message_body(env, message):
    """Format an HR mail.message body into clean Vietnamese HTML for chatter/UI."""
    body = message.body or ''
    text = html_to_inner_content(body)
    kind, payload = _classify_legacy_body(message, text)
    if kind == 'identity_legacy':
        return Markup('<p>%s</p><p>%s</p>') % (
            escape(env._('Đã đồng bộ tên và ảnh hồ sơ với tài khoản. Bằng chứng gốc được giữ trong nhật ký.')),
            escape(env._('Lý do: %s', payload['reason'])),
        )
    if kind == 'role_snapshot_legacy':
        return Markup('<p>%s</p>') % escape(
            env._('Đã lưu đối chiếu phân quyền thay đổi vai trò vào nhật ký kiểm toán.'),
        )
    if kind == 'transfer_legacy':
        return _render_transfer_legacy_html(env, payload)
    if kind == 'onboarding_legacy':
        return Markup('<p>%s</p>') % escape(
            env._('Hồ sơ nhân viên đã được khởi tạo. Quản trị HR có thể thiết lập lộ trình hội nhập.'),
        )
    if kind == 'created_legacy':
        return Markup('<p>%s</p>') % escape(env._('Khởi tạo hồ sơ nhân viên.'))

    if message.model not in ('hr.employee', 'hr.version') or message.message_type != 'tracking' or not body:
        return body

    tree = html.fragment_fromstring(body, create_parent='div')
    changed = False
    for node in tree.iter():
        if node.tag == 'b' and node.text and node.text.startswith('As of'):
            translated = _translate_as_of_text(node.text)
            if translated != node.text:
                node.text = translated
                changed = True
        elif node.tag == 'i' and node.text and node.text.startswith('(') and node.text.endswith(')'):
            inner = node.text[1:-1].strip()
            vi_label = _translate_field_label(inner)
            if vi_label != inner:
                node.text = f'({vi_label})'
                changed = True
        if node.text and node.tag != 'i':
            new_text = _translate_inline_tracking_text(node.text)
            if new_text != node.text:
                node.text = new_text
                changed = True
        if node.tail:
            new_tail = _translate_inline_tracking_text(node.tail)
            if new_tail != node.tail:
                node.tail = new_tail
                changed = True

    if not changed:
        return body
    return escape(tree.text or '') + Markup(''.join(html.tostring(child, encoding='unicode') for child in tree))


def _format_tracking_record(tracking):
    field_desc = tracking.field_id.field_description or (tracking.field_info or {}).get('desc') or ''
    field_name = _translate_field_label(field_desc)
    field_type = tracking.field_id.ttype or ''
    if field_type in ('char', 'text', 'selection', 'many2one', 'boolean'):
        old_val = tracking.old_value_char or tracking.old_value_text or ''
        new_val = tracking.new_value_char or tracking.new_value_text or ''
    elif field_type == 'integer':
        old_val = '' if tracking.old_value_integer in (False, None) else str(tracking.old_value_integer)
        new_val = '' if tracking.new_value_integer in (False, None) else str(tracking.new_value_integer)
    elif field_type == 'float':
        old_val = '' if tracking.old_value_float in (False, None) else str(tracking.old_value_float)
        new_val = '' if tracking.new_value_float in (False, None) else str(tracking.new_value_float)
    elif field_type in ('date', 'datetime'):
        old_val = str(tracking.old_value_datetime or '')[:10]
        new_val = str(tracking.new_value_datetime or '')[:10]
    else:
        old_val = tracking.old_value_char or tracking.old_value_text or ''
        new_val = tracking.new_value_char or tracking.new_value_text or ''
    return {
        'field': field_name,
        'old_value': _translate_tracking_value(old_val),
        'new_value': _translate_tracking_value(new_val),
    }


def _extract_html_changes_and_summary(rendered_body):
    """Extract leading effective date, plain summary paragraphs, and line-by-line tracking diffs."""
    if not rendered_body:
        return '', [], []
    tree = html.fragment_fromstring(str(rendered_body), create_parent='div')
    effective_date = ''
    summary_lines = []
    changes = []

    for child in tree:
        if child.tag == 'b':
            b_text = ' '.join((child.text_content() or '').split())
            if b_text.startswith('Có hiệu lực từ '):
                effective_date = b_text[len('Có hiệu lực từ '):].strip()
                continue
        if child.tag == 'div':
            raw_html = html.tostring(child, encoding='unicode')
            raw_html = re.sub(r'<\s*br\s*/?>', '\n', raw_html, flags=re.IGNORECASE)
            raw_html = re.sub(r'</?\s*div[^>]*>', '', raw_html, flags=re.IGNORECASE)
            parsed_any_line = False
            for part in raw_html.splitlines():
                line_text = ' '.join(html.fragment_fromstring(part, create_parent='span').text_content().split())
                if not line_text:
                    continue
                match = _LEGACY_TRACKING_LINE_RE.match(line_text)
                if match:
                    old_v, new_v, label = match.groups()
                    vi_label = _translate_field_label(label)
                    changes.append({
                        'field': vi_label,
                        'old_value': _translate_tracking_value(old_v),
                        'new_value': _translate_tracking_value(new_v),
                    })
                    parsed_any_line = True
                else:
                    summary_lines.append(line_text)
            if parsed_any_line or summary_lines:
                continue
        if child.tag == 'p':
            p_text = ' '.join((child.text_content() or '').split())
            if p_text:
                summary_lines.append(p_text)
        else:
            other_text = ' '.join((child.text_content() or '').split())
            if other_text:
                summary_lines.append(other_text)

    if not summary_lines and not changes and (tree.text or '').strip():
        summary_lines.append(' '.join((tree.text or '').split()))
    return effective_date, summary_lines, changes


def _infer_history_category(kind, summary_lines, changes):
    joined = ' '.join(summary_lines).lower()
    field_names = {c['field'] for c in changes}
    if kind == 'transfer_legacy' or 'chuyển phòng ban' in joined or 'Phòng ban' in field_names:
        return 'transfer'
    if 'thay đổi vai trò' in joined or 'bổ nhiệm' in joined or ('chức vụ' in joined and 'Chức vụ' not in field_names):
        return 'role'
    if (
        'tài khoản' in joined
        or 'mật khẩu' in joined
        or 'đồng bộ tên và ảnh' in joined
        or {'Tên đăng nhập', 'Trạng thái tài khoản', 'Múi giờ'} & field_names
    ):
        return 'account'
    if 'hồ sơ năng lực' in joined or 'kỹ năng' in joined:
        return 'resume'
    if (
        'hợp đồng' in joined
        or {'Loại hình lao động', 'Ngày bắt đầu hợp đồng', 'Ngày kết thúc hợp đồng', 'Hồ sơ hợp đồng'} & field_names
    ):
        return 'contract'
    if kind == 'created_legacy' or 'khởi tạo' in joined:
        return 'system'
    return 'profile'


def extract_history_item(env, msg, date_formatter):
    """Build one normalized, clean Vietnamese history item for self-service My Profile."""
    text = html_to_inner_content(msg.body or '')
    kind, _payload = _classify_legacy_body(msg, text)
    if kind in ('role_snapshot_legacy', 'onboarding_legacy'):
        return None

    rendered_body = format_hr_message_body(env, msg)
    effective_date, summary_lines, html_changes = _extract_html_changes_and_summary(rendered_body)

    orm_trackings = [
        _format_tracking_record(tr)
        for tr in (msg.tracking_value_ids if 'tracking_value_ids' in msg._fields else ())
        if tr.field_id and tr.field_id.name not in {'tp_source_snapshot', 'tp_wage_confirmed'}
    ]

    changes = list(orm_trackings or html_changes)
    # Remove duplicate "Ngày hiệu lực hồ sơ" when "Ngày hiệu lực" or effective_date is already shown.
    if effective_date or any(c['field'] == 'Ngày hiệu lực' for c in changes):
        changes = [c for c in changes if c['field'] != 'Ngày hiệu lực hồ sơ']

    if not summary_lines and not changes:
        return None

    cat_key = _infer_history_category(kind, summary_lines, changes)
    cat_label, filter_group, tone = _CATEGORY_META[cat_key]

    return {
        'id': msg.id,
        'author': msg.author_id.name or 'Hệ thống',
        'date': date_formatter(env, msg.date),
        'category': cat_key,
        'category_label': cat_label,
        'filter_group': filter_group,
        'tone': tone,
        'effective_date': effective_date,
        'summary_lines': summary_lines,
        'body': ' '.join(summary_lines),
        'changes': changes,
        'trackings': changes,
    }


class HrHistoryMessage(models.Model):
    _inherit = 'mail.message'

    def _tp_hr_identity_summary(self):
        self.ensure_one()
        return format_hr_message_body(self.env, self)

    def _tp_hr_display_body(self):
        return format_hr_message_body(self.env, self)

    def _store_message_fields(self, res, **kwargs):
        super()._store_message_fields(res, **kwargs)
        res.attr('body', lambda message: message._tp_hr_display_body())


class HrIdentityAudit(models.Model):
    _inherit = 'tp.hr.employee.audit'

    action = fields.Selection(
        selection_add=[
            ('identity', 'Đồng bộ danh tính hồ sơ và tài khoản'),
            ('role_change', 'Thay đổi vai trò nghiệp vụ'),
            ('department_transfer', 'Chuyển phòng ban'),
            ('login_change', 'Đổi tên đăng nhập'),
        ],
        ondelete={
            'identity': 'cascade',
            'role_change': 'cascade',
            'department_transfer': 'cascade',
            'login_change': 'cascade',
        },
    )


def readable_tracking(values):
    if values.get('field_label'):
        values['field_label'] = _translate_field_label(values['field_label'])
    for key in ('old_value', 'new_value'):
        if values.get(key) is not None:
            values[key] = _translate_tracking_value(str(values[key]))
    if values.get('field_name') == 'user_state':
        values['field_label'] = 'Trạng thái tài khoản'
    return values


class HrEmployeeTracking(models.Model):
    _inherit = 'hr.employee'

    def _create_mail_tracking_values(self, *args, **kwargs):
        return readable_tracking(super()._create_mail_tracking_values(*args, **kwargs))

    def _track_set_log_message(self, message):
        text = str(message)
        if text.startswith('<b>As of') and text.endswith('</b>'):
            message = Markup('<b>') + escape(_translate_as_of_text(text[3:-4])) + Markup('</b>')
        return super()._track_set_log_message(message)


class HrVersionTracking(models.Model):
    _inherit = 'hr.version'

    def _create_mail_tracking_values(self, *args, **kwargs):
        return readable_tracking(super()._create_mail_tracking_values(*args, **kwargs))
