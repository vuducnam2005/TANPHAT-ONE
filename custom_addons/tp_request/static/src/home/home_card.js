/** @odoo-module **/
import { ADMIN_MODULES, APP_LABELS, SECTIONS } from "@tp_web_home/home/home_catalog";

/**
 * Register "Đề nghị & Phê duyệt" on TANPHAT ONE Home without modifying tp_web_home.
 * Visibility follows the server-filtered menu tree (all internal users with base.group_user).
 */
if (!SECTIONS.some((s) => s.key === "operations")) {
    const personal = SECTIONS.findIndex((s) => s.key === "personal");
    SECTIONS.splice(personal < 0 ? SECTIONS.length : personal, 0, {
        key: "operations",
        label: "Vận hành nội bộ",
    });
}

if (!ADMIN_MODULES.some((m) => m.key === "tp_request")) {
    ADMIN_MODULES.push({
        key: "tp_request",
        group: "operations",
        name: "Đề nghị & Phê duyệt",
        description: "Gửi đề nghị, phê duyệt và theo dõi thực hiện nội bộ",
        status: "Đang hoạt động",
        badgeKind: "active",
        icon: "request_check",
        xmlid: "tp_request.menu_root",
        aliases: "de nghi phe duyet request approval dieu chinh cong thiet bi it ho tro",
        copy: "Nơi dùng chung toàn công ty để lập đề nghị, phê duyệt tuần tự, thực hiện sau duyệt và theo dõi tiến trình.",
    });
}

APP_LABELS["tp_request.menu_root"] = {
    label: "Đề nghị & Phê duyệt",
    hint: "Lập đề nghị, phê duyệt và theo dõi thực hiện",
    group: "workspace",
    order: 25,
    aliases: "de nghi phe duyet request approval",
};
