import { Component, onWillStart, proxy, useProps } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";
import { uuid } from "@web/core/utils/strings";
import { InlineErrors } from "@tp_web_home/validation/inline_errors";
import { saveError } from "@tp_web_home/validation/validation";

/**
 * Explicit dialog to share a Personal Task or Calendar Event link into Trao đổi.
 * Never auto-sends on task/event save; recipients pass backend ACL when opening the link.
 */
export class TpShareToDiscussDialog extends Component {
    static template = "tp_personal_tools.ShareToDiscussDialog";
    static components = { Dialog, InlineErrors };
    props = useProps();
    operationToken = uuid();

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.actionService = useService("action");
        this.state = proxy({
            channels: [],
            loading: true,
            query: "",
            selectedChannelId: 0,
            note: "",
            busy: false,
            attempt: 0,
            serverError: null,
        });

        onWillStart(async () => {
            await this.loadChannels("");
        });
    }

    async loadChannels(query) {
        this.state.loading = true;
        try {
            const list = await this.orm.call("discuss.channel", "tp_list_share_targets", [
                query || "",
                30,
            ]);
            this.state.channels = Array.isArray(list) ? list : [];
            if (!this.state.selectedChannelId && this.state.channels.length) {
                this.state.selectedChannelId = this.state.channels[0].id;
            }
        } catch (err) {
            this.state.serverError = saveError(err, {
                verb: "tải danh sách hội thoại",
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
        if (!this.state.selectedChannelId) {
            errs.push({
                id: "tp_share_channel_select",
                label: "Hội thoại nhận",
                message: "Vui lòng chọn người hoặc nhóm để gửi liên kết.",
            });
        }
        return errs;
    }

    async onSubmit() {
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
            const res = await this.orm.call("discuss.channel", "tp_share_record_to_channel", [
                Number(this.state.selectedChannelId),
                this.props.targetModel,
                Number(this.props.targetId),
                this.state.note,
                this.operationToken,
            ]);
            this.notification.add("Đã gửi liên kết vào hội thoại.", { type: "success" });
            this.props.onShared?.(res);
            this.props.close();
        } catch (err) {
            this.state.serverError = saveError(err, { verb: "gửi liên kết" });
        } finally {
            this.state.busy = false;
        }
    }
}
