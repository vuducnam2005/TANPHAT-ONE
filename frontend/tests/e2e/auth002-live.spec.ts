import { expect, test, type Page } from '@playwright/test';
import { createHmac } from 'node:crypto';
import { readFileSync } from 'node:fs';
import path from 'node:path';

const enabled = process.env.TP_AUTH002_LIVE === '1';
const database = 'tp_tanphat_auth002_verify';
const origin = 'http://127.0.0.1:18099';
type Actor = { login: string; password: string; totp_secret?: string };
type Fixture = { database: string; origin: string; actors: { plain: Actor; totp: Actor } };
let fixture: Fixture | undefined;

// Deliberately opt-in, with no dev/test database fallback and no secret diagnostics.
if (enabled) {
  if (process.env.VITE_ODOO_DATABASE !== database || process.env.TP_ODOO_ORIGIN !== origin) {
    throw new Error('AUTH-002 live tests require the owned verify database and isolated origin on port 18099.');
  }
  const local = path.resolve(process.cwd(), '../.local');
  const credentialsPath = path.resolve(process.env.TP_AUTH002_CREDENTIALS ?? path.join(local, 'auth002-verify/credentials.json'));
  if (!credentialsPath.startsWith(`${local}${path.sep}`)) throw new Error('AUTH-002 credentials must stay inside .local.');
  fixture = JSON.parse(readFileSync(credentialsPath, 'utf8')) as Fixture;
  const owner = JSON.parse(readFileSync(path.join(local, 'auth002-verify/owner.json'), 'utf8')) as { database: string; workspace: string };
  if (fixture.database !== database || fixture.origin !== origin || owner.database !== database ||
      path.resolve(owner.workspace) !== path.resolve(process.cwd(), '..')) {
    throw new Error('AUTH-002 fixture ownership or target does not match this workspace.');
  }
  if (![fixture.actors.plain, fixture.actors.totp].every((actor) => actor.login.startsWith('auth002.verify.') && actor.password) ||
      !fixture.actors.totp.totp_secret) throw new Error('AUTH-002 synthetic fixture credentials are incomplete.');
}

const totpError = 'Chưa xác thực được mã. Vui lòng nhập mã mới nhất trên ứng dụng xác thực; nếu đã thử nhiều lần, chờ ít phút rồi thử lại.';
const deepLink = '/work/projects?q=AUTH002#details';
test.use({ locale: 'en-US', trace: 'off', video: 'off', screenshot: 'off' });

function totp(secret: string) {
  const alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ234567';
  const bits = secret.replace(/=+$/, '').toUpperCase().split('').map((letter) => {
    const index = alphabet.indexOf(letter);
    if (index < 0) throw new Error('Invalid synthetic TOTP fixture format.');
    return index.toString(2).padStart(5, '0');
  }).join('');
  const key = Buffer.from((bits.match(/.{8}/g) ?? []).map((byte) => Number.parseInt(byte, 2)));
  const counter = Buffer.alloc(8);
  counter.writeBigUInt64BE(BigInt(Math.floor(Date.now() / 30000)));
  const digest = createHmac('sha1', key).update(counter).digest();
  const offset = digest[digest.length - 1] & 15;
  return ((digest.readUInt32BE(offset) & 0x7fffffff) % 1000000).toString().padStart(6, '0');
}

async function noSecrets(page: Page, codes: string[] = []) {
  const actorSecrets = Object.values(fixture!.actors).flatMap((actor) => [actor.password, actor.totp_secret ?? '']).filter(Boolean);
  const sessionSecrets = (await page.context().cookies()).filter((cookie) => cookie.name === 'session_id').map((cookie) => cookie.value);
  const storage = await page.evaluate(() => ({ local: { ...localStorage }, session: { ...sessionStorage } }));
  const exposed = `${page.url()} ${JSON.stringify(storage)}`;
  // Boolean assertions avoid echoing any secret value on failure.
  expect([...actorSecrets, ...sessionSecrets, ...codes].some((secret) => exposed.includes(secret)), 'No credentials, session or code in URL/storage').toBe(false);
  const storageKeys = [...Object.keys(storage.local), ...Object.keys(storage.session)];
  expect(storageKeys.some((key) => /password|totp|session|credential|csrf/i.test(key)), 'No auth secret keys in storage').toBe(false);
  const url = new URL(page.url());
  expect([...url.searchParams.keys()].some((key) => /password|totp|session/i.test(key))).toBe(false);
}

async function signIn(page: Page, actor: Actor, destination = deepLink) {
  await page.goto(destination);
  await expect(page.getByRole('heading', { name: 'Chào mừng trở lại.' })).toBeVisible();
  await page.getByLabel('Tên đăng nhập', { exact: true }).fill(actor.login);
  await page.getByLabel('Mật khẩu', { exact: true }).fill(actor.password);
  await page.getByRole('button', { name: 'Đăng nhập', exact: true }).click();
}

async function handoff(page: Page) {
  const link = page.getByRole('link', { name: 'Tiếp tục nhập mã xác thực' });
  await expect(link).toBeVisible();
  await expect(page.getByLabel('Mật khẩu', { exact: true })).toBeEmpty();
  const url = new URL((await link.getAttribute('href'))!, page.url());
  expect(url.origin).toBe(new URL(page.url()).origin);
  expect(url.pathname).toBe('/web/login/totp');
  expect(url.searchParams.get('redirect')).toBe(deepLink);
  expect(url.searchParams.get('redirect')?.startsWith('/work/')).toBe(true);
  await noSecrets(page);
  await link.click();
  await expect(page.locator('input[name="totp_token"]')).toBeVisible();
}

test.describe('AUTH-002 isolated live verification', () => {
  test.skip(!enabled, 'Enable TP_AUTH002_LIVE=1 with the owned isolated test runtime.');
  test.describe.configure({ mode: 'serial' });

  test('T05/T12 logout shows signed_out, cleans URL/session and preserves later deep links', async ({ page }) => {
    await signIn(page, fixture!.actors.plain);
    await expect(page.getByRole('heading', { name: 'Dự án đang theo dõi' })).toBeVisible();
    await noSecrets(page);
    await page.getByRole('button', { name: 'Đăng xuất', exact: true }).click();
    await expect(page.getByRole('status')).toContainText('Bạn đã đăng xuất khỏi TANPHAT ONE.');
    await expect(page).toHaveURL(/\/work\/$/);
    expect((await page.request.get('/api/v1/me')).status()).toBe(401);
    await noSecrets(page);
    await signIn(page, fixture!.actors.plain);
    await expect(page.getByRole('heading', { name: 'Dự án đang theo dõi' })).toBeVisible();
    expect(new URL(page.url()).pathname + new URL(page.url()).search + new URL(page.url()).hash).toBe(deepLink);
    await noSecrets(page);
  });

  test('T08/T12 native 2FA in English browser keeps Vietnamese copy, validates code and cancels', async ({ page }) => {
    await signIn(page, fixture!.actors.totp);
    await handoff(page);
    await expect(page.locator('.tp-native-wordmark')).toContainText('TANPHAT ONE');
    await expect(page.getByRole('heading', { name: 'Nhập mã xác thực' })).toBeVisible();
    await expect(page.getByText('Mở ứng dụng xác thực để xem mã gồm 6 chữ số.')).toBeVisible();
    await expect(page.getByLabel('Không hỏi lại trên thiết bị này')).toBeVisible();
    await expect(page.locator('input[name="password"]')).toHaveCount(0);
    const token = page.getByPlaceholder('Mã 6 chữ số');
    const current = totp(fixture!.actors.totp.totp_secret!);
    const wrong = current === '000000' ? '111111' : '000000';
    await token.fill(wrong);
    await page.getByRole('button', { name: 'Xác nhận', exact: true }).click();
    await expect(page.getByRole('alert')).toHaveText(totpError);
    await expect(page.locator('body')).not.toContainText('Verification failed');
    await expect(page.locator('body')).not.toContainText('Invalid authentication code format');
    await noSecrets(page, [wrong]);
    const valid = totp(fixture!.actors.totp.totp_secret!);
    await token.fill(valid);
    await page.getByRole('button', { name: 'Xác nhận', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'Dự án đang theo dõi' })).toBeVisible();
    expect(new URL(page.url()).pathname + new URL(page.url()).search + new URL(page.url()).hash).toBe(deepLink);
    expect((await page.request.get('/api/v1/me')).status()).toBe(200);
    await noSecrets(page, [wrong, valid]);
    await page.getByRole('button', { name: 'Đăng xuất', exact: true }).click();
    await signIn(page, fixture!.actors.totp);
    await handoff(page);
    await page.getByRole('button', { name: 'Hủy và quay lại', exact: true }).click();
    await expect(page).toHaveURL(/\/work\/$/);
    await expect(page.getByRole('heading', { name: 'Chào mừng trở lại.' })).toBeVisible();
    expect((await page.request.get('/api/v1/me')).status()).toBe(401);
    await noSecrets(page, [wrong, valid]);
  });

  test('T09/T12 real cooldown blocks even a correct password, then expires', async ({ page }) => {
    test.setTimeout(75000);
    const actor = fixture!.actors.plain;
    await page.goto('/work/');
    await page.getByLabel('Tên đăng nhập', { exact: true }).fill(actor.login);
    const password = page.getByLabel('Mật khẩu', { exact: true });
    const submit = page.getByRole('button', { name: 'Đăng nhập', exact: true });
    for (let attempt = 0; attempt < 3; attempt += 1) {
      await password.fill('auth002-synthetic-invalid-password');
      await submit.click();
      await expect(page.getByRole('alert')).toContainText('Tên đăng nhập hoặc mật khẩu chưa đúng');
      await expect(password).toBeEmpty();
    }
    await password.fill(actor.password);
    await submit.click();
    await expect(page.getByRole('alert')).toHaveText('Tạm thời chưa thể đăng nhập vì đã thử sai nhiều lần. Vui lòng chờ ít phút rồi thử lại.');
    expect((await page.request.get('/api/v1/me')).status()).toBe(401);
    await noSecrets(page);
    // The owned verify fixture uses the previously approved 3 attempts / 20 seconds policy.
    await page.waitForTimeout(21000);
    await password.fill(actor.password);
    await submit.click();
    await expect(page.getByRole('heading', { name: 'Dự án đang theo dõi' })).toBeVisible();
    expect((await page.request.get('/api/v1/me')).status()).toBe(200);
    await noSecrets(page);
  });
});
