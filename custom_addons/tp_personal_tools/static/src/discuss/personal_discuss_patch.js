import { onMounted, onWillUnmount, proxy, useListener } from "@odoo/owl";
import { ACTION_TAGS } from "@mail/core/common/action";
import { Composer } from "@mail/core/common/composer";
import { registerComposerAction } from "@mail/core/common/composer_actions";
import { Message } from "@mail/core/common/message";
import { registerMessageAction } from "@mail/core/common/message_actions";
import { registerThreadAction } from "@mail/core/common/thread_actions";
import { Thread } from "@mail/core/common/thread_model";
import { DiscussContent } from "@mail/core/public_web/discuss_content";
import { Discuss } from "@mail/core/public_web/discuss_app/discuss_app";
import { MessagingMenu } from "@mail/core/public_web/messaging_menu/messaging_menu";
import { MENU_TABS } from "@mail/core/public_web/messaging_menu/messaging_menu_model";
import { DiscussChannel } from "@mail/discuss/core/common/discuss_channel_model";
import { browser } from "@web/core/browser/browser";
import { router } from "@web/core/browser/router";
import { useService } from "@web/core/utils/hooks";
import { patch } from "@web/core/utils/patch";
import { TpCreateChatDialog } from "./create_chat_dialog";
import { TpMessageToTaskDialog } from "./message_to_task_dialog";
import { TpShareItemDialog } from "./share_item_dialog";

const TP_DIRECT_FILTER_KEY = "tp_direct_only";

// 0. Message action: Convert Discuss message -> Task with preview & confirmation
registerMessageAction("tp-create-task-from-message", {
    condition: ({ message, owner }) =>
        Boolean(
            owner.env.inDiscussApp &&
                message?.id &&
                !message.isEmpty &&
                message.thread?.model === "discuss.channel"
        ),
    icon: "check_circle",
    name: "Tạo công việc",
    onSelected: ({ message, store }) => {
        if (!message?.id) {
            return;
        }
        store.env.services.dialog.add(TpMessageToTaskDialog, {
            messageId: message.id,
        });
    },
    sequence: 42,
});

// 1. Composer action: Share permitted Personal Task or Calendar Event into conversation
registerComposerAction("tp-share-personal-item", {
    condition: ({ composer, owner }) =>
        Boolean(
            owner.env.inDiscussApp &&
                composer.targetThread?.channel &&
                !composer.message
        ),
    icon: "link",
    name: "Chia sẻ việc cá nhân / lịch hẹn",
    onSelected: ({ composer, store }) => {
        const chan = composer.targetThread?.channel;
        if (!chan?.id) {
            return;
        }
        store.env.services.dialog.add(TpShareItemDialog, {
            channelId: chan.id,
        });
    },
    sequenceQuick: 18,
});

// 2. Explicit, accurately named Hide (DM) vs Leave (Group/Channel) actions in Discuss header
registerThreadAction("tp-hide-dm-from-list", {
    condition: ({ channel, owner, store }) =>
        Boolean(
            owner.isDiscussContent &&
                store.self_user?.share === false &&
                channel?.channel_type === "chat" &&
                channel?.canHide &&
                !channel?.isSelfInCall
        ),
    icon: "visibility_off",
    name: "Ẩn khỏi danh sách",
    onSelected: ({ channel }) => channel.unpinChannel(),
    sequence: 85,
    sequenceGroup: 40,
});

registerThreadAction("tp-leave-group-or-channel", {
    condition: ({ channel, owner }) =>
        Boolean(
            owner.isDiscussContent &&
                channel?.isAllowedToLeave &&
                ["group", "channel"].includes(channel?.channel_type)
        ),
    icon: "logout",
    name: ({ channel }) => (channel?.channel_type === "group" ? "Rời nhóm trao đổi" : "Rời kênh"),
    onSelected: ({ channel }) => channel.leaveChannel(),
    sequence: 90,
    sequenceGroup: 40,
    tags: ACTION_TAGS.DANGER,
});

// 3. Mobile single-screen navigation inside DiscussApp (avoid floating ChatWindow popup on mobile)
patch(DiscussChannel.prototype, {
    _openChannel() {
        if (this.store.discuss.isActive) {
            this.setAsDiscussThread();
            return true;
        }
        return super._openChannel(...arguments);
    },
});

patch(Thread.prototype, {
    setAsDiscussThread(pushState) {
        if (this.store.discuss.isActive && this.store.env.services.ui.isSmall) {
            if (this.channel && !this.channel?.self_member_id?.is_pinned) {
                this.channel.isLocallyPinned = true;
            }
            if (pushState === undefined) {
                pushState = !this.discussAppAsThread;
            }
            this.store.discuss.thread = this;
            if (pushState) {
                this.setActiveURL();
            }
            const menu = this.store.messagingMenu;
            const sidebarState = this.store.discuss.sidebarState;
            if (sidebarState.activeTab?.notEq(menu.bookmarkTab)) {
                sidebarState.activeTab = this.channel?.primaryMessagingMenuTab ?? menu.chatTab;
            }
            return;
        }
        return super.setAsDiscussThread(...arguments);
    },
});

// 4. Root Discuss component: scope body class & offline connection indicator
patch(Discuss.prototype, {
    setup() {
        super.setup(...arguments);
        this.tpOnlineState = proxy({
            isOffline: typeof navigator !== "undefined" ? !navigator.onLine : false,
        });

        useListener(window, "online", () => {
            this.tpOnlineState.isOffline = false;
        });
        useListener(window, "offline", () => {
            this.tpOnlineState.isOffline = true;
        });

        onMounted(() => {
            document.body.classList.add("o_tp_personal_discuss_active");
        });
        onWillUnmount(() => {
            document.body.classList.remove("o_tp_personal_discuss_active");
        });
    },
});

// 5. MessagingMenu (Left Sidebar inside DiscussApp): unified 1-sidebar pill filters & + Tạo mới
patch(MessagingMenu.prototype, {
    tpOpenCreateDialog(initialMode = "dm") {
        this.dialog.add(TpCreateChatDialog, { initialMode });
    },

    get tpActivePill() {
        const uiState = this.state();
        const tabId = uiState?.activeTab?.id;
        if (tabId === MENU_TABS.CHANNEL) {
            return "channel";
        }
        if (tabId === MENU_TABS.BOOKMARK) {
            return "bookmark";
        }
        if (uiState?.pluginFilters?.[TP_DIRECT_FILTER_KEY]) {
            return "direct";
        }
        if (uiState?.selectedFilter?.id === "chat_unread") {
            return "unread";
        }
        if (uiState?.selectedFilter?.id === "chat_group") {
            return "group";
        }
        return "all";
    },

    get tpUnreadChatCounter() {
        return this.store.messagingMenu?.chatTab?.counter || 0;
    },

    get tpUnreadChannelCounter() {
        return this.store.messagingMenu?.channelTab?.counter || 0;
    },

    tpSelectPill(pillKey) {
        const uiState = this.state();
        const menu = this.store.messagingMenu;
        if (!uiState || !menu) {
            return;
        }
        if (pillKey === "channel" && menu.channelTab) {
            uiState.selectTab(menu.channelTab);
            uiState.setPluginFilter(TP_DIRECT_FILTER_KEY, undefined);
            uiState.selectedFilter = undefined;
            return;
        }
        if (pillKey === "bookmark" && menu.bookmarkTab) {
            uiState.selectTab(menu.bookmarkTab);
            uiState.setPluginFilter(TP_DIRECT_FILTER_KEY, undefined);
            return;
        }
        if (menu.chatTab && !uiState.activeTab?.eq(menu.chatTab)) {
            uiState.selectTab(menu.chatTab);
        }
        uiState.setPluginFilter(TP_DIRECT_FILTER_KEY, undefined);
        uiState.selectedFilter = undefined;

        if (pillKey === "unread") {
            const unreadFilter = menu.chatTab?.filters?.find((f) => f.id === "chat_unread");
            if (unreadFilter) {
                uiState.selectedFilter = unreadFilter;
            }
        } else if (pillKey === "group") {
            const groupFilter = menu.chatTab?.filters?.find((f) => f.id === "chat_group");
            if (groupFilter) {
                uiState.selectedFilter = groupFilter;
            }
        } else if (pillKey === "direct") {
            uiState.setPluginFilter(TP_DIRECT_FILTER_KEY, {
                id: "tp_direct",
                includesChannel: (c) => c.channel_type === "chat",
            });
        }
    },
});

// 6. DiscussContent: close right member panel by default on narrower screens (< 1440px),
//    mobile back-to-list button, real presence subtitle, and rich TANPHAT ONE empty state.
patch(DiscussContent.prototype, {
    setup() {
        super.setup(...arguments);
        this.tpDialog = useService("dialog");
    },

    actionPanelAutoOpenFn() {
        if (typeof window !== "undefined" && window.innerWidth < 1440) {
            return;
        }
        return super.actionPanelAutoOpenFn(...arguments);
    },

    tpBackToConversationList() {
        this.store.discuss.thread = undefined;
        router.pushState({ active_id: undefined });
        if (browser.location?.pathname?.startsWith("/app/ca-nhan/trao-doi/")) {
            browser.history.replaceState({}, "", "/app/ca-nhan/trao-doi");
        }
    },

    tpOpenCreateConversation(mode = "dm") {
        this.tpDialog.add(TpCreateChatDialog, { initialMode: mode });
    },

    get tpHeaderMetaLabel() {
        const ch = this.thread?.channel;
        if (!ch) {
            return "";
        }
        if (ch.channel_type === "chat") {
            // Show presence ONLY when native bus/store confirms real online/away status!
            const status = ch.correspondent?.persona?.im_status;
            if (status === "online") {
                return "Đang trực tuyến";
            }
            if (status === "away") {
                return "Tạm vắng";
            }
            return "Tin nhắn trực tiếp";
        }
        const count = ch.member_count || ch.channel_member_ids?.length || 0;
        if (ch.channel_type === "group") {
            return count ? `Nhóm trao đổi · ${count} thành viên` : "Nhóm trao đổi";
        }
        if (ch.channel_type === "channel") {
            return count ? `Kênh nội bộ · ${count} thành viên` : "Kênh nội bộ";
        }
        return "";
    },
});

// 7. Message bubbles: right-align self-authored messages inside DiscussApp channels ONLY
//    (leaves form chatters in HR / KH-KD / Request 100% untouched).
patch(Message.prototype, {
    get isTpDiscussChannelMessage() {
        return Boolean(
            this.env.inDiscussApp &&
                !this.env.messageCard &&
                this.props.thread?.model === "discuss.channel"
        );
    },

    get isAlignedRight() {
        if (this.isTpDiscussChannelMessage && this.props.message?.isSelfAuthored) {
            return true;
        }
        return super.isAlignedRight;
    },

    get shouldDisplayAuthorName() {
        if (this.isTpDiscussChannelMessage) {
            if (this.message.isSelfAuthored) {
                return false;
            }
            if (this.props.thread?.channel?.channel_type === "chat") {
                return false;
            }
            return true;
        }
        return super.shouldDisplayAuthorName;
    },
});

// 8. Composer inside DiscussApp: Vietnamese placeholder & IME composition guard
patch(Composer.prototype, {
    get placeholder() {
        if (this.env.inDiscussApp && this.thread?.channel && !this.props.placeholder) {
            return "Nhập tin nhắn…";
        }
        return super.placeholder;
    },

    get SEND_TEXT() {
        if (this.env.inDiscussApp && !this.props.composer?.message) {
            return "Gửi";
        }
        return super.SEND_TEXT;
    },

    onKeydown(ev) {
        if (ev.key === "Enter" && (ev.isComposing || ev.keyCode === 229)) {
            return;
        }
        return super.onKeydown(ev);
    },
});
