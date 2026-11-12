import { describe, expect, test } from "@odoo/hoot";
import { buildAdminCatalog } from "@tp_web_home/home/home_catalog";

describe("HR-001 Home navigation", () => {
    test("admin HR tile prefers the authorized HR workspace and keeps seven tiles", () => {
        const tree={childrenTree:[{id:1,xmlid:"hr.menu_hr_root",name:"Employees",actionID:20},{id:2,xmlid:"tp_hr_workspace.menu_hr",name:"TP HR",actionID:21}]};
        const catalog=buildAdminCatalog(tree);
        expect(catalog.modules.length).toBe(7);
        expect(catalog.hr[0].menu.id).toBe(2);
        expect(catalog.hr[0].href).toBe("/odoo/action-21");
    });
    test("no unauthorized menu is synthesized by the Home catalog", () => {
        const catalog=buildAdminCatalog({childrenTree:[]});
        expect(catalog.hr[0].menu).toBe(undefined);
        expect(catalog.hr[0].href).toBe(undefined);
    });
});
