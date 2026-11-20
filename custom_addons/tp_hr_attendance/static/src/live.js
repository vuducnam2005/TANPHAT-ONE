import { onMounted, onWillUnmount } from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { useService } from "@web/core/utils/hooks";

/** Bus notification sent by the server-side ENTI sync (``tp.hr.attendance.source._tp_enti_notify``). */
export const LIVE_BUS_TYPE = "tp_hr_attendance/updated";

/**
 * ENTI-ATTENDANCE-002: keep an attendance screen current without F5.
 *
 * - One server-side sync reads ENTI for everybody and notifies internal users on the bus when stored days change
 *   (``{source_id, at, dates, health?}``, no personal data). Browsers never call ENTI.
 * - A notification refreshes the screen (debounced) only when ``relevant(payload)`` says it touches what is shown.
 * - A slow fallback poll runs only while the tab is visible (lost websocket, proxy without websocket).
 * - A hidden tab only remembers that something changed and refreshes once it is shown again.
 *
 * ``refresh()`` returns ``false`` when the screen is busy (loading, exporting…); the refresh is then kept pending
 * and ``flush()`` runs it once the screen is free. Call ``loaded()`` after every successful load.
 */
export function useAttendanceLive({ refresh, relevant = () => true, pollMs = 4000, debounceMs = 250 }) {
    let bus = null;
    try {
        bus = useService("bus_service");
    } catch {
        bus = null; // No bus in this context: the visible-tab poll still keeps the screen current.
    }
    const live = { pending: false, last: Date.now(), debounce: null, poll: null, unsubscribe: null };

    function trigger() {
        browser.clearTimeout(live.debounce);
        if (document.hidden) {
            live.pending = true;
            return;
        }
        live.pending = false;
        if (refresh() === false) {
            live.pending = true;
        }
    }
    function onNotify(payload) {
        if (!relevant(payload || {})) {
            return;
        }
        if (document.hidden) {
            live.pending = true;
            return;
        }
        browser.clearTimeout(live.debounce);
        live.debounce = browser.setTimeout(trigger, debounceMs);
    }
    function onVisibility() {
        if (!document.hidden && (live.pending || Date.now() - live.last > 2000)) {
            trigger();
        }
    }

    onMounted(() => {
        if (bus) {
            try {
                live.unsubscribe = bus.subscribe(LIVE_BUS_TYPE, onNotify);
                bus.start();
            } catch {
                live.unsubscribe = null;
            }
        }
        live.poll = browser.setInterval(() => {
            if (!document.hidden && Date.now() - live.last >= pollMs * 0.9) {
                trigger();
            }
        }, pollMs);
        document.addEventListener("visibilitychange", onVisibility);
    });
    onWillUnmount(() => {
        if (typeof live.unsubscribe === "function") {
            live.unsubscribe();
        }
        document.removeEventListener("visibilitychange", onVisibility);
        browser.clearInterval(live.poll);
        browser.clearTimeout(live.debounce);
    });

    return {
        loaded() {
            live.pending = false;
            live.last = Date.now();
        },
        flush() {
            if (live.pending) {
                trigger();
            }
        },
    };
}
