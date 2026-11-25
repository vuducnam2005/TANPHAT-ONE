import { Component, onWillStart, proxy, useProps } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";
import { uuid } from "@web/core/utils/strings";
import { InlineErrors } from "@tp_web_home/validation/inline_errors";
import { saveError } from "@tp_web_home/validation/validation";
import { TpColleaguePicker } from "../shared/colleague_picker";

/**
 * Preview & Confirm dialog to convert a Discuss `mail.message` into a `project.task`
 * (`tp_source_kind = 'chat'`, `tp_source_message_id = message.id`).
 * Enforces backend read ACL check and `operation_token` idempotency.
 */
export class TpMessageToTaskDialog extends Component {
    static template = "tp_personal_tools.MessageToTaskDialog";
    static components = { Dialog, InlineErrors, TpColleaguePicker };
    props = useProps();
    operationToken = uuid();

    setup() {
        this.orm = useService("orm");
        this.ui = useService("ui");
        this.notification = useService("notification");

        this.state = proxy({
            loading: true,
            loadError: null,
            preview: null,
            name: "",
            deliverable: "",
            priority: "1",
            deadlineIso: "",
            assignees: [],
            noteText: "",
            notifyChannel: true,
            busy: false,
            attempt: 0,
            serverError: null,
        });

        onWillStart(async () => {
            await this.loadPreview();
        });
    }

    get dialogSize() {
        return this.ui.isSmall ? "fullscreen" : "md";
    }

    async loadPreview() {
        this.state.loading = true;
        this.state.loadError = null;
        try {
            const info = await this.orm.call(
                "discuss.channel",
                "tp_preview_message_for_task",
                [Number(this.props.messageId || 0)]
            );
            this.state.preview = info;
            this.state.name = info?.suggested_title || "";
            this.state.noteText = info?.body_text || "";
            this.state.assignees = Array.isArray(info?.default_assignees)
                ? info.default_assignees
                : [];
        } catch (err) {
            this.state.loadError = saveError(err, {
                verb: "đọc tin nhắn nguồn",
                write: false,
            });
        } finally {
            this.state.loading = false;
        }
    }

    get fieldErrors() {
        if (!this.state.attempt) {
            return [];
        }
        const errs = [];
        if (!this.state.name.trim()) {
            errs.push({
                id: "tp_msg_task_name",
                label: "Tiêu đề công việc",
                message: "Vui lòng nhập tiêu đề công việc.",
            });
        }
        if (!this.state.assignees.length) {
            errs.push({
                id: "tp_msg_task_assignees",
                label: "Người nhận việc",
                message: "Vui lòng chọn ít nhất một người thực hiện.",
            });
        }
        return errs;
    }

    hasFieldError(id) {
        return this.fieldErrors.some((e) => e.id === id);
    }

    async onSubmit() {
        if (this.state.busy || this.state.loading || this.state.loadError) {
            return;
        }
        this.state.serverError = null;
        this.state.attempt++;
        if (this.fieldErrors.length) {
            return;
        }
        this.state.busy = true;
        try {
            const created = await this.orm.call(
                "discuss.channel",
                "tp_create_task_from_message",
                [
                    Number(this.props.messageId),
                    {
                        name: this.state.name.trim(),
                        deliverable: this.state.deliverable.trim(),
                        priority: this.state.priority,
                        deadline_iso: this.state.deadlineIso || false,
                        user_ids: this.state.assignees.map((a) => a.user_id),
                        note_text: this.state.noteText,
                        notify_channel: Boolean(this.state.notifyChannel),
                    },
                    this.operationToken,
                ]
            );
            this.notification.add(
                `Đã tạo công việc "${created.name}" từ tin nhắn trao đổi.`,
                { type: "success" }
            );
            this.props.onCreated?.(created);
            this.props.close();
        } catch (err) {
            this.state.serverError = saveError(err, { verb: "tạo công việc từ tin nhắn" });
        } finally {
            this.state.busy = false;
        }
    }
}
