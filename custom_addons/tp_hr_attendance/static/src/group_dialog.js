import { Component, onWillStart, onWillUnmount, proxy, useProps } from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";
import { InlineErrors } from "@tp_web_home/validation/inline_errors";
import { saveError } from "@tp_web_home/validation/validation";
import { GROUP_ORDER, formatDate } from "./common";
import { AttPager } from "./parts";

const SIZES = [10, 20, 50, 100];
const HIGHLIGHT_MS = 2400;
const NOTE_LABELS = { working: "Trạng thái", done: "Ghi chú", unknown: "Lý do" };

export class GroupDialog extends Component {
    static template = "tp_hr_attendance.GroupDialog";
    static components = { Dialog, InlineErrors, AttPager };
    props = useProps();

    setup() {
        this.orm = useService("orm");
        this.sizes = SIZES;
        this.formatDate = formatDate;
        this.state = proxy({
            group: this.props.group, q: "", dept: 0, page: 1, pageSize: 100,
            data: null, loading: true, serverError: null, attempt: 0, fresh: {},
        });
        this.request = 0;
        this.timers = { search: null, highlight: null };
        const unregister = this.props.register?.(this);
        onWillStart(() => this.load());
        onWillUnmount(() => {
            unregister?.();
            browser.clearTimeout(this.timers.search);
            browser.clearTimeout(this.timers.highlight);
            this.request++;
        });
    }

    // ----------------------------------------------------------------- view data
    get data() {
        return this.state.data;
    }
    get labels() {
        return this.props.labels || {};
    }
    get groupLabel() {
        return this.labels[this.state.group] || "";
    }
    get title() {
        const data = this.data;
        const day = data ? formatDate(data.class_date) : formatDate(this.props.date);
        const total = data ? data.group_total : this.props.count;
        return `${this.groupLabel} — ${day} — ${total ?? "…"} nhân viên`;
    }
    /** Group switch: the three main groups, plus "Chưa xác định" whenever it has people or is open. */
    get tabs() {
        const counts = this.data?.counts || this.props.counts || {};
        return GROUP_ORDER.filter((key) => key !== "unknown" || counts.unknown || this.state.group === "unknown")
            .map((key) => ({ key, label: this.labels[key], count: counts[key] ?? 0 }));
    }
    get noteLabel() {
        return NOTE_LABELS[this.state.group] || "";
    }
    get filtered() {
        return Boolean(this.state.q || this.state.dept);
    }
    get colspan() {
        return { working: 7, done: 8, not_started: 4, unknown: 5 }[this.state.group] || 4;
    }
    isFresh(row) {
        return Boolean(this.state.fresh[row.employee_id]);
    }

    // ------------------------------------------------------------------ loading
    params() {
        const state = this.state;
        return {
            ...this.props.scope(), group: state.group, q: state.q, dept: Number(state.dept) || 0,
            page: state.page, page_size: state.pageSize,
        };
    }

    /** ``silent``: automatic refresh after a dashboard update — keep everything on screen as it is. */
    async load({ silent = false } = {}) {
        const request = ++this.request;
        if (!silent) {
            Object.assign(this.state, { loading: true, serverError: null });
        }
        try {
            const orm = silent ? this.orm.silent : this.orm;
            const data = await orm.call("tp.hr.attendance.day", "tp_overview_group", [this.params()]);
            if (request !== this.request) {
                return;
            }
            const before = this.state.data;
            if (silent && before && before.group === data.group) {
                this.highlight(before, data);
            }
            Object.assign(this.state, { data, page: data.page, pageSize: data.page_size, dept: data.dept, serverError: null });
        } catch (error) {
            if (request === this.request && !silent) {
                this.state.serverError = saveError(error, { verb: "tải danh sách nhân viên" });
                this.state.attempt++;
            }
        } finally {
            if (request === this.request) {
                this.state.loading = false;
            }
        }
    }
    refresh() {
        if (!this.state.loading) {
            this.load({ silent: true });
        }
    }
    highlight(before, after) {
        const known = new Map(before.rows.map((row) => [row.employee_id, `${row.in}|${row.out}`]));
        const fresh = {};
        for (const row of after.rows) {
            if (known.get(row.employee_id) !== `${row.in}|${row.out}`) {
                fresh[row.employee_id] = true;
            }
        }
        if (!Object.keys(fresh).length) {
            return;
        }
        this.state.fresh = fresh;
        browser.clearTimeout(this.timers.highlight);
        this.timers.highlight = browser.setTimeout(() => {
            this.state.fresh = {};
        }, HIGHLIGHT_MS);
    }

    // ------------------------------------------------------------------ filters
    reset(changes) {
        Object.assign(this.state, { page: 1, fresh: {} }, changes);
        return this.load();
    }
    setGroup(group) {
        if (group !== this.state.group) {
            browser.clearTimeout(this.timers.search);
            return this.reset({ group, q: "", dept: 0 });
        }
    }
    onSearch(ev) {
        const value = ev.target.value;
        browser.clearTimeout(this.timers.search);
        this.timers.search = browser.setTimeout(() => this.reset({ q: value.trim() }), 300);
    }
    onDept(ev) {
        return this.reset({ dept: Number(ev.target.value) || 0 });
    }
    clearFilters() {
        browser.clearTimeout(this.timers.search);
        return this.reset({ q: "", dept: 0 });
    }
    setPage(page) {
        this.state.page = page;
        return this.load();
    }
    setSize(size) {
        return this.reset({ pageSize: size });
    }
}
