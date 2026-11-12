import { describe, expect, test } from "@odoo/hoot";
import { Attachment } from "@mail/core/common/attachment_model";
import { Message } from "@mail/core/common/message_model";
import "@tp_kd_workspace/head_chatter";

describe("tp_kd_workspace HEAD native chatter", () => {
    test("HEAD keeps files and comments readable without mutation controls", () => {
        const thread = { tpKdHeadContentCommand: true };
        const attachmentDelete = Object.getOwnPropertyDescriptor(Attachment.prototype, "isDeletable").get;
        const messageEdit = Object.getOwnPropertyDescriptor(Message.prototype, "editable").get;
        const messageDelete = Object.getOwnPropertyDescriptor(Message.prototype, "deletable").get;
        expect(attachmentDelete.call({ thread })).toBe(false);
        expect(attachmentDelete.call({ message: { thread } })).toBe(false);
        expect(messageEdit.call({ thread })).toBe(false);
        expect(messageDelete.call({ thread })).toBe(false);
    });

    test("other staff retain native file and comment controls", () => {
        const thread = { tpKdHeadContentCommand: false };
        const attachmentDelete = Object.getOwnPropertyDescriptor(Attachment.prototype, "isDeletable").get;
        const messageEdit = Object.getOwnPropertyDescriptor(Message.prototype, "editable").get;
        const messageDelete = Object.getOwnPropertyDescriptor(Message.prototype, "deletable").get;
        const message = { thread, isEmpty: false, allowsEdition: true, poll: false, message_type: "comment" };
        expect(attachmentDelete.call({ thread })).toBe(true);
        expect(messageEdit.call(message)).toBe(true);
        expect(messageDelete.call(message)).toBe(true);
    });
});
