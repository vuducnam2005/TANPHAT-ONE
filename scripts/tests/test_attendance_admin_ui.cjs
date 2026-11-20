const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

const source = fs.readFileSync(path.join(__dirname,
    "../../custom_addons/tp_hr_attendance/static/src/sources.js"), "utf8")
    .replace(/^import .*;$/gm, "").replace("export class", "class");

test("admin export validates the selected scope and preserves form edits while polling", async () => {
    let today = "2026-11-20";
    let allowed = false;
    const file = { filename: "attendance.xlsx", content: "YWJj" };
    const exports = [];
    const downloads = [];
    const actions = [];
    const orm = {
        async call(model, method, [params]) {
            if (method === "tp_sources_overview") {
                return { today, can_export: allowed };
            }
            assert.equal(model, "tp.hr.attendance.day");
            assert.equal(method, "tp_export_sheet");
            exports.push({ ...params });
            return file;
        },
    };
    orm.silent = orm;
    const context = vm.createContext({
        Component: class {},
        registry: { category: () => ({ add() {} }) },
        proxy: (state) => state,
        useProps: () => ({}),
        useService: (name) => name === "orm" ? orm : {
            doAction(xmlid, options) { actions.push({ xmlid, filters: { ...options.additionalContext } }); },
        },
        useAttendanceLive: () => ({ loaded() {}, flush() {} }),
        onWillStart() {},
        onWillUnmount() {},
        downloadBase64: (download) => downloads.push(download),
    });
    vm.runInContext(source + "\nglobalThis.Screen = AttendanceSources;", context);
    const screen = new context.Screen();
    screen.setup();
    await screen.load();

    assert.equal(screen.state.date, today);
    assert.equal(screen.state.from, today);
    assert.equal(screen.state.to, today);
    await screen.exportSheet();
    assert.equal(exports.length, 0);

    allowed = true;
    today = "2026-11-21";
    Object.assign(screen.state, { mode: "range", date: "", from: "2026-11-20", to: "", department: "42" });
    const originalState = screen.state;
    await screen.load({ silent: true });
    assert.equal(screen.state, originalState);
    assert.equal(screen.state.date, "");
    assert.equal(screen.state.from, "2026-11-20");
    assert.equal(screen.state.to, "");
    assert.equal(screen.state.department, "42");
    screen.state.to = "2026-11-19";
    await screen.exportSheet();
    assert.equal(exports.length, 0);
    assert.ok(screen.state.exportError);

    screen.state.to = "2026-11-21";
    await screen.exportSheet();
    assert.deepEqual(exports, [{
        mode: "range", date: "", from: "2026-11-20", to: "2026-11-21", department_id: 42,
    }]);
    assert.deepEqual(downloads, [file]);
    assert.equal(screen.state.exportError, "");

    const xmlid = "tp_hr_attendance.action_enti_mapping";
    screen.open(xmlid, { search_default_state_suggested: 1 });
    screen.open(xmlid, { search_default_state_unmapped: 1 });
    assert.deepEqual(actions, [
        { xmlid, filters: { search_default_state_suggested: 1, search_default_state_unmapped: 0 } },
        { xmlid, filters: { search_default_state_suggested: 0, search_default_state_unmapped: 1 } },
    ]);
});
