import { Component, onWillStart, proxy, useProps } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { downloadBase64, formatDate, rpcError } from "../common";
import { AttPager } from "../parts";

const SCOPE_SHORT = {
    out_of_scope: "Ngoài kỳ tệp",
    blank_in_period: "Ô trống",
    not_in_file: "Không có trong tệp",
    no_batch_b: "Chưa chọn B",
};

/**
 * A/B comparison of two stored Excel source files (HR-ATTENDANCE-MATRIX-003). ENTI-ATTENDANCE-002 closed Excel
 * import, so this screen only reads history (tp_compare_batches, tp_export_compare); the former apply/resolve
 * RPCs are closed on the server.
 */
export class AttendanceCompare extends Component {
    static template = "tp_hr_attendance.Compare";
    static components = { AttPager };
    props = useProps();

    setup() {
        this.orm = useService("orm");

        const list = this.props.batches || [];
        const initA = Number(this.props.initialA || list[0]?.id || 0);
        const other = list.find((b) => b.id !== initA);
        const initB = this.props.initialB !== undefined ? Number(this.props.initialB || 0) : (other ? other.id : 0);

        this.state = proxy({
            batchAId: initA,
            batchBId: initB,
            sheetAIndex: 0,
            sheetBIndex: initA && initA === initB ? 1 : 0,
            // Pending DEC-044 filter inputs
            draftOnlyDiff: false,
            draftGroup: "",
            draftSourceGroup: "",
            draftWorkDate: "",
            draftSearch: "",
            // Applied DEC-044 filters sent to server
            onlyDiff: false,
            group: "",
            sourceGroup: "",
            workDate: "",
            search: "",
            page: 1,
            pageSize: 20,
            mobileView: "cards",
            loading: true,
            error: "",
            data: null,
        });
        this.request = 0;

        onWillStart(async () => {
            await this.load();
        });
    }

    get data() {
        return this.state.data;
    }

    get batches() {
        return this.data?.batches || this.props.batches || [];
    }

    get batchAObj() {
        return this.batches.find((b) => b.id === this.state.batchAId) || this.data?.batch_a || null;
    }

    get batchBObj() {
        if (!this.state.batchBId) {
            return null;
        }
        return this.batches.find((b) => b.id === this.state.batchBId) || this.data?.batch_b || null;
    }

    get isSameTarget() {
        return Boolean(
            this.state.batchAId
            && this.state.batchBId
            && this.state.batchAId === this.state.batchBId
            && this.state.sheetAIndex === this.state.sheetBIndex
        );
    }

    get chips() {
        const list = [];
        if (this.state.onlyDiff) {
            list.push({ key: "onlyDiff", label: "Chỉ xem sai khác" });
        }
        if (this.state.group) {
            const grp = (this.data?.compare_groups || []).find((g) => g.key === this.state.group);
            list.push({ key: "group", label: `Nhóm: ${grp ? grp.label : this.state.group}` });
        }
        if (this.state.sourceGroup) {
            const ug = (this.data?.group_options || []).find((g) => g.key === this.state.sourceGroup);
            list.push({ key: "sourceGroup", label: `Đơn vị: ${ug ? ug.label : this.state.sourceGroup}` });
        }
        if (this.state.workDate) {
            list.push({ key: "workDate", label: `Ngày: ${formatDate(this.state.workDate)}` });
        }
        if (this.state.search) {
            list.push({ key: "search", label: `Tìm: ${this.state.search}` });
        }
        return list;
    }

    formatDate(iso) {
        return formatDate(iso);
    }

    scopeLabel(scope) {
        return SCOPE_SHORT[scope] || scope || "—";
    }

    params() {
        return {
            batch_a_id: this.state.batchAId,
            batch_b_id: this.state.batchBId,
            sheet_a_index: this.state.sheetAIndex,
            sheet_b_index: this.state.sheetBIndex,
            only_diff: this.state.onlyDiff,
            group: this.state.group,
            source_group: this.state.sourceGroup,
            work_date: this.state.workDate,
            search: this.state.search,
            page: this.state.page,
            page_size: this.state.pageSize,
        };
    }

    async load() {
        const req = ++this.request;
        this.state.loading = true;
        this.state.error = "";
        try {
            const res = await this.orm.call("tp.hr.attendance.batch", "tp_compare_batches", [this.params()]);
            if (req !== this.request) {
                return;
            }
            this.state.data = res;
            if (res.has_batches) {
                this.state.batchAId = res.batch_a?.id || this.state.batchAId;
                this.state.batchBId = res.batch_b?.id || 0;
                this.state.sheetAIndex = res.sheet_a?.index ?? this.state.sheetAIndex;
                this.state.sheetBIndex = res.sheet_b?.index ?? 0;
                this.state.page = res.page;
                this.state.pageSize = res.page_size;
            }
        } catch (error) {
            if (req === this.request) {
                this.state.error = rpcError(error, "Không tải được bảng đối chiếu A/B. Vui lòng thử lại.");
            }
        } finally {
            if (req === this.request) {
                this.state.loading = false;
            }
        }
    }

    onChangeBatchA(ev) {
        const id = Number(ev.target.value) || 0;
        if (!id || id === this.state.batchAId) {
            return;
        }
        Object.assign(this.state, {
            batchAId: id,
            sheetAIndex: 0,
            page: 1,
        });
        return this.load();
    }

    onChangeSheetA(ev) {
        Object.assign(this.state, { sheetAIndex: Number(ev.target.value) || 0, page: 1 });
        return this.load();
    }

    onChangeBatchB(ev) {
        const id = Number(ev.target.value) || 0;
        if (id === this.state.batchBId) {
            return;
        }
        const same = id && id === this.state.batchAId;
        const bObj = this.batches.find((b) => b.id === id);
        Object.assign(this.state, {
            batchBId: id,
            sheetBIndex: same && (bObj?.sheets?.length || 0) > 1 && this.state.sheetAIndex === 0 ? 1 : 0,
            page: 1,
        });
        return this.load();
    }

    onChangeSheetB(ev) {
        Object.assign(this.state, { sheetBIndex: Number(ev.target.value) || 0, page: 1 });
        return this.load();
    }

    swapSides() {
        if (!this.state.batchBId) {
            return;
        }
        const aId = this.state.batchAId;
        const aSh = this.state.sheetAIndex;
        Object.assign(this.state, {
            batchAId: this.state.batchBId,
            sheetAIndex: this.state.sheetBIndex,
            batchBId: aId,
            sheetBIndex: aSh,
            page: 1,
        });
        return this.load();
    }

    toggleGroupCard(key) {
        const next = this.state.group === key ? "" : key;
        Object.assign(this.state, {
            draftGroup: next,
            group: next,
            page: 1,
        });
        return this.load();
    }

    toggleOnlyDiff(ev) {
        const val = Boolean(ev.target.checked);
        Object.assign(this.state, {
            draftOnlyDiff: val,
            onlyDiff: val,
            page: 1,
        });
        return this.load();
    }

    applyFilters() {
        Object.assign(this.state, {
            onlyDiff: Boolean(this.state.draftOnlyDiff),
            group: this.state.draftGroup,
            sourceGroup: this.state.draftSourceGroup,
            workDate: this.state.draftWorkDate,
            search: this.state.draftSearch.trim(),
            page: 1,
        });
        return this.load();
    }

    clearFilters() {
        Object.assign(this.state, {
            draftOnlyDiff: false,
            draftGroup: "",
            draftSourceGroup: "",
            draftWorkDate: "",
            draftSearch: "",
            onlyDiff: false,
            group: "",
            sourceGroup: "",
            workDate: "",
            search: "",
            page: 1,
        });
        return this.load();
    }

    removeChip(key) {
        if (key === "onlyDiff") {
            Object.assign(this.state, { draftOnlyDiff: false, onlyDiff: false, page: 1 });
        } else if (key === "group") {
            Object.assign(this.state, { draftGroup: "", group: "", page: 1 });
        } else if (key === "sourceGroup") {
            Object.assign(this.state, { draftSourceGroup: "", sourceGroup: "", page: 1 });
        } else if (key === "workDate") {
            Object.assign(this.state, { draftWorkDate: "", workDate: "", page: 1 });
        } else if (key === "search") {
            Object.assign(this.state, { draftSearch: "", search: "", page: 1 });
        }
        return this.load();
    }

    onSearchKeydown(ev) {
        if (ev.key === "Enter") {
            ev.preventDefault();
            this.applyFilters();
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

    async exportCompare() {
        if (!this.state.batchAId) {
            return;
        }
        try {
            const file = await this.orm.call("tp.hr.attendance.batch", "tp_export_compare", [this.params()]);
            downloadBase64(file);
        } catch (error) {
            this.state.error = rpcError(error, "Không xuất được tệp đối chiếu Excel.");
        }
    }

    formatCellTime(scope, cell) {
        if (scope !== "in_period" || !cell) {
            return this.scopeLabel(scope);
        }
        if (cell.kind === "empty") {
            return "Ô trống";
        }
        return `${cell.raw_in || "—"} / ${cell.raw_out || "—"}`;
    }

    formatCanonicalTime(can) {
        if (!can || !can.exists) {
            return "Chưa áp dụng";
        }
        return `${can.norm_in || "—"} / ${can.norm_out || "—"}`;
    }

    formatLateBox(late) {
        if (!late) {
            return "—";
        }
        if (late.source_state === "ok") {
            return `${late.count} lần · ${late.minutes}p`;
        }
        return `${late.raw_count || "—"} / ${late.raw_minutes || "—"} (${late.source_state})`;
    }

    groupBadgeClass(groupKey) {
        if (groupKey === "same") {
            return "o_ok";
        }
        if (groupKey === "only_a" || groupKey === "only_b") {
            return "o_info";
        }
        if (groupKey === "diff") {
            return "o_danger";
        }
        if (groupKey === "unready") {
            return "o_warn";
        }
        return "o_muted";
    }
}
