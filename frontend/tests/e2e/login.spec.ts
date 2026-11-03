import { expect, test } from '@playwright/test';

// All five tests use synthetic HTTP responses; live authentication is covered by auth002-live.spec.ts.
test.beforeEach(async ({ page }) => {
  let signedIn = false;
  await page.route('**/api/v1/**', (route) => {
    const pathname = new URL(route.request().url()).pathname;
    if (!signedIn) return route.fulfill({ status: 401, json: { error: { code: 'unauthenticated', message: 'Authentication required', details: null }, meta: { request_id: 'login-mock' } } });
    if (pathname === '/api/v1/me') return route.fulfill({ json: { data: {
      user: { id: 7, name: 'Người lập giả lập' }, company: { id: 1, name: 'Công ty giả lập' },
      companies: [{ id: 1, name: 'Công ty giả lập' }], csrf_token: 'csrf-login-mock', api_version: '1',
    }, meta: { request_id: 'login-mock' } } });
    if (pathname === '/api/v1/projects') return route.fulfill({ json: { data: [{
      id: 1, code: 'DEV-001', name: 'Dự án giả lập', active: true,
      company: { id: 1, name: 'Công ty giả lập' }, department: null, customer: null, updated_at: '2026-10-29T00:00:00Z',
    }], meta: { request_id: 'login-mock', pagination: { limit: 20, offset: 0, has_more: false } } } });
    return route.fulfill({ status: 404, json: { error: { code: 'not_found', message: 'Not found', details: null }, meta: { request_id: 'login-mock' } } });
  });
  await page.route('**/web/session/authenticate', (route) => {
    const password = route.request().postDataJSON()?.params?.password;
    if (password === 'invalid-for-login-test') return route.fulfill({ json: { error: { data: {
      name: 'odoo.exceptions.AccessDenied', arguments: ['Access Denied'],
    } } } });
    signedIn = true;
    return route.fulfill({ json: { result: { uid: 7 } } });
  });
});

test('custom login has responsive layouts, password visibility and reduced motion', async ({ page }) => {
  await page.goto('/work/');
  await expect(page.getByRole('heading', { name: 'Chào mừng trở lại.' })).toBeVisible();
  await page.evaluate(() => document.fonts.ready);
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await expect(page.locator('.tp-bridge-road')).toHaveCSS('stroke-dashoffset', '0px');
  await expect(page.locator('.tp-bridge-road')).toHaveCSS('animation-name', 'none');
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.screenshot({ path: '../.local/login-desktop.png', fullPage: true });
  await page.setViewportSize({ width: 390, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: '../.local/login-mobile.png', fullPage: true });
  await page.setViewportSize({ width: 320, height: 740 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  const password = page.getByLabel('Mật khẩu', { exact: true });
  await password.fill('visibility-check');
  await page.getByRole('button', { name: 'Hiện mật khẩu' }).click();
  await expect(password).toHaveAttribute('type', 'text');
  await page.getByRole('button', { name: 'Ẩn mật khẩu' }).click();
  await expect(password).toHaveAttribute('type', 'password');
  await password.clear();
});

test('invalid credentials stay in TANPHAT ONE and allow correction with Enter', async ({ page }) => {
  await page.goto('/work/');
  const account = page.getByLabel('Tên đăng nhập', { exact: true });
  const password = page.getByLabel('Mật khẩu', { exact: true });
  await account.fill('planner.dev');
  await password.fill('invalid-for-login-test');
  await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('Tên đăng nhập hoặc mật khẩu chưa đúng');
  await expect(page).toHaveURL(/\/work\/$/);
  await expect(password).toBeEmpty();
  expect(await page.evaluate(async () => (await fetch('/api/v1/me')).status)).toBe(401);
  await password.fill('synthetic-login-password');
  await password.press('Enter');
  await expect(page).toHaveURL(/\/work\/projects$/);
  await expect(page.getByRole('heading', { name: 'Dự án đang theo dõi' })).toBeVisible();
});

test('login preserves a protected deep link and its query', async ({ page }) => {
  await page.goto('/work/projects?q=DEV-001');
  await page.getByLabel('Tên đăng nhập', { exact: true }).fill('planner.dev');
  await page.getByLabel('Mật khẩu', { exact: true }).fill('synthetic-login-password');
  await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click();
  await expect(page.locator('.tp-project-card')).toHaveCount(1);
  await expect(page).toHaveURL(/\/work\/projects\?q=DEV-001$/);
});

test('pending submit is locked and MFA requires an explicit handoff', async ({ page }) => {
  let release!: () => void;
  const gate = new Promise<void>((resolve) => { release = resolve; });
  let calls = 0;
  await page.route('**/web/session/authenticate', async (route) => {
    calls += 1;
    await gate;
    await route.fulfill({ json: { result: { uid: null } } });
  });
  await page.goto('/work/projects?q=DEV-001');
  await page.getByLabel('Tên đăng nhập', { exact: true }).fill('test.mfa');
  await page.getByLabel('Mật khẩu', { exact: true }).fill('sample');
  await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Đang đăng nhập…' })).toBeDisabled();
  release();
  await expect(page.getByText('Tài khoản cần xác thực hai lớp.')).toBeVisible();
  expect(calls).toBe(1);
  await expect(page.getByText('Mở ứng dụng xác thực trên điện thoại để lấy mã, rồi nhập ở bước tiếp theo.')).toBeVisible();
  const href = await page.getByRole('link', { name: 'Tiếp tục nhập mã xác thực' }).getAttribute('href');
  const handoff = new URL(href!, page.url());
  expect(handoff.origin).toBe(new URL(page.url()).origin);
  expect(handoff.pathname).toBe('/web/login/totp');
  expect(handoff.searchParams.get('redirect')).toBe('/work/projects?q=DEV-001');
  expect(handoff.searchParams.get('redirect')?.startsWith('/work/')).toBe(true);
  await page.getByText('Cần hỗ trợ đăng nhập?', { exact: true }).click();
  const native = new URL(await page.getByRole('link', { name: 'Dùng xác thực hai bước hoặc khóa bảo mật' }).getAttribute('href')!, page.url());
  expect(native.origin).toBe(new URL(page.url()).origin);
  expect(native.pathname).toBe('/web/login');
  await expect(page.getByLabel('Mật khẩu', { exact: true })).toBeEmpty();
  await expect(page.locator('.tp-project-card')).toHaveCount(0);
  expect(await page.evaluate(async () => (await fetch('/api/v1/me')).status)).toBe(401);
});

test('connection failure explains recovery without leaking server details', async ({ page }) => {
  await page.route('**/web/session/authenticate', (route) => route.fulfill({ status: 502, contentType: 'text/html', body: '<html>private gateway details</html>' }));
  await page.goto('/work/');
  await page.getByLabel('Tên đăng nhập', { exact: true }).fill('sample');
  await page.getByLabel('Mật khẩu', { exact: true }).fill('sample');
  await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('Chưa kết nối được hệ thống');
  await expect(page.getByRole('alert')).not.toContainText('private gateway');
  await expect(page.getByRole('button', { name: 'Đăng nhập', exact: true })).toBeEnabled();
});
