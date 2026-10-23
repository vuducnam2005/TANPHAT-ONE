import { useState } from 'react'
import { Button, StatusBadge } from './components/ui'
import './App.css'

const repository = 'https://github.com/vuducnam2005/TadicManagement'

const readiness = [
  {
    name: 'Odoo 20 và PostgreSQL',
    detail: 'Database tadic_demo và trang đăng nhập đã chạy trên máy phát triển.',
    tone: 'ready' as const,
    status: 'Đã kiểm tra',
  },
  {
    name: 'Giao diện React',
    detail: 'React, TypeScript và Vite đã chạy; bản build và lint đạt.',
    tone: 'ready' as const,
    status: 'Đã kiểm tra',
  },
  {
    name: 'Kho mã nguồn',
    detail: 'Git cục bộ đã kết nối với GitHub; cấu hình và mật khẩu nằm ngoài Git.',
    tone: 'ready' as const,
    status: 'Sẵn sàng',
  },
  {
    name: 'Yêu cầu nghiệp vụ',
    detail: 'Quy trình, biểu mẫu và quyền của hai module cần phòng ban xác nhận.',
    tone: 'pending' as const,
    status: 'Cần khảo sát',
  },
]

const navigation = [
  { href: '#tong-quan', label: 'Tổng quan' },
  { href: '#chuan-bi', label: 'Tình trạng chuẩn bị' },
  { href: '#hai-module', label: 'Hai module dự kiến' },
]

function normalizeSearch(value: string) {
  return value
    .toLocaleLowerCase('vi')
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .replaceAll('đ', 'd')
}

function App() {
  const [search, setSearch] = useState('')
  const term = normalizeSearch(search.trim())
  const visibleReadiness = readiness.filter((item) =>
    normalizeSearch(`${item.name} ${item.detail} ${item.status}`).includes(term),
  )

  return (
    <div className="app-shell" id="dau-trang">
      <a className="skip-link" href="#noi-dung">Bỏ qua điều hướng</a>

      <aside className="sidebar" aria-label="Điều hướng dự án">
        <a className="brand" href="#dau-trang" aria-label="Tadic Management, về đầu trang">
          <span className="brand-mark" aria-hidden="true">T</span>
          <span className="brand-copy"><strong>Tadic</strong><small>Management</small></span>
        </a>

        <div className="sidebar-group">
          <p className="sidebar-caption">Không gian làm việc</p>
          <nav aria-label="Nội dung trang">
            {navigation.map((item) => (
              <a className="nav-link" href={item.href} key={item.href}>{item.label}</a>
            ))}
          </nav>
        </div>

        <div className="sidebar-foot">
          <span className="sidebar-foot-line" aria-hidden="true" />
          <p>Tuần 1 · 26/10–01/11/2026</p>
          <span>Bản xem trước giao diện</span>
        </div>
      </aside>

      <main className="workspace" id="noi-dung">
        <div className="workspace-inner">
          <header className="topbar">
            <span>Không gian chuẩn bị</span>
            <a href={repository} target="_blank" rel="noreferrer">Kho mã nguồn</a>
          </header>

          <section className="intro" id="tong-quan" aria-labelledby="page-title">
            <div className="intro-copy">
              <p className="context-line">Kế hoạch tuần 44 <span aria-hidden="true">/</span> 26/10–01/11/2026</p>
              <h1 id="page-title">Khung giao diện quản trị nội bộ</h1>
              <p className="intro-description">
                Bản mẫu cho P.KHKD và Ban quản trị. Cấu trúc điều hướng, bảng trạng thái
                và các thành phần cơ bản đã sẵn sàng để phát triển sau khi chốt yêu cầu.
              </p>
              <a
                className="button-link button-link--primary"
                href={`${repository}/blob/main/docs/tuan-1-checklist.md`}
                target="_blank"
                rel="noreferrer"
              >
                Xem checklist tuần 1
              </a>
            </div>
            <div className="phase" aria-label="Giai đoạn 1 trong 4 tuần">
              <span className="phase-label">Giai đoạn chuẩn bị</span>
              <strong className="phase-number">01</strong>
              <span className="phase-total">trong 04 tuần</span>
            </div>
          </section>

          <section className="section" id="chuan-bi" aria-labelledby="readiness-title">
            <div className="section-heading">
              <div>
                <h2 id="readiness-title">Tình trạng chuẩn bị</h2>
                <p>Ảnh chụp từ môi trường phát triển ngày 23/10/2026; chưa đồng bộ với workbook.</p>
              </div>
              <span className="item-count" aria-live="polite">{visibleReadiness.length} hạng mục</span>
            </div>

            <div className="list-toolbar">
              <label htmlFor="search-readiness">Tìm hạng mục</label>
              <div className="search-controls">
                <input
                  id="search-readiness"
                  type="search"
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Ví dụ: PostgreSQL"
                />
                {search && <Button variant="quiet" onClick={() => setSearch('')}>Xóa tìm kiếm</Button>}
              </div>
            </div>

            <div className="readiness-heading" aria-hidden="true">
              <span>Hạng mục</span><span>Kết quả hiện có</span><span>Tình trạng</span>
            </div>
            <ul className="readiness-list">
              {visibleReadiness.map((item) => (
                <li className="readiness-row" key={item.name}>
                  <strong>{item.name}</strong>
                  <span className="readiness-detail">{item.detail}</span>
                  <StatusBadge tone={item.tone}>{item.status}</StatusBadge>
                </li>
              ))}
            </ul>
            {visibleReadiness.length === 0 && (
              <p className="empty-state" role="status">Không thấy hạng mục phù hợp. Hãy thử từ khóa khác.</p>
            )}
          </section>

          <section className="section" id="hai-module" aria-labelledby="module-title">
            <div className="section-heading">
              <div>
                <h2 id="module-title">Hai module dự kiến</h2>
                <p>Những nội dung cần xác nhận trước khi thiết kế màn hình nghiệp vụ.</p>
              </div>
            </div>
            <div className="module-grid">
              <article className="module">
                <div className="module-header">
                  <h3>P.KHKD</h3>
                  <StatusBadge tone="pending">Chờ khảo sát</StatusBadge>
                </div>
                <p>Ghi nhận luồng công việc và dữ liệu đang dùng để xác định màn hình ưu tiên.</p>
                <ul>
                  <li>Quy trình và người sử dụng</li>
                  <li>Biểu mẫu, trường dữ liệu và mẫu hồ sơ</li>
                  <li>Chức năng cần có trong bản demo</li>
                </ul>
              </article>
              <article className="module">
                <div className="module-header">
                  <h3>Ban quản trị</h3>
                  <StatusBadge tone="pending">Chờ khảo sát</StatusBadge>
                </div>
                <p>Làm rõ trách nhiệm và quyền truy cập trước khi xây dựng cấu trúc dữ liệu.</p>
                <ul>
                  <li>Nhóm người dùng và trách nhiệm</li>
                  <li>Quyền xem, tạo, sửa và duyệt</li>
                  <li>Dữ liệu cần quản lý trong bản demo</li>
                </ul>
              </article>
            </div>
          </section>

          <footer className="footer">
            <span>Khung React để kiểm tra giao diện, chưa đọc hoặc ghi dữ liệu Odoo.</span>
            <a href={`${repository}/blob/main/docs/mau-khao-sat.md`} target="_blank" rel="noreferrer">
              Mẫu khảo sát yêu cầu
            </a>
          </footer>
        </div>
      </main>
    </div>
  )
}

export default App
