import {
    Component,
    onMounted,
    onWillUnmount,
    proxy,
    signal,
    useListener,
    useProps,
} from "@odoo/owl";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { useService } from "@web/core/utils/hooks";
import { user } from "@web/core/user";
import { uuid } from "@web/core/utils/strings";
import { TpDateTime24Field } from "@tp_web_home/inputs/time24";
import { InlineErrors } from "@tp_web_home/validation/inline_errors";
import { saveError } from "@tp_web_home/validation/validation";
import { TpColleaguePicker } from "../shared/colleague_picker";
import { TpShareToDiscussDialog } from "../shared/share_to_discuss_dialog";
import { TpScheduleTaskDialog } from "./schedule_task_dialog";

function readFileAsBase64(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => {
            const raw = String(reader.result || "");
            const idx = raw.indexOf(",");
            resolve(idx >= 0 ? raw.slice(idx + 1) : raw);
        };
        reader.onerror = () => reject(new Error("Không đọc được tệp đính kèm."));
        reader.readAsDataURL(file);
    });
}

function formatBytes(bytes) {
    const n = Number(bytes || 0);
    if (n < 1024) {
        return `${n} B`;
    }
    if (n < 1024 * 1024) {
        return `${(n / 1024).toFixed(1)} KB`;
    }
    return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}

export class TpTodoDetailDrawer extends Component {
    static template = "tp_personal_tools.TodoDetailDrawer";
    static components = { InlineErrors, TpColleaguePicker, TpDateTime24Field };
    props = useProps();

    drawerRef = signal.ref();
    fileInputRef = signal.ref();

    setup() {
        this.orm = useService("orm");
        this.dialog = useService("dialog");
        this.notification = useService("notification");
        this.actionService = useService("action");
        this.selfUserId = user.userId;
        this.createToken = uuid();
        this.commentToken = uuid();
        this.previousFocusEl = document.activeElement;

        this.state = proxy({
            loading: !this.props.isNew,
            loadError: null,
            expanded: false,
            dirty: false,
            confirmClosePrompt: false,
            saving: false,
            uploading: false,
            postingComment: false,
            attempt: 0,
            serverError: null,
            // Form fields
            id: this.props.taskId || 0,
            active: true,
            canWrite: true,
            canUploadEvidence: true,
            canReportDone: false,
            canVerify: false,
            requiresVerification: false,
            sourceKind: "self",
            sourceLabel: "Tự tạo",
            project: null,
            assigner: null,
            verifier: null,
            sourceMessageInfo: null,
            execReportState: "in_progress",
            execReportLabel: "Đang thực hiện",
            reportedResult: "",
            reportingBusy: false,
            name: "",
            deliverable: "",
            isDone: false,
            priority: "0",
            stageId: this.props.defaultStageId || 0,
            deadlineIso: "",
            assignees: [],
            tagIds: [],
            newTagName: "",
            noteText: "",
            checklist: [],
            newCheckText: "",
            attachments: [],
            linkedEvents: [],
            messages: [],
            commentDraft: "",
            stages: this.props.stages || [],
            allTags: this.props.allTags || [],
        });

        useListener(window, "keydown", (ev) => {
            if (ev.key === "Escape") {
                ev.stopPropagation();
                this.requestClose();
            }
        });

        onMounted(async () => {
            if (this.props.isNew) {
                if (!this.state.stageId && this.state.stages.length) {
                    this.state.stageId = this.state.stages[0].id;
                }
                const titleInput = this.drawerRef()?.querySelector("#tp_todo_drawer_name");
                titleInput?.focus();
            } else if (this.props.taskId) {
                await this.loadDetail(this.props.taskId);
            }
        });

        onWillUnmount(() => {
            if (this.previousFocusEl && typeof this.previousFocusEl.focus === "function") {
                try {
                    this.previousFocusEl.focus({ preventScroll: true });
                } catch {
                    // element detached
                }
            }
        });
    }

    formatBytes(size) {
        return formatBytes(size);
    }

    async loadDetail(taskId) {
        this.state.loading = true;
        this.state.loadError = null;
        this.state.serverError = null;
        try {
            const detail = await this.orm.call("project.task", "tp_get_personal_task_detail", [
                Number(taskId),
            ]);
            this.applyDetailData(detail);
        } catch (err) {
            this.state.loadError = saveError(err, { verb: "mở công việc", write: false });
        } finally {
            this.state.loading = false;
        }
    }

    applyDetailData(detail) {
        this.state.id = detail.id;
        this.state.active = Boolean(detail.active);
        this.state.canWrite = Boolean(detail.can_write);
        this.state.canUploadEvidence = Boolean(
            detail.can_upload_evidence ?? detail.can_write
        );
        this.state.canReportDone = Boolean(detail.can_report_done);
        this.state.canVerify = Boolean(detail.can_verify);
        this.state.requiresVerification = Boolean(detail.requires_verification);
        this.state.sourceKind = detail.source_kind || "self";
        this.state.sourceLabel = detail.source_label || "Tự tạo";
        this.state.project = detail.project || null;
        this.state.assigner = detail.assigner || null;
        this.state.verifier = detail.verifier || null;
        this.state.sourceMessageInfo = detail.source_message_info || null;
        this.state.execReportState = detail.exec_report_state || "in_progress";
        this.state.execReportLabel = detail.exec_report_label || "Đang thực hiện";
        this.state.reportedResult = detail.reported_result || "";
        this.state.name = detail.name || "";
        this.state.deliverable = detail.deliverable || "";
        this.state.isDone = Boolean(detail.is_done);
        this.state.priority = detail.priority || "0";
        this.state.stageId = detail.stage_id || (detail.stages?.[0]?.id ?? 0);
        this.state.deadlineIso = detail.deadline?.iso_local || "";
        this.state.assignees = Array.isArray(detail.assignees) ? detail.assignees : [];
        this.state.tagIds = (detail.tags || []).map((t) => t.id);
        this.state.noteText = detail.note_text || "";
        this.state.checklist = (detail.checklist || []).map((c, idx) => ({
            key: `${idx}-${c.text}`,
            text: c.text,
            checked: Boolean(c.checked),
        }));
        this.state.attachments = detail.attachments || [];
        this.state.linkedEvents = detail.linked_events || [];
        this.state.messages = detail.messages || [];
        if (detail.stages?.length) {
            this.state.stages = detail.stages;
        }
        this.state.dirty = false;
        this.state.confirmClosePrompt = false;
    }

    markDirty() {
        this.state.dirty = true;
        this.state.confirmClosePrompt = false;
    }

    get fieldErrors() {
        if (!this.state.attempt) {
            return [];
        }
        const errs = [];
        if (!this.state.name.trim()) {
            errs.push({
                id: "tp_todo_drawer_name",
                label: "Tiêu đề công việc",
                message: "Vui lòng nhập tiêu đề công việc.",
            });
        }
        return errs;
    }

    isTagSelected(tagId) {
        return this.state.tagIds.includes(tagId);
    }

    toggleTag(tagId) {
        if (!this.state.canWrite) {
            return;
        }
        if (this.state.tagIds.includes(tagId)) {
            this.state.tagIds = this.state.tagIds.filter((id) => id !== tagId);
        } else {
            this.state.tagIds = [...this.state.tagIds, tagId];
        }
        this.markDirty();
    }

    async createQuickTag() {
        const clean = this.state.newTagName.trim();
        if (!clean || !this.state.canWrite) {
            return;
        }
        try {
            const tag = await this.orm.call("project.task", "tp_create_personal_tag", [
                clean,
                (this.state.allTags.length % 10) + 1,
            ]);
            if (!this.state.allTags.some((t) => t.id === tag.id)) {
                this.state.allTags = [...this.state.allTags, tag];
            }
            if (!this.state.tagIds.includes(tag.id)) {
                this.state.tagIds = [...this.state.tagIds, tag.id];
            }
            this.state.newTagName = "";
            this.markDirty();
            this.props.onTagCreated?.(tag);
        } catch (err) {
            this.state.serverError = saveError(err, { verb: "tạo nhãn" });
        }
    }

    onAssigneesChange(list) {
        this.state.assignees = list;
        this.markDirty();
    }

    addChecklistItem() {
        const text = this.state.newCheckText.trim();
        if (!text || !this.state.canWrite) {
            return;
        }
        this.state.checklist = [
            ...this.state.checklist,
            { key: uuid(), text, checked: false },
        ];
        this.state.newCheckText = "";
        this.markDirty();
    }

    onChecklistKeydown(ev) {
        if (ev.isComposing || ev.keyCode === 229) {
            return;
        }
        if (ev.key === "Enter") {
            ev.preventDefault();
            this.addChecklistItem();
        }
    }

    toggleChecklistItem(item) {
        if (!this.state.canWrite) {
            return;
        }
        item.checked = !item.checked;
        this.markDirty();
    }

    removeChecklistItem(key) {
        if (!this.state.canWrite) {
            return;
        }
        this.state.checklist = this.state.checklist.filter((c) => c.key !== key);
        this.markDirty();
    }

    async onSave() {
        if (this.state.saving || !this.state.canWrite) {
            return false;
        }
        this.state.serverError = null;
        this.state.attempt++;
        if (this.fieldErrors.length) {
            return false;
        }
        // Flush any typed checklist item before saving
        if (this.state.newCheckText.trim()) {
            this.addChecklistItem();
        }
        this.state.saving = true;
        try {
            const payload = {
                name: this.state.name.trim(),
                deliverable: this.state.deliverable.trim(),
                reported_result: this.state.reportedResult.trim(),
                is_done: this.state.isDone,
                priority: this.state.priority,
                stage_id: Number(this.state.stageId) || false,
                deadline_iso: this.state.deadlineIso || false,
                user_ids: this.state.assignees.map((a) => a.user_id),
                tag_ids: this.state.tagIds,
                note_text: this.state.noteText,
                checklist: this.state.checklist.map((c) => ({
                    text: c.text,
                    checked: Boolean(c.checked),
                })),
            };
            if (this.props.isNew && !this.state.id) {
                const created = await this.orm.call("project.task", "tp_create_personal_task", [
                    payload,
                    this.createToken,
                ]);
                this.notification.add("Đã thêm công việc cá nhân.", { type: "success" });
                this.state.dirty = false;
                this.props.onSaved?.(created, { created: true });
                this.props.onClose?.(true);
                return true;
            }
            const updatedDetail = await this.orm.call("project.task", "tp_save_personal_task", [
                Number(this.state.id),
                payload,
            ]);
            this.applyDetailData(updatedDetail);
            this.notification.add("Đã lưu thay đổi công việc.", { type: "success" });
            this.props.onSaved?.(updatedDetail, { created: false });
            return true;
        } catch (err) {
            this.state.serverError = saveError(err, { verb: "lưu công việc" });
            return false;
        } finally {
            this.state.saving = false;
        }
    }

    async onReportOrVerify(action) {
        if (!this.state.id || this.state.reportingBusy) {
            return;
        }
        this.state.reportingBusy = true;
        this.state.serverError = null;
        try {
            const detail = await this.orm.call(
                "project.task",
                "tp_report_or_verify_task",
                [Number(this.state.id), action, this.state.reportedResult.trim(), uuid()]
            );
            this.applyDetailData(detail);
            const msgMap = {
                report_done: "Đã báo hoàn thành công việc (chờ xác nhận kết quả).",
                verify: "Đã xác nhận kết quả hoàn thành công việc.",
                reopen: "Đã mở lại trạng thái thực hiện công việc.",
            };
            this.notification.add(msgMap[action] || "Đã cập nhật kết quả.", { type: "success" });
            this.props.onSaved?.(detail, { created: false });
        } catch (err) {
            this.state.serverError = saveError(err, { verb: "cập nhật kết quả thực hiện" });
        } finally {
            this.state.reportingBusy = false;
        }
    }

    async onStageChangeForReadonlyTask(ev) {
        const nextStageId = Number(ev.target.value || 0);
        this.state.stageId = nextStageId;
        if (!this.state.canWrite && this.state.id && nextStageId) {
            try {
                await this.orm.call("project.task", "tp_move_personal_task", [
                    Number(this.state.id),
                    nextStageId,
                    [Number(this.state.id)],
                ]);
                this.notification.add("Đã chuyển giai đoạn cá nhân.", { type: "success" });
                this.props.onMutated?.();
            } catch (err) {
                this.state.serverError = saveError(err, { verb: "chuyển giai đoạn cá nhân" });
            }
        } else {
            this.markDirty();
        }
    }

    async onFileSelected(ev) {
        const files = Array.from(ev.target.files || []);
        if (!files.length || !this.state.id || this.state.uploading) {
            return;
        }
        this.state.uploading = true;
        this.state.serverError = null;
        try {
            for (const file of files) {
                const b64 = await readFileAsBase64(file);
                const att = await this.orm.call(
                    "project.task",
                    "tp_upload_personal_task_attachment",
                    [Number(this.state.id), file.name, b64]
                );
                this.state.attachments = [att, ...this.state.attachments];
            }
            this.props.onMutated?.();
        } catch (err) {
            this.state.serverError = saveError(err, { verb: "tải tệp đính kèm" });
        } finally {
            this.state.uploading = false;
            if (this.fileInputRef()) {
                this.fileInputRef().value = "";
            }
        }
    }

    async removeAttachment(att) {
        if (!this.state.id || this.state.saving) {
            return;
        }
        try {
            await this.orm.call("project.task", "tp_delete_personal_task_attachment", [
                Number(this.state.id),
                Number(att.id),
            ]);
            this.state.attachments = this.state.attachments.filter((a) => a.id !== att.id);
            this.props.onMutated?.();
        } catch (err) {
            this.state.serverError = saveError(err, { verb: "xóa tệp đính kèm" });
        }
    }

    async postComment() {
        const body = this.state.commentDraft.trim();
        if (!body || !this.state.id || this.state.postingComment) {
            return;
        }
        this.state.postingComment = true;
        this.state.serverError = null;
        try {
            const detail = await this.orm.call("project.task", "tp_post_personal_task_comment", [
                Number(this.state.id),
                body,
                this.commentToken,
            ]);
            this.commentToken = uuid();
            this.state.commentDraft = "";
            this.state.messages = detail.messages || [];
            this.props.onMutated?.();
        } catch (err) {
            this.state.serverError = saveError(err, { verb: "gửi trao đổi" });
        } finally {
            this.state.postingComment = false;
        }
    }

    openScheduleDialog() {
        if (!this.state.id) {
            return;
        }
        this.dialog.add(TpScheduleTaskDialog, {
            task: {
                id: this.state.id,
                name: this.state.name,
                deadline: { iso_local: this.state.deadlineIso },
                note_preview: this.state.noteText.slice(0, 200),
            },
            onScheduled: () => {
                this.loadDetail(this.state.id);
                this.props.onMutated?.();
            },
        });
    }

    openShareDialog() {
        if (!this.state.id) {
            return;
        }
        this.dialog.add(TpShareToDiscussDialog, {
            targetModel: "project.task",
            targetId: this.state.id,
            targetTitle: this.state.name,
        });
    }

    async toggleArchive() {
        if (!this.state.id || this.state.saving) {
            return;
        }
        this.state.saving = true;
        try {
            const nextActive = !this.state.active;
            await this.orm.call("project.task", "tp_archive_personal_task", [
                Number(this.state.id),
                nextActive,
            ]);
            this.state.active = nextActive;
            this.notification.add(
                nextActive ? "Đã khôi phục công việc." : "Đã chuyển công việc vào Lưu trữ.",
                { type: "success" }
            );
            this.props.onMutated?.();
            if (!nextActive) {
                this.props.onClose?.(true);
            }
        } catch (err) {
            this.state.serverError = saveError(err, {
                verb: this.state.active ? "lưu trữ" : "khôi phục",
            });
        } finally {
            this.state.saving = false;
        }
    }

    confirmDelete() {
        if (!this.state.id) {
            return;
        }
        this.dialog.add(ConfirmationDialog, {
            title: "Xóa công việc cá nhân",
            body: `Bạn có chắc chắn muốn xóa vĩnh viễn công việc "${this.state.name}" không? Bạn cũng có thể chọn Lưu trữ nếu chỉ muốn ẩn khỏi danh sách đang làm.`,
            confirmLabel: "Xóa công việc",
            cancelLabel: "Hủy",
            confirm: async () => {
                try {
                    await this.orm.call("project.task", "tp_delete_personal_task", [
                        Number(this.state.id),
                    ]);
                    this.notification.add("Đã xóa công việc.", { type: "success" });
                    this.props.onMutated?.();
                    this.props.onClose?.(true);
                } catch (err) {
                    this.state.serverError = saveError(err, { verb: "xóa công việc" });
                }
            },
        });
    }

    requestClose() {
        if (this.state.dirty && !this.state.confirmClosePrompt) {
            this.state.confirmClosePrompt = true;
            return;
        }
        this.props.onClose?.(true);
    }

    discardAndClose() {
        this.state.dirty = false;
        this.state.confirmClosePrompt = false;
        this.props.onClose?.(true);
    }

    onNewTagKeydown(ev) {
        if (!ev.isComposing && ev.key === "Enter") {
            ev.preventDefault();
            this.createQuickTag();
        }
    }

    onCommentKeydown(ev) {
        if (!ev.isComposing && ev.key === "Enter") {
            ev.preventDefault();
            this.postComment();
        }
    }
}
