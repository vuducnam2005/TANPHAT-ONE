import { Component, onWillStart, proxy, useProps } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";
import { downloadBase64, formatDate, rpcError } from "../common";
import { AttPager } from "../parts";

const SCOPE_SHORT = {
    out_of_scope: "Ngoài kỳ tệp",
    blank_in_period: "Ô trống",
    not_in_file: "Không có trong tệp",
    no_batch_b: "Chưa chọn B",
};

const DECISION_LABELS = {
    use_a: "Chọn A",
    use_b: "Chọn B",
    keep_current: "Giữ hiện tại",
    defer: "Xử lý sau",
};

/**
 * Confirmation dialog for applying valid/non-conflicting comparison entries cleanly.
 */
export class CompareConfirmDialog extends Component {
    static template = "tp_hr_attendance.CompareConfirmDialog";
    static components = { Dialog };
    props = useProps();

    setup() {
        this.state = proxy({ busy: false, error: "" });
    }

    async confirm() {
        if (this.state.busy) {
            return;
        }
        this.state.busy = true;
        this.state.error = "";
        try {
            await this.props.onConfirm();
            this.props.close();
        } catch (error) {
            this.state.error = rpcError(error, "Không áp dụng được phần hợp lệ. Vui lòng thử lại.");
            this.state.busy = false;
        }
    }
}

/**
 * Pre-consolidation A/B file comparison & conflict resolution screen (HR-ATTENDANCE-MATRIX-003).
 * Uses tp.hr.attendance.batch RPCs: tp_compare_batches, tp_apply_compare_valid,
 * tp_resolve_compare_batch, and tp_export_compare.
 */
export class AttendanceCompare extends Component {
    static template = "tp_hr_attendance.Compare";
    static components = { AttPager };
    props = useProps();

    setup() {
        this.orm = useService("orm");
        this.dialog = useService("dialog");
        this.notification = useService("notification");

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
            savingDecisions: false,
            error: "",
            resolveError: "",
            resolveReason: "",
            pendingChoices: {},
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

    get pendingList() {
        return Object.values(this.state.pendingChoices || {});
    }

    get pendingNeedsReason() {
        return this.pendingList.some((c) => c.needs_reason);
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

    decisionLabel(key) {
        return DECISION_LABELS[key] || key;
    }

    scopeLabel(scope) {
        return SCOPE_SHORT[scope] || scope || "—";
    }

    dayChoiceKey(empId, workDate) {
        return `day:${empId}:${workDate}`;
    }

    lateChoiceKey(empId, dateFrom, dateTo) {
        return `late:${empId}:${dateFrom}:${dateTo}`;
    }

    selectedDayDecision(empId, workDate) {
        return this.state.pendingChoices[this.dayChoiceKey(empId, workDate)]?.decision || "";
    }

    selectedLateDecision(empId, dateFrom, dateTo) {
        return this.state.pendingChoices[this.lateChoiceKey(empId, dateFrom, dateTo)]?.decision || "";
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

    resetChoices() {
        this.state.pendingChoices = {};
        this.state.resolveReason = "";
        this.state.resolveError = "";
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
        this.resetChoices();
        return this.load();
    }

    onChangeSheetA(ev) {
        Object.assign(this.state, { sheetAIndex: Number(ev.target.value) || 0, page: 1 });
        this.resetChoices();
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
        this.resetChoices();
        return this.load();
    }

    onChangeSheetB(ev) {
        Object.assign(this.state, { sheetBIndex: Number(ev.target.value) || 0, page: 1 });
        this.resetChoices();
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
        this.resetChoices();
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

    pickDayDecision(row, d, decision) {
        if (!row.employee_id || row.mapping_state !== "mapped") {
            return;
        }
        if (decision === "use_a" && !d.can_use_a) {
            return;
        }
        if (decision === "use_b" && !d.can_use_b) {
            return;
        }
        const key = this.dayChoiceKey(row.employee_id, d.date);
        const existing = this.state.pendingChoices[key];
        const next = { ...this.state.pendingChoices };
        if (existing && existing.decision === decision) {
            delete next[key];
            this.state.pendingChoices = next;
            this.state.resolveError = "";
            return;
        }
        const srcCell = decision === "use_a" ? d.a_cell : decision === "use_b" ? d.b_cell : null;
        const can = d.canonical || {};
        const changesCanonical = Boolean(
            can.exists
            && srcCell
            && (srcCell.norm_in !== can.norm_in || srcCell.norm_out !== can.norm_out || srcCell.kind !== can.kind)
        );
        next[key] = {
            key,
            target_kind: "day",
            employee_id: row.employee_id,
            work_date: d.date,
            decision,
            expected_digest: d.target_digest,
            needs_reason: (decision === "use_a" || decision === "use_b") && changesCanonical,
            label: `${row.display_name} · ${formatDate(d.date)}`,
        };
        this.state.pendingChoices = next;
        this.state.resolveError = "";
    }

    pickLateDecision(row, li, decision) {
        if (!row.employee_id || row.mapping_state !== "mapped") {
            return;
        }
        if (decision === "use_a" && !li.can_use_a) {
            return;
        }
        if (decision === "use_b" && !li.can_use_b) {
            return;
        }
        const key = this.lateChoiceKey(row.employee_id, li.date_from, li.date_to);
        const existing = this.state.pendingChoices[key];
        const next = { ...this.state.pendingChoices };
        if (existing && existing.decision === decision) {
            delete next[key];
            this.state.pendingChoices = next;
            this.state.resolveError = "";
            return;
        }
        const srcLate = decision === "use_a" ? li.a_late : decision === "use_b" ? li.b_late : null;
        const can = li.canonical_late || {};
        const changesCanonical = Boolean(
            can.exists
            && srcLate
            && (srcLate.count !== can.count || srcLate.minutes !== can.minutes)
        );
        next[key] = {
            key,
            target_kind: "late",
            employee_id: row.employee_id,
            date_from: li.date_from,
            date_to: li.date_to,
            decision,
            expected_digest: li.target_digest,
            needs_reason: (decision === "use_a" || decision === "use_b") && changesCanonical,
            label: `${row.display_name} · Đi muộn (${li.period_label})`,
        };
        this.state.pendingChoices = next;
        this.state.resolveError = "";
    }

    async savePendingChoices() {
        const list = this.pendingList;
        if (!list.length || this.state.savingDecisions) {
            return;
        }
        const reason = this.state.resolveReason.trim();
        if (this.pendingNeedsReason && !reason) {
            this.state.resolveError = "Cần nhập lý do / căn cứ vì bạn đang thay đổi dữ liệu đã áp dụng.";
            return;
        }
        this.state.savingDecisions = true;
        this.state.resolveError = "";
        this.state.error = "";
        try {
            const payload = {
                ...this.params(),
                reason,
                items: list.map((c) => ({
                    target_kind: c.target_kind,
                    employee_id: c.employee_id,
                    work_date: c.work_date || "",
                    date_from: c.date_from || "",
                    date_to: c.date_to || "",
                    decision: c.decision,
                    reason,
                    expected_digest: c.expected_digest,
                })),
            };
            const result = await this.orm.call("tp.hr.attendance.batch", "tp_resolve_compare_batch", [payload]);
            this.state.data = result.compare;
            this.resetChoices();
            this.notification.add(
                `Đã lưu ${result.resolved} lựa chọn đối chiếu và ghi nhật ký kiểm toán.`,
                { type: "success" }
            );
        } catch (error) {
            this.state.resolveError = rpcError(error, "Không lưu được các lựa chọn đối chiếu. Vui lòng thử lại.");
        } finally {
            this.state.savingDecisions = false;
        }
    }

    openApplyValidModal() {
        if (!this.data?.can_apply_valid) {
            return;
        }
        const cc = this.data.cell_counts || {};
        const lc = this.data.late_counts || {};
        const validCells = (cc.same || 0) + (cc.only_a || 0) + (cc.only_b || 0);
        const validLates = (lc.same || 0) + (lc.only_a || 0) + (lc.only_b || 0);
        const diffCells = cc.diff || 0;
        const unreadyCells = cc.unready || 0;

        this.dialog.add(CompareConfirmDialog, {
            title: "Áp dụng phần giống nhau & mới hợp lệ",
            summaryLines: [
                `Ô ngày sẽ đưa vào tổng hợp: ${validCells} (Giống nhau: ${cc.same || 0}, Chỉ có ở A: ${cc.only_a || 0}, Chỉ có ở B: ${cc.only_b || 0}).`,
                `Tổng Đi muộn đúng kỳ sẽ ghi: ${validLates}.`,
                `Không tự ghi đè ${diffCells} ô khác giờ/số liệu, ${unreadyCells} ô chưa đủ căn cứ, các kỳ đã chốt và các ngày đã có điều chỉnh được duyệt.`,
            ],
            confirmLabel: "Xác nhận áp dụng phần hợp lệ",
            onConfirm: async () => {
                const res = await this.orm.call("tp.hr.attendance.batch", "tp_apply_compare_valid", [this.params()]);
                this.state.data = res.compare;
                this.resetChoices();
                this.notification.add(
                    `Đã áp dụng ${res.applied_cells} ô ngày và ${res.applied_lates} kỳ Đi muộn hợp lệ`
                    + (res.skipped_locked ? ` (bỏ qua ${res.skipped_locked} ô đã chốt/điều chỉnh).` : "."),
                    { type: "success" }
                );
            },
        });
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
