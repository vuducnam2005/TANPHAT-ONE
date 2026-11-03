import { expect, test, type Page } from '@playwright/test';

// Regression fixture for AUTH-002 L02: a signed-in business mutation receives 401.
// It is intentionally isolated from Odoo and uses the same returned-rework shape as
// the contract workflow mock. No runtime, database or credentials are used.
const session = {
  data: {
    user: { id: 5, name: 'Người soạn giả lập' },
    company: { id: 1, name: 'Công ty giả lập' },
    companies: [{ id: 1, name: 'Công ty giả lập' }],
    csrf_token: 'csrf-e2e', api_version: '1',
  },
  meta: { request_id: 'mutation-401' },
};

const revision = {
  id: 34, contract_id: 12, sequence: 1, kind: 'original', name: 'Bản hoàn lại giả lập', reference: null,
  review_state: 'returned', signature_status: 'unsigned', effectivity_status: 'not_effective',
  previous_revision_id: null, signed_date: null, effective_date: null, recorded_at: null,
  signature_authority_status: 'pending', legacy_unverified: false, line_count: 0,
  base_references: [], contract_version: 3,
  permissions: { financial_read: true, draft_edit: true, financial_draft_edit: true, submit: true, review_commercial: false },
  allowed_actions: ['begin_rework'], lines: [], submissions: [],
};

type Method = 'POST' | 'PATCH';

async function mockMutationError(page: Page, method: Method, status = 401) {
  let mutationCalls = 0;
  let revisionReads = 0;
  let authenticated = true;
  let currentRevision = {
    ...revision,
    kind: method === 'PATCH' ? 'amendment' : 'original',
    review_state: method === 'PATCH' ? 'draft' : 'returned',
    allowed_actions: method === 'PATCH' ? ['edit_draft'] : ['begin_rework'],
  };
  await page.route('**/api/v1/**', (route) => {
    const path = new URL(route.request().url()).pathname;
    if (route.request().method() !== 'GET') {
      expect(route.request().method()).toBe(method);
      mutationCalls += 1;
      if (status === 401) authenticated = false;
      const code = { 401: 'unauthenticated', 403: 'forbidden', 409: 'stale_version', 422: 'invalid_request', 503: 'service_unavailable' }[status];
      return route.fulfill({ status, json: {
        error: { code, message: 'Synthetic mutation error', details: null }, meta: session.meta,
      } });
    }
    if (path === '/api/v1/me') {
      return authenticated
        ? route.fulfill({ json: session })
        : route.fulfill({ status: 401, json: { error: { code: 'unauthenticated', message: 'Authentication required', details: null }, meta: session.meta } });
    }
    if (path === '/api/v1/contracts/12/revisions/34') {
      revisionReads += 1;
      return route.fulfill({ json: { data: currentRevision, meta: session.meta } });
    }
    if (path === '/api/v1/contracts/12') {
      return route.fulfill({ json: { data: { id: 12, code: 'HD-E2E-01', name: 'Hợp đồng giả lập', contract_type: 'owner', version: 3 }, meta: session.meta } });
    }
    return route.fulfill({ status: 404, json: { error: { code: 'not_found', message: 'Not found', details: null }, meta: session.meta } });
  });
  await page.route('**/web/session/authenticate', (route) => {
    authenticated = true;
    currentRevision = { ...currentRevision, name: 'Bản mới sau đăng nhập' };
    return route.fulfill({ json: { jsonrpc: '2.0', id: 'login', result: { uid: 5 } } });
  });
  return { mutationCalls: () => mutationCalls, revisionReads: () => revisionReads };
}

async function submitMutation(page: Page, method: Method) {
  const action = method === 'PATCH' ? 'Sửa bản nháp' : 'Mở lại để sửa';
  await page.getByRole('button', { name: action, exact: true }).click();
  const form = page.getByRole('form', { name: action });
  if (method === 'PATCH') {
    await form.getByLabel('Tên bản', { exact: true }).fill('Sửa trong phiên vừa hết hạn');
  } else {
    await form.getByLabel('Lý do mở lại để sửa').fill('Phiên hết hạn trong lúc gửi');
  }
  await form.getByRole('button', { name: method === 'PATCH' ? 'Lưu bản nháp' : action, exact: true }).click();
}

for (const method of ['POST', 'PATCH'] as const) {
  test(`${method} mutation 401 shows expired login, preserves deep link, and does not retry`, async ({ page }) => {
    const mock = await mockMutationError(page, method);
    const deepLink = '/work/contracts/12/revisions/34?view=review#rework';
    await page.goto(deepLink);
    await expect(page.getByRole('heading', { name: 'Bản hoàn lại giả lập' })).toBeVisible();
    const initialReads = mock.revisionReads();
    await submitMutation(page, method);

    await expect(page.locator('.tp-login-notice')).toHaveText('Phiên làm việc đã hết hạn. Vui lòng đăng nhập lại để tiếp tục.');
    await expect(page).toHaveURL(new URL(deepLink, 'http://127.0.0.1:4173').href);
    await expect(page.getByRole('heading', { name: 'Chào mừng trở lại.' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Bản hoàn lại giả lập' })).toHaveCount(0);
    expect(mock.mutationCalls()).toBe(1);

    await page.getByLabel('Tên đăng nhập', { exact: true }).fill('planner.e2e');
    await page.getByLabel('Mật khẩu', { exact: true }).fill('sample');
    await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'Bản mới sau đăng nhập' })).toBeVisible();
    await expect(page.locator('.tp-login-notice')).toHaveCount(0);
    await expect(page).toHaveURL(new URL(deepLink, 'http://127.0.0.1:4173').href);
    expect(mock.revisionReads()).toBeGreaterThan(initialReads);
    // Authentication must not replay the rejected user intent.
    expect(mock.mutationCalls()).toBe(1);
    expect(await page.evaluate(() => [localStorage.length, sessionStorage.length])).toEqual([0, 0]);
  });
}

for (const status of [403, 409, 422, 503]) {
  test(`mutation ${status} keeps the workspace and does not become session expiry`, async ({ page }) => {
    const mock = await mockMutationError(page, 'POST', status);
    await page.goto('/work/contracts/12/revisions/34');
    await expect(page.getByRole('heading', { name: 'Bản hoàn lại giả lập' })).toBeVisible();
    await submitMutation(page, 'POST');
    await expect(page.getByRole('alert')).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Bản hoàn lại giả lập' })).toBeVisible();
    await expect(page.locator('.tp-login-notice')).toHaveCount(0);
    await expect(page.getByRole('heading', { name: 'Chào mừng trở lại.' })).toHaveCount(0);
    expect(mock.mutationCalls()).toBe(1);
  });
}
