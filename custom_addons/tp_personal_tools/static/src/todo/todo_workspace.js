import {
    Component,
    onMounted,
    onWillStart,
    onWillUnmount,
    proxy,
    signal,
    useListener,
    useProps,
} from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { router } from "@web/core/browser/router";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { useSortable } from "@web/core/utils/sortable_owl";
import { uuid } from "@web/core/utils/strings";
import { InlineErrors } from "@tp_web_home/validation/inline_errors";
import { saveError } from "@tp_web_home/validation/validation";
import { TpShareToDiscussDialog } from "../shared/share_to_discuss_dialog";
import { TpScheduleTaskDialog } from "./schedule_task_dialog";
import { TpTodoDetailDrawer } from "./todo_detail_drawer";

const BUCKETS = [
    { key: "today", label: "Hôm nay" },
    { key: "upcoming", label: "Sắp tới" },
    { key: "overdue", label: "Quá hạn" },
    { key: "all", label: "Tất cả" },
    { key: "done", label: "Hoàn thành" },
    { key: "archived", label: "Lưu trữ" },
];

const PAGE_SIZES = [10, 20, 50, 100];

function resolveInitialTaskstate(props) {
    const path = browser.location?.pathname || "";
    if (/\/app\/ca-nhan\/cong-viec\/(tao-moi|new)$/.test(path) || props?.resId === "new") {
        return { taskId: 0, isNew: true };
    }
    const candidates = [
        props?.resId,
        props?.action?.params?.resId,
        props?.action?.context?.active_id,
        router.current?.resId,
    ];
    for (const c of candidates) {
        const n = Number(c);
        if (Number.isInteger(n) && n > 0) {
            return { taskId: n, isNew: false };
        }
    }
    const m = path.match(/\/app\/ca-nhan\/cong-viec\/(\d+)/);
    if (m) {
        return { taskId: Number(m[1]), isNew: false };
    }
    return { taskId: 0, isNew: false };
}

function emptyFilters() {
    return {
        date_from: "",
        date_to: "",
        priority: "",
        tag_id: 0,
        stage_id: 0,
        completion: "",
        assignee_id: 0,
    };
}

export class TpPersonalTodoWorkspace extends Component {
    static template = "tp_personal_tools.TodoWorkspace";
    static components = { InlineErrors, TpTodoDetailDrawer };
    props = useProps();

    boardRef = signal.ref();

    setup() {
        this.orm = useService("orm");
        this.ui = useService("ui");
        this.dialog = useService("dialog");
        this.notification = useService("notification");
        this.BUCKETS = BUCKETS;
        this.PAGE_SIZES = PAGE_SIZES;

        const initialRoute = resolveInitialTaskstate(this.props);
        const defaultView = this.ui.isSmall ? "list" : "board";

        this.searchTimer = null;
        this.loadSeq = 0;
        this.justDraggedUntil = 0;
        this.quickAddTokens = {};

        this.state = proxy({
            loading: true,
            loadError: "",
            bannerError: null,
            bannerAttempt: 0,
            bucket: "all",
            viewMode: defaultView,
            sortBy: "manual",
            searchQuery: "",
            filterPanelOpen: false,
            mobileSidebarOpen: false,
            pendingFilters: emptyFilters(),
            appliedFilters: emptyFilters(),
            colleagues: [],
            // Server data
            summary: {
                today: 0,
                overdue: 0,
                upcoming: 0,
                all_open: 0,
                done: 0,
                done_in_range: 0,
                archived: 0,
            },
            stages: [],
            tags: [],
            tasks: [],
            totalCount: 0,
            page: 1,
            pageSize: 100,
            manualSortEnabled: true,
            // Quick-add & stage management
            quickAddStageId: 0,
            quickAddTitle: "",
            quickAddBusy: false,
            addingStage: false,
            newStageName: "",
            renamingStageId: 0,
            renamingStageName: "",
            openCardMenuId: 0,
            openStageMenuId: 0,
            // Detail drawer
            drawerOpen: Boolean(initialRoute.taskId || initialRoute.isNew),
            drawerTaskId: initialRoute.taskId,
            drawerIsNew: initialRoute.isNew,
            drawerDefaultStageId: 0,
        });

        // Sortable cards across and within personal stages
        useSortable({
            enable: () =>
                !this.ui.isSmall &&
                this.state.viewMode === "board" &&
                this.state.bucket !== "archived" &&
                this.state.manualSortEnabled,
            ref: this.boardRef,
            elements: ".tp-todo-card-draggable",
            handle: ".tp-todo-drag-handle",
            ignore: "button,input,a,select,textarea,.tp-todo-card-menu-wrap,.tp-todo-check-toggle",
            groups: () => ".tp-todo-column",
            connectGroups: () => true,
            cursor: "grabbing",
            placeholderClasses: ["tp-todo-drag-placeholder"],
            onDragStart: () => {
                this.state.openCardMenuId = 0;
                this.state.openStageMenuId = 0;
                this.state.bannerError = null;
            },
            onDragEnd: () => {
                this.justDraggedUntil = Date.now() + 280;
            },
            onDrop: (params) => this.onCardSortDrop(params),
        });

        // Sortable personal stage columns
        useSortable({
            enable: () => !this.ui.isSmall && this.state.viewMode === "board",
            ref: this.boardRef,
            elements: ".tp-todo-column-draggable",
            handle: ".tp-todo-col-drag-handle",
            cursor: "grabbing",
            placeholderClasses: ["tp-todo-col-placeholder"],
            onDragEnd: () => {
                this.justDraggedUntil = Date.now() + 280;
            },
            onDrop: (params) => this.onColumnSortDrop(params),
        });

        useListener(window, "pointerdown", (ev) => {
            if (this.state.openCardMenuId && !ev.target?.closest?.(".tp-todo-card-menu-wrap")) {
                this.state.openCardMenuId = 0;
            }
            if (this.state.openStageMenuId && !ev.target?.closest?.(".tp-todo-stage-menu-wrap")) {
                this.state.openStageMenuId = 0;
            }
        });

        this.onPopState = () => {
            const next = resolveInitialTaskstate({});
            if (next.isNew) {
                this.state.drawerIsNew = true;
                this.state.drawerTaskId = 0;
                this.state.drawerOpen = true;
            } else if (next.taskId) {
                this.state.drawerIsNew = false;
                this.state.drawerTaskId = next.taskId;
                this.state.drawerOpen = true;
            } else if ((browser.location?.pathname || "").startsWith("/app/ca-nhan/cong-viec")) {
                this.state.drawerOpen = false;
                this.state.drawerTaskId = 0;
                this.state.drawerIsNew = false;
            }
        };

        onWillStart(async () => {
            await Promise.all([this.loadWorkspace(), this.loadColleagueOptions()]);
        });

        onMounted(() => {
            document.body.classList.add("o_tp_personal_todo_active");
            window.addEventListener("popstate", this.onPopState);
        });

        onWillUnmount(() => {
            document.body.classList.remove("o_tp_personal_todo_active");
            window.removeEventListener("popstate", this.onPopState);
            if (this.searchTimer) {
                clearTimeout(this.searchTimer);
            }
        });
    }

    syncBrowserUrl(taskId = 0, isNew = false) {
        const base = "/app/ca-nhan/cong-viec";
        const targetPath = isNew ? `${base}/tao-moi` : taskId ? `${base}/${taskId}` : base;
        if (browser.location?.pathname !== targetPath) {
            try {
                browser.history.pushState(browser.history.state, "", targetPath + (browser.location.search || ""));
            } catch {
                // ignore in test mocks
            }
        }
    }

    async loadColleagueOptions() {
        try {
            const list = await this.orm.call("res.users", "tp_search_colleagues", ["", 40, true]);
            this.state.colleagues = Array.isArray(list) ? list : [];
        } catch {
            this.state.colleagues = [];
        }
    }

    async loadWorkspace() {
        const seq = ++this.loadSeq;
        this.state.loading = true;
        this.state.loadError = "";
        const f = this.state.appliedFilters;
        try {
            const res = await this.orm.call("project.task", "tp_get_personal_workspace", [
                {
                    bucket: this.state.bucket,
                    view_mode: this.state.viewMode,
                    sort_by: this.state.sortBy,
                    q: this.state.searchQuery,
                    date_from: f.date_from,
                    date_to: f.date_to,
                    priority: f.priority,
                    tag_ids: f.tag_id ? [Number(f.tag_id)] : [],
                    stage_id: Number(f.stage_id) || 0,
                    completion: f.completion,
                    assignee_id: Number(f.assignee_id) || 0,
                    page: this.state.page,
                    page_size: this.state.pageSize,
                },
            ]);
            if (seq !== this.loadSeq) {
                return;
            }
            this.state.summary = res.summary || this.state.summary;
            this.state.stages = res.stages || [];
            this.state.tags = res.tags || [];
            this.state.tasks = res.tasks || [];
            this.state.totalCount = res.total_count || 0;
            this.state.page = res.page || 1;
            this.state.pageSize = res.page_size || 100;
            this.state.manualSortEnabled = Boolean(res.manual_sort_enabled);
        } catch (err) {
            if (seq !== this.loadSeq) {
                return;
            }
            const parsed = saveError(err, { verb: "tải danh sách việc cá nhân", write: false });
            this.state.loadError = parsed?.message || "Không tải được danh sách công việc.";
        } finally {
            if (seq === this.loadSeq) {
                this.state.loading = false;
            }
        }
    }

    bucketCount(key) {
        const s = this.state.summary;
        if (key === "today") return s.today;
        if (key === "upcoming") return s.upcoming;
        if (key === "overdue") return s.overdue;
        if (key === "all") return s.all_open;
        if (key === "done") return s.done;
        if (key === "archived") return s.archived;
        return 0;
    }

    selectBucket(key) {
        this.state.bucket = key;
        this.state.page = 1;
        this.state.mobileSidebarOpen = false;
        this.loadWorkspace();
    }

    setViewMode(mode) {
        this.state.viewMode = mode;
        this.state.page = 1;
        this.loadWorkspace();
    }

    onSortChange(ev) {
        this.state.sortBy = ev.target.value || "manual";
        this.state.page = 1;
        this.loadWorkspace();
    }

    switchToManualSort() {
        this.state.sortBy = "manual";
        this.state.page = 1;
        this.loadWorkspace();
    }

    onSearchInput(ev) {
        this.state.searchQuery = ev.target.value || "";
        this.state.page = 1;
        if (this.searchTimer) {
            clearTimeout(this.searchTimer);
        }
        this.searchTimer = setTimeout(() => {
            this.loadWorkspace();
        }, 220);
    }

    clearSearch() {
        this.state.searchQuery = "";
        this.state.page = 1;
        this.loadWorkspace();
    }

    get activeFilterChips() {
        const f = this.state.appliedFilters;
        const chips = [];
        if (this.state.searchQuery.trim()) {
            chips.push({ key: "q", label: `Từ khóa: "${this.state.searchQuery.trim()}"` });
        }
        if (f.date_from || f.date_to) {
            chips.push({
                key: "date",
                label: `Hạn: ${f.date_from || "…"} → ${f.date_to || "…"}`,
            });
        }
        if (f.priority !== "") {
            const pMap = { "0": "Bình thường", "1": "Trung bình", "2": "Cao", "3": "Khẩn cấp" };
            chips.push({ key: "priority", label: `Ưu tiên: ${pMap[f.priority] || f.priority}` });
        }
        if (Number(f.tag_id)) {
            const tg = this.state.tags.find((t) => t.id === Number(f.tag_id));
            chips.push({ key: "tag_id", label: `Nhãn: ${tg ? tg.name : f.tag_id}` });
        }
        if (Number(f.stage_id)) {
            const st = this.state.stages.find((s) => s.id === Number(f.stage_id));
            chips.push({ key: "stage_id", label: `Giai đoạn: ${st ? st.name : f.stage_id}` });
        }
        if (f.completion) {
            chips.push({
                key: "completion",
                label: `Trạng thái: ${f.completion === "done" ? "Đã hoàn thành" : "Chưa hoàn thành"}`,
            });
        }
        if (Number(f.assignee_id)) {
            const col = this.state.colleagues.find((c) => c.user_id === Number(f.assignee_id));
            chips.push({ key: "assignee_id", label: `Người liên quan: ${col ? col.name : f.assignee_id}` });
        }
        return chips;
    }

    applyFilters() {
        const p = this.state.pendingFilters;
        if (p.date_from && p.date_to && p.date_from > p.date_to) {
            this.state.bannerAttempt++;
            this.state.bannerError = {
                kind: "validation",
                title: "Khoảng ngày chưa hợp lệ",
                message: "Ngày bắt đầu không được lớn hơn ngày kết thúc.",
            };
            return;
        }
        this.state.bannerError = null;
        this.state.appliedFilters = { ...p };
        this.state.page = 1;
        this.state.filterPanelOpen = false;
        this.loadWorkspace();
    }

    resetAllFilters() {
        this.state.pendingFilters = emptyFilters();
        this.state.appliedFilters = emptyFilters();
        this.state.searchQuery = "";
        this.state.page = 1;
        this.state.bannerError = null;
        this.loadWorkspace();
    }

    removeFilterChip(key) {
        if (key === "q") {
            this.state.searchQuery = "";
        } else if (key === "date") {
            this.state.pendingFilters.date_from = "";
            this.state.pendingFilters.date_to = "";
            this.state.appliedFilters.date_from = "";
            this.state.appliedFilters.date_to = "";
        } else if (key in this.state.appliedFilters) {
            const resetVal = typeof emptyFilters()[key] === "number" ? 0 : "";
            this.state.pendingFilters[key] = resetVal;
            this.state.appliedFilters[key] = resetVal;
        }
        this.state.page = 1;
        this.loadWorkspace();
    }

    tasksForStage(stageId) {
        return this.state.tasks.filter((t) => t.stage_id === stageId);
    }

    get totalPages() {
        return Math.max(1, Math.ceil((this.state.totalCount || 0) / (this.state.pageSize || 100)));
    }

    changePage(nextPage) {
        const clamped = Math.max(1, Math.min(nextPage, this.totalPages));
        if (clamped !== this.state.page) {
            this.state.page = clamped;
            this.loadWorkspace();
        }
    }

    changePageSize(ev) {
        this.state.pageSize = Number(ev.target.value) || 100;
        this.state.page = 1;
        this.loadWorkspace();
    }

    // --- Quick Add & Drawer ---
    openCreateDrawer(stageId = 0) {
        this.state.drawerDefaultStageId = stageId || (this.state.stages[0]?.id ?? 0);
        this.state.drawerTaskId = 0;
        this.state.drawerIsNew = true;
        this.state.drawerOpen = true;
        this.syncBrowserUrl(0, true);
    }

    openTaskDetail(task, ev) {
        if (Date.now() < this.justDraggedUntil) {
            return;
        }
        if (ev?.target?.closest?.("button,input,a,.tp-todo-card-menu-wrap,.tp-todo-check-toggle")) {
            return;
        }
        this.state.drawerTaskId = task.id;
        this.state.drawerIsNew = false;
        this.state.drawerOpen = true;
        this.syncBrowserUrl(task.id, false);
    }

    closeDrawer(resetUrl = false) {
        this.state.drawerOpen = false;
        this.state.drawerTaskId = 0;
        this.state.drawerIsNew = false;
        if (resetUrl) {
            this.syncBrowserUrl(0, false);
        }
    }

    startQuickAdd(stageId) {
        this.state.quickAddStageId = stageId;
        this.state.quickAddTitle = "";
        this.quickAddTokens[stageId] = uuid();
    }

    async submitQuickAdd(stageId) {
        const title = this.state.quickAddTitle.trim();
        if (!title || this.state.quickAddBusy) {
            return;
        }
        const token = this.quickAddTokens[stageId] || uuid();
        this.quickAddTokens[stageId] = token;
        this.state.quickAddBusy = true;
        this.state.bannerError = null;
        try {
            await this.orm.call("project.task", "tp_create_personal_task", [
                { name: title, stage_id: stageId },
                token,
            ]);
            this.quickAddTokens[stageId] = uuid();
            this.state.quickAddTitle = "";
            await this.loadWorkspace();
        } catch (err) {
            this.state.bannerAttempt++;
            this.state.bannerError = saveError(err, { verb: "thêm nhanh công việc" });
        } finally {
            this.state.quickAddBusy = false;
        }
    }

    onQuickAddKeydown(stageId, ev) {
        if (ev.isComposing || ev.keyCode === 229) {
            return;
        }
        if (ev.key === "Enter") {
            ev.preventDefault();
            this.submitQuickAdd(stageId);
        } else if (ev.key === "Escape") {
            this.state.quickAddStageId = 0;
            this.state.quickAddTitle = "";
        }
    }

    async toggleTaskDone(task, ev) {
        ev?.stopPropagation?.();
        const prev = task.is_done;
        task.is_done = !prev;
        this.state.bannerError = null;
        try {
            await this.orm.call("project.task", "tp_toggle_personal_task_done", [
                task.id,
                task.is_done,
            ]);
            await this.loadWorkspace();
        } catch (err) {
            task.is_done = prev;
            this.state.bannerAttempt++;
            this.state.bannerError = saveError(err, {
                verb: "cập nhật trạng thái hoàn thành",
                note: "Trạng thái trước đó đã được khôi phục.",
            });
        }
    }

    // --- Drag & Drop + Accessible/Mobile Alternatives ---
    async onCardSortDrop({ element, group, previous, next }) {
        const taskId = Number(element?.dataset?.taskId || 0);
        const targetStageId = Number(group?.dataset?.stageId || 0);
        if (!taskId || !targetStageId) {
            return;
        }
        const prevId = Number(previous?.dataset?.taskId || 0);
        const nextId = Number(next?.dataset?.taskId || 0);

        const snapshot = this.state.tasks.map((t) => ({ ...t }));
        const movedTask = this.state.tasks.find((t) => t.id === taskId);
        if (!movedTask) {
            return;
        }

        // Compute new ordered IDs in target stage
        const targetList = this.state.tasks
            .filter((t) => t.stage_id === targetStageId && t.id !== taskId)
            .map((t) => t.id);

        let insertIdx = targetList.length;
        if (prevId && targetList.includes(prevId)) {
            insertIdx = targetList.indexOf(prevId) + 1;
        } else if (nextId && targetList.includes(nextId)) {
            insertIdx = targetList.indexOf(nextId);
        } else if (!prevId) {
            insertIdx = 0;
        }
        targetList.splice(insertIdx, 0, taskId);

        // Optimistic update in UI, rolled back if backend fails
        const targetStage = this.state.stages.find((s) => s.id === targetStageId);
        movedTask.stage_id = targetStageId;
        if (targetStage) {
            movedTask.stage_name = targetStage.name;
        }
        const orderMap = new Map(targetList.map((id, idx) => [id, (idx + 1) * 10]));
        for (const t of this.state.tasks) {
            if (orderMap.has(t.id)) {
                t.personal_sequence = orderMap.get(t.id);
            }
        }
        const stageOrder = new Map(this.state.stages.map((s, i) => [s.id, i]));
        this.state.tasks.sort(
            (a, b) =>
                (stageOrder.get(a.stage_id) ?? 999) - (stageOrder.get(b.stage_id) ?? 999) ||
                a.personal_sequence - b.personal_sequence ||
                b.id - a.id
        );

        try {
            await this.orm.call("project.task", "tp_move_personal_task", [
                taskId,
                targetStageId,
                targetList,
            ]);
        } catch (err) {
            this.state.tasks = snapshot;
            this.state.bannerAttempt++;
            this.state.bannerError = saveError(err, {
                verb: "sắp xếp công việc",
                note: "Đã khôi phục vị trí cũ trong bảng việc.",
            });
        }
    }

    async moveTaskByMenu(task, targetStageId, position = "keep") {
        this.state.openCardMenuId = 0;
        const snapshot = this.state.tasks.map((t) => ({ ...t }));
        const stageTasks = this.state.tasks
            .filter((t) => t.stage_id === targetStageId)
            .map((t) => t.id);

        let ordered = stageTasks.filter((id) => id !== task.id);
        const curIdx = stageTasks.indexOf(task.id);

        if (position === "top") {
            ordered.unshift(task.id);
        } else if (position === "bottom") {
            ordered.push(task.id);
        } else if (position === "up" && curIdx > 0) {
            ordered.splice(curIdx - 1, 0, task.id);
        } else if (position === "down" && curIdx >= 0 && curIdx < stageTasks.length - 1) {
            ordered.splice(curIdx + 1, 0, task.id);
        } else {
            ordered.unshift(task.id);
        }

        try {
            await this.orm.call("project.task", "tp_move_personal_task", [
                task.id,
                targetStageId,
                ordered,
            ]);
            await this.loadWorkspace();
        } catch (err) {
            this.state.tasks = snapshot;
            this.state.bannerAttempt++;
            this.state.bannerError = saveError(err, {
                verb: "di chuyển công việc",
                note: "Đã khôi phục vị trí cũ.",
            });
        }
    }

    async onColumnSortDrop({ element, previous, next }) {
        const stageId = Number(element?.dataset?.stageId || 0);
        if (!stageId) {
            return;
        }
        const prevId = Number(previous?.dataset?.stageId || 0);
        const nextId = Number(next?.dataset?.stageId || 0);
        const snapshot = this.state.stages.map((s) => ({ ...s }));
        const ids = this.state.stages.filter((s) => s.id !== stageId).map((s) => s.id);
        let idx = ids.length;
        if (prevId && ids.includes(prevId)) {
            idx = ids.indexOf(prevId) + 1;
        } else if (nextId && ids.includes(nextId)) {
            idx = ids.indexOf(nextId);
        } else if (!prevId) {
            idx = 0;
        }
        ids.splice(idx, 0, stageId);
        const map = new Map(this.state.stages.map((s) => [s.id, s]));
        this.state.stages = ids.map((id) => map.get(id)).filter(Boolean);

        try {
            await this.orm.call("project.task", "tp_manage_personal_stage", [
                "reorder",
                0,
                { stage_ids: ids },
            ]);
        } catch (err) {
            this.state.stages = snapshot;
            this.state.bannerAttempt++;
            this.state.bannerError = saveError(err, {
                verb: "sắp xếp giai đoạn",
                note: "Thứ tự cột đã khôi phục như cũ.",
            });
        }
    }

    // --- Stage Actions ---
    async createNewStage() {
        const clean = this.state.newStageName.trim();
        if (!clean) {
            return;
        }
        try {
            await this.orm.call("project.task", "tp_manage_personal_stage", [
                "create",
                0,
                { name: clean },
            ]);
            this.state.newStageName = "";
            this.state.addingStage = false;
            await this.loadWorkspace();
        } catch (err) {
            this.state.bannerAttempt++;
            this.state.bannerError = saveError(err, { verb: "tạo giai đoạn mới" });
        }
    }

    startRenameStage(stage) {
        this.state.openStageMenuId = 0;
        this.state.renamingStageId = stage.id;
        this.state.renamingStageName = stage.name;
    }

    async saveRenameStage(stageId) {
        const clean = this.state.renamingStageName.trim();
        if (!clean) {
            this.state.renamingStageId = 0;
            return;
        }
        try {
            await this.orm.call("project.task", "tp_manage_personal_stage", [
                "rename",
                stageId,
                { name: clean },
            ]);
            this.state.renamingStageId = 0;
            await this.loadWorkspace();
        } catch (err) {
            this.state.bannerAttempt++;
            this.state.bannerError = saveError(err, { verb: "đổi tên giai đoạn" });
        }
    }

    async toggleFoldStage(stage) {
        this.state.openStageMenuId = 0;
        try {
            await this.orm.call("project.task", "tp_manage_personal_stage", [
                "toggle_fold",
                stage.id,
                {},
            ]);
            await this.loadWorkspace();
        } catch (err) {
            this.state.bannerAttempt++;
            this.state.bannerError = saveError(err, { verb: "thu gọn giai đoạn" });
        }
    }

    confirmDeleteStage(stage) {
        this.state.openStageMenuId = 0;
        this.dialog.add(ConfirmationDialog, {
            title: "Xóa giai đoạn cá nhân",
            body: `Xóa giai đoạn "${stage.name}"? Các công việc đang nằm trong cột này sẽ tự động chuyển sang giai đoạn liền kề của bạn.`,
            confirmLabel: "Xóa giai đoạn",
            cancelLabel: "Hủy",
            confirm: async () => {
                try {
                    await this.orm.call("project.task", "tp_manage_personal_stage", [
                        "delete",
                        stage.id,
                        {},
                    ]);
                    await this.loadWorkspace();
                } catch (err) {
                    this.state.bannerAttempt++;
                    this.state.bannerError = saveError(err, { verb: "xóa giai đoạn" });
                }
            },
        });
    }

    // --- Card Shortcut Menus ---
    scheduleTaskFromCard(task) {
        this.state.openCardMenuId = 0;
        this.dialog.add(TpScheduleTaskDialog, {
            task,
            onScheduled: () => this.loadWorkspace(),
        });
    }

    shareTaskFromCard(task) {
        this.state.openCardMenuId = 0;
        this.dialog.add(TpShareToDiscussDialog, {
            targetModel: "project.task",
            targetId: task.id,
            targetTitle: task.name,
        });
    }

    async archiveTaskFromCard(task) {
        this.state.openCardMenuId = 0;
        try {
            await this.orm.call("project.task", "tp_archive_personal_task", [
                task.id,
                !task.active,
            ]);
            this.notification.add(
                task.active ? "Đã chuyển công việc vào Lưu trữ." : "Đã khôi phục công việc.",
                { type: "success" }
            );
            await this.loadWorkspace();
        } catch (err) {
            this.state.bannerAttempt++;
            this.state.bannerError = saveError(err, { verb: "lưu trữ công việc" });
        }
    }

    onNewStageKeydown(ev) {
        if (!ev.isComposing && ev.key === "Enter") {
            ev.preventDefault();
            this.createNewStage();
        }
    }

    toggleSidebarStageFilter(stageId) {
        const next = Number(this.state.appliedFilters.stage_id) === stageId ? 0 : stageId;
        this.state.pendingFilters.stage_id = next;
        this.state.appliedFilters.stage_id = next;
        this.state.page = 1;
        this.state.mobileSidebarOpen = false;
        this.loadWorkspace();
    }

    onRenameStageKeydown(stageId, ev) {
        if (ev.key === "Enter") {
            this.saveRenameStage(stageId);
        } else if (ev.key === "Escape") {
            this.state.renamingStageId = 0;
        }
    }

    onCardKeydown(task, ev) {
        if (ev.key === "Enter" && ev.target === ev.currentTarget) {
            this.openTaskDetail(task, ev);
        }
    }

    toggleCardMenu(taskId, ev) {
        ev.stopPropagation();
        this.state.openCardMenuId = this.state.openCardMenuId === taskId ? 0 : taskId;
    }

    openDetailFromMenu(task) {
        this.state.openCardMenuId = 0;
        this.openTaskDetail(task);
    }

    onDrawerTagCreated(tg) {
        if (!this.state.tags.some((t) => t.id === tg.id)) {
            this.state.tags = [...this.state.tags, tg];
        }
    }
}

registry.category("actions").add("tp_personal_tools.todo_workspace", TpPersonalTodoWorkspace);
