import { Component, onWillStart, proxy, useProps } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { HrListController } from "@tp_hr_workspace/table/table";
import { TpHrMyProfile } from "@tp_hr_workspace/my_profile/my_profile";
import { downloadBase64, readStore, rpcError, stepPeriod, writeStore } from "./common";
import { PersonDetail, SourceStrip } from "./parts";

/**
 * "Công của tôi" (HR-ATTENDANCE-SIMPLE-002). The employee always comes from the session user (tp_mine ignores
 * any client id): header, two machine late metrics for the exact source period, then Thứ/ngày · Giờ vào · Giờ ra.
 */
const STORE_KEY = "tp_hr_attendance.mine";
const MODES = [["week", "Tuần"], ["month", "Tháng"]];

export class MyAttendance extends Component {
    static template = "tp_hr_attendance.Mine";
    static components = { PersonDetail, SourceStrip };
    props = useProps();

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        const saved = readStore(STORE_KEY);
        this.state = proxy({ mode: MODES.some(([key]) => key === saved.mode) ? saved.mode : "month", date: "", from: "", to: "",
            fileMenu: false, loading: true, error: "", data: null });
        this.modes = MODES;
        this.request = 0;
        onWillStart(() => this.load());
    }

    get data() {
        return this.state.data;
    }

    async load() {
        const request = ++this.request;
        this.state.loading = true;
        this.state.error = "";
        try {
            const data = await this.orm.call("tp.hr.attendance.day", "tp_mine", [{
                mode: this.state.mode, date: this.state.date, from: this.state.from, to: this.state.to,
            }]);
            if (request !== this.request) {
                return;
            }
            this.state.data = data;
            if (data.has_employee) {
                Object.assign(this.state, { date: data.date, from: data.start, to: data.end });
                writeStore(STORE_KEY, { mode: data.mode === "range" ? "month" : data.mode });
            }
        } catch (error) {
            if (request === this.request) {
                this.state.error = rpcError(error, "Không tải được công cá nhân. Vui lòng thử lại.");
            }
        } finally {
            if (request === this.request) {
                this.state.loading = false;
            }
        }
    }
    reset(changes) {
        Object.assign(this.state, { fileMenu: false }, changes);
        return this.load();
    }
    setMode(mode) {
        return this.reset({ mode, date: this.state.from || this.state.date });
    }
    step(delta) {
        return this.reset(stepPeriod(this.state.mode, this.data, delta));
    }
    goToday() {
        return this.reset({ mode: this.state.mode === "range" ? "month" : this.state.mode, date: this.data?.today || "" });
    }
    onDate(ev) {
        if (ev.target.value) {
            return this.reset({ date: ev.target.value });
        }
    }
    onMonth(ev) {
        if (ev.target.value) {
            return this.reset({ date: `${ev.target.value}-01` });
        }
    }
    openFilePeriod(item) {
        return this.reset({ mode: "range", from: item.from, to: item.to });
    }
    async exportOwn() {
        try {
            downloadBase64(await this.orm.call("tp.hr.attendance.day", "tp_export_mine", [{
                mode: this.state.mode, date: this.state.date, from: this.state.from, to: this.state.to,
            }]));
        } catch (error) {
            this.state.error = rpcError(error, "Không xuất được công cá nhân. Vui lòng thử lại.");
        }
    }
    async openRequest() {
        await this.action.doAction({
            type: "ir.actions.act_window", name: "Đề nghị điều chỉnh công", res_model: "tp.hr.attendance.correction",
            views: [[false, "form"]], target: "new",
        }, { onClose: () => this.load() });
    }
    openRequests() {
        return this.action.doAction("tp_hr_attendance.action_my_requests");
    }
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
