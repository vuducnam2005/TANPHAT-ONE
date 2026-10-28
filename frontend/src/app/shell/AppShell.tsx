import { NavLink, Outlet } from 'react-router-dom';
import { useCurrentSession } from '../../shared/api/session';
import { useQueryClient } from '@tanstack/react-query';
import { planningBusinessWorkspace as workspace } from '../workspaces/registry';
import { product } from '../../shared/config/product';

export function AppShell() {
  const session = useCurrentSession();
  const queryClient = useQueryClient();
  const { user, company } = session;

  return (
    <div className="tp-shell">
      <a className="tp-skip-link" href="#main-content">Đến nội dung chính</a>
      <aside className="tp-sidebar">
        <div className="tp-logo" aria-label={product.name}>
          <span className="tp-logo-mark">{product.mark}</span>
          <span><strong>{product.name}</strong><small>Quản trị doanh nghiệp</small></span>
        </div>
        <div className="tp-workspace-card">
          <span className="tp-eyebrow">Không gian hiện tại</span>
          <strong>{workspace.name}</strong>
          <span>{workspace.description}</span>
        </div>
        <nav className="tp-nav" aria-label="Điều hướng chính">
          <span className="tp-eyebrow">Làm việc</span>
          {workspace.routes.map((route) => (
            <NavLink key={route.path} to={route.path} end={route.path === '/'} className={({ isActive }) => `tp-nav-link${isActive ? ' is-active' : ''}`}>
              <span aria-hidden="true">{route.icon}</span>{route.label}
            </NavLink>
          ))}
        </nav>
        <div className="tp-sidebar-foot">Không gian Kế hoạch Kinh doanh</div>
      </aside>
      <main className="tp-main">
        <header className="tp-topbar">
          <div><span className="tp-eyebrow">{product.name} / {workspace.shortName}</span><h1>Không gian làm việc</h1></div>
          <div className="tp-identity">
            <span className="tp-avatar">{user?.name?.slice(0, 1) ?? '•'}</span>
            <span><strong>{user?.name ?? 'Đang tải phiên'}</strong><small>{company?.name ?? 'Công ty'}</small></span>
            <form action="/web/session/logout" method="post" onSubmit={() => queryClient.clear()}>
              <input type="hidden" name="csrf_token" value={session.csrf_token} />
              <input type="hidden" name="redirect" value="/work/" />
              <button className="tp-quiet-button" type="submit">Đăng xuất</button>
            </form>
          </div>
        </header>
        <div className="tp-content" id="main-content" tabIndex={-1}>
          {import.meta.env.DEV && <div className="tp-dev-banner">Môi trường phát triển · Dữ liệu thử nghiệm</div>}
          <Outlet />
        </div>
      </main>
    </div>
  );
}
