/** @odoo-module **/
import { registerHomeModule } from "@tp_web_home/home/home_catalog";

// Activate the existing "Tuyển dụng" Home card (order: 5 in "Nhân sự và chấm công") without touching tp_web_home!
registerHomeModule({
    key: "recruitment",
    group: "hr",
    order: 5,
    placeholderOnly: false,
    featured: true,
    name: "Tuyển dụng",
    status: "Đang hoạt động",
    badgeKind: "active",
    icon: "user-plus",
    xmlid: "tp_enterprise_ops.menu_recruitment_root",
    aliases: "tuyen dung ung vien recruitment phỏng vấn",
});
