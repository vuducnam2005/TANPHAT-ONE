import { Component, proxy, useProps } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";
import { daysBetween, formatDate, rpcError } from "../common";

/**
 * "Nhập Excel máy chấm công" (HR-ATTENDANCE-SIMPLE-002): drop or pick the machine .xlsx, the server reads
 * it at once into a preview batch (nothing written yet), then "Nhập dữ liệu" applies the valid lines and
 * the exact-period late totals. Same batch / mapping / dedupe as the HR form flow; no second importer.
 */
const MAX_BYTES = 15 * 1024 * 1024;
const LINE_TILES = [
    { key: "valid", label: "Dòng mới hợp lệ", tone: "ok" },
    { key: "duplicate", label: "Trùng đã có", tone: "muted" },
    { key: "missing", label: "Thiếu giờ vào/ra", tone: "warn" },
    { key: "unmapped", label: "Chưa khớp nhân viên", tone: "warn" },
    { key: "name_conflict", label: "Tên khác hồ sơ", tone: "warn" },
    { key: "conflict", label: "Xung đột", tone: "danger" },
    { key: "review", label: "Cần kiểm tra", tone: "warn" },
    { key: "locked", label: "Kỳ đã chốt", tone: "muted" },
];
const LATE_TILES = [
    { key: "valid", label: "Hợp lệ" },
    { key: "duplicate", label: "Trùng đã có" },
    { key: "missing", label: "Chưa có số liệu" },
    { key: "conflict", label: "Khác tổng đã nhập" },
    { key: "review", label: "Cần kiểm tra" },
    { key: "unmapped", label: "Chưa khớp" },
    { key: "name_conflict", label: "Tên khác hồ sơ" },
    { key: "locked", label: "Kỳ đã chốt" },
];

export class AttendanceUploadDialog extends Component {
    static template = "tp_hr_attendance.UploadDialog";
    static components = { Dialog };
    props = useProps();

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.state = proxy({ step: "pick", drag: false, error: "", data: null, fileName: "" });
        this.formatDate = formatDate;
    }

    get data() {
        return this.state.data;
    }
    get busy() {
        return ["reading", "applying"].includes(this.state.step);
    }
    get days() {
        const period = this.data?.period;
        return period?.from && period?.to ? daysBetween(period.from, period.to) + 1 : 0;
    }
    get lineTiles() {
        const counts = this.data?.counts || {};
        return LINE_TILES.filter((tile) => ["valid", "duplicate", "missing"].includes(tile.key) || counts[tile.key])
            .map((tile) => ({ ...tile, value: counts[tile.key] || 0 }));
    }
    get lateTiles() {
        const late = this.data?.late || {};
        const applied = this.data?.state === "applied";
        return LATE_TILES.map((tile) => ({ ...tile, value: (tile.key === "valid" && applied ? late.applied : late[tile.key]) || 0 }))
            .filter((tile) => tile.value || tile.key === "valid");
    }
    get writable() {
        const counts = this.data?.counts || {};
        const late = this.data?.late || {};
        return (counts.valid || 0) + (counts.missing || 0) + (counts.review || 0) + (counts.conflict || 0) + (late.valid || 0);
    }
    get lateNotes() {
        return (this.data?.sheets || []).filter((sheet) => sheet.late_state !== "ok" && sheet.late_message);
    }
    get sheetErrors() {
        return (this.data?.sheets || []).filter((sheet) => sheet.errors.length);
    }

    onDragOver(ev) {
        ev.preventDefault();
        if (!this.busy) {
            this.state.drag = true;
        }
    }
    onDragLeave() {
        this.state.drag = false;
    }
    onDrop(ev) {
        ev.preventDefault();
        this.state.drag = false;
        if (!this.busy) {
            this.readFile(ev.dataTransfer?.files?.[0]);
        }
    }
    onPick(ev) {
        const file = ev.target.files?.[0];
        ev.target.value = ""; // Picking the same file again after a cancel still triggers a read.
        this.readFile(file);
    }

    async readFile(file) {
        if (!file) {
            return;
        }
        this.state.error = "";
        if (!/\.xlsx$/i.test(file.name)) {
            this.state.error = "Chỉ nhận tệp .xlsx xuất từ máy chấm công.";
            return;
        }
        if (file.size > MAX_BYTES) {
            this.state.error = "Tệp quá lớn (tối đa 15 MB).";
            return;
        }
        if (this.data?.can_apply) {
            await this.cancelBatch(); // Picking another file discards the unapplied preview.
        }
        this.state.step = "reading";
        this.state.fileName = file.name;
        this.state.data = null;
        try {
            const content = await new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.onload = () => resolve(String(reader.result).split(",", 2)[1] || "");
                reader.onerror = () => reject(reader.error);
                reader.readAsDataURL(file);
            });
            this.state.data = await this.orm.call("tp.hr.attendance.batch", "tp_upload_preview", [{ file_name: file.name, data: content }]);
            this.state.step = "preview";
            this.track();
        } catch (error) {
            this.state.step = "pick";
            this.state.error = rpcError(error, "Không đọc được tệp. Kiểm tra đúng tệp xuất từ máy chấm công rồi thử lại.");
        }
    }

    async apply() {
        if (!this.data?.can_apply || this.busy) {
            return;
        }
        this.state.step = "applying";
        this.state.error = "";
        try {
            this.state.data = await this.orm.call("tp.hr.attendance.batch", "tp_upload_apply", [this.data.batch_id]);
            this.state.step = "done";
            this.track();
            this.notification.add("Đã nhập dữ liệu chấm công từ tệp Excel máy.", { type: "success" });
            this.props.onApplied?.(this.data);
        } catch (error) {
            this.state.step = "preview";
            this.state.error = rpcError(error, "Chưa nhập được dữ liệu. Vui lòng thử lại; dữ liệu cũ không thay đổi.");
        }
    }

    /** Lets the dialog's own close (×, Esc) cancel an unapplied preview through ``onClose``. */
    track() {
        if (this.props.tracker) {
            this.props.tracker.pending = this.data?.can_apply ? this.data.batch_id : 0;
        }
    }
    async cancelBatch() {
        const batchId = this.data?.batch_id;
        if (!batchId || !this.data.can_apply) {
            return;
        }
        if (this.props.tracker) {
            this.props.tracker.pending = 0;
        }
        try {
            await this.orm.call("tp.hr.attendance.batch", "tp_upload_cancel", [batchId]);
        } catch {
            // A preview that cannot be cancelled stays a draft batch for HR; it never writes data.
        }
    }
    async another() {
        await this.cancelBatch();
        Object.assign(this.state, { step: "pick", data: null, error: "", fileName: "" });
    }
    async close() {
        if (this.busy) {
            return;
        }
        await this.cancelBatch();
        this.props.close();
    }
    openPeriod() {
        const period = this.data?.period;
        this.props.close();
        if (period?.from && period?.to) {
            this.props.onOpenPeriod?.(period);
        }
    }
}

/** Open the upload dialog; ``onApplied(payload)`` reloads the caller, ``onOpenPeriod(period)`` shows the file period. */
export function openAttendanceUpload(env, { onApplied, onOpenPeriod } = {}) {
    const tracker = { pending: 0 };
    env.services.dialog.add(AttendanceUploadDialog, { onApplied, onOpenPeriod, tracker }, {
        onClose: () => {
            if (tracker.pending) {
                env.services.orm.call("tp.hr.attendance.batch", "tp_upload_cancel", [tracker.pending]).catch(() => {});
                tracker.pending = 0;
            }
        },
    });
}
