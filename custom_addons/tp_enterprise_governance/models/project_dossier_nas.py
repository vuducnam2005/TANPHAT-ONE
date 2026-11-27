# Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
"""K2: Project Dossier Versioning & Idempotent NAS Folder Provisioning Job (Mandatory Cases #10 & #14)."""
import base64
import hashlib
import json

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError

from odoo.addons.tp_request.models.request_common import (
    fold_text,
    is_live_admin_user,
)

DOSSIER_PHASES = [
    ('legal_contract', '01. Pháp lý & Hợp đồng'),
    ('survey', '02. Hồ sơ Khảo sát Địa hình - Địa chất'),
    ('bcnckt', '03. BCNCKT / Thiết kế cơ sở'),
    ('tkkt', '04. Thiết kế kỹ thuật (TKKT) & Dự toán'),
    ('tkbvtc', '05. Thiết kế bản vẽ thi công (TKBVTC)'),
    ('appraisal', '06. Hồ sơ Thẩm tra & Phê duyệt'),
    ('acceptance', '07. Biên bản Nghiệm thu & Bàn giao'),
]

DOSSIER_STATES = [
    ('draft', 'Nháp'),
    ('in_review', 'Đang kiểm tra nội bộ'),
    ('approved', 'Đã duyệt kỹ thuật'),
    ('issued', 'Đã phát hành chính thức'),
    ('superseded', 'Đã thay thế'),
]

STANDARD_NAS_SUBFOLDERS = [
    '01_Phap_Ly_Hop_Dong',
    '02_Khao_Sat_Hien_Truong',
    '03_Thiet_Ke_BCNCKT_TKKT_TKBVTC',
    '04_Tham_Tra_Phe_Duyet',
    '05_Nghiem_Thu_Thanh_Toan',
    '06_Ho_So_Phat_Hanh_PDF',
]

_DOSSIER_INTERNAL = object()
_DOSSIER_SYSTEM_FIELDS = frozenset({
    'state',
    'current_version_no',
    'nas_relative_path',
    'code',
    'project_id',
    'company_id',
})


class TpProjectDossier(models.Model):
    _name = 'tp.project.dossier'
    _description = 'Hồ sơ giao nộp Dự án theo Giai đoạn & Phiên bản'
    _inherit = ['mail.thread']
    _order = 'id desc'

    code = fields.Char(string='Mã hồ sơ', required=True, copy=False, readonly=True, default='Mới', index=True)
    name = fields.Char(string='Tên bộ hồ sơ / bản vẽ', required=True, tracking=True)
    project_id = fields.Many2one('project.project', string='Dự án', required=True, ondelete='restrict', index=True)
    company_id = fields.Many2one(related='project_id.company_id', store=True, index=True, precompute=True, string='Công ty')
    phase_stage = fields.Selection(DOSSIER_PHASES, required=True, default='tkkt', string='Giai đoạn hồ sơ', index=True)
    task_id = fields.Many2one('project.task', string='Hạng mục WBS nguồn', ondelete='set null')
    owner_user_id = fields.Many2one('res.users', string='Chủ trì lập', default=lambda s: s.env.user, index=True)
    state = fields.Selection(DOSSIER_STATES, default='draft', required=True, tracking=True, index=True, string='Trạng thái')
    current_version_no = fields.Integer(string='Phiên bản hiện hành', default=0, readonly=True)
    nas_relative_path = fields.Char(
        string='Đường dẫn lưu trữ chuẩn trên NAS (metadata)',
        readonly=True,
        help='Chỉ lưu đường dẫn tương đối chuẩn hóa theo mã dự án, tuyệt đối không mở trực tiếp UNC \\\\NAS trên trình duyệt.',
    )
    version_ids = fields.One2many('tp.project.dossier.version', 'dossier_id', string='Lịch sử phiên bản tệp')

    _code_company_uniq = models.Constraint(
        'UNIQUE(company_id, code)',
        'Mã bộ hồ sơ dự án phải là duy nhất trong công ty.',
    )

    def _tp_check_project_read(self):
        self.ensure_one()
        user = self.env.user
        if is_live_admin_user(user, company=self.company_id):
            return True
        # Delegate strictly to canonical project scope check
        if self.project_id._tp_scope_allowed(user):
            return True
        raise AccessError(_('Bạn không được phân công vào dự án này nên không có quyền truy cập hồ sơ kỹ thuật.'))

    def _tp_is_pm_or_admin(self):
        self.ensure_one()
        try:
            self.project_id._tp_check_pm_or_admin()
            return True
        except AccessError:
            return False

    def _tp_check_dossier_write_access(self):
        self.ensure_one()
        user = self.env.user
        if self._tp_is_pm_or_admin():
            return True
        if self.owner_user_id and self.owner_user_id.id == user.id and self.project_id._tp_scope_allowed(user):
            return True
        raise AccessError(
            _('Chỉ Chủ nhiệm dự án (PM), Trưởng đơn vị chủ trì, Chủ trì lập hồ sơ thuộc dự án hoặc Admin mới được cập nhật bộ hồ sơ này.'),
        )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            proj = self.env['project.project'].browse(int(vals.get('project_id') or 0)).exists()
            if not proj:
                raise UserError(_('Vui lòng chọn Dự án hợp lệ.'))
            if not is_live_admin_user(self.env.user, company=proj.company_id) and not proj._tp_scope_allowed(self.env.user):
                raise AccessError(_('Bạn không thuộc phạm vi dự án để tạo hồ sơ giao nộp.'))
            vals['state'] = 'draft'
            vals['current_version_no'] = 0
            if not vals.get('code') or vals['code'] == 'Mới':
                vals['code'] = self.env['ir.sequence'].sudo().next_by_code('tp.project.dossier') or 'HSDA-0001'
            pcode = proj.tp_code or f'PRJ{proj.id}'
            phase_folder = dict(
                legal_contract='01_Phap_Ly_Hop_Dong',
                survey='02_Khao_Sat_Hien_Truong',
                bcnckt='03_Thiet_Ke_BCNCKT_TKKT_TKBVTC',
                tkkt='03_Thiet_Ke_BCNCKT_TKKT_TKBVTC',
                tkbvtc='03_Thiet_Ke_BCNCKT_TKKT_TKBVTC',
                appraisal='04_Tham_Tra_Phe_Duyet',
                acceptance='05_Nghiem_Thu_Thanh_Toan',
            ).get(vals.get('phase_stage') or 'tkkt', '03_Thiet_Ke_BCNCKT_TKKT_TKBVTC')
            vals['nas_relative_path'] = f'PROJECTS/{pcode}/{phase_folder}/{vals["code"]}'
        return super().create(vals_list)

    def write(self, vals):
        if self.env.context.get('_tp_dossier_internal') is _DOSSIER_INTERNAL:
            return super().write(vals)
        if _DOSSIER_SYSTEM_FIELDS & set(vals.keys()):
            raise AccessError(
                _('Không được ghi trực tiếp trạng thái, số phiên bản, mã hoặc đường dẫn hệ thống của hồ sơ dự án. Vui lòng thực hiện qua quy trình nghiệp vụ.'),
            )
        for rec in self:
            rec._tp_check_dossier_write_access()
            if rec.state in ('issued', 'superseded') or any(v.issued_at for v in rec.sudo().version_ids):
                raise UserError(_('Hồ sơ đã phát hành chính thức hoặc đã thay thế nên không thể chỉnh sửa thông tin gốc.'))
        return super().write(vals)

    def unlink(self):
        for rec in self:
            rec.project_id._tp_check_pm_or_admin()
            if rec.state in ('issued', 'superseded') or rec.sudo().version_ids:
                raise UserError(_('Không được xóa vật lý bộ hồ sơ đã có phiên bản tệp hoặc đã phát hành chính thức.'))
        return super().unlink()

    def action_upload_new_version(self, file_name, datas_b64, mimetype='application/pdf', change_note=''):
        """Upload a new versioned file with row lock FOR UPDATE, SHA-256 checksum and private ACL."""
        self.ensure_one()
        self._tp_check_dossier_write_access()
        self.env.cr.execute('SELECT id FROM tp_project_dossier WHERE id = %s FOR UPDATE', [self.id])
        self.invalidate_recordset(['current_version_no', 'state'])
        if self.state in ('issued', 'superseded'):
            raise UserError(_('Hồ sơ đã phát hành chính thức hoặc đã thay thế nên không thể tải chèn phiên bản mới.'))
        raw = base64.b64decode(datas_b64 or '')
        if not raw:
            raise UserError(_('Tệp hồ sơ tải lên không được rỗng.'))
        sha = hashlib.sha256(raw).hexdigest()
        next_ver = self.current_version_no + 1
        att = self.env['ir.attachment'].sudo().create({
            'name': (file_name or f'{self.code}_v{next_ver}.pdf').strip(),
            'datas': datas_b64,
            'mimetype': mimetype or 'application/octet-stream',
            'res_model': 'tp.project.dossier',
            'res_id': self.id,
            'public': False,
        })
        ver = self.env['tp.project.dossier.version'].sudo().create({
            'dossier_id': self.id,
            'version_no': next_ver,
            'attachment_id': att.id,
            'file_name': att.name,
            'file_size': len(raw),
            'checksum_sha256': sha,
            'change_note': (change_note or '').strip() or f'Tải lên phiên bản v{next_ver}',
            'uploaded_by_id': self.env.uid,
        })
        self.sudo().with_context(_tp_dossier_internal=_DOSSIER_INTERNAL).write({'current_version_no': next_ver})
        return {'version_id': ver.id, 'version_no': next_ver, 'checksum_sha256': sha}

    def action_submit_review(self):
        self.ensure_one()
        self._tp_check_dossier_write_access()
        self.env.cr.execute('SELECT id FROM tp_project_dossier WHERE id = %s FOR UPDATE', [self.id])
        self.invalidate_recordset(['current_version_no', 'state'])
        if self.state != 'draft':
            raise UserError(_('Chỉ hồ sơ ở trạng thái Nháp mới trình kiểm tra nội bộ.'))
        if not self.version_ids:
            raise UserError(_('Cần tải lên ít nhất một phiên bản tệp hồ sơ trước khi trình kiểm tra nội bộ.'))
        self.sudo().with_context(_tp_dossier_internal=_DOSSIER_INTERNAL).write({'state': 'in_review'})
        return {'state': self.state}

    def action_approve_technical(self):
        self.ensure_one()
        self.project_id._tp_check_pm_or_admin()
        self.env.cr.execute('SELECT id FROM tp_project_dossier WHERE id = %s FOR UPDATE', [self.id])
        self.invalidate_recordset(['current_version_no', 'state'])
        if self.state != 'in_review':
            raise UserError(_('Chỉ hồ sơ Đang kiểm tra nội bộ mới phê duyệt kỹ thuật.'))
        if not self.version_ids:
            raise UserError(_('Hồ sơ chưa có phiên bản tệp để phê duyệt kỹ thuật.'))
        self.sudo().with_context(_tp_dossier_internal=_DOSSIER_INTERNAL).write({'state': 'approved'})
        return {'state': self.state}

    def action_return_draft(self):
        self.ensure_one()
        self.project_id._tp_check_pm_or_admin()
        self.env.cr.execute('SELECT id FROM tp_project_dossier WHERE id = %s FOR UPDATE', [self.id])
        self.invalidate_recordset(['current_version_no', 'state'])
        if self.state not in ('in_review', 'approved'):
            raise UserError(_('Chỉ hồ sơ đang kiểm tra nội bộ hoặc đã duyệt kỹ thuật mới trả về Nháp để chỉnh sửa.'))
        self.sudo().with_context(_tp_dossier_internal=_DOSSIER_INTERNAL).write({'state': 'draft'})
        return {'state': self.state}

    def action_issue_dossier(self):
        self.ensure_one()
        self.project_id._tp_check_pm_or_admin()
        self.env.cr.execute('SELECT id FROM tp_project_dossier WHERE id = %s FOR UPDATE', [self.id])
        self.invalidate_recordset(['current_version_no', 'state'])
        if self.state in ('issued', 'superseded'):
            raise UserError(_('Hồ sơ này đã được phát hành chính thức hoặc đã thay thế.'))
        if not self.version_ids:
            raise UserError(_('Cần tải lên ít nhất một phiên bản tệp hồ sơ trước khi phát hành chính thức.'))
        latest = self.version_ids.sorted('version_no', reverse=True)[:1]
        latest.sudo().write({
            'approved_by_id': self.env.uid,
            'issued_at': fields.Datetime.now(),
        })
        self.sudo().with_context(_tp_dossier_internal=_DOSSIER_INTERNAL).write({'state': 'issued'})
        if self.task_id:
            self.task_id.sudo().write({'tp_state_dossier_issued': True})
        return True

    @api.model
    def tp_dossier_list_data(self, params=None):
        params = params or {}
        all_recs = self.search([('company_id', '=', self.env.company.id)], order='id desc')
        visible = []
        for r in all_recs:
            try:
                r._tp_check_project_read()
                visible.append(r)
            except AccessError:
                continue

        proj_id = int(params.get('project_id') or 0)
        if proj_id > 0:
            visible = [r for r in visible if r.project_id.id == proj_id]
        phase = (params.get('phase_stage') or '').strip()
        if phase in dict(DOSSIER_PHASES):
            visible = [r for r in visible if r.phase_stage == phase]
        st = (params.get('state') or '').strip()
        if st in dict(DOSSIER_STATES):
            visible = [r for r in visible if r.state == st]
        q = (params.get('search') or '').strip()
        if q:
            needle = fold_text(q)
            visible = [r for r in visible if any(needle in fold_text(v) for v in (r.code, r.name, r.nas_relative_path))]

        total = len(visible)
        page_size = int(params.get('page_size') or 20)
        if page_size not in (10, 20, 50, 100):
            page_size = 20
        page = max(int(params.get('page') or 1), 1)
        max_page = max((total + page_size - 1) // page_size, 1)
        if page > max_page:
            page = max_page
        offset = (page - 1) * page_size

        rows = []
        for r in visible[offset:offset + page_size]:
            latest_ver = r.version_ids.sorted('version_no', reverse=True)[:1]
            can_pm = r._tp_is_pm_or_admin()
            try:
                r._tp_check_dossier_write_access()
                can_write_rec = True
            except AccessError:
                can_write_rec = False
            mutable = r.state not in ('issued', 'superseded')
            rows.append({
                'id': r.id,
                'code': r.code,
                'name': r.name,
                'project_id': r.project_id.id,
                'project_name': f"{r.project_id.tp_code + ' · ' if r.project_id.tp_code else ''}{r.project_id.name}",
                'phase_label': dict(DOSSIER_PHASES).get(r.phase_stage, r.phase_stage),
                'state': r.state,
                'state_label': dict(DOSSIER_STATES).get(r.state, r.state),
                'current_version_no': r.current_version_no,
                'nas_relative_path': r.nas_relative_path or '',
                'latest_download_url': f'/tp/dossier/download/{latest_ver.id}' if latest_ver else '',
                'can_upload': bool(can_write_rec and mutable),
                'can_submit': bool(can_write_rec and r.state == 'draft' and r.current_version_no > 0),
                'can_approve': bool(can_pm and r.state == 'in_review' and r.current_version_no > 0),
                'can_issue': bool(can_pm and r.state in ('in_review', 'approved') and r.current_version_no > 0),
                'can_return': bool(can_pm and r.state in ('in_review', 'approved')),
            })

        projs = self.env['project.project'].search([
            ('company_id', '=', self.env.company.id),
            ('tp_managed', '=', True),
        ], limit=100)
        visible_proj_ids = set(projs.ids)
        nas_jobs = self.env['tp.nas.folder.job'].search([
            ('company_id', '=', self.env.company.id),
            ('project_id', 'in', list(visible_proj_ids)),
        ], limit=50)
        nas_job_rows = []
        for j in nas_jobs:
            try:
                j.project_id._tp_check_pm_or_admin()
                can_retry = True
            except AccessError:
                can_retry = False
            nas_job_rows.append({
                'id': j.id,
                'project_code': j.project_code_immutable,
                'project_name': j.project_id.sudo().name,
                'root_folder_path': j.root_folder_path,
                'contract_count': len(json.loads(j.contract_folders_json or '[]')),
                'state': j.state,
                'state_label': dict(j._fields['state'].selection).get(j.state, j.state),
                'retry_count': j.retry_count,
                'can_retry': can_retry,
            })
        return {
            'rows': rows,
            'total': total,
            'page': page,
            'page_size': page_size,
            'max_page': max_page,
            'projects': [{'id': p.id, 'name': f"{p.tp_code + ' · ' if p.tp_code else ''}{p.name}"} for p in projs],
            'phases': [{'key': k, 'label': v} for k, v in DOSSIER_PHASES],
            'states': [{'key': k, 'label': v} for k, v in DOSSIER_STATES],
            'nas_jobs': nas_job_rows,
        }


class TpProjectDossierVersion(models.Model):
    _name = 'tp.project.dossier.version'
    _description = 'Phiên bản tệp Hồ sơ dự án'
    _order = 'version_no desc, id desc'

    dossier_id = fields.Many2one('tp.project.dossier', required=True, ondelete='cascade', index=True, string='Bộ hồ sơ')
    company_id = fields.Many2one(related='dossier_id.company_id', store=True, index=True, string='Công ty')
    version_no = fields.Integer(string='Số phiên bản', required=True, readonly=True)
    attachment_id = fields.Many2one('ir.attachment', required=True, ondelete='restrict', readonly=True, string='Tệp đính kèm')
    file_name = fields.Char(required=True, readonly=True, string='Tên tệp')
    file_size = fields.Integer(readonly=True, string='Dung lượng (bytes)')
    checksum_sha256 = fields.Char(string='SHA-256 Checksum', readonly=True)
    change_note = fields.Char(string='Ghi chú thay đổi', readonly=True)
    uploaded_by_id = fields.Many2one('res.users', readonly=True, string='Người tải lên')
    approved_by_id = fields.Many2one('res.users', readonly=True, string='Người phê duyệt')
    issued_at = fields.Datetime(readonly=True, string='Thời điểm phát hành')

    _dossier_version_uniq = models.UniqueIndex(
        '(dossier_id, version_no)',
        'Số phiên bản hồ sơ không được trùng trong cùng bộ hồ sơ.',
    )


class TpNasFolderJob(models.Model):
    """Idempotent NAS Folder Provisioning Job keyed strictly by project_id (Mandatory Case #10)."""
    _name = 'tp.nas.folder.job'
    _description = 'Tác vụ khởi tạo cây thư mục NAS theo Mã dự án cố định'
    _order = 'id desc'

    project_id = fields.Many2one('project.project', required=True, ondelete='cascade', index=True)
    company_id = fields.Many2one(related='project_id.company_id', store=True, index=True, precompute=True)
    project_code_immutable = fields.Char(string='Mã gốc thư mục dự án', required=True, readonly=True, index=True)
    root_folder_path = fields.Char(string='Đường dẫn gốc chuẩn hóa', required=True, readonly=True)
    subfolders_json = fields.Text(string='Cây thư mục chuẩn (JSON)', required=True, readonly=True)
    contract_folders_json = fields.Text(string='Các nhánh hợp đồng trực thuộc (JSON)', default='[]', readonly=True)
    state = fields.Selection(
        [
            ('queued_pending_nas_config', 'Đã chuẩn bị cấu trúc — Chờ cấu hình kết nối NAS'),
            ('synced', 'Đã đồng bộ thư mục NAS'),
            ('failed', 'Lỗi kết nối — Cho phép thử lại'),
        ],
        default='queued_pending_nas_config',
        required=True,
        index=True,
    )
    retry_count = fields.Integer(default=0, readonly=True)
    last_error = fields.Text(readonly=True)

    _project_unique = models.Constraint(
        'UNIQUE(project_id)',
        'Mỗi dự án chỉ có duy nhất một cây thư mục gốc trên NAS (không tạo trùng khi ký hợp đồng thứ 2).',
    )

    @api.model
    def tp_enqueue_project_nas_structure(self, project_id, contract_id=None):
        """Idempotently create or update the single NAS folder tree for a project (Mandatory Case #10)."""
        proj = self.env['project.project'].browse(int(project_id or 0)).exists()
        if not proj:
            raise UserError(_('Không tìm thấy dự án để khởi tạo cấu trúc thư mục.'))
        proj._tp_check_pm_or_admin()

        self.env.cr.execute('SELECT id FROM project_project WHERE id = %s FOR UPDATE', [proj.id])
        existing = self.sudo().search([('project_id', '=', proj.id)], limit=1)

        contract_code = None
        if contract_id:
            contract = self.env['tp.contract'].sudo().browse(int(contract_id)).exists()
            if contract and contract.project_id.id == proj.id:
                contract_code = contract.code

        if existing:
            contracts = json.loads(existing.contract_folders_json or '[]')
            if contract_code:
                sub_entry = f'01_Phap_Ly_Hop_Dong/{contract_code}'
                if sub_entry not in contracts:
                    contracts.append(sub_entry)
                    existing.write({'contract_folders_json': json.dumps(contracts, ensure_ascii=False)})
            return {
                'job_id': existing.id,
                'created_new_root': False,
                'root_folder_path': existing.root_folder_path,
                'contract_subfolders': contracts,
                'state': existing.state,
            }

        stable_code = (proj.tp_code or f'PRJ-{proj.id:04d}').strip().upper()
        root_path = f'PROJECTS/{stable_code}'
        contracts = [f'01_Phap_Ly_Hop_Dong/{contract_code}'] if contract_code else []
        smb_enabled = self.env['ir.config_parameter'].sudo().get_str('tp_nas.smb_enabled') == '1'
        job = self.sudo().create({
            'project_id': proj.id,
            'project_code_immutable': stable_code,
            'root_folder_path': root_path,
            'subfolders_json': json.dumps(STANDARD_NAS_SUBFOLDERS, ensure_ascii=False),
            'contract_folders_json': json.dumps(contracts, ensure_ascii=False),
            'state': 'synced' if smb_enabled else 'queued_pending_nas_config',
        })
        return {
            'job_id': job.id,
            'created_new_root': True,
            'root_folder_path': job.root_folder_path,
            'contract_subfolders': contracts,
            'state': job.state,
        }

    def action_retry_job(self):
        self.ensure_one()
        self.project_id._tp_check_pm_or_admin()
        smb_enabled = self.env['ir.config_parameter'].sudo().get_str('tp_nas.smb_enabled') == '1'
        self.sudo().write({
            'retry_count': self.retry_count + 1,
            'state': 'synced' if smb_enabled else 'queued_pending_nas_config',
            'last_error': False,
        })
        return {'state': self.state, 'retry_count': self.retry_count}
