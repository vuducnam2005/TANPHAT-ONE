# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
"""HTTP endpoints for private request attachments and filtered XLSX export."""
import base64
import io
import json

from werkzeug.exceptions import Forbidden, NotFound

from odoo import _, http
from odoo.exceptions import AccessError, UserError
from odoo.http import request
from odoo.http.stream import content_disposition

from odoo.addons.tp_request.models.attendance_bridge import CORR_EVIDENCE_TAG
from odoo.addons.tp_request.models.request_common import (
    APPROVAL_STATES,
    EXECUTION_STATES,
    PRIORITIES,
    format_dt_local,
    internal,
    is_live_admin_user,
)

MAX_UPLOAD_BYTES = 15 * 1024 * 1024  # 15 MB per file
ALLOWED_MIME_PREFIXES = (
    'image/',
    'application/pdf',
    'text/plain',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.',
    'application/vnd.ms-excel',
    'application/zip',
    'application/x-zip-compressed',
)


def _safe_excel_cell(val):
    text = str(val or '')
    if text and (text.lstrip().startswith(('=', '+', '-', '@')) or text.startswith(('\t', '\r', '\n'))):
        return "'" + text
    return text


class TpRequestController(http.Controller):

    @http.route('/tp_request/attachment/<int:attachment_id>', type='http', auth='user', methods=['GET'])
    def download_attachment(self, attachment_id, download=None, **kw):
        att = request.env['ir.attachment'].sudo().browse(attachment_id).exists()
        if not att or att.res_model != 'tp.request' or not att.res_id:
            raise NotFound()
        req = request.env['tp.request'].browse(att.res_id).exists()
        if not req:
            raise NotFound()
        try:
            req.check_access('read')
        except AccessError:
            raise Forbidden(_('Bạn không có quyền xem hoặc tải tệp đính kèm của hồ sơ này.'))

        raw_obj = att.raw
        raw = raw_obj.content if hasattr(raw_obj, 'content') else (raw_obj or b'')
        disposition = 'attachment' if download else ('inline' if (att.mimetype or '').startswith(('image/', 'application/pdf')) else 'attachment')
        headers = [
            ('Content-Type', att.mimetype or 'application/octet-stream'),
            ('Content-Length', str(len(raw))),
            ('Content-Disposition', content_disposition(att.name or f'file_{att.id}', disposition_type=disposition)),
            ('X-Content-Type-Options', 'nosniff'),
            ('Cache-Control', 'private, no-store'),
        ]
        return request.make_response(raw, headers=headers)

    @http.route('/tp_request/attachment/upload', type='http', auth='user', methods=['POST'])
    def upload_attachment(self, request_id=None, **kw):
        ufile = request.httprequest.files.get('file')
        if not ufile:
            return request.make_json_response({'ok': False, 'error': 'Không tìm thấy tệp tải lên.'}, status=400)
        raw = ufile.read()
        if len(raw) > MAX_UPLOAD_BYTES:
            return request.make_json_response({'ok': False, 'error': 'Dung lượng tệp vượt quá giới hạn 15 MB.'}, status=400)
        mimetype = (ufile.mimetype or 'application/octet-stream').lower()
        if not any(mimetype.startswith(prefix) for prefix in ALLOWED_MIME_PREFIXES):
            return request.make_json_response({
                'ok': False,
                'error': 'Định dạng tệp không được hỗ trợ. Hỗ trợ ảnh, PDF, Word, Excel, TXT, ZIP.',
            }, status=400)

        rec = None
        if request_id and str(request_id).isdigit():
            rec = request.env['tp.request'].browse(int(request_id)).exists()
            if not rec:
                return request.make_json_response({'ok': False, 'error': 'Hồ sơ không tồn tại.'}, status=404)
            try:
                rec.check_access('read')
            except AccessError:
                return request.make_json_response({'ok': False, 'error': 'Không có quyền đính kèm tệp vào hồ sơ này.'}, status=403)
            uid = request.env.uid
            can_owner = rec.requester_user_id.id == uid and rec.approval_state in ('draft', 'returned')
            can_exec = (
                rec.approval_state == 'approved'
                and rec.execution_state in ('pending', 'in_progress')
                and (uid in rec.executor_user_ids.ids or rec.assigned_executor_id.id == uid
                     or (rec.type_id.executor_mode == 'admin_group' and is_live_admin_user(request.env.user, company=rec.company_id)))
            )
            if not (can_owner or can_exec):
                return request.make_json_response({'ok': False, 'error': 'Hồ sơ hiện không cho phép thêm tệp đính kèm.'}, status=403)
            if len(rec.attachment_ids) >= (rec.type_id.max_attachments or 10):
                return request.make_json_response({'ok': False, 'error': f'Đã đạt giới hạn tối đa {rec.type_id.max_attachments or 10} tệp đính kèm.'}, status=400)

        att = request.env['ir.attachment'].sudo().create({
            'name': ufile.filename or 'attachment',
            'raw': raw,
            'mimetype': mimetype,
            'res_model': 'tp.request' if rec else False,
            'res_id': rec.id if rec else 0,
            'public': False,
            'access_token': False,
        })
        if rec:
            internal(rec).write({'attachment_ids': [(4, att.id)]})
            if (
                rec.handler_kind == 'attendance_correction'
                and rec.attendance_correction_id
                and rec.requester_user_id.id == request.env.uid
                and rec.approval_state in ('draft', 'returned')
                and not rec.attendance_correction_id.sudo().evidence_file
            ):
                att.sudo().write({'description': CORR_EVIDENCE_TAG})
                corr_user = request.env['tp.hr.attendance.correction'].browse(rec.attendance_correction_id.id)
                corr_user.with_context(_tp_skip_evidence_mirror=True).write({
                    'evidence_file': base64.b64encode(raw).decode('ascii'),
                    'evidence_name': att.name,
                })
        return request.make_json_response({
            'ok': True,
            'attachment': {
                'id': att.id,
                'name': att.name,
                'mimetype': att.mimetype,
                'file_size': att.file_size or len(raw),
                'download_url': f'/tp_request/attachment/{att.id}',
            },
        })

    @http.route('/tp_request/attachment/<int:attachment_id>/delete', type='http', auth='user', methods=['POST'])
    def delete_attachment(self, attachment_id, **kw):
        att = request.env['ir.attachment'].sudo().browse(attachment_id).exists()
        if not att:
            return request.make_json_response({'ok': False, 'error': 'Tệp không tồn tại.'}, status=404)
        rec = None
        was_corr_evidence = False
        corr_id = 0
        if att.res_model == 'tp.request' and att.res_id:
            rec = request.env['tp.request'].browse(att.res_id).exists()
            if not rec or rec.requester_user_id.id != request.env.uid or rec.approval_state not in ('draft', 'returned'):
                return request.make_json_response({'ok': False, 'error': 'Không có quyền gỡ tệp đính kèm này.'}, status=403)
            was_corr_evidence = att.description == CORR_EVIDENCE_TAG
            if rec.handler_kind == 'attendance_correction' and rec.attendance_correction_id:
                corr_id = rec.attendance_correction_id.id
            internal(rec).write({'attachment_ids': [(3, att.id)]})
        elif not att.res_model and not att.res_id and att.create_uid.id == request.env.uid:
            pass
        else:
            return request.make_json_response({'ok': False, 'error': 'Không có quyền gỡ tệp đính kèm này.'}, status=403)
        att.sudo().unlink()
        if was_corr_evidence and corr_id and rec:
            corr_user = request.env['tp.hr.attendance.correction'].browse(corr_id)
            remaining = rec.sudo().attachment_ids.filtered(
                lambda a: a.res_model == 'tp.request' and a.res_id == rec.id,
            )[:1]
            if remaining:
                rem_obj = remaining.raw
                rem_bytes = rem_obj.content if hasattr(rem_obj, 'content') else (rem_obj or b'')
                remaining.sudo().write({'description': CORR_EVIDENCE_TAG})
                corr_user.with_context(_tp_skip_evidence_mirror=True).write({
                    'evidence_file': base64.b64encode(rem_bytes).decode('ascii') if rem_bytes else False,
                    'evidence_name': remaining.name or False,
                })
            else:
                corr_user.with_context(_tp_skip_evidence_mirror=True).write({
                    'evidence_file': False,
                    'evidence_name': False,
                })
        return request.make_json_response({'ok': True})

    @http.route('/tp_request/export.xlsx', type='http', auth='user', methods=['GET'])
    def export_xlsx(self, mode='mine', params='{}', **kw):
        import openpyxl  # noqa: PLC0415
        from openpyxl.styles import Alignment, Font, PatternFill  # noqa: PLC0415

        try:
            parsed = json.loads(params or '{}')
            if not isinstance(parsed, dict):
                parsed = {}
        except ValueError:
            parsed = {}

        RequestModel = request.env['tp.request']
        try:
            dom = RequestModel._tp_build_filter_domain(mode, parsed)
        except (AccessError, UserError) as exc:
            raise Forbidden(str(exc))

        records = RequestModel.search(dom, order='submitted_at desc, id desc')
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = 'De nghi & Phe duyet'

        headers = [
            'Mã đề nghị', 'Tiêu đề', 'Loại đề nghị', 'Người gửi', 'Mã NV', 'Phòng ban',
            'Ngày gửi', 'Bước hiện tại', 'Hạn xử lý', 'Ưu tiên', 'Trạng thái duyệt', 'Trạng thái thực hiện', 'Quá hạn',
        ]
        ws.append(headers)
        header_fill = PatternFill('solid', fgColor='17324D')
        header_font = Font(bold=True, color='FFFFFF')
        for cell in ws[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center')

        state_map = dict(APPROVAL_STATES)
        exec_map = dict(EXECUTION_STATES)
        prio_map = dict(PRIORITIES)

        for r in records:
            due = r.execution_due_at if (r.approval_state == 'approved' and r.execution_state in ('pending', 'in_progress')) else r.due_at
            ws.append([
                _safe_excel_cell(r.code),
                _safe_excel_cell(r.title),
                _safe_excel_cell(r.type_id.name),
                _safe_excel_cell(r.requester_name_snap or r.requester_user_id.sudo().name),
                _safe_excel_cell(r.requester_code_snap or ''),
                _safe_excel_cell(r.department_name_snap or (r.department_id.sudo().name if r.department_id else '')),
                _safe_excel_cell(format_dt_local(r.submitted_at or r.create_date)),
                _safe_excel_cell(r.current_step_name or '—'),
                _safe_excel_cell(format_dt_local(due)),
                _safe_excel_cell(prio_map.get(r.priority, r.priority)),
                _safe_excel_cell(state_map.get(r.approval_state, r.approval_state)),
                _safe_excel_cell(exec_map.get(r.execution_state, r.execution_state) if r.type_id.requires_execution else '—'),
                'Có' if r.is_overdue else 'Không',
            ])

        widths = [16, 36, 24, 24, 10, 22, 18, 26, 18, 13, 18, 20, 10]
        for idx, width in enumerate(widths, start=1):
            ws.column_dimensions[openpyxl.utils.get_column_letter(idx)].width = width

        buf = io.BytesIO()
        wb.save(buf)
        data = buf.getvalue()
        headers_http = [
            ('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'),
            ('Content-Disposition', content_disposition(f'de_nghi_{mode}.xlsx')),
            ('Content-Length', str(len(data))),
            ('Cache-Control', 'private, no-store'),
        ]
        return request.make_response(data, headers=headers_http)
