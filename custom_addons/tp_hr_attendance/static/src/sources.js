import { Component, onWillStart, onWillUnmount, proxy, useProps } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { downloadBase64, rpcError } from "./common";
import { useAttendanceLive } from "./live";

/**
 * "Nguồn dữ liệu chấm công" (HR/admin area, ENTI-LIVE-001, ENTI-ATTENDANCE-002). ENTI is the only live source:
 * connector health, last successful sync, mapping progress with the unmapped people and their reasons, and a
 * manual sync. Excel file import is closed; earlier import batches stay readable as history.
 */
export class AttendanceSources extends Component {
    static template = "tp_hr_attendance.Sources";
    props = useProps();

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = proxy({
            loading: true, refreshing: false, syncing: false, error: "", notice: "", data: null,
            exporting: false, exportError: "", mode: "month", date: "", from: "", to: "", department: "",
        });
        this.request = 0;
        // Sync health and the last update time follow the server sync without F5 (bus + visible-tab fallback poll).
        this.live = useAttendanceLive({
            refresh: () => {
                if (this.state.loading || this.state.refreshing || this.state.syncing) {
                    return false;
                }
                return this.load({ silent: true });
            },
        });
        onWillStart(() => this.load());
        onWillUnmount(() => { this.request++; });
    }

    get data() {
        return this.state.data;
    }
    get enti() {
        return this.data?.api?.enti || {};
    }
    get unmapped() {
        return (this.enti.unmapped_people || []).slice(0, 5);
    }
    get health() {
        const source = this.enti;
        if (!source.configured) {
            return { tone: "neutral", text: "Chưa cấu hình" };
        }
        if (this.data?.health === "error") {
            return { tone: "danger", text: "Cần kiểm tra đồng bộ" };
        }
        if (this.data?.health === "stale") {
            return { tone: "warn", text: source.last_success_at ? "Đồng bộ đang chậm" : "Chờ đồng bộ thành công" };
        }
        if (!source.live || source.state === "paused") {
            return { tone: "neutral", text: "Đồng bộ tự động đang tắt" };
        }
        return source.last_success_at
            ? { tone: "good", text: "Đồng bộ tự động đang bật" }
            : { tone: "warn", text: "Chờ đồng bộ thành công" };
    }

    async load({ silent = false } = {}) {
        const request = ++this.request;
        this.state[silent ? "refreshing" : "loading"] = true;
        try {
            const orm = silent ? this.orm.silent : this.orm;
            const data = await orm.call("tp.hr.attendance.source", "tp_sources_overview", [{}]);
            if (request === this.request) {
                if (!this.state.data && data.today) {
                    Object.assign(this.state, { date: data.today, from: data.today, to: data.today });
                }
                this.state.data = data;
                if (!silent) {
                    this.state.error = "";
                }
                this.live.loaded();
            }
        } catch (error) {
            if (request === this.request && !silent) {
                this.state.error = rpcError(error, "Không tải được nguồn dữ liệu chấm công. Vui lòng thử lại.");
            }
        } finally {
            if (request === this.request) {
                this.state.loading = false;
                this.state.refreshing = false;
                this.live.flush();
            }
        }
    }

    /** Manual sync (HR/admin). The result stays on the screen; a failure never removes stored attendance. */
    async syncEntiNow() {
        if (this.state.syncing) {
            return;
        }
        Object.assign(this.state, { syncing: true, error: "", notice: "" });
        try {
            const res = await this.orm.call("tp.hr.attendance.source", "action_sync_enti_quick", []);
            if (res && res.success === false) {
                this.state.error = res.skipped
                    ? res.message
                    : "Đồng bộ chưa thành công. Xem Nhật ký đồng bộ để kiểm tra.";
            } else {
                this.state.notice = `Đã đồng bộ ${res?.employees || 0} nhân viên, cập nhật ${res?.days_applied || 0} bản ghi công.`;
            }
        } catch (error) {
            this.state.error = rpcError(error, "Đồng bộ thất bại. Vui lòng thử lại.");
        } finally {
            this.state.syncing = false;
        }
        await this.load({ silent: true });
    }

    async exportSheet() {
        const state = this.state;
        if (!this.data?.can_export || state.exporting) {
            return;
        }
        const { mode, date, from, to } = state;
        if (mode === "range" ? (!from || !to || from > to) : !date) {
            state.exportError = "Chọn kỳ xuất hợp lệ.";
            return;
        }
        Object.assign(state, { exporting: true, exportError: "" });
        try {
            const file = await this.orm.call("tp.hr.attendance.day", "tp_export_sheet", [{
                mode, date, from, to, department_id: Number(state.department) || 0,
            }]);
            downloadBase64(file);
        } catch (error) {
            state.exportError = rpcError(error, "Không xuất được bảng công. Vui lòng thử lại.");
        } finally {
            state.exporting = false;
        }
    }
    open(xmlid, filters = {}) {
        if (xmlid === "tp_hr_attendance.action_enti_mapping" && Object.keys(filters).length) {
            filters = { search_default_state_suggested: 0, search_default_state_unmapped: 0, ...filters };
        }
        return this.action.doAction(xmlid, { additionalContext: filters });
    }
}

registry.category("actions").add("tp_hr_attendance.sources", AttendanceSources);
