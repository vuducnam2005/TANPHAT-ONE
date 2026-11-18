/* Run against an existing authenticated session; never log in or write attendance data. */
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require("../../frontend/node_modules/playwright");

const base = process.env.TP_SCROLL_BASE_URL || "http://127.0.0.1:18069";
const storageState = process.env.TP_SCROLL_STORAGE_STATE;
const output = path.resolve(process.env.TP_SCROLL_OUTPUT || ".local/attendance-scroll");
const viewports = [{ width: 1440, height: 900 }, { width: 1366, height: 768 }, { width: 390, height: 844 }, { width: 375, height: 667 }];

async function metrics(page) {
    return page.evaluate(() => {
        const root = document.scrollingElement;
        const screen = document.querySelector(".o_tp_att_overview");
        const navbar = document.querySelector(".o_navbar");
        const sidebar = document.querySelector(".o_tp_hr_sidebar:not(.is-hidden)");
        return {
            documentY: root.scrollTop, documentHeight: root.scrollHeight, viewportHeight: innerHeight,
            documentWidth: root.scrollWidth, viewportWidth: innerWidth,
            screenY: screen.scrollTop, screenHeight: screen.clientHeight, contentHeight: screen.scrollHeight,
            navbarY: navbar.getBoundingClientRect().top,
            sidebarY: sidebar?.getBoundingClientRect().top ?? null,
            hiddenLabelContained: [...screen.querySelectorAll(".visually-hidden")].every(label => screen.contains(label.offsetParent)),
        };
    });
}

async function run() {
    assert(storageState, "Set TP_SCROLL_STORAGE_STATE to an existing private Playwright storage state");
    fs.mkdirSync(output, { recursive: true });
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext({ storageState, locale: "vi-VN" });
    const page = await context.newPage();
    const errors = [];
    const results = [];
    page.on("pageerror", error => errors.push(error.message));
    try {
        for (const viewport of viewports) {
            await page.setViewportSize(viewport);
            await page.goto(`${base}/app/cham-cong`, { waitUntil: "domcontentloaded" });
            await page.locator(".o_tp_att_overview[aria-busy='false']").waitFor();
            for (const mode of ["Ngày", "Tuần", "Tháng"]) {
                const modeButton = page.getByRole("button", { name: mode, exact: true });
                if (await modeButton.getAttribute("aria-pressed") !== "true") {
                    await Promise.all([
                        page.waitForResponse(response => response.url().includes("/tp_overview")),
                        modeButton.click(),
                    ]);
                    await page.locator(".o_tp_att_overview[aria-busy='false']").waitFor();
                }
                await page.locator(".o_tp_att_overview").evaluate(el => { el.scrollTop = 0; });
                const before = await metrics(page);
                assert(before.hiddenLabelContained, "Accessibility labels escape the attendance scrollport");
                assert(before.documentHeight <= before.viewportHeight + 1, "Document has blank overflow below the web client");
                assert(before.documentWidth <= before.viewportWidth + 1, "Document overflows horizontally");
                const screen = page.locator(".o_tp_att_overview");
                const box = await screen.boundingBox();
                // Scroll on the screen's padding, outside the independently scrollable table.
                await page.mouse.move(box.x + 3, box.y + box.height / 2);
                for (let i = 0; i < 5; i++) {
                    await page.mouse.wheel(0, 1800);
                    await page.waitForTimeout(50);
                }
                const down = await metrics(page);
                assert(down.screenY > 0, "Overview content did not scroll");
                assert.equal(down.documentY, 0, "Wheel escaped to the document at the bottom");
                assert.equal(down.navbarY, before.navbarY, "Navbar moved with the document");
                assert.equal(down.sidebarY, before.sidebarY, "Sidebar moved with the document");
                assert(Math.abs(down.screenY + down.screenHeight - down.contentHeight) <= 2, "Cannot reach bottom of overview");
                await page.screenshot({ path: path.join(output, `${viewport.width}-${mode}-bottom.png`) });
                for (let i = 0; i < 5; i++) {
                    await page.mouse.wheel(0, -1800);
                    await page.waitForTimeout(50);
                }
                const up = await metrics(page);
                assert.equal(up.screenY, 0, "Cannot return to the top of overview");
                assert.equal(up.documentY, 0, "Wheel escaped to the document at the top");
                results.push({ viewport, mode, before, down, up });
            }
        }
        assert.deepEqual(errors, [], "Browser JavaScript errors");
    } finally {
        fs.writeFileSync(path.join(output, "results.json"), JSON.stringify({ base, results, errors }, null, 2));
        await browser.close();
    }
    console.log(`PASS: ${results.length} attendance overview viewport/mode cases; no document scroll, navbar/sidebar movement or JS errors`);
}

run().catch(error => { console.error(error.message); process.exitCode = 1; });
