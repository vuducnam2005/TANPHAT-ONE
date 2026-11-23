// Chromium regression with Odoo's bundled Owl and current source templates.
// The dialog shell and RPC services are mocked. This test has no Odoo or database dependency.
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const { chromium } = require("../../frontend/node_modules/playwright");

const root = path.resolve(__dirname, "../..");
const attendance = path.join(root, "custom_addons/tp_hr_attendance/static/src");
const mine = fs.readFileSync(path.join(attendance, "mine.xml"), "utf8");
const compare = fs.readFileSync(path.join(attendance, "matrix/compare.xml"), "utf8");
const source = fs.readFileSync(path.join(attendance, "mine.js"), "utf8");
const dialogStart = source.indexOf("function parseClockToFloat");
const dialogEnd = source.indexOf("export class MyAttendance");
assert(dialogStart >= 0 && dialogEnd > dialogStart, "Cannot locate attendance dialog source");
const dialogCode = source.slice(dialogStart, dialogEnd).replaceAll("export class", "class");

async function mountDialogs(page) {
    await page.evaluate(async ({ mine, dialogCode }) => {
        const host = document.querySelector("main");
        const { Component, mount, useProps } = owl;
        const calls = [];
        const notifications = [];
        let response;
        let readEvidence;
        const services = {
            orm: { call(...args) {
                calls.push(args);
                return new Promise((resolve, reject) => { response = { resolve, reject }; });
            } },
            notification: { add(message) { notifications.push(message); } },
        };
        class Dialog extends Component { static template = "AttendanceTest.Dialog"; }
        class InlineErrors extends Component {
            static template = "AttendanceTest.InlineErrors";
            props = useProps();
        }
        const templates = mine.replace("</templates>", `
            <t t-name="AttendanceTest.Dialog">
                <section role="dialog"><t t-call-slot="default"/><footer><t t-call-slot="footer"/></footer></section>
            </t>
            <t t-name="AttendanceTest.InlineErrors">
                <section role="alert" t-if="this.props.errors.length or this.props.server">
                    <p t-out="this.props.server?.message || this.props.errors[0].message"/>
                </section>
            </t>
        </templates>`);
        const [Correction, Withdraw] = new Function(
            "owl", "Dialog", "InlineErrors", "useService", "saveError", "uuid",
            `const { Component, proxy, signal, useProps } = owl;
             ${dialogCode}
             return [CorrectionFormDialog, WithdrawDialog];`
        )(owl, Dialog, InlineErrors, (name) => services[name], (error) => ({ message: error.message }),
            () => "0123456789abcdef");

        window.FileReader = class extends FileReader {
            readAsDataURL(file) { readEvidence = () => super.readAsDataURL(file); }
        };
        const close = () => { host.textContent = ""; };
        const form = await mount(Correction, host, {
            templates, props: { workDate: "2026-11-22", requestedIn: "07:37", close },
        });
        window.attendanceTest = {
            form, calls, notifications,
            resolve: (result) => response.resolve(result),
            reject: () => response.reject(new Error("Synthetic RPC failure")),
            readEvidence: () => readEvidence(),
            mountWithdraw: () => mount(Withdraw, host, {
                templates, props: { request: { id: 3, name: "Synthetic request" }, close },
            }),
        };
    }, { mine, dialogCode });
}

async function testDialogs(page) {
    await mountDialogs(page);
    const date = page.locator("#tp_att_correction_date");
    const clockIn = page.locator("#tp_att_correction_in");
    const clockOut = page.locator("#tp_att_correction_out");
    const reason = page.locator("#tp_att_correction_reason");
    const submit = page.locator("footer .btn-primary");
    const draft = page.locator("footer .btn-outline-secondary");
    const calls = () => page.evaluate(() => attendanceTest.calls);

    assert.equal(await date.inputValue(), "2026-11-22");
    assert.equal(await clockIn.inputValue(), "07:37");
    assert.equal(await clockOut.inputValue(), "");
    await submit.click();
    await page.getByRole("alert").waitFor();
    assert.equal((await calls()).length, 0);

    await date.fill("2026-11-21");
    await clockIn.fill("00:00");
    await clockOut.fill("17:13");
    await reason.fill("Synthetic explanation");
    await page.locator("#tp_att_correction_evidence").setInputFiles({
        name: "evidence.txt", mimeType: "text/plain", buffer: Buffer.from("evidence"),
    });
    await page.waitForFunction(() => document.querySelector("footer .btn-primary").disabled);
    assert(await draft.isDisabled());
    assert.equal((await calls()).length, 0);
    await page.evaluate(() => attendanceTest.readEvidence());
    await page.getByText("evidence.txt", { exact: true }).waitFor();
    await submit.click();
    await page.waitForFunction(() => document.querySelector("footer .btn-primary").disabled);
    await page.evaluate(() => { void attendanceTest.form.save(true); });

    const vals = {
        work_date: "2026-11-21", requested_in: 0, requested_out: 17 + 13 / 60,
        reason: "Synthetic explanation", evidence_file: Buffer.from("evidence").toString("base64"),
        evidence_name: "evidence.txt",
    };
    assert.deepEqual(await calls(), [[
        "tp.hr.attendance.correction", "tp_save_and_submit", [vals, false, true, "0123456789abcdef"],
    ]]);

    await page.evaluate(() => attendanceTest.reject());
    await page.getByText("Synthetic RPC failure").waitFor();
    assert.equal(await date.inputValue(), vals.work_date);
    assert.equal(await clockIn.inputValue(), "00:00");
    assert.equal(await clockOut.inputValue(), "17:13");
    assert.equal(await reason.inputValue(), vals.reason);
    await draft.click();
    assert.deepEqual((await calls())[1][2], [vals, false, false, "0123456789abcdef"]);
    await page.evaluate(() => attendanceTest.resolve({ state: "draft" }));
    await page.getByRole("dialog").waitFor({ state: "detached" });

    await page.evaluate(() => attendanceTest.mountWithdraw());
    await page.locator("#tp_att_withdraw_reason").fill("Synthetic withdrawal reason");
    await page.locator("footer .btn-danger").click();
    assert.deepEqual((await calls())[2], [
        "tp.hr.attendance.correction", "action_withdraw", [[3], "Synthetic withdrawal reason"],
    ]);
    await page.evaluate(() => attendanceTest.resolve(true));
    await page.getByRole("dialog").waitFor({ state: "detached" });
}

async function testCompareBindings(page) {
    const version = await page.evaluate(async (xml) => {
        const { App, Component, mount, proxy } = owl;
        new App({ templates: xml }).getTemplate("tp_hr_attendance.Compare");
        const doc = new DOMParser().parseFromString(xml, "application/xml");
        const fields = doc.querySelector(".o_tp_att_filters .o_tp_att_filter_row").outerHTML;
        class CompareFilters extends Component {
            static template = "AttendanceTest.CompareFilters";
            state = proxy({ draftOnlyDiff: false, draftGroup: "", draftSourceGroup: "", draftWorkDate: "", draftSearch: "" });
            data = {
                compare_groups: [{ key: "diff", label: "Different", cells: 1 }],
                group_options: [{ key: "source", label: "Source group" }], total_all_people: 1,
            };
            toggleOnlyDiff(event) { this.state.draftOnlyDiff = event.target.checked; }
            onSearchKeydown() {}
            applyFilters() {}
            clearFilters() {}
        }
        window.compareFilters = await mount(CompareFilters, document.querySelector("main"), {
            templates: `<templates><t t-name="AttendanceTest.CompareFilters">${fields}</t></templates>`,
        });
        return owl.__info__.version;
    }, compare);

    await page.getByRole("checkbox").check();
    const selects = page.getByRole("combobox");
    await selects.nth(0).selectOption("diff");
    await selects.nth(1).selectOption("source");
    await page.locator("input[type=date]").fill("2026-11-22");
    await page.getByRole("searchbox").fill("Synthetic employee");
    assert.deepEqual(await page.evaluate(() => ({ ...compareFilters.state })), {
        draftOnlyDiff: true, draftGroup: "diff", draftSourceGroup: "source",
        draftWorkDate: "2026-11-22", draftSearch: "Synthetic employee",
    });
    return version;
}

async function run() {
    const browserOptions = process.platform === "win32" && !fs.existsSync(chromium.executablePath())
        ? { channel: "msedge" }
        : {};
    const browser = await chromium.launch(browserOptions);
    try {
        const page = await browser.newPage();
        const errors = [];
        page.on("pageerror", (error) => errors.push(error.message));
        await page.setContent("<main></main>");
        await page.addScriptTag({ path: path.join(root, "addons/web/static/lib/owl/owl.js") });
        await testDialogs(page);
        const version = await testCompareBindings(page);
        assert.deepEqual(errors, []);
        console.log(`PASS attendance correction and comparison bindings on Owl ${version} (mock RPC)`);
    } finally {
        await browser.close();
    }
}

run().catch((error) => { console.error(error); process.exitCode = 1; });
