// BANK-001: browser check of the "Tài khoản ngân hàng" card in "Hồ sơ của tôi".
// Invoked only by the synthetic HttpCase (tp_hr_bank TestTpHrBank); private cookies are deleted by its caller.
// Read-only in the UI: opens the card and the add modal, searches a bank, then cancels; in edit mode it
// searches a country and a province, then discards. Saves nothing.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require('../../frontend/node_modules/playwright');

const TABS = ['Tổng quan', 'Thông tin cá nhân', 'Hồ sơ và năng lực', 'Hợp đồng lao động', 'Tài khoản và phân quyền', 'Lịch sử hoạt động'];

/** The web client redraws on the next animation frame: poll instead of reading once. */
async function waitValue(locator, pattern) {
    let value = '';
    for (const deadline = Date.now() + 5000; Date.now() < deadline;) {
        value = await locator.inputValue();
        if (pattern.test(value)) {
            return value;
        }
        await new Promise((resolve) => setTimeout(resolve, 50));
    }
    assert.match(value, pattern);
    return value;
}

/** Same for text: a list that is filtered after typing still shows its old content for a frame. */
async function waitText(locator, pattern) {
    let text = '';
    for (const deadline = Date.now() + 5000; Date.now() < deadline;) {
        text = (await locator.textContent()) || '';
        if (pattern.test(text)) {
            return text;
        }
        await new Promise((resolve) => setTimeout(resolve, 50));
    }
    assert.match(text, pattern);
    return text;
}

async function run() {
    const f = JSON.parse(fs.readFileSync(process.env.TP_HR_BANK_FIXTURE, 'utf8'));
    assert(f.holderName.includes('SYNTHETIC'));
    const browser = await chromium.launch({ headless: true });
    const errors = [], checks = [];
    let page;
    try {
        const context = await browser.newContext({ locale: 'vi-VN' });
        await context.addCookies(f.cookies);
        page = await context.newPage();
        page.setDefaultTimeout(45000);
        page.on('pageerror', (e) => errors.push(e.message));
        page.on('console', (msg) => { if (msg.type() === 'error') { errors.push(msg.text()); } });
        for (const [size, width, height] of [['desktop', 1440, 900], ['mobile', 390, 844]]) {
            await page.setViewportSize({ width, height });
            await page.goto(`${f.base}/app/nhan-su/ho-so-cua-toi`, { waitUntil: 'domcontentloaded' });
            await page.locator('.o_tp_hr_my_profile [role="tab"]', { hasText: 'Thông tin cá nhân' }).click();
            const card = page.locator('.o_tp_bank_card');
            await card.waitFor();
            const row = card.locator('.o_tp_bank_account').first();
            await row.waitFor();
            const rowText = await row.innerText();
            for (const text of ['Vietcombank', '0123 4567 89', f.holderName, 'Chờ Nhân sự xác minh']) {
                assert(rowText.includes(text), `${size}: account row is missing "${text}": ${rowText}`);
            }
            assert.equal(await row.locator('.o_tp_bank_badge').innerText(), 'VCB');
            // Styles really applied (a failed SCSS compile serves an old bundle and a "Style error" toast).
            assert.equal(await row.locator('.o_tp_bank_badge').evaluate((el) => getComputedStyle(el).width), '44px');
            assert.equal(await page.locator('.o_notification', { hasText: 'Style error' }).count(), 0);
            await card.screenshot({ path: path.join(f.output, `${size}-card.png`) });
            // Read-only values: ISO dates shown as DD/MM/YYYY; real data and "Chưa khai báo" look different.
            const birthday = page.locator('.tp-mp-value', { hasText: '12/05/1990' });
            assert.equal(await birthday.count(), 1, `${size}: birthday is not shown as 12/05/1990`);
            assert.doesNotMatch(await birthday.getAttribute('class'), /tp-mp-empty/);
            const missing = page.locator('.tp-mp-empty', { hasText: 'Chưa khai báo' }).first();
            assert.equal(await missing.evaluate((el) => getComputedStyle(el).fontStyle), 'italic');

            await card.locator('.o_tp_bank_add').click();
            const modal = page.locator('.o_tp_bank_modal');
            await modal.waitFor();
            assert.equal(await modal.locator('#tp_bank_modal_title').innerText(), 'Thêm tài khoản ngân hàng');
            const input = modal.locator('#tp_bank_bank_id');
            await input.click();
            await waitText(modal.locator('.o_tp_bank_picker_count'), /^\d+ ngân hàng$/);
            await input.fill('vietin');
            const option = modal.locator('.o_tp_bank_option', { hasText: 'VietinBank' }).first();
            await option.waitFor();
            await waitText(modal.locator('.o_tp_bank_picker_count'), /^Tìm thấy 1 ngân hàng$/);
            assert.equal(await modal.locator('.o_tp_bank_picker_search').count(), 1);
            await page.screenshot({ path: path.join(f.output, `${size}-search.png`) });
            await option.click();
            // Closed: short name in the box, full legal name and NAPAS BIN on the line under it.
            await waitValue(input, /^VietinBank$/);
            await waitText(modal.locator('.o_tp_bank_picker_hint'), /^Ngân hàng TMCP Công thương Việt Nam · BIN 970415$/);
            // Keyboard path: accent-free search, Enter picks the highlighted bank.
            await input.click();
            await input.fill('dau tu va phat trien viet');
            await modal.locator('.o_tp_bank_option', { hasText: 'BIDV' }).first().waitFor();
            await input.press('Enter');
            await waitValue(input, /^BIDV$/);
            const overflow = await page.evaluate(() => document.scrollingElement.scrollWidth - innerWidth);
            assert(overflow <= 1, `${size}: page scrolls sideways by ${overflow}px`);
            await page.screenshot({ path: path.join(f.output, `${size}-modal.png`) });
            await modal.getByRole('button', { name: 'Hủy', exact: true }).click();
            await modal.waitFor({ state: 'detached' });
            assert.equal(await card.locator('.o_tp_bank_account').count(), 1);
            checks.push(`${size}: card, badge, masked number, pending status; modal search by mouse and keyboard; cancel`);
        }
        // Review captures: every tab on a tall viewport so the whole screen is in one image.
        for (const [size, width, height] of [['desktop', 1440, 2600], ['mobile', 390, 4200]]) {
            await page.setViewportSize({ width, height });
            for (const [index, label] of TABS.entries()) {
                const tab = page.locator('.o_tp_hr_my_profile [role="tab"]', { hasText: label });
                await tab.click();
                await page.waitForFunction((el) => el.getAttribute('aria-selected') === 'true', await tab.elementHandle());
                await page.waitForTimeout(300);
                await page.screenshot({ path: path.join(f.output, `review-${size}-${index}.png`) });
            }
            // Edit mode of "Thông tin cá nhân", then cancel without changes (no confirmation, nothing saved).
            await page.locator('.o_tp_hr_my_profile [role="tab"]', { hasText: 'Thông tin cá nhân' }).click();
            await page.locator('.o_tp_hr_edit').click();
            await page.locator('#tp_mp_private_email').waitFor();
            await page.waitForTimeout(300);
            await page.screenshot({ path: path.join(f.output, `review-${size}-edit.png`) });
            // Dates use the Odoo picker fixed to DD/MM/YYYY (same as view mode), whatever the browser or account locale.
            const birthdayInput = page.locator('#tp_mp_birthday');
            await waitValue(birthdayInput, /^12\/05\/1990$/);
            const birthdayWidth = await birthdayInput.evaluate((el) => el.getBoundingClientRect().width);
            const emailWidth = await page.locator('#tp_mp_private_email').evaluate((el) => el.getBoundingClientRect().width);
            assert(Math.abs(birthdayWidth - emailWidth) <= 2, `${size}: date input is ${birthdayWidth}px, email ${emailWidth}px`);
            await birthdayInput.click();
            const picker = page.locator('.o_datetime_picker');
            await picker.waitFor();
            await page.waitForTimeout(400); // popover fade-in
            await page.screenshot({ path: path.join(f.output, `review-${size}-datepicker.png`) });
            await page.locator('#tp_mp_private_email').click();
            await picker.waitFor({ state: 'detached' });
            await waitValue(birthdayInput, /^12\/05\/1990$/);
            // Country: accent-free search with a result count; the province list follows the country.
            const country = page.locator('#tp_mp_priv_country');
            await country.click();
            await waitText(page.locator('.o_tp_search_select_count'), /^\d+ quốc gia$/);
            await country.fill('viet');
            await waitText(page.locator('.o_tp_search_select_count'), /^Tìm thấy \d+ quốc gia$/);
            const vietnam = page.locator('.o_tp_search_select_option', { hasText: /vi[eệ]t ?nam/i }).first();
            await vietnam.waitFor();
            await country.screenshot({ path: path.join(f.output, `review-${size}-country-input.png`) });
            await page.screenshot({ path: path.join(f.output, `review-${size}-country.png`) });
            await vietnam.click();
            await waitValue(country, /^vi[eệ]t ?nam$/i);
            const province = page.locator('#tp_mp_priv_state');
            let provinceNote = 'no provinces for this country in this database';
            if (await province.isEnabled()) {
                await province.click();
                await province.fill('ha noi');
                await waitText(page.locator('.o_tp_search_select_count'), /^Tìm thấy \d+ tỉnh \/ thành phố$/);
                const hanoi = page.locator('.o_tp_search_select_option', { hasText: /h[aà] n[oộ]i/i }).first();
                await hanoi.waitFor();
                await page.screenshot({ path: path.join(f.output, `review-${size}-province.png`) });
                await hanoi.click();
                await waitValue(province, /h[aà] n[oộ]i/i);
                provinceNote = 'province search "ha noi"';
            }
            // Discard: the form is dirty, so the confirmation dialog must appear; nothing is saved.
            await page.locator('.o_tp_hr_cancel').click();
            await page.getByRole('button', { name: 'Bỏ thay đổi', exact: true }).click();
            await page.locator('.o_tp_hr_edit').waitFor();
            checks.push(`${size}: date picker DD/MM/YYYY, country search "viet", ${provinceNote}, discard`);
        }
        assert.deepEqual(errors, []);
    } catch (error) {
        if (page) {
            await page.screenshot({ path: path.join(f.output, 'failure.png') }).catch(() => {});
            const body = await page.evaluate(() => document.body.innerText.slice(0, 800)).catch(() => '');
            error.message += `\nURL: ${page.url()}\nBrowser errors: ${JSON.stringify(errors)}\nBody: ${body}`;
        }
        throw error;
    } finally {
        await browser.close();
    }
    fs.writeFileSync(path.join(f.output, 'result.json'), JSON.stringify({ checks, errors }, null, 2));
    console.log(checks.join('\n'));
}

run().catch((error) => {
    console.error(error.stack || error.message);
    process.exit(1);
});
