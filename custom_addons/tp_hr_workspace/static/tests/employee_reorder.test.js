import { describe, expect, test } from "@odoo/hoot";
import { contains, defineModels, fields, models, mountView, onRpc, patchWithCleanup } from "@web/../tests/web_test_helpers";
import { defineMailModels } from "@mail/../tests/mail_test_helpers";
import { session } from "@web/session";
import "@tp_hr_workspace/table/table";

class Department extends models.Model {
    _name = "hr.department";
    name = fields.Char();
    _records = [{id: 1, name: "Synthetic A"}, {id: 2, name: "Synthetic B"}];
}
class Employee extends models.Model {
    _name = "hr.employee";
    name = fields.Char();
    sequence = fields.Integer();
    department_id = fields.Many2one({relation: "hr.department"});
    _records = [
        {id: 1, name: "Synthetic Z", sequence: 10, department_id: 1},
        {id: 2, name: "Synthetic A", sequence: 20, department_id: 1},
        {id: 3, name: "Synthetic B", sequence: 10, department_id: 2},
    ];
}
defineModels([Department, Employee]);
defineMailModels();
const arch = '<list js_class="tp_hr_table" expand="1" default_order="sequence,id"><field name="sequence" column_invisible="True"/><field name="department_id"/><field name="name"/></list>';
describe("HR-EMPLOYEE-ORDER mounted mock list", () => {
    test("authorized whole rows stay within separate department boundaries", async () => {
        patchWithCleanup(session, {tp_hr_can_reorder: true});
        await mountView({type: "list", resModel: "hr.employee", arch});
        expect("tbody.o_tp_hr_dept_tbody").toHaveCount(2);
        expect(".o_tp_hr_draggable_row").toHaveCount(3);
        expect("tbody[data-dept-id='1'] .o_data_row").toHaveCount(2);
        expect(".o_tp_hr_drag_handle").toHaveCount(0);
        await contains(".o_data_row[data-res-id='1'] .o_list_record_selector").click();
        expect(".o_form_view").toHaveCount(0);
        expect(".o_list_record_selector input:checked").toHaveCount(1);
    });
    test("native whole-row drop sends real group ID and adjacent anchor", async () => {
        patchWithCleanup(session, {tp_hr_can_reorder: true});
        onRpc("tp_reorder_in_department", ({args}) => {
            expect(args).toEqual([2, 1, 1, null]);
            expect.step("reorder");
            return true;
        });
        await mountView({type: "list", resModel: "hr.employee", arch});
        await contains(".o_data_row[data-res-id='2'] [name='name']").dragAndDrop(".o_data_row[data-res-id='1']");
        expect.verifySteps(["reorder"]);
        expect(".o_form_view").toHaveCount(0);
        expect(".o_list_record_selector input:checked").toHaveCount(0);
    });
    test("column sorting disables dragging and supplies exact reset guidance", async () => {
        patchWithCleanup(session, {tp_hr_can_reorder: true});
        await mountView({type: "list", resModel: "hr.employee", arch});
        await contains("th[data-name='name']").click();
        expect(".o_tp_hr_draggable_row").toHaveCount(0);
        expect(".o_tp_hr_reorder_guidance").toHaveText("Về thứ tự tùy chỉnh và bỏ bộ lọc nhân viên để sắp xếp");
        await contains(".o_tp_hr_reorder_guidance button").click();
        expect(".o_tp_hr_draggable_row").toHaveCount(3);
    });
    test("viewer has no handles while keeping column sorting", async () => {
        patchWithCleanup(session, {tp_hr_can_reorder: false});
        await mountView({type: "list", resModel: "hr.employee", arch});
        expect(".o_tp_hr_drag_handle").toHaveCount(0);
        await contains("th[data-name='name']").click();
        expect("th[data-name='name'] .o_list_sortable_icon").toHaveCount(1);
        expect(".o_tp_hr_reorder_guidance").toHaveCount(0);
    });
});
