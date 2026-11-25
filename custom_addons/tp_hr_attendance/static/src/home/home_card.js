import { APP_LABELS, registerHomeModule, registerHomeSection } from "@tp_web_home/home/home_catalog";
import { ATT_APP_XMLID } from "../prefs";

/**
 * Register standalone "Chấm công" app card in the "Nhân sự và chấm công" Home group
 * right after "Quản lý nhân sự" (order 10) and before "Tuyển dụng" (order 30).
 * Visibility strictly follows server-filtered menu rights (`requiresMenu: true`).
 */
registerHomeSection({ key: "hr", label: "Nhân sự và chấm công", order: 10 });

registerHomeModule({
    key: "attendance",
    group: "hr",
    order: 20,
    requiresMenu: true,
    name: "Chấm công",
    description: "Tổng quan chấm công, công cá nhân và điều chỉnh công",
    status: "Đang hoạt động",
    badgeKind: "active",
    icon: "clock",
    xmlid: ATT_APP_XMLID,
    aliases: "cham cong bang cong cong cua toi di muon dieu chinh cong enti attendance",
    copy: "Không gian chấm công độc lập: tổng quan chấm công, công cá nhân, xuất bảng công, đề nghị điều chỉnh công và quản trị đồng bộ theo quyền.",
});

APP_LABELS[ATT_APP_XMLID] = {
    label: "Chấm công",
    hint: "Tổng quan chấm công, công cá nhân và điều chỉnh công",
    group: "hr",
    order: 20,
    icon: "clock",
    aliases: "cham cong bang cong cong cua toi di muon dieu chinh cong attendance",
};
