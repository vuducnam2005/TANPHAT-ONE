import { APP_LABELS, registerHomeModule, registerHomeSection } from "@tp_web_home/home/home_catalog";
import { registry } from "@web/core/registry";
registerHomeSection({ key: "reporting", label: "Báo cáo và phê duyệt", order: 20 });
registerHomeModule({
    key: "reporting",
    group: "reporting",
    order: 10,
    requiresMenu: true,
    name: "Báo cáo",
    description: "Mục tiêu, kế hoạch và báo cáo toàn công ty",
    status: "Trong phạm vi được cấp",
    badgeKind: "active",
    icon: "bar-chart",
    xmlid: "tp_reporting.menu_root",
    aliases: "bao cao ke hoach muc tieu reporting",
    copy: "Lập kế hoạch quý–tháng–tuần; tổng hợp kết quả cá nhân, phòng ban và công ty.",
});
APP_LABELS["tp_reporting.menu_root"] = {
    label: "Báo cáo",
    hint: "Mục tiêu, kế hoạch và kết quả",
    group: "reporting",
    order: 10,
    icon: "bar-chart",
    aliases: "bao cao ke hoach muc tieu reporting",
};
const fallback = registry.category("tp_back_fallbacks");
for (const [model, action] of Object.entries({ "tp.report.review": "reviews", "tp.report.plan": "plans", "tp.report.document": "personal", "tp.report.line": "lines", "tp.report.snapshot": "snapshots", "tp.report.obligation": "obligations", "tp.report.template": "templates", "tp.report.section": "sections", "tp.report.assignment": "assignments", "tp.report.metric": "metrics", "tp.report.value": "values", "tp.report.schedule": "schedules", "tp.report.directive": "directives" })) {
    fallback.add(model, `tp_reporting.action_${action}`, { force: true });
}
