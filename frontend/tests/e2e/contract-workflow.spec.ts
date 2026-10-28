import { expect, test, type Page, type Request } from '@playwright/test';

// CTR-002a screens against a mocked /api/v1 only: no Odoo runtime, database or credentials are used.
const IDEMPOTENCY_KEY = /^[A-Za-z0-9_.:-]{8,128}$/;

type Json = Record<string, unknown>;
interface Sent { method: string; path: string; body: Json; csrf?: string; key?: string }

function revision(overrides: Json = {}): Json {
  return {
    id: 34, contract_id: 12, sequence: 1, kind: 'original', name: 'Bản gốc (giả lập)', reference: null,
    review_state: 'draft', signature_status: 'unsigned', effectivity_status: 'not_effective', previous_revision_id: null,
    signed_date: null, effective_date: null, recorded_at: null, signature_authority_status: 'pending',
    legacy_unverified: false, line_count: 2, base_references: [], contract_version: 3,
    permissions: { financial_read: true, draft_edit: true, financial_draft_edit: true, submit: true, review_commercial: false },
    allowed_actions: ['edit_draft', 'submit_review'],
    lines: [
      { id: 1, sequence: 10, scope_key: 'L1', name: 'Khảo sát', work_item: null, change_kind: 'original', previous_line_id: null,
        amount: { value: '100000000', currency: 'VND', status: 'confirmed', tax_basis: 'excluding_tax' } },
      { id: 2, sequence: 20, scope_key: 'L2', name: 'Thiết kế', work_item: null, change_kind: 'original', previous_line_id: null,
        amount: { value: '50000000', currency: 'VND', status: 'confirmed', tax_basis: 'excluding_tax' } },
    ],
    total: { value: '150000000', currency: 'VND', status: 'confirmed', tax_basis: 'excluding_tax' },
    submissions: [],
    ...overrides,
  };
}

const withoutMoney = (data: Json): Json => ({
  ...data,
  permissions: { financial_read: false, draft_edit: true, financial_draft_edit: false, submit: false, review_commercial: false },
  allowed_actions: ['edit_draft'],
  lines: (data.lines as Json[]).map(({ amount: _amount, ...line }) => line),
  total: undefined,
});

/** Serves a stateful fake revision; `write` decides each write's response. */
async function mockApi(page: Page, state: { revision: Json }, write: (sent: Sent, call: number) => { status: number; body: Json }) {
  const sent: Sent[] = [];
  let reads = 0;
  await page.route('**/api/v1/**', async (route) => {
    const request: Request = route.request();
    const url = new URL(request.url());
    const meta = { request_id: 'e2e' };
    if (request.method() === 'GET') {
      if (url.pathname === '/api/v1/me') {
        return route.fulfill({ json: { data: {
          user: { id: 5, name: 'Người soạn giả lập' }, company: { id: 1, name: 'Công ty giả lập' },
          companies: [{ id: 1, name: 'Công ty giả lập' }], csrf_token: 'csrf-e2e', api_version: '1',
        }, meta } });
      }
      if (url.pathname === '/api/v1/contracts/12/revisions/34') {
        reads += 1;
        return route.fulfill({ json: { data: state.revision, meta } });
      }
      if (url.pathname === '/api/v1/contracts/12') {
        return route.fulfill({ json: { data: { id: 12, code: 'HD-E2E-01', name: 'Hợp đồng giả lập', contract_type: 'owner', version: state.revision.contract_version }, meta } });
      }
      if (url.pathname === '/api/v1/contracts/12/reviewers') {
        return route.fulfill({ json: { data: [{ id: 9, name: 'Người rà soát giả lập' }], meta } });
      }
      return route.fulfill({ status: 404, json: { error: { code: 'not_found', message: 'Not found', details: null }, meta } });
    }
    const headers = request.headers();
    const entry: Sent = {
      method: request.method(), path: url.pathname, body: request.postDataJSON() as Json,
      csrf: headers['x-csrf-token'], key: headers['idempotency-key'],
    };
    sent.push(entry);
    const response = write(entry, sent.length);
    return route.fulfill({ status: response.status, json: { ...response.body, meta } });
  });
  return { sent, reads: () => reads };
}

const ok = (state: { revision: Json }, changes: Json) => {
  state.revision = { ...state.revision, ...changes, contract_version: (state.revision.contract_version as number) + 1 };
  return { status: 200, body: { data: {
    contract_id: 12, revision_id: 34, submission_id: null, version: state.revision.contract_version,
    review_state: state.revision.review_state, replayed: false,
  } } };
};

test('editor saves a draft with amounts as decimal strings, then submits once despite a retry', async ({ page }) => {
  const state = { revision: revision() };
  const api = await mockApi(page, state, (sent, call) => {
    if (sent.method === 'PATCH') return ok(state, { name: 'Bản gốc đã sửa' });
    if (call === 2) return { status: 503, body: { error: { code: 'service_unavailable', message: 'Hệ thống tạm thời gián đoạn.', details: null } } };
    return ok(state, {
      review_state: 'in_review', allowed_actions: [],
      submissions: [{
        id: 1, sequence: 1, submitted_by: { id: 5, name: 'Người soạn giả lập' }, submitted_at: '2026-10-28 08:00:00',
        reviewer: { id: 9, name: 'Người rà soát giả lập' }, contract_version: 4, fix_summary: null, outcome: 'pending',
        returned_by: null, returned_at: null, return_reason: null, return_issues: [], rework_started_by: null,
        rework_started_at: null, rework_reason: null, payload_sha256: 'e2e',
      }],
    });
  });
  await page.goto('/work/contracts/12/revisions/34');
  const actions = page.getByRole('group', { name: 'Thao tác với bản hợp đồng' });
  await expect(actions.getByRole('button')).toHaveText(['Sửa bản nháp', 'Gửi rà soát']);

  await actions.getByRole('button', { name: 'Sửa bản nháp' }).click();
  const editor = page.getByRole('form', { name: 'Sửa bản nháp' });
  await expect(editor.getByLabel('Số hợp đồng')).toHaveValue('HD-E2E-01');
  await editor.getByLabel('Tên bản').fill('Bản gốc đã sửa');
  await editor.getByLabel('Số tiền dòng 1').fill('120000000');
  await editor.getByRole('button', { name: 'Thêm dòng phạm vi' }).click();
  await editor.getByLabel('Mã phạm vi dòng 3').fill('L3');
  await editor.getByLabel('Nội dung dòng 3').fill('Giám sát tác giả');
  await expect(editor.getByLabel('Số tiền dòng 3')).toBeDisabled();
  await editor.getByRole('button', { name: 'Lưu bản nháp' }).click();
  await expect(page.getByRole('status').filter({ hasText: 'Đã lưu bản nháp.' })).toBeVisible();

  const patch = api.sent[0];
  expect(patch).toMatchObject({ method: 'PATCH', path: '/api/v1/contracts/12/revisions/34', csrf: 'csrf-e2e' });
  expect(patch.key).toMatch(IDEMPOTENCY_KEY);
  expect(patch.body).toEqual({
    expected_version: 3,
    revision: { name: 'Bản gốc đã sửa' },
    lines: [
      { scope_key: 'L1', name: 'Khảo sát', amount: { state: 'confirmed', value: '120000000', tax_basis: 'excluding_tax' } },
      { scope_key: 'L2', name: 'Thiết kế' },
      { scope_key: 'L3', name: 'Giám sát tác giả', amount: { state: 'unconfirmed', value: null, tax_basis: 'unknown' } },
    ],
  });

  await actions.getByRole('button', { name: 'Gửi rà soát' }).click();
  const submit = page.getByRole('form', { name: 'Gửi rà soát' });
  await submit.getByLabel('Người rà soát').selectOption('9');
  await submit.getByRole('button', { name: 'Gửi rà soát' }).click();
  await expect(submit.getByRole('alert')).toContainText('Hệ thống tạm thời gián đoạn.');
  await submit.getByRole('button', { name: 'Gửi rà soát' }).click();
  await expect(page.getByRole('status').filter({ hasText: 'Đã gửi rà soát.' })).toBeVisible();
  const [failed, retried] = api.sent.slice(1);
  expect(failed.body).toEqual({ expected_version: 4, reviewer_id: 9 });
  expect(retried.key).toBe(failed.key);
  expect(retried.key).not.toBe(patch.key);
  await expect(actions).toHaveCount(0);
  await expect(page.getByText('Lần gửi 1')).toBeVisible();
  await expect(page.getByText('Đang chờ rà soát')).toBeVisible();
});

test('metadata editor never sends amounts and must reload after a concurrent change', async ({ page }) => {
  const state = { revision: withoutMoney(revision()) };
  const api = await mockApi(page, state, () => ({
    status: 409, body: { error: { code: 'stale_version', message: 'Changed', details: { current_version: 4 } } },
  }));
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/work/contracts/12/revisions/34');
  await page.getByRole('button', { name: 'Sửa bản nháp' }).click();
  const editor = page.getByRole('form', { name: 'Sửa bản nháp' });
  await expect(editor.getByText('giá trị đã ghi nhận được giữ nguyên')).toBeVisible();
  await expect(editor.getByLabel('Số tiền dòng 1')).toHaveCount(0);
  await expect(page.locator('.tp-money')).toHaveCount(0);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);

  await editor.getByLabel('Nội dung dòng 1').fill('Khảo sát địa hình');
  await editor.getByRole('button', { name: 'Lưu bản nháp' }).click();
  await expect(editor.getByRole('alert')).toContainText('Hồ sơ vừa được cập nhật ở nơi khác');
  expect(api.sent[0].body).toEqual({
    expected_version: 3, lines: [{ scope_key: 'L1', name: 'Khảo sát địa hình' }, { scope_key: 'L2', name: 'Thiết kế' }],
  });

  const readsBefore = api.reads();
  state.revision = { ...state.revision, contract_version: 4, name: 'Bản gốc (người khác vừa sửa)' };
  await editor.getByRole('button', { name: 'Tải lại bản mới nhất' }).click();
  await expect(page.getByRole('form', { name: 'Sửa bản nháp' }).getByLabel('Tên bản')).toHaveValue('Bản gốc (người khác vừa sửa)');
  await expect(page.getByRole('form', { name: 'Sửa bản nháp' }).getByLabel('Nội dung dòng 1')).toHaveValue('Khảo sát');
  expect(api.reads()).toBeGreaterThan(readsBefore);
});

test('reviewer returns with a reason and scope-level issues', async ({ page }) => {
  const pending = {
    id: 1, sequence: 1, submitted_by: { id: 5, name: 'Người soạn giả lập' }, submitted_at: '2026-10-28 08:00:00',
    reviewer: { id: 9, name: 'Người rà soát giả lập' }, contract_version: 4, fix_summary: null, outcome: 'pending',
    returned_by: null, returned_at: null, return_reason: null, return_issues: [], rework_started_by: null,
    rework_started_at: null, rework_reason: null, payload_sha256: 'e2e',
  };
  const state = { revision: revision({
    review_state: 'in_review', contract_version: 4, allowed_actions: ['return_review'], submissions: [pending],
    permissions: { financial_read: true, draft_edit: false, financial_draft_edit: false, submit: false, review_commercial: true },
  }) };
  const api = await mockApi(page, state, () => ok(state, {
    review_state: 'returned', allowed_actions: [],
    submissions: [{ ...pending, outcome: 'returned', return_reason: 'Tách giai đoạn thiết kế', return_issues: [{ scope_key: 'L2', note: 'Tách hai giai đoạn' }] }],
  }));
  await page.goto('/work/contracts/12/revisions/34');
  await page.getByRole('button', { name: 'Trả lại để sửa' }).click();
  const form = page.getByRole('form', { name: 'Trả lại để sửa' });
  await form.getByRole('button', { name: 'Trả lại để sửa' }).click();
  expect(api.sent).toHaveLength(0);
  await form.getByLabel('Lý do trả lại').fill('Tách giai đoạn thiết kế');
  await form.getByRole('button', { name: 'Thêm ý kiến' }).click();
  await form.getByLabel('Dòng phạm vi').selectOption('L2');
  await form.getByLabel('Nội dung').fill('Tách hai giai đoạn');
  await form.getByRole('button', { name: 'Trả lại để sửa' }).click();
  await expect(page.getByRole('status').filter({ hasText: 'Đã trả lại bản hợp đồng để sửa.' })).toBeVisible();
  expect(api.sent[0]).toMatchObject({ method: 'POST', path: '/api/v1/contracts/12/revisions/34/return', csrf: 'csrf-e2e' });
  expect(api.sent[0].body).toEqual({ expected_version: 4, reason: 'Tách giai đoạn thiết kế', issues: [{ scope_key: 'L2', note: 'Tách hai giai đoạn' }] });
  await expect(page.getByText('Đã trả lại để sửa')).toBeVisible();
  await expect(page.getByText('Tách hai giai đoạn')).toBeVisible();
});
