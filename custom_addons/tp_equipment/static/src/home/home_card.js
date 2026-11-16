import { ADMIN_MODULES, APP_LABELS, SECTIONS } from "@tp_web_home/home/home_catalog";

/**
 * EQUIP-001 Home card. Metadata only: the card renders when the server sent the
 * "Kho thiết bị văn phòng" menu, which is restricted to system administrators.
 */
if (!SECTIONS.some((s) => s.key === "operations")) {
    const personal = SECTIONS.findIndex((s) => s.key === "personal");
    SECTIONS.splice(personal < 0 ? SECTIONS.length : personal, 0, {
        key: "operations",
        label: "Vận hành nội bộ",
    });
}

if (!ADMIN_MODULES.some((m) => m.key === "equipment")) {
    ADMIN_MODULES.push({
        key: "equipment",
        group: "operations",
        name: "Kho thiết bị văn phòng",
        description: "Thiết bị, gán / đổi / trả kho và yêu cầu đề xuất",
        status: "Chỉ quản trị hệ thống",
        badgeKind: "active",
        icon: "monitor",
        xmlid: "tp_equipment.menu_root",
        aliases: "kho thiet bi van phong may tinh may in photocopy ban giao sua chua kiem ke equipment it asset",
        copy: "Một danh sách thiết bị trên cùng dữ liệu nhân sự: ai đang dùng máy nào, máy nào còn trong kho; gán, đổi máy, trả về kho và yêu cầu đề xuất. Chỉ quản trị hệ thống truy cập.",
    });
}

APP_LABELS["tp_equipment.menu_root"] = {
    label: "Kho thiết bị văn phòng",
    hint: "Thiết bị, gán / đổi / trả kho, yêu cầu đề xuất",
    group: "workspace",
    order: 30,
    aliases: "kho thiet bi van phong equipment",
};
