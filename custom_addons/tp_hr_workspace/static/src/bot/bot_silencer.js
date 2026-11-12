import { Thread } from "@mail/core/common/thread";
import { SuggestionService } from "@mail/core/common/suggestion_service";
import { MessagingMenu } from "@mail/core/public_web/messaging_menu/messaging_menu_model";
import { Store } from "@mail/core/common/store_service";
import { patch } from "@web/core/utils/patch";

patch(Thread.prototype, {
    get orderedMessages() {
        const messages = super.orderedMessages;
        if (!messages || !messages.length) {
            return messages;
        }
        const odoobotId = this.store.odoobot?.id;
        return messages.filter((msg) => {
            if (msg.author?.isBot || (odoobotId && (msg.author_id?.id === odoobotId || msg.author?.id === odoobotId))) {
                return false;
            }
            if (msg.authorName && msg.authorName.toLowerCase().includes("odoobot")) {
                return false;
            }
            return true;
        });
    },
});

patch(SuggestionService.prototype, {
    isPartnerSuggestionValid(partner, { composerType, thread } = {}) {
        if (partner && (partner.eq(this.store.odoobot) || partner.isBot)) {
            return false;
        }
        return super.isPartnerSuggestionValid(partner, { composerType, thread });
    },
});

patch(MessagingMenu.prototype, {
    get odooBotNotificationsTab() {
        return null;
    },
});

patch(Store.prototype, {
    onStarted() {
        super.onStarted(...arguments);
        this.isNotificationPermissionDismissed = true;
    },
});
