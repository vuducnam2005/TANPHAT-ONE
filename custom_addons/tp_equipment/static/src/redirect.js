import { registry } from "@web/core/registry";

/**
 * EQUIP-SIMPLE-003 (DEC-047): the old "Tổng quan thiết bị" client action (path /odoo/tong-quan-thiet-bi, old
 * last-leaf, old bookmarks) now opens the single "Thiết bị" list instead of a dashboard. The ir.actions.client
 * record and its XML ID are kept; only the client-side tag is redirected, so no old link shows a blank screen.
 */
registry.category("actions").add("tp_equipment.dashboard", () => "tp_equipment.action_equipment", { force: true });
