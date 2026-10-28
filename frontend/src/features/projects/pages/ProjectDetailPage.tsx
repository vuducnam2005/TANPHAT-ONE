import { Link, useParams } from 'react-router-dom';
import { useProject } from '../queries';
import { ApiError } from '../../../shared/api/client';
import { StatusPanel } from '../../../shared/ui/StatusPanel';

export function ProjectDetailPage() {
  const parameter = useParams().projectId ?? '';
  const id = /^\d+$/.test(parameter) ? Number(parameter) : 0;
  const validId = Number.isSafeInteger(id) && id > 0;
  const query = useProject(validId ? id : undefined);
  const notFound = !validId || (query.error instanceof ApiError && query.error.status === 404);
  if (notFound || query.isError) {
    return (
      <StatusPanel
        title={notFound ? 'Không mở được dự án' : 'Chưa tải được hồ sơ dự án'}
        description={notFound ? 'Dự án không tồn tại hoặc nằm ngoài phạm vi được phân công.' : 'Kiểm tra kết nối rồi thử lại.'}
        error={query.error ?? undefined}
      >
        <Link className="tp-primary-button" to="/projects">Danh sách dự án</Link>
        {!notFound && <button onClick={() => query.refetch()}>Thử lại</button>}
      </StatusPanel>
    );
  }
  if (query.isPending) return <div role="status" aria-label="Đang tải hồ sơ dự án" className="tp-skeleton" />;
  const project = query.data.data;
  const updated = new Intl.DateTimeFormat('vi-VN', { timeZone: 'Asia/Ho_Chi_Minh', dateStyle: 'medium', timeStyle: 'short' }).format(new Date(project.updated_at));
  return (
    <section className="tp-page" aria-labelledby="project-title">
      <Link className="tp-back-link" to="/projects">← Danh sách dự án</Link>
      <div className="tp-detail-heading">
        <div><span className="tp-code">{project.code}</span><h2 id="project-title">{project.name}</h2><p>{project.company.name}</p></div>
        <span className="tp-live"><i aria-hidden="true" />{project.active ? 'Đang hoạt động' : 'Đã lưu trữ'}</span>
      </div>
      <dl className="tp-fact-grid">
        <Fact label="Phòng chủ trì" value={project.department?.name ?? 'Chưa cập nhật'} />
        <Fact label="Đối tác" value={project.customer?.name ?? 'Chưa cập nhật'} />
        <Fact label="Công ty quản lý" value={project.company.name} />
        <Fact label="Cập nhật gần nhất" value={updated} />
      </dl>
      <div className="tp-next-step"><strong>Hồ sơ nghiệp vụ</strong><p>Hợp đồng, giao khoán và nghiệm thu sẽ được bổ sung trong giai đoạn tiếp theo.</p></div>
    </section>
  );
}

function Fact({ label, value }: { label: string; value: string }) {
  return <div><dt>{label}</dt><dd>{value}</dd></div>;
}
