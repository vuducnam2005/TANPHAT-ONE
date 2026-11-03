import { animationFrame, describe, expect, test } from "@odoo/hoot";
import { getMockEnv, mockService, mountWithCleanup } from "@web/../tests/web_test_helpers";
import { DemoNavigation } from "@tp_demo_workspace/navigation/navigation";
import { defineMailModels } from "@mail/../tests/mail_test_helpers";
import { activeDestination, buildCatalog, DEMO_APP_XMLID, filterCatalog, MODULES, normalizeMenuSearch } from "@tp_demo_workspace/navigation/navigation_catalog";

describe("tp_demo_workspace navigation", () => {
    defineMailModels();
    function tree(business = true) {
        const nodes = MODULES.filter((item) => business || !["crm", "bid"].includes(item.key))
            .flatMap((item) => item.menus.map((key, index) => ({
                id: `${item.key}-${index}`, xmlid: `tp_demo_workspace.${key}`,
                actionID: `${item.key}-${index}`, actionPath: `tp-${item.key}-${index}`,
                name: key.replace("menu_demo_", ""), childrenTree: [],
            })));
        return { xmlid: DEMO_APP_XMLID, childrenTree: nodes };
    }

    test("normalizes Vietnamese accents, case, spaces and đ", () => {
        expect(normalizeMenuSearch("  HỢP   ĐỒNG  ")).toBe("hop dong");
        expect(normalizeMenuSearch("Dự án")).toBe("du an");
    });

    test("keeps all 17 permitted leaf actions and all 12 modules", () => {
        const catalog = buildCatalog(tree());
        expect(catalog).toHaveLength(6);
        expect(catalog.flatMap((group) => group.modules)).toHaveLength(12);
        expect(catalog.flatMap((group) => group.modules.flatMap((item) => item.leaves))).toHaveLength(17);
    });

    test("absent server menus never become search results or links", () => {
        const catalog = buildCatalog(tree(false));
        expect(catalog.flatMap((group) => group.modules)).toHaveLength(10);
        expect(catalog.flatMap((group) => group.modules.flatMap((item) => item.leaves))).toHaveLength(15);
        expect(catalog.map((group) => group.key)).not.toInclude("business");
        expect(filterCatalog(catalog, "crm")).toEqual([]);
        expect(filterCatalog(catalog, "dau thau")).toEqual([]);
        expect(buildCatalog({ xmlid: "tp_core.menu_platform", childrenTree: tree().childrenTree })).toEqual([]);
        expect(buildCatalog({ xmlid: DEMO_APP_XMLID, childrenTree: [] })).toEqual([]);
    });

    test("Vietnamese and familiar English queries reach the same permitted modules", () => {
        const catalog = buildCatalog(tree());
        for (const query of ["hop dong", "hợp đồng", "contract"]) {
            expect(filterCatalog(catalog, query).flatMap((group) => group.modules).some((item) => item.key === "contracts")).toBe(true);
        }
        for (const [query, key] of [["du an", "projects"], ["project", "projects"], ["dau thau", "bid"], ["request", "request"], ["yêu cầu", "request"], ["tai lieu", "documents"]]) {
            expect(filterCatalog(catalog, query).flatMap((group) => group.modules).some((item) => item.key === key)).toBe(true);
        }
        expect(filterCatalog(catalog, "khongtimthay")).toEqual([]);
        expect(filterCatalog(catalog, "   ")).toEqual(catalog);
    });

    test("current action identifies its leaf and parent without navigation", () => {
        const catalog = buildCatalog(tree());
        expect(activeDestination(catalog, { id: "contracts-1" })?.group).toBe("records");
        expect(activeDestination(catalog, { path: "tp-survey-0" })?.module).toBe("survey");
        expect(activeDestination(catalog, { res_model: "tp.contract.revision" })?.module).toBe("contracts");
        expect(activeDestination(catalog, { id: "outside" })).toBe(null);
        expect(activeDestination(buildCatalog(tree(false)), { id: "crm-0" })).toBe(null);
    });

    test("native view update changes active parent without dispatching another action", async () => {
        const app = { ...tree(), id: 1 };
        const actionService = { currentController: { action: { id: "dashboard-0" } } };
        let dispatched = 0;
        mockService("menu", () => ({
            getCurrentApp: () => app,
            getMenuAsTree: () => app,
            selectMenu: () => { dispatched++; },
        }));
        mockService("action", () => actionService);
        await mountWithCleanup(DemoNavigation);
        expect(".o_tp_demo_group_active").toHaveText("Tổng quan");
        // Window controllers do not supply componentProps.action on UPDATE.
        actionService.currentController = { action: { id: "contracts-1", res_model: "tp.contract.revision" } };
        getMockEnv().bus.trigger("ACTION_MANAGER:UPDATE", { componentProps: { resModel: "tp.contract.revision" } });
        getMockEnv().bus.trigger("ACTION_MANAGER:UI-UPDATED", "current");
        await animationFrame();
        expect(".o_tp_demo_group_active").toHaveText("Hợp đồng & hồ sơ");
        actionService.currentController = { action: { id: "projects-0", res_model: "project.project" } };
        getMockEnv().bus.trigger("ACTION_MANAGER:UI-UPDATED", "current");
        await animationFrame();
        expect(".o_tp_demo_group_active").toHaveText("Dự án & công việc");
        expect(dispatched).toBe(0);
    });
});
