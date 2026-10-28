import { expect, test, type Page } from '@playwright/test';
import { existsSync, readFileSync } from 'node:fs';
import path from 'node:path';

// Only the isolated development runtime is used. No credentials are printed.
const credentialPath = path.resolve('../.local/dev-secrets.json');
const localCredentials = existsSync(credentialPath)
  ? JSON.parse(readFileSync(credentialPath, 'utf8')) as { planner: string; admin: string }
  : null;

async function login(page: Page, role: 'planner' | 'admin' = 'planner') {
  if (!localCredentials) throw new Error('Run scripts/dev.ps1 setup before the live browser tests.');
  await page.goto('/work/');
  await expect(page.getByRole('heading', { name: 'Chào mừng trở lại.' })).toBeVisible();
  await page.locator('input[name="login"]').fill(role === 'planner' ? 'planner.dev' : 'admin');
  await page.locator('input[name="password"]').fill(localCredentials[role]);
  await page.locator('button[type="submit"]').click();
  await expect(page).toHaveURL(/\/work\/projects/);
  await expect(page.getByRole('heading', { name: 'Dự án đang theo dõi' })).toBeVisible();
}

test('TANPHAT ONE login, assigned project, detail reload, search, and CSRF logout', async ({ page }) => {
  await login(page);
  const card = page.locator('.tp-project-card');
  await expect(card).toHaveCount(1);
  await expect(card).toContainText('DEV-001');
  await expect(page.getByText('DEV-002', { exact: true })).toHaveCount(0);
  await card.click();
  await expect(page.getByRole('heading', { name: /du an|dự án/i }).last()).toBeVisible();
  await page.reload();
  await expect(page.locator('.tp-fact-grid')).toBeVisible();
  await page.getByRole('link', { name: '← Danh sách dự án' }).click();
  await page.getByRole('searchbox').fill('no-such-project');
  await page.getByRole('button', { name: 'Tìm dự án', exact: true }).click();
  await expect(page.getByText('Không có dự án phù hợp', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Xóa tìm kiếm' }).click();
  await expect(card).toContainText('DEV-001');
  const rejectedLogout = await page.request.post('/web/session/logout', {
    form: { csrf_token: 'invalid-token', redirect: '/work/' },
  });
  expect(rejectedLogout.status()).toBe(400);
  expect((await page.request.get('/api/v1/me')).status()).toBe(200);
  await page.getByRole('button', { name: 'Đăng xuất' }).click();
  await expect(page.getByRole('heading', { name: 'Chào mừng trở lại.' })).toBeVisible();
  expect((await page.request.get('/api/v1/me')).status()).toBe(401);
});

test('manager scope differs and inaccessible detail is not disclosed', async ({ page }) => {
  await login(page, 'admin');
  await expect(page.locator('.tp-project-card')).toHaveCount(2);
  const privateProject = page.locator('.tp-project-card').filter({ hasText: 'DEV-002' });
  const privatePath = await privateProject.getAttribute('href');
  await page.getByRole('button', { name: 'Đăng xuất' }).click();
  await login(page);
  await page.goto(privatePath!);
  await expect(page.getByRole('heading', { name: 'Không mở được dự án', exact: true })).toBeVisible();
  await expect(page.locator('.tp-fact-grid')).toHaveCount(0);
  await page.goto('/work/projects/not-a-number');
  await expect(page.getByRole('heading', { name: 'Không mở được dự án', exact: true })).toBeVisible();
});

test('expired session clears project content; mobile view does not overflow', async ({ page, context }) => {
  await login(page);
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.locator('.tp-project-card')).toHaveCount(1);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  await page.screenshot({ path: '../.local/frontend-mobile.png', fullPage: true });
  await page.setViewportSize({ width: 1440, height: 1000 });
  await page.screenshot({ path: '../.local/frontend-projects.png', fullPage: true });
  await context.clearCookies();
  await page.getByRole('button', { name: 'Làm mới', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Chào mừng trở lại.' })).toBeVisible();
  await expect(page.locator('.tp-project-card')).toHaveCount(0);
});
