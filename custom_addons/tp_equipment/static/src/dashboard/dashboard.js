import { Component, markup, onWillStart, proxy, useProps } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardActionServiceProps } from "@web/webclient/actions/action_plugin";

/**
 * EQUIP-UI-002 — office-equipment overview. Every number opens exactly the set it counts
 * (server `open_ui_detail`). Charts animate once per load / filter change, never on hover.
 */
const MODEL = "tp.equipment.dashboard";
const DONUT_RADIUS = 100;
const DONUT_CIRCUMFERENCE = 2 * Math.PI * DONUT_RADIUS;

const emptyFilters = () => ({ department_id: "", location_id: "", date_from: "", date_to: "" });
const FILTER_KEYS = ["department_id", "location_id", "date_from", "date_to"];

function sameFilters(a, b) {
    return FILTER_KEYS.every((key) => String(a?.[key] || "") === String(b?.[key] || ""));
}

const pctWidth = (value, max) => (max > 0 ? Math.max((value * 100) / max, value > 0 ? 2 : 0) : 0);

class EquipmentDashboard extends Component {
    static template = "tp_equipment.Dashboard";

    setup() {
        useProps(standardActionServiceProps);
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = proxy({
            loading: true,
            error: "",
            data: null,
            pending: emptyFilters(),
            applied: emptyFilters(),
            moreOpen: false,
            qualityOpen: false,
            hoveredAllocKey: null,
            busy: false,
            animKey: 0,
        });
        onWillStart(() => this.load());
    }

    async load() {
        this.state.loading = !this.state.data;
        this.state.busy = true;
        this.state.error = "";
        const filters = { ...this.state.pending };
        try {
            const data = await this.orm.call(MODEL, "get_dashboard", [filters]);
            this.state.data = data;
            this.state.applied = filters;
            this.state.moreOpen = false;
            this.state.hoveredAllocKey = null;
            this.state.animKey += 1;
        } catch (err) {
            this.state.error = err?.data?.message || err?.message || "Không tải được dữ liệu tổng quan.";
        } finally {
            this.state.loading = false;
            this.state.busy = false;
        }
    }

    apply() {
        return this.load();
    }

    clear() {
        this.state.pending = emptyFilters();
        return this.load();
    }

    toggleMore() {
        this.state.moreOpen = !this.state.moreOpen;
    }

    toggleQuality() {
        this.state.qualityOpen = !this.state.qualityOpen;
    }

    get isDirty() {
        return !sameFilters(this.state.pending, this.state.applied);
    }

    get hasAppliedFilters() {
        const a = this.state.applied;
        return FILTER_KEYS.some((key) => Boolean(a[key]));
    }

    get extraBadgeText() {
        const n = ["date_from", "date_to"].filter((key) => this.state.pending[key]).length;
        return n > 0 ? `Lọc thêm (${n})` : "Lọc thêm";
    }

    get scopeSummaryText() {
        const meta = this.state.data?.scope_meta;
        return meta ? `${meta.physical_total} thiết bị vật lý · ${meta.service_count} dịch vụ` : "";
    }

    get kpis() {
        return this.state.data?.ui_kpis || [];
    }

    get allocationSlices() {
        const alloc = this.state.data?.allocation;
        if (!alloc) return [];
        const denom = alloc.denominator || 0;
        const items = alloc.items || [];
        const gap = items.filter((item) => item.count > 0).length > 1 ? 3 : 0;
        let offset = 0;
        return items.map((item) => {
            const rawLen = denom > 0 ? (item.count / denom) * DONUT_CIRCUMFERENCE : 0;
            const visibleLen = item.count > 0 ? Math.max(rawLen - gap, 3) : 0;
            const slice = {
                ...item,
                dasharray: `${visibleLen.toFixed(2)} ${DONUT_CIRCUMFERENCE.toFixed(2)}`,
                dashoffset: `${(-offset).toFixed(2)}`,
                isHovered: this.state.hoveredAllocKey === item.key,
                isDimmed: Boolean(this.state.hoveredAllocKey && this.state.hoveredAllocKey !== item.key),
                pctText: `${item.percent}%`,
                dotStyle: `background-color: ${item.color};`,
            };
            offset += rawLen;
            return slice;
        });
    }

    get donutCenter() {
        const alloc = this.state.data?.allocation;
        if (this.state.hoveredAllocKey) {
            const slice = (alloc?.items || []).find((i) => i.key === this.state.hoveredAllocKey);
            if (slice) {
                return { value: slice.count, label: slice.label, sub: `${slice.percent}% tổng thiết bị` };
            }
        }
        return { value: alloc?.denominator ?? 0, label: "thiết bị vật lý", sub: "đang quản lý" };
    }

    get typeRows() {
        const rows = this.state.data?.ui_types || [];
        const maxVal = Math.max(...rows.map((r) => r.count), 1);
        return rows.map((row) => ({
            ...row,
            fillStyle: `width: ${pctWidth(row.count, maxVal).toFixed(1)}%; background-color: ${row.color};`,
            dotStyle: `background-color: ${row.color};`,
            pctText: `${row.percent}%`,
            title: row.members
                ? `${row.label}: ${row.count} thiết bị (${row.percent}%) — gồm ${row.members}`
                : `${row.label}: ${row.count} thiết bị (${row.percent}%)`,
        }));
    }

    get typeTotal() {
        return (this.state.data?.ui_types || []).reduce((sum, row) => sum + row.count, 0);
    }

    get departmentRows() {
        const rows = this.state.data?.departments || [];
        const maxVal = Math.max(...rows.map((r) => r.count), 1);
        return rows.map((row, index) => {
            const isDept = row.kind === "department";
            const personalW = isDept ? pctWidth(row.personal, maxVal) : 0;
            const sharedW = isDept ? Math.max(pctWidth(row.count, maxVal) - personalW, 0) : 0;
            return {
                ...row,
                isDept,
                firstSpecial: !isDept && (index === 0 || rows[index - 1].kind === "department"),
                personalStyle: `width: ${personalW.toFixed(1)}%;`,
                sharedStyle: `width: ${sharedW.toFixed(1)}%;`,
                fillStyle: `width: ${pctWidth(row.count, maxVal).toFixed(1)}%; background-color: ${row.color};`,
            };
        });
    }

    get attentionItems() {
        return this.state.data?.attention || [];
    }

    get qualityItems() {
        return this.state.data?.quality || [];
    }

    get qualityTotal() {
        return this.qualityItems.reduce((sum, item) => sum + (item.count || 0), 0);
    }

    get recentProposals() {
        return this.state.data?.recent_proposals || [];
    }

    proposalTone(prop) {
        if (prop.review_state === "returned") return "orange";
        if (prop.review_state === "review") return "blue";
        if (prop.approval_state === "approved") return "teal";
        return "neutral";
    }

    get filterScopeNote() {
        const meta = this.state.data?.scope_meta;
        if (!meta) return "";
        return (
            `Phạm vi chuẩn: ${meta.physical_total} thiết bị vật lý đang quản lý (${meta.all_records} hồ sơ, gồm ` +
            `${meta.service_count} dịch vụ, ${meta.draft_count} nháp, ${meta.retired_count} ngừng quản lý). ` +
            `Đề xuất lọc theo bộ phận yêu cầu và ngày đề xuất, không áp vị trí kho.`
        );
    }

    async openUi(kind, key = false) {
        if (this.state.busy || !kind) return;
        this.state.busy = true;
        try {
            const act = await this.orm.call(MODEL, "open_ui_detail", [kind, key, this.state.applied]);
            if (act) {
                // An action returned by orm.call keeps `help` as a plain string, which the list
                // would print as raw HTML; /web/action/load marks it the same way.
                if (typeof act.help === "string" && act.help) {
                    act.help = markup(act.help);
                }
                await this.action.doAction(act);
            }
        } finally {
            this.state.busy = false;
        }
    }

    openDepartment(row) {
        return row.kind === "department" ? this.openUi("department", row.key) : this.openUi(row.kind);
    }

    async openProposal(proposalId) {
        if (!proposalId || this.state.busy) return;
        await this.action.doAction({
            type: "ir.actions.act_window",
            res_model: "tp.equipment.proposal",
            res_id: proposalId,
            view_mode: "form",
            views: [[false, "form"]],
            target: "current",
            context: { tp_eq_leaf: "tp_equipment.menu_proposals" },
        });
    }

    exportExcel() {
        const domain = encodeURIComponent(JSON.stringify(this.state.data?.domain || []));
        return this.action.doAction({
            type: "ir.actions.act_url",
            url: `/tp_equipment/equipment.xlsx?domain=${domain}`,
            target: "download",
        });
    }
}

registry.category("actions").add("tp_equipment.dashboard", EquipmentDashboard);
