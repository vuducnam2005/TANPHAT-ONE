import { Component, onWillStart, proxy, useProps } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { rpcError } from "./common";
import { openAttendanceUpload } from "./upload/upload";

/**
 * "Nguồn dữ liệu chấm công" (HR/admin area, HR-ATTENDANCE-SIMPLE-002). Says plainly which source feeds the
 * screens today (Excel máy chấm công), that the device API is not configured and live sync is off, lists what
 * the vendor must provide before any adapter is built, and keeps a compact import history.
 */
export class AttendanceSources extends Component {
    static template = "tp_hr_attendance.Sources";
    props = useProps();

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = proxy({ loading: true, error: "", data: null });
        onWillStart(() => this.load());
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
