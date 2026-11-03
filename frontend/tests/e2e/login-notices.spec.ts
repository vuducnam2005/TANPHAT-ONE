import { expect, test, type Locator, type Page } from '@playwright/test';

// AUTH-002 slice 1 (T02–T04, T06, L03) against a mocked Odoo: no runtime, database or real account.
const copy = {
  cooldown: 'Tạm thời chưa thể đăng nhập vì đã thử sai nhiều lần. Vui lòng chờ ít phút rồi thử lại.',
  credentials: 'Tên đăng nhập hoặc mật khẩu chưa đúng. Vui lòng kiểm tra và thử lại.',
  expired: 'Phiên làm việc đã hết hạn. Vui lòng đăng nhập lại để tiếp tục.',
  signedOut: 'Bạn đã đăng xuất khỏi TANPHAT ONE.',
  capsLock: 'Caps Lock đang bật.',
};
const cooldownText = 'Too many login failures, please wait a bit before trying again.';

const meta = { request_id: 'e2e' };
const session = {
  data: {
    user: { id: 7, name: 'Người lập kế hoạch giả lập' },
    company: { id: 1, name: 'Công ty giả lập' },
    companies: [{ id: 1, name: 'Công ty giả lập' }],
    csrf_token: 'csrf-e2e',
    api_version: '1',
  },
  meta,
};
const project = {
  id: 1, code: 'DEV-001', name: 'Dự án giả lập', active: true,
  company: { id: 1, name: 'Công ty giả lập' }, department: null, customer: null, updated_at: '2026-10-29T00:00:00Z',
};
const unauthenticated = { error: { code: 'unauthenticated', message: 'Authentication required', details: null }, meta };

type MockOdoo = { me: boolean; projects: boolean; login: 'success' | 'cooldown' };

/** /me and /projects answer 401 while their flag is off; a successful login turns both on. */
async function mockOdoo(page: Page, state: MockOdoo = { me: false, projects: false, login: 'success' }) {
  await page.route('**/api/v1/**', (route) => {
    const path = new URL(route.request().url()).pathname;
    if (path === '/api/v1/me') {
      return state.me ? route.fulfill({ json: session }) : route.fulfill({ status: 401, json: unauthenticated });
    }
    if (path === '/api/v1/projects') {
      return state.projects
        ? route.fulfill({ json: { data: [project], meta: { ...meta, pagination: { limit: 20, offset: 0, has_more: false } } } })
        : route.fulfill({ status: 401, json: unauthenticated });
    }
    return route.fulfill({ status: 404, json: { error: { code: 'not_found', message: 'Not found', details: null }, meta } });
  });
  await page.route('**/web/session/authenticate', (route) => {
    if (state.login === 'cooldown') {
      return route.fulfill({ json: { jsonrpc: '2.0', id: 'login', error: { code: 200, message: 'Odoo Server Error', data: {
        name: 'odoo.exceptions.AccessDenied', message: cooldownText, arguments: [cooldownText], debug: '',
      } } } });
    }
    state.me = true;
    state.projects = true;
    return route.fulfill({ json: { jsonrpc: '2.0', id: 'login', result: { uid: 7 } } });
  });
  return state;
}

async function signIn(page: Page, password = 'sample') {
  await page.getByLabel('Tên đăng nhập', { exact: true }).fill('planner.e2e');
  await page.getByLabel('Mật khẩu', { exact: true }).fill(password);
  await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click();
}

async function expectNothingStored(page: Page) {
  expect(await page.evaluate(() => [localStorage.length, sessionStorage.length])).toEqual([0, 0]);
}

/** Playwright cannot toggle Caps Lock, so the key event carries the modifier state itself. */
async function capsLockKey(field: Locator, type: 'keydown' | 'keyup', on: boolean) {
  await field.evaluate((input, init) => {
    input.dispatchEvent(new KeyboardEvent(init.type, { key: 'a', bubbles: true, modifierCapsLock: init.on }));
  }, { type, on });
}

test('first visit opens on the account field with no notice and a plain language label (T04)', async ({ page }) => {
  await mockOdoo(page);
  await page.goto('/work/');
  await expect(page.getByRole('heading', { name: 'Chào mừng trở lại.' })).toBeVisible();
  await expect(page.getByLabel('Tên đăng nhập', { exact: true })).toBeFocused();
  await expect(page.locator('.tp-login-notice')).toHaveCount(0);
  await expect(page.getByText(copy.expired)).toHaveCount(0);
  await expect(page.getByText(copy.signedOut)).toHaveCount(0);
  const language = page.locator('.tp-login-language');
  await expect(language).toHaveCSS('border-left-style', 'none');
  expect(await language.evaluate((label) => label.closest('a, button, select, [role="button"], [tabindex]') === null)).toBe(true);
});

test('a login cooldown is not reported as a wrong password and clears the password (T02)', async ({ page }) => {
  const state = await mockOdoo(page);
  state.login = 'cooldown';
  await page.goto('/work/');
  await signIn(page, 'cooldown-check');
  const alert = page.getByRole('alert');
  await expect(alert).toHaveText(copy.cooldown);
  await expect(page.getByText(copy.credentials)).toHaveCount(0);
  await expect(page.getByText(cooldownText)).toHaveCount(0);
  await expect(alert).toBeFocused();
  await expect(page.getByLabel('Mật khẩu', { exact: true })).toBeEmpty();
  expect(page.url()).not.toContain('cooldown-check');
  await expectNothingStored(page);
});

test('a rejected request on the project page asks to sign in again and returns there (T03)', async ({ page }) => {
  const state = await mockOdoo(page, { me: true, projects: true, login: 'success' });
  await page.goto('/work/projects?q=DEV-001');
  await expect(page.locator('.tp-project-card')).toHaveCount(1);
  state.me = false;
  state.projects = false;
  await page.getByRole('button', { name: 'Làm mới', exact: true }).click();
  await expect(page.locator('.tp-login-notice')).toHaveText(copy.expired);
  await expect(page.locator('.tp-project-card')).toHaveCount(0);
  await expect(page).toHaveURL(/\/work\/projects\?q=DEV-001$/);
  await expectNothingStored(page);
  await signIn(page);
  await expect(page.locator('.tp-project-card')).toHaveCount(1);
  await expect(page).toHaveURL(/\/work\/projects\?q=DEV-001$/);
  await expect(page.locator('.tp-login-notice')).toHaveCount(0);
});

test('an expired session found on refocus shows the notice until the page reloads (T03, L02)', async ({ page }) => {
  const state = await mockOdoo(page, { me: true, projects: true, login: 'success' });
  await page.goto('/work/projects');
  await expect(page.locator('.tp-project-card')).toHaveCount(1);
  // Only /me rejects the session; the project list still answers.
  state.me = false;
  await page.evaluate(() => window.dispatchEvent(new Event('visibilitychange')));
  await expect(page.locator('.tp-login-notice')).toHaveText(copy.expired);
  await page.reload();
  await expect(page.getByRole('heading', { name: 'Chào mừng trở lại.' })).toBeVisible();
  await expect(page.locator('.tp-login-notice')).toHaveCount(0);
  await expectNothingStored(page);
});

test('logout notice shows once and leaves no marker in the address bar or history (L03)', async ({ page }) => {
  await mockOdoo(page);
  await page.goto('/work/');
  const entries = await page.evaluate(() => history.length);
  await page.goto('/work/?signed_out=1');
  await expect(page.locator('.tp-login-notice')).toHaveText(copy.signedOut);
  await expect(page).toHaveURL(/\/work\/$/);
  expect(await page.evaluate(() => history.length)).toBe(entries + 1);
  await expect(page.getByLabel('Tên đăng nhập', { exact: true })).toBeFocused();
  await expect(page.getByText(copy.expired)).toHaveCount(0);
  await page.reload();
  await expect(page.getByRole('heading', { name: 'Chào mừng trở lại.' })).toBeVisible();
  await expect(page.locator('.tp-login-notice')).toHaveCount(0);
  await expectNothingStored(page);
});

test('logout notice keeps the rest of a deep link and goes away on sign-in (L03)', async ({ page }) => {
  await mockOdoo(page);
  await page.goto('/work/projects?q=DEV-001&signed_out=1');
  await expect(page.locator('.tp-login-notice')).toHaveText(copy.signedOut);
  await expect(page).toHaveURL(/\/work\/projects\?q=DEV-001$/);
  await page.setViewportSize({ width: 320, height: 740 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await signIn(page);
  await expect(page.locator('.tp-project-card')).toHaveCount(1);
  await expect(page).toHaveURL(/\/work\/projects\?q=DEV-001$/);
});

test('Caps Lock warning follows the key state in the password field only (T06)', async ({ page }) => {
  await mockOdoo(page);
  await page.goto('/work/');
  const account = page.getByLabel('Tên đăng nhập', { exact: true });
  const password = page.getByLabel('Mật khẩu', { exact: true });
  const warning = page.locator('.tp-login-caps');
  await expect(warning).toHaveAttribute('aria-live', 'polite');
  await expect(warning).toBeEmpty();

  await capsLockKey(account, 'keydown', true);
  await expect(warning).toBeEmpty();
  await password.focus();
  await capsLockKey(password, 'keydown', true);
  await expect(warning).toHaveText(copy.capsLock);
  await capsLockKey(password, 'keyup', false);
  await expect(warning).toBeEmpty();
  await capsLockKey(password, 'keydown', true);
  await expect(warning).toHaveText(copy.capsLock);
  await account.focus();
  await expect(warning).toBeEmpty();

  const secret = 'Sentinel-Caps-7319';
  await password.fill(secret);
  await capsLockKey(password, 'keydown', true);
  await expect(warning).toHaveText(copy.capsLock);
  await page.setViewportSize({ width: 320, height: 740 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  const pageText =() => page.evaluate(() => document.documentElement.outerHTML + document.body.innerText);
  expect(await pageText()).not.toContain(secret);
  await page.getByRole('button', { name: 'Hiện mật khẩu' }).click();
  await expect(password).toHaveAttribute('type', 'text');
  expect(await pageText()).not.toContain(secret);
  await expect(password).toHaveValue(secret);
  await password.clear();
  await expectNothingStored(page);
});
