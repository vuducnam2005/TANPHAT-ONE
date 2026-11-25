import { Component, onWillStart, proxy, useProps } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";
import { uuid } from "@web/core/utils/strings";
import { InlineErrors } from "@tp_web_home/validation/inline_errors";
import { saveError } from "@tp_web_home/validation/validation";
import { TpColleaguePicker } from "../shared/colleague_picker";

/**
 * Unified TANPHAT ONE conversation creator:
 * - Tab `dm`     : Tin nhắn trực tiếp (reuses `store.joinChat(partnerId, true)` — zero duplicate DMs)
 * - Tab `group`  : Nhóm trao đổi (explicit group name + member preview before creating)
 * - Tab `scoped` : Nhóm Dự án / Phòng ban (rule-based member resolution, never adds whole company or admin)
 * - Tab `channel`: Kênh nội bộ (`discuss.channel.tp_create_internal_channel`)
 */
export class TpCreateChatDialog extends Component {
    static template = "tp_personal_tools.CreateChatDialog";
    static components = { Dialog, InlineErrors, TpColleaguePicker };
    props = useProps();
    operationToken = uuid();

    setup() {
        this.orm = useService("orm");
        this.ui = useService("ui");
        this.store = useService("mail.store");
        this.notification = useService("notification");
        this.dmTimer = null;

        this.state = proxy({
            mode: this.props.initialMode || "dm", // 'dm' | 'group' | 'scoped' | 'channel'
            // Direct Message search
            dmQuery: "",
            dmLoading: true,
            dmColleagues: [],
            selectedDmColleague: null,
            // Group Chat
            groupName: "",
            groupMembers: [],
            // Scoped Project / Department Group
            scopedKind: "project", // 'project' | 'department'
            scopedSourceId: 0,
            scopedName: "",
            scopedDescription: "",
            scopedDepartments: [],
            scopedProjects: [],
            scopedPreviewMembers: [],
            scopedPreviewLoading: false,
            // Internal Channel
            channelName: "",
            channelDescription: "",
            // Status & Validation
            busy: false,
            attempt: 0,
            serverError: null,
        });

        onWillStart(async () => {
            await Promise.all([this.fetchDmColleagues(""), this.loadScopedOptions()]);
        });
    }

    get dialogSize() {
        return this.ui.isSmall ? "fullscreen" : "md";
    }

    switchMode(mode) {
        if (this.state.busy) {
            return;
        }
        this.state.mode = mode;
        this.state.attempt = 0;
        this.state.serverError = null;
        this.operationToken = uuid();
    }

    async loadScopedOptions() {
        try {
            const opts = await this.orm.call(
                "discuss.channel",
                "tp_get_channel_creation_options",
                []
            );
            this.state.scopedDepartments = opts?.departments || [];
            this.state.scopedProjects = opts?.projects || [];
            if (!this.state.scopedProjects.length && this.state.scopedDepartments.length) {
                this.state.scopedKind = "department";
            }
        } catch {
            this.state.scopedDepartments = [];
            this.state.scopedProjects = [];
        }
    }

    async onScopedSelectionChange() {
        const sid = Number(this.state.scopedSourceId || 0);
        if (!sid) {
            this.state.scopedPreviewMembers = [];
            return;
        }
        if (this.state.scopedKind === "project") {
            const p = this.state.scopedProjects.find((x) => x.id === sid);
            if (p && !this.state.scopedName.trim()) {
                this.state.scopedName = `Dự án ${p.code ? `[${p.code}] ` : ""}${p.name}`;
            }
        } else {
            const d = this.state.scopedDepartments.find((x) => x.id === sid);
            if (d && !this.state.scopedName.trim()) {
                this.state.scopedName = `Phòng ${d.name}`;
            }
        }
        this.state.scopedPreviewLoading = true;
        try {
            const list = await this.orm.call(
                "discuss.channel",
                "tp_preview_scoped_members",
                [this.state.scopedKind, sid]
            );
            this.state.scopedPreviewMembers = Array.isArray(list) ? list : [];
        } catch {
            this.state.scopedPreviewMembers = [];
        } finally {
            this.state.scopedPreviewLoading = false;
        }
    }

    onSwitchScopedKind(kind) {
        this.state.scopedKind = kind;
        this.state.scopedSourceId = 0;
        this.state.scopedName = "";
        this.state.scopedPreviewMembers = [];
    }

    async fetchDmColleagues(q) {
        this.state.dmLoading = true;
        try {
            const list = await this.orm.call("res.users", "tp_search_colleagues", [
                q || "",
                30,
                false,
            ]);
            this.state.dmColleagues = Array.isArray(list) ? list : [];
        } catch {
            this.state.dmColleagues = [];
        } finally {
            this.state.dmLoading = false;
        }
    }

    onDmQueryInput(ev) {
        this.state.dmQuery = ev.target.value || "";
        if (this.dmTimer) {
            clearTimeout(this.dmTimer);
        }
        this.dmTimer = setTimeout(() => {
            this.fetchDmColleagues(this.state.dmQuery);
        }, 200);
    }

    async onPickDmColleague(col) {
        this.state.selectedDmColleague = col;
        await this.onSubmit();
    }

    get fieldErrors() {
        if (!this.state.attempt) {
            return [];
        }
        const errs = [];
        if (this.state.mode === "dm") {
            if (!this.state.selectedDmColleague?.partner_id) {
                errs.push({
                    id: "tp_chat_dm_search",
                    label: "Đồng nghiệp",
                    message: "Vui lòng chọn đồng nghiệp cần nhắn tin trực tiếp.",
                });
            }
        } else if (this.state.mode === "group") {
            if (!this.state.groupName.trim()) {
                errs.push({
                    id: "tp_chat_group_name",
                    label: "Tên nhóm trao đổi",
                    message: "Vui lòng nhập tên cho nhóm trao đổi.",
                });
            }
            if (!this.state.groupMembers.length) {
                errs.push({
                    id: "tp_chat_group_members",
                    label: "Thành viên nhóm",
                    message: "Vui lòng chọn ít nhất một đồng nghiệp tham gia nhóm.",
                });
            }
        } else if (this.state.mode === "scoped") {
            if (!Number(this.state.scopedSourceId)) {
                errs.push({
                    id: "tp_chat_scoped_source",
                    label: this.state.scopedKind === "project" ? "Dự án nguồn" : "Phòng ban nguồn",
                    message:
                        this.state.scopedKind === "project"
                            ? "Vui lòng chọn dự án cần khởi tạo nhóm trao đổi."
                            : "Vui lòng chọn phòng ban cần khởi tạo nhóm trao đổi.",
                });
            }
        } else if (this.state.mode === "channel") {
            if (!this.state.channelName.trim()) {
                errs.push({
                    id: "tp_chat_channel_name",
                    label: "Tên kênh nội bộ",
                    message: "Vui lòng nhập tên kênh trao đổi nội bộ.",
                });
            }
        }
        return errs;
    }

    hasFieldError(id) {
        return this.fieldErrors.some((e) => e.id === id);
    }

    get primaryLabel() {
        if (this.state.busy) {
            return "Đang mở…";
        }
        if (this.state.mode === "dm") {
            return "Mở cuộc trò chuyện";
        }
        if (this.state.mode === "group") {
            return `Tạo nhóm (${this.state.groupMembers.length + 1} thành viên)`;
        }
        if (this.state.mode === "scoped") {
            const cnt = this.state.scopedPreviewMembers.length || 1;
            return `Tạo nhóm liên kết (${cnt} thành viên)`;
        }
        return "Tạo kênh nội bộ";
    }

    async openCreatedChannelById(channelId) {
        if (!channelId) {
            return;
        }
        await this.store.fetchChannel(channelId, { with_last_message: true });
        const chanRec = this.store["discuss.channel"].get(channelId);
        if (chanRec) {
            if (this.store.discuss.isActive) {
                chanRec.setAsDiscussThread();
            } else {
                await chanRec.open({ focus: true, bypassCompact: true });
            }
        }
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
            if (this.state.mode === "dm") {
                const partnerId = Number(this.state.selectedDmColleague.partner_id);
                const chat = await this.store.joinChat(partnerId, true);
                if (chat) {
                    if (this.store.discuss.isActive) {
                        chat.setAsDiscussThread();
                    } else {
                        await chat.open({ focus: true, bypassCompact: true });
                    }
                }
                this.props.close();
                return;
            }

            if (this.state.mode === "group") {
                const selfUid = this.store.self_user?.id;
                const usersTo = [
                    ...new Set([
                        ...(selfUid ? [selfUid] : []),
                        ...this.state.groupMembers.map((m) => Number(m.user_id)).filter(Boolean),
                    ]),
                ];
                const channel = await this.store.createGroupChat({
                    name: this.state.groupName.trim(),
                    users_to: usersTo,
                });
                if (channel && this.store.discuss.isActive) {
                    channel.setAsDiscussThread();
                }
                this.notification.add(`Đã tạo nhóm "${this.state.groupName.trim()}".`, {
                    type: "success",
                });
                this.props.close();
                return;
            }

            if (this.state.mode === "scoped") {
                const created = await this.orm.call(
                    "discuss.channel",
                    "tp_create_scoped_channel",
                    [
                        {
                            scope: this.state.scopedKind,
                            source_id: Number(this.state.scopedSourceId),
                            name: this.state.scopedName.trim(),
                            description: this.state.scopedDescription,
                        },
                        this.operationToken,
                    ]
                );
                await this.openCreatedChannelById(created?.id);
                this.notification.add(
                    `Đã tạo nhóm liên kết "${created?.name || ""}" (${created?.member_count || 1} thành viên).`,
                    { type: "success" }
                );
                this.props.close();
                return;
            }

            if (this.state.mode === "channel") {
                const created = await this.orm.call(
                    "discuss.channel",
                    "tp_create_internal_channel",
                    [
                        this.state.channelName.trim(),
                        this.state.channelDescription,
                        this.operationToken,
                    ]
                );
                await this.openCreatedChannelById(created?.id);
                this.notification.add(`Đã tạo kênh "${this.state.channelName.trim()}".`, {
                    type: "success",
                });
                this.props.close();
            }
        } catch (err) {
            this.state.serverError = saveError(err, { verb: "khởi tạo hội thoại" });
        } finally {
            this.state.busy = false;
        }
    }
}
