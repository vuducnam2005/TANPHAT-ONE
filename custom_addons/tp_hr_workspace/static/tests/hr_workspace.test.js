import { describe, expect, test } from "@odoo/hoot";
import { patchWithCleanup } from "@web/../tests/web_test_helpers";
import { browser } from "@web/core/browser/browser";
import { user } from "@web/core/user";
import { chartSegments, departmentColor, donutPath, HrOverview } from "@tp_hr_workspace/overview/overview";
import { readPageSize, writePageSize, tablePageKey, fold } from "@tp_hr_workspace/prefs";
import { HrListRenderer } from "@tp_hr_workspace/table/table";
import { ListRenderer } from "@web/views/list/list_renderer";
describe("TP HR display contract", () => {
    test("department segments conserve total without collapsing units", () => {
        const rows = chartSegments(Array.from({length:9}, (_,i) => ({id:i+1,name:`Đơn vị ${i+1}`,count:i+1})),45);
        expect(rows.length).toBe(9);
        expect(Math.round(rows.reduce((sum,row) => sum+row.percent,0))).toBe(100);
        expect(chartSegments([],0)).toEqual([]);
        expect(chartSegments([{id:4,count:3}],3)[0].color).toBe(chartSegments([{id:8,count:1},{id:4,count:3}],4)[1].color);
    });
    test("ID colors survive reorder/filter and avoid old modulo collisions", () => {
        const ids=[0,18,27,28,29,30,31,32,33];
        const rows=ids.map(id=>({id,count:1}));
        const colors=ids.map(id=>departmentColor(id,rows));
        expect(new Set(colors).size).toBe(ids.length);
        expect(departmentColor(18) === departmentColor(27)).toBe(false);
        const reordered=chartSegments([...rows].reverse(),ids.length,[...rows].reverse());
        for(const row of chartSegments(rows,ids.length,rows)) {
            expect(row.color).toBe(reordered.find(other=>other.id===row.id).color);
            expect(row.color).toBe(chartSegments([row],1,rows)[0].color);
        }
    });
    test("donut supports full ring and large sectors; jobs share a zero scale", () => {
        expect(donutPath(100,0)).toInclude('A146,146 0 1 1');
        expect(donutPath(60,0)).toInclude('A146,146 0 1 1');
        const component=Object.create(HrOverview.prototype);
        component.state={data:{total:7,jobs:[{id:3,name:'B',count:2},{id:2,name:'A',count:2},{id:1,name:'C',count:3}]}};
        expect(component.jobs.map(row=>row.id)).toEqual([1,2,3]);
        expect(component.axisTicks).toEqual([0,3]);
        expect(component.axisMax >= component.maxCount).toBe(true);
    });
    test("page length defaults to twenty and rejects invalid persisted values", () => {
        const key = tablePageKey("hr.employee",100,200);
        patchWithCleanup(browser.localStorage,{getItem:()=>"999",setItem:(k,value)=>expect(value).toBe("10")});
        expect(readPageSize(key)).toBe(20);
        writePageSize(key,10);
    });
    test("view and company preferences are isolated", () => {
        const first=tablePageKey("hr.employee",1,1);
        expect(first === tablePageKey("hr.employee",1,2)).toBe(false);
        patchWithCleanup(user,{activeCompanies:[{id:987654}]});
        expect(first === tablePageKey("hr.employee",1,1)).toBe(false);
    });
    test("Vietnamese menu search accepts unaccented text", () => {expect(fold("Hồ sơ Nhân viên")).toBe("ho so nhan vien");});
    test("group labels are scoped to the HR renderer and retain accurate record units", () => {
        const hrRenderer = Object.create(HrListRenderer.prototype);
        hrRenderer.props = {list:{resModel:"hr.ui.row"}};
        expect(hrRenderer.getGroupText({ count: 4 })).toBe("4 bản ghi");
        hrRenderer.props.list.resModel = "hr.employee";
        expect(hrRenderer.getGroupText({ count: 4 })).toBe("4 thành viên");
        expect(hrRenderer.getEmptyRowIds).toEqual([]);
        const baseRenderer = Object.create(ListRenderer.prototype);
        expect(baseRenderer.getGroupText({ count: 4 }) === "4 bản ghi").toBe(false);
    });
});
