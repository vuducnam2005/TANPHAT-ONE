import { Navigate, Route, Routes } from 'react-router-dom';
import { AppShell } from './shell/AppShell';
import { ProjectsPage, ProjectDetailPage } from '../features/projects';
import { ContractDetailPage, ContractRevisionPage, ContractsPage } from '../features/contracts';
import { LoginPage } from '../features/auth';
import { useSession } from '../shared/api/hooks';
import { SessionContext } from '../shared/api/session';
import { StatusPanel } from '../shared/ui/StatusPanel';
import { subsystems } from '../shared/config/product';

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
    return <LoginPage />;
  }

  return (
    <SessionContext.Provider value={session.data.data}>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<Navigate to="/projects" replace />} />
          <Route path="projects" element={<ProjectsPage />} />
          <Route path="projects/:projectId" element={<ProjectDetailPage />} />
          <Route path="contracts" element={<ContractsPage />} />
          <Route path="contracts/:contractId" element={<ContractDetailPage />} />
          <Route path="contracts/:contractId/revisions/:revisionId" element={<ContractRevisionPage />} />
          <Route path="*" element={<StatusPanel title="Không tìm thấy trang" description={`Chọn ${subsystems.projects.name} hoặc ${subsystems.contracts.name} trong thanh điều hướng để tiếp tục.`} />} />
        </Route>
      </Routes>
    </SessionContext.Provider>
  );
}
