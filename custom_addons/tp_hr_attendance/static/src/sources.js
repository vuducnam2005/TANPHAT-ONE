import { Component, onWillStart, proxy, useProps } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { rpcError } from "./common";
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
        this.state = proxy({ loading: true, syncing: false, error: "", notice: "", data: null });
        this.request = 0;
        // Sync health and the last update time follow the server sync without F5 (bus + visible-tab fallback poll).
        this.live = useAttendanceLive({ refresh: () => (this.state.loading ? false : this.load({ silent: true })) });
        onWillStart(() => this.load());
    }

    get data() {
        return this.state.data;
    }
    get enti() {
        return this.data?.api?.enti || {};
    }
    get unmapped() {
        return this.enti.unmapped_people || [];
    }
    get referenceHours() {
        return (this.data?.reference_hours || "08:30-17:00").replace("-", "–");
    }

    async load({ silent = false } = {}) {
        const request = ++this.request;
        this.state.loading = true;
        try {
            const orm = silent ? this.orm.silent : this.orm;
            const data = await orm.call("tp.hr.attendance.source", "tp_sources_overview", [{}]);
            if (request === this.request) {
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
                    : `Đồng bộ ENTI chưa thành công: ${res.message || "lỗi không rõ"}. Dữ liệu công đã có được giữ nguyên.`;
            } else {
                const unmapped = res?.unmapped ? `, ${res.unmapped} người ENTI chưa ghép` : "";
                this.state.notice = `Đồng bộ ENTI xong: ${res?.employees || 0} nhân viên${unmapped}, ${res?.days_applied || 0} ngày công cập nhật.`;
            }
        } catch (error) {
            this.state.error = rpcError(error, "Đồng bộ ENTI thất bại. Dữ liệu công đã có được giữ nguyên; vui lòng thử lại.");
        } finally {
            this.state.syncing = false;
        }
        await this.load({ silent: true });
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
