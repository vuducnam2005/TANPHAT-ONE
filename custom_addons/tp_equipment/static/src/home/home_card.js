import { APP_LABELS, registerHomeModule, registerHomeSection } from "@tp_web_home/home/home_catalog";

/**
 * EQUIP-001 Home card. Metadata only: the card renders in the "Kho" group at the
 * bottom of Home only when the server sent the "Kho thiết bị văn phòng" menu.
 */
registerHomeSection({ key: "warehouse", label: "Kho", order: 50 });

registerHomeModule({
    key: "equipment",
    group: "warehouse",
    order: 10,
    requiresMenu: true,
    name: "Kho thiết bị văn phòng",
    description: "Thiết bị, gán / đổi / trả kho và yêu cầu đề xuất",
    status: "Chỉ quản trị hệ thống",
    badgeKind: "active",
    icon: "monitor",
    xmlid: "tp_equipment.menu_root",
    aliases: "kho thiet bi van phong may tinh may in photocopy ban giao sua chua kiem ke equipment it asset",
    copy: "Một danh sách thiết bị trên cùng dữ liệu nhân sự: ai đang dùng máy nào, máy nào còn trong kho; gán, đổi máy, trả về kho và yêu cầu đề xuất. Chỉ quản trị hệ thống truy cập.",
});

APP_LABELS["tp_equipment.menu_root"] = {
    label: "Kho thiết bị văn phòng",
    hint: "Thiết bị, gán / đổi / trả kho, yêu cầu đề xuất",
    group: "warehouse",
    order: 10,
    aliases: "kho thiet bi van phong equipment",
};
