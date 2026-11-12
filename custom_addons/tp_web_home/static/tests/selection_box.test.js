import { describe, expect, test } from "@odoo/hoot";
import { contains, defineModels, defineWebModels, fields, models, mountView } from "@web/../tests/web_test_helpers";

// HR-CORRECTION-008: the list selection counter reads in Vietnamese order ("Đã chọn 1 hồ sơ").
class TpSelectionPartner extends models.Model {
    _name = "tp.selection.partner";
    name = fields.Char();
    _records = [
        { id: 1, name: "Synthetic A" },
        { id: 2, name: "Synthetic B" },
        { id: 3, name: "Synthetic C" },
    ];
}
// The list view loads user settings (res.users) from the mock server, as in web's own list tests.
defineWebModels();
defineModels([TpSelectionPartner]);

describe.current.tags("desktop");

test("selection counter uses Vietnamese word order and keeps select-all", async () => {
    await mountView({ resModel: "tp.selection.partner", type: "list", arch: `<list limit="2"><field name="name"/></list>` });
    await contains(".o_data_row:eq(0) .o_list_record_selector input").click();
    expect(".o_selection_box .o_tp_selection_count").toHaveText("Đã chọn 1 hồ sơ");
    expect(".o_selection_box").not.toHaveText(/selected/);

    // The whole page (2 of 3) is selected: the native select-all offer stays, in Vietnamese.
    await contains(".o_data_row:eq(1) .o_list_record_selector input").click();
    expect(".o_selection_box .o_tp_selection_count").toHaveText("Đã chọn 2 hồ sơ");
    expect(".o_selection_box .o_select_domain").toHaveText("Chọn tất cả 3");

    await contains(".o_selection_box .o_select_domain").click();
    expect(".o_selection_box .o_tp_selection_count").toHaveText("Đã chọn tất cả 3 hồ sơ");

    await contains(".o_selection_box .o_unselect_all").click();
    expect(".o_selection_box").toHaveCount(0);

    await contains("thead .o_list_record_selector input").click();
    expect(".o_selection_box .o_tp_selection_count").toHaveText("Đã chọn 2 hồ sơ");
});
