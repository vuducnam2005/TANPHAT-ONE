"""Synthetic fixtures for UI-DEMO-001.

Every name, amount and file here is invented for the demo; nothing comes from
Tan Phat records, NAS folders or Excel files. ``seed`` is idempotent: records
are bound to external IDs under ``tp_demo_seed`` and contract reviews move
forward only from the state they are in, through the real TP Contracts
workflow acting as the demo workflow users.
"""

import datetime

from odoo import Command, fields
from odoo.tools import BinaryBytes

SEED_MODULE = 'tp_demo_seed'
DB_PREFIX = 'tp_tanphat_demo_'
COMPANY_NAME = 'Công ty Trình diễn TANPHAT ONE (DEMO)'
CREATE_CONTEXT = {'no_reset_password': True, 'tracking_disable': True, 'mail_create_nosubscribe': True,
                  'mail_create_nolog': True, 'mail_notrack': True, 'mail_auto_subscribe_no_notify': True}

# Users who sign in to the demo; every other user has no password.
ACTOR_LOGINS = ('demo.lanhdao', 'demo.kysu')

DEPARTMENTS = [
    ('KHKD', 'Phòng Kế hoạch – Kinh doanh (DEMO)'),
    ('KS', 'Phòng Khảo sát (DEMO)'),
    ('TK', 'Phòng Thiết kế (DEMO)'),
    ('TCKT', 'Phòng Tài chính – Kế toán (DEMO)'),
    ('HCNS', 'Phòng Hành chính – Nhân sự (DEMO)'),
]

PARTNERS = {
    'owner_song_xanh': 'Ban QLDA Giao thông tỉnh Sông Xanh (DEMO)',
    'owner_binh_minh': 'Ban QLDA Khu công nghiệp Bình Minh (DEMO)',
    'owner_doi_cat': 'Sở Giao thông Vận tải tỉnh Đồi Cát (DEMO)',
    'owner_go_may': 'Ban QLDA huyện Gò Mây (DEMO)',
    'owner_ven_bien': 'Công ty Hạ tầng Ven Biển (DEMO)',
    'sub_drilling': 'Công ty Khoan Địa chất Thử nghiệm (DEMO)',
}

# key, name, department, job title, is a (password-less) user
STAFF = [
    ('khoa', 'Trần Minh Khoa (DEMO)', 'KS', 'Chủ nhiệm khảo sát', True),
    ('long', 'Vũ Đức Long (DEMO)', 'KS', 'Kỹ sư địa chất', True),
    ('son', 'Hoàng Văn Sơn (DEMO)', 'KS', 'Kỹ sư khảo sát', True),
    ('nam', 'Nguyễn Hải Nam (DEMO)', 'TK', 'Chủ nhiệm thiết kế cầu', True),
    ('lan', 'Bùi Thị Lan (DEMO)', 'TK', 'Kỹ sư thiết kế đường', True),
    ('tuan', 'Phan Anh Tuấn (DEMO)', 'TK', 'Kỹ sư kết cấu', True),
    ('linh', 'Đặng Thùy Linh (DEMO)', 'TK', 'Kỹ sư thoát nước', True),
    ('tri', 'Đỗ Minh Trí (DEMO)', 'KHKD', 'Chuyên viên kinh doanh', True),
    ('huong', 'Mai Thanh Hương (DEMO)', 'KHKD', 'Chuyên viên kế hoạch', False),
    ('bao', 'Lê Quốc Bảo (DEMO)', 'TCKT', 'Kế toán dự án', False),
    ('ha', 'Ngô Thị Hà (DEMO)', 'HCNS', 'Chuyên viên nhân sự', False),
    ('phuc', 'Tạ Văn Phúc (DEMO)', 'KS', 'Kỹ thuật viên đo đạc', False),
]

# key, code, name, lead department, partner, manager, start, end
PROJECTS = [
    ('cau', 'DEMO-CAU-01', 'Cầu Sông Xanh – tư vấn khảo sát, thiết kế (DEMO)', 'TK', 'owner_song_xanh', 'nam',
     '2026-08-15', '2027-06-30'),
    ('duong', 'DEMO-DUONG-02', 'Đường nối Khu công nghiệp Bình Minh (DEMO)', 'TK', 'owner_binh_minh', 'lan',
     '2026-07-01', '2027-03-31'),
    ('nut', 'DEMO-NUT-03', 'Nút giao Đồi Cát – khảo sát, lập phương án (DEMO)', 'KS', 'owner_doi_cat', 'khoa',
     '2026-10-01', '2027-04-30'),
]

STAGES = [('prepare', 'Chuẩn bị', False), ('doing', 'Đang thực hiện', False),
          ('check', 'Chờ kiểm tra', False), ('done', 'Hoàn thành', True)]
TAGS = [('survey', 'Khảo sát'), ('design', 'Thiết kế'), ('records', 'Hồ sơ'), ('site', 'Hiện trường')]

# project, name, stage, assignee (or None), deadline offset in days, tags
TASKS = [
    ('cau', 'Lập đề cương nhiệm vụ khảo sát', 'done', 'khoa', -40, ['records']),
    ('cau', 'Khảo sát địa hình đường dẫn bờ trái', 'doing', 'khoa', 6, ['survey', 'site']),
    ('cau', 'Khảo sát địa hình đường dẫn bờ phải', 'doing', 'long', -3, ['survey', 'site']),
    ('cau', 'Lập phương án khoan địa chất mố, trụ', 'check', 'long', 2, ['survey']),
    ('cau', 'Bản vẽ bố trí chung cầu – phiên bản B', 'doing', 'nam', 12, ['design']),
    ('cau', 'Tính toán kết cấu nhịp dẫn', 'prepare', 'tuan', 20, ['design']),
    ('cau', 'Thống kê khối lượng sơ bộ', 'prepare', None, 25, ['design', 'records']),
    ('cau', 'Báo cáo tiến độ tháng 10 cho chủ đầu tư', 'done', 'nam', -2, ['records']),
    ('duong', 'Khảo sát hiện trạng tuyến', 'done', 'son', -30, ['survey', 'site']),
    ('duong', 'Khảo sát thủy văn 3 cống ngang đường', 'done', 'son', -20, ['survey', 'site']),
    ('duong', 'Bình đồ, trắc dọc tuyến – sửa theo ý kiến kiểm tra', 'doing', 'lan', -5, ['design']),
    ('duong', 'Thiết kế thoát nước dọc tuyến', 'check', 'linh', 3, ['design']),
    ('duong', 'Thiết kế kết cấu áo đường', 'doing', 'lan', 10, ['design']),
    ('duong', 'Lập dự toán xây dựng', 'prepare', None, 18, ['records']),
    ('duong', 'Chuẩn bị hồ sơ trình thẩm định', 'prepare', 'nam', 30, ['records']),
    ('nut', 'Đo vẽ địa hình nút giao', 'doing', 'khoa', -1, ['survey', 'site']),
    ('nut', 'Đo bù điểm khuất', 'prepare', 'son', 4, ['survey', 'site']),
    ('nut', 'Khảo sát địa chất nền đường nhánh N2', 'prepare', 'long', 35, ['survey']),
    ('nut', 'Phương án tổ chức nút giao', 'doing', 'lan', 14, ['design']),
    ('nut', 'Phân tích lưu lượng giao thông hiện trạng', 'check', None, -8, ['design']),
]

# name, partner, crm stage xmlid, expected revenue (VND), probability, deadline offset
OPPORTUNITIES = [
    ('Tư vấn thiết kế cầu Sông Xanh giai đoạn 2 (DEMO)', 'owner_song_xanh', 'crm.stage_lead3', 4_200_000_000, 60, 45),
    ('Khảo sát địa chất mở rộng đường dẫn cầu (DEMO)', 'owner_song_xanh', 'crm.stage_lead2', 900_000_000, 40, 30),
    ('Thẩm tra thiết kế đường nối KCN Bình Minh (DEMO)', 'owner_binh_minh', 'crm.stage_lead1', 650_000_000, 20, 60),
    ('Giám sát khảo sát tuyến KCN giai đoạn 2 (DEMO)', 'owner_binh_minh', 'crm.stage_lead2', 1_100_000_000, 35, 40),
    ('Lập báo cáo nghiên cứu khả thi nút giao Đồi Cát (DEMO)', 'owner_doi_cat', 'crm.stage_lead3', 2_300_000_000, 55, 20),
    ('Khảo sát địa hình tuyến tránh thị trấn Gò Mây (DEMO)', 'owner_go_may', 'crm.stage_lead1', 1_600_000_000, 15, 75),
    ('Thiết kế cải tạo cầu yếu Kênh Đào (DEMO)', 'owner_go_may', 'crm.stage_lead2', 3_400_000_000, 30, 50),
    ('Tư vấn giám sát tuyến đê kết hợp đường (DEMO)', 'owner_ven_bien', 'crm.stage_lead3', 5_000_000_000, 50, 25),
    ('Kiểm định cầu cũ tỉnh lộ 9 (DEMO)', 'owner_doi_cat', 'crm.stage_lead4', 780_000_000, 100, -10),
    ('Khảo sát thủy văn cầu Bến Lở (DEMO)', 'owner_ven_bien', 'crm.stage_lead1', 450_000_000, 10, 90),
]


def set_password(user, password):
    """Hash and store a password like the base inverse, without the mail module's
    "password changed" e-mail: demo accounts have no mailbox and the demo sends no mail."""
    user.ensure_one()
    user._set_encrypted_password(user.id, user._crypt_context().hash(password))
    user.invalidate_recordset(['password'])


def seed(env, passwords=None):
    """Create or complete the demo dataset in ``env`` (superuser, demo database only).

    :param passwords: optional ``{login: password}`` for :data:`ACTOR_LOGINS`;
        given passwords are (re)applied, other users never get one.
    :returns: dict of the main records, for tools and tests.
    """
    dbname = env.cr.dbname
    if not dbname.startswith(DB_PREFIX):
        raise RuntimeError(f'Refusing to seed demo data into {dbname!r}: only {DB_PREFIX}* databases are allowed.')
    if not env.su:
        message = 'The demo seed runs as superuser while preparing fixtures.'
        raise RuntimeError(message)
    env = env(context=dict(env.context, **CREATE_CONTEXT))

    def ref(key):
        return env.ref(f'{SEED_MODULE}.{key}', raise_if_not_found=False)

    def bind(key, record):
        env['ir.model.data'].create({
            'module': SEED_MODULE, 'name': key, 'model': record._name, 'res_id': record.id, 'noupdate': True,
        })
        return record

    def seeded(model, key, values):
        return ref(key) or bind(key, env[model].create(values))

    today = fields.Date.context_today(env['res.users'])
    company = env.company
    currency = env.ref('base.VND')
    currency.active = True
    if company.name != COMPANY_NAME or company.currency_id != currency:
        company.write({'name': COMPANY_NAME, 'currency_id': currency.id, 'country_id': env.ref('base.vn').id})
    vietnamese = bool(env['res.lang'].search([('code', '=', 'vi_VN')], limit=1))

    departments = {
        code: seeded('hr.department', f'department_{code.lower()}', {'name': name, 'tp_code': code, 'company_id': company.id})
        for code, name in DEPARTMENTS
    }
    partners = {
        key: seeded('res.partner', f'partner_{key}', {'name': name, 'is_company': True, 'country_id': env.ref('base.vn').id})
        for key, name in PARTNERS.items()
    }

    def user(key, login, name, groups, home=None):
        values = {
            'name': name, 'login': login, 'company_id': company.id, 'company_ids': [Command.set(company.ids)],
            'group_ids': [Command.set([env.ref(group).id for group in groups])], 'tz': 'Asia/Ho_Chi_Minh',
        }
        if vietnamese:
            values['lang'] = 'vi_VN'
        record = seeded('res.users', key, values)
        if home:
            record.action_id = env.ref(home).id
        return record

    staff_users, employees = {}, {}
    for key, name, department, job, has_user in STAFF:
        if has_user:
            staff_users[key] = user(f'user_{key}', f'nv.{key}.demo', name, ['base.group_user'])
        employees[key] = seeded('hr.employee', f'employee_{key}', {
            'name': name, 'department_id': departments[department].id, 'job_title': job, 'company_id': company.id,
            'user_id': staff_users[key].id if has_user else False,
        })

    dashboard = 'tp_demo_workspace.action_demo_dashboard'
    actors = {
        'lanhdao': user('actor_lanhdao', 'demo.lanhdao', 'Lãnh đạo xem toàn cảnh (DEMO)',
                        ['tp_demo_workspace.group_demo_business'], dashboard),
        'kysu': user('actor_kysu', 'demo.kysu', 'Kỹ sư phạm vi hạn chế (DEMO)',
                     ['tp_demo_workspace.group_demo_viewer'], dashboard),
        'drafter': user('actor_drafter', 'demo.lap-hd', 'Người lập hợp đồng (DEMO)', ['tp_core.group_user']),
        'reviewer': user('actor_reviewer', 'demo.ra-soat', 'Người rà soát thương mại (DEMO)', ['tp_core.group_user']),
    }
    for login, password in (passwords or {}).items():
        if login not in ACTOR_LOGINS:
            raise ValueError(f'Only demo actors get a password, not {login!r}.')
        set_password(env['res.users'].search([('login', '=', login)]), password)

    projects = {}
    for key, code, name, department, partner, manager, start, end in PROJECTS:
        projects[key] = seeded('project.project', f'project_{key}', {
            'name': name, 'tp_managed': True, 'tp_code': code, 'company_id': company.id,
            'tp_department_id': departments[department].id, 'partner_id': partners[partner].id,
            'user_id': staff_users[manager].id, 'privacy_visibility': 'employees',
            'date_start': start, 'date': end,
        })

    _seed_access(env, seeded, projects, actors)
    stages = {
        key: seeded('project.task.type', f'stage_{key}', {
            'name': name, 'sequence': index * 10, 'fold': fold, 'project_ids': [Command.set([p.id for p in projects.values()])],
        })
        for index, (key, name, fold) in enumerate(STAGES)
    }
    tags = {key: seeded('project.tags', f'tag_{key}', {'name': name}) for key, name in TAGS}
    for index, (project, name, stage, assignee, offset, tag_keys) in enumerate(TASKS, start=1):
        deadline = datetime.datetime.combine(today + datetime.timedelta(days=offset), datetime.time(3, 0))
        seeded('project.task', f'task_{index:02d}', {
            'name': name, 'project_id': projects[project].id, 'stage_id': stages[stage].id,
            'user_ids': [Command.set([staff_users[assignee].id] if assignee else [])],
            'date_deadline': fields.Datetime.to_string(deadline),
            'tag_ids': [Command.set([tags[tag].id for tag in tag_keys])],
            'state': '1_done' if stage == 'done' else '01_in_progress',
        })

    team = env.ref('sales_team.team_sales_department', raise_if_not_found=False)
    for index, (name, partner, stage, revenue, probability, offset) in enumerate(OPPORTUNITIES, start=1):
        seeded('crm.lead', f'opportunity_{index:02d}', {
            'name': name, 'type': 'opportunity', 'partner_id': partners[partner].id, 'stage_id': env.ref(stage).id,
            'expected_revenue': revenue, 'probability': probability, 'company_id': company.id,
            'user_id': staff_users['tri'].id, 'team_id': team.id if team else False,
            'date_deadline': today + datetime.timedelta(days=offset),
        })

    contracts = _seed_contracts(env, seeded, ref, bind, projects, partners, actors)
    return {'company': company, 'projects': projects, 'actors': actors, 'contracts': contracts,
            'departments': departments, 'staff': staff_users, 'employees': employees}


def _seed_access(env, seeded, projects, actors):
    """Assignments and grants. Only the overview actor and the workflow users hold financial.read."""
    reason = 'UI-DEMO-001: quyền trình diễn trên dữ liệu giả lập (DEMO).'
    for key, project in projects.items():
        department = project.tp_department_id
        seeded('tp.project.assignment', f'assignment_lanhdao_{key}',
               {'project_id': project.id, 'user_id': actors['lanhdao'].id, 'role': 'reader'})
        seeded('tp.project.grant', f'grant_lanhdao_read_{key}', {
            'project_id': project.id, 'user_id': actors['lanhdao'].id, 'capability': 'financial_read', 'reason': reason,
        })
        seeded('tp.project.assignment', f'assignment_drafter_{key}',
               {'project_id': project.id, 'user_id': actors['drafter'].id, 'role': 'coordinator'})
        seeded('tp.project.assignment', f'assignment_reviewer_{key}',
               {'project_id': project.id, 'user_id': actors['reviewer'].id, 'role': 'reader'})
        for capability in ('contract_draft_edit', 'contract_submit', 'financial_draft_edit'):
            seeded('tp.project.grant', f'grant_drafter_{capability}_{key}', {
                'project_id': project.id, 'user_id': actors['drafter'].id, 'capability': capability,
                'department_id': department.id, 'reason': reason,
            })
        seeded('tp.project.grant', f'grant_reviewer_commercial_{key}', {
            'project_id': project.id, 'user_id': actors['reviewer'].id, 'capability': 'contract_review_commercial',
            'department_id': department.id, 'reason': reason,
        })
        for actor in ('drafter', 'reviewer'):
            seeded('tp.project.grant', f'grant_{actor}_read_{key}', {
                'project_id': project.id, 'user_id': actors[actor].id, 'capability': 'financial_read', 'reason': reason,
            })
    # The restricted actor sees one project and holds no financial grant.
    seeded('tp.project.assignment', 'assignment_kysu_duong',
           {'project_id': projects['duong'].id, 'user_id': actors['kysu'].id, 'role': 'reader'})


def _seed_contracts(env, seeded, ref, bind, projects, partners, actors):
    Workflow = env['tp.contract.workflow']
    drafter = Workflow.with_user(actors['drafter'])
    reviewer = Workflow.with_user(actors['reviewer'])

    def amount(value, state='confirmed'):
        return {'state': state, 'value': value, 'tax_basis': 'excluding_tax'}

    def latest(contract):
        return contract.revision_ids.sorted('sequence')[-1:]

    def create(key, payload):
        contract = ref(key)
        if not contract:
            result = drafter._tp_run('create_contract', payload, key=f'demo-ui001-{key}-create')
            contract = bind(key, result['contract'].sudo())
        return contract

    def submit(contract, key):
        revision = latest(contract)
        if revision.review_state == 'draft' and not revision.submission_ids:
            drafter._tp_run('submit_review', {'expected_version': contract.aggregate_version, 'reviewer_id': actors['reviewer'].id},
                            key=f'demo-ui001-{key}-submit', contract_id=contract.id, revision_id=revision.id)

    # C1: historical owner contract, recorded as signed and effective before the review workflow existed.
    legacy = ref('contract_cau_owner')
    if not legacy:
        legacy = bind('contract_cau_owner', env['tp.contract'].create({
            'code': 'DEMO-HD-CAU-01', 'name': 'Hợp đồng tư vấn khảo sát, thiết kế cầu Sông Xanh (DEMO)',
            'project_id': projects['cau'].id, 'partner_id': partners['owner_song_xanh'].id,
            'contract_type': 'owner', 'currency_id': env.ref('base.VND').id, 'legacy_unverified': True,
        }))
        original = env['tp.contract.revision'].create({
            'contract_id': legacy.id, 'sequence': 0, 'revision_kind': 'original', 'name': 'Hợp đồng gốc',
            'reference': 'DEMO/HĐTV-01', 'review_state': 'review_complete', 'legacy_unverified': True,
            'signature_status': 'signed_recorded', 'signed_date': '2026-08-20',
            'effectivity_status': 'effective_recorded', 'effective_date': '2026-09-01',
        })
        for scope_key, name, value in (('KS', 'Khảo sát địa hình, địa chất (DEMO)', 1_250_000_000),
                                       ('TK', 'Thiết kế bản vẽ thi công (DEMO)', 1_850_000_000)):
            line = env['tp.contract.line'].create({
                'revision_id': original.id, 'scope_key': scope_key, 'name': name, 'change_kind': 'original',
            })
            env['tp.contract.line.amount'].create({
                'line_id': line.id, 'amount_state': 'confirmed', 'amount': value, 'tax_basis': 'excluding_tax',
            })
        legacy.lifecycle_state = 'effective'
        env['tp.contract.document'].create([
            {'contract_id': legacy.id, 'revision_id': original.id, 'name': 'Hợp đồng đã ký – bản giả lập (DEMO)',
             'document_kind': 'signed_contract', 'confidentiality': 'financial',
             'file': BinaryBytes('Tệp giả lập cho UI-DEMO-001. Không phải hợp đồng thật.'.encode()),
             'file_name': 'hop-dong-da-ky-gia-lap-DEMO.txt'},
            {'contract_id': legacy.id, 'name': 'Đề cương nhiệm vụ khảo sát (DEMO)', 'document_kind': 'technical_scope',
             'confidentiality': 'general',
             'file': BinaryBytes('Đề cương giả lập cho UI-DEMO-001. Không phải hồ sơ thật.'.encode()),
             'file_name': 'de-cuong-gia-lap-DEMO.txt'},
        ])

    # C2: subcontract submitted, then returned by the commercial reviewer with a reason.
    subcontract = create('contract_cau_drilling', {
        'project_id': projects['cau'].id, 'code': 'DEMO-HD-CAU-02', 'name': 'Hợp đồng thầu phụ khoan địa chất (DEMO)',
        'contract_type': 'subcontractor', 'currency': 'VND', 'partner_id': partners['sub_drilling'].id,
        'revision': {'name': 'Hợp đồng gốc', 'reference': 'DEMO/HĐTP-02'},
        'lines': [
            {'scope_key': 'KHOAN', 'name': 'Khoan địa chất 6 lỗ tại mố, trụ (DEMO)', 'amount': amount('420000000')},
            {'scope_key': 'TN', 'name': 'Thí nghiệm mẫu đất trong phòng (DEMO)', 'amount': amount('85000000')},
        ],
    })
    submit(subcontract, 'contract_cau_drilling')
    revision = latest(subcontract)
    if revision.review_state == 'in_review':
        reviewer._tp_run('return_review', {
            'expected_version': subcontract.aggregate_version,
            'reason': 'Thiếu căn cứ đơn giá khoan; đề nghị bổ sung báo giá so sánh (DEMO).',
            'issues': [{'scope_key': 'KHOAN', 'note': 'Đơn giá khoan cao hơn định mức tham chiếu giả lập (DEMO).'}],
        }, key='demo-ui001-contract_cau_drilling-return', contract_id=subcontract.id, revision_id=revision.id)

    # C3: owner contract of the restricted actor's project, with a general and a financial file, now in review.
    road = create('contract_duong_owner', {
        'project_id': projects['duong'].id, 'code': 'DEMO-HD-DUONG-01',
        'name': 'Hợp đồng tư vấn thiết kế đường nối KCN Bình Minh (DEMO)', 'contract_type': 'owner', 'currency': 'VND',
        'partner_id': partners['owner_binh_minh'].id, 'revision': {'name': 'Hợp đồng gốc', 'reference': 'DEMO/HĐTV-02'},
        'lines': [
            {'scope_key': 'KS', 'name': 'Khảo sát hiện trạng, thủy văn (DEMO)', 'amount': amount('640000000')},
            {'scope_key': 'TK', 'name': 'Thiết kế cơ sở và bản vẽ thi công (DEMO)', 'amount': amount('1380000000')},
        ],
    })
    revision = latest(road)
    if not ref('document_duong_scope'):
        bind('document_duong_scope', env['tp.contract.document'].create({
            'contract_id': road.id, 'revision_id': revision.id, 'name': 'Phạm vi công việc kỹ thuật tuyến đường (DEMO)',
            'document_kind': 'technical_scope', 'confidentiality': 'general',
            'file': BinaryBytes('Phạm vi kỹ thuật giả lập cho UI-DEMO-001.'.encode()), 'file_name': 'pham-vi-ky-thuat-DEMO.txt',
        }))
        bind('document_duong_estimate', env['tp.contract.document'].create({
            'contract_id': road.id, 'revision_id': revision.id, 'name': 'Bảng giá trị hợp đồng dự thảo (DEMO)',
            'document_kind': 'other', 'confidentiality': 'financial',
            'file': BinaryBytes('Bảng giá trị giả lập cho UI-DEMO-001; vùng tài chính.'.encode()),
            'file_name': 'bang-gia-tri-du-thao-DEMO.txt',
        }))
    submit(road, 'contract_duong_owner')

    # C4: owner contract still being drafted; one amount is not confirmed yet.
    junction = create('contract_nut_owner', {
        'project_id': projects['nut'].id, 'code': 'DEMO-HD-NUT-01',
        'name': 'Hợp đồng khảo sát, lập phương án nút giao Đồi Cát (DEMO)', 'contract_type': 'owner', 'currency': 'VND',
        'partner_id': partners['owner_doi_cat'].id, 'revision': {'name': 'Dự thảo hợp đồng'},
        'lines': [
            {'scope_key': 'KS', 'name': 'Đo vẽ địa hình nút giao (DEMO)', 'amount': amount('310000000')},
            {'scope_key': 'PA', 'name': 'Lập phương án tổ chức giao thông (DEMO)', 'amount': amount(None, 'unconfirmed')},
        ],
    })
    return {'legacy': legacy, 'returned': subcontract, 'in_review': road, 'draft': junction}
