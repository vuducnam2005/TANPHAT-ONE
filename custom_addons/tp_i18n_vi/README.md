# tp_i18n_vi — Việt hóa giao diện (VI-001)

Addon chỉ chứa bản dịch: [`i18n/vi.po`](i18n/vi.po) thay các nhãn native vi_VN khác bảng thuật ngữ TANPHAT ONE (tên app, action mở app, vài menu con còn tiếng Anh, nhãn trạng thái dịch sai). Không có model, view, menu, dữ liệu, ACL, rule hay asset.

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

Giới hạn: nút chung của web client (`New`, `Discard`…) do module `web` dịch theo không gian tên riêng, nên không thay được bằng catalog của addon khác nếu không sửa `addons/`. Các nhãn này giữ bản native (xem gap).
