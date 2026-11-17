import { Component, onWillStart, proxy, useProps, usePlugin } from "@odoo/owl";
import { UIPlugin } from "@web/core/ui/ui_plugin";
import { registry } from "@web/core/registry";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { HrListController } from "@tp_hr_workspace/table/table";
import { TpHrMyProfile } from "@tp_hr_workspace/my_profile/my_profile";
import { formatDate, formatHours, readStore, shiftMonth, writeStore } from "./board/board";

export class MyAttendance extends Component {
    static template = "tp_hr_attendance.Mine";
    props = useProps();

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.ui = usePlugin(UIPlugin);
        this.state = proxy({ month: readStore("tp_att_mine").month || "", data: null, loading: true, error: "", filter: "", lock: "", selected: "", page: 1, size: 20, view: this.ui.size() <= 1 ? "days" : "calendar" });
        this.formatDate = formatDate;
        this.formatHours = formatHours;
        this.request = 0;
        onWillStart(() => this.load());
    }
    get data() { return this.state.data; }
    get filteredRows() { return this.data.rows.filter((row) => (!this.state.filter || row.state === this.state.filter) && (!this.state.lock || row.lock === this.state.lock)); }
    get pages() { return Math.max(1, Math.ceil(this.filteredRows.length / this.state.size)); }
    get rows() { return this.filteredRows.slice((this.state.page - 1) * this.state.size, this.state.page * this.state.size); }
    get selected() { return this.data?.rows.find((row) => row.date === this.state.selected); }
    get blanks() { return Array.from({ length: this.data.lead }, (_, index) => index); }
    async load() {
        const request = ++this.request;
        this.state.loading = true;
        this.state.error = "";
        try {
            const data = await this.orm.call("tp.hr.attendance.day", "tp_my_attendance", [{ month: this.state.month }]);
            if (request !== this.request) return;
            this.state.data = data;
            if (data.has_employee) {
                this.state.month = data.month;
                this.state.selected = data.rows.find((row) => row.date === this.state.selected)?.date || data.anchor;
                writeStore("tp_att_mine", { month: data.month });
            }
        } catch (error) {
            if (/SessionExpired/.test(error.data?.name || error.name || "")) throw error;
            this.state.error = error.data?.message || "Không tải được công cá nhân. Vui lòng thử lại.";
        } finally { if (request === this.request) this.state.loading = false; }
    }
    step(delta) { this.state.month = shiftMonth(this.state.month, delta); return this.load(); }
    onMonth(ev) { if (ev.target.value) { this.state.month = ev.target.value; return this.load(); } }
    async openRequest(row) {
        await this.action.doAction({ type: "ir.actions.act_window", name: "Đề nghị điều chỉnh công", res_model: "tp.hr.attendance.correction",
            views: [[false, "form"]], target: "new", context: { default_work_date: row.date } }, { onClose: () => this.load() });
    }
    openRequests() { return this.action.doAction("tp_hr_attendance.action_my_requests"); }
    openExisting(id) { return this.action.doAction({ type: "ir.actions.act_window", res_model: "tp.hr.attendance.correction", res_id: id, views: [[false, "form"]] }); }
}
registry.category("actions").add("tp_hr_attendance.mine", MyAttendance);

const CONTENT = {
    "tp.hr.attendance.correction": ["Đề nghị điều chỉnh công", "Phiếu riêng theo người đề nghị và phạm vi được phân công xử lý.", "Tạo đề nghị", "Chưa có đề nghị"],
    "tp.hr.attendance.period": ["Chốt kỳ công", "Rà soát các ngày và đề nghị trước khi chốt. Quyền chốt cần phân công riêng.", "Tạo kỳ công", "Chưa có kỳ công"],
    "tp.hr.attendance.batch": ["Nhập dữ liệu công", "Xem trước và đối chiếu nguồn trước khi ghi nhận giờ công.", "Tạo lô nhập", "Chưa có lô nhập"],
    "tp.hr.attendance.log": ["Nhật ký chấm công", "Lịch sử thao tác và phiên bản, không chứa giải trình hoặc minh chứng cá nhân.", "", "Chưa có nhật ký"],
};
patch(HrListController.prototype, {
    get hrContent() { return CONTENT[this.props.resModel] || super.hrContent; },
});

patch(TpHrMyProfile, { components: { ...TpHrMyProfile.components, MyAttendance } });
patch(TpHrMyProfile.prototype, {
    setup() {
        super.setup(...arguments);
        this.tabs = [...this.tabs, { id: "attendance", label: "Công của tôi", icon: "calendar_month" }];
    },
});
