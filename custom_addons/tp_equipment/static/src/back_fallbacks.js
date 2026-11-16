import { registry } from "@web/core/registry";

/**
 * UI-BACK-001 / EQUIP-SIMPLE-003: where the shared "Quay lại" goes for an equipment detail opened by deep link
 * (no previous screen in the action stack). Every managed, unmounted device/component → the single "Thiết bị"
 * list (it shows stock, in use, shared, located and at-vendor machines); drafts, retired machines, services and
 * mounted components → "Tất cả hồ sơ thiết bị" (Phạm vi nâng cao).
 */
const backFallbacks = registry.category("tp_back_fallbacks");

const HOLDER_FIELDS = ["tp_lifecycle", "tp_asset_class", "tp_parent_id", "tp_custody"];

function equipmentBackTarget(data) {
    const inMainScope = data?.tp_lifecycle === "active"
        && ["device", "component"].includes(data?.tp_asset_class)
        && !data?.tp_parent_id;
    return inMainScope ? "tp_equipment.action_equipment" : "tp_equipment.action_equipment_all_records";
}

backFallbacks.add("maintenance.equipment", async (data, { resId, orm } = {}) => {
    let info = data || {};
    // A model-only URL (/odoo/maintenance.equipment/<id>) is served by the base maintenance form,
    // which does not carry the custody fields: read them (read-only) to pick the right list.
    if ((info.tp_lifecycle === undefined || info.tp_asset_class === undefined) && resId && orm) {
        const [row] = await orm.read("maintenance.equipment", [resId], HOLDER_FIELDS);
        info = row || {};
    }
    return equipmentBackTarget(info);
}, { force: true });

for (const [model, xmlid] of Object.entries({
    "tp.equipment.move": "tp_equipment.action_moves",
    "maintenance.request": "tp_equipment.action_repairs",
    "tp.equipment.proposal": "tp_equipment.action_proposals",
    "tp.equipment.receipt": "tp_equipment.action_receipts",
    "tp.equipment.inventory": "tp_equipment.action_inventories",
    "tp.equipment.import.batch": "tp_equipment.action_import",
    "maintenance.equipment.category": "tp_equipment.action_category",
    "tp.equipment.location": "tp_equipment.action_location",
})) {
    backFallbacks.add(model, xmlid, { force: true });
}
