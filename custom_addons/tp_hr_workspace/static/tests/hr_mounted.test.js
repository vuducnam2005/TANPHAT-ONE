import { describe, expect, test } from "@odoo/hoot";
import { contains, defineModels, fields, models, mountView, mountWithCleanup, onRpc, mockService } from "@web/../tests/web_test_helpers";
import { defineMailModels } from "@mail/../tests/mail_test_helpers";
import { HrOverview } from "@tp_hr_workspace/overview/overview";
import "@tp_hr_workspace/table/table";
class HrUiRow extends models.Model {
    _name="hr.ui.row";
    name=fields.Char();
    _records=Array.from({length:118},(_,i)=>({id:i+1,name:`Synthetic ${i+1}`}));
}
defineModels([HrUiRow]);
defineMailModels();
const population = {total:39,units:9,missing_basic:2,complete_basic:37,linked:0,pending:39,updated_at:"2026-11-11",domain:[],departments:[{id:42,name:"Synthetic unit",count:39}], jobs:[{id:7,name:"Synthetic role",count:39}], catalog_jobs:[{id:7,name:"Synthetic role"}]};
describe("HR-001 mounted native UI",()=>{
    test("list applies actual server limit for every allowed size",async()=>{
        await mountView({type:"list",resModel:"hr.ui.row",arch:'<list js_class="tp_hr_table"><field name="name"/></list>',searchViewArch:'<search><field name="name"/></search>'});
        expect('.o_data_row').toHaveCount(20);
        for (const size of [10,50,100,20]) {
            await contains('[aria-label="Số dòng mỗi trang"]').select(String(size));
            expect('.o_data_row').toHaveCount(size);
        }
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
        expect(calls.at(-1)).toEqual({department_id:false,job_id:false,status:'active'});
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
});
