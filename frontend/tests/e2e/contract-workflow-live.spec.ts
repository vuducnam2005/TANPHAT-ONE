import { expect, test, type Browser, type BrowserContext, type Page } from '@playwright/test';
import { existsSync, readFileSync } from 'node:fs';
import path from 'node:path';

const enabled = process.env.TP_CTR002A_LIVE === '1';
const targetDatabase = process.env.VITE_ODOO_DATABASE?.trim() ?? '';
const odooOrigin = process.env.TP_ODOO_ORIGIN?.trim() ?? '';
const credentialsPath = path.resolve(process.cwd(), '../.local/ctr002a-verify/credentials.json');

type ActorCredentials = { login: string; password: string; name?: string };
type LiveConfig = {
  database: string;
  origin: string;
  projectCode: string;
  editor: ActorCredentials;
  reviewer: ActorCredentials;
};
type RawLiveConfig = {
  database: string;
  origin: string;
  project_id: number;
  actors: { editor: ActorCredentials; reviewer: ActorCredentials; reader?: ActorCredentials };
};
type ApiEnvelope<T> = { data: T; meta?: { request_id?: string } };

// This suite is deliberately inert during the normal mocked E2E run.
if (enabled) {
  if (!targetDatabase) throw new Error('Live CTR-002a E2E requires VITE_ODOO_DATABASE.');
  if (targetDatabase === 'tp_tanphat_dev') throw new Error('Refusing live CTR-002a E2E against tp_tanphat_dev.');
  if (targetDatabase !== 'tp_tanphat_ctr002a_verify') {
    throw new Error('Live CTR-002a E2E is restricted to tp_tanphat_ctr002a_verify.');
  }
  if (!odooOrigin || odooOrigin !== 'http://127.0.0.1:18089') {
    throw new Error('Live CTR-002a E2E requires TP_ODOO_ORIGIN on the isolated port 18089.');
  }
  if (!existsSync(credentialsPath)) {
    throw new Error('Live CTR-002a E2E credentials are missing from .local/ctr002a-verify/credentials.json.');
  }
}

const rawConfig: RawLiveConfig | null = enabled
  ? JSON.parse(readFileSync(credentialsPath, 'utf8')) as RawLiveConfig
  : null;
const liveConfig: LiveConfig | null = rawConfig && {
  database: rawConfig.database, origin: rawConfig.origin, projectCode: 'CTR-VERIFY',
  editor: rawConfig.actors.editor, reviewer: rawConfig.actors.reviewer,
};

if (enabled && (liveConfig?.database !== targetDatabase || liveConfig.origin !== odooOrigin)) {
  throw new Error('Live CTR-002a credentials config database does not match the selected target.');
}
if (enabled && (!liveConfig?.projectCode || !liveConfig.editor?.login || !liveConfig.editor.password ||
  !liveConfig.reviewer?.login || !liveConfig.reviewer.password ||
  liveConfig.editor.login === liveConfig.reviewer.login)) {
  throw new Error('Live CTR-002a credentials config must contain distinct editor and reviewer fixture accounts.');
}

const nonce = () => `${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;

async function signIn(page: Page, actor: ActorCredentials) {
  await page.goto('/work/');
  await expect(page.getByRole('heading', { name: 'Chào mừng trở lại.' })).toBeVisible();
  await page.locator('input[name="login"]').fill(actor.login);
  await page.locator('input[name="password"]').fill(actor.password);
  await page.locator('button[type="submit"]').click();
  await expect(page).toHaveURL(/\/work\/projects/);
}

async function openContracts(page: Page) {
  await page.getByRole('link', { name: 'TP Contracts' }).click();
  await expect(page.getByRole('heading', { name: 'Hồ sơ hợp đồng' })).toBeVisible();
}

async function createDraft(page: Page, label: string) {
  const config = liveConfig!;
  const code = `CTR-E2E-${label}-${nonce()}`.slice(0, 64);
  await openContracts(page);
  await page.getByRole('button', { name: 'Tạo hợp đồng nháp' }).click();
  const form = page.getByRole('region', { name: 'Tạo hợp đồng nháp', exact: true }).locator('form');
  const project = form.getByLabel('Dự án');
  await expect(project.locator('option').filter({ hasText: config.projectCode })).toHaveCount(1);
  const projectOptions = await project.locator('option').allTextContents();
  const projectLabel = projectOptions.find((label) => label.includes(config.projectCode));
  if (!projectLabel) throw new Error(`Project ${config.projectCode} was not present in the fixture project list.`);
  await project.selectOption({ label: projectLabel });
  await form.getByLabel('Số hợp đồng').fill(code);
  await form.getByLabel('Tên hợp đồng').fill(`Hồ sơ kiểm tra CTR-002a ${label}`);
  await form.getByLabel('Đơn vị tiền tệ').fill('VND');
  await form.getByRole('button', { name: 'Tạo bản nháp' }).click();
  await expect(page).toHaveURL(/\/work\/contracts\/\d+\/revisions\/\d+/);
  return { code, page, revisionUrl: page.url() };
}

async function editDraft(page: Page, name: string, addLine = true) {
  await page.getByRole('button', { name: 'Sửa bản nháp' }).click();
  const form = page.getByRole('form', { name: 'Sửa bản nháp' });
  await form.getByLabel('Tên bản').fill(name);
  if (addLine) await form.getByRole('button', { name: 'Thêm dòng phạm vi' }).click();
  const lineIndex = await form.getByLabel(/Mã phạm vi dòng/).count();
  const lineCode = form.getByLabel(/Mã phạm vi dòng/).nth(lineIndex - 1);
  const lineName = form.getByLabel(/Nội dung dòng/).nth(lineIndex - 1);
  if (addLine) await lineCode.fill('TEST-01');
  await lineName.fill(addLine ? 'Phạm vi kiểm tra giả lập' : 'Phạm vi kiểm tra giả lập sau khi làm rõ');
  const state = form.getByLabel(/Trạng thái giá trị dòng/).nth(lineIndex - 1);
  await state.selectOption('confirmed');
  await form.getByLabel(/Số tiền dòng/).last().fill('1000');
  await form.getByLabel(/Cơ sở thuế dòng/).last().selectOption('excluding_tax');
  await form.getByRole('button', { name: 'Lưu bản nháp' }).click();
  await expect(page.getByRole('status').filter({ hasText: 'Đã lưu bản nháp.' })).toBeVisible();
}

async function submitForReview(page: Page, reviewerName?: string) {
  await page.getByRole('button', { name: 'Gửi rà soát' }).click();
  const form = page.getByRole('form', { name: 'Gửi rà soát' });
  const reviewerSelect = form.getByLabel('Người rà soát');
  await expect(reviewerSelect.locator('option').nth(1)).toHaveCount(1);
  const options = await reviewerSelect.locator('option').allTextContents();
  expect(options.length).toBeGreaterThan(1);
  if (reviewerName) expect(options.join('\n')).toContain(reviewerName);
  await reviewerSelect.selectOption({ label: reviewerName! });
  await form.getByRole('button', { name: 'Gửi rà soát' }).click();
  await expect(page.getByRole('status').filter({ hasText: 'Đã gửi rà soát.' })).toBeVisible();
}

async function returnToSender(page: Page) {
  await page.reload();
  await expect(page.getByRole('button', { name: 'Trả lại để sửa' })).toBeVisible();
  await page.getByRole('button', { name: 'Trả lại để sửa' }).click();
  const form = page.getByRole('form', { name: 'Trả lại để sửa' });
  await form.getByLabel('Lý do trả lại').fill('Kiểm tra giả lập: bổ sung mô tả phạm vi.');
  await form.getByRole('button', { name: 'Trả lại để sửa' }).click();
  await expect(page.getByRole('status').filter({ hasText: 'Đã trả lại bản hợp đồng để sửa.' })).toBeVisible();
}

async function beginReworkAndResubmit(page: Page, reviewerName: string) {
  await page.reload();
  await page.getByRole('button', { name: 'Mở lại để sửa' }).click();
  const rework = page.getByRole('form', { name: 'Mở lại để sửa' });
  await rework.getByLabel('Lý do mở lại').fill('Sửa theo ý kiến giả lập.');
  await rework.getByRole('button', { name: 'Mở lại để sửa' }).click();
  await expect(page.getByRole('status').filter({ hasText: 'Đã mở lại bản nháp để sửa.' })).toBeVisible();
  await editDraft(page, 'Bản nháp sau khi sửa', false);
  await page.getByRole('button', { name: 'Gửi rà soát' }).click();
  const submit = page.getByRole('form', { name: 'Gửi rà soát' });
  await submit.getByLabel('Người rà soát').selectOption({ label: reviewerName });
  await submit.getByLabel('Nội dung đã sửa so với lần bị trả lại').fill('Đã bổ sung mô tả phạm vi.');
  await submit.getByRole('button', { name: 'Gửi rà soát' }).click();
  await expect(page.getByRole('status').filter({ hasText: 'Đã gửi rà soát.' })).toBeVisible();
  await expect(page.getByText('Lần gửi 2')).toBeVisible();
}

async function createContextPage(browser: Browser): Promise<{ context: BrowserContext; page: Page }> {
  const context = await browser.newContext({ baseURL: 'http://127.0.0.1:4173' });
  return { context, page: await context.newPage() };
}

async function me(page: Page) {
  const response = await page.request.get('/api/v1/me');
  expect(response.ok()).toBeTruthy();
  return await response.json() as ApiEnvelope<{ csrf_token: string; user: { id: number; name: string } }>;
}

async function workflowPost<T>(page: Page, url: string, csrf: string, body: object, key: string) {
  return page.request.post(url, {
    data: body,
    headers: {
      Origin: 'http://127.0.0.1:4173',
      'X-CSRF-Token': csrf,
      'Idempotency-Key': key,
    },
  }) as Promise<import('@playwright/test').APIResponse>;
}

test.skip(!enabled, 'Set TP_CTR002A_LIVE=1 to run against the isolated Odoo verification instance.');

test('live Odoo: draft, edit, submit, return, rework, and resubmit with distinct actors', async ({ browser, page }) => {
  const config = liveConfig!;
  const editor = config.editor;
  const reviewer = config.reviewer;
  await signIn(page, editor);
  const created = await createDraft(page, 'FLOW');
  await editDraft(page, 'Bản nháp lần đầu');

  await page.getByRole('button', { name: 'Gửi rà soát' }).click();
  const sendForm = page.getByRole('form', { name: 'Gửi rà soát' });
  await expect(sendForm.getByLabel('Người rà soát').locator('option').nth(1)).toHaveCount(1);
  const reviewerOptions = await sendForm.getByLabel('Người rà soát').locator('option').allTextContents();
  expect(reviewerOptions).not.toContain(editor.name ?? editor.login);
  expect(reviewerOptions.join('\n')).toContain(reviewer.name ?? reviewer.login);
  await sendForm.getByLabel('Người rà soát').selectOption({ label: reviewer.name ?? reviewer.login });
  await sendForm.getByRole('button', { name: 'Gửi rà soát' }).click();
  await expect(page.getByRole('status').filter({ hasText: 'Đã gửi rà soát.' })).toBeVisible();
  await expect(page.getByText('Lần gửi 1')).toBeVisible();

  const reviewerSession = await createContextPage(browser);
  try {
    await signIn(reviewerSession.page, reviewer);
    await reviewerSession.page.goto(created.revisionUrl);
    await expect(reviewerSession.page.getByText('Đang chờ rà soát')).toBeVisible();
    await returnToSender(reviewerSession.page);
  } finally {
    await reviewerSession.context.close();
  }

  await beginReworkAndResubmit(page, reviewer.name ?? reviewer.login);
  const submissions = page.locator('section[aria-labelledby="submissions-title"] li');
  await expect(submissions).toHaveCount(2);
  await expect(submissions.nth(1)).toContainText('Đã trả lại để sửa');
  await expect(submissions.nth(0)).toContainText(reviewer.name ?? reviewer.login);
  await expect(page.getByRole('heading', { name: 'Kết quả BASE' })).toBeVisible();
});

test('live API race: two returns against one version produce one mutation', async ({ browser }) => {
  test.skip(process.env.TP_CTR002A_RACE !== '1', 'Set TP_CTR002A_RACE=1 to include the real HTTP race check.');
  const config = liveConfig!;
  const editorSession = await createContextPage(browser);
  const reviewerSession = await createContextPage(browser);
  try {
    await signIn(editorSession.page, config.editor);
    const created = await createDraft(editorSession.page, 'RACE');
    await editDraft(editorSession.page, 'Bản nháp race');
    await submitForReview(editorSession.page, config.reviewer.name ?? config.reviewer.login);

    await signIn(reviewerSession.page, config.reviewer);
    const contractId = Number(new URL(created.revisionUrl).pathname.split('/')[3]);
    const revisionId = Number(new URL(created.revisionUrl).pathname.split('/').at(-1));
    const session = await me(reviewerSession.page);
    const revisionResponse = await reviewerSession.page.request.get(`/api/v1/contracts/${contractId}/revisions/${revisionId}`);
    expect(revisionResponse.ok()).toBeTruthy();
    const revision = (await revisionResponse.json() as ApiEnvelope<{ contract_version: number }>).data;
    const route = `/api/v1/contracts/${contractId}/revisions/${revisionId}/return`;
    const payload = { expected_version: revision.contract_version, reason: 'Race check on isolated synthetic fixture.' };
    const [first, second] = await Promise.all([
      workflowPost(reviewerSession.page, route, session.data.csrf_token, payload, `race-a-${nonce()}`),
      workflowPost(reviewerSession.page, route, session.data.csrf_token, payload, `race-b-${nonce()}`),
    ]);
    const statuses = [first.status(), second.status()].sort();
    expect(statuses).toEqual([200, 409]);
    const finalResponse = await reviewerSession.page.request.get(`/api/v1/contracts/${contractId}/revisions/${revisionId}`);
    expect(finalResponse.ok()).toBeTruthy();
    const finalRevision = (await finalResponse.json() as ApiEnvelope<{ review_state: string; submissions: Array<{ outcome: string }> }>).data;
    expect(finalRevision.review_state).toBe('returned');
    expect(finalRevision.submissions.filter((submission) => submission.outcome === 'returned')).toHaveLength(1);
  } finally {
    await Promise.all([editorSession.context.close(), reviewerSession.context.close()]);
  }
});
