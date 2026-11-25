/** @odoo-module **/
import { Component, onWillStart, proxy, useProps } from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { uuid } from "@web/core/utils/strings";
import { InlineErrors } from "@tp_web_home/validation/inline_errors";
import { saveError } from "@tp_web_home/validation/validation";

class TpDigitalOfficeBase extends Component {
    static template = "tp_digital_office.Workspace";
    static components = { InlineErrors };
    props = useProps();
    initialTab = "announcements";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");

        this.state = proxy({
            tab: this.initialTab, // 'announcements' | 'minutes'
            mobileNavOpen: false,
            mode: "list", // 'list' | 'detail' | 'form'
            loading: true,
            busy: false,
            attempt: 0,
            fieldErrors: [],
            serverError: null,

            // List + DEC-044 filter state
            rows: [],
            total: 0,
            page: 1,
            pageSize: 20,
            maxPage: 1,
            canCreate: false,
            canPublishCompany: false,
            filterOptions: {
                categories: [],
                states: [],
                scopes: [],
                departments: [],
                projects: [],
                users: [],
                events: [],
            },
            filters: {
                search: "",
                category: "",
                state: "",
                department_id: "0",
                project_id: "0",
                ack_filter: "",
                date_from: "",
                date_to: "",
            },

            // Active detail
            detail: null,
            ackTracking: null,
            showReviseBox: false,
            reviseReason: "",
            reviseMajor: true,
            showRevokeBox: false,
            revokeReason: "",

            // Form state (Announcement or Minute)
            annForm: {
                id: 0,
                name: "",
                category: "general",
                issuing_department_id: "0",
                audience_scope: "departments",
                target_department_ids: [],
                target_user_ids: [],
                body: "",
                effective_date: new Date().toISOString().slice(0, 10),
                require_ack: true,
                ack_deadline: "",
            },
            minForm: {
                id: 0,
                name: "",
                calendar_event_id: "0",
                meeting_date_iso: new Date().toISOString().slice(0, 16),
                chair_user_id: "0",
                project_id: "0",
                department_id: "0",
                attendee_user_ids: [],
                discussion_content: "",
                conclusion_content: "",
                action_items: [],
            },
        });

        onWillStart(async () => {
            await this.loadList();
            const prefillEventId = Number(this.props.action?.context?.tp_from_calendar_event_id || 0);
            if (this.state.tab === "minutes" && prefillEventId > 0) {
                await this.openMinuteFromCalendarEvent(prefillEventId);
            }
        });
    }

    goHome() {
        this.action.doAction("tp_web_home.action_home");
    }

    toggleMobileNav() {
        this.state.mobileNavOpen = !this.state.mobileNavOpen;
    }

    async switchTab(targetTab) {
        this.state.mobileNavOpen = false;
        if (this.state.tab === targetTab && this.state.mode === "list") {
            return;
        }
        const targetAction =
            targetTab === "minutes"
                ? "tp_digital_office.action_meeting_minutes"
                : "tp_digital_office.action_announcements";
        await this.action.doAction(targetAction, { clearBreadcrumbs: true });
    }

    resetFilters() {
        this.state.filters.search = "";
        this.state.filters.category = "";
        this.state.filters.state = "";
        this.state.filters.department_id = "0";
        this.state.filters.project_id = "0";
        this.state.filters.ack_filter = "";
        this.state.filters.date_from = "";
        this.state.filters.date_to = "";
        this.state.page = 1;
        this.loadList();
    }

    get hasActiveFilters() {
        const f = this.state.filters;
        return Boolean(
            f.search ||
                f.category ||
                f.state ||
                (f.department_id && f.department_id !== "0") ||
                (f.project_id && f.project_id !== "0") ||
                f.ack_filter ||
                f.date_from ||
                f.date_to
        );
    }

    onFilterChange(key, ev) {
        this.state.filters[key] = ev.target.value;
        this.state.page = 1;
        this.loadList();
    }

    onSearchKeydown(ev) {
        if (ev.key === "Enter") {
            this.state.page = 1;
            this.loadList();
        }
    }

    onSearchInput(ev) {
        this.state.filters.search = ev.target.value;
    }

    triggerSearch() {
        this.state.page = 1;
        this.loadList();
    }

    onPageSizeChange(ev) {
        this.state.pageSize = Number(ev.target.value) || 20;
        this.state.page = 1;
        this.loadList();
    }

    changePage(delta) {
        const next = this.state.page + delta;
        if (next < 1 || next > this.state.maxPage) return;
        this.state.page = next;
        this.loadList();
    }

    async loadList() {
        this.state.loading = true;
        this.state.serverError = null;
        try {
            const params = {
                ...this.state.filters,
                page: this.state.page,
                page_size: this.state.pageSize,
            };
            if (this.state.tab === "announcements") {
                const res = await this.orm.call("tp.announcement", "tp_announcement_list_data", [params]);
                this.state.rows = res.rows || [];
                this.state.total = res.total || 0;
                this.state.page = res.page || 1;
                this.state.maxPage = res.max_page || 1;
                this.state.canCreate = Boolean(res.can_create);
                this.state.canPublishCompany = Boolean(res.can_publish_company);
                this.state.filterOptions = { ...this.state.filterOptions, ...(res.filter_options || {}) };
            } else {
                const res = await this.orm.call("tp.meeting.minute", "tp_minute_list_data", [params]);
                this.state.rows = res.rows || [];
                this.state.total = res.total || 0;
                this.state.page = res.page || 1;
                this.state.maxPage = res.max_page || 1;
                this.state.canCreate = true;
                this.state.filterOptions = { ...this.state.filterOptions, ...(res.filter_options || {}) };
            }
        } catch (err) {
            this.state.serverError = saveError(err, { verb: "tải danh sách", write: false });
        } finally {
            this.state.loading = false;
        }
    }

    backToList() {
        this.state.mode = "list";
        this.state.detail = null;
        this.state.ackTracking = null;
        this.state.fieldErrors = [];
        this.state.serverError = null;
        this.loadList();
    }

    // --------------------------------------------------------- Announcements Flow
    openCreateAnnouncement() {
        this.state.fieldErrors = [];
        this.state.serverError = null;
        this.state.annForm = {
            id: 0,
            name: "",
            category: "general",
            issuing_department_id: "0",
            audience_scope: this.state.canPublishCompany ? "company" : "departments",
            target_department_ids: [],
            target_user_ids: [],
            body: "",
            effective_date: new Date().toISOString().slice(0, 10),
            require_ack: true,
            ack_deadline: "",
        };
        this.state.mode = "form";
    }

    openEditAnnouncement() {
        const d = this.state.detail;
        if (!d) return;
        this.state.fieldErrors = [];
        this.state.serverError = null;
        this.state.annForm = {
            id: d.id,
            name: d.name || "",
            category: d.category || "general",
            issuing_department_id: String(d.issuing_department_id || 0),
            audience_scope: d.audience_scope || "company",
            target_department_ids: [...(d.target_department_ids || [])],
            target_user_ids: [...(d.target_user_ids || [])],
            body: d.body || "",
            effective_date: d.effective_date || "",
            require_ack: Boolean(d.require_ack),
            ack_deadline: d.ack_deadline || "",
        };
        this.state.mode = "form";
    }

    toggleAnnMultiId(listKey, idVal) {
        const arr = [...(this.state.annForm[listKey] || [])];
        const idx = arr.indexOf(idVal);
        if (idx >= 0) arr.splice(idx, 1);
        else arr.push(idVal);
        this.state.annForm[listKey] = arr;
    }

    isAnnMultiSelected(listKey, idVal) {
        return (this.state.annForm[listKey] || []).includes(idVal);
    }

    async saveAnnouncement(publishNow = false) {
        if (this.state.busy) return;
        this.state.busy = true;
        this.state.attempt += 1;
        this.state.fieldErrors = [];
        this.state.serverError = null;
        try {
            const res = await this.orm.call("tp.announcement", "tp_save_announcement", [this.state.annForm, publishNow]);
            if (!res?.ok) {
                this.state.fieldErrors = res?.field_errors || [];
                return;
            }
            this.notification.add(
                publishNow ? `Đã phát hành thông báo ${res.code}.` : `Đã lưu nháp thông báo ${res.code}.`,
                { type: "success" }
            );
            await this.openAnnouncementDetail(res.id);
        } catch (err) {
            this.state.serverError = saveError(err, { verb: publishNow ? "phát hành thông báo" : "lưu thông báo" });
        } finally {
            this.state.busy = false;
        }
    }

    async openAnnouncementDetail(id) {
        this.state.loading = true;
        this.state.serverError = null;
        this.state.ackTracking = null;
        this.state.showReviseBox = false;
        this.state.showRevokeBox = false;
        try {
            // Opening detail NEVER writes an acknowledgement!
            this.state.detail = await this.orm.call("tp.announcement", "tp_announcement_detail_data", [id]);
            this.state.mode = "detail";
            if (this.state.detail.can_manage && this.state.detail.state === "published") {
                this.state.ackTracking = await this.orm.call("tp.announcement", "tp_get_ack_tracking", [id]);
            }
        } catch (err) {
            this.state.serverError = saveError(err, { verb: "mở chi tiết thông báo", write: false });
        } finally {
            this.state.loading = false;
        }
    }

    async acknowledgeRead() {
        const d = this.state.detail;
        if (!d || this.state.busy) return;
        this.state.busy = true;
        try {
            await this.orm.call("tp.announcement", "tp_acknowledge_announcement", [d.id, uuid()]);
            this.notification.add(`Đã xác nhận đọc thông báo ${d.code} (v${d.version}).`, { type: "success" });
            await this.openAnnouncementDetail(d.id);
        } catch (err) {
            this.state.serverError = saveError(err, { verb: "xác nhận đã đọc" });
        } finally {
            this.state.busy = false;
        }
    }

    async publishDraftAnnouncement() {
        const d = this.state.detail;
        if (!d || this.state.busy) return;
        this.state.busy = true;
        try {
            await this.orm.call("tp.announcement", "action_publish", [[d.id]]);
            this.notification.add("Đã phát hành chính thức thông báo.", { type: "success" });
            await this.openAnnouncementDetail(d.id);
        } catch (err) {
            this.state.serverError = saveError(err, { verb: "phát hành thông báo" });
        } finally {
            this.state.busy = false;
        }
    }

    toggleReviseBox() {
        this.state.showReviseBox = !this.state.showReviseBox;
        this.state.showRevokeBox = false;
    }

    toggleRevokeBox() {
        this.state.showRevokeBox = !this.state.showRevokeBox;
        this.state.showReviseBox = false;
    }

    async submitPublishedAnnouncementRevision() {
        const d = this.state.detail;
        if (!d || this.state.busy) return;
        this.state.busy = true;
        this.state.serverError = null;
        try {
            await this.orm.call("tp.announcement", "action_revise_published", [[d.id]], {
                updated_vals: { body: d.body, name: d.name },
                major_reack: Boolean(this.state.reviseMajor),
                reason: this.state.reviseReason,
            });
            this.state.reviseReason = "";
            this.state.showReviseBox = false;
            this.notification.add("Đã cập nhật phiên bản thông báo.", { type: "success" });
            await this.openAnnouncementDetail(d.id);
        } catch (err) {
            this.state.serverError = saveError(err, { verb: "cập nhật phiên bản thông báo" });
        } finally {
            this.state.busy = false;
        }
    }

    async submitRevokeAnnouncement() {
        const d = this.state.detail;
        if (!d || this.state.busy) return;
        this.state.busy = true;
        this.state.serverError = null;
        try {
            await this.orm.call("tp.announcement", "action_revoke", [[d.id]], {
                reason: this.state.revokeReason,
                mode: "revoked",
            });
            this.state.revokeReason = "";
            this.state.showRevokeBox = false;
            this.notification.add("Đã thu hồi thông báo nội bộ.", { type: "warning" });
            await this.openAnnouncementDetail(d.id);
        } catch (err) {
            this.state.serverError = saveError(err, { verb: "thu hồi thông báo" });
        } finally {
            this.state.busy = false;
        }
    }

    // --------------------------------------------------------- Meeting Minutes Flow
    async openMinuteFromCalendarEvent(eventId) {
        try {
            const pre = await this.orm.call("tp.meeting.minute", "tp_prefill_from_calendar_event", [eventId]);
            if (pre.existing_minute_id) {
                await this.openMinuteDetail(pre.existing_minute_id);
                return;
            }
            this.openCreateMinute(pre);
        } catch (err) {
            this.state.serverError = saveError(err, { verb: "liên kết lịch họp", write: false });
        }
    }

    openCreateMinute(prefill = null) {
        this.state.fieldErrors = [];
        this.state.serverError = null;
        this.state.minForm = {
            id: 0,
            name: prefill?.name || "",
            calendar_event_id: String(prefill?.calendar_event_id || 0),
            meeting_date_iso: prefill?.meeting_date || new Date().toISOString().slice(0, 16),
            chair_user_id: String(prefill?.chair_user_id || 0),
            project_id: String(prefill?.project_id || 0),
            department_id: "0",
            attendee_user_ids: [...(prefill?.attendee_user_ids || [])],
            discussion_content: "",
            conclusion_content: "",
            action_items: [
                { id: 0, name: "", assignee_user_id: "", deadline: "", deliverable_expected: "", task_id: 0 },
            ],
        };
        this.state.mode = "form";
    }

    async onSelectCalendarEventPrefill(ev) {
        const evId = Number(ev.target.value || 0);
        this.state.minForm.calendar_event_id = String(evId);
        if (evId > 0 && !this.state.minForm.id) {
            try {
                const pre = await this.orm.call("tp.meeting.minute", "tp_prefill_from_calendar_event", [evId]);
                if (!pre.existing_minute_id) {
                    if (!this.state.minForm.name) this.state.minForm.name = pre.name || "";
                    if (pre.meeting_date) this.state.minForm.meeting_date_iso = pre.meeting_date;
                    if (pre.project_id) this.state.minForm.project_id = String(pre.project_id);
                    if (pre.chair_user_id) this.state.minForm.chair_user_id = String(pre.chair_user_id);
                    this.state.minForm.attendee_user_ids = [...(pre.attendee_user_ids || [])];
                }
            } catch {
                // ignore prefill failure
            }
        }
    }

    openEditMinute() {
        const d = this.state.detail;
        if (!d) return;
        this.state.fieldErrors = [];
        this.state.serverError = null;
        this.state.minForm = {
            id: d.id,
            name: d.name || "",
            calendar_event_id: String(d.calendar_event_id || 0),
            meeting_date_iso: d.meeting_date_iso || "",
            chair_user_id: String(d.chair_user_id || 0),
            project_id: String(d.project_id || 0),
            department_id: String(d.department_id || 0),
            attendee_user_ids: [...(d.attendee_user_ids || [])],
            discussion_content: d.discussion_content || "",
            conclusion_content: d.conclusion_content || "",
            action_items: (d.action_items || []).map((it) => ({
                id: it.id,
                name: it.name,
                assignee_user_id: String(it.assignee_user_id || ""),
                deadline: it.deadline || "",
                deliverable_expected: it.deliverable_expected || "",
                task_id: it.task_id || 0,
            })),
        };
        this.state.mode = "form";
    }

    toggleMinAttendee(uid) {
        const arr = [...(this.state.minForm.attendee_user_ids || [])];
        const idx = arr.indexOf(uid);
        if (idx >= 0) arr.splice(idx, 1);
        else arr.push(uid);
        this.state.minForm.attendee_user_ids = arr;
    }

    isMinAttendeeSelected(uid) {
        return (this.state.minForm.attendee_user_ids || []).includes(uid);
    }

    addActionItemRow() {
        this.state.minForm.action_items.push({
            id: 0,
            name: "",
            assignee_user_id: "",
            deadline: "",
            deliverable_expected: "",
            task_id: 0,
        });
    }

    removeActionItemRow(idx) {
        const row = this.state.minForm.action_items[idx];
        if (row?.task_id) return;
        this.state.minForm.action_items.splice(idx, 1);
    }

    onActionItemChange(idx, field, ev) {
        if (this.state.minForm.action_items[idx]) {
            this.state.minForm.action_items[idx][field] = ev.target.value;
        }
    }

    async saveMinute(issueNow = false) {
        if (this.state.busy) return;
        this.state.busy = true;
        this.state.attempt += 1;
        this.state.fieldErrors = [];
        this.state.serverError = null;
        try {
            const cleanedItems = (this.state.minForm.action_items || []).filter(
                (it) => (it.name || "").trim() || it.assignee_user_id || it.task_id
            );
            const payload = { ...this.state.minForm, action_items: cleanedItems };
            const res = await this.orm.call("tp.meeting.minute", "tp_save_minute", [payload, issueNow]);
            if (!res?.ok) {
                this.state.fieldErrors = res?.field_errors || [];
                return;
            }
            this.notification.add(
                issueNow
                    ? `Đã phát hành biên bản ${res.code} và giao đầu việc.`
                    : `Đã lưu biên bản ${res.code}.`,
                { type: "success" }
            );
            await this.openMinuteDetail(res.id);
        } catch (err) {
            this.state.serverError = saveError(err, { verb: issueNow ? "phát hành biên bản" : "lưu biên bản" });
        } finally {
            this.state.busy = false;
        }
    }

    async openMinuteDetail(id) {
        this.state.loading = true;
        this.state.serverError = null;
        this.state.showReviseBox = false;
        try {
            this.state.detail = await this.orm.call("tp.meeting.minute", "tp_minute_detail_data", [id]);
            this.state.mode = "detail";
        } catch (err) {
            this.state.serverError = saveError(err, { verb: "mở biên bản họp", write: false });
        } finally {
            this.state.loading = false;
        }
    }

    async confirmMinute() {
        const d = this.state.detail;
        if (!d || this.state.busy) return;
        this.state.busy = true;
        try {
            await this.orm.call("tp.meeting.minute", "action_confirm", [[d.id]]);
            this.notification.add("Đã xác nhận nội dung biên bản họp.", { type: "success" });
            await this.openMinuteDetail(d.id);
        } catch (err) {
            this.state.serverError = saveError(err, { verb: "xác nhận biên bản" });
        } finally {
            this.state.busy = false;
        }
    }

    async issueMinute() {
        const d = this.state.detail;
        if (!d || this.state.busy) return;
        this.state.busy = true;
        try {
            await this.orm.call("tp.meeting.minute", "action_issue", [[d.id]]);
            this.notification.add("Đã phát hành biên bản và tạo đầu việc cho người phụ trách.", { type: "success" });
            await this.openMinuteDetail(d.id);
        } catch (err) {
            this.state.serverError = saveError(err, { verb: "phát hành biên bản" });
        } finally {
            this.state.busy = false;
        }
    }

    async submitMinuteRevision() {
        const d = this.state.detail;
        if (!d || this.state.busy) return;
        this.state.busy = true;
        try {
            await this.orm.call("tp.meeting.minute", "action_revise", [[d.id], this.state.reviseReason]);
            this.state.reviseReason = "";
            this.state.showReviseBox = false;
            await this.openMinuteDetail(d.id);
            this.openEditMinute();
        } catch (err) {
            this.state.serverError = saveError(err, { verb: "mở hiệu chỉnh biên bản" });
        } finally {
            this.state.busy = false;
        }
    }

    openMyTasks() {
        browser.location.assign("/app/ca-nhan/cong-viec");
    }

    async uploadDetailAttachment(ev) {
        const files = [...(ev.target.files || [])];
        ev.target.value = "";
        const d = this.state.detail;
        if (!files.length || !d) return;
        const resModel = this.state.tab === "announcements" ? "tp.announcement" : "tp.meeting.minute";
        this.state.busy = true;
        try {
            for (const f of files) {
                const fd = new FormData();
                fd.append("file", f);
                fd.append("csrf_token", odoo?.csrf_token || "");
                const resp = await fetch(`/tp_digital_office/attachment/${resModel}/${d.id}/upload`, {
                    method: "POST",
                    body: fd,
                });
                const json = await resp.json();
                if (!resp.ok || !json.ok) {
                    throw new Error(json.error || "Không tải được tệp.");
                }
            }
            if (this.state.tab === "announcements") {
                await this.openAnnouncementDetail(d.id);
            } else {
                await this.openMinuteDetail(d.id);
            }
        } catch (err) {
            this.state.serverError = saveError(err, { verb: "tải tệp đính kèm" });
        } finally {
            this.state.busy = false;
        }
    }
}

export class TpAnnouncementsWorkspace extends TpDigitalOfficeBase {
    initialTab = "announcements";
}

export class TpMeetingMinutesWorkspace extends TpDigitalOfficeBase {
    initialTab = "minutes";
}

registry.category("actions").add("tp_digital_office.announcements", TpAnnouncementsWorkspace);
registry.category("actions").add("tp_digital_office.meeting_minutes", TpMeetingMinutesWorkspace);
