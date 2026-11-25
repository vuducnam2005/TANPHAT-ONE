import { onWillStart, proxy } from "@odoo/owl";
import { useAskRecurrenceUpdatePolicy } from "@calendar/views/ask_recurrence_update_policy_hook";
import { CalendarCommonPopover } from "@web/views/calendar/calendar_common/calendar_common_popover";
import { useService } from "@web/core/utils/hooks";
import { TpShareToDiscussDialog } from "../shared/share_to_discuss_dialog";

/**
 * Clean, concise quick-view popover when clicking an event on Lịch làm việc.
 * - Strictly masks private events (`'Bận'`, zero organizer/attendee/note leaks).
 * - Allows invited attendees to RSVP (`Chấp nhận`, `Chưa chắc`, `Từ chối`) even when `user_can_edit=false`.
 * - Shows Edit/Delete ONLY when `user_can_edit=true`.
 */
export class TpCalendarPopover extends CalendarCommonPopover {
    static template = "tp_personal_tools.CalendarPopover";

    setup() {
        super.setup();
        this.orm = useService("orm");
        this.dialog = useService("dialog");
        this.notification = useService("notification");
        this.askRecurrenceUpdatePolicy = useAskRecurrenceUpdatePolicy();

        this.state = proxy({
            loading: true,
            card: null,
            rsvpBusy: false,
        });

        onWillStart(async () => {
            await this.loadCard();
        });
    }

    async loadCard() {
        this.state.loading = true;
        try {
            const card = await this.orm.call("calendar.event", "tp_get_event_detail_card", [
                Number(this.props.record.id),
            ]);
            this.state.card = card;
        } catch {
            // Fallback to safe minimal record data if offline/transient error
            const rec = this.props.record;
            const isPriv = rec.rawRecord?.privacy === "private" && !rec.rawRecord?.user_can_edit;
            this.state.card = {
                id: rec.id,
                name: isPriv ? "Bận" : rec.title || "Lịch làm việc",
                is_masked_private: isPriv,
                time_display: [this.date, this.time].filter(Boolean).join(" · "),
                organizer: { name: "" },
                attendees: [],
                location: "",
                videocall_location: "",
                privacy_label: isPriv ? "Riêng tư (chỉ hiện Bận)" : "Lịch làm việc",
                user_can_edit: Boolean(rec.rawRecord?.user_can_edit),
                is_attendee: false,
                my_status: "",
                recurrency: Boolean(rec.rawRecord?.recurrency),
            };
        } finally {
            this.state.loading = false;
        }
    }

    get visibleAttendees() {
        return (this.state.card?.attendees || []).slice(0, 5);
    }

    get hiddenAttendeeCount() {
        const total = this.state.card?.attendees?.length || 0;
        return Math.max(0, total - 5);
    }

    async onRespondStatus(nextStatus) {
        const card = this.state.card;
        if (!card || this.state.rsvpBusy || card.my_status === nextStatus) {
            return;
        }
        let recurrenceUpdate = false;
        if (card.recurrency) {
            recurrenceUpdate = await this.askRecurrenceUpdatePolicy();
            if (!recurrenceUpdate) {
                return;
            }
        }
        this.state.rsvpBusy = true;
        try {
            await this.orm.call("calendar.event", "change_attendee_status", [
                [card.id],
                nextStatus,
                recurrenceUpdate,
            ]);
            this.notification.add("Đã cập nhật phản hồi lời mời.", { type: "success" });
            await this.props.model.load();
            this.props.close();
        } catch (err) {
            this.notification.add(err?.data?.message || "Không thể cập nhật trạng thái tham gia.", {
                type: "warning",
            });
        } finally {
            this.state.rsvpBusy = false;
        }
    }

    onShareToDiscuss() {
        const card = this.state.card;
        if (!card || card.is_masked_private) {
            return;
        }
        this.props.close();
        this.dialog.add(TpShareToDiscussDialog, {
            targetModel: "calendar.event",
            targetId: card.id,
            targetTitle: card.name,
        });
    }
}
