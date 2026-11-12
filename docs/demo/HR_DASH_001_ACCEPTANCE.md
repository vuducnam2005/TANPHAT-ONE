# HR-DASH-001 và khóa tài khoản — nghiệm thu

**Cập nhật12/11/2026:** HR-DASH-002 thay hình thức dashboard bằng giao diện
sáng cố định và biểu đồ lớn; kết quả tại [acceptance mới](HR_DASH_002_ACCEPTANCE.md).
Các ca dark-theme CHG010 bên dưới là lịch sử; hiện HR luôn sáng khi dark.
Backend và khóa/mở tài khoản CHG010 giữ nguyên.

Batch CHG-20261111-010. Người dùng ngày 11/11/2026 yêu cầu thực thi trực tiếp,
test 18079, backup/restore kiểm chứng rồi áp 18069, không commit/push.
Đây là cho phép triển khai của lượt này, không thay vai trò điều phối mặc định.

## Ca kiểm trước code

HD01–HD12 theo [prompt](../prompts/CLAUDE_HR_DASH_001_OVERVIEW_REDESIGN.md).

| ID | Điều kiện đạt | Kết quả |
| --- | --- | --- |
| HD01–HD03 | 5 KPI, donut đơn vị, bar chức vụ, tổng/partition cùng population | Đạt kỹ thuật; xem bằng chứng dưới |
| HD04–HD06 | Department/job/status/reset/catalog/scope; click đúng list; màu ổn định | Đạt kỹ thuật; xem bằng chứng dưới |
| HD07 | Response cũ bị bỏ; loading/error chặn drilldown/export | Đạt kỹ thuật; xem bằng chứng dưới |
| HD08–HD09 | Excel cùng filter; mobile tính liên hệ; không field riêng tư | Đạt kỹ thuật; xem bằng chứng dưới |
| HD10–HD12 | Responsive/dark/reduced-motion/zoom; bảo toàn main; empty/error/retry | Đạt kỹ thuật; xem bằng chứng dưới |
| AL01 | Tình trạng: Mở/Khóa/Chưa liên kết; archive hồ sơ tách khóa user | Đạt kỹ thuật; xem bằng chứng dưới |
| AL02 | Chỉ system admin đúng company được khóa/mở; bắt buộc lý do; lưu audit | Đạt kỹ thuật; xem bằng chứng dưới |
| AL03 | Không khóa chính mình/root/admin/public/template; target cũ bị từ chối | Đạt kỹ thuật; xem bằng chứng dưới |
| AL04 | Đúng mật khẩu của user khóa: thông báo khóa; sai mật khẩu/unknown: generic | Đạt kỹ thuật; xem bằng chứng dưới |
| AL05 | Khóa chặn xác thực và session hiện hữu; mở không thay quyền/mật khẩu | Đạt kỹ thuật; xem bằng chứng dưới |
| AL06 | Gửi phản hồi chỉ báo đang phát triển; không network/ticket/email | Đạt kỹ thuật; xem bằng chứng dưới |
| OPS01 | Backup DB/filestore/source/config, SHA/table/blob/sequence restore kiểm chứng | Đạt kỹ thuật; xem bằng chứng dưới |
| OPS02 | Apply đúng module lên main; giữ roster/account/grant; smoke chỉ đọc | Đạt kỹ thuật; xem bằng chứng dưới |

Kết quả kỹ thuật và nghiệm thu hình thức/nghiệp vụ của người dùng ghi riêng.
Không gọi tự kiểm là audit độc lập. Evidence chứa dữ liệu nhân viên nằm private `.local/`.

## Kết quả thực chạy

Ngày11/11/2026, CHG010. **Kỹ thuật đạt; visual/business/pilot chờ người dùng.**

- HD01–HD04/HD06/HD08–HD09: Odoo backend và XLSX/filter/catalog/company,
  tổng/partition/job/mobile/empty/scope đạt; browser đối chiếu39/9/6.
- HD05: legend/bar/table mở native list, back dashboard; KPI hồ sơ/liên kết/
  chưa liên kết/thiếu cơ bản chung action scope. KPI đơn vị cuộn bảng tổng hợp.
- HD07/HD12: HOOT có late-response/loading-block/action/reset/error/retry;
  12HRtests +2dependency,42assertions đạt; Home suite đạt. Backend401/native
  session/CSRF/TOTP được HttpCase kiểm. Browser không inject mọi loại lỗi
  server; không gọi HOOT mock là test lỗi mạng thật.
- HD10: browser1440/1024/768/390/320, dark/reduced-motion, CSSzoom200,
  1navbar/0pageerror đạt trên test/main; keyboard slice có native tabindex/
  Enter/Space, focus styling; không thay kiểm thiết bị thật.
- HD11: main39employee/6KDlinked,9đơn vị có người; fingerprint79bảng trên
  các cột có trước upgrade và612blob không thuộc assets không đổi.
- AL01–AL06: backend và browser bằng actor giả đạt. Lock giữ employee.active,
  native user.active=false; active session bị chặn, unlock cùng password,
  token revision không hồi sinh session; đúng password mới hiện lock notice;
  feedback không có network/submission. Reason/admin/company/stale/self/
  protected identity có guard. Không khóa/reset tài khoản thật trên main.
- OPS01–OPS02: snapshot cuối092100242854Z, restore test595rowsets/
  636blobs/428sequences đúng trước neutralize; test lại20ca,0failed/0errors.
  Main upgrade2module sạch và browser smoke5nhóm đạt. Test cuối đã restore
  về roster39, không giữ fixture giả của E2E.

Evidence private:

- .local/hr-dash001/odoo-final-rehearsal.log
- .local/hr-dash001/ui-18079/result.json và ui-18069/result.json, ảnh/XLSX
- .local/hr-dash001/lock-e2e/result.json và locked-login.png
- .local/hr001/hoot-18079/result.json và log từng module
- .local/hr001/restore-evidence.json
- .local/hr-dash001/main-preservation-result.json
- .local/hr-dash001/tested-source.json và rollback-source.zip

Lượt HTTP test đầu lỗi bind socket; restore đầu bị FK mới trong test không
có trong dump cũ. Đã sửa điều kiện vận hành, chạy lại đạt. Các lượt fail
giữ log, không tính là pass. Log Windows GC asset có PermissionError trong
cleanup test, kết quả tests0errors; blob restore/main có kiểm riêng.
Chưa có cặp ảnh before–after mới cùng phiên CHG010; tham chiếu ảnh HR cũ,
ảnh after thật đã xem desktop/mobile. Không có audit độc lập.
