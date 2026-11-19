import { describe, expect, test } from "@odoo/hoot";
import { contains, defineModels, editSearch, fields, models, mountView, mountWithCleanup, onRpc, mockService, removeFacet, validateSearch } from "@web/../tests/web_test_helpers";
import { defineMailModels } from "@mail/../tests/mail_test_helpers";
import { HrOverview } from "@tp_hr_workspace/overview/overview";
import "@tp_hr_workspace/table/table";
import "@tp_hr_workspace/profile/employee_profile";
import { TpHrHierarchyModel } from "@tp_hr_workspace/hierarchy/hierarchy";
class HrUiRow extends models.Model {
    _name="hr.ui.row";
    name=fields.Char();
    team=fields.Char();
    _records=Array.from({length:118},(_,i)=>({id:i+1,name:`Synthetic ${i+1}`,team:i%2?'Alpha':'Beta'}));
}
class HrUiDepartment extends models.Model {
    _name = "hr.department";
    name = fields.Char();
    active = fields.Boolean({ default: true });
    _records = [{ id: 1, name: "Thiết kế", active: true }, { id: 2, name: "Ban Giám đốc", active: true }];
}
class HrUiJob extends models.Model {
    _name = "hr.job";
    name = fields.Char();
    _records = [{ id: 1, name: "Tổng giám đốc" }, { id: 2, name: "Nhân viên" }];
}
class HrUiEmployee extends models.Model {
    _name = "hr.employee";
    name = fields.Char();
    department_id = fields.Many2one({relation: "hr.department"});
    job_id = fields.Many2one({relation: "hr.job"});
    parent_id = fields.Many2one({relation: "hr.employee"});
    child_ids = fields.One2many({relation: "hr.employee", relation_field: "parent_id"});
    image_128 = fields.Image();
    tp_employment_kind = fields.Selection({selection:[["short_term","Ngắn hạn"],["long_term","Dài hạn"],["outsourced","Thuê khoán"]]});
    _records = [{id:1,name:"Synthetic employee",department_id:1,job_id:1,parent_id:false,child_ids:[]}];
}
defineModels([HrUiRow, HrUiDepartment, HrUiJob, HrUiEmployee]);
defineMailModels();
const population = {total:39,units:9,missing_basic:2,complete_basic:37,linked:0,pending:39,updated_at:"2026-11-11",domain:[],departments:[{id:42,name:"Synthetic unit",count:39}], jobs:[{id:7,name:"Synthetic role",count:39}], catalog_jobs:[{id:7,name:"Synthetic role"}]};
describe("HR-001 mounted native UI",()=>{
    test("employment keeps unknown distinct and editing uses the record field",async()=>{
        await mountView({type:"form",resModel:"hr.employee",resId:1,arch:'<form><field name="tp_employment_kind" widget="tp_hr_employment"/></form>'});
        expect('[aria-label="Loại hình lao động"]').toHaveValue('');
        await contains('[aria-label="Loại hình lao động"]').select('outsourced');
        await contains('.o_form_button_save').click();
        expect('[aria-label="Loại hình lao động"]').toHaveValue('outsourced');
    });
    test("employee department sections survive clearing search without a group facet",async()=>{
        onRpc('web_read_group', ({ kwargs }) => { expect(kwargs.groupby).toEqual(['department_id']); });
        await mountView({type:"list",resModel:"hr.employee",arch:'<list js_class="tp_hr_table" expand="1"><field name="department_id"/><field name="name"/></list>',searchViewArch:'<search><field name="name" string="Name"/></search>',context:{tp_filter_profile:'pending'}});
        // Profile lists (pending, missing, archived, directory) keep the native search bar.
        expect('.o_tp_hr_employee_list').toHaveCount(1);
        expect('.o_searchview_facet').toHaveCount(0);
        expect('.o_group_header').toHaveCount(1);
        expect('.o_group_header').toHaveText(/1 thành viên/);
        expect('thead th[data-name="department_id"]').toHaveCount(0);
        expect('.o_data_row [name="department_id"]').toHaveCount(0);
        expect('.o_data_row [name="name"]').toHaveText('Synthetic employee');
        expect('.o_tp_hr_list_heading').toHaveCount(0);
        await editSearch('absent employee');
        await validateSearch();
        expect('.o_data_row').toHaveCount(0);
        expect('.o_searchview_facet').toHaveCount(1);
        await contains('.o_searchview_facet .o_facet_remove').click();
        expect('.o_searchview_facet').toHaveCount(0);
        expect('.o_group_header').toHaveCount(1);
        expect('.o_data_row [name="name"]').toHaveText('Synthetic employee');
        expect('.o_data_row [name="department_id"]').toHaveCount(0);
    });
    test("removing employee filters and secondary groups keeps department sections",async()=>{
        await mountView({type:"list",resModel:"hr.employee",arch:'<list js_class="tp_hr_table" expand="1"><field name="department_id"/><field name="name"/></list>',searchViewArch:'<search><filter name="matching" string="Matching" domain="[(\'id\',\'=\',1)]"/><group><filter name="name" string="Name group" context="{\'group_by\':\'name\'}"/></group></search>',context:{search_default_matching:1,search_default_name:1,tp_filter_profile:'pending'}});
        expect('.o_searchview_facet').toHaveCount(2);
        expect('.o_group_header').toHaveCount(2);
        await removeFacet('Name group');
        expect('.o_group_header').toHaveCount(1);
        expect('thead th[data-name="department_id"]').toHaveCount(0);
        await removeFacet('Matching');
        expect('.o_searchview_facet').toHaveCount(0);
        expect('.o_group_header').toHaveCount(1);
        expect('.o_data_row [name="name"]').toHaveText('Synthetic employee');
    });
    test("profile cancel confirms dirty fields and preserves them when dismissed",async()=>{
        await mountView({type:"form",resModel:"hr.ui.row",resId:1,arch:'<form js_class="tp_hr_profile"><sheet><field name="name"/></sheet></form>'});
        await contains('.o_tp_hr_edit').click();
        await contains('[name="name"] input').edit('Synthetic changed');
        await contains('.o_tp_hr_cancel').click();
        expect('.modal').toHaveText(/Bỏ thay đổi chưa lưu/);
        await contains('.modal .btn-secondary').click();
        expect('[name="name"] input').toHaveValue('Synthetic changed');
        await contains('.o_tp_hr_cancel').click();
        await contains('.modal .btn-primary').click();
        expect('[name="name"]').toHaveText('Synthetic 1');
        expect('.o_tp_hr_edit').toHaveCount(1);
    });
    test("grouped table labels count groups and clear restores flat results",async()=>{
        await mountView({type:"list",resModel:"hr.ui.row",arch:'<list js_class="tp_hr_table"><field name="name"/><field name="team"/></list>',searchViewArch:'<search><field name="name"/><group><filter name="team" string="Team" context="{\'group_by\':\'team\'}"/></group></search>',context:{search_default_team:1}});
        expect('.o_group_header').toHaveCount(2);
        expect('.o_tp_hr_result_count').toHaveText(/2 nhóm kết quả/);
        expect('.o_tp_hr_page_size').toHaveText(/nhóm mỗi trang/);
        await contains('.o_tp_hr_clear').click();
        expect('.o_group_header').toHaveCount(0);
        expect('.o_tp_hr_result_count').toHaveText('118 kết quả');
    });
    test("empty HR tables have an actionable explanation and no fake rows",async()=>{
        await mountView({type:"list",resModel:"hr.ui.row",domain:[["id","=",0]],arch:'<list js_class="tp_hr_table"><field name="name"/></list>'});
        expect('.o_tp_hr_empty').toHaveCount(1);
        expect('.o_tp_hr_empty').toHaveText(/Chưa có dữ liệu/);
        expect('.o_list_table tbody tr').toHaveCount(0);
    });
    test("list applies actual server limit for every allowed size",async()=>{
        await mountView({type:"list",resModel:"hr.ui.row",arch:'<list js_class="tp_hr_table"><field name="name"/></list>',searchViewArch:'<search><field name="name"/></search>'});
        expect('.o_data_row').toHaveCount(20);
        for (const size of [10,50,100,20]) {
            await contains('[aria-label="Số dòng mỗi trang"]').select(String(size));
            expect('.o_data_row').toHaveCount(size);
        }
    });
    test("page-size failure is visible and a subsequent selection retries",async()=>{
        let fail = true;
        onRpc('web_search_read', ({ kwargs }) => { if (kwargs.limit === 50 && fail) throw Error('offline'); });
        await mountView({type:"list",resModel:"hr.ui.row",arch:'<list js_class="tp_hr_table"><field name="name"/></list>'});
        await contains('[aria-label="Số dòng mỗi trang"]').select('50');
        expect('.o_tp_hr_table_tools [role="alert"]').toHaveText(/Không tải được trang/);
        fail = false;
        await contains('[aria-label="Số dòng mỗi trang"]').select('50');
        expect('.o_data_row').toHaveCount(50);
        expect('.o_tp_hr_table_tools [role="alert"]').toHaveCount(0);
    });
    test("overview filter reaches backend and chart click opens scoped action",async()=>{
        const calls=[];
        mockService("orm",{call:async(model,method,args)=>{calls.push({method,args});return method==='get_overview' ? population : {type:'ir.actions.act_window'};}});
        mockService("action",{doAction:(action)=>expect.step(action.type)});
        await mountWithCleanup(HrOverview);
        expect('.o_tp_hr_donut_total').toHaveText('39');
        expect('.o_tp_hr_charts tbody tr').toHaveCount(1);
        await contains('.o_tp_hr_filters label:first-child select').select('42');
        expect(calls.at(-1).args[0].department_id).toBe(42);
        await contains('.o_tp_hr_charts tbody button').click();
        expect(calls.at(-1).args[1]).toEqual([['department_id','=',42]]);
        expect.verifySteps(['ir.actions.act_window']);
    });
    test("empty population exposes an explanation and no chart",async()=>{
        mockService("orm",{call:async()=>({...population,total:0,units:0,departments:[]})});
        await mountWithCleanup(HrOverview);
        expect('.o_tp_hr_message').toHaveText(/Không có hồ sơ/);
        expect('.o_tp_hr_charts').toHaveCount(0);
    });
    test("failed overview exposes retry and recovers",async()=>{
        let count=0;
        mockService("orm",{call:async()=>{if (!count++) throw Error('offline'); return population;}});
        await mountWithCleanup(HrOverview);
        expect('[role="alert"]').toHaveText(/Không tải được/);
        await contains('[role="alert"] button').click();
        expect('.o_tp_hr_donut_total').toHaveText('39');
    });
    test("job filter and reset use the backend population",async()=>{
        const calls=[];
        mockService("orm",{call:async(model,method,args)=>{calls.push(args[0]);return population;}});
        await mountWithCleanup(HrOverview);
        expect('.o_tp_hr_kpis > *').toHaveCount(5);
        await contains('[aria-label="Lọc chức vụ"]').select('7');
        expect(calls.at(-1).job_id).toBe(7);
        await contains('.o_tp_hr_filters button').click();
        expect(calls.at(-1)).toEqual({department_id:false,job_id:false,status:'active',employment_kind:''});
    });
    test("late response cannot replace newer data; actions stay blocked while loading",async()=>{
        const component = Object.create(HrOverview.prototype);
        component.state={department:'',job:'',status:'active',data:null,catalog:[],jobs:[],loading:false,error:''};
        component.request=0;
        let resolveOld;
        const old = new Promise(resolve=>{resolveOld=resolve;});
        let calls=0,actionCalls=0;
        component.orm={call:()=>++calls===1?old:Promise.resolve({...population,total:2})};
        component.action={doAction:()=>actionCalls++};
        const first=component.load();
        await component.openEmployees();
        expect(actionCalls).toBe(0);
        component.state.job='7';
        await component.load();
        resolveOld(population);
        await first;
        expect(component.state.data.total).toBe(2);
        expect(component.loadedFilters.job_id).toBe(7);
        expect(component.state.loading).toBe(false);
    });
    test("legend focus links highlight and tooltip; chart keyboard keeps department domain",async()=>{
        const calls=[];
        mockService("orm",{call:async(model,method,args)=>{calls.push({method,args});return method==='get_overview' ? population : {type:'ir.actions.act_window'};}});
        mockService("action",{doAction:()=>{}});
        await mountWithCleanup(HrOverview);
        await contains('.o_tp_hr_legend button').focus();
        expect('[role="tooltip"]').toHaveText(/Synthetic unit[\s\S]*39 hồ sơ.*100.0%/);
        expect('.o_tp_hr_donut path.is-highlighted').toHaveCount(1);
        await contains('[aria-label="Lọc chức vụ"]').focus();
        expect('[role="tooltip"]').toHaveCount(0);
        const component=Object.create(HrOverview.prototype);
        component.state={loading:false,error:'',data:population};component.loadedFilters={department_id:false,job_id:false,status:'active'};
        component.orm={call:async(model,method,args)=>{calls.push({method,args});return {type:'ir.actions.act_window'};}};
        component.action={doAction:()=>{}};
        let prevented=false;
        await component.onSliceKey({key:' ',preventDefault:()=>prevented=true},{id:42});
        expect(prevented).toBe(true);
        expect(calls.at(-1).args[1]).toEqual([['department_id','=',42]]);
    });
    test("hierarchy view exposes department filter with Ban Giam doc first and preserves root order",async()=>{
        onRpc("hr.employee", "hierarchy_read", () => [
            { id: 10, name: "Lê Nguyên Tuấn", department_id: { id: 2, display_name: "Ban Giám đốc" }, job_id: { id: 1, display_name: "Tổng giám đốc" }, parent_id: false, child_ids: [] },
            { id: 11, name: "An Nhân Viên", department_id: { id: 1, display_name: "Thiết kế" }, job_id: { id: 2, display_name: "Nhân viên" }, parent_id: { id: 99, display_name: "Quản lý ngoài lọc" }, child_ids: [] },
        ]);
        await mountView({
            type: "hierarchy",
            resModel: "hr.employee",
            arch: '<hierarchy js_class="tp_hr_hierarchy" child_field="child_ids"><field name="name"/><field name="parent_id"/><field name="department_id"/><field name="job_id"/><field name="child_ids"/><templates><t t-name="hierarchy-box"><div class="tp_test_card"><field name="name"/></div></t></templates></hierarchy>',
            searchViewArch: '<search><field name="name"/><field name="department_id"/></search>',
        });
        expect('.o_tp_hr_dept_select option').toHaveCount(3);
        expect('.o_tp_hr_dept_select option:nth-child(2)').toHaveText('Ban Giám đốc');
        expect('.o_hierarchy_node .tp_test_card:first').toHaveText('Lê Nguyên Tuấn');
        await contains('.o_tp_hr_dept_select').select('2');
        expect('.o_searchview_facet').toHaveText(/Phòng ban: Ban Giám đốc/);
        await contains('.o_tp_hr_hierarchy_clear').click();
        expect('.o_searchview_facet').toHaveCount(0);
        expect('.o_tp_hr_dept_select').toHaveValue('');
        const model = Object.create(TpHrHierarchyModel.prototype);
        model.parentFieldName = "parent_id";
        model.childFieldName = "child_ids";
        expect(model._formatData([
            { id: 10, name: "Lê Nguyên Tuấn", parent_id: false, child_ids: [] },
            { id: 11, name: "An Nhân Viên", parent_id: { id: 99, display_name: "Outside" }, child_ids: [] },
        ]).map((r) => r.id)).toEqual([10, 11]);
    });
});
