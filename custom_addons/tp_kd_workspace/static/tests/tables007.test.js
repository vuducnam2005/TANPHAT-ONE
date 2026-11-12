import { describe, expect, test } from "@odoo/hoot";
import { contains, defineModels, fields, models, mountView, onRpc, patchWithCleanup, mockService } from "@web/../tests/web_test_helpers";
import { browser } from "@web/core/browser/browser";
import { user } from "@web/core/user";
import { session } from "@web/session";
import { readPageSize, writePageSize, tablePageKey } from "@tp_kd_workspace/prefs";
import { statusTone } from "@tp_kd_workspace/table/status_badge";
import { KdTableController } from "@tp_kd_workspace/table/table_tools";
import { CallbackRecorder } from "@web/search/action_hook";
import "@tp_kd_workspace/table/relation_tools";
import { defineMailModels } from "@mail/../tests/mail_test_helpers";

class Ui007Row extends models.Model {
    _name = "ui007.row";
    name = fields.Char();
    state = fields.Selection({selection:[["draft", "Nháp"],["in_review","Đang rà soát"],["returned","Bị trả lại"]]});
    _records = Array.from({length:118}, (_,i)=>({id:i+1,name:`Row ${i+1}`,state:i%2?"in_review":"draft"}));
}
class Ui007Parent extends models.Model {
    _name = "ui007.parent";
    name = fields.Char();
    line_ids = fields.One2many({relation:"ui007.row"});
    _records = [{id:1,name:"Parent",line_ids:Array.from({length:18},(_,i)=>i+1)}];
}
defineModels([Ui007Row, Ui007Parent]);
defineMailModels();
describe("KD-UI-007 tables", () => {
    test("page preference validates and isolates model/action/view", () => {
        const key = tablePageKey("ui007.row", 1, 2);
        expect(readPageSize(key)).toBe(20);
        writePageSize(key, 100);
        expect(readPageSize(key)).toBe(100);
        expect(readPageSize(tablePageKey("ui007.row", 1, 3))).toBe(20);
        browser.localStorage.setItem(key, "junk");
        expect(readPageSize(key)).toBe(20);
        writePageSize(key, 101);
        expect(readPageSize(key)).toBe(20);
    });
    test("status mapping keeps submitted and legal layers distinct", () => {
        expect(statusTone("crm.lead", "kd_bid_state", "submitted")).toBe("warning");
        expect(statusTone("tp.allocation", "state", "returned")).toBe("danger");
        expect(statusTone("tp.contract.revision", "signature_status", "signed_recorded")).toBe("info");
        expect(statusTone("project.project", "state", "returned")).toBe("neutral");
        expect(statusTone("tp.obligation", "checklist_status", "internal_checked")).toBe("success");
    });
    test("storage unavailable falls back safely", () => {
        patchWithCleanup(browser.localStorage, {
            getItem() { throw new Error("Storage unavailable"); },
            setItem() { throw new Error("Storage unavailable"); },
        });
        expect(readPageSize("blocked")).toBe(20);
        writePageSize("blocked", 50);
        expect(readPageSize("blocked")).toBe(20);
    });
    test("page keys isolate database and actor", () => {
        const first = tablePageKey("ui007.row", 7, 8);
        patchWithCleanup(session, { db: "ui007_other_database" });
        const otherDatabase = tablePageKey("ui007.row", 7, 8);
        expect(otherDatabase).not.toBe(first);
        patchWithCleanup(user, { userId: 99999 });
        expect(tablePageKey("ui007.row", 7, 8)).not.toBe(otherDatabase);
    });
    test("unsaved relation filters and page length are disabled without losing rows", async () => {
        mockService("menu", {getCurrentApp:()=>({xmlid:"tp_kd_workspace.menu_kd"})});
        await mountView({type:"form",resModel:"ui007.parent",resId:1,
            arch:'<form><field name="name"/><field name="line_ids" widget="tp_kd_relation"><list editable="bottom"><field name="name"/></list></field></form>'});
        expect('.o_data_row').toHaveCount(18);
        await contains('[name="name"] input').edit("Changed");
        expect('.tp_kd_relation_filter').toHaveAttribute("disabled");
        expect('[aria-label="Số dòng bảng con"]').toHaveAttribute("disabled");
        expect('.tp_kd_save_hint').toHaveText("Lưu thay đổi để lọc");
        expect('.o_data_row').toHaveCount(18);
    });
    test("native list limit is server side and quick filters create native facets", async () => {
        await mountView({ type:"list", resModel:"ui007.row", context:{tp_kd_relation:"hoot"},
            arch:'<list js_class="tp_kd_table"><field name="name"/><field name="state" widget="tp_kd_badge"/></list>',
            searchViewArch:'<search><field name="name"/><filter name="draft" string="Nháp" domain="[(\'state\',\'=\',\'draft\')]"/></search>' });
        expect('.o_data_row').toHaveCount(20);
        onRpc("web_search_read", ({kwargs})=>expect.step(`limit:${kwargs.limit}:offset:${kwargs.offset}`));
        await contains('[aria-label="Số dòng mỗi trang"]').select("10");
        expect('.o_data_row').toHaveCount(10);
        expect.verifySteps(["limit:10:offset:0"]);
        await contains('.tp_kd_quick_filter').click();
        expect('.o_searchview_facet').toHaveCount(1);
        expect('.o_data_row').toHaveCount(10);
        expect.verifySteps(["limit:10:offset:0"]);
    });
    test("browser history restores page and sort without replacing native search state", async () => {
        const recorder = new CallbackRecorder();
        const key = tablePageKey("ui007.row", undefined, "hoot");
        onRpc("web_search_read", ({ kwargs }) => {
            expect.step(`${kwargs.limit}:${kwargs.offset}:${kwargs.order}`);
        });
        await mountView({ type:"list", resModel:"ui007.row", context:{tp_kd_relation:"hoot"},
            __getGlobalState__: recorder,
            globalState:{tpKdListState:{key,limit:10,offset:10,orderBy:[{name:"id",asc:false}]}},
            arch:'<list js_class="tp_kd_table"><field name="name"/></list>',
            searchViewArch:'<search><field name="name"/></search>' });
        expect.verifySteps(["10:10:id DESC"]);
        expect('.o_data_row').toHaveCount(10);
        expect('.o_data_row:first-child [name="name"]').toHaveText("Row 108");
        const globalState = Object.assign({}, ...recorder.callbacks.map(callback => callback()));
        expect(typeof globalState.searchModel).toBe("string");
        expect(Object.keys(globalState.tpKdListState).sort()).toEqual(["key","limit","offset","orderBy"]);
        expect(globalState.tpKdListState).toEqual({key,limit:10,offset:10,orderBy:[{name:"id",asc:false}]});
    });
    test("native breadcrumb model state wins over stale browser history", async () => {
        let controller;
        patchWithCleanup(KdTableController.prototype, {
            setup() { super.setup(); controller = this; },
        });
        const params = { type:"list", resModel:"ui007.row", context:{tp_kd_relation:"hoot"},
            arch:'<list js_class="tp_kd_table"><field name="name"/></list>' };
        await mountView(params);
        await controller.model.root.load({limit:10,offset:10,orderBy:[{name:"id",asc:true}]});
        const modelState = controller.model.exportState();
        onRpc("web_search_read", ({ kwargs }) => {
            expect.step(`${kwargs.limit}:${kwargs.offset}:${kwargs.order}`);
        });
        await mountView({...params,state:{modelState},globalState:{tpKdListState:{
            key:tablePageKey("ui007.row",undefined,"hoot"),limit:20,offset:20,orderBy:[{name:"id",asc:false}],
        }}});
        expect.verifySteps(["10:10:id ASC"]);
        expect(controller.model.root.records[0].data.name).toBe("Row 11");
    });
});
