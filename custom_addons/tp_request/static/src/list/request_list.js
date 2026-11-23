/** @odoo-module **/
import { Component, onMounted, onWillStart, proxy, signal, useProps } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useBus, useService } from "@web/core/utils/hooks";
import { TpRequestCreateModal } from "../create/create_modal";
import {
    APPROVAL_BADGE,
    EXEC_BADGE,
    PRIORITY_BADGE,
    extractErrorMessage,
    openRequestDetail,
    readListState,
    writeListState,
} from "../prefs";

const MODE_META = {
    mine: {
        title: "Đề nghị của tôi",
        subtitle: "Theo dõi các bản nháp, hồ sơ đang chờ duyệt, bị trả lại và kết quả thực hiện của bạn.",
        tabs: [
            { key: "all", label: "Tất cả" },
            { key: "draft", label: "Nháp" },
            { key: "pending", label: "Chờ duyệt" },
            { key: "returned", label: "Trả lại bổ sung" },
            { key: "approved", label: "Đã duyệt" },
            { key: "rejected", label: "Từ chối" },
            { key: "withdrawn", label: "Đã rút" },
        ],
    },
    to_approve: {
        title: "Cần tôi duyệt",
        subtitle: "Hàng đợi hồ sơ đang đến lượt bạn phê duyệt; hỗ trợ lọc nhanh và kiểm soát quá hạn.",
        tabs: [
            { key: "all", label: "Đến lượt tôi duyệt" },
            { key: "overdue", label: "Quá hạn" },
        ],
    },
    to_execute: {
        title: "Cần thực hiện",
        subtitle: "Các đề nghị đã được phê duyệt hoàn tất và giao cho bạn/bộ phận bạn triển khai.",
        tabs: [
            { key: "all", label: "Tất cả cần làm" },
            { key: "exec_pending", label: "Chờ nhận việc" },
            { key: "exec_in_progress", label: "Đang thực hiện" },
            { key: "overdue", label: "Quá hạn" },
        ],
    },
    watching: {
        title: "Theo dõi",
        subtitle: "Hồ sơ bạn theo dõi hoặc đã từng tham gia phê duyệt / thực hiện.",
        tabs: [
            { key: "all", label: "Tất cả" },
            { key: "pending", label: "Chờ duyệt" },
            { key: "returned", label: "Trả lại" },
            { key: "approved", label: "Đã duyệt" },
            { key: "rejected", label: "Từ chối" },
            { key: "overdue", label: "Quá hạn" },
        ],
    },
    admin_all: {
        title: "Toàn bộ hồ sơ công ty",
        subtitle: "Theo dõi tập trung toàn bộ đề nghị đã gửi trong phạm vi công ty được phép.",
        tabs: [
            { key: "all", label: "Tất cả" },
            { key: "pending", label: "Chờ duyệt" },
            { key: "returned", label: "Trả lại" },
            { key: "approved", label: "Đã duyệt" },
            { key: "rejected", label: "Từ chối" },
            { key: "overdue", label: "Quá hạn" },
        ],
    },
};

export class TpRequestList extends Component {
    static template = "tp_request.List";
    static components = { TpRequestCreateModal };
    props = useProps();

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.APPROVAL_BADGE = APPROVAL_BADGE;
        this.EXEC_BADGE = EXEC_BADGE;
        this.PRIORITY_BADGE = PRIORITY_BADGE;
        this.scrollRef = signal.ref();

        const mode = this.props.mode || this.props.action?.params?.mode || "mine";
        const saved = readListState(mode) || {};

        this.state = proxy({
            mode,
            loading: true,
            error: "",
            data: null,
            showCreate: false,
            tab: saved.tab || "all",
            // Draft vs Applied filters (TP_TABLE_FILTER_STANDARD DEC-044)
            draft: {
                search: saved.search || "",
                type_id: saved.type_id || "",
                department_id: saved.department_id || "",
                requester_user_id: saved.requester_user_id || "",
                priority: saved.priority || "",
                date_from: saved.date_from || "",
                date_to: saved.date_to || "",
                overdue_only: Boolean(saved.overdue_only),
            },
            applied: {
                search: saved.search || "",
                type_id: saved.type_id || "",
                department_id: saved.department_id || "",
                requester_user_id: saved.requester_user_id || "",
                priority: saved.priority || "",
                date_from: saved.date_from || "",
                date_to: saved.date_to || "",
                overdue_only: Boolean(saved.overdue_only),
            },
            page: saved.page || 1,
            pageSize: saved.page_size || 100,
            savedScrollTop: saved.scrollTop || 0,
        });

        this.reqSeq = 0;
        useBus(this.env.bus, "TP_REQUEST:LIVE_UPDATED", () => this.load(true));
        onWillStart(() => this.load());
        onMounted(() => {
            if (this.state.savedScrollTop && this.scrollRef()) {
                this.scrollRef().scrollTop = this.state.savedScrollTop;
            }
        });
    }

    get meta() {
        return MODE_META[this.state.mode] || MODE_META.mine;
    }

    get isEmbedded() {
        return Boolean(this.props.embedded);
    }

    persistState() {
        writeListState(this.state.mode, {
            tab: this.state.tab,
            ...this.state.applied,
            page: this.state.page,
            page_size: this.state.pageSize,
            scrollTop: this.scrollRef()?.scrollTop || 0,
        });
    }

    buildQueryParams() {
        return {
            tab: this.state.tab,
            search: this.state.applied.search,
            type_id: this.state.applied.type_id || false,
            department_id: this.state.applied.department_id || false,
            requester_user_id: this.state.applied.requester_user_id || false,
            priority: this.state.applied.priority || "",
            date_from: this.state.applied.date_from || "",
            date_to: this.state.applied.date_to || "",
            overdue_only: this.state.applied.overdue_only,
            page: this.state.page,
            page_size: this.state.pageSize,
        };
    }

    async load(silent = false) {
        const seq = ++this.reqSeq;
        if (!silent) {
            this.state.loading = true;
            this.state.error = "";
        }
        try {
            const data = await (silent ? this.orm.silent : this.orm).call("tp.request", "tp_list_data", [
                this.state.mode,
                this.buildQueryParams(),
            ]);
            if (seq !== this.reqSeq) return;
            this.state.data = data;
            this.state.page = data.page || 1;
            this.state.error = "";
            this.persistState();
        } catch (err) {
            if (seq === this.reqSeq && !silent) {
                this.state.error = extractErrorMessage(err, "Không tải được danh sách đề nghị.");
            }
        } finally {
            if (seq === this.reqSeq) {
                this.state.loading = false;
            }
        }
    }

    selectTab(tabKey) {
        this.state.tab = tabKey;
        this.state.page = 1;
        this.load();
    }

    onDraftInput(key, ev) {
        this.state.draft[key] = key === "overdue_only" ? ev.target.checked : ev.target.value;
    }

    onSearchKeydown(ev) {
        if (ev.key === "Enter") {
            ev.preventDefault();
            this.applyFilters();
        }
    }

    applyFilters() {
        if (this.state.draft.date_from && this.state.draft.date_to && this.state.draft.date_from > this.state.draft.date_to) {
            this.state.error = "Ngày bắt đầu không được lớn hơn ngày kết thúc.";
            return;
        }
        Object.assign(this.state.applied, { ...this.state.draft });
        this.state.page = 1;
        this.load();
    }

    clearFilters() {
        const blank = {
            search: "",
            type_id: "",
            department_id: "",
            requester_user_id: "",
            priority: "",
            date_from: "",
            date_to: "",
            overdue_only: false,
        };
        Object.assign(this.state.draft, blank);
        Object.assign(this.state.applied, blank);
        this.state.tab = "all";
        this.state.page = 1;
        this.load();
    }

    removeChip(key) {
        const emptyVal = key === "overdue_only" ? false : "";
        this.state.draft[key] = emptyVal;
        this.state.applied[key] = emptyVal;
        this.state.page = 1;
        this.load();
    }

    get appliedChips() {
        const chips = [];
        const opts = this.state.data?.options || {};
        if (this.state.applied.search) {
            chips.push({ key: "search", label: `Từ khóa: "${this.state.applied.search}"` });
        }
        if (this.state.applied.type_id) {
            const found = (opts.types || []).find((t) => String(t.id) === String(this.state.applied.type_id));
            chips.push({ key: "type_id", label: `Loại: ${found?.name || this.state.applied.type_id}` });
        }
        if (this.state.applied.department_id) {
            const found = (opts.departments || []).find((d) => String(d.id) === String(this.state.applied.department_id));
            chips.push({ key: "department_id", label: `Phòng: ${found?.name || this.state.applied.department_id}` });
        }
        if (this.state.applied.requester_user_id) {
            const found = (opts.requesters || []).find((u) => String(u.id) === String(this.state.applied.requester_user_id));
            chips.push({ key: "requester_user_id", label: `Người gửi: ${found?.name || this.state.applied.requester_user_id}` });
        }
        if (this.state.applied.priority) {
            chips.push({ key: "priority", label: `Ưu tiên: ${PRIORITY_BADGE[this.state.applied.priority]?.label || this.state.applied.priority}` });
        }
        if (this.state.applied.date_from) {
            chips.push({ key: "date_from", label: `Từ: ${this.state.applied.date_from}` });
        }
        if (this.state.applied.date_to) {
            chips.push({ key: "date_to", label: `Đến: ${this.state.applied.date_to}` });
        }
        if (this.state.applied.overdue_only) {
            chips.push({ key: "overdue_only", label: "Chỉ hồ sơ quá hạn" });
        }
        return chips;
    }

    setPage(p) {
        const max = this.state.data?.max_page || 1;
        const target = Math.min(Math.max(1, p), max);
        if (target !== this.state.page) {
            this.state.page = target;
            this.load();
        }
    }

    onPageSizeChange(ev) {
        this.state.pageSize = Number(ev.target.value) || 100;
        this.state.page = 1;
        this.load();
    }

    exportExcel() {
        const q = encodeURIComponent(JSON.stringify(this.buildQueryParams()));
        window.open(`/tp_request/export.xlsx?mode=${encodeURIComponent(this.state.mode)}&params=${q}`, "_blank");
    }

    openDetail(row) {
        this.persistState();
        openRequestDetail(this.action, row.id, this.state.mode);
    }

    onCreated(res) {
        this.state.showCreate = false;
        if (res?.id) {
            this.persistState();
            openRequestDetail(this.action, res.id, this.state.mode);
        } else {
            this.load();
        }
    }
}

registry.category("actions").add("tp_request.list", TpRequestList);
