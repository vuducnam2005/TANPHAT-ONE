import { Link, useSearchParams } from 'react-router-dom';
import { parseRouteId, useContracts } from '../queries';
import { ApiError } from '../../../shared/api/client';
import { StatusPanel } from '../../../shared/ui/StatusPanel';
import { ContractCard } from '../components/ContractCard';

export function ContractsPage() {
  const [parameters, setParameters] = useSearchParams();
  const search = (parameters.get('q') ?? '').slice(0, 100);
  const projectId = parseRouteId(parameters.get('project_id'));
  const rawOffset = Number(parameters.get('offset') ?? 0);
  const offset = Number.isInteger(rawOffset) && rawOffset >= 0 && rawOffset <= 10000 ? rawOffset : 0;
  const query = useContracts({ q: search, offset, projectId });
  const records = query.data?.data ?? [];
  const project = projectId ? records[0]?.project : undefined;

  function navigate(next: { q?: string; offset?: number; projectId?: number }) {
    setParameters({
      ...(next.q ? { q: next.q } : {}),
      ...(next.projectId ? { project_id: String(next.projectId) } : {}),
      ...(next.offset ? { offset: String(next.offset) } : {}),
    });
  }

  return (
    <section className="tp-page" aria-labelledby="contracts-title">
      <div className="tp-page-intro">
        <div>
          <h2 id="contracts-title">Hồ sơ hợp đồng</h2>
          <p>Hợp đồng của các dự án trong phạm vi được phân công. Số tiền chỉ hiển thị khi bạn được cấp quyền xem tài chính của dự án.</p>
        </div>
        {query.isSuccess && <div className="tp-count-block"><strong>{records.length}</strong><span>hợp đồng trên trang</span></div>}
      </div>
      <form className="tp-toolbar" key={`${search}-${projectId ?? ''}`} onSubmit={(event) => {
        event.preventDefault();
        const value = String(new FormData(event.currentTarget).get('search') ?? '').trim();
        navigate({ q: value, projectId });
      }}>
        <label htmlFor="contract-search">
          <span>Tìm theo số hoặc tên hợp đồng</span>
          <input id="contract-search" name="search" type="search" defaultValue={search} maxLength={100} placeholder="Nhập số hoặc tên hợp đồng" />
        </label>
        <button className="tp-primary-button" type="submit">Tìm hợp đồng</button>
        <button className="tp-quiet-button" type="button" disabled={query.isFetching} onClick={() => query.refetch()}>Làm mới</button>
        {search && <button className="tp-quiet-button" type="button" onClick={() => navigate({ projectId })}>Xóa tìm kiếm</button>}
      </form>
      {projectId && (
        <div className="tp-notice tp-filter-note">
          <span>Đang xem hợp đồng của dự án {project ? `${project.code} · ${project.name}` : 'đã chọn'}.</span>
          <span>
            <Link to={`/projects/${projectId}`}>Hồ sơ dự án</Link>
            {' · '}
            <Link to="/contracts">Xem tất cả hợp đồng</Link>
          </span>
        </div>
      )}

      {query.isPending ? (
        <div role="status" aria-label="Đang tải hợp đồng" className="tp-project-grid"><div className="tp-skeleton" /><div className="tp-skeleton" /></div>
      ) : query.isError ? (
        <StatusPanel
          title={query.error instanceof ApiError && query.error.status === 403 ? 'Chưa có quyền truy cập hợp đồng' : 'Chưa tải được danh sách hợp đồng'}
          description={query.error instanceof ApiError && query.error.status === 403 ? 'Liên hệ quản trị viên để được cấp quyền vào không gian này.' : 'Kiểm tra kết nối rồi thử lại.'}
          error={query.error}
        ><button onClick={() => query.refetch()}>Thử lại</button></StatusPanel>
      ) : records.length ? (
        <div className="tp-project-grid">{records.map((contract) => <ContractCard key={contract.id} contract={contract} />)}</div>
      ) : (
        <div className="tp-empty" role="status">
          <strong>{search ? 'Không có hợp đồng phù hợp' : 'Chưa có hợp đồng trong phạm vi được phân công'}</strong>
          <span>{search ? 'Thử tìm theo số khác hoặc xóa tìm kiếm.' : 'Hợp đồng chỉ hiển thị khi dự án của hợp đồng nằm trong phạm vi bạn được phân công.'}</span>
        </div>
      )}

      {query.isSuccess && (
        <nav className="tp-pagination" aria-label="Phân trang hợp đồng">
          <button className="tp-quiet-button" disabled={offset === 0} onClick={() => navigate({ q: search, projectId, offset: Math.max(0, offset - 20) })}>Trang trước</button>
          <span>Trang {Math.floor(offset / 20) + 1}</span>
          <button className="tp-quiet-button" disabled={!query.data.meta.pagination?.has_more || offset + 20 > 10000} onClick={() => navigate({ q: search, projectId, offset: offset + 20 })}>Trang sau</button>
        </nav>
      )}
    </section>
  );
}
