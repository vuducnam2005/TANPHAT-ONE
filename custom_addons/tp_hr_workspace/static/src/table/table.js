import { Component, onPatched, onWillStart, onWillUnmount, proxy, useProps } from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { Dialog } from "@web/core/dialog/dialog";
import { download } from "@web/core/network/download";
import { formatDateTime } from "@web/core/l10n/dates";
import { registry } from "@web/core/registry";
import { useBus, useService } from "@web/core/utils/hooks";
import { useSortable } from "@web/core/utils/sortable_owl";
import { RelationalModel } from "@web/model/relational_model/relational_model";
import { render } from "@web/owl2/utils";
import { session } from "@web/session";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { ListController } from "@web/views/list/list_controller";
import { ListRenderer } from "@web/views/list/list_renderer";
import { listView } from "@web/views/list/list_view";
import { TpTableFilterBar } from "@tp_web_home/search/table_filter_bar";
import { InlineErrors } from "@tp_web_home/validation/inline_errors";
import { saveError } from "@tp_web_home/validation/validation";
import { HrEmployeeFilterBar } from "./live_name_filter";
import { PAGE_SIZE_OPTIONS, readPageSize, tablePageKey, writePageSize } from "../prefs";
import {
    REORDER_LOCK_GUIDANCE,
    REORDER_SUCCESS_TOAST,
    analyzeEmployeeReorderState,
    isDepartmentCompleteDomain,
} from "./employee_reorder_rules";
import "./filter_profiles";

// Shared motion so neighbours making room and the dropped row settling feel like one gesture.
const ROW_MOTION_EASING = "cubic-bezier(0.2, 0, 0, 1)";
const ROW_SHIFT_MS = 180;
const ROW_SETTLE_MS = 220;
const DROP_SETTLE_MAX_WAIT_MS = 1000;

export class HrEmployeeExportDialog extends Component {
    static template = "tp_hr_workspace.EmployeeExportDialog";
    static components = { Dialog };
    props = useProps();

    setup() {
        this.orm = useService("orm");
        this.state = proxy({ scope: "filtered", counts: {}, loading: true, busy: false, error: "" });
        onWillStart(() => this.loadCounts());
    }

    async loadCounts() {
        this.state.loading = true;
        this.state.error = "";
        try {
            const results = await Promise.all(["filtered", "all", "selected"].map((scope) =>
                this.orm.call("tp.hr.workspace", "get_employee_export_summary", [{ ...this.props.options, scope }])
            ));
            this.state.counts = Object.fromEntries(results.map((result) => [result.scope, result.count]));
        } catch (error) {
            this.state.error = error.data?.message || "Không đếm được nhân viên. Hãy thử lại.";
        } finally {
            this.state.loading = false;
        }
    }

    async exportFile() {
        if (this.state.busy || this.state.loading || !this.state.counts[this.state.scope]) {
            return;
        }
        this.state.busy = true;
        this.state.error = "";
        try {
            await download({ url: "/tp_hr/export", data: {
                options: JSON.stringify({ ...this.props.options, scope: this.state.scope }),
            } });
            this.props.close();
        } catch (error) {
            this.state.error = error.data?.message || "Không xuất được Excel. Hãy thử lại.";
        } finally {
            this.state.busy = false;
        }
    }

    changeScope(ev) {
        this.state.scope = ev.target.value;
    }
}

function isEmployeeListModel(resModel) {
    return resModel === "hr.employee" || resModel === "hr.employee.public";
}

export class HrListModel extends RelationalModel {
    _getNextConfig(currentConfig, params) {
        const nextConfig = super._getNextConfig(currentConfig, params);
        if (
            isEmployeeListModel(nextConfig.resModel) &&
            !nextConfig.isMonoRecord &&
            !nextConfig.context?.tp_hr_relation &&
            nextConfig.fields?.department_id
        ) {
            // Department sections belong to the list layout, independent of search facets.
            const groupBy = nextConfig.groupBy || [];
            nextConfig.groupBy = ["department_id", ...groupBy.filter((name) => name !== "department_id")];
        }
        return nextConfig;
    }
}

export class HrTableTools extends Component {
    static template = "tp_hr_workspace.TableTools";
    props = useProps();
    pageSizes = PAGE_SIZE_OPTIONS;
    state = proxy({ busy: false, error: "" });
    async changeSize(ev) {
        const controller = this.props.controller;
        const limit = Number(ev.target.value);
        if (this.state.busy || controller.editedRecord || !PAGE_SIZE_OPTIONS.includes(limit)) {
            return;
        }
        this.state.busy = true;
        this.state.error = "";
        try {
            await controller.model.root.load({ limit, offset: 0 });
            writePageSize(controller.hrPageKey, limit);
            render(controller);
        } catch {
            this.state.error = "Không tải được trang. Hãy chọn lại số dòng để thử lại.";
            ev.target.value = String(controller.model.root.limit);
        } finally {
            this.state.busy = false;
        }
    }
}

export class HrListRenderer extends ListRenderer {
    static template = "tp_hr_workspace.ListRenderer";
    static recordRowTemplate = "tp_hr_workspace.RecordRow";
    static groupRowTemplate = "tp_hr_workspace.GroupRow";
    static components = { ...ListRenderer.components, InlineErrors };

    setup() {
        super.setup();
        this.tpReorderBusy = false;
        // FORM-VALIDATION-002: a rejected reorder is explained above the list it happened in.
        this.tpReorderError = null;
        this.tpReorderAttempt = 0;
        this._tpSuppressClickUntil = 0;
        this._tpCleanupDragPointer = null;
        this._tpRowAnimations = new Map();
        this._tpDropSettle = null;
        this._tpUnmounted = false;
        // The optimistic reorder is only in the DOM once Owl has patched; animating earlier
        // measures the old row order and makes neighbours jump a full row on release.
        onPatched(() => this.settleDroppedRow());
        onWillUnmount(() => {
            this._tpUnmounted = true;
            this._tpDropSettle = null;
            for (const animation of this._tpRowAnimations.values()) {
                animation.cancel();
            }
            this._tpRowAnimations.clear();
        });

        let activeSourceGroup = null;
        let lastPointer = null;
        let neighborPositions = new Map();
        const isInsideSource = () => {
            if (!activeSourceGroup || !lastPointer) {
                return false;
            }
            const rect = activeSourceGroup.getBoundingClientRect();
            return lastPointer.clientX >= rect.left && lastPointer.clientX <= rect.right &&
                lastPointer.clientY >= rect.top && lastPointer.clientY <= rect.bottom;
        };

        const clearDragZoneMarkers = () => {
            const table = this.tableRef();
            if (table) {
                table.classList.remove("o_tp_hr_dragging", "o_tp_hr_drop_invalid");
                for (const tb of table.querySelectorAll("tbody.is-drop-forbidden, tbody.is-drag-source")) {
                    tb.classList.remove("is-drop-forbidden", "is-drag-source");
                }
            }
            browser.document?.body?.classList.remove("o_tp_hr_drop_forbidden_cursor");
        };

        const cleanupPointerTracking = () => {
            if (this._tpCleanupDragPointer) {
                this._tpCleanupDragPointer();
                this._tpCleanupDragPointer = null;
            }
            clearDragZoneMarkers();
            activeSourceGroup = null;
            lastPointer = null;
        };

        onWillUnmount(cleanupPointerTracking);

        this.tpDragState = useSortable({
            enable: () => this.canDragEmployeesNow && !this.tpReorderBusy,
            ref: this.rootRef,
            elements: ".o_tp_hr_draggable_row",
            groups: "tbody.o_tp_hr_dept_tbody",
            connectGroups: false,
            ignore: ".o_list_record_selector, button, a, input, select, textarea, label, [role=button], [contenteditable=true]",
            preventDrag: () => Boolean(this.props.list.editedRecord),
            cursor: "grabbing",
            placeholderClasses: ["d-table-row", "o_tp_hr_drop_placeholder"],
            followingElementClasses: ["o_tp_hr_drag_preview"],
            onDragStart: (params) => {
                this._tpSuppressClickUntil = Date.now() + 600;
                this._tpDropSettle = null;
                this.sortStart(params);
                activeSourceGroup = params.group || params.element?.closest("tbody.o_tp_hr_dept_tbody");
                lastPointer = null;

                const table = this.tableRef();
                if (table) {
                    table.classList.add("o_tp_hr_dragging");
                }
                if (activeSourceGroup) {
                    activeSourceGroup.classList.add("is-drag-source");
                }
                neighborPositions = this.employeeRowPositions();

                const onPointerMove = (ev) => {
                    if (!activeSourceGroup) {
                        return;
                    }
                    lastPointer = { clientX: ev.clientX, clientY: ev.clientY };
                    const valid = isInsideSource();
                    table?.classList.toggle("o_tp_hr_drop_invalid", !valid);
                    browser.document?.body?.classList.toggle("o_tp_hr_drop_forbidden_cursor", !valid);
                };

                browser.addEventListener("pointermove", onPointerMove, { capture: true });
                browser.addEventListener("pointerup", onPointerMove, { capture: true });
                this._tpCleanupDragPointer = () => {
                    browser.removeEventListener("pointermove", onPointerMove, { capture: true });
                    browser.removeEventListener("pointerup", onPointerMove, { capture: true });
                };
            },
            onElementEnter: () => {
                this.animateEmployeeRows(neighborPositions);
                neighborPositions = this.employeeRowPositions();
            },
            onDragEnd: (params) => {
                this._tpSuppressClickUntil = Date.now() + 350;
                this.sortStop(params);
                // Delay cleanup by one microtask until the sortable drop callback has read the final pointer position.
                Promise.resolve().then(cleanupPointerTracking);
            },
            onDrop: async ({ element, group, previous, next, parent }) => {
                this._tpSuppressClickUntil = Date.now() + 450;
                const validZone = isInsideSource();
                if (!validZone || !group || (parent && parent !== group)) {
                    return;
                }
                // Read where the row floats under the pointer before sortable cleanup snaps it back.
                const releaseRect = element?.getBoundingClientRect?.();
                await this.onEmployeeDropInDepartment({ element, group, previous, next, releaseRect });
            },
        });
    }

    get getEmptyRowIds() {
        return [];
    }

    get employeeReorderState() {
        const list = this.props.list;
        return analyzeEmployeeReorderState({
            resModel: list.resModel,
            isGrouped: list.isGrouped,
            groupBy: list.groupBy,
            orderBy: list.orderBy,
            domain: list.domain,
            context: list.context,
            displayName: this.env.config?.displayName,
            canReorderSession: Boolean(session.tp_hr_can_reorder),
            readonly: Boolean(this.props.readonly),
            canEditView: this.props.activeActions?.edit,
        });
    }

    get canDragEmployeesNow() {
        return this.employeeReorderState.canDrag;
    }

    get isDeptGroupedEmployeeList() {
        const list = this.props.list;
        return (
            list.resModel === "hr.employee" &&
            list.isGrouped &&
            list.groupBy?.length === 1 &&
            list.groupBy[0] === "department_id"
        );
    }

    hrGroupDeptId(group) {
        const raw =
            group?.record?.resId ||
            (Array.isArray(group?.value) ? group.value[0] : group?.value);
        return typeof raw === "number" && raw > 0 ? raw : 0;
    }

    get hasSelectors() {
        if (this.props.list.resModel === "hr.employee.public" && session.tp_hr_readonly) {
            return false;
        }
        return super.hasSelectors;
    }

    getActiveColumns() {
        const columns = super.getActiveColumns();
        const filtered =
            isEmployeeListModel(this.props.list.resModel) &&
            this.props.list.groupBy?.includes("department_id")
                ? columns.filter((column) => column.name !== "department_id")
                : columns;
        return filtered;
    }

    getRowClass(record) {
        const base = super.getRowClass(record);
        if (this.canDragEmployeesNow) {
            return `${base} o_tp_hr_draggable_row`.trim();
        }
        return base;
    }

    _shouldSuppressAfterDrag(ev) {
        if (
            this.tpDragState?.dragging ||
            Date.now() < this._tpSuppressClickUntil
        ) {
            ev?.stopPropagation?.();
            ev?.preventDefault?.();
            return true;
        }
        return false;
    }

    onClickCapture(record, ev) {
        if (this._shouldSuppressAfterDrag(ev)) {
            return;
        }
        return super.onClickCapture(record, ev);
    }

    async onCellClicked(record, column, ev, newWindow) {
        if (this._shouldSuppressAfterDrag(ev)) {
            return;
        }
        return super.onCellClicked(record, column, ev, newWindow);
    }

    toggleRecordSelection(record, ev) {
        if (this.tpDragState?.dragging || Date.now() < this._tpSuppressClickUntil) {
            return;
        }
        return super.toggleRecordSelection(record, ev);
    }

    employeeRowPositions() {
        return new Map(
            [...(this.tableRef()?.querySelectorAll(".o_data_row:not(.o_dragged):not(.o_tp_hr_drop_placeholder)") || [])]
                .map((row) => [row.dataset.resId, row.offsetTop])
        );
    }

    get prefersReducedMotion() {
        return Boolean(browser.matchMedia?.("(prefers-reduced-motion: reduce)").matches);
    }

    /**
     * Animates the cells, not the row: the row's native pointer hitbox stays where the
     * layout put it, so sortable keeps receiving the right pointerenter targets.
     * Returns the started animations.
     */
    animateRowCells(row, keyframesFor, duration) {
        const animations = [];
        for (const cell of row.children) {
            const keyframes = keyframesFor(cell);
            this._tpRowAnimations.get(cell)?.cancel();
            const animation = cell.animate?.(keyframes, { duration, easing: ROW_MOTION_EASING });
            if (!animation) {
                continue;
            }
            animations.push(animation);
            this._tpRowAnimations.set(cell, animation);
            const clear = () => {
                if (this._tpRowAnimations.get(cell) === animation) {
                    this._tpRowAnimations.delete(cell);
                }
            };
            animation.finished.then(clear, clear);
        }
        return animations;
    }

    animateEmployeeRows(positions) {
        if (this._tpUnmounted || this.prefersReducedMotion) {
            return;
        }
        for (const row of this.tableRef()?.querySelectorAll(".o_data_row:not(.o_dragged):not(.o_tp_hr_drop_placeholder)") || []) {
            const previousTop = positions.get(row.dataset.resId);
            const delta = previousTop === undefined ? 0 : previousTop - row.offsetTop;
            if (delta) {
                this.animateRowCells(row, (cell) => {
                    // Continue from where an interrupted shift currently shows the cell.
                    const transform = browser.getComputedStyle(cell).transform;
                    const visualDelta = transform === "none" ? 0 : new browser.DOMMatrixReadOnly(transform).m42;
                    return [{ transform: `translateY(${delta + visualDelta}px)` }, { transform: "translateY(0)" }];
                }, ROW_SHIFT_MS);
            }
        }
    }

    /**
     * Called after each patch: once the optimistic order is in the DOM, glide the dropped
     * row from where the pointer released it into its slot instead of snapping there.
     */
    settleDroppedRow() {
        const settle = this._tpDropSettle;
        if (!settle) {
            return;
        }
        if (this._tpUnmounted || Date.now() - settle.at > DROP_SETTLE_MAX_WAIT_MS) {
            this._tpDropSettle = null;
            return;
        }
        const row = this.tableRef()?.querySelector(`.o_data_row[data-res-id="${settle.employeeId}"]`);
        const sibling = (direction) => {
            let el = row?.[direction];
            while (el && !el.classList?.contains("o_data_row")) {
                el = el[direction];
            }
            return Number(el?.dataset?.resId || 0) || null;
        };
        const inDroppedSlot = settle.beforeId
            ? sibling("nextElementSibling") === settle.beforeId
            : sibling("previousElementSibling") === settle.afterId;
        if (!row || !inDroppedSlot) {
            // An unrelated patch ran first; wait for the one carrying the reorder.
            return;
        }
        this._tpDropSettle = null;
        if (this.prefersReducedMotion) {
            return;
        }
        const rect = row.getBoundingClientRect();
        const dx = settle.releaseRect.left - rect.left;
        const dy = settle.releaseRect.top - rect.top;
        if (Math.abs(dx) < 1 && Math.abs(dy) < 1) {
            return;
        }
        row.classList.add("o_tp_hr_row_settling");
        const animations = this.animateRowCells(row, () => [
            { transform: `translate(${dx}px, ${dy}px)`, opacity: 0.85 },
            { transform: "translate(0, 0)", opacity: 1 },
        ], ROW_SETTLE_MS);
        const done = () => row.classList.remove("o_tp_hr_row_settling");
        Promise.all(animations.map((animation) => animation.finished)).then(done, done);
    }

    async onEmployeeDropInDepartment({ element, group, previous, next, releaseRect }) {
        if (this.tpReorderBusy || !this.canDragEmployeesNow) {
            return;
        }
        const employeeId = Number(element?.dataset?.resId || 0);
        const deptId = Number(group?.dataset?.deptId || 0);
        if (!employeeId) {
            return;
        }

        let prevRow = previous;
        while (prevRow && (!prevRow.classList?.contains("o_data_row") || prevRow === element)) {
            prevRow = prevRow.previousElementSibling;
        }
        let nextRow = next;
        while (nextRow && (!nextRow.classList?.contains("o_data_row") || nextRow === element)) {
            nextRow = nextRow.nextElementSibling;
        }

        const afterId = prevRow ? Number(prevRow.dataset.resId || 0) || null : null;
        const beforeId = nextRow ? Number(nextRow.dataset.resId || 0) || null : null;
        if (!afterId && !beforeId) {
            return;
        }

        const departmentList = this.props.list.groups
            ?.find((item) => this.hrGroupDeptId(item) === deptId)?.list;
        const records = departmentList?.records;
        const movedIndex = records?.findIndex((record) => record.resId === employeeId) ?? -1;
        if (movedIndex < 0) {
            return;
        }
        const originalRecords = [...records];
        const rootList = this.props.list;
        const isCurrentDepartment = () => !this._tpUnmounted && this.props.list.groups
            ?.some((item) => item.list === departmentList);
        const isCurrentList = () => isCurrentDepartment() && departmentList.records === records;
        const [moved] = records.splice(movedIndex, 1);
        const anchorIndex = records.findIndex((record) => record.resId === (beforeId || afterId));
        if (anchorIndex < 0) {
            records.splice(0, records.length, ...originalRecords);
            return;
        }
        records.splice(anchorIndex + (beforeId ? 0 : 1), 0, moved);

        // Neighbours already sit where the placeholder left them; only the dropped row
        // still has to travel, which onPatched does right after Owl applies this render.
        this._tpDropSettle = releaseRect
            ? { employeeId, beforeId, afterId, releaseRect, at: Date.now() }
            : null;
        this.tpReorderBusy = true;
        this.tpReorderError = null;
        render(this);
        let saved = false;
        try {
            const result = await this.orm.call("hr.employee", "tp_reorder_in_department", [
                employeeId,
                deptId || false,
                beforeId,
                afterId,
            ]);
            saved = true;
            if (!isCurrentList()) {
                return;
            }
            if (Array.isArray(result?.ordered_ids)) {
                const rank = new Map(result.ordered_ids.map((id, index) => [id, index]));
                const pageIds = result.ordered_ids.slice(departmentList.offset || 0,
                    (departmentList.offset || 0) + originalRecords.length);
                if (pageIds.length === records.length && pageIds.every((id) => records.some((record) => record.resId === id))) {
                    records.sort((left, right) => rank.get(left.resId) - rank.get(right.resId));
                    for (const record of records) {
                        record._applyValues({ sequence: (rank.get(record.resId) + 1) * 10 });
                    }
                } else {
                    // Concurrent changes can move another employee onto this page.
                    await departmentList.load();
                }
            }
            if (!isCurrentDepartment()) {
                return;
            }
            render(this);
            this.notificationService.add(REORDER_SUCCESS_TOAST, { type: "success" });
        } catch (err) {
            if (saved) {
                if (isCurrentDepartment()) {
                    this.notificationService.add("Đã lưu thứ tự nhưng chưa tải lại được danh sách. Hãy tải lại trang.", { type: "warning" });
                }
                return;
            }
            if (!isCurrentList()) {
                return;
            }
            records.splice(0, records.length, ...originalRecords);
            render(this);
            try {
                await rootList.model.root.load();
                if (!this._tpUnmounted && this.props.list === rootList) {
                    render(this);
                }
            } catch {
                // ignore secondary reload error
            }
            if (this._tpUnmounted || this.props.list !== rootList) {
                return;
            }
            this.tpReorderError = saveError(err, { verb: "sắp xếp", note: "Đã khôi phục vị trí cũ trong danh sách." });
            this.tpReorderAttempt++;
            render(this);
        } finally {
            this.tpReorderBusy = false;
        }
    }

    getGroupText(group) {
        return `${group.count} ${isEmployeeListModel(this.props.list.resModel) ? "thành viên" : "bản ghi"}`;
    }

    hrGroupLabel(group) {
        return isEmployeeListModel(this.props.list.resModel) &&
            group.groupByField.name === "department_id" &&
            !group.value
            ? "Chưa khai báo phòng ban"
            : group.displayName;
    }
}

const TABLE_CONTENT = {
    "tp.hr.employee.audit": [
        "Nhật ký hồ sơ và tài khoản",
        "Theo dõi thay đổi nhân viên và tài khoản. Chọn các dòng cần dọn, mở Tác vụ → Xóa nhật ký khỏi danh sách.",
        "",
        "Chưa có nhật ký",
    ],
    "hr.employee": [
        "Danh sách nhân viên",
        "Thông tin công việc, liên hệ và tài khoản trong phạm vi được xem.",
        "Thêm nhân viên",
        "Chưa có nhân viên",
    ],
    "hr.department": [
        "Phòng ban và đơn vị",
        "Cơ cấu tổ chức, người quản lý và nhân viên đang sử dụng hồ sơ.",
        "Thêm phòng ban",
        "Chưa có phòng ban",
    ],
    "hr.job": [
        "Chức vụ",
        "Vị trí nhân sự và phòng ban áp dụng. Chức vụ không tự cấp quyền hệ thống.",
        "Thêm chức vụ",
        "Chưa có chức vụ",
    ],
    "hr.work.location": [
        "Nơi làm việc",
        "Quản lý địa điểm để phân công nơi làm việc cho nhân viên.",
        "Thêm nơi làm việc",
        "Chưa có nơi làm việc",
    ],
    "hr.employee.category": [
        "Nhãn nhân viên",
        "Phân loại hồ sơ bằng nhãn; nhãn không thay đổi phòng ban hoặc quyền.",
        "Thêm nhãn nhân viên",
        "Chưa có nhãn nhân viên",
    ],
    "tp.hr.import.batch": [
        "Nhập và đối chiếu",
        "Chọn tệp, xem trước và đối chiếu trước khi áp dụng vào hồ sơ.",
        "Tạo lô nhập",
        "Chưa có lô nhập",
    ],
    "hr.employee.public": [
        "Danh sách nhân viên",
        "Thông tin công việc của đồng nghiệp trong phạm vi được xem.",
        "",
        "Chưa có nhân viên",
    ],
    "tp.hr.import.line": [
        "Đối chiếu từng dòng",
        "Rà soát ánh xạ và xử lý xung đột trước khi áp dụng lô nhập.",
        "",
        "Không có dòng đối chiếu",
    ],
    "tp.hr.attendance.day": [
        "Bảng ngày công",
        "Tổng hợp giờ vào/ra và trạng thái ngày công trong phạm vi được xem.",
        "",
        "Chưa có dữ liệu ngày công",
    ],
    "tp.hr.attendance.correction": [
        "Đề nghị điều chỉnh công",
        "Danh sách phiếu giải trình và phê duyệt điều chỉnh giờ chấm công.",
        "Tạo đề nghị",
        "Chưa có đề nghị điều chỉnh",
    ],
    "tp.hr.attendance.period": [
        "Chốt kỳ công",
        "Quản lý kỳ chấm công, kiểm soát ngày cần rà soát và khóa kỳ.",
        "Tạo kỳ công",
        "Chưa có kỳ công nào",
    ],
    "tp.hr.attendance.rule": [
        "Quy tắc công",
        "Thiết lập khung giờ hành chính và quy tắc xác nhận công theo phòng ban.",
        "Thêm quy tắc",
        "Chưa có quy tắc công",
    ],
    "tp.hr.attendance.code": [
        "Mã máy chấm công",
        "Ánh xạ mã thiết bị chấm công với hồ sơ nhân sự tương ứng.",
        "Thêm mã máy",
        "Chưa có mã máy chấm công",
    ],
    "tp.hr.attendance.assignment": [
        "Phân công xử lý công",
        "Phân quyền phụ trách nhập liệu, rà soát và chốt kỳ công theo phòng ban.",
        "Thêm phân công",
        "Chưa có phân công xử lý công",
    ],
    "tp.hr.attendance.batch": [
        "Lịch sử nhập Excel chấm công",
        "Lưu vết các lô dữ liệu chấm công lịch sử trước khi đồng bộ ENTI tự động.",
        "",
        "Chưa có lô nhập lịch sử",
    ],
    "tp.hr.attendance.enti.mapping": [
        "Đối chiếu nhân viên chấm công",
        "Ghép nối tài khoản trên máy chấm công ENTI với hồ sơ nhân viên trong hệ thống.",
        "",
        "Chưa có dữ liệu đối chiếu ENTI",
    ],
    "tp.hr.attendance.enti.sync.log": [
        "Nhật ký đồng bộ chấm công",
        "Theo dõi lịch sử kết nối, số bản ghi đồng bộ và cảnh báo từ hệ thống ENTI.",
        "",
        "Chưa có nhật ký đồng bộ",
    ],
    "tp.hr.attendance.enti.employee.image": [
        "Nhật ký đồng bộ ảnh hồ sơ ENTI",
        "Lịch sử kiểm tra và áp dụng ảnh đại diện từ máy chấm công ENTI sang hồ sơ HR.",
        "",
        "Chưa có nhật ký đồng bộ ảnh",
    ],
    "tp.hr.attendance.late": [
        "Tổng đi muộn theo kỳ",
        "Thống kê số lần và số phút đi muộn ghi nhận theo kỳ công.",
        "",
        "Chưa có dữ liệu đi muộn",
    ],
};

export class HrListController extends ListController {
    static template = "tp_hr_workspace.ListView";
    static components = { ...ListController.components, HrTableTools, TpTableFilterBar, HrEmployeeFilterBar };

    setup() {
        super.setup();
        if (this.env.searchModel) {
            useBus(this.env.searchModel, "update", () => render(this));
        }
    }

    get showEmployeeExport() {
        return this.props.resModel === "hr.employee" && !this.env.inDialog && !this.props.context?.tp_hr_relation;
    }

    get showEmployeeLiveSearch() {
        return this.showEmployeeExport && !this.props.context?.tp_filter_profile;
    }

    openEmployeeExport() {
        const root = this.model.root;
        const facets = this.env.searchModel?.facets || [];
        this.dialogService.add(HrEmployeeExportDialog, {
            options: {
                domain: JSON.parse(JSON.stringify(this.env.searchModel?.domain || root.domain)),
                active_test: (this.env.searchModel?.context || root.context)?.active_test !== false,
                selected_ids: root.selection.map((record) => record.resId),
                selection_all: Boolean(root.isDomainSelected),
                filter_label: facets.map((facet) =>
                    [facet.title, ...(facet.values || []).map((value) => value.label)].filter(Boolean).join(": ")
                ).join("; ") || "Phạm vi danh sách hiện hành",
            },
        });
    }

    get isEmployeeList() {
        return isEmployeeListModel(this.props.resModel);
    }

    get isReadonlyDirectory() {
        return this.props.resModel === "hr.employee.public" && !this.activeActions?.edit;
    }

    get className() {
        return `${super.className || ""} o_tp_hr_table${this.isEmployeeList ? " o_tp_hr_employee_list" : ""}`;
    }

    get hrContent() {
        const mapped = TABLE_CONTENT[this.props.resModel];
        if (mapped) {
            return mapped;
        }
        const title =
            this.env.config?.displayName ||
            this.props.archInfo?.xmlDoc?.getAttribute?.("string") ||
            "Danh sách dữ liệu";
        return [
            title,
            "Quản lý và tra cứu dữ liệu trong phạm vi được xem.",
            "Thêm mới",
            "Chưa có dữ liệu",
        ];
    }

    get hrHasFilters() {
        return Boolean(this.env.searchModel?.facets.length);
    }

    get hrMissing() {
        return Boolean(this.props.context?.tp_hr_missing);
    }

    get hrReorderGuidanceText() {
        return REORDER_LOCK_GUIDANCE;
    }

    get showEmployeeReorderLockBanner() {
        if (!this.model?.isReady?.()) {
            return false;
        }
        const root = this.model.root;
        return analyzeEmployeeReorderState({
            resModel: this.props.resModel,
            isGrouped: root.isGrouped,
            groupBy: root.groupBy,
            orderBy: root.orderBy,
            domain: root.domain,
            context: root.context || this.props.context,
            displayName: this.env.config?.displayName,
            canReorderSession: Boolean(session.tp_hr_can_reorder),
            readonly: false,
            canEditView: this.activeActions?.edit,
        }).showLockBanner;
    }

    async resetToEmployeeCustomOrder() {
        const sm = this.env.searchModel;
        if (sm) {
            for (const facet of [...(sm.facets || [])]) {
                // Keep department-only filter facets; remove any employee-hiding or sub-group facets.
                let isDeptOnlyFacet = false;
                if (facet.type === "field") {
                    const searchItems = sm.getSearchItems(
                        (item) => item.groupId === facet.groupId && item.fieldName === "department_id"
                    );
                    isDeptOnlyFacet = searchItems.length > 0;
                }
                if (!isDeptOnlyFacet) {
                    sm.deactivateGroup(facet.groupId);
                }
            }
        }
        const root = this.model.root;
        if (!isDepartmentCompleteDomain(root.domain)) {
            await this.env.services.action.doAction("tp_hr_workspace.action_employees");
            return;
        }
        await root.load({
            orderBy: [
                { name: "sequence", asc: true },
                { name: "id", asc: true },
            ],
        });
        render(this);
    }

    clearHrFilters() {
        this.env.searchModel.clearQuery();
    }

    get hrPageKey() {
        return tablePageKey(this.props.resModel, this.env.config.actionId, this.env.config.viewId);
    }

    get modelParams() {
        const params = super.modelParams;
        if (params.config) {
            params.config.openGroupsByDefault = true;
        }
        const limit = readPageSize(this.hrPageKey);
        return this.props.state?.modelState ? params : { ...params, limit, groupsLimit: limit };
    }
}

registry.category("views").add("tp_hr_table", {
    ...listView,
    Model: HrListModel,
    Controller: HrListController,
    Renderer: HrListRenderer,
    buttonTemplate: "tp_hr_workspace.ListButtons",
});

export class HrIdentityCell extends Component {
    static template = "tp_hr_workspace.IdentityCell";
    props = useProps(standardFieldProps);
    get isEmployee() {
        return isEmployeeListModel(this.props.record.resModel);
    }
    get avatarUrl() {
        return `/web/image/${this.props.record.resModel}/${this.props.record.resId}/avatar_128`;
    }
}
registry.category("fields").add("tp_hr_identity", {
    component: HrIdentityCell,
    supportedTypes: ["char"],
});

export class HrActiveCell extends Component {
    static template = "tp_hr_workspace.ActiveCell";
    props = useProps(standardFieldProps);
}
registry.category("fields").add("tp_hr_active", {
    component: HrActiveCell,
    supportedTypes: ["boolean"],
});

export class HrEmploymentCell extends Component {
    static template = "tp_hr_workspace.EmploymentCell";
    props = useProps(standardFieldProps);
    get value() {
        return this.props.record.data[this.props.name] || "";
    }
    get label() {
        return (
            { short_term: "Ngắn hạn", long_term: "Dài hạn", outsourced: "Thuê khoán" }[this.value] ||
            "Chưa khai báo"
        );
    }
    change(ev) {
        return this.props.record.update({ [this.props.name]: ev.target.value || false });
    }
}
registry.category("fields").add("tp_hr_employment", {
    component: HrEmploymentCell,
    supportedTypes: ["selection"],
});

export class HrCountCell extends Component {
    static template = "tp_hr_workspace.CountCell";
    props = useProps(standardFieldProps);
    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
    }
    async open() {
        const action = await this.orm.call(this.props.record.resModel, "action_tp_employees", [
            [this.props.record.resId],
        ]);
        return this.action.doAction(action);
    }
}
registry.category("fields").add("tp_hr_count", {
    component: HrCountCell,
    supportedTypes: ["integer"],
});

export class HrDateTimeCell extends Component {
    static template = "tp_hr_workspace.DateTimeCell";
    props = useProps(standardFieldProps);
    get value() {
        const value = this.props.record.data[this.props.name];
        return value ? formatDateTime(value, { format: "dd/MM/yyyy HH:mm:ss" }) : "";
    }
}
registry.category("fields").add("tp_hr_datetime", {
    component: HrDateTimeCell,
    supportedTypes: ["datetime"],
});
