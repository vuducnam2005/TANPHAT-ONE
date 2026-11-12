# KD-ACCESS-001 — Đăng nhập và kiểm tra năm vai trò

Hướng dẫn lịch sử. Xem [guide KD-ACCESS-002](KD_ACCESS_002_USER_GUIDE.md) cho
quyền CRM mới; tài khoản/mật khẩu và scope dự án của batch001 được giữ.

Dev: [TANPHAT ONE](http://127.0.0.1:18069/odoo), database `tp_tanphat_dev`.
Ngày 08/11/2026; đã provision và tự kiểm kỹ thuật trên dev, chưa nghiệm thu nghiệp vụ/pilot.

## Lấy thông tin đăng nhập

Mở file local `.local/kd-access001/dev-credentials.json` để lấy login và mật khẩu
riêng của từng alias. Đối chiếu người–alias ở `.local/kd-access001/staff-map.json`.
Các file này ngoài Git, chỉ Windows owner/SYSTEM/Administrators có quyền đọc.
Mật khẩu dev được sinh riêng với clone; không dùng credential của actor mẫu cũ.
Không gửi file này cho nhân sự qua email/chat trong task này.

1. Mở URL trên, nhập login/password đúng alias; chọn DB `tp_tanphat_dev` nếu được hỏi.
2. Từ Trang chủ, mở **Kế hoạch Kinh doanh**, rồi **Hồ sơ dự án** hoặc **Tổng quan**.
3. Để đổi vai trong cùng browser, mở menu người dùng góc phải → **Đăng xuất**;
   đăng nhập tài khoản tiếp theo. Tab cùng browser dùng chung session. Muốn so sánh
   song song, dùng profile browser riêng; nhiều cửa sổ riêng tư có thể vẫn chung session.
4. Nếu tài khoản không vào được, đối chiếu đúng file **dev** và DB; không reset tài
   khoản mẫu hoặc chạy setup/seed. Người vận hành kiểm provenance trước mọi sửa quyền.

## Kiểm từng vai trò

| Alias | Dự án minh họa được xem | Quyền và cách kiểm |
| --- | --- | --- |
| head | ANP/HLM/NTH/DVT/BSN/PLC/THA/HPT (8) | Đọc tiền, Tổng quan/Báo cáo; trả hồ sơ khi đúng reviewer. Không có nút tạo typed dossier; không sửa nháp của người khác |
| deputy | ANP/HLM/NTH/DVT (4) | Lập/sửa/gửi hồ sơ của mình; đọc/sửa tiền nháp đúng scope; hợp đồng draft/submit; trả khi được chỉ định reviewer của người khác |
| project_lead | BSN/PLC/THA/HPT (4) | Tương tự deputy, với bốn dự án khác. ANP/HLM phải không xuất hiện trong danh sách/dropdown |
| planning | ANP/HLM/BSN/PLC (4) | Lập/sửa/gửi giao khoán, sản lượng, kế hoạch, năng lực của mình; đọc/sửa tiền nháp đúng scope. Không lập nghiệm thu/đề nghị thanh toán hoặc gửi/rà soát hợp đồng; không review |
| support | ANP/HLM (2) | Chỉ lập/sửa năng lực của mình; không gửi/rà soát hoặc đọc tiền, snapshot/file tài chính. Nút Tạo hồ sơ ở Tổng quan chỉ có năng lực |

Mã đầy đủ có tiền tố `KD26-`. Assignment đều là **reader**; role chuyên môn được
thể hiện qua capability, không dùng coordinator/manager để mở rộng quyền.
Các domain typed của head/deputy/project_lead: allocation, production, acceptance,
payment, plan, credential, obligation. Grant review không cho tự rà soát và không
thay yêu cầu reviewer được chỉ định. Hồ sơ cũ giữ owner/reviewer cũ, vì vậy không
đòi phải có nút sửa/trả trên hồ sơ của actor mẫu. Người lập mới chọn reviewer đủ
quyền trong cùng dự án; head là lựa chọn chung cho tám dự án.

Kiểm đọc trên dev: đếm dự án, mở một form, xem Tổng quan, mở Năng lực và kiểm nút
Tạo hồ sơ. Không cần tạo/gửi/trả hồ sơ để thử quyền. Luồng ghi đã được kiểm trên
clone và rollback; [acceptance](KD_ACCESS_001_ACCEPTANCE.md) ghi bằng chứng.

## Giới hạn đã bàn giao

CRM/cơ hội chưa mở cho cả năm role: backend hiện gộp prepare với khai báo nộp,
chưa bảo vệ owner-only và tiền CRM theo ma trận này. Không cấp salesman/all-leads
để hiện menu. Cũng chưa mở tạo dự án/ghi WBS vì cần quyền manager hiện hành.
Đây là phần chưa cung cấp, không phải lỗi đăng nhập.

Scope dự án/grant là minh họa trên registry `KD_NATIVE_001_REALISTIC_V1`, không
tự cấp dự án mới và không là phân công công việc thật. Không có BASE approval,
ký/hiệu lực, posting/paid hoặc quản trị grant cho các tài khoản này. Odoo tự sinh
một task hướng dẫn và bảy stage cá nhân mỗi user; được journal private, không thuộc
dataset KH-KD và không thấy qua rule Project/Task của nhóm scoped staff.

## Vận hành và rollback

Journal ID/scope và before/after ở `.local/kd-access001/dev-delta.json`;
backup verified tại `.local/kd-access001/backup-pre-apply-20261108T130448Z/`.
Không đưa các file private, dump hoặc credential vào Git.

Khi cần rollback theo quyết định của chủ dự án, công cụ sau archive đúng năm user,
revoke đúng assignment/grant đã journal; giữ lịch sử và onboarding, không xóa dữ liệu:

```powershell
.\.venv\Scripts\python.exe -X utf8 scripts/kd_access001.py rollback --target dev
```

Không chạy lệnh này chỉ để đổi vai. Rule security của nhóm mới vẫn an toàn khi
không còn user hoạt động. Khôi phục source/module cần review riêng; bản source cũ
nằm trong snapshot/backup. Không restore toàn DB dev để hoàn tác riêng tài khoản.
