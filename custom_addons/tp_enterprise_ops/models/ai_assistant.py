# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
"""L: RBAC-Guarded Grounded Executive AI Assistant (Mandatory Case #16 — Zero Cross-Scope / Payroll Leak)."""
from odoo import _, api, models
from odoo.exceptions import AccessError, UserError

from odoo.addons.tp_request.models.request_common import fold_text


class TpAiAssistant(models.AbstractModel):
    _name = 'tp.ai.assistant'
    _description = 'Trợ lý AI Nội bộ có Kiểm soát Quyền truy cập (RBAC Grounded Retrieval)'

    @api.model
    def tp_grounded_query(self, query_text):
        """Search ONLY records permitted to the current caller via ORM ACL — NEVER sudo(), NEVER payroll/confidential!

        Mandatory Case #16:
        - Caller's ORM ACL + audience/project scope checks run BEFORE assembling results or citations.
        - Explicitly excludes tp.payroll.*, hr.version.wage, and restricted financial models.
        - Decoupled from core CRUD: if external LLM is disabled (default), deterministic grounded retrieval + summary runs cleanly.
        """
        q = (query_text or '').strip()
        needle = fold_text(q)
        citations = []

        # 1. Permitted Internal Announcements (audience-checked, never sudo)
        for ann in self.env['tp.announcement'].search([('company_id', '=', self.env.company.id)], limit=50):
            if not ann._tp_is_user_in_audience(self.env.user):
                continue
            if not needle or any(needle in fold_text(v) for v in (ann.code, ann.name, ann.body)):
                citations.append({
                    'source_type': 'Thông báo nội bộ',
                    'model': 'tp.announcement',
                    'res_id': ann.id,
                    'action_xmlid': 'tp_digital_office.action_announcements',
                    'open_mode': 'client_action',
                    'code': ann.code,
                    'title': ann.name,
                    'snippet': (ann.body or '')[:180],
                    'url': '/app/van-phong-so/thong-bao',
                })

        # 2. Permitted Meeting Minutes (ORM record rule enforced, never sudo)
        for mm in self.env['tp.meeting.minute'].search([('company_id', '=', self.env.company.id)], limit=50):
            if not needle or any(needle in fold_text(v) for v in (mm.code, mm.name, mm.conclusion_content)):
                citations.append({
                    'source_type': 'Biên bản họp',
                    'model': 'tp.meeting.minute',
                    'res_id': mm.id,
                    'action_xmlid': 'tp_digital_office.action_meeting_minutes',
                    'open_mode': 'client_action',
                    'code': mm.code,
                    'title': mm.name,
                    'snippet': (mm.conclusion_content or '')[:180],
                    'url': '/app/van-phong-so/bien-ban-hop',
                })

        # 3. Permitted Project Dossiers (strict _tp_check_project_read enforced!)
        for dos in self.env['tp.project.dossier'].search([('company_id', '=', self.env.company.id)], limit=50):
            try:
                dos._tp_check_project_read()
            except AccessError:
                continue
            if not needle or any(needle in fold_text(v) for v in (dos.code, dos.name, dos.nas_relative_path)):
                citations.append({
                    'source_type': 'Hồ sơ dự án',
                    'model': 'tp.project.dossier',
                    'res_id': dos.id,
                    'action_xmlid': 'tp_enterprise_governance.action_project_dossier_nas',
                    'open_mode': 'client_action',
                    'code': dos.code,
                    'title': dos.name,
                    'snippet': f'Giai đoạn: {dos.phase_stage} · Phiên bản v{dos.current_version_no}',
                    'url': '/app/du-an/ho-so-nas',
                })

        # 4. Permitted Tasks (ORM record rule enforced, never sudo)
        for tsk in self.env['project.task'].search([], limit=50):
            if not needle or needle in fold_text(tsk.name):
                citations.append({
                    'source_type': 'Công việc',
                    'model': 'project.task',
                    'res_id': tsk.id,
                    'action_xmlid': 'tp_personal_tools.action_my_work_workspace',
                    'open_mode': 'form',
                    'code': tsk.tp_wbs_code or f'TASK-{tsk.id}',
                    'title': tsk.name,
                    'snippet': getattr(tsk, 'tp_deliverable', '') or 'Công việc trong phạm vi quyền đọc của bạn',
                    'url': f'/app/ca-nhan/cong-viec/{tsk.id}',
                })

        ext_llm = self.env['ir.config_parameter'].sudo().get_str('tp_ai.external_llm_enabled') == '1'
        summary = (
            f'Tìm thấy {len(citations)} nguồn dữ liệu nội bộ trong đúng phạm vi quyền truy cập của tài khoản "{self.env.user.name}". '
            'Dữ liệu lương, hồ sơ mật ngoài phân công dự án và hợp đồng hạn chế quyền được loại trừ hoàn toàn.'
            if citations
            else 'Không tìm thấy văn bản, biên bản, hồ sơ dự án hoặc công việc nào khớp từ khóa trong phạm vi quyền được phép xem của bạn.'
        )
        return {
            'query': q,
            'summary': summary,
            'citations': citations[:20],
            'external_llm_enabled': ext_llm,
            'policy_notice': 'Chế độ Tra cứu nội bộ có trích dẫn nguồn (RBAC). Kết nối LLM bên ngoài đang tắt mặc định chờ cấu hình nhà cung cấp & quy chế dữ liệu.',
        }

    @api.model
    def tp_preview_draft_from_prompt(self, text_prompt, draft_kind='task'):
        """Preview-only draft builder — NEVER writes to DB without explicit user confirmation."""
        clean = (text_prompt or '').strip()
        if not clean:
            raise UserError(_('Vui lòng nhập nội dung yêu cầu trước khi tạo bản xem trước công việc.'))
        return {
            'saved_to_db': False,
            'draft_kind': draft_kind,
            'preview': {
                'title': clean[:120] or 'Đầu việc dự thảo từ Trợ lý nội bộ',
                'description': clean,
                'requires_explicit_confirm': True,
            },
        }
