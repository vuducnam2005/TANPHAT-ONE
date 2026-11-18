import { Component, onWillStart, proxy, useProps } from "@odoo/owl";
import { session } from "@web/session";
import { user } from "@web/core/user";
import { Dialog } from "@web/core/dialog/dialog";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { downloadBase64, formatDate, readStore, rpcError, writeStore } from "../common";
import { AttendanceCompare } from "./compare";
import { AttPager } from "../parts";
import { openAttendanceUpload } from "../upload/upload";

const STORE_KEY = "tp_hr_attendance.matrix.v2";

/**
 * Confirmation dialog for applying valid/identical lines of a source batch or discarding an unapplied batch.
 */
export class MatrixConfirmDialog extends Component {
    static template = "tp_hr_attendance.MatrixConfirmDialog";
    static components = { Dialog };
    props = useProps();

    setup() {
        this.state = proxy({ reason: "", busy: false, error: "" });
    }

    async confirm() {
        if (this.state.busy) {
            return;
        }
        this.state.busy = true;
        this.state.error = "";
        try {
            await this.props.onConfirm(this.state.reason.trim());
            this.props.close();
        } catch (error) {
            this.state.error = rpcError(error, "Không thực hiện được thao tác. Vui lòng thử lại.");
            this.state.busy = false;
        }
    }
}

/**
 * Per-employee source day-by-day detail modal (especially handy on mobile or when inspecting cell coordinates).
 */
export class MatrixPersonDialog extends Component {
    static template = "tp_hr_attendance.MatrixPersonDialog";
    static components = { Dialog };
    props = useProps();
}

/**
 * Full-width "Bảng dữ liệu theo file" (HR-ATTENDANCE-MATRIX-003, DEC-058 & DEC-044).
 * Displays the exact immutable two-row (Vào / Ra) matrix of a selected Excel source batch + sheet,
 * with content-specific filters, collapsible source unit bands, employee-level pagination (10/20/50/100)
 * and faithful Excel export.
 */
export class AttendanceFileMatrix extends Component {
    static template = "tp_hr_attendance.FileMatrix";
    static components = { AttPager };
    props = useProps();

    setup() {
        this.CompareComponent = AttendanceCompare;
        this.orm = useService("orm");
        this.action = useService("action");
        this.dialog = useService("dialog");
        this.notification = useService("notification");

        this.storeKey = `${STORE_KEY}:${session.db}:${user.userId}:${user.context.allowed_company_ids?.join(",") || ""}`;
        const saved = readStore(this.storeKey);
        const actionParams = this.props.action?.params || {};
        const initialCols = saved.cols || {};

        this.state = proxy({
            viewMode: actionParams.mode === "compare" ? "compare" : "matrix",
            batchId: Number(actionParams.batch_id || 0),
            compareBatchAId: Number(actionParams.batch_a_id || actionParams.batch_id || 0),
            compareBatchBId: Number(actionParams.batch_b_id || 0),
            uploadedIds: Array.isArray(actionParams.uploaded_ids) ? actionParams.uploaded_ids : [],
            uploadNotice: actionParams.upload_notice || "",
            includeCancelled: false,
            sheetIndex: 0,
            // Pending filter inputs (DEC-044: applied only on "Áp dụng" / Enter / chip removal)
            draftFrom: "",
            draftTo: "",
            draftGroup: "",
            draftSearch: "",
            draftStatus: "",
            // Applied filter state sent to server
            dateFrom: "",
            dateTo: "",
            sourceGroup: "",
            search: "",
            status: "",
            page: 1,
            pageSize: [10, 20, 50, 100].includes(saved.pageSize) ? saved.pageSize : 20,
            // Optional columns & UI toggles (default ID, Chức vụ, Vắng mặt ON to match machine attendance sheet)
            cols: {
                machineId: initialCols.machineId !== undefined ? Boolean(initialCols.machineId) : true,
                title: initialCols.title !== undefined ? Boolean(initialCols.title) : true,
                hrCode: Boolean(initialCols.hrCode),
                absent: initialCols.absent !== undefined ? Boolean(initialCols.absent) : true,
            },
            colMenuOpen: false,
            mobileFilterOpen: false,
            mobileView: "cards", // 'cards' | 'table'
            collapsedGroups: {},
            loading: true,
            applying: false,
            error: "",
            data: null,
        });

        this.formatDate = formatDate;
        this.request = 0;
        onWillStart(() => this.load());
    }

    get data() {
        return this.state.data;
    }
    get batch() {
        return this.data?.batch || null;
    }
    get sheet() {
        return this.data?.sheet || null;
    }
    get uploadedBatches() {
        if (!this.state.uploadedIds.length || !this.data?.batches) {
            return [];
        }
        const wanted = new Set(this.state.uploadedIds);
        return this.data.batches.filter((b) => wanted.has(b.id));
    }
    get stateBadgeTone() {
        const st = this.batch?.state;
        if (st === "applied") {
            return "o_ok";
        }
        if (st === "partial") {
            return "o_warn";
        }
        if (st === "cancelled") {
            return "o_muted";
        }
        return "o_info";
    }
    get hasPendingFilterDiff() {
        return (
            this.state.draftFrom !== this.state.dateFrom ||
            this.state.draftTo !== this.state.dateTo ||
            this.state.draftGroup !== this.state.sourceGroup ||
            this.state.draftSearch.trim() !== this.state.search ||
            this.state.draftStatus !== this.state.status
        );
    }
    get activeFilterCount() {
        return (this.data?.chips || []).length;
    }
    /** Total colspan of a source group header band row matching currently visible columns. */
    get totalMatrixCols() {
        if (!this.data) {
            return 6;
        }
        let cols = 4; // STT + Mã NV (Excel) + Tên nhân viên + Vào/Ra
        if (this.state.cols.hrCode) {
            cols += 1;
        }
        if (this.state.cols.machineId) {
            cols += 1;
        }
        if (this.state.cols.title) {
            cols += 1;
        }
        cols += (this.data.day_columns || []).length;
        if (this.sheet?.has_late) {
            cols += 2;
        }
        if (this.state.cols.absent && this.sheet?.has_absent) {
            cols += 1;
        }
        return cols;
    }

    params() {
        return {
            batch_id: this.state.batchId || 0,
            sheet_index: this.state.sheetIndex || 0,
            include_cancelled: this.state.includeCancelled,
            date_from: this.state.dateFrom,
            date_to: this.state.dateTo,
            source_group: this.state.sourceGroup,
            search: this.state.search,
            status: this.state.status,
            page: this.state.page,
            page_size: this.state.pageSize,
        };
    }

    savePrefs() {
        writeStore(this.storeKey, {
            pageSize: this.state.pageSize,
            cols: { ...this.state.cols },
        });
    }

    async load() {
        const req = ++this.request;
        this.state.loading = true;
        this.state.error = "";
        this.state.data = null;
        try {
            const data = await this.orm.call("tp.hr.attendance.batch", "tp_matrix_data", [this.params()]);
            if (req !== this.request) {
                return;
            }
            this.state.data = data;
            if (data.batch) {
                this.state.batchId = data.batch.id;
                this.state.sheetIndex = data.sheet.index;
                this.state.page = data.page;
                this.state.pageSize = data.page_size;
            }
            this.savePrefs();
        } catch (error) {
            if (req === this.request) {
                this.state.error = rpcError(error, "Không tải được bảng dữ liệu theo file. Vui lòng thử lại.");
            }
        } finally {
            if (req === this.request) {
                this.state.loading = false;
            }
        }
    }

    selectBatch(batchId) {
        const id = Number(batchId) || 0;
        if (!id || id === this.state.batchId) {
            return;
        }
        Object.assign(this.state, {
            batchId: id,
            sheetIndex: 0,
            draftFrom: "",
            draftTo: "",
            draftGroup: "",
            draftStatus: "",
            dateFrom: "",
            dateTo: "",
            sourceGroup: "",
            status: "",
            page: 1,
            collapsedGroups: {},
        });
        return this.load();
    }

    onBatchSelect(ev) {
        return this.selectBatch(ev.target.value);
    }

    selectSheet(index) {
        const idx = Number(index) || 0;
        if (idx === this.state.sheetIndex) {
            return;
        }
        Object.assign(this.state, {
            sheetIndex: idx,
            draftFrom: "",
            draftTo: "",
            draftGroup: "",
            dateFrom: "",
            dateTo: "",
            sourceGroup: "",
            page: 1,
            collapsedGroups: {},
        });
        return this.load();
    }

    toggleIncludeCancelled(ev) {
        this.state.includeCancelled = Boolean(ev.target.checked);
        this.state.page = 1;
        return this.load();
    }

    applyFilters() {
        if (this.state.draftFrom && this.state.draftTo && this.state.draftTo < this.state.draftFrom) {
            this.state.error = "Ngày kết thúc lọc phải sau hoặc bằng ngày bắt đầu.";
            return;
        }
        Object.assign(this.state, {
            dateFrom: this.state.draftFrom,
            dateTo: this.state.draftTo,
            sourceGroup: this.state.draftGroup,
            search: this.state.draftSearch.trim(),
            status: this.state.draftStatus,
            page: 1,
            mobileFilterOpen: false,
        });
        return this.load();
    }

    onFilterKeydown(ev) {
        if (ev.key === "Enter") {
            ev.preventDefault();
            this.applyFilters();
        } else if (ev.key === "Escape" && this.state.mobileFilterOpen) {
            this.state.mobileFilterOpen = false;
        }
    }

    clearFilters() {
        Object.assign(this.state, {
            draftFrom: "",
            draftTo: "",
            draftGroup: "",
            draftSearch: "",
            draftStatus: "",
            dateFrom: "",
            dateTo: "",
            sourceGroup: "",
            search: "",
            status: "",
            page: 1,
            mobileFilterOpen: false,
        });
        return this.load();
    }

    removeChip(chipKey) {
        if (chipKey === "date_range") {
            Object.assign(this.state, { draftFrom: "", draftTo: "", dateFrom: "", dateTo: "" });
        } else if (chipKey === "source_group") {
            Object.assign(this.state, { draftGroup: "", sourceGroup: "" });
        } else if (chipKey === "search") {
            Object.assign(this.state, { draftSearch: "", search: "" });
        } else if (chipKey.startsWith("status:")) {
            const target = chipKey.slice(7);
            const remaining = this.state.status
                .split(",")
                .map((s) => s.trim())
                .filter((s) => s && s !== target)
                .join(",");
            Object.assign(this.state, { draftStatus: remaining, status: remaining });
        }
        this.state.page = 1;
        return this.load();
    }

    toggleCol(colKey) {
        this.state.cols[colKey] = !this.state.cols[colKey];
        this.savePrefs();
    }

    toggleGroup(groupKey) {
        this.state.collapsedGroups[groupKey] = !this.state.collapsedGroups[groupKey];
    }

    setPage(page) {
        this.state.page = page;
        return this.load();
    }

    setSize(size) {
        Object.assign(this.state, { pageSize: size, page: 1 });
        return this.load();
    }

    cellTone(status) {
        if (status === "valid" || status === "applied") {
            return "o_tone_ok";
        }
        if (status === "duplicate") {
            return "o_tone_dup";
        }
        if (status === "conflict") {
            return "o_tone_conflict";
        }
        if (status === "missing") {
            return "o_tone_warn";
        }
        if (status === "review" || status === "unmapped" || status === "name_conflict") {
            return "o_tone_review";
        }
        if (status === "locked") {
            return "o_tone_locked";
        }
        return "";
    }

    cellTooltip(person, cell) {
        const parts = [`${person.source_name} · ${this.formatDate(cell.date)}`];
        if (cell.cell_ref) {
            parts.push(`Ô ${cell.cell_ref}`);
        }
        parts.push(`Vào: ${cell.raw_in || "—"} | Ra: ${cell.raw_out || "—"}`);
        if (cell.status_label) {
            parts.push(cell.status_label);
        }
        if (cell.message) {
            parts.push(cell.message);
        }
        return parts.join(" · ");
    }

    openPersonDetail(person) {
        this.dialog.add(MatrixPersonDialog, {
            person,
            dayColumns: this.data?.day_columns || [],
            sheet: this.sheet,
            batch: this.batch,
            formatDate: this.formatDate,
        });
    }

    openUploadMore() {
        openAttendanceUpload(this.env, {
            onUploaded: ({ createdIds, uploadNotice }) => {
                Object.assign(this.state, {
                    viewMode: "matrix",
                    batchId: createdIds[0] || this.state.batchId,
                    uploadedIds: createdIds,
                    uploadNotice: uploadNotice || "",
                    sheetIndex: 0,
                    draftFrom: "",
                    draftTo: "",
                    draftGroup: "",
                    dateFrom: "",
                    dateTo: "",
                    sourceGroup: "",
                    page: 1,
                });
                this.load();
            },
        });
    }

    openApplyConfirm() {
        if (!this.batch?.can_apply) {
            return;
        }
        const summary = this.data?.summary || {};
        this.dialog.add(MatrixConfirmDialog, {
            title: "Áp dụng toàn bộ lô nguồn vào bảng chấm công",
            mode: "apply",
            batch: this.batch,
            summary,
            onConfirm: async () => {
                await this.orm.call("tp.hr.attendance.batch", "tp_upload_apply", [this.batch.id]);
                this.notification.add("Đã áp dụng các dòng hợp lệ của lô nguồn vào bảng chấm công.", { type: "success" });
                await this.load();
            },
        });
    }

    openDiscardConfirm() {
        if (!this.batch?.can_discard) {
            return;
        }
        this.dialog.add(MatrixConfirmDialog, {
            title: "Bỏ qua nguồn tệp Excel này",
            mode: "discard",
            batch: this.batch,
            summary: this.data?.summary || {},
            onConfirm: async (reason) => {
                await this.orm.call("tp.hr.attendance.batch", "tp_discard_batch", [this.batch.id, reason]);
                this.notification.add("Đã đánh dấu bỏ qua lô nguồn (dữ liệu đã áp dụng trước đó không bị ảnh hưởng).", { type: "info" });
                await this.load();
            },
        });
    }

    async exportMatrix() {
        if (!this.batch) {
            return;
        }
        try {
            const file = await this.orm.call("tp.hr.attendance.batch", "tp_export_matrix", [{
                ...this.params(),
                show_machine_id: this.state.cols.machineId,
                show_title: this.state.cols.title,
                show_hr_code: this.state.cols.hrCode,
                show_absent: this.state.cols.absent,
            }]);
            downloadBase64(file);
        } catch (error) {
            this.state.error = rpcError(error, "Không xuất được tệp Excel của bảng nguồn.");
        }
    }

    openCompare() {
        const batches = (this.data?.batches || []).filter((b) => b.state !== "cancelled");
        const currentId = this.batch?.state !== "cancelled" ? (this.batch?.id || 0) : (batches[0]?.id || 0);
        const other = batches.find((b) => b.id !== currentId);
        this.state.compareBatchAId = currentId;
        this.state.compareBatchBId = other ? other.id : 0;
        this.state.viewMode = "compare";
    }

    backToMatrix(batchId = 0) {
        this.state.viewMode = "matrix";
        if (batchId && batchId !== this.state.batchId) {
            return this.selectBatch(batchId);
        }
        return this.load();
    }

    goBack() {
        return this.action.doAction("tp_hr_attendance.action_board");
    }
}

registry.category("actions").add("tp_hr_attendance.file_matrix", AttendanceFileMatrix);
