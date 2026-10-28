# Dashboard prototype cũ

Bản vanilla JavaScript với dữ liệu hoàn toàn giả lập, dùng để tham khảo trình bày KPI, hai sổ chủ đầu tư/thầu phụ và giao khoán cấp 1/cấp 2. Không kết nối dữ liệu doanh nghiệp.

Từ root repository:

```powershell
npm.cmd run prototype --prefix frontend
npm.cmd run test:prototype --prefix frontend
```

Server mặc định dùng `127.0.0.1:4173`, cần dừng Vite hoặc đặt `PORT=4174`. Có thể chạy `node scripts/serve.js` trực tiếp từ thư mục prototype. [Ứng dụng React hiện hành](../README.md) nối API Odoo thật; không lấy quy tắc tài chính trong fixture làm quy tắc production.
