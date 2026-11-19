import { browser } from "@web/core/browser/browser";

/**
 * Shared helpers for the attendance screens (HR-ATTENDANCE-SIMPLE-002, DEC-055/056).
 * Dates travel as ISO strings (YYYY-MM-DD); the server decides "today" in Asia/Ho_Chi_Minh.
 */
export const PAGE_SIZES = [10, 20, 50, 100];
// Same order as the server (attendance_figures.STATUS_ORDER). "absent" = a finished scheduled working day without
// any punch; "no_punch" = not punched yet / not decided; "rest" = not a working day by schedule (Sunday).
export const STATE_ORDER = ["out_recorded", "working", "missing", "review", "absent", "no_punch", "rest", "leave", "no_source"];
// ENTI-ATTENDANCE-002 palette: blue = complete, teal = still at work, amber = needs a check, red = absent,
// slate/grey = nothing to show yet, violet = confirmed leave. Every colour is always paired with a text label.
export const STATE_COLORS = {
    out_recorded: "#2563EB", working: "#0D9488", missing: "#D97706", review: "#B45309", absent: "#DC2626",
    no_punch: "#94A3B8", rest: "#CBD5E1", leave: "#A78BFA", no_source: "#64748B", future: "#EEF1F5",
};
export const TOTAL_COLOR = "#2563EB";
export function attendanceIssue(row) {
    if (row.state === "missing") {
        const label = !row.in && !row.out ? "Thiếu giờ vào và ra" : !row.in ? "Thiếu giờ vào" : !row.out ? "Thiếu giờ ra" : "Thiếu lượt chấm công";
        return { label, icon: "schedule" };
    }
    return { label: row.state === "review" ? "Cần đối chiếu dữ liệu" : row.state_label, icon: row.state === "review" ? "warning" : "info" };
}
const XLSX_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";
const EXPECTED = ["odoo.exceptions.UserError", "odoo.exceptions.ValidationError", "odoo.exceptions.AccessError"];

export function readStore(key) {
    try {
        return JSON.parse(browser.sessionStorage.getItem(key) || "{}") || {};
    } catch {
        return {}; // Private window / blocked storage: start from defaults.
    }
}

export function writeStore(key, value) {
    try {
        browser.sessionStorage.setItem(key, JSON.stringify(value));
    } catch {
        // Storage unavailable: the screen still works, it just forgets the filters.
    }
}

export function shiftMonth(month, delta) {
    const [year, number] = month.split("-").map(Number);
    const value = new Date(Date.UTC(year, number - 1 + delta, 1));
    return `${value.getUTCFullYear()}-${String(value.getUTCMonth() + 1).padStart(2, "0")}`;
}

export function shiftDate(iso, delta) {
    const value = new Date(`${iso}T00:00:00Z`);
    value.setUTCDate(value.getUTCDate() + delta);
    return value.toISOString().slice(0, 10);
}

export function daysBetween(start, end) {
    return Math.round((new Date(`${end}T00:00:00Z`) - new Date(`${start}T00:00:00Z`)) / 86400000);
}

export function formatDate(iso) {
    return iso ? `${iso.slice(8, 10)}/${iso.slice(5, 7)}/${iso.slice(0, 4)}` : "";
}

export function formatHours(value) {
    if (!value) {
        return "0:00";
    }
    const minutes = Math.round(value * 60);
    return `${Math.floor(minutes / 60)}:${String(minutes % 60).padStart(2, "0")}`;
}

/** Next anchor date for prev/next in day / week (Mon–Sun) / month / free range modes. */
export function stepPeriod(mode, data, delta) {
    if (mode === "month") {
        return { date: `${shiftMonth(data.start.slice(0, 7), delta)}-01` };
    }
    if (mode === "week") {
        return { date: shiftDate(data.start, 7 * delta) };
    }
    if (mode === "range") {
        const span = daysBetween(data.start, data.end) + 1;
        return { from: shiftDate(data.start, span * delta), to: shiftDate(data.end, span * delta) };
    }
    return { date: shiftDate(data.start, delta) };
}

export function pagerText(data, unit = "dòng") {
    if (!data || !data.total) {
        return `0 ${unit}`;
    }
    const first = (data.page - 1) * data.page_size + 1;
    const last = Math.min(data.total, data.page * data.page_size);
    return `${first}–${last} / ${data.total} ${unit}`;
}

/** Message to show for a failed RPC; a session expiry is re-thrown so Odoo shows its login flow. */
export function rpcError(error, fallback) {
    if (/SessionExpired/.test(error?.data?.name || error?.name || "")) {
        throw error;
    }
    return EXPECTED.includes(error?.data?.name) ? error.data.message : fallback;
}

/** Save a server-built workbook (``{filename, data: base64}``) without leaving the page. */
export function downloadBase64(file, mime = XLSX_MIME) {
    const binary = atob(file.data);
    const bytes = new Uint8Array(binary.length);
    for (let index = 0; index < binary.length; index++) {
        bytes[index] = binary.charCodeAt(index);
    }
    const url = URL.createObjectURL(new Blob([bytes], { type: mime }));
    const link = document.createElement("a");
    link.href = url;
    link.download = file.filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    browser.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

/** Late total cell text for a period row/panel: exact machine numbers or an honest "no data" text. */
export function lateText(late) {
    if (!late) {
        return "Chưa có số liệu";
    }
    return late.state === "exact" ? `${late.count} lần · ${late.minutes} phút` : late.text;
}

/** Small in-cell note next to "—" (missing side, not yet punched, no data); never an invented time. */
export function cellNote(row, side) {
    if (row.future || row.state === "future") {
        return side === "in" ? "Chưa đến" : "";
    }
    if (row.state === "missing") {
        if (side === "in" && !row.in) {
            return "Thiếu giờ vào";
        }
        if (side === "out" && !row.out) {
            return "Thiếu giờ ra";
        }
        return "";
    }
    if (row.state === "working") {
        return side === "out" && !row.out ? "Đang làm" : "";
    }
    if (row.state === "review") {
        return side === "out" ? "Cần kiểm tra" : "";
    }
    if (["absent", "no_punch", "rest", "no_source", "leave"].includes(row.state)) {
        return side === "in" ? row.state_label : "";
    }
    return "";
}

/** Semantic status pill for one personal attendance row (maps strictly to backend presence state). */
export function mineStatusInfo(row) {
    if (!row) {
        return { key: "no_source", label: "Chưa có dữ liệu", tone: "muted", icon: "remove" };
    }
    if (row.state === "out_recorded") {
        return { key: "out_recorded", label: "Đủ vào/ra", tone: "ok", icon: "check_circle" };
    }
    if (row.state === "working") {
        return { key: "working", label: "Chờ ghi nhận giờ ra", tone: "info", icon: "schedule" };
    }
    if (row.state === "missing") {
        const label = !row.in && !row.out
            ? "Thiếu giờ vào/ra"
            : !row.in
                ? "Thiếu giờ vào"
                : !row.out
                    ? "Thiếu giờ ra"
                    : "Thiếu lượt chấm công";
        return { key: "missing", label, tone: "warn", icon: "schedule" };
    }
    if (row.state === "review") {
        return { key: "review", label: "Cần kiểm tra", tone: "danger", icon: "warning" };
    }
    if (row.state === "leave") {
        return { key: "leave", label: "Nghỉ đã xác nhận", tone: "leave", icon: "event_available" };
    }
    if (row.state === "absent") {
        return { key: "absent", label: "Vắng theo lịch", tone: "danger", icon: "event_busy" };
    }
    if (row.state === "no_punch") {
        return { key: "no_punch", label: "Chưa chấm công", tone: "muted", icon: "radio_button_unchecked" };
    }
    if (row.state === "rest") {
        return { key: "rest", label: row.state_label || "Nghỉ theo lịch", tone: "future", icon: "calendar_today" };
    }
    if (row.state === "future" || row.future) {
        return { key: "future", label: "Ngày tương lai", tone: "future", icon: "calendar_today" };
    }
    return { key: "no_source", label: row.status_label || "Chưa có dữ liệu", tone: "muted", icon: "help_outline" };
}
