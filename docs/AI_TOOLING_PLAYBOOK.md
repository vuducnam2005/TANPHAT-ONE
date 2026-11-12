# TANPHAT ONE — Công cụ AI và cách áp dụng

Ngày 07/11/2026, CHG-20261107-010. Áp dụng theo yêu cầu người dùng học hỏi từ
Playwright CLI, Ponytail, OmniRoute, Graphify và Agent Skills. Đây là công cụ
phát triển, không phải các phân hệ nghiệp vụ đã đưa vào ERP.

## 1. Phần đã áp dụng

| Nguồn | Áp dụng vào TANPHAT ONE | Trạng thái |
| --- | --- | --- |
| [Playwright CLI](https://github.com/microsoft/playwright-cli) | Inspect DOM, phiên riêng, ảnh desktop/mobile, kiểm thao tác và console; dùng lại test có sẵn | CLI 0.1.23 có sẵn; đã bổ sung skill Codex; có smoke chỉ đọc |
| [Ponytail](https://github.com/DietrichGebert/ponytail) | Hiểu luồng trước; ưu tiên helper/native Odoo; sửa nhỏ nhưng đủ yêu cầu; review cả caller/security/test | Đã bổ sung `ponytail`, `ponytail-review` cho Codex và đưa nguyên tắc vào skill dự án |
| [OmniRoute](https://github.com/diegosouzapw/OmniRoute) | Thiết kế ranh giới provider, lỗi/retry/chi phí/dữ liệu cho giai đoạn tích hợp AI | Chỉ tiếp thu thiết kế ở mục 5; chưa cài gateway hoặc nối provider vào Odoo |
| [Graphify](https://github.com/Graphify-Labs/graphify) | Bản đồ quan hệ code để hỗ trợ đọc và đánh giá phạm vi ảnh hưởng | CLI 0.9.101 có sẵn; đã chạy local AST cho `custom_addons/`, không chạy semantic AI |
| [Anthropic Skills](https://github.com/anthropics/skills) / [Agent Skills](https://agentskills.io) | Skill có entrypoint và metadata; dùng chung quy tắc Codex/Claude, hướng dẫn theo đúng việc | Đã thêm `webapp-testing` cho Codex và skill dự án; giữ frontend-design/document skills hiện có |

Không thay core Odoo, model, quyền, workflow kinh doanh, cấu hình hoặc database.
Không cài hooks toàn cục, không chép đè AGENTS bằng mẫu bên ngoài. Các skill
mới có thể được nhận diện ở lượt tiếp theo; mở lại phiên nếu client chưa thấy.

## 2. Điểm vào cho AI và nguồn cài đặt

- Codex: [.agents/skills/tanphat-odoo-delivery/SKILL.md](../.agents/skills/tanphat-odoo-delivery/SKILL.md).
- Claude: [CLAUDE.md](../CLAUDE.md) và [adapter](../.claude/skills/tanphat-odoo-delivery/SKILL.md).
- Luật dự án: [AGENTS.md](../AGENTS.md), [workflow](AI_CHANGE_WORKFLOW.md), [status](PROJECT_STATUS.md).
- Codex tìm skill dự án trong `.agents/skills` theo [tài liệu chính thức](https://developers.openai.com/codex/skills/).

Các skill upstream được cài vào `C:\Users\vuduc\.codex\skills`, không nằm trong
Git của dự án. Cài bằng helper của `skill-installer`, pin revision để có thể
tái lập; không cập nhật lên `latest` trong lúc chạy một task:

| Repo / license nguồn | Revision đã cài hoặc đối chiếu | Đường dẫn skill |
| --- | --- | --- |
| microsoft/playwright-cli / Apache-2.0 | `4bc00fb7fa5b4329f2fb53ac4743a066c2c664e8` | `skills/playwright-cli` |
| DietrichGebert/ponytail / MIT | `96608e078b2d5ea607c5c3b8b5a54d1c1fba6846` | `skills/ponytail`, `skills/ponytail-review` |
| anthropics/skills / theo LICENSE.txt của skill | `2c5958ecac7cee2b583967a2c4981d0f4a75c579` | `skills/webapp-testing` |
| Graphify-Labs/graphify / Apache-2.0 | `16218bfc80d4ca2799734d045039f7ed1a5fa9fb` (nhánh v8, nguồn tham khảo) | CLI cài trước: 0.9.101; không tuyên bố binary khớp commit này |
| diegosouzapw/OmniRoute / MIT | `191dce8d534ceb56c28a08e71381284a9a87838f` (nguồn tham khảo) | Chưa cài runtime |

Ví dụ tái lập một skill trên máy mới, khi có nhu cầu sử dụng:

```powershell
.\.venv\Scripts\python.exe "$env:USERPROFILE\.codex\skills\.system\skill-installer\scripts\install-skill-from-github.py" --repo microsoft/playwright-cli --ref 4bc00fb7fa5b4329f2fb53ac4743a066c2c664e8 --path skills/playwright-cli
```

Claude đã có skill `graphify` và `playwright-cli` ở user scope trước lượt này.
Adapter dự án đọc cùng một bản hướng dẫn thay vì duy trì hai bộ luật khác nhau.
Không đổi các skill Claude có sẵn. Khi upstream gợi ý Python/React hoặc quét
toàn corpus, chọn phương án phù hợp native Odoo và scope task của dự án.

## 3. Kiểm giao diện và review code

Trước khi sửa, ghi acceptance có thể quan sát: người dùng nào, màn nào, thao tác
gì, kết quả nào, bằng chứng gì. Với sửa giao diện, lưu ảnh trước–sau cùng route,
vai trò, dữ liệu và viewport. Test xanh, người dùng chấp nhận hình thức, xác nhận
nghiệp vụ và cho phép pilot là bốn kết luận riêng.

Ưu tiên các test `scripts/*_ui.cjs`, `*_checks.cjs` đã có và package Playwright
của dự án. Dùng CLI cho khảo sát/kiểm nhanh; locator theo role/label/DOM thật,
chờ phần tử cần thiết của Odoo, tránh chỉ dựa vào `networkidle` hoặc sleep.
Không thay cả test suite chỉ để theo ví dụ Python của skill upstream.

CLI có sẵn: `playwright-cli.cmd` trong npm user path. Dùng tên phiên riêng,
không dùng `close-all` hoặc `kill-all`. Ví dụ **chỉ đọc** trang đăng nhập:

```powershell
New-Item -ItemType Directory -Force '.local/ai-tooling' | Out-Null
Push-Location '.local/ai-tooling'
try {
    playwright-cli -s=tp-own-review open http://127.0.0.1:18069/web/login --browser msedge
    playwright-cli -s=tp-own-review snapshot
    playwright-cli -s=tp-own-review resize 1440 1000
    playwright-cli -s=tp-own-review screenshot --filename=login-desktop.png
    playwright-cli -s=tp-own-review resize 390 844
    playwright-cli -s=tp-own-review screenshot --filename=login-mobile.png
} finally {
    playwright-cli -s=tp-own-review close
    Pop-Location
}
```

Trình duyệt thật có thể ghi session/log kỹ thuật; “chỉ đọc” ở đây nghĩa là không
gửi action ghi nghiệp vụ, không đăng nhập hay thay account. Không đưa cookie,
storage state hoặc dữ liệu công ty vào Git. Smoke login không chứng minh quyền,
luồng hợp đồng hay chất lượng workspace sau đăng nhập.

Review theo Ponytail: lần theo data vào → action → security → dữ liệu ra; kiểm
cả caller ngoài diff; mỗi finding có tình huống tái hiện, file/dòng, ảnh hưởng và
cách sửa nhỏ nhất. Không cắt validation/security/accessibility để giảm số dòng.
Self-review phải ghi là tự kiểm; chưa có reviewer khác thì không gọi audit độc lập.

## 4. Bản đồ source Graphify chỉ chạy tại máy

Đầu ra riêng: `.local/ai-tooling/graphify-out/graph.json`. Đã chạy trên
`custom_addons/` (14 addon `tp_*` hiện có). Không quét `odoo/`, `addons/`, NAS,
Excel/PDF, filestore, credential hoặc dump DB; không kết nối PostgreSQL.

Lệnh tái tạo ở root dự án, môi trường chỉ đặt cho process này:

```powershell
$env:GRAPHIFY_BACKEND='none'
$env:GRAPHIFY_OUT='C:\TANPHAT ONE\.local\ai-tooling\graphify-out'
$env:PYTHONIOENCODING='utf-8'
graphify extract 'C:\TANPHAT ONE\custom_addons' --code-only --no-cluster --max-workers 2 --out 'C:\TANPHAT ONE\.local\ai-tooling'
```

Không bật semantic/label/provider/global/watch/hook tự động. Đọc/query trước
nếu graph còn đúng source; cập nhật khi code liên quan thay đổi, không build
lại cho câu hỏi tên hàm đơn giản. Graph build không thay Git/status/checker.

```powershell
graphify query 'contract workflow' --seed tp_contract_models_tp_contract_tpcontract --budget 1000 --graph '.local/ai-tooling/graphify-out/graph.json'
graphify god-nodes --top 8 --graph '.local/ai-tooling/graphify-out/graph.json'
graphify tree --graph '.local/ai-tooling/graphify-out/graph.json' --output '.local/ai-tooling/graphify-out/SOURCE_TREE.html' --label 'TANPHAT ONE custom addons'
```

Lần build đầu: **150 code files, 1.547 nodes, 3.039 edges**. Bỏ 12 tài liệu/ảnh,
73 file không được phân loại (gồm XML/SCSS) và `credential.xml` bị đánh dấu nhạy cảm;
50 code files không có symbol. Đây là bản đồ AST hỗ trợ đọc source, **không phải
sơ đồ nghiệp vụ hoàn chỉnh hay bằng chứng ACL đúng**. Quan hệ ORM động `_inherit`,
XML action/menu/view/rule, quyền và công thức phải đọc source/test/runtime.
Nhãn EXTRACTED/INFERRED là mức bằng chứng của tool, không là kết luận nghiệp vụ.
Khi graph và source khác nhau, ưu tiên source và ghi rõ độ cũ của graph.

Query tên ngắn có thể trùng symbol và trả exit 3; chọn node ID sau khi đối chiếu
file nguồn rồi dùng `--seed`, không đoán. `--budget` của CLI hiện có thể vẫn xuất
đủ quan hệ vượt số token đề nghị; thu hẹp câu hỏi/context khi cần. Tree dùng
source_file tương đối với `custom_addons/`; không truyền absolute `--root` vì
không khớp node. `affected` không thấy node không chứng minh Odoo không bị ảnh
hưởng: các quan hệ `_inherit`/XML động vẫn cần kiểm riêng.

## 5. Áp dụng tư duy OmniRoute khi tới bước AI

Hiện chưa có nhu cầu đặt gateway vào luồng KH-KD. Giai đoạn chuẩn bị này chốt
**hướng thiết kế đề xuất**, chưa tạo provider, key, service hoặc quyền mới:

- ERP vẫn hoạt động khi AI lỗi; tính tiền, quyền và chuyển trạng thái thuộc Odoo.
- Chỉ backend gọi provider qua adapter; key ở cấu hình bí mật ngoài Git/browser.
- Chọn provider/model theo allowlist và nhu cầu dữ liệu; không âm thầm hạ model
  hoặc chuyển nhà cung cấp khi chưa có policy tương ứng.
- Giảm dữ liệu gửi đi, khử thông tin nhạy cảm; nguồn/phiên bản và người dùng phải
  có scope đúng. Không upload hồ sơ doanh nghiệp chỉ để thử gateway.
- Có timeout, ngân sách và giới hạn retry; thao tác ghi cần idempotency và kiểm
  quyền phía Odoo. AI không tự duyệt BASE, ký hoặc chốt số liệu.
- Ghi request ID, provider/model, thời gian, trạng thái, lượng sử dụng và chi phí
  khi đo được; không ghi nguyên prompt nhạy cảm/key. Không coi quota quảng cáo
  của bên thứ ba là tín dụng miễn phí được bảo đảm.

Khi có task AI cụ thể mới so sánh gọi trực tiếp, adapter nhỏ và OmniRoute; đọc
license/dependency, kiểm provider, test lỗi/budget/permission trên test trước khi
đề xuất triển khai. Phần này không đánh dấu “AI tích hợp xong”.

## 6. Bằng chứng và bước kế tiếp

Bằng chứng local nằm trong `.local/ai-tooling/`: log build, source baseline,
graph JSON/HTML và smoke browser. Skill/checker/link/diff và đối chiếu hash được
ghi ở CHG-20261107-010; checker không tự kiểm mọi file skill mới.

Smoke lần này: input tài khoản/mật khẩu/nút đăng nhập hiển thị, không tràn ngang
ở 1440×1000 và 390×844; bật/tắt hiện mật khẩu trên trường rỗng đạt; không có
pageerror trong smoke, console phiên không lỗi/cảnh báo. Chỉ kiểm khả năng bật
emulation reduced motion, chưa chứng minh mọi animation của hệ thống tuân thủ.
Không đăng nhập, không submit form, không gọi action ghi nghiệp vụ; phiên riêng
đã đóng. Ảnh login đã mở kiểm thị giác. Đây không phải test sau đăng nhập.

Việc sản phẩm kế tiếp vẫn là **review mẫu KD-UI-006**, rồi triển khai native
theo phản hồi người dùng và scope đã giao. Không mở phân hệ khác hoặc đóng các
gate nghiệp vụ/pilot bằng một lượt chuẩn hóa công cụ.
