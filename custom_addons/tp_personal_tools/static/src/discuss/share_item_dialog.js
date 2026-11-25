import { Component, onWillStart, proxy, useProps } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";
import { uuid } from "@web/core/utils/strings";
import { InlineErrors } from "@tp_web_home/validation/inline_errors";
import { saveError } from "@tp_web_home/validation/validation";

/**
 * Dialog opened from the Discuss Composer to share a safe internal link to a
 * Personal Task (`project.task`) or Calendar Event (`calendar.event`).
 * Recipients still pass full backend ACL when clicking the link.
 */
export class TpShareItemDialog extends Component {
    static template = "tp_personal_tools.ShareItemDialog";
    static components = { Dialog, InlineErrors };
    props = useProps();
    operationToken = uuid();

    setup() {
        this.orm = useService("orm");
        this.ui = useService("ui");
        this.notification = useService("notification");
        this.searchTimer = null;

        this.state = proxy({
            kind: "todo", // 'todo' | 'calendar'
            query: "",
            loading: true,
            items: [],
            selectedItem: null,
            note: "",
            busy: false,
            attempt: 0,
            serverError: null,
        });

        onWillStart(async () => {
            await this.fetchItems();
        });
    }

    async fetchItems() {
        this.state.loading = true;
        try {
            const list = await this.orm.call(
                "discuss.channel",
                "tp_list_shareable_personal_items",
                [this.state.kind, this.state.query, 25]
            );
            this.state.items = Array.isArray(list) ? list : [];
            if (
                this.state.selectedItem &&
                !this.state.items.some((i) => i.id === this.state.selectedItem.id)
            ) {
                this.state.selectedItem = null;
            }
        } catch {
            this.state.items = [];
        } finally {
            this.state.loading = false;
        }
    }

    async switchKind(kind) {
        this.state.kind = kind;
        this.state.selectedItem = null;
        this.state.attempt = 0;
        this.operationToken = uuid();
        await this.fetchItems();
    }

    onQueryInput(ev) {
        this.state.query = ev.target.value || "";
        if (this.searchTimer) {
            clearTimeout(this.searchTimer);
        }
        this.searchTimer = setTimeout(() => this.fetchItems(), 200);
    }

    get fieldErrors() {
        if (!this.state.attempt) {
            return [];
        }
        if (!this.state.selectedItem) {
            return [
                {
                    id: "tp_share_item_pick",
                    label: "Mục cần chia sẻ",
                    message: "Vui lòng chọn một công việc hoặc lịch hẹn để gửi vào hội thoại.",
                },
            ];
        }
        return [];
    }

    async onSendShare() {
        if (this.state.busy) {
            return;
        }
        this.state.serverError = null;
        this.state.attempt++;
        if (this.fieldErrors.length) {
            return;
        }
        this.state.busy = true;
        try {
            await this.orm.call("discuss.channel", "tp_share_record_to_channel", [
                Number(this.props.channelId),
                this.state.selectedItem.model,
                Number(this.state.selectedItem.id),
                this.state.note,
                this.operationToken,
            ]);
            this.notification.add("Đã gửi liên kết vào cuộc hội thoại.", { type: "success" });
            this.props.onPosted?.();
            this.props.close();
        } catch (err) {
            this.state.serverError = saveError(err, { verb: "chia sẻ liên kết" });
        } finally {
            this.state.busy = false;
        }
    }
}
