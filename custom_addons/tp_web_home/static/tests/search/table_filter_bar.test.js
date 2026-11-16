/** @odoo-module **/
import { describe, expect, test } from "@odoo/hoot";
import { queryOne, waitFor } from "@odoo/hoot-dom";
import {
    contains,
    defineModels,
    defineWebModels,
    editSearch,
    fields,
    models,
    mountView,
    onRpc,
    validateSearch,
} from "@web/../tests/web_test_helpers";
import { ListController } from "@web/views/list/list_controller";
import { listView } from "@web/views/list/list_view";
import { registry } from "@web/core/registry";
import { registerTableFilterProfile } from "@tp_web_home/search/filter_domain";
import { TpTableFilterBar } from "@tp_web_home/search/table_filter_bar";

class TpFilterTestPartner extends models.Model {
    _name = "tp.filter.partner";
    name = fields.Char();
    _records = [
        { id: 1, name: "Chủ đầu tư A" },
        { id: 2, name: "Đơn vị B" },
    ];
}

class TpFilterTestRow extends models.Model {
    _name = "tp.filter.row";
    name = fields.Char({ string: "Tiêu đề" });
    state = fields.Selection({
        string: "Trạng thái",
        selection: [
            ["draft", "Nháp"],
            ["review", "Đang rà soát"],
            ["approved", "Đã duyệt"],
        ],
    });
    partner_id = fields.Many2one({ string: "Đối tác", relation: "tp.filter.partner" });
    is_locked = fields.Boolean({ string: "Khóa" });
    due_date = fields.Date({ string: "Hạn xử lý" });
    logged_at = fields.Datetime({ string: "Thời điểm ghi" });
    _records = [
        { id: 1, name: "Hồ sơ A1", state: "draft", partner_id: 1, is_locked: false, due_date: "2026-11-10", logged_at: "2026-11-10 08:00:00" },
        { id: 2, name: "Hồ sơ B2", state: "review", partner_id: 2, is_locked: true, due_date: "2026-11-14", logged_at: "2026-11-14 23:30:00" },
        { id: 3, name: "Hồ sơ C3", state: "approved", partner_id: false, is_locked: false, due_date: "2026-11-20", logged_at: "2026-11-20 01:00:00" },
        { id: 4, name: "Hồ sơ D4", state: false, partner_id: 1, is_locked: false, due_date: "2026-11-12", logged_at: "2026-11-12 10:00:00" },
    ];
}

class TpFilterTestController extends ListController {
    static template = "tp_web_home.TestFilterListView";
    static components = { ...ListController.components, TpTableFilterBar };
}

registry.category("views").add("tp_filter_test_list", {
    ...listView,
    Controller: TpFilterTestController,
});

defineWebModels();
defineModels([TpFilterTestPartner, TpFilterTestRow]);

registerTableFilterProfile("tp.filter.row", {
    criteria: [
        { key: "name", field: "name", label: "Từ khóa", type: "char" },
        { key: "state", field: "state", label: "Trạng thái", type: "selection", multi: true, allowEmpty: true },
        { key: "partner_id", field: "partner_id", label: "Đối tác", type: "many2one", allowEmpty: true },
        { key: "is_locked", field: "is_locked", label: "Khóa", type: "boolean", positiveLabel: "Đã khóa", negativeLabel: "Chưa khóa" },
        { key: "due_date", field: "due_date", label: "Hạn xử lý", type: "date" },
        { key: "logged_at", field: "logged_at", label: "Thời điểm ghi", type: "datetime" },
    ],
});

const LIST_ARCH = `<list js_class="tp_filter_test_list"><field name="name"/><field name="state"/><field name="partner_id"/><field name="is_locked"/><field name="due_date"/><field name="logged_at"/></list>`;
const SEARCH_ARCH = `<search><field name="name"/><field name="state"/><field name="partner_id"/><field name="is_locked"/><field name="due_date"/><field name="logged_at"/><group><filter name="g_partner" string="Đối tác" context="{'group_by':'partner_id'}"/></group></search>`;

describe("TP TableFilterBar", () => {
    test("pending vs applied: waits for Áp dụng and supports OR within criterion + AND across criteria", async () => {
        let searchCalls = 0;
        onRpc("web_search_read", () => { searchCalls++; });
        await mountView({
            type: "list",
            resModel: "tp.filter.row",
            arch: LIST_ARCH,
            searchViewArch: SEARCH_ARCH,
        });
        expect(".o_data_row").toHaveCount(4);
        const initialCalls = searchCalls;

        // Open multi-select state & pick draft + review (OR inside state), without applying yet.
        await contains(".tp_filter_multi_btn").click();
        await contains('.tp_filter_popover label:contains("Nháp") input').click();
        await contains('.tp_filter_popover label:contains("Đang rà soát") input').click();
        expect(".tp_filter_pending_note").toHaveCount(1);
        expect(searchCalls).toBe(initialCalls);

        // Also filter is_locked = false (AND across criteria).
        await contains('[data-filter-key="is_locked"] select').select("false");
        await contains(".tp_filter_apply").click();
        expect(".o_data_row").toHaveCount(1);
        expect(".o_data_row [name='name']").toHaveText("Hồ sơ A1");
        expect(".tp_filter_chip").toHaveCount(2);
    });

    test("boolean, unset selection (__false__), date validation (from > to), and datetime TZ domain", async () => {
        const seenDomains = [];
        onRpc("web_search_read", ({ kwargs }) => { seenDomains.push(kwargs.domain); });
        await mountView({
            type: "list",
            resModel: "tp.filter.row",
            arch: LIST_ARCH,
            searchViewArch: SEARCH_ARCH,
        });

        // Invalid date range blocks Apply and shows alert.
        await contains('[data-filter-key="due_date"] input[aria-label="Từ ngày"]').fill("2026-11-20", { instantly: true });
        await contains('[data-filter-key="due_date"] input[aria-label="Đến ngày"]').fill("2026-11-10", { instantly: true });
        await waitFor(".tp_filter_alert");
        expect(".tp_filter_alert").toHaveText(/"Từ ngày" không được lớn hơn "Đến ngày"/);
        expect(".tp_filter_apply").toHaveAttribute("disabled");

        // Fix date range (2026-11-10 -> 2026-11-15) and also test unset selection (__false__).
        const dueFromEl = queryOne('[data-filter-key="due_date"] input[aria-label="Từ ngày"]');
        const dueToEl = queryOne('[data-filter-key="due_date"] input[aria-label="Đến ngày"]');
        dueFromEl.value = "2026-11-10";
        dueFromEl.dispatchEvent(new Event("input", { bubbles: true }));
        dueToEl.value = "2026-11-15";
        dueToEl.dispatchEvent(new Event("input", { bubbles: true }));
        await waitFor(".tp_filter_apply:not([disabled])");
        expect(".tp_filter_alert").toHaveCount(0);
        await contains(".tp_filter_multi_btn").click();
        await contains('.tp_filter_popover label:contains("Chưa khai báo") input').click();
        await contains(".tp_filter_apply").click();
        expect(".o_data_row").toHaveCount(1);
        expect(".o_data_row [name='name']").toHaveText("Hồ sơ D4");

        // Clear all filters then test datetime boundary half-open operator (`<` next day).
        await contains(".tp_filter_clear").click();
        expect(".o_data_row").toHaveCount(4);
        await contains('[data-filter-key="logged_at"] input[aria-label="Từ ngày"]').fill("2026-11-14", { instantly: true });
        await contains('[data-filter-key="logged_at"] input[aria-label="Đến ngày"]').fill("2026-11-14", { instantly: true });
        await contains(".tp_filter_apply").click();
        const lastDomain = seenDomains.at(-1);
        expect(lastDomain.some((leaf) => Array.isArray(leaf) && leaf[0] === "logged_at" && leaf[1] === "<")).toBe(true);
    });

    test("preserves non-managed SearchBar facets & groupBy; clear keeps mandatory domain", async () => {
        await mountView({
            type: "list",
            resModel: "tp.filter.row",
            domain: [["id", "in", [1, 2, 3]]],
            arch: LIST_ARCH,
            searchViewArch: SEARCH_ARCH,
            context: { search_default_g_partner: 1 },
        });
        expect(".o_group_header").toHaveCount(3);
        await editSearch("Hồ sơ");
        await validateSearch();
        expect(".o_searchview_facet").toHaveCount(2);

        await contains('[data-filter-key="is_locked"] select').select("true");
        await contains(".tp_filter_apply").click();
        expect(".o_searchview_facet").toHaveCount(3);
        expect(".o_group_header").toHaveCount(1);
        await contains(".o_group_header").click();
        expect(".o_data_row").toHaveCount(1);

        // Clearing filters removes filters but preserves mandatory action domain (id in [1,2,3], 3 groups) and groupBy!
        await contains(".tp_filter_clear").click();
        expect(".o_group_header").toHaveCount(3);
        expect(".o_data_row").toHaveCount(1);
    });

    test("many2one uses name_search exact ID and handles RPC failure cleanly", async () => {
        await mountView({
            type: "list",
            resModel: "tp.filter.row",
            arch: LIST_ARCH,
            searchViewArch: SEARCH_ARCH,
        });
        await contains('[data-filter-key="partner_id"] input').click();
        await contains('.o-autocomplete--dropdown-item:contains("Đơn vị B")').click();
        await contains(".tp_filter_apply").click();
        expect(".o_data_row").toHaveCount(1);
        expect(".o_data_row [name='name']").toHaveText("Hồ sơ B2");

        // Simulated RPC failure when applying text filter -> shows error alert with Retry.
        let failOnce = true;
        onRpc("web_search_read", () => {
            if (failOnce) {
                failOnce = false;
                throw new Error("Simulated offline");
            }
        });
        await contains('[data-filter-key="name"] input').edit("Hồ sơ B2");
        await contains(".tp_filter_apply").click();
        await contains('.tp_filter_alert button:contains("Thử lại")').click();
        expect(".tp_filter_alert").toHaveCount(0);
        expect(".o_data_row").toHaveCount(1);
    });
});
