# tp_i18n_vi — Việt hóa giao diện (VI-001)

Addon bổ sung tiếng Việt: [`i18n/vi.po`](i18n/vi.po) cho nhãn native, menu, action và trường; `i18n/supplements/` cho chuỗi JavaScript/Python theo namespace gốc; `i18n/server_vi.po` cho thông báo Python còn thiếu. Không có model nghiệp vụ, view, menu, dữ liệu, ACL hay rule. Một asset bổ sung nhãn tuần dài còn thiếu trong locale Việt của FullCalendar, giữ nguyên các locale khác.

- Bảng thuật ngữ, ma trận màn hình và gap: [docs/i18n/VI_GLOSSARY_AND_COVERAGE.md](../../docs/i18n/VI_GLOSSARY_AND_COVERAGE.md).
- `depends` liệt kê mọi module có thuật ngữ bị thay. Khi nạp lại ngôn ngữ cho toàn bộ module, Odoo nạp theo thứ tự phụ thuộc nên addon này luôn được nạp sau cùng.
- en_US giữ nguyên; ID menu/action/selection và quyền không đổi.
- Sinh lại catalog: `.local/vi001/build_overlay.py` (ngoài Git) đọc giá trị en_US từ DB cô lập làm `msgid`. Test `test_catalog_matches_installed_source` báo lỗi nếu bản gốc native đổi.

Cài hoặc áp lại bản dịch (cần vi_VN đã active):

```powershell
.\.venv\Scripts\python.exe odoo-bin -c .local/odoo.conf -d tp_tanphat_dev --db-filter '^tp_tanphat_dev$' -i tp_i18n_vi --stop-after-init --no-http
.\.venv\Scripts\python.exe odoo-bin -c .local/odoo.conf -d tp_tanphat_dev --db-filter '^tp_tanphat_dev$' -u tp_i18n_vi --i18n-overwrite --stop-after-init --no-http
```

Lần cài đầu không ghi đè bản dịch native đã có, nên phải chạy thêm `-u tp_i18n_vi --i18n-overwrite`. Lệnh này chỉ ghi đè thuật ngữ trong catalog của addon. Gỡ addon không xóa bản dịch đã ghi; để về bản native, chạy `odoo-bin i18n import -w -l vi_VN` với catalog native của từng module liên quan, hoặc khôi phục snapshot.

Từ 20.0.1.1.0, hook đăng ký của `ir.http` nạp catalog bổ sung vào cache dịch native theo đúng namespace `web`, `mail`… Chỉ lấp chuỗi thiếu bản dịch hoặc còn nguyên văn tiếng Anh/ASCII; giữ bản Việt native đã có. Không sửa core, thay DOM, đổi quyền hay ngôn ngữ tài khoản. JavaScript vẫn dùng `_t`; Python vẫn dùng `env._`. Khởi động lại mọi worker sau cập nhật catalog; gỡ addon cần khởi động lại để bỏ cache bổ sung.

Kiểm độc lập không cần database: `python scripts/check_vi_catalog.py` và `node custom_addons/tp_i18n_vi/tests/fullcalendar_locale.cjs`. Catalog mở rộng từ chuỗi giao diện upstream công khai, có bản dịch tự động đã kiểm định dạng và rà mẫu; thông báo quan trọng và thuật ngữ đang dùng được rà thủ công. Không gửi hồ sơ, dữ liệu doanh nghiệp hoặc secret tới dịch vụ dịch. Tên người, nội dung hồ sơ và mã kỹ thuật giữ nguyên.

Catalog bổ sung được kiểm placeholder, XML ID/source, bản native, en_US và UI. Phạm vi thực kiểm và những màn hình chưa đi hết nằm ở tài liệu coverage; không nhận số thuật ngữ là bằng chứng đã kiểm mọi luồng nghiệp vụ.
