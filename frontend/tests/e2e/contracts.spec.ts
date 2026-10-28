import { expect, test, type Page } from '@playwright/test';
import { existsSync, readFileSync } from 'node:fs';
import path from 'node:path';

// Runs against the isolated development runtime and its synthetic contracts only. No credentials are printed.
const credentialPath = path.resolve('../.local/dev-secrets.json');
const localCredentials = existsSync(credentialPath)
  ? JSON.parse(readFileSync(credentialPath, 'utf8')) as { planner: string; admin: string }
  : null;
// Grouped VND amounts such as 40.000.000 must never reach a metadata-only reader.
const groupedAmount = /\d{1,3}(?:\.\d{3}){2,}/;

async function login(page: Page, role: 'planner' | 'admin' = 'planner') {
  if (!localCredentials) throw new Error('Run scripts/dev.ps1 setup before the live browser tests.');
  await page.goto('/work/');
  await expect(page.getByRole('heading', { name: 'Chào mừng trở lại.' })).toBeVisible();
  await page.locator('input[name="login"]').fill(role === 'planner' ? 'planner.dev' : 'admin');
  await page.locator('input[name="password"]').fill(localCredentials[role]);
  await page.locator('button[type="submit"]').click();
  await expect(page).toHaveURL(/\/work\/projects/);
}

async function openContracts(page: Page) {
  await page.getByRole('link', { name: 'TP Contracts' }).click();
  await expect(page.getByRole('heading', { name: 'Hồ sơ hợp đồng' })).toBeVisible();
}

test('metadata reader sees contracts, scope and BASE status without any amount', async ({ page }) => {
  await login(page);
  await openContracts(page);
  const cards = page.locator('.tp-project-card');
  await expect(cards).toHaveCount(2);
  await expect(cards.nth(0)).toContainText('HD-DEV-001');
  await expect(cards.nth(1)).toContainText('HD-DEV-003');
  await expect(page.getByText('HD-DEV-002')).toHaveCount(0);

  await cards.filter({ hasText: 'HD-DEV-001' }).click();
  await expect(page.getByRole('heading', { name: 'Hợp đồng tư vấn khảo sát thiết kế (giả lập)' })).toBeVisible();
  await expect(page.getByText('Bạn chưa được cấp quyền xem số tiền của dự án này.')).toBeVisible();
  await expect(page.locator('.tp-money')).toHaveCount(0);
  await expect(page.getByText('Đề cương kỹ thuật (giả lập)')).toBeVisible();
  await expect(page.getByText('Phụ lục 01 đã ký (giả lập)')).toHaveCount(0);
  await expect(page.getByText('Kết quả BASE chưa xác minh')).toBeVisible();
  expect(await page.locator('main').innerText()).not.toMatch(groupedAmount);

  await page.getByRole('link', { name: 'Xem phạm vi công việc' }).last().click();
  await expect(page.getByRole('heading', { name: 'Phụ lục 01', exact: true })).toBeVisible();
  await expect(page.locator('.tp-table tbody tr')).toHaveCount(2);
  await expect(page.getByRole('columnheader', { name: 'Giá trị' })).toHaveCount(0);
  await expect(page.locator('.tp-money')).toHaveCount(0);
  expect(await page.locator('main').innerText()).not.toMatch(groupedAmount);
  await page.reload();
  await expect(page.locator('.tp-table tbody tr')).toHaveCount(2);
});

test('financial reader sees the amendment replace the total; other scopes stay hidden', async ({ page }) => {
  await login(page, 'admin');
  await openContracts(page);
  const cards = page.locator('.tp-project-card');
  await expect(cards).toHaveCount(3);
  const hiddenContractPath = await cards.filter({ hasText: 'HD-DEV-002' }).getAttribute('href');
  await cards.filter({ hasText: 'HD-DEV-001' }).click();

  const snapshot = page.locator('.tp-snapshot');
  await page.getByLabel('Ngày xem').fill('2026-10-31');
  await page.getByRole('button', { name: 'Xem bản áp dụng' }).click();
  await expect(page).toHaveURL(/as_of=2026-10-31/);
  // Today's snapshot looks the same, so wait for the requested date before reading values.
  await expect(snapshot).toContainText('Bản áp dụng ngày 31/10/2026');
  await expect(snapshot).toContainText('Hợp đồng gốc');
  await expect(snapshot).toContainText('100.000.000 VND');
  await expect(page.getByText('Đã có bản sửa đổi được ghi nhận hiệu lực sau ngày đang xem.')).toBeVisible();
  await page.getByLabel('Ngày xem').fill('2026-11-01');
  await page.getByRole('button', { name: 'Xem bản áp dụng' }).click();
  await expect(snapshot).toContainText('Bản áp dụng ngày 01/11/2026');
  await expect(snapshot).toContainText('Phụ lục 01');
  await expect(snapshot).toContainText('110.000.000 VND');
  await expect(snapshot).not.toContainText('210.000.000');
  await expect(page.locator('.tp-revision.is-current')).toContainText('Phụ lục 01');
  const base = page.locator('.tp-base-item');
  await expect(base).toContainText('Kết quả BASE chưa xác minh');
  await expect(base).toContainText('110.000.000 VND');

  const financialLink = page.locator('.tp-document-list li').filter({ hasText: 'Phụ lục 01 đã ký (giả lập)' }).getByRole('link', { name: 'Tải tệp' });
  const financialPath = await financialLink.getAttribute('href');
  const download = await page.request.get(financialPath!);
  expect(download.status()).toBe(200);
  expect(download.headers()['content-disposition']).toContain('attachment');
  expect(await download.text()).toBe('Synthetic signed amendment - DEV');

  await page.locator('.tp-revision.is-current').getByRole('link', { name: 'Xem phạm vi công việc' }).click();
  const rows = page.locator('.tp-table tbody tr');
  await expect(rows.nth(0)).toContainText('70.000.000 VND');
  await expect(rows.nth(0)).toContainText('Điều chỉnh');
  await expect(rows.nth(1)).toContainText('40.000.000 VND');
  await expect(page.locator('.tp-table tfoot')).toContainText('110.000.000 VND');

  // BASE approved and verified is still not signed or effective; an unconfirmed line is not zero.
  await page.goto('/work/contracts?q=HD-DEV-003');
  await cards.filter({ hasText: 'HD-DEV-003' }).click();
  await expect(page.getByText('Kết quả BASE đã xác minh')).toBeVisible();
  await expect(page.locator('.tp-detail-heading')).toContainText('Chưa ghi nhận hiệu lực');
  await expect(page.locator('.tp-revision')).toContainText('Chưa ghi nhận ký');
  await expect(snapshot).toContainText('Không có bản áp dụng');
  await expect(page.getByText('Chưa có bản nào được ghi nhận hiệu lực tại ngày đang xem.')).toBeVisible();
  await page.getByRole('link', { name: 'Xem phạm vi công việc' }).click();
  await expect(rows.filter({ hasText: 'DP' })).toContainText('Chưa xác nhận');
  await expect(rows.filter({ hasText: 'TN' })).toContainText('45.000.000 VND');
  await expect(page.locator('.tp-table tfoot')).toContainText('Chưa đủ: có dòng chưa xác nhận');

  // Project access without a financial grant: metadata only.
  await page.goto(hiddenContractPath!);
  await expect(page.getByRole('heading', { name: 'Hợp đồng giám sát (giả lập)' })).toBeVisible();
  await expect(page.getByText('Bạn chưa được cấp quyền xem số tiền của dự án này.')).toBeVisible();
  await expect(page.locator('.tp-money')).toHaveCount(0);

  await page.getByRole('button', { name: 'Đăng xuất' }).click();
  await login(page);
  expect((await page.request.get(financialPath!)).status()).toBe(404);
  await page.goto(hiddenContractPath!);
  await expect(page.getByRole('heading', { name: 'Không mở được hợp đồng', exact: true })).toBeVisible();
  await expect(page.locator('.tp-fact-grid')).toHaveCount(0);
  await page.goto('/work/contracts/not-a-number');
  await expect(page.getByRole('heading', { name: 'Không mở được hợp đồng', exact: true })).toBeVisible();
});

test('project link filters contracts; contract pages fit a phone screen', async ({ page }) => {
  await login(page, 'admin');
  await page.locator('.tp-project-card').filter({ hasText: 'DEV-001' }).click();
  await page.getByRole('link', { name: 'Xem hợp đồng của dự án' }).click();
  await expect(page).toHaveURL(/project_id=\d+/);
  await expect(page.locator('.tp-filter-note')).toContainText('DEV-001');
  await expect(page.locator('.tp-project-card')).toHaveCount(2);
  await page.locator('.tp-project-card').filter({ hasText: 'HD-DEV-001' }).click();
  await expect(page.locator('.tp-snapshot')).toBeVisible();
  await page.screenshot({ path: '../.local/frontend-contract-detail.png', fullPage: true });

  await page.setViewportSize({ width: 390, height: 844 });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.getByRole('link', { name: 'Xem phạm vi công việc' }).last().click();
  await expect(page.locator('.tp-table tbody tr')).toHaveCount(2);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: '../.local/frontend-contract-mobile.png', fullPage: true });
});
