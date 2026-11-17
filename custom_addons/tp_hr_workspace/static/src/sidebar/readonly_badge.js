import { session } from "@web/session";
import { patch } from "@web/core/utils/patch";
import { TpHrSidebar } from "./sidebar";

/** "Chỉ xem" label for employees without an HR group; the flag comes from the server session. */
patch(TpHrSidebar.prototype, {
    get tpReadonly() {
        return Boolean(session.tp_hr_readonly);
    },
});
