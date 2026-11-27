import { Component, t, useProps } from "@odoo/owl";

const HOURS_24 = Array.from({ length: 24 }, (_, idx) => String(idx).padStart(2, "0"));

function parseHHmm(rawValue) {
    const raw = typeof rawValue === "string" ? rawValue.trim() : "";
    const match = raw.match(/^([01]\d|2[0-3]):([0-5]\d)(?::[0-5]\d)?$/);
    if (!match) {
        return { hour: "", minute: "" };
    }
    return { hour: match[1], minute: match[2] };
}

function parseIsoDateTime24(rawValue) {
    const raw = typeof rawValue === "string" ? rawValue.trim() : "";
    if (!raw) {
        return { date: "", time: "" };
    }
    const dtMatch = raw.match(/^(\d{4}-\d{2}-\d{2})[T ](\d{2}:\d{2})(?::\d{2})?/);
    if (dtMatch) {
        const parsedTime = parseHHmm(dtMatch[2]);
        return {
            date: dtMatch[1],
            time: parsedTime.hour ? `${parsedTime.hour}:${parsedTime.minute}` : "",
        };
    }
    const dateOnly = raw.match(/^(\d{4}-\d{2}-\d{2})$/);
    if (dateOnly) {
        return { date: dateOnly[1], time: "" };
    }
    return { date: "", time: "" };
}

function localTodayIso() {
    const now = new Date();
    const y = now.getFullYear();
    const m = String(now.getMonth() + 1).padStart(2, "0");
    const d = String(now.getDate()).padStart(2, "0");
    return `${y}-${m}-${d}`;
}

/**
 * 24-hour time selector (`HH:mm`, `00:00`..`23:59`, never AM/PM or SA/CH).
 * Renders two compact `<select>` controls side by side and preserves odd minutes
 * (e.g. `08:07`) if already present on the record.
 */
export class TpTime24Field extends Component {
    static template = "tp_web_home.TpTime24Field";

    props = useProps({
        value: t.any().optional(),
        id: t.string().optional(),
        name: t.string().optional(),
        placeholder: t.string().optional(),
        disabled: t.boolean().optional(),
        readonly: t.boolean().optional(),
        invalid: t.any().optional(),
        stepMinutes: t.number().optional(),
        class: t.string().optional(),
        onChange: t.function().optional(),
    });

    get hours() {
        return HOURS_24;
    }

    get parsed() {
        return parseHHmm(this.props.value);
    }

    get isLocked() {
        return Boolean(this.props.disabled || this.props.readonly);
    }

    get isInvalid() {
        return Boolean(this.props.invalid);
    }

    get minutes() {
        const rawStep = Number(this.props.stepMinutes);
        const step = Number.isFinite(rawStep) && rawStep >= 1 && rawStep <= 30 ? Math.floor(rawStep) : 5;
        const set = new Set();
        for (let m = 0; m < 60; m += step) {
            set.add(String(m).padStart(2, "0"));
        }
        const curMin = this.parsed.minute;
        if (curMin) {
            set.add(curMin);
        }
        return Array.from(set).sort();
    }

    onHourChange(ev) {
        const nextHour = ev.target.value;
        if (!nextHour) {
            this.props.onChange?.("");
            return;
        }
        const nextMinute = this.parsed.minute || "00";
        this.props.onChange?.(`${nextHour}:${nextMinute}`);
    }

    onMinuteChange(ev) {
        const nextMinute = ev.target.value;
        if (!nextMinute) {
            this.props.onChange?.("");
            return;
        }
        const nextHour = this.parsed.hour || "00";
        this.props.onChange?.(`${nextHour}:${nextMinute}`);
    }
}

/**
 * 24-hour date + time selector (`YYYY-MM-DDTHH:mm`, never `<input type="datetime-local">`).
 * Pairs a native `<input type="date">` with `<TpTime24Field/>`.
 */
export class TpDateTime24Field extends Component {
    static template = "tp_web_home.TpDateTime24Field";
    static components = { TpTime24Field };

    props = useProps({
        value: t.any().optional(),
        id: t.string().optional(),
        name: t.string().optional(),
        placeholder: t.string().optional(),
        disabled: t.boolean().optional(),
        readonly: t.boolean().optional(),
        invalid: t.any().optional(),
        stepMinutes: t.number().optional(),
        class: t.string().optional(),
        onChange: t.function().optional(),
    });

    get parsed() {
        return parseIsoDateTime24(this.props.value);
    }

    get isLocked() {
        return Boolean(this.props.disabled || this.props.readonly);
    }

    get isInvalid() {
        return Boolean(this.props.invalid);
    }

    onDateChange(ev) {
        const nextDate = (ev.target.value || "").trim();
        if (!nextDate) {
            this.props.onChange?.("");
            return;
        }
        const nextTime = this.parsed.time || "08:00";
        this.props.onChange?.(`${nextDate}T${nextTime}`);
    }

    onTimeChange(nextHHmm) {
        const curDate = this.parsed.date;
        if (!curDate) {
            if (!nextHHmm) {
                this.props.onChange?.("");
                return;
            }
            this.props.onChange?.(`${localTodayIso()}T${nextHHmm}`);
            return;
        }
        const safeTime = nextHHmm || "08:00";
        this.props.onChange?.(`${curDate}T${safeTime}`);
    }
}
