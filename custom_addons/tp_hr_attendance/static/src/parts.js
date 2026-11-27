import { Component, onWillStart, proxy, useProps } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";
import { InlineErrors } from "@tp_web_home/validation/inline_errors";
import { saveError } from "@tp_web_home/validation/validation";
import { PAGE_SIZES, cellNote, formatDate, lateText, pagerText } from "./common";

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
        const source = this.props.source;
        if (source.connected && source.cron_active === false) {
            return "stale";
        }
        return source.auto ? source.health : "off";
    }
    get label() {
        const source = this.props.source;
        if (source.connected && source.cron_active === false) {
            return "Đồng bộ tự động: Đang tạm tắt";
        }
        if (source.auto && source.health === "stale" && !source.updated_at) {
            return "Đồng bộ tự động: Chờ đồng bộ lần đầu";
        }
        return source.auto && HEALTH[source.health] ? HEALTH[source.health][0] : source.label;
    }
    get icon() {
        const source = this.props.source;
        if (source.connected && source.cron_active === false) {
            return "pause_circle";
        }
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
    static components = { Dialog, InlineErrors, PersonDetail };
    props = useProps();
    setup() {
        this.orm = useService("orm");
        this.state = proxy({ data: null, serverError: null, attempt: 0 });
        onWillStart(() => this.load());
    }
    async load() {
        try {
            this.state.data = await this.orm.call("tp.hr.attendance.day", "tp_person", [this.props.params]);
            this.state.serverError = null;
        } catch (error) {
            this.state.serverError = saveError(error, { verb: "tải giờ theo ngày" });
            this.state.attempt++;
        }
    }
}

/** Machine late totals of a source period, opened from a day view without changing the day filter. */
export class LateDialog extends Component {
    static template = "tp_hr_attendance.LateDialog";
    static components = { Dialog, InlineErrors, PeriodTable, AttPager };
    props = useProps();
    setup() {
        this.orm = useService("orm");
        this.dialog = useService("dialog");
        this.state = proxy({ data: null, serverError: null, attempt: 0, page: 1, pageSize: 100 });
        onWillStart(() => this.load());
    }
    async load() {
        try {
            this.state.data = await this.orm.call("tp.hr.attendance.day", "tp_sheet", [{
                ...this.props.params, mode: "range", page: this.state.page, page_size: this.state.pageSize,
            }]);
            this.state.serverError = null;
        } catch (error) {
            this.state.serverError = saveError(error, { verb: "tải tổng đi muộn" });
            this.state.attempt++;
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
