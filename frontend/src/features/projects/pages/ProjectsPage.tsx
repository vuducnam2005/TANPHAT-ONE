import { useSearchParams } from 'react-router-dom';
import { useProjects } from '../queries';
import { ApiError } from '../../../shared/api/client';
import { StatusPanel } from '../../../shared/ui/StatusPanel';
import { ProjectCard } from '../components/ProjectCard';

export function ProjectsPage() {
  const [parameters, setParameters] = useSearchParams();
  const search = (parameters.get('q') ?? '').slice(0, 100);
  const rawOffset = Number(parameters.get('offset') ?? 0);
  const offset = Number.isInteger(rawOffset) && rawOffset >= 0 && rawOffset <= 10000 ? rawOffset : 0;
  const query = useProjects({ q: search, offset });
  const records = query.data?.data ?? [];

  function changePage(next: number) {
    setParameters({ ...(search ? { q: search } : {}), ...(next ? { offset: String(next) } : {}) });
  }

  return (
    <section className="tp-page" aria-labelledby="projects-title">
      <div className="tp-page-intro">
        <div>
          <h2 id="projects-title">Dự án đang theo dõi</h2>
          <p>Danh sách dự án trong phạm vi được phân công. Mở một dự án để xem hồ sơ và phòng chủ trì.</p>
        </div>
        {query.isSuccess && <div className="tp-count-block"><strong>{records.length}</strong><span>dự án trên trang</span></div>}
      </div>
      <form className="tp-toolbar" key={search} onSubmit={(event) => {
        event.preventDefault();
        const value = String(new FormData(event.currentTarget).get('search') ?? '').trim();
        setParameters(value ? { q: value } : {});
      }}>
        <label htmlFor="project-search">
          <span>Tìm theo mã hoặc tên</span>
          <input id="project-search" name="search" type="search" defaultValue={search} maxLength={100} placeholder="Nhập mã hoặc tên dự án" />
        </label>
        <button className="tp-primary-button" type="submit">Tìm dự án</button>
        <button className="tp-quiet-button" type="button" disabled={query.isFetching} onClick={() => query.refetch()}>Làm mới</button>
        {search && <button className="tp-quiet-button" type="button" onClick={() => setParameters({})}>Xóa tìm kiếm</button>}
      </form>

      {query.isPending ? (
        <div role="status" aria-label="Đang tải dự án" className="tp-project-grid"><div className="tp-skeleton" /><div className="tp-skeleton" /></div>
      ) : query.isError ? (
        <StatusPanel
          title={query.error instanceof ApiError && query.error.status === 403 ? 'Chưa có quyền truy cập dự án' : 'Chưa tải được danh sách dự án'}
          description={query.error instanceof ApiError && query.error.status === 403 ? 'Liên hệ quản trị viên để được cấp quyền vào không gian này.' : 'Kiểm tra kết nối rồi thử lại.'}
          error={query.error}
        ><button onClick={() => query.refetch()}>Thử lại</button></StatusPanel>
      ) : records.length ? (
        <div className="tp-project-grid">{records.map((project) => <ProjectCard key={project.id} project={project} />)}</div>
      ) : (
        <div className="tp-empty" role="status"><strong>{search ? 'Không có dự án phù hợp' : 'Chưa có dự án được phân công'}</strong><span>{search ? 'Thử tìm theo mã khác hoặc xóa tìm kiếm.' : 'Liên hệ quản trị viên để kiểm tra phân công dự án.'}</span></div>
      )}

      {query.isSuccess && (
        <nav className="tp-pagination" aria-label="Phân trang dự án">
          <button className="tp-quiet-button" disabled={offset === 0} onClick={() => changePage(Math.max(0, offset - 20))}>Trang trước</button>
          <span>Trang {Math.floor(offset / 20) + 1}</span>
          <button className="tp-quiet-button" disabled={!query.data.meta.pagination?.has_more || offset + 20 > 10000} onClick={() => changePage(offset + 20)}>Trang sau</button>
        </nav>
      )}
    </section>
  );
}
