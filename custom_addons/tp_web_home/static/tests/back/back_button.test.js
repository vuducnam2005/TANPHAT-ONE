import { animationFrame, describe, expect, test } from "@odoo/hoot";
import {
    contains,
    defineModels,
    defineWebModels,
    fields,
    getService,
    models,
    mountWebClient,
} from "@web/../tests/web_test_helpers";
import { registry } from "@web/core/registry";
import { HOME_ACTION, resolveBackFallback, resolveBackTarget } from "@tp_web_home/back/back_navigation";

// UI-BACK-001: one shared "Quay lại" per detail screen; synthetic records only.
class TpBackPartner extends models.Model {
    _name = "tp.back.partner";
    name = fields.Char();
    _records = [
        { id: 1, name: "Synthetic A" },
        { id: 2, name: "Synthetic B" },
    ];
    _views = {
        list: `<list><field name="name"/></list>`,
        form: `<form><sheet><field name="name"/></sheet></form>`,
        search: `<search><field name="name"/></search>`,
    };
}
defineWebModels();
defineModels([TpBackPartner]);

describe.current.tags("desktop");

const LIST_ACTION = {
    type: "ir.actions.act_window",
    name: "Synthetic list",
    res_model: "tp.back.partner",
    views: [[false, "list"], [false, "form"]],
};

test("fallback resolution: registered model, then the action list, then Home", async () => {
    registry.category("tp_back_fallbacks").add("tp.back.partner", (data) => (data.name === "x" ? "tp_x.action_x" : "javascript:alert(1)"), { force: true });
    expect(resolveBackFallback("tp.back.partner", { name: "x" })).toBe("tp_x.action_x");
    // Anything that is not an xmlid is refused (no arbitrary URL or code).
    expect(resolveBackFallback("tp.back.partner", { name: "y" })).toBe(HOME_ACTION);
    expect(resolveBackFallback("res.partner", {}, { actionId: 7, views: [[false, "list"], [false, "form"]] })).toBe(7);
    expect(resolveBackFallback("res.partner", {}, { actionId: 7, views: [[false, "form"]] })).toBe(HOME_ACTION);
    registry.category("tp_back_fallbacks").remove("tp.back.partner");
});

test("async fallback may read missing fields (read-only) and is still validated", async () => {
    const reads = [];
    const orm = { read: async (model, ids, fnames) => { reads.push([model, ids, fnames]); return [{ id: ids[0], kind: "stock" }]; } };
    registry.category("tp_back_fallbacks").add("tp.back.partner", async (data, { resId, orm: o } = {}) => {
        const info = data.kind === undefined ? (await o.read("tp.back.partner", [resId], ["kind"]))[0] : data;
        return info.kind === "stock" ? "tp_x.action_stock" : "https://evil.example/";
    }, { force: true });
    expect(await resolveBackTarget("tp.back.partner", {}, {}, { resId: 2, orm })).toBe("tp_x.action_stock");
    expect(reads).toEqual([["tp.back.partner", [2], ["kind"]]]);
    expect(await resolveBackTarget("tp.back.partner", { kind: "other" }, {}, { resId: 2, orm })).toBe(HOME_ACTION);
    expect(await resolveBackTarget("res.partner", {}, { actionId: 7, views: [[false, "list"]] })).toBe(7);
    registry.category("tp_back_fallbacks").remove("tp.back.partner");
});

test("form shows exactly one back button and returns to the list", async () => {
    await mountWebClient();
    await getService("action").doAction(LIST_ACTION);
    expect(".o_list_view").toHaveCount(1);
    expect(".o_tp_back_button").toHaveCount(0);

    await contains(".o_data_row:eq(1) .o_data_cell").click();
    expect(".o_form_view").toHaveCount(1);
    expect(".o_tp_back_button").toHaveCount(1);
    expect(".o_tp_back_button").toHaveAttribute("title", "Quay lại: Synthetic list");

    await contains(".o_tp_back_button").click();
    await animationFrame();
    expect(".o_list_view").toHaveCount(1);
    expect(".o_tp_back_button").toHaveCount(0);
});

test("tooltip falls back to a generic label when the previous screen has no name", async () => {
    await mountWebClient();
    await getService("action").doAction({ ...LIST_ACTION, name: "" });
    await contains(".o_data_row:eq(0) .o_data_cell").click();
    expect(".o_tp_back_button").toHaveAttribute("title", "Quay lại danh sách");
});

test("dirty form: stay keeps the edit, discard leaves without saving", async () => {
    await mountWebClient();
    await getService("action").doAction(LIST_ACTION);
    await contains(".o_data_row:eq(0) .o_data_cell").click();
    await contains(".o_field_widget[name=name] input").edit("Synthetic changed");

    await contains(".o_tp_back_button").click();
    expect(".modal .o_tp_back_save").toHaveCount(1);
    expect(".modal .o_tp_back_discard").toHaveCount(1);
    await contains(".modal .o_tp_back_stay").click();
    expect(".o_form_view").toHaveCount(1);
    expect(".o_field_widget[name=name] input").toHaveValue("Synthetic changed");

    await contains(".o_tp_back_button").click();
    await contains(".modal .o_tp_back_discard").click();
    await animationFrame();
    expect(".o_list_view").toHaveCount(1);
    expect(".o_data_row:eq(0) .o_data_cell").toHaveText("Synthetic A");
});

test("no back button in a dialog form", async () => {
    await mountWebClient();
    await getService("action").doAction({
        type: "ir.actions.act_window",
        res_model: "tp.back.partner",
        res_id: 1,
        target: "new",
        views: [[false, "form"]],
    });
    expect(".modal .o_form_view").toHaveCount(1);
    expect(".o_tp_back_button").toHaveCount(0);
});
