import { Navigate, Route, Routes } from 'react-router-dom';
import { AppShell } from './shell/AppShell';
import { ProjectsPage, ProjectDetailPage } from '../features/projects';
import { useSession } from '../shared/api/hooks';
import { loginUrl, SessionContext } from '../shared/api/session';
import { StatusPanel } from '../shared/ui/StatusPanel';
import { product, subsystems } from '../shared/config/product';

export function App() {
  const session = useSession();
  if (session.isPending) {
    return (
      <div className="tp-session-page">
        <StatusPanel title="Đang mở không gian làm việc" description="Đang kiểm tra phiên đăng nhập…" />
      </div>
    );
  }
  if (session.isError) {
    return (
      <div className="tp-session-page">
        <StatusPanel title="Chưa kết nối được hệ thống" description="Kiểm tra kết nối và thử tải lại trang." error={session.error}>
          <button onClick={() => session.refetch()}>Thử lại</button>
        </StatusPanel>
      </div>
    );
  }
  if (!session.data) {
    return (
      <div className="tp-session-page">
        <div className="tp-login-brand">{product.name} <span>Không gian làm việc</span></div>
        <StatusPanel title="Đăng nhập để tiếp tục" description="Mở các dự án được phân công và làm việc cùng phòng Kế hoạch Kinh doanh.">
          <a className="tp-primary-button" href={loginUrl()}>Đăng nhập</a>
        </StatusPanel>
      </div>
    );
  }

  return (
    <SessionContext.Provider value={session.data.data}>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<Navigate to="/projects" replace />} />
          <Route path="projects" element={<ProjectsPage />} />
          <Route path="projects/:projectId" element={<ProjectDetailPage />} />
          <Route path="*" element={<StatusPanel title="Không tìm thấy trang" description={`Chọn ${subsystems.projects.name} trong thanh điều hướng để tiếp tục.`} />} />
        </Route>
      </Routes>
    </SessionContext.Provider>
  );
}
