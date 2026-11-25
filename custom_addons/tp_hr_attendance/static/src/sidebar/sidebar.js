import { onMounted } from "@odoo/owl";
import { WebClient } from "@web/webclient/webclient";
import { TpHrPrefs, TpHrSidebar } from "@tp_hr_workspace/sidebar/sidebar";
import {
    ATT_APP_XMLID,
    ATT_LAST_LEAF_KEY,
    attPrefs,
    resetAttPrefs,
    saveAttPrefs,
} from "../prefs";

const ATT_GROUP_ICONS = {
    "tp_hr_attendance.menu_group_attendance": "schedule",
    "tp_hr_attendance.menu_group_attendance_admin": "tune",
};

const ATT_LEAF_ICONS = {
    "tp_hr_attendance.menu_dashboard": "dashboard",
    "tp_hr_attendance.menu_mine": "event_available",
};

const ACTION_TO_LEAF_XMLID = {
    "tp_hr_attendance.action_dashboard": "tp_hr_attendance.menu_dashboard",
    "tp_hr_attendance.action_days": "tp_hr_attendance.menu_dashboard",
    "tp_hr_attendance.action_late": "tp_hr_attendance.menu_dashboard",
    "tp_hr_attendance.action_board": "tp_hr_attendance.menu_dashboard",
    "tp_hr_attendance.action_mine": "tp_hr_attendance.menu_mine",
    "tp_hr_attendance.action_my_requests": "tp_hr_attendance.menu_mine",
    "tp_hr_attendance.action_sources": "tp_hr_attendance.menu_sources",
    "tp_hr_attendance.action_enti_employee_images": "tp_hr_attendance.menu_sources",
    "tp_hr_attendance.action_rules": "tp_hr_attendance.menu_sources",
    "tp_hr_attendance.action_codes": "tp_hr_attendance.menu_sources",
    "tp_hr_attendance.action_assignments": "tp_hr_attendance.menu_sources",
    "tp_hr_attendance.action_enti_mapping": "tp_hr_attendance.menu_enti_mapping",
    "tp_hr_attendance.action_enti_config": "tp_hr_attendance.menu_enti_config",
    "tp_hr_attendance.action_enti_logs": "tp_hr_attendance.menu_enti_logs",
    "tp_hr_attendance.action_review": "tp_hr_attendance.menu_review",
    "tp_hr_attendance.action_periods": "tp_hr_attendance.action_periods",
    "tp_hr_attendance.action_logs": "tp_hr_attendance.menu_periods",
};

const MODEL_TO_LEAF_XMLIDS = {
    "tp.hr.attendance.day": ["tp_hr_attendance.menu_dashboard"],
    "tp.hr.attendance.late": ["tp_hr_attendance.menu_dashboard"],
    "tp.hr.attendance.correction": ["tp_hr_attendance.menu_review", "tp_hr_attendance.menu_mine"],
    "tp.hr.attendance.period": ["tp_hr_attendance.menu_periods"],
    "tp.hr.attendance.log": ["tp_hr_attendance.menu_periods"],
    "tp.hr.attendance.enti.mapping": ["tp_hr_attendance.menu_enti_mapping"],
    "tp.hr.attendance.enti.sync.log": ["tp_hr_attendance.menu_enti_logs"],
    "tp.hr.attendance.enti.employee.image": ["tp_hr_attendance.menu_sources"],
    "tp.hr.attendance.enti.config.wizard": ["tp_hr_attendance.menu_enti_config"],
};

function str(val) {
    return typeof val === "string" ? val : "";
}

function isAttendanceAction(action) {
    if (!action) {
        return false;
    }
    return (
        str(action.xml_id).startsWith("tp_hr_attendance.") ||
        str(action.tag).startsWith("tp_hr_attendance.") ||
        str(action.res_model).startsWith("tp.hr.attendance.")
    );
}

const ATT_BODY_CLASSES = {
    shell: "o_tp_att_shell",
    rail: "o_tp_att_rail",
    mobile: "o_tp_att_mobile",
    compact: "o_tp_att_compact",
    reduceMotion: "o_tp_att_reduce_motion",
};

export class TpAttendancePrefs extends TpHrPrefs {
    get prefs() {
        return attPrefs;
    }

    setDensity(density) {
        saveAttPrefs({ density });
    }
    setMotion(motion) {
        saveAttPrefs({ motion });
    }
    toggleCollapsed() {
        saveAttPrefs({ collapsed: !attPrefs.collapsed });
    }
    reset() {
        resetAttPrefs();
    }
}

/**
 * Dedicated sidebar for the standalone Chấm công application.
 * Extends TpHrSidebar directly so layout, collapse rail, mobile drawer, user menu,
 * and keyboard focus handling stay 100% consistent without duplicating code or state.
 */
export class TpAttendanceSidebar extends TpHrSidebar {
    static components = { ...TpHrSidebar.components, TpAttendancePrefs };

    get appXmlid() {
        return ATT_APP_XMLID;
    }
    get appTitle() {
        return "Chấm công";
    }
    get appMark() {
        return "";
    }
    get appIcon() {
        return "schedule";
    }
    get sidebarId() {
        return "tp_att_sidebar";
    }
    get searchInputId() {
        return "tp_att_function_search";
    }
    get lastLeafKey() {
        return ATT_LAST_LEAF_KEY;
    }
    get prefsComponent() {
        return TpAttendancePrefs;
    }
    get groupIcons() {
        return ATT_GROUP_ICONS;
    }
    get leafIcons() {
        return ATT_LEAF_ICONS;
    }
    get bodyClassConfig() {
        return ATT_BODY_CLASSES;
    }
    get prefs() {
        return attPrefs;
    }
    saveAppPrefs(changes) {
        saveAttPrefs(changes);
    }
    resetAppPrefs() {
        resetAttPrefs();
    }
    get tpReadonly() {
        // Regular employees create/withdraw their own corrections & export personal sheets.
        return false;
    }

    setup() {
        super.setup();
        this._switchingApp = false;
        onMounted(() => this.syncActive());
    }

    syncActive() {
        const current = this.action.currentController?.action;
        if (!this._switchingApp && isAttendanceAction(current) && this.menu.getCurrentApp()?.xmlid !== ATT_APP_XMLID) {
            const attApp = (this.menu.getApps?.() || []).find((a) => a.xmlid === ATT_APP_XMLID);
            if (attApp) {
                this._switchingApp = true;
                try {
                    this.menu.setCurrentMenu(attApp);
                } finally {
                    this._switchingApp = false;
                }
            }
        }
        super.syncActive();
    }

    resolveFallbackLeaf(leaves, current) {
        const xmlId = str(current.xml_id);
        const targetXmlid = xmlId && ACTION_TO_LEAF_XMLID[xmlId];
        if (targetXmlid) {
            const hit = leaves.filter((l) => l.xmlid === targetXmlid);
            if (hit.length) {
                return hit;
            }
        }
        const resModel = str(current.res_model);
        const modelXmlids = resModel && MODEL_TO_LEAF_XMLIDS[resModel];
        if (modelXmlids) {
            for (const xmlid of modelXmlids) {
                const hit = leaves.filter((l) => l.xmlid === xmlid);
                if (hit.length) {
                    return hit;
                }
            }
        }
        return [];
    }
}

WebClient.components = { ...WebClient.components, TpAttendanceSidebar };
