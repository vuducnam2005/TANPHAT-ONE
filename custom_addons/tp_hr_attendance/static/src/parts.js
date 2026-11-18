import { Component, onWillStart, proxy, useProps } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";
import { PAGE_SIZES, cellNote, formatDate, lateText, pagerText, rpcError } from "./common";

/** Small source strip: Excel / API / mixed, update time, data-to date, connection state (never "realtime"). */
export class SourceStrip extends Component {
    static template = "tp_hr_attendance.SourceStrip";
    props = useProps();
}

export class AttPager extends Component {
    static template = "tp_hr_attendance.Pager";
    props = useProps();
    setup() {
        this.sizes = PAGE_SIZES;
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
        return late.state === "exact" ? `Theo Excel máy · kỳ ${late.source}` : late.text;
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
