import { Component, onWillStart, proxy, useProps } from "@odoo/owl";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";
import { uuid } from "@web/core/utils/strings";
import { InlineErrors } from "@tp_web_home/validation/inline_errors";
import { saveError } from "@tp_web_home/validation/validation";
import { TpColleaguePicker } from "../shared/colleague_picker";
import { TpShareToDiscussDialog } from "../shared/share_to_discuss_dialog";

function buildDefaultTimes(initialSlot) {
    const pad = (n) => String(n).padStart(2, "0");
    if (initialSlot?.startIso && initialSlot?.stopIso) {
        return {
            allday: Boolean(initialSlot.allday),
            startIso: initialSlot.startIso,
            stopIso: initialSlot.stopIso,
            startDate: initialSlot.startDate || initialSlot.startIso.slice(0, 10),
            stopDate: initialSlot.stopDate || initialSlot.stopIso.slice(0, 10),
        };
    }
    const now = new Date();
    const dStr = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
    const startH = Math.min(Math.max(now.getHours() + 1, 8), 16);
    const stopH = Math.min(startH + 1, 18);
    return {
        allday: false,
        startIso: `${dStr}T${pad(startH)}:00`,
        stopIso: `${dStr}T${pad(stopH)}:00`,
        startDate: dStr,
        stopDate: dStr,
    };
}

function formatIsoPreview24h(isoStr) {
    if (!isoStr || isoStr.length < 16) {
        return "";
    }
    const [dPart, tPart] = isoStr.slice(0, 16).split("T");
    const [y, m, d] = dPart.split("-");
    if (!y || !m || !d) {
        return isoStr;
    }
    return `${d}/${m}/${y} · ${tPart || "00:00"}`;
}

/**
 * Unified Create / Edit / Detail modal for Lịch làm việc.
 * - Fullscreen on mobile (< 768px), crisp modal on desktop.
 * - Uses `InlineErrors` + `saveError` (no danger toast on validation/save error).
 * - Never sends invitations before explicit Save; supports recurrence update scopes.
 */
export class TpCalendarEventDialog extends Component {
    static template = "tp_personal_tools.CalendarEventDialog";
    static components = { Dialog, InlineErrors, TpColleaguePicker };
    props = useProps();
    operationToken = uuid();

    setup() {
        this.orm = useService("orm");
        this.ui = useService("ui");
        this.dialog = useService("dialog");
        this.notification = useService("notification");
        this.actionService = useService("action");

        const slot = buildDefaultTimes(this.props.initialSlot);
        const tomorrow = new Date(Date.now() + 86400000 * 14).toISOString().slice(0, 10);

        this.state = proxy({
            loading: true,
            loadError: null,
            readOnlyMode: false,
            maskedPrivate: false,
            eventId: Number(this.props.eventId || 0),
            detailCard: null,

            // Form fields
            name: this.props.initialSlot?.title || "",
            calendarId: 0,
            allday: slot.allday,
            startIso: slot.startIso,
            stopIso: slot.stopIso,
            startDate: slot.startDate,
            stopDate: slot.stopDate,
            invitedColleagues: [],
            location: "",
            useDiscussVideocall: false,
            videocallLocation: "",
            notes: "",
            privacy: "public",
            showAs: "busy",
            alarmIds: [],
            categIds: [],
            recurrency: false,
            rruleTypeUi: "weekly",
            interval: 1,
            endType: "count",
            count: 5,
            until: tomorrow,
            recurrenceUpdate: "self_only",
            wasRecurring: false,

            // Reference data
            writableCalendars: [],
            alarms: [],
            tags: [],
            selfPartnerId: 0,
            conflicts: [],

            // Status
            dirty: false,
            busy: false,
            rsvpBusy: false,
            attempt: 0,
            serverError: null,
        });

        onWillStart(async () => {
            await this.bootstrapDialog();
        });
    }

    async bootstrapDialog() {
        this.state.loading = true;
        this.state.loadError = null;
        try {
            const boot = await this.orm.call("calendar.event", "tp_get_calendar_bootstrap", []);
            this.state.selfPartnerId = boot?.self_partner_id || 0;
            this.state.writableCalendars = (boot?.my_calendars || []).concat(
                (boot?.shared_calendars || []).filter((c) => c.can_write)
            );
            this.state.alarms = boot?.alarms || [];
            this.state.tags = boot?.tags || [];
            if (boot?.primary_calendar_id) {
                this.state.calendarId = boot.primary_calendar_id;
            } else if (this.state.writableCalendars.length) {
                this.state.calendarId = this.state.writableCalendars[0].id;
            }

            if (this.state.eventId > 0) {
                const card = await this.orm.call("calendar.event", "tp_get_event_detail_card", [
                    this.state.eventId,
                ]);
                this.applyDetailCard(card);
            } else {
                await this.refreshConflicts();
            }
        } catch (err) {
            this.state.loadError = saveError(err, {
                verb: "mở chi tiết lịch làm việc",
                write: false,
            });
        } finally {
            this.state.loading = false;
        }
    }

    applyDetailCard(card) {
        this.state.detailCard = card;
        this.state.maskedPrivate = Boolean(card.is_masked_private);
        this.state.readOnlyMode = Boolean(card.is_masked_private || !card.user_can_edit);
        this.state.name = card.name || "";
        this.state.allday = Boolean(card.allday);
        this.state.startIso = card.start_iso || this.state.startIso;
        this.state.stopIso = card.stop_iso || this.state.stopIso;
        this.state.startDate = card.start_date || this.state.startDate;
        this.state.stopDate = card.stop_date || this.state.stopDate;
        if (card.calendar_id) {
            this.state.calendarId = card.calendar_id;
        }
        this.state.location = card.location || "";
        this.state.videocallLocation = card.videocall_location || "";
        this.state.useDiscussVideocall = card.videocall_source === "discuss";
        this.state.notes = card.notes_text || "";
        this.state.privacy = card.privacy || "public";
        this.state.showAs = card.show_as || "busy";
        this.state.alarmIds = [...(card.alarm_ids || [])];
        this.state.categIds = (card.categ_ids || []).map((c) => c.id);
        this.state.recurrency = Boolean(card.recurrency);
        this.state.wasRecurring = Boolean(card.recurrency);
        this.state.rruleTypeUi = card.rrule_type_ui || "weekly";
        this.state.interval = Number(card.interval || 1);
        this.state.endType = card.end_type || "count";
        this.state.count = Number(card.count || 5);
        if (card.until) {
            this.state.until = card.until;
        }
        this.state.invitedColleagues = (card.attendees || [])
            .filter((a) => a.partner_id && a.partner_id !== this.state.selfPartnerId)
            .map((a) => ({
                user_id: a.user_id || 0,
                partner_id: a.partner_id,
                name: a.name,
                avatar_url: a.avatar_url,
                state: a.state,
                state_label: a.state_label,
            }));
        this.state.dirty = false;
    }

    get dialogTitle() {
        if (this.state.maskedPrivate) {
            return "Khung giờ bận";
        }
        if (this.state.readOnlyMode) {
            return "Chi tiết lịch làm việc";
        }
        return this.state.eventId ? "Chỉnh sửa lịch làm việc" : "Tạo lịch làm việc";
    }

    get dialogSize() {
        return this.ui.isSmall ? "fullscreen" : "lg";
    }

    get timeSummary24h() {
        if (this.state.allday) {
            if (!this.state.startDate) {
                return "";
            }
            const fmt = (d) => d.split("-").reverse().join("/");
            return this.state.startDate === this.state.stopDate
                ? `${fmt(this.state.startDate)} · Cả ngày`
                : `${fmt(this.state.startDate)} – ${fmt(this.state.stopDate)} · Cả ngày`;
        }
        const s = formatIsoPreview24h(this.state.startIso);
        const e = formatIsoPreview24h(this.state.stopIso);
        return s && e ? `${s} → ${e} (24h)` : "";
    }

    get fieldErrors() {
        if (!this.state.attempt) {
            return [];
        }
        const errs = [];
        if (!this.state.name.trim()) {
            errs.push({
                id: "tp_cal_ev_name",
                label: "Tiêu đề sự kiện",
                message: "Vui lòng nhập tiêu đề lịch làm việc.",
            });
        }
        if (this.state.allday) {
            if (!this.state.startDate || !this.state.stopDate) {
                errs.push({
                    id: "tp_cal_ev_start_date",
                    label: "Ngày diễn ra",
                    message: "Vui lòng chọn ngày bắt đầu và ngày kết thúc.",
                });
            } else if (this.state.stopDate < this.state.startDate) {
                errs.push({
                    id: "tp_cal_ev_stop_date",
                    label: "Ngày kết thúc",
                    message: "Ngày kết thúc không được trước ngày bắt đầu.",
                });
            }
        } else {
            if (!this.state.startIso || !this.state.stopIso) {
                errs.push({
                    id: "tp_cal_ev_start_iso",
                    label: "Thời gian",
                    message: "Vui lòng chọn thời gian bắt đầu và kết thúc.",
                });
            } else if (this.state.stopIso <= this.state.startIso) {
                errs.push({
                    id: "tp_cal_ev_stop_iso",
                    label: "Giờ kết thúc",
                    message: "Giờ kết thúc phải sau giờ bắt đầu.",
                });
            }
        }
        if (
            this.state.recurrency &&
            this.state.endType === "end_date" &&
            !this.state.until
        ) {
            errs.push({
                id: "tp_cal_ev_until",
                label: "Ngày kết thúc lặp",
                message: "Vui lòng chọn ngày kết thúc cho chuỗi lịch lặp.",
            });
        }
        return errs;
    }

    hasFieldError(id) {
        return this.fieldErrors.some((e) => e.id === id);
    }

    fieldErrorMessage(id) {
        return this.fieldErrors.find((e) => e.id === id)?.message || "";
    }

    get primaryButtonLabel() {
        if (this.state.busy) {
            return "Đang lưu…";
        }
        const hasInvitees = this.state.invitedColleagues.length > 0;
        if (this.state.eventId) {
            return hasInvitees ? "Lưu và cập nhật lời mời" : "Lưu thay đổi";
        }
        return hasInvitees ? "Tạo lịch và gửi lời mời" : "Lưu lịch";
    }

    markDirty() {
        this.state.dirty = true;
    }

    async refreshConflicts() {
        if (this.state.readOnlyMode) {
            return;
        }
        try {
            const pids = this.state.invitedColleagues.map((c) => c.partner_id);
            const startVal = this.state.allday ? this.state.startDate : this.state.startIso;
            const stopVal = this.state.allday ? this.state.stopDate : this.state.stopIso;
            const rows = await this.orm.call("calendar.event", "tp_check_schedule_conflicts", [
                startVal,
                stopVal,
                this.state.allday,
                pids,
                this.state.eventId || 0,
            ]);
            this.state.conflicts = Array.isArray(rows) ? rows : [];
        } catch {
            this.state.conflicts = [];
        }
    }

    onTimeFieldChange() {
        this.markDirty();
        if (!this.state.allday && this.state.startIso && this.state.stopIso <= this.state.startIso) {
            const dt = new Date(this.state.startIso);
            if (!Number.isNaN(dt.getTime())) {
                const pad = (n) => String(n).padStart(2, "0");
                const plus1h = new Date(dt.getTime() + 3600000);
                this.state.stopIso = `${plus1h.getFullYear()}-${pad(plus1h.getMonth() + 1)}-${pad(
                    plus1h.getDate()
                )}T${pad(plus1h.getHours())}:${pad(plus1h.getMinutes())}`;
            }
        }
        if (this.state.allday && this.state.startDate && this.state.stopDate < this.state.startDate) {
            this.state.stopDate = this.state.startDate;
        }
        this.refreshConflicts();
    }

    onColleaguesChange(list) {
        this.state.invitedColleagues = list;
        this.markDirty();
        this.refreshConflicts();
    }

    toggleAlarm(alarmId) {
        this.markDirty();
        if (this.state.alarmIds.includes(alarmId)) {
            this.state.alarmIds = this.state.alarmIds.filter((id) => id !== alarmId);
        } else {
            this.state.alarmIds = [...this.state.alarmIds, alarmId];
        }
    }

    async onSave() {
        if (this.state.busy || this.state.readOnlyMode) {
            return;
        }
        this.state.serverError = null;
        this.state.attempt++;
        if (this.fieldErrors.length) {
            return;
        }
        this.state.busy = true;
        try {
            const payload = {
                name: this.state.name.trim(),
                calendar_id: Number(this.state.calendarId) || false,
                allday: this.state.allday,
                start_iso: this.state.startIso,
                stop_iso: this.state.stopIso,
                start_date: this.state.startDate,
                stop_date: this.state.stopDate,
                partner_ids: this.state.invitedColleagues.map((c) => c.partner_id),
                location: this.state.location,
                use_discuss_videocall: this.state.useDiscussVideocall,
                videocall_location: this.state.videocallLocation,
                notes: this.state.notes,
                privacy: this.state.privacy,
                show_as: this.state.showAs,
                alarm_ids: this.state.alarmIds,
                categ_ids: this.state.categIds,
                recurrency: this.state.recurrency,
                rrule_type_ui: this.state.rruleTypeUi,
                interval: Number(this.state.interval || 1),
                end_type: this.state.endType,
                count: Number(this.state.count || 5),
                until: this.state.until,
                recurrence_update: this.state.recurrenceUpdate,
            };
            const savedCard = await this.orm.call("calendar.event", "tp_save_calendar_event", [
                this.state.eventId || 0,
                payload,
                this.operationToken,
            ]);
            const msg = this.state.eventId
                ? "Đã cập nhật lịch làm việc."
                : this.state.invitedColleagues.length
                  ? "Đã tạo lịch và gửi lời mời cho người tham gia."
                  : "Đã lưu lịch làm việc.";
            this.notification.add(msg, { type: "success" });
            this.state.dirty = false;
            await this.props.onSaved?.(savedCard);
            this.props.close();
        } catch (err) {
            this.state.serverError = saveError(err, { verb: "lưu lịch làm việc" });
        } finally {
            this.state.busy = false;
        }
    }

    async onRespondRsvp(statusKey) {
        if (!this.state.eventId || this.state.rsvpBusy) {
            return;
        }
        this.state.rsvpBusy = true;
        this.state.serverError = null;
        try {
            await this.orm.call("calendar.event", "change_attendee_status", [
                [this.state.eventId],
                statusKey,
                this.state.wasRecurring ? "self_only" : false,
            ]);
            this.notification.add("Đã cập nhật phản hồi lời mời.", { type: "success" });
            const refreshed = await this.orm.call("calendar.event", "tp_get_event_detail_card", [
                this.state.eventId,
            ]);
            this.applyDetailCard(refreshed);
            await this.props.onSaved?.(refreshed);
        } catch (err) {
            this.state.serverError = saveError(err, { verb: "cập nhật phản hồi lời mời" });
        } finally {
            this.state.rsvpBusy = false;
        }
    }

    onOpenShare() {
        if (!this.state.eventId || this.state.maskedPrivate) {
            return;
        }
        this.dialog.add(TpShareToDiscussDialog, {
            targetModel: "calendar.event",
            targetId: this.state.eventId,
            targetTitle: this.state.name,
        });
    }

    onRequestDelete() {
        if (!this.state.eventId || this.state.readOnlyMode) {
            return;
        }
        this.dialog.add(ConfirmationDialog, {
            title: "Xóa lịch làm việc",
            body: `Bạn có chắc chắn muốn xóa sự kiện "${this.state.name}" không?`,
            confirmLabel: "Xóa sự kiện",
            confirmClass: "btn-danger",
            cancelLabel: "Giữ lại",
            confirm: async () => {
                this.state.busy = true;
                try {
                    await this.orm.unlink("calendar.event", [this.state.eventId]);
                    this.notification.add("Đã xóa sự kiện khỏi lịch.", { type: "success" });
                    await this.props.onDeleted?.(this.state.eventId);
                    this.props.close();
                } catch (err) {
                    this.state.serverError = saveError(err, { verb: "xóa sự kiện" });
                } finally {
                    this.state.busy = false;
                }
            },
            cancel: () => {},
        });
    }

    onRequestClose() {
        if (this.state.dirty && !this.state.busy && !this.state.readOnlyMode) {
            this.dialog.add(ConfirmationDialog, {
                title: "Bỏ thay đổi chưa lưu?",
                body: "Bạn đang có thông tin lịch làm việc chưa lưu. Đóng cửa sổ sẽ hủy các thay đổi này.",
                confirmLabel: "Bỏ thay đổi",
                confirmClass: "btn-danger",
                cancelLabel: "Tiếp tục chỉnh sửa",
                confirm: () => this.props.close(),
                cancel: () => {},
            });
            return;
        }
        this.props.close();
    }
}
