/** @odoo-module **/
import { APP_LABELS, registerHomeModule, registerHomeSection } from "@tp_web_home/home/home_catalog";

/**
 * Register "Yêu cầu phê duyệt" inside the "Báo cáo và phê duyệt" section on TANPHAT ONE Home.
 * Visibility follows the server-filtered menu tree (all internal users with base.group_user).
 */
registerHomeSection({ key: "reporting", label: "Báo cáo và phê duyệt", order: 20 });

registerHomeModule({
    key: "tp_request",
    group: "reporting",
    order: 20,
    requiresMenu: true,
    name: "Yêu cầu phê duyệt",
    description: "Gửi đề nghị, phê duyệt và theo dõi thực hiện nội bộ",
    status: "Đang hoạt động",
    badgeKind: "active",
    icon: "request_check",
    xmlid: "tp_request.menu_root",
    aliases: "yeu cau phe duyet de nghi phe duyet request approval dieu chinh cong thiet bi it ho tro",
    copy: "Nơi dùng chung toàn công ty để lập đề nghị, phê duyệt tuần tự, thực hiện sau duyệt và theo dõi tiến trình.",
});

APP_LABELS["tp_request.menu_root"] = {
    label: "Yêu cầu phê duyệt",
    hint: "Lập đề nghị, phê duyệt và theo dõi thực hiện",
    group: "reporting",
    order: 20,
    aliases: "yeu cau phe duyet de nghi phe duyet request approval",
};
