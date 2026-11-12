import { Attachment } from "@mail/core/common/attachment_model";
import { Message } from "@mail/core/common/message_model";
import { Thread } from "@mail/core/common/thread_model";
import { fields } from "@mail/model/export";
import { patch } from "@web/core/utils/patch";

patch(Thread.prototype, {
    setup() {
        super.setup(...arguments);
        this.tpKdHeadContentCommand = fields.Attr(false);
    },
});

patch(Attachment.prototype, {
    get isDeletable() {
        const thread = this.thread || this.message?.thread;
        return !thread?.tpKdHeadContentCommand && super.isDeletable;
    },
});

patch(Message.prototype, {
    get editable() {
        return !this.thread?.tpKdHeadContentCommand && super.editable;
    },
    get deletable() {
        return !this.thread?.tpKdHeadContentCommand && super.deletable;
    },
});
