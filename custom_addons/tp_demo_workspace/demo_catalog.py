"""Static catalogue of the UI-DEMO-001 workspace.

Every value here is synthetic and marked DEMO. Illustrative datasets stay on
the server: the projection in ``models/tp_demo_workspace.py`` returns only the
rows of projects the viewer can read, and amounts only with ``financial_read``.
Nothing in this module is a business rule of Tan Phat.
"""

PROJECT_CODES = ('DEMO-CAU-01', 'DEMO-DUONG-02', 'DEMO-NUT-03')
PROJECT_DOMAIN = [('tp_managed', '=', True), ('tp_code', '=like', 'DEMO-%')]

ILLUSTRATIVE_LABEL = 'Minh họa định hướng'
ENVIRONMENT_LABEL = 'Dữ liệu trình diễn'

# Modules shown on the dashboard map. ``nature`` is real (Odoo records),
# illustrative (backend sample rows) or mixed (both, labelled per column).
MODULES = {
    'projects': {
        'name': 'TP Projects', 'purpose': 'Quản lý dự án cầu đường', 'nature': 'real',
        'source': 'project.project · tp_project', 'action': 'tp_demo_workspace.action_demo_projects',
    },
    'survey': {
        'name': 'TP Survey', 'purpose': 'Khảo sát hiện trường', 'nature': 'illustrative',
        'source': 'Dữ liệu mẫu do backend demo trả', 'action': 'tp_demo_workspace.action_demo_survey',
    },
    'design': {
        'name': 'TP Design', 'purpose': 'Hồ sơ thiết kế', 'nature': 'illustrative',
        'source': 'Dữ liệu mẫu do backend demo trả', 'action': 'tp_demo_workspace.action_demo_design',
    },
    'tasks': {
        'name': 'TP Tasks', 'purpose': 'Tiến độ, giao việc', 'nature': 'real',
        'source': 'project.task', 'action': 'tp_demo_workspace.action_demo_tasks',
    },
    'contracts': {
        'name': 'TP Contracts', 'purpose': 'Hợp đồng và rà soát nội bộ', 'nature': 'real',
        'source': 'tp.contract · tp.contract.revision', 'action': 'tp_demo_workspace.action_demo_contracts',
    },
    'documents': {
        'name': 'TP Documents', 'purpose': 'Văn bản, hồ sơ', 'nature': 'real',
        'source': 'tp.contract.document', 'action': 'tp_demo_workspace.action_demo_documents',
    },
    'hr': {
        'name': 'TP HR', 'purpose': 'Nhân sự', 'nature': 'mixed',
        'source': 'hr.employee.public · phân bổ minh họa', 'action': 'tp_demo_workspace.action_demo_employees',
    },
    'finance': {
        'name': 'TP Finance', 'purpose': 'Tài chính, chi phí', 'nature': 'mixed',
        'source': 'tp.contract.line.amount · số minh họa', 'action': 'tp_demo_workspace.action_demo_finance',
    },
    'crm': {
        'name': 'Cơ hội (CRM)', 'purpose': 'Phễu cơ hội kinh doanh', 'nature': 'real',
        'source': 'crm.lead', 'action': 'tp_demo_workspace.action_demo_crm', 'business': True,
    },
    'bid': {
        'name': 'Dự thầu', 'purpose': 'Gói thầu Tấn Phát tham gia', 'nature': 'illustrative',
        'source': 'Dữ liệu mẫu do backend demo trả', 'action': 'tp_demo_workspace.action_demo_bid', 'business': True,
    },
    'request': {
        'name': 'Đề nghị BASE', 'purpose': 'Hồ sơ đề nghị gửi BASE duyệt', 'nature': 'illustrative',
        'source': 'Dữ liệu mẫu do backend demo trả', 'action': 'tp_demo_workspace.action_demo_request',
    },
}

LANES = [
    {'key': 'delivery', 'label': 'Thực hiện dự án', 'modules': ['projects', 'survey', 'design', 'tasks']},
    {'key': 'records', 'label': 'Hợp đồng và hồ sơ', 'modules': ['contracts', 'documents']},
    {'key': 'business', 'label': 'Kinh doanh và đề nghị', 'modules': ['crm', 'bid', 'request']},
    {'key': 'resources', 'label': 'Nguồn lực', 'modules': ['hr', 'finance']},
]

# Layout lenses only reorder lanes; they never change rights.
LENSES = [
    {'key': 'executive', 'label': 'Điều hành', 'order': ['delivery', 'records', 'business', 'resources']},
    {'key': 'delivery', 'label': 'Dự án và kỹ thuật', 'order': ['delivery', 'records', 'resources', 'business']},
    {'key': 'business', 'label': 'Kinh doanh', 'order': ['business', 'delivery', 'records', 'resources'], 'business': True},
    {'key': 'finance', 'label': 'Tài chính', 'order': ['resources', 'records', 'delivery', 'business']},
]


def _row(key, project, name, status, columns, sections, **extra):
    return {'key': key, 'project': project, 'name': name, 'status': status, 'columns': columns, 'sections': sections, **extra}


SCREENS = {
    'survey': {
        'module': 'TP Survey',
        'title': 'Khảo sát hiện trường',
        'purpose': 'Kế hoạch khảo sát, vị trí và hạng mục, nhân sự và thiết bị, nhật ký và kết quả theo dự án.',
        'columns': [('kind', 'Loại khảo sát'), ('period', 'Thời gian'), ('lead', 'Tổ trưởng')],
        'out_of_scope': [
            'Không dùng module survey (bảng hỏi) của Odoo cho khảo sát hiện trường.',
            'Chưa có model, quyền ghi hay nghiệm thu kết quả khảo sát.',
        ],
    },
    'design': {
        'module': 'TP Design',
        'title': 'Hồ sơ thiết kế',
        'purpose': 'Bộ bản vẽ, các lần sửa đổi, ý kiến kiểm tra và gói bàn giao theo dự án.',
        'columns': [('discipline', 'Bộ môn'), ('revision', 'Phiên bản'), ('owner', 'Chủ trì')],
        'out_of_scope': [
            'Không có phê duyệt, ký số hay đóng dấu bản vẽ.',
            'Chưa lưu tệp bản vẽ thật; danh mục chỉ để minh họa cấu trúc hồ sơ.',
        ],
    },
    'request': {
        'module': 'Đề nghị BASE',
        'title': 'Đề nghị gửi BASE',
        'purpose': 'Hồ sơ đề nghị được rà soát trong TANPHAT ONE rồi gửi BASE; BASE vẫn là nơi phê duyệt chính thức.',
        'columns': [('group', 'Nhóm BASE'), ('requester', 'Người đề nghị'), ('amount', 'Số tiền đề nghị')],
        'out_of_scope': [
            'Không có nút duyệt: kết quả chỉ được ghi nhận từ BASE.',
            'Không có connector, chữ ký, chi tiền hay liên kết kèm token tới BASE.',
            'Các bước là luồng đề xuất (Proposed-TP), không phải state thật của BASE.',
        ],
    },
    'bid': {
        'module': 'Dự thầu',
        'title': 'Gói thầu đang theo dõi',
        'purpose': 'Gói thầu Tấn Phát tham gia với vai trò nhà thầu hoặc tư vấn: hạn nộp, hồ sơ, liên danh và kết quả dự kiến.',
        'columns': [('inviter', 'Bên mời thầu'), ('role', 'Vai trò Tấn Phát'), ('deadline', 'Hạn nộp')],
        'out_of_scope': [
            'Tấn Phát là bên dự thầu, không phải chủ đầu tư; không dùng purchase_requisition.',
            'Không hiển thị giá dự thầu: quyền xem giá cho Bid chưa được thiết kế.',
            'Không liên kết tự động cơ hội → gói thầu → hợp đồng.',
        ],
    },
    'staffing': {
        'module': 'TP HR',
        'title': 'Năng lực và phân bổ nhân sự',
        'purpose': 'Ai đang được phân bổ vào dự án nào, với vai trò và chứng chỉ gì.',
        'columns': [('role', 'Vai trò dự án'), ('department', 'Phòng ban'), ('allocation', 'Phân bổ')],
        'out_of_scope': [
            'Không có lương, chấm công hay dữ liệu cá nhân nhạy cảm.',
            'Phân bổ chưa nối với TP Tasks hay timesheet.',
        ],
    },
}

ROWS = {
    'survey': [
        _row('KS-CAU01-01', 'DEMO-CAU-01', 'Khảo sát địa hình tuyến cầu và đường dẫn (DEMO)',
             ('in_progress', 'Đang thực hiện'),
             {'kind': 'Địa hình', 'period': '05/10 – 15/11/2026', 'lead': 'Trần Minh Khoa (DEMO)'},
             [
                 {'title': 'Vị trí và hạng mục', 'lines': ['Km0+000 – Km1+250 tuyến chính', 'Mố M1, M2; trụ T1 – T4', 'Bình đồ tỷ lệ 1/500']},
                 {'title': 'Nhân sự và thiết bị', 'lines': ['Tổ khảo sát 1: 4 người', 'Máy toàn đạc điện tử, máy GNSS RTK (giả lập)']},
                 {'title': 'Nhật ký', 'timeline': [('06/10/2026', 'Lập lưới khống chế mặt bằng'), ('20/10/2026', 'Đo bình đồ đoạn đường dẫn bờ trái')]},
                 {'title': 'Kết quả', 'lines': ['Chưa có kết quả chính thức; số liệu đo đang xử lý.']},
             ]),
        _row('KS-CAU01-02', 'DEMO-CAU-01', 'Khoan khảo sát địa chất mố, trụ cầu (DEMO)',
             ('planned', 'Kế hoạch'),
             {'kind': 'Địa chất', 'period': '18/11 – 20/12/2026', 'lead': 'Vũ Đức Long (DEMO)'},
             [
                 {'title': 'Vị trí và hạng mục', 'lines': ['6 lỗ khoan tại M1, T1 – T4, M2', 'Thí nghiệm SPT theo chiều sâu']},
                 {'title': 'Nhân sự và thiết bị', 'lines': ['Tổ khoan 2: 5 người', 'Máy khoan XY-1 (giả lập)']},
                 {'title': 'Nhật ký', 'timeline': [('28/10/2026', 'Lập phương án khoan, chờ mặt bằng')]},
                 {'title': 'Kết quả', 'lines': ['Chưa thực hiện.']},
             ]),
        _row('KS-DUONG02-01', 'DEMO-DUONG-02', 'Khảo sát hiện trạng tuyến đường nối KCN (DEMO)',
             ('reported', 'Đã có kết quả sơ bộ'),
             {'kind': 'Hiện trạng và thủy văn', 'period': '01/09 – 30/09/2026', 'lead': 'Hoàng Văn Sơn (DEMO)'},
             [
                 {'title': 'Vị trí và hạng mục', 'lines': ['Km0+000 – Km3+400', '3 cống ngang đường hiện hữu']},
                 {'title': 'Nhân sự và thiết bị', 'lines': ['Tổ khảo sát 2: 3 người', 'Máy thủy bình, thước đo độ bằng phẳng (giả lập)']},
                 {'title': 'Nhật ký', 'timeline': [('05/09/2026', 'Đo hiện trạng mặt đường'), ('22/09/2026', 'Điều tra mực nước lũ tại cống C2')]},
                 {'title': 'Kết quả', 'lines': ['Báo cáo sơ bộ đã gửi phòng Thiết kế (giả lập).']},
             ]),
        _row('KS-NUT03-01', 'DEMO-NUT-03', 'Đo vẽ địa hình nút giao Đồi Cát (DEMO)',
             ('in_progress', 'Đang thực hiện'),
             {'kind': 'Địa hình', 'period': '15/10 – 30/11/2026', 'lead': 'Trần Minh Khoa (DEMO)'},
             [
                 {'title': 'Vị trí và hạng mục', 'lines': ['Phạm vi nút giao 450 m × 300 m', 'Các nhánh rẽ N1 – N4']},
                 {'title': 'Nhân sự và thiết bị', 'lines': ['Tổ khảo sát 1: 4 người', 'Máy bay không người lái chụp ảnh (giả lập)']},
                 {'title': 'Nhật ký', 'timeline': [('16/10/2026', 'Bay chụp toàn khu vực'), ('25/10/2026', 'Đo bù các điểm khuất')]},
                 {'title': 'Kết quả', 'lines': ['Đang dựng mô hình số địa hình.']},
             ]),
        _row('KS-NUT03-02', 'DEMO-NUT-03', 'Khảo sát địa chất nền đường nhánh N2 (DEMO)',
             ('planned', 'Kế hoạch'),
             {'kind': 'Địa chất', 'period': '01/12 – 20/12/2026', 'lead': 'Vũ Đức Long (DEMO)'},
             [
                 {'title': 'Vị trí và hạng mục', 'lines': ['4 lỗ khoan, 2 hố đào thăm dò']},
                 {'title': 'Nhân sự và thiết bị', 'lines': ['Tổ khoan 2: 5 người']},
                 {'title': 'Nhật ký', 'timeline': []},
                 {'title': 'Kết quả', 'lines': ['Chưa thực hiện.']},
             ]),
    ],
    'design': [
        _row('TK-CAU01-01', 'DEMO-CAU-01', 'Bản vẽ bố trí chung cầu Sông Xanh (DEMO)',
             ('in_check', 'Đang kiểm tra nội bộ'),
             {'discipline': 'Cầu', 'revision': 'B', 'owner': 'Nguyễn Hải Nam (DEMO)'},
             [
                 {'title': 'Các lần sửa đổi', 'timeline': [('02/10/2026', 'A — phát hành nội bộ'), ('24/10/2026', 'B — điều chỉnh khẩu độ nhịp biên')]},
                 {'title': 'Ý kiến kiểm tra', 'lines': ['Kiểm tra cao độ đáy dầm so với mực nước thông thuyền (giả lập).']},
                 {'title': 'Gói bàn giao', 'lines': ['Chưa đưa vào gói bàn giao.']},
             ]),
        _row('TK-CAU01-02', 'DEMO-CAU-01', 'Thuyết minh thiết kế kết cấu nhịp (DEMO)',
             ('draft', 'Đang soạn'),
             {'discipline': 'Kết cấu', 'revision': 'A', 'owner': 'Phan Anh Tuấn (DEMO)'},
             [
                 {'title': 'Các lần sửa đổi', 'timeline': [('15/10/2026', 'A — bản soạn thảo')]},
                 {'title': 'Ý kiến kiểm tra', 'lines': ['Chưa gửi kiểm tra.']},
                 {'title': 'Gói bàn giao', 'lines': ['—']},
             ]),
        _row('TK-DUONG02-01', 'DEMO-DUONG-02', 'Bình đồ, trắc dọc tuyến đường nối KCN (DEMO)',
             ('commented', 'Có ý kiến cần sửa'),
             {'discipline': 'Đường', 'revision': 'C', 'owner': 'Bùi Thị Lan (DEMO)'},
             [
                 {'title': 'Các lần sửa đổi', 'timeline': [('10/09/2026', 'A'), ('01/10/2026', 'B — chỉnh đường cong nằm'), ('21/10/2026', 'C — theo ý kiến chủ đầu tư')]},
                 {'title': 'Ý kiến kiểm tra', 'lines': ['Bổ sung bố trí siêu cao đoạn Km1+200 (giả lập).', 'Đối chiếu cao độ khống chế với cống C2.']},
                 {'title': 'Gói bàn giao', 'lines': ['Dự kiến gói BVTC đợt 1.']},
             ]),
        _row('TK-DUONG02-02', 'DEMO-DUONG-02', 'Thiết kế thoát nước dọc tuyến (DEMO)',
             ('handover_ready', 'Sẵn sàng bàn giao'),
             {'discipline': 'Thoát nước', 'revision': 'B', 'owner': 'Đặng Thùy Linh (DEMO)'},
             [
                 {'title': 'Các lần sửa đổi', 'timeline': [('20/09/2026', 'A'), ('12/10/2026', 'B — tăng khẩu độ cống C2')]},
                 {'title': 'Ý kiến kiểm tra', 'lines': ['Đã đóng ý kiến kiểm tra nội bộ (giả lập).']},
                 {'title': 'Gói bàn giao', 'lines': ['Gói BVTC đợt 1 — chờ phát hành.']},
             ]),
        _row('TK-NUT03-01', 'DEMO-NUT-03', 'Phương án tổ chức nút giao (DEMO)',
             ('draft', 'Đang soạn'),
             {'discipline': 'Giao thông', 'revision': 'A', 'owner': 'Bùi Thị Lan (DEMO)'},
             [
                 {'title': 'Các lần sửa đổi', 'timeline': [('27/10/2026', 'A — hai phương án so sánh')]},
                 {'title': 'Ý kiến kiểm tra', 'lines': ['Chờ số liệu địa hình.']},
                 {'title': 'Gói bàn giao', 'lines': ['—']},
             ]),
    ],
    'request': [
        _row('RQ-DEMO-001', 'DEMO-CAU-01', 'Tạm ứng chi phí khảo sát hiện trường đợt 1 (DEMO)',
             ('awaiting_base', 'Chờ kết quả BASE'),
             {'group': 'Đề xuất tạm ứng, thanh toán', 'requester': 'Trần Minh Khoa (DEMO)'},
             [], amount='45000000',
             steps=[('Soạn hồ sơ', 'done'), ('Rà soát tài chính', 'done'), ('Sẵn sàng gửi BASE', 'done'),
                    ('Chờ kết quả BASE', 'current'), ('Ghi nhận kết quả BASE', 'todo'), ('Đối chiếu bằng chứng', 'todo')]),
        _row('RQ-DEMO-002', 'DEMO-CAU-01', 'Công tác hiện trường khoan địa chất (DEMO)',
             ('draft', 'Đang soạn'),
             {'group': 'Công tác', 'requester': 'Vũ Đức Long (DEMO)'},
             [], steps=[('Soạn hồ sơ', 'current'), ('Sẵn sàng gửi BASE', 'todo'), ('Chờ kết quả BASE', 'todo'), ('Ghi nhận kết quả BASE', 'todo')]),
        _row('RQ-DEMO-003', 'DEMO-DUONG-02', 'Thanh toán thuê thiết bị đo thủy văn (DEMO)',
             ('returned', 'Trả lại để sửa'),
             {'group': 'Đề xuất tạm ứng, thanh toán', 'requester': 'Hoàng Văn Sơn (DEMO)'},
             [{'title': 'Lý do trả lại', 'lines': ['Thiếu biên bản bàn giao thiết bị (giả lập).']}], amount='18500000',
             steps=[('Soạn hồ sơ', 'done'), ('Rà soát tài chính', 'returned'), ('Sửa và gửi lại', 'current'),
                    ('Chờ kết quả BASE', 'todo'), ('Ghi nhận kết quả BASE', 'todo')]),
        _row('RQ-DEMO-004', 'DEMO-DUONG-02', 'Mượn xe đi hiện trường tuyến KCN (DEMO)',
             ('declared', 'BASE đã ghi nhận chấp nhận'),
             {'group': 'Mượn xe', 'requester': 'Bùi Thị Lan (DEMO)'},
             [{'title': 'Ghi chú', 'lines': ['“Chấp nhận” trên BASE không đồng nghĩa đã ký, hiệu lực hay đã chi tiền.']}],
             steps=[('Soạn hồ sơ', 'done'), ('Sẵn sàng gửi BASE', 'done'), ('Chờ kết quả BASE', 'done'),
                    ('Ghi nhận kết quả BASE', 'done'), ('Đối chiếu bằng chứng', 'current')]),
        _row('RQ-DEMO-005', 'DEMO-NUT-03', 'Phiếu giao việc đo bù điểm khuất (DEMO)',
             ('ready_for_base', 'Sẵn sàng gửi BASE'),
             {'group': 'Phiếu giao việc', 'requester': 'Trần Minh Khoa (DEMO)'},
             [], steps=[('Soạn hồ sơ', 'done'), ('Sẵn sàng gửi BASE', 'current'), ('Chờ kết quả BASE', 'todo'), ('Ghi nhận kết quả BASE', 'todo')]),
        _row('RQ-DEMO-006', 'DEMO-NUT-03', 'Tạm ứng thuê máy bay chụp ảnh (DEMO)',
             ('finance_review', 'Đang rà soát tài chính'),
             {'group': 'Đề xuất tạm ứng, thanh toán', 'requester': 'Trần Minh Khoa (DEMO)'},
             [], amount='32000000',
             steps=[('Soạn hồ sơ', 'done'), ('Rà soát tài chính', 'current'), ('Sẵn sàng gửi BASE', 'todo'),
                    ('Chờ kết quả BASE', 'todo'), ('Ghi nhận kết quả BASE', 'todo')]),
    ],
    'bid': [
        _row('BID-DEMO-01', None, 'TV-03: Tư vấn khảo sát, thiết kế BVTC cầu Sông Xanh 2 (DEMO)',
             ('preparing', 'Đang chuẩn bị hồ sơ'),
             {'inviter': 'Ban Quản lý dự án Giao thông Tỉnh Mẫu (DEMO)', 'role': 'Nhà thầu tư vấn độc lập', 'deadline': '20/11/2026'},
             [
                 {'title': 'Hồ sơ dự thầu', 'lines': ['Năng lực, kinh nghiệm: đang tổng hợp', 'Đề xuất kỹ thuật: bản thảo', 'Đề xuất tài chính: thuộc quyền tài chính, không hiển thị trong demo']},
                 {'title': 'Liên danh', 'lines': ['Không liên danh']},
                 {'title': 'Kết quả dự kiến', 'lines': ['Bên mời thầu dự kiến công bố trong 12/2026']},
             ]),
        _row('BID-DEMO-02', None, 'TV-07: Tư vấn thiết kế cải tạo nút giao Đồi Cát mở rộng (DEMO)',
             ('submitted', 'Đã nộp, chờ mở thầu'),
             {'inviter': 'Ban Quản lý dự án Huyện Đồi Cát (DEMO)', 'role': 'Thành viên liên danh', 'deadline': '25/10/2026'},
             [
                 {'title': 'Hồ sơ dự thầu', 'lines': ['Đã nộp đủ thành phần theo danh mục (giả lập)']},
                 {'title': 'Liên danh', 'lines': ['Liên danh với Công ty Tư vấn Cầu Đường Mẫu (DEMO)', 'Tấn Phát phụ trách phần khảo sát']},
                 {'title': 'Kết quả dự kiến', 'lines': ['Chờ mở thầu']},
             ]),
        _row('BID-DEMO-03', None, 'KS-11: Khảo sát địa chất tuyến tránh Đông Mẫu (DEMO)',
             ('watching', 'Đang theo dõi thông báo'),
             {'inviter': 'Công ty Hạ tầng Mẫu Sông Xanh (DEMO)', 'role': 'Nhà thầu khảo sát', 'deadline': '15/12/2026'},
             [
                 {'title': 'Hồ sơ dự thầu', 'lines': ['Chưa mua hồ sơ mời thầu']},
                 {'title': 'Liên danh', 'lines': ['Chưa xác định']},
                 {'title': 'Kết quả dự kiến', 'lines': ['Quyết định tham gia trước 20/11/2026']},
             ]),
        _row('BID-DEMO-04', None, 'TV-02: Thẩm tra thiết kế đường gom KCN Mẫu (DEMO)',
             ('lost', 'Không trúng thầu'),
             {'inviter': 'Công ty Hạ tầng Mẫu Sông Xanh (DEMO)', 'role': 'Nhà thầu tư vấn độc lập', 'deadline': '10/08/2026'},
             [
                 {'title': 'Hồ sơ dự thầu', 'lines': ['Đã nộp']},
                 {'title': 'Liên danh', 'lines': ['Không liên danh']},
                 {'title': 'Kết quả dự kiến', 'lines': ['Đã công bố: không trúng (giả lập); lưu bài học kinh nghiệm']},
             ]),
    ],
    'staffing': [
        _row('PB-CAU01-01', 'DEMO-CAU-01', 'Nguyễn Hải Nam (DEMO)', ('allocated', 'Đã phân bổ'),
             {'role': 'Chủ nhiệm thiết kế', 'department': 'Phòng Thiết kế cầu đường (DEMO)', 'allocation': '60% · 10/2026 – 03/2027'},
             [{'title': 'Chứng chỉ', 'lines': ['Chứng chỉ hành nghề thiết kế cầu hạng II (giả lập)']}]),
        _row('PB-CAU01-02', 'DEMO-CAU-01', 'Phan Anh Tuấn (DEMO)', ('allocated', 'Đã phân bổ'),
             {'role': 'Kỹ sư kết cấu', 'department': 'Phòng Thiết kế cầu đường (DEMO)', 'allocation': '80% · 10/2026 – 01/2027'},
             [{'title': 'Chứng chỉ', 'lines': ['Chứng chỉ hành nghề thiết kế kết cấu hạng III (giả lập)']}]),
        _row('PB-CAU01-03', 'DEMO-CAU-01', 'Trần Minh Khoa (DEMO)', ('allocated', 'Đã phân bổ'),
             {'role': 'Tổ trưởng khảo sát địa hình', 'department': 'Phòng Khảo sát (DEMO)', 'allocation': '50% · 10/2026 – 11/2026'},
             [{'title': 'Chứng chỉ', 'lines': ['Chứng chỉ hành nghề khảo sát địa hình hạng II (giả lập)']}]),
        _row('PB-DUONG02-01', 'DEMO-DUONG-02', 'Bùi Thị Lan (DEMO)', ('allocated', 'Đã phân bổ'),
             {'role': 'Chủ trì thiết kế đường', 'department': 'Phòng Thiết kế cầu đường (DEMO)', 'allocation': '70% · 09/2026 – 12/2026'},
             [{'title': 'Chứng chỉ', 'lines': ['Chứng chỉ hành nghề thiết kế đường hạng II (giả lập)']}]),
        _row('PB-DUONG02-02', 'DEMO-DUONG-02', 'Đặng Thùy Linh (DEMO)', ('allocated', 'Đã phân bổ'),
             {'role': 'Kỹ sư thoát nước', 'department': 'Phòng Thiết kế cầu đường (DEMO)', 'allocation': '40% · 09/2026 – 11/2026'},
             [{'title': 'Chứng chỉ', 'lines': ['Chưa có chứng chỉ hành nghề — cần người ký thay (giả lập)']}]),
        _row('PB-DUONG02-03', 'DEMO-DUONG-02', 'Hoàng Văn Sơn (DEMO)', ('released', 'Đã kết thúc phân bổ'),
             {'role': 'Kỹ thuật viên khảo sát', 'department': 'Phòng Khảo sát (DEMO)', 'allocation': '100% · 09/2026'},
             [{'title': 'Chứng chỉ', 'lines': ['—']}]),
        _row('PB-NUT03-01', 'DEMO-NUT-03', 'Vũ Đức Long (DEMO)', ('proposed', 'Đề xuất phân bổ'),
             {'role': 'Chủ trì khảo sát địa chất', 'department': 'Phòng Khảo sát (DEMO)', 'allocation': '50% · 12/2026'},
             [{'title': 'Chứng chỉ', 'lines': ['Chứng chỉ hành nghề khảo sát địa chất hạng II (giả lập)']}]),
        _row('PB-NUT03-02', 'DEMO-NUT-03', 'Trần Minh Khoa (DEMO)', ('allocated', 'Đã phân bổ'),
             {'role': 'Tổ trưởng khảo sát địa hình', 'department': 'Phòng Khảo sát (DEMO)', 'allocation': '50% · 10/2026 – 11/2026'},
             [{'title': 'Chứng chỉ', 'lines': ['Chứng chỉ hành nghề khảo sát địa hình hạng II (giả lập)']}]),
    ],
}

# Illustrative accepted value and cash per contract code (VND decimal strings).
# Shown only next to the real contract value, only with financial_read.
FINANCE_ILLUSTRATION = {
    'DEMO-HD-CAU-01': {'accepted': '1500000000', 'collected': '1200000000'},
}

FINANCE_SOURCES = [
    {'name': 'Giá trị hợp đồng', 'source': 'tp.contract.line.amount (TP Contracts)', 'state': 'Đang dùng trong demo', 'nature': 'real'},
    {'name': 'Giá trị nghiệm thu', 'source': 'Chưa có model — STL-001', 'state': 'Minh họa', 'nature': 'illustrative'},
    {'name': 'Tiền đã thu', 'source': 'account.payment khi nối TP Finance — FIN-001', 'state': 'Minh họa', 'nature': 'illustrative'},
    {'name': 'Chi phí nhân công', 'source': 'account.analytic.line (hr_timesheet)', 'state': 'Chưa cài trên DB demo', 'nature': 'absent'},
    {'name': 'Chi phí khác', 'source': 'hr.expense, account.move', 'state': 'Chưa cài trên DB demo', 'nature': 'absent'},
]
