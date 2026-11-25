/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { TpCalendarEventDialog } from "@tp_personal_tools/calendar/calendar_event_dialog";

patch(TpCalendarEventDialog.prototype, {
    async onOpenMeetingMinute() {
        if (!this.state.eventId) {
            return;
        }
        const evId = this.state.eventId;
        if (this.props.close) {
            this.props.close();
        }
        await this.actionService.doAction("tp_digital_office.action_meeting_minutes", {
            additionalContext: { tp_from_calendar_event_id: evId },
        });
    },
});
