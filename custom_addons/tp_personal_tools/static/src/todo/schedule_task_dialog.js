import { Component, onWillStart, proxy, useProps } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";
import { uuid } from "@web/core/utils/strings";
import { TpDateTime24Field } from "@tp_web_home/inputs/time24";
import { InlineErrors } from "@tp_web_home/validation/inline_errors";
import { saveError } from "@tp_web_home/validation/validation";
import { TpColleaguePicker } from "../shared/colleague_picker";

function defaultScheduleSlot(deadlineIso) {
    const now = new Date();
    const pad = (n) => String(n).padStart(2, "0");
    let baseDate = `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`;
    if (deadlineIso && /^\d{4}-\d{2}-\d{2}/.test(deadlineIso)) {
        baseDate = deadlineIso.slice(0, 10);
    }
    const nextHour = Math.min(Math.max(now.getHours() + 1, 9), 16);
    return {
        startIso: `${baseDate}T${pad(nextHour)}:00`,
        stopIso: `${baseDate}T${pad(nextHour + 1)}:00`,
        startDate: baseDate,
        stopDate: baseDate,
    };
}

/**
 * Dialog to schedule a Personal Task onto Lịch làm việc (`res_model='project.task'`, `res_id=task.id`).
 * Never duplicates the task and never mutates the task deadline silently.
 */
export class TpScheduleTaskDialog extends Component {
    static template = "tp_personal_tools.ScheduleTaskDialog";
    static components = { Dialog, InlineErrors, TpColleaguePicker, TpDateTime24Field };
    props = useProps();
    operationToken = uuid();

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        const slot = defaultScheduleSlot(this.props.task?.deadline?.iso_local);
        this.state = proxy({
            name: this.props.task?.name || "",
            allday: false,
            startIso: slot.startIso,
            stopIso: slot.stopIso,
            startDate: slot.startDate,
            stopDate: slot.stopDate,
            calendarId: 0,
            myCalendars: [],
            privacy: "private",
            location: "",
            notes: this.props.task?.note_preview || "",
            invitedColleagues: [],
            conflicts: [],
            busy: false,
            attempt: 0,
            serverError: null,
        });

        onWillStart(async () => {
            try {
                const boot = await this.orm.call("calendar.event", "tp_get_calendar_bootstrap", []);
                this.state.myCalendars = (boot?.my_calendars || []).concat(
                    (boot?.shared_calendars || []).filter((c) => c.can_write)
                );
                if (boot?.primary_calendar_id) {
                    this.state.calendarId = boot.primary_calendar_id;
                }
                await this.checkConflicts();
            } catch {
                // Non-blocking bootstrap
            }
        });
    }

    get fieldErrors() {
        if (!this.state.attempt) {
            return [];
        }
        const errs = [];
        if (!this.state.name.trim()) {
            errs.push({
                id: "tp_sched_name",
                label: "Tiêu đề lịch",
                message: "Vui lòng nhập tiêu đề cho lịch làm việc.",
            });
        }
        if (this.state.allday) {
            if (!this.state.startDate || !this.state.stopDate) {
                errs.push({
                    id: "tp_sched_start_date",
                    label: "Ngày thực hiện",
                    message: "Vui lòng chọn ngày bắt đầu và ngày kết thúc.",
                });
            } else if (this.state.stopDate < this.state.startDate) {
                errs.push({
                    id: "tp_sched_stop_date",
                    label: "Ngày kết thúc",
                    message: "Ngày kết thúc không được trước ngày bắt đầu.",
                });
            }
        } else {
            if (!this.state.startIso || !this.state.stopIso) {
                errs.push({
                    id: "tp_sched_start_iso",
                    label: "Khung giờ",
                    message: "Vui lòng chọn thời gian bắt đầu và kết thúc.",
                });
            } else if (this.state.stopIso <= this.state.startIso) {
                errs.push({
                    id: "tp_sched_stop_iso",
                    label: "Giờ kết thúc",
                    message: "Giờ kết thúc phải sau giờ bắt đầu.",
                });
            }
        }
        return errs;
    }

    get primaryCtaLabel() {
        if (this.state.busy) {
            return "Đang lưu lịch…";
        }
        return this.state.invitedColleagues.length > 0
            ? "Đưa vào lịch và gửi lời mời"
            : "Đưa vào lịch";
    }

    async checkConflicts() {
        try {
            const partnerIds = this.state.invitedColleagues.map((c) => c.partner_id);
            const startVal = this.state.allday ? this.state.startDate : this.state.startIso;
            const stopVal = this.state.allday ? this.state.stopDate : this.state.stopIso;
            const list = await this.orm.call("calendar.event", "tp_check_schedule_conflicts", [
                startVal,
                stopVal,
                this.state.allday,
                partnerIds,
                0,
            ]);
            this.state.conflicts = Array.isArray(list) ? list : [];
        } catch {
            this.state.conflicts = [];
        }
    }

    onColleaguesChange(list) {
        this.state.invitedColleagues = list;
        this.checkConflicts();
    }

    hasFieldError(id) {
        return this.fieldErrors.some((e) => e.id === id);
    }

    onTimeChange() {
        this.checkConflicts();
    }

    async onSave() {
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
            const eventCard = await this.orm.call("project.task", "tp_schedule_personal_task", [
                Number(this.props.task.id),
                {
                    name: this.state.name.trim(),
                    allday: this.state.allday,
                    start_iso: this.state.startIso,
                    stop_iso: this.state.stopIso,
                    start_date: this.state.startDate,
                    stop_date: this.state.stopDate,
                    calendar_id: Number(this.state.calendarId) || false,
                    privacy: this.state.privacy,
                    location: this.state.location,
                    notes: this.state.notes,
                    partner_ids: this.state.invitedColleagues.map((c) => c.partner_id),
                },
                this.operationToken,
            ]);
            this.notification.add("Đã đưa công việc vào Lịch làm việc.", { type: "success" });
            this.props.onScheduled?.(eventCard);
            this.props.close();
        } catch (err) {
            this.state.serverError = saveError(err, { verb: "đưa vào lịch" });
        } finally {
            this.state.busy = false;
        }
    }
}
