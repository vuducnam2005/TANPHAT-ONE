import './App.css'

const setupItems = [
  {
    title: 'Khảo sát nghiệp vụ',
    detail: 'Ghi nhận quy trình, biểu mẫu và dữ liệu mẫu của P.KHKD và Ban quản trị.',
  },
  {
    title: 'Chốt phạm vi MVP',
    detail: 'Xác định chức năng ưu tiên và các phần để triển khai sau.',
  },
  {
    title: 'Chuẩn bị môi trường',
    detail: 'Odoo, PostgreSQL, Git và React đã có cấu trúc để phát triển.',
  },
]

function App() {
  return (
    <main className="page">
      <header className="header">
        <div className="brand-mark" aria-hidden="true">T</div>
        <div>
          <p className="eyebrow">TADIC</p>
          <p className="brand-name">Management</p>
        </div>
      </header>

      <section className="hero" aria-labelledby="page-title">
        <span className="pill">Bản khởi tạo · Tuần 1</span>
        <h1 id="page-title">Nền tảng quản trị nội bộ</h1>
        <p className="intro">
          Trang mẫu ReactJS đã hoạt động. Chức năng P.KHKD và Ban quản trị sẽ
          được xây dựng sau khi chốt yêu cầu và dữ liệu mẫu.
        </p>
      </section>

      <section className="content" aria-label="Các bước chuẩn bị">
        <div className="section-heading">
          <p className="eyebrow">Kế hoạch triển khai</p>
          <h2>Việc cần hoàn tất trước khi lập trình hai module</h2>
        </div>
        <div className="cards">
          {setupItems.map((item, index) => (
            <article className="card" key={item.title}>
              <span className="card-number">0{index + 1}</span>
              <h3>{item.title}</h3>
              <p>{item.detail}</p>
            </article>
          ))}
        </div>
      </section>

      <footer>Trang mẫu giao diện · chưa kết nối dữ liệu Odoo</footer>
    </main>
  )
}

export default App
