import { Link } from 'react-router-dom';
import type { Project } from '../../../shared/api/types';

export function ProjectCard({ project }: { project: Project }) {
  return (
    <Link className="tp-project-card" to={`/projects/${project.id}`}>
      <div className="tp-project-card-top"><span className="tp-code">{project.code}</span><span className="tp-live"><i /> Đang hoạt động</span></div>
      <h3>{project.name}</h3>
      <dl>
        <div><dt>Công ty</dt><dd>{project.company.name}</dd></div>
        <div><dt>Phòng chủ trì</dt><dd>{project.department?.name ?? 'Chưa gắn'}</dd></div>
        <div><dt>Đối tác</dt><dd>{project.customer?.name ?? 'Chưa cập nhật'}</dd></div>
      </dl>
      <span className="tp-card-action">Mở hồ sơ <b>→</b></span>
    </Link>
  );
}
