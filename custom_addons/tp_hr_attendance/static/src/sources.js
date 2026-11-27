import { Component, onWillStart, onWillUnmount, proxy, useProps } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { InlineErrors } from "@tp_web_home/validation/inline_errors";
import { saveError } from "@tp_web_home/validation/validation";
import { downloadBase64 } from "./common";
import { useAttendanceLive } from "./live";

/**
 * "Nguồn dữ liệu chấm công" (HR/admin area, ENTI-LIVE-001, ENTI-ATTENDANCE-002). ENTI is the only live source:
 * connector health, last successful sync, mapping progress with the unmapped people and their reasons, and a
 * manual sync. Excel file import is closed; earlier import batches stay readable as history.
 */
export class AttendanceSources extends Component {
    static template = "tp_hr_attendance.Sources";
    static components = { InlineErrors };
    props = useProps();

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = proxy({
            loading: true, refreshing: false, syncing: false,
            serverError: null, attempt: 0, notice: "", data: null,
            exporting: false, exportErrors: [], exportServerError: null, exportAttempt: 0,
            mode: "month", date: "", from: "", to: "", department: "",
            imageSyncing: false, imageRetrying: false, imageFiltering: false,
            imageState: "", imageDepartment: "", imageSearch: "",
        });
        this.request = 0;
        // Sync health and the last update time follow the server sync without F5 (bus + visible-tab fallback poll).
        this.live = useAttendanceLive({
            refresh: () => {
                if (this.state.loading || this.state.refreshing || this.state.syncing) {
                    return false;
                }
                return this.load({ silent: true });
            },
        });
        onWillStart(() => this.load());
        onWillUnmount(() => { this.request++; });
    }

    get data() {
        return this.state.data;
    }
    get enti() {
        return this.data?.api?.enti || {};
    }
    get unmapped() {
        return (this.enti.unmapped_people || []).slice(0, 5);
    }
    get imageSync() {
        return this.data?.image_sync || {
            state: "idle",
            state_label: "Chưa đồng bộ",
            last_sync_at: "",
            message: "",
            prefer_manual_image: false,
            total_employees: 0,
            synced_count: 0,
            no_image_count: 0,
            failed_count: 0,
            unmapped_count: 0,
            rows: [],
        };
    }
    get imageHealth() {
        const st = this.imageSync.state;
        if (st === "success") {
            return { tone: "good", text: this.imageSync.state_label || "Đã đồng bộ" };
        }
        if (st === "partial") {
            return { tone: "warn", text: this.imageSync.state_label || "Hoàn tất (Có ảnh lỗi)" };
        }
        if (st === "error") {
            return { tone: "danger", text: this.imageSync.state_label || "Lỗi đồng bộ" };
        }
        return { tone: "neutral", text: this.imageSync.state_label || "Chưa đồng bộ" };
    }
    get health() {
        const source = this.enti;
        if (!source.configured) {
            return { tone: "neutral", text: "Chưa cấu hình" };
        }
        if (this.data?.health === "error") {
            return { tone: "danger", text: "Cần kiểm tra đồng bộ" };
        }
        if (this.data?.health === "stale") {
            return { tone: "warn", text: source.last_success_at ? "Đồng bộ đang chậm" : "Chờ đồng bộ thành công" };
        }
        if (!source.live || source.state === "paused" || source.cron_active === false) {
            return { tone: "neutral", text: "Đồng bộ tự động đang tắt" };
        }
        return source.last_success_at
            ? { tone: "good", text: "Đồng bộ tự động đang bật" }
            : { tone: "warn", text: "Chờ đồng bộ thành công" };
    }

    async load({ silent = false } = {}) {
        const request = ++this.request;
        this.state[silent ? "refreshing" : "loading"] = true;
        try {
            const orm = silent ? this.orm.silent : this.orm;
            const params = {
                image_state: this.state.imageState,
                image_department_id: this.state.imageDepartment,
                image_search: this.state.imageSearch,
            };
            const data = await orm.call("tp.hr.attendance.source", "tp_sources_overview", [params]);
            if (request === this.request) {
                if (!this.state.data && data.today) {
                    Object.assign(this.state, { date: data.today, from: data.today, to: data.today });
                }
                this.state.data = data;
                if (!silent) {
                    this.state.serverError = null;
                }
                this.live.loaded();
            }
        } catch (error) {
            if (request === this.request && !silent) {
                this.state.serverError = saveError(error, { verb: "tải nguồn dữ liệu chấm công" });
                this.state.attempt++;
            }
        } finally {
            if (request === this.request) {
                this.state.loading = false;
                this.state.refreshing = false;
                this.live.flush();
            }
        }
    }

    /** Manual sync (HR/admin). The result stays on the screen; a failure never removes stored attendance. */
    async syncEntiNow() {
        if (this.state.syncing) {
            return;
        }
        Object.assign(this.state, { syncing: true, serverError: null, notice: "" });
        try {
            const res = await this.orm.call("tp.hr.attendance.source", "action_sync_enti_quick", []);
            if (res && res.success === false) {
                const msg = res.skipped
                    ? res.message
                    : (res.message || "Đồng bộ chưa thành công. Xem Nhật ký đồng bộ để kiểm tra.");
                this.state.serverError = { title: "Chưa đồng bộ được", message: msg };
                this.state.attempt++;
            } else {
                const dur = res?.duration_seconds != null ? ` (${res.duration_seconds}s)` : "";
                this.state.notice = `Đã đồng bộ ${res?.employees || 0} nhân viên, cập nhật ${res?.days_applied || 0} bản ghi công${dur}.`;
            }
        } catch (error) {
            this.state.serverError = saveError(error, { verb: "đồng bộ dữ liệu chấm công" });
            this.state.attempt++;
        } finally {
            this.state.syncing = false;
        }
        await this.load({ silent: true });
    }

    async syncEntiImages({ onlyFailed = false } = {}) {
        if (this.state.imageSyncing || this.state.imageRetrying) {
            return;
        }
        const flag = onlyFailed ? "imageRetrying" : "imageSyncing";
        Object.assign(this.state, { [flag]: true, serverError: null, notice: "" });
        try {
            const method = onlyFailed
                ? "action_retry_failed_enti_images_quick"
                : "action_sync_enti_images_quick";
            const res = await this.orm.call("tp.hr.attendance.source", method, []);
            if (res && res.success === false) {
                this.state.serverError = {
                    title: "Chưa đồng bộ được ảnh hồ sơ",
                    message: res.message || "Đồng bộ ảnh hồ sơ chưa thành công.",
                };
                this.state.attempt++;
            } else {
                this.state.notice = res?.message || "Đã đồng bộ ảnh hồ sơ nhân viên từ ENTI.";
            }
        } catch (error) {
            this.state.serverError = saveError(error, { verb: "đồng bộ ảnh hồ sơ" });
            this.state.attempt++;
        } finally {
            this.state[flag] = false;
        }
        await this.load({ silent: true });
    }

    async togglePreferManualImage(ev) {
        const enabled = Boolean(ev.target.checked);
        try {
            const res = await this.orm.call("tp.hr.attendance.source", "action_toggle_prefer_manual_image", [enabled]);
            if (this.state.data?.image_sync) {
                this.state.data.image_sync.prefer_manual_image = Boolean(res?.prefer_manual_image);
            }
        } catch (error) {
            this.state.serverError = saveError(error, { verb: "cập nhật cấu hình ưu tiên ảnh thủ công" });
            this.state.attempt++;
        }
    }

    async applyImageFilters() {
        this.state.imageFiltering = true;
        try {
            const imgData = await this.orm.call("tp.hr.attendance.source", "tp_enti_image_logs", [{
                image_state: this.state.imageState,
                image_department_id: this.state.imageDepartment,
                image_search: this.state.imageSearch,
            }]);
            if (this.state.data) {
                this.state.data.image_sync = imgData;
            }
        } catch (error) {
            this.state.serverError = saveError(error, { verb: "lọc nhật ký đồng bộ ảnh" });
            this.state.attempt++;
        } finally {
            this.state.imageFiltering = false;
        }
    }

    openImageRecord(row) {
        if (!row?.id) {
            return;
        }
        return this.action.doAction({
            type: "ir.actions.act_window",
            name: "Xem trước & Đối chiếu ảnh hồ sơ ENTI",
            res_model: "tp.hr.attendance.enti.employee.image",
            res_id: row.id,
            views: [[false, "form"]],
            target: "new",
        });
    }

    async applyRowImage(row) {
        if (!row?.id || row.mapping_state !== "mapped" || !row.has_enti_image) {
            return;
        }
        try {
            await this.orm.call("tp.hr.attendance.enti.employee.image", "action_apply_to_employee", [[row.id]]);
            this.state.notice = `Đã cập nhật ảnh hồ sơ cho nhân viên ${row.employee_name || row.ten_nv}.`;
            await this.load({ silent: true });
        } catch (error) {
            this.state.serverError = saveError(error, { verb: "cập nhật ảnh hồ sơ" });
            this.state.attempt++;
        }
    }

    async exportSheet() {
        const state = this.state;
        if (!this.data?.can_export || state.exporting) {
            return;
        }
        const { mode, date, from, to } = state;
        if (mode === "range" ? (!from || !to || from > to) : !date) {
            state.exportErrors = [{ label: "Kỳ xuất", message: "Vui lòng chọn kỳ xuất hợp lệ." }];
            state.exportServerError = null;
            state.exportAttempt++;
            return;
        }
        Object.assign(state, { exporting: true, exportErrors: [], exportServerError: null });
        try {
            const file = await this.orm.call("tp.hr.attendance.day", "tp_export_sheet", [{
                mode, date, from, to, department_id: Number(state.department) || 0,
            }]);
            downloadBase64(file);
        } catch (error) {
            state.exportServerError = saveError(error, { verb: "xuất bảng công" });
            state.exportAttempt++;
        } finally {
            state.exporting = false;
        }
    }
    open(xmlid, filters = {}) {
        if (xmlid === "tp_hr_attendance.action_enti_mapping" && Object.keys(filters).length) {
            filters = { search_default_state_suggested: 0, search_default_state_unmapped: 0, ...filters };
        }
        return this.action.doAction(xmlid, { additionalContext: filters });
    }
}

registry.category("actions").add("tp_hr_attendance.sources", AttendanceSources);
