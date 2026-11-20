import { Component, onWillStart, proxy, useProps } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";
import { PAGE_SIZES, cellNote, formatDate, lateText, pagerText, rpcError } from "./common";

const HEALTH = {
    ok: ["Đồng bộ tự động: Hoạt động", "autorenew"],
    stale: ["Đồng bộ tự động: Đang chậm", "schedule"],
    error: ["Đồng bộ tự động: Mất kết nối", "error"],
};

/**
 * Small source strip: automatic ENTI sync health, the real time Odoo last received ENTI data, data-to date.
 * The update time is when Odoo received the data from ENTI — not when the person punched on the machine.
 */
export class SourceStrip extends Component {
    static template = "tp_hr_attendance.SourceStrip";
    props = useProps();
    get tone() {
        return this.props.source.auto ? this.props.source.health : "off";
    }
    get label() {
        const source = this.props.source;
        return source.auto && HEALTH[source.health] ? HEALTH[source.health][0] : source.label;
    }
    get icon() {
        const source = this.props.source;
        if (source.auto && HEALTH[source.health]) {
            return HEALTH[source.health][1];
        }
        return source.kind === "none" ? "cloud_off" : "description";
    }
    get title() {
        const source = this.props.source;
        if (!source.auto) {
            return "";
        }
        const poll = source.poll_seconds ? `Máy chủ đồng bộ dữ liệu khoảng ${source.poll_seconds} giây/lần trong giờ làm việc. ` : "";
        return `${poll}Thời điểm cập nhật là lúc hệ thống nhận dữ liệu thành công.`;
    }
}

export class AttPager extends Component {
    static template = "tp_hr_attendance.Pager";
    props = useProps();
    /** Page sizes offered: ``props.sizes`` when a screen allows fewer (the group dialog: 10/20/50). */
    get sizes() {
        return this.props.sizes || PAGE_SIZES;
    }
    get text() {
        return pagerText(this.props.data, this.props.unit || "dòng");
    }
    onSize(value) {
        return this.props.onSize(Number(value));
    }
}

/** Period rows: one line per person with the machine late total for exactly the viewed period. */
export class PeriodTable extends Component {
    static template = "tp_hr_attendance.PeriodTable";
    props = useProps();
    setup() {
        this.lateText = lateText;
    }
}

/** Header, two late metrics for the exact source period, then only Thứ/ngày · Giờ vào · Giờ ra. */
export class PersonDetail extends Component {
    static template = "tp_hr_attendance.PersonDetail";
    props = useProps();
    setup() {
        this.cellNote = cellNote;
        this.formatDate = formatDate;
    }
    get late() {
        return this.props.data.late;
    }
    get lateNote() {
        const late = this.late;
        return late.state === "exact" ? late.note || `Theo Excel máy · kỳ ${late.source}` : late.text;
    }
}

export class PersonDialog extends Component {
    static template = "tp_hr_attendance.PersonDialog";
    static components = { Dialog, PersonDetail };
    props = useProps();
    setup() {
        this.orm = useService("orm");
        this.state = proxy({ data: null, error: "" });
        onWillStart(() => this.load());
    }
    async load() {
        try {
            this.state.data = await this.orm.call("tp.hr.attendance.day", "tp_person", [this.props.params]);
        } catch (error) {
            this.state.error = rpcError(error, "Không tải được giờ theo ngày của nhân viên này.");
        }
    }
}

/** Machine late totals of a source period, opened from a day view without changing the day filter. */
export class LateDialog extends Component {
    static template = "tp_hr_attendance.LateDialog";
    static components = { Dialog, PeriodTable, AttPager };
    props = useProps();
    setup() {
        this.orm = useService("orm");
        this.dialog = useService("dialog");
        this.state = proxy({ data: null, error: "", page: 1, pageSize: 20 });
        onWillStart(() => this.load());
    }
    async load() {
        try {
            this.state.data = await this.orm.call("tp.hr.attendance.day", "tp_sheet", [{
                ...this.props.params, mode: "range", page: this.state.page, page_size: this.state.pageSize,
            }]);
        } catch (error) {
            this.state.error = rpcError(error, "Không tải được tổng đi muộn của kỳ này.");
        }
    }
    setPage(page) {
        this.state.page = page;
        return this.load();
    }
    setSize(size) {
        Object.assign(this.state, { pageSize: size, page: 1 });
        return this.load();
    }
    openPerson(row) {
        this.dialog.add(PersonDialog, { params: { employee_id: row.id, mode: "range", from: this.state.data.start, to: this.state.data.end } });
    }
}
