const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const root = path.resolve(__dirname, "../../..");
const context = vm.createContext({ FullCalendar: { globalLocales: [] } });
vm.runInContext(fs.readFileSync(path.join(root, "addons/web/static/lib/fullcalendar/core/locales-all.global.js"), "utf8"), context);
const before = JSON.parse(JSON.stringify(context.FullCalendar.globalLocales));
const patch = fs.readFileSync(path.join(root, "custom_addons/tp_i18n_vi/static/src/fullcalendar_vi.js"), "utf8");
vm.runInContext(patch, context);
vm.runInContext(patch, context);
const after = JSON.parse(JSON.stringify(context.FullCalendar.globalLocales));
for (const locale of before) {
    if (locale.code === "vi") locale.weekTextLong = "Tuần";
}
assert.deepEqual(after, before);
assert.equal(after.find((locale) => locale.code === "vi").weekTextLong, "Tuần");
console.log("PASS FullCalendar Vietnamese long week label; other locales preserved; idempotent");
