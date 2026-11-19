import { Component, onMounted, onWillStart, onWillUnmount, proxy, useProps } from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { rpcError } from "./common";
import { openAttendanceUpload } from "./upload/upload";

/**
 * "Nguồn dữ liệu chấm công" (HR/admin area, ENTI-LIVE-001). Displays both Excel fallback and
 * live ENTI API connector status, employee mapping progress, sync trigger, and import history.
 */
export class AttendanceSources extends Component {
    static template = "tp_hr_attendance.Sources";
    props = useProps();

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        try {
            this.busService = useService("bus_service");
        } catch (_) {
            this.busService = null;
        }
        this.state = proxy({ loading: true, error: "", data: null });
        this.pollTimer = null;

        onWillStart(async () => {
            if (this.busService) {
                try {
                    this.busService.addChannel("tp_hr_attendance_channel");
                    this.busService.subscribe("enti_sync_completed", () => this.load());
                } catch (_) {}
            }
            await this.load();
        });

        onMounted(() => {
            this.pollTimer = browser.setInterval(() => {
                if (!document.hidden && !this.state.loading) {
                    this.load();
                }
            }, 30000);
        });

        onWillUnmount(() => {
            if (this.pollTimer) {
                browser.clearInterval(this.pollTimer);
            }
        });
    }

    get data() {
        return this.state.data;
    }
    get referenceHours() {
        return (this.data?.reference_hours || "08:30-17:00").replace("-", "–");
    }

    async load() {
        this.state.loading = true;
        this.state.error = "";
        try {
            this.state.data = await this.orm.call("tp.hr.attendance.source", "tp_sources_overview", [{}]);
        } catch (error) {
            this.state.error = rpcError(error, "Không tải được nguồn dữ liệu chấm công. Vui lòng thử lại.");
        } finally {
            this.state.loading = false;
        }
    }

    async syncEntiNow() {
        this.state.loading = true;
        this.state.error = "";
        try {
            const res = await this.orm.call("tp.hr.attendance.source", "action_sync_enti_quick", []);
            if (this.notification) {
                this.notification.add(
                    `Đồng bộ ENTI thành công: ${res.employees || 0} nhân viên, ${res.days_applied || 0} ngày công.`,
                    { type: "success" }
                );
            }
            await this.load();
        } catch (error) {
            this.state.error = rpcError(error, "Đồng bộ ENTI thất bại. Vui lòng kiểm tra lại cấu hình hoặc kết nối mạng.");
        } finally {
            this.state.loading = false;
        }
    }

    openUpload() {
        openAttendanceUpload(this.env, {
            onApplied: () => this.load(),
            onOpenPeriod: (period) => this.action.doAction({
                type: "ir.actions.client", tag: "tp_hr_attendance.board", name: "Bảng chấm công", params: { from: period.from, to: period.to },
            }),
        });
    }
    openBatch(row) {
        return this.action.doAction({
            type: "ir.actions.act_window", name: "Lô nhập dữ liệu công", res_model: "tp.hr.attendance.batch", res_id: row.id,
            views: [[false, "form"]], target: "current",
        });
    }
    open(xmlid) {
        return this.action.doAction(xmlid);
    }
}

registry.category("actions").add("tp_hr_attendance.sources", AttendanceSources);
