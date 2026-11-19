import { Component, proxy, useProps } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";
import { rpcError } from "../common";

/**
 * Multi-file Excel uploader (HR-ATTENDANCE-MATRIX-003, DEC-058):
 * - Supports drag-and-drop or picking one or many .xlsx files at once.
 * - Each file is validated and read independently (one invalid file never loses valid files).
 * - Each source stays persistent; valid open days update from the newest file, with old hours retained in history.
 * - Immediately opens "Bảng dữ liệu theo file" in the main content area when >= 1 file succeeds.
 */
const MAX_BYTES = 15 * 1024 * 1024;
const MAX_FILES = 20;

function readFileAsBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(String(reader.result || "").split(",", 2)[1] || "");
        reader.onerror = () => reject(reader.error || new Error("Read failed"));
        reader.readAsDataURL(file);
    });
}

export class AttendanceUploadDialog extends Component {
    static template = "tp_hr_attendance.UploadDialog";
    static components = { Dialog };
    props = useProps();

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        this.state = proxy({
            step: "pick",
            drag: false,
            error: "",
            items: [],
            createdIds: [],
        });
    }

    get busy() {
        return this.state.step === "reading";
    }
    get okItems() {
        return this.state.items.filter((item) => item.ok);
    }
    get failedItems() {
        return this.state.items.filter((item) => !item.ok && item.done);
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
            this.readFiles(Array.from(ev.dataTransfer?.files || []));
        }
    }
    onPick(ev) {
        const files = Array.from(ev.target.files || []);
        ev.target.value = "";
        this.readFiles(files);
    }

    async readFiles(files) {
        if (!files.length || this.busy) {
            return;
        }
        this.state.error = "";
        if (files.length > MAX_FILES) {
            this.state.error = `Mỗi lần chọn tối đa ${MAX_FILES} tệp Excel.`;
            return;
        }
        this.state.step = "reading";
        const items = files.map((file, idx) => ({
            key: `${idx}-${file.name}`,
            file_name: file.name,
            size: file.size,
            ok: false,
            done: false,
            error: "",
            batch_code: "",
            period_label: "",
            people_count: 0,
            id: 0,
        }));
        this.state.items = items;
        this.state.createdIds = [];

        const payloadFiles = [];
        const payloadMap = [];
        for (let idx = 0; idx < files.length; idx++) {
            const file = files[idx];
            const item = items[idx];
            if (!/\.xlsx$/i.test(file.name)) {
                Object.assign(item, { done: true, ok: false, error: "Chỉ nhận tệp định dạng .xlsx xuất từ máy chấm công." });
                continue;
            }
            if (file.size > MAX_BYTES) {
                Object.assign(item, { done: true, ok: false, error: "Tệp vượt quá giới hạn 15 MB." });
                continue;
            }
            if (!file.size) {
                Object.assign(item, { done: true, ok: false, error: "Tệp rỗng (0 byte)." });
                continue;
            }
            try {
                const b64 = await readFileAsBase64(file);
                payloadMap.push(idx);
                payloadFiles.push({ file_name: file.name, data: b64 });
            } catch {
                Object.assign(item, { done: true, ok: false, error: "Không đọc được tệp từ trình duyệt." });
            }
        }

        if (payloadFiles.length) {
            try {
                const res = await this.orm.call("tp.hr.attendance.batch", "tp_upload_files", [{ files: payloadFiles }]);
                for (let rIdx = 0; rIdx < (res.results || []).length; rIdx++) {
                    const serverItem = res.results[rIdx];
                    const targetIdx = payloadMap[rIdx];
                    if (targetIdx !== undefined && items[targetIdx]) {
                        Object.assign(items[targetIdx], serverItem, { done: true });
                    }
                }
                this.state.createdIds = res.created_ids || [];
            } catch (error) {
                const msg = rpcError(error, "Không tải được tệp lên máy chủ. Vui lòng thử lại.");
                for (const targetIdx of payloadMap) {
                    if (items[targetIdx] && !items[targetIdx].done) {
                        Object.assign(items[targetIdx], { done: true, ok: false, error: msg });
                    }
                }
                this.state.error = msg;
            }
        }

        const createdIds = items.filter((it) => it.ok && it.id).map((it) => it.id);
        this.state.createdIds = createdIds;
        const failed = items.filter((it) => !it.ok);

        if (createdIds.length) {
            this.notification.add(
                createdIds.length === 1
                    ? "Đã lưu tệp và cập nhật bảng công theo nguồn mới nhất."
                    : `Đã lưu ${createdIds.length} tệp và cập nhật bảng công theo thứ tự tải lên.`,
                { type: "success" }
            );
            // Show the last uploaded source, including any rows that still need review.
            const uploadNotice = failed.length
                ? failed.map((f) => `${f.file_name}: ${f.error}`).join(" | ")
                : "";
            this.props.close();
            if (this.props.onUploaded) {
                this.props.onUploaded({ createdIds, items: [...items], uploadNotice });
            } else {
                await this.action.doAction({
                    type: "ir.actions.client",
                    tag: "tp_hr_attendance.file_matrix",
                    name: "Bảng dữ liệu theo file",
                    params: {
                        batch_id: createdIds[createdIds.length - 1],
                        uploaded_ids: createdIds,
                        upload_notice: uploadNotice,
                    },
                });
            }
            return;
        }
        this.state.step = "result";
    }

    pickAgain() {
        Object.assign(this.state, { step: "pick", error: "", items: [], createdIds: [] });
    }

    close() {
        if (!this.busy) {
            this.props.close();
        }
    }
}

/**
 * Open the multi-file Excel upload dialog.
 * ``onUploaded({ createdIds, items, uploadNotice })`` is called when the caller is already on File Matrix;
 * otherwise the dialog navigates straight to ``tp_hr_attendance.file_matrix`` in full width.
 */
export function openAttendanceUpload(env, { onUploaded, onApplied, onOpenPeriod } = {}) {
    env.services.dialog.add(AttendanceUploadDialog, { onUploaded, onApplied, onOpenPeriod });
}
