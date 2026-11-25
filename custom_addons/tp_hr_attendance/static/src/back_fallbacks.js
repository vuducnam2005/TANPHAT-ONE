import { registry } from "@web/core/registry";

// UI-BACK-001: deep-link fallbacks so "Quay lại" on attendance forms stays inside Chấm công.
const backFallbacks = registry.category("tp_back_fallbacks");
for (const [model, xmlid] of Object.entries({
    "tp.hr.attendance.day": "tp_hr_attendance.action_dashboard",
    "tp.hr.attendance.late": "tp_hr_attendance.action_dashboard",
    "tp.hr.attendance.correction": "tp_hr_attendance.action_review",
    "tp.hr.attendance.period": "tp_hr_attendance.action_periods",
    "tp.hr.attendance.log": "tp_hr_attendance.action_periods",
    "tp.hr.attendance.enti.mapping": "tp_hr_attendance.action_enti_mapping",
    "tp.hr.attendance.enti.sync.log": "tp_hr_attendance.action_enti_logs",
    "tp.hr.attendance.enti.employee.image": "tp_hr_attendance.action_sources",
    "tp.hr.attendance.rule": "tp_hr_attendance.action_sources",
    "tp.hr.attendance.code": "tp_hr_attendance.action_sources",
    "tp.hr.attendance.assignment": "tp_hr_attendance.action_sources",
})) {
    backFallbacks.add(model, xmlid, { force: true });
}
