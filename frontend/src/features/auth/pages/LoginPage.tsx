import { useRef, useState, type FormEvent } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { api, LoginError } from '../../../shared/api/client';
import { loginUrl } from '../../../shared/api/session';
import { product } from '../../../shared/config/product';
import { BridgeIllustration } from '../components/BridgeIllustration';
import '@fontsource/be-vietnam-pro/400.css';
import '@fontsource/be-vietnam-pro/600.css';
import '@fontsource/be-vietnam-pro/700.css';
import '../styles/login.css';

function LoginIcon({ name }: { name: 'user' | 'lock' | 'eye' | 'eye-off' | 'arrow' | 'shield' }) {
  const paths = {
    user: <><circle cx="12" cy="8" r="3.5" /><path d="M5 21v-2a7 7 0 0 1 14 0v2" /></>,
    lock: <><rect x="5" y="10" width="14" height="11" rx="2" /><path d="M8 10V7a4 4 0 0 1 8 0v3m-4 5v2" /></>,
    eye: <><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z" /><circle cx="12" cy="12" r="3" /></>,
    'eye-off': <><path d="m3 3 18 18M10.6 5.1 12 5c6.5 0 10 7 10 7a20 20 0 0 1-3 3.8M6.1 6.1A23 23 0 0 0 2 12s3.5 7 10 7a13 13 0 0 0 5.7-1.4M10 10a3 3 0 0 0 4 4" /></>,
    arrow: <path d="M4 12h16m-6-6 6 6-6 6" />,
    shield: <><path d="M12 3 4 6v6c0 5 8 9 8 9s8-4 8-9V6Z" /><path d="m8.5 12 2.5 2.5 4.5-5" /></>,
  };
  return <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name]}</svg>;
}

export function LoginPage() {
  const queryClient = useQueryClient();
  const [showPassword, setShowPassword] = useState(false);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState('');
  const [requiresVerification, setRequiresVerification] = useState(false);
  const submitting = useRef(false);
  const passwordRef = useRef<HTMLInputElement>(null);
  const errorRef = useRef<HTMLDivElement>(null);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (submitting.current) return;
    const data = new FormData(event.currentTarget);
    const login = String(data.get('login') ?? '').trim();
    if (!login) {
      setError('Vui lòng nhập tên đăng nhập.');
      return;
    }
    submitting.current = true;
    setPending(true);
    setError('');
    setRequiresVerification(false);
    try {
      const result = await api.authenticate(login, String(data.get('password') ?? ''));
      // Keep neither credentials nor the returned Odoo session payload in browser storage.
      data.delete('password');
      if (passwordRef.current) passwordRef.current.value = '';
      setShowPassword(false);
      if (result.requiresVerification) {
        setRequiresVerification(true);
        return;
      }
      const session = await api.session();
      await queryClient.cancelQueries();
      queryClient.removeQueries({ predicate: (query) => query.queryKey[0] !== 'session' });
      queryClient.setQueryData(['session'], session);
    } catch (cause) {
      setError(cause instanceof LoginError ? cause.message : 'Chưa mở được phiên làm việc. Vui lòng thử đăng nhập lại.');
      requestAnimationFrame(() => errorRef.current?.focus());
    } finally {
      data.delete('password');
      if (passwordRef.current) passwordRef.current.value = '';
      setShowPassword(false);
      submitting.current = false;
      setPending(false);
    }
  }

  return (
    <main className="tp-login" aria-label="Đăng nhập TANPHAT ONE">
      <section className="tp-login-story" aria-labelledby="tp-login-story-title">
        <div className="tp-login-wordmark" aria-label={product.name}>
          <span className="tp-login-monogram" aria-hidden="true">
            <svg viewBox="0 0 40 40" fill="none"><path d="M5 11h30M20 11v23M7 28l7-11h12l7 11M8 28h24" stroke="currentColor" strokeWidth="2.4" /></svg>
          </span>
          <span><strong>{product.name}</strong><small>Không gian làm việc chung</small></span>
        </div>

        <div className="tp-login-story-copy">
          <h1 id="tp-login-story-title">Kết nối con người.<br />Kiến tạo công trình.</h1>
          <p>Từ kế hoạch đến công trường, cùng Tấn Phát làm việc trên một nền tảng thống nhất.</p>
        </div>

        <div className="tp-login-landscape"><BridgeIllustration /></div>

        <div className="tp-login-story-foot">
          <span className="tp-login-story-line" />
          <p>Cùng một tầm nhìn.<br /><strong>Cùng một nhịp tiến.</strong></p>
        </div>
      </section>

      <section className="tp-login-entry" aria-labelledby="tp-login-title">
        <div className="tp-login-entry-top"><span>Hệ thống quản trị doanh nghiệp</span><span className="tp-login-language" lang="vi">Tiếng Việt</span></div>

        <div className="tp-login-form-wrap">
          <div className="tp-login-welcome-icon" aria-hidden="true"><LoginIcon name="lock" /></div>
          <header className="tp-login-heading">
            <h2 id="tp-login-title">Chào mừng trở lại.</h2>
            <p>Đăng nhập để bắt đầu ngày làm việc.</p>
          </header>

          <form className="tp-login-form" onSubmit={handleSubmit} aria-busy={pending}>
            <div className="tp-login-field">
              <label htmlFor="tp-login-account">Tên đăng nhập</label>
              <div className="tp-login-input-wrap">
                <LoginIcon name="user" />
                <input id="tp-login-account" name="login" type="text" placeholder="Nhập tên đăng nhập của bạn" autoComplete="username" autoCapitalize="none" spellCheck={false} required readOnly={pending} aria-describedby={error ? 'tp-login-error' : undefined} />
              </div>
            </div>
            <div className="tp-login-field">
              <label htmlFor="tp-login-password">Mật khẩu</label>
              <div className="tp-login-input-wrap">
                <LoginIcon name="lock" />
                <input ref={passwordRef} id="tp-login-password" name="password" type={showPassword ? 'text' : 'password'} placeholder="Nhập mật khẩu" autoComplete="current-password" required readOnly={pending} aria-describedby={error ? 'tp-login-error' : undefined} />
                <button type="button" className="tp-login-reveal" aria-label={showPassword ? 'Ẩn mật khẩu' : 'Hiện mật khẩu'} aria-pressed={showPassword} onClick={() => setShowPassword(!showPassword)} disabled={pending}><LoginIcon name={showPassword ? 'eye-off' : 'eye'} /></button>
              </div>
            </div>

            {error && <div ref={errorRef} className="tp-login-error" id="tp-login-error" role="alert" tabIndex={-1}>{error}</div>}
            {requiresVerification && <div className="tp-login-verification" role="status">
              <strong>Tài khoản cần xác thực bổ sung.</strong>
              <p>Tiếp tục bằng phương thức bảo mật đã thiết lập, sau đó quay lại không gian làm việc.</p>
              <a href={loginUrl()}>Tiếp tục xác thực bảo mật</a>
            </div>}

            <button className="tp-login-submit" type="submit" disabled={pending}>
              <span>{pending ? 'Đang đăng nhập…' : 'Đăng nhập'}</span>
              {pending ? <span className="tp-login-spinner" aria-hidden="true" /> : <LoginIcon name="arrow" />}
            </button>
          </form>

          <div className="tp-login-help">
            <details>
              <summary>Cần hỗ trợ đăng nhập?</summary>
              <p>Nếu quên mật khẩu hoặc chưa có tài khoản, vui lòng liên hệ quản trị viên hệ thống Tấn Phát.</p>
              <a href={loginUrl()}>Dùng xác thực hai bước hoặc khóa bảo mật</a>
            </details>
          </div>

          <div className="tp-login-access-note"><LoginIcon name="shield" /><p>Một tài khoản cho toàn hệ thống.<br />Truy cập theo vai trò và phân quyền của bạn.</p></div>
        </div>

        <footer className="tp-login-footer"><span>© {new Date().getFullYear()} {product.name}</span><span>Kết nối để kiến tạo.</span></footer>
      </section>
    </main>
  );
}
