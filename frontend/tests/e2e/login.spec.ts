import { expect, test } from '@playwright/test';
import { readFileSync } from 'node:fs';

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
  const credentials = JSON.parse(readFileSync('../.local/dev-secrets.json', 'utf8')) as { planner: string };
  await page.goto('/work/');
  const account = page.getByLabel('Tên đăng nhập', { exact: true });
  const password = page.getByLabel('Mật khẩu', { exact: true });
  await account.fill('planner.dev');
  await password.fill('invalid-for-login-test');
  await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('Tên đăng nhập hoặc mật khẩu chưa đúng');
  await expect(page).toHaveURL(/\/work\/$/);
  await expect(password).toBeEmpty();
  expect((await page.request.get('/api/v1/me')).status()).toBe(401);
  await password.fill(credentials.planner);
  await password.press('Enter');
  await expect(page).toHaveURL(/\/work\/projects$/);
  await expect(page.getByRole('heading', { name: 'Dự án đang theo dõi' })).toBeVisible();
});

test('login preserves a protected deep link and its query', async ({ page }) => {
  const credentials = JSON.parse(readFileSync('../.local/dev-secrets.json', 'utf8')) as { planner: string };
  await page.goto('/work/projects?q=DEV-001');
  await page.getByLabel('Tên đăng nhập', { exact: true }).fill('planner.dev');
  await page.getByLabel('Mật khẩu', { exact: true }).fill(credentials.planner);
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
  await expect(page.getByText('Tài khoản cần xác thực bổ sung.')).toBeVisible();
  expect(calls).toBe(1);
  const href = await page.getByRole('link', { name: 'Tiếp tục xác thực bảo mật' }).getAttribute('href');
  expect(new URL(href!, 'http://test').searchParams.get('redirect')).toBe('/work/projects?q=DEV-001');
  await expect(page.getByLabel('Mật khẩu', { exact: true })).toBeEmpty();
  await expect(page.locator('.tp-project-card')).toHaveCount(0);
  expect((await page.request.get('/api/v1/me')).status()).toBe(401);
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
