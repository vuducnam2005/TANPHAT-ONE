import { Component, onMounted, onWillDestroy, proxy, useListener, useProps } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { usePopover } from "@web/core/popover/popover_hook";
import { patch } from "@web/core/utils/patch";
import { DashboardLoader } from "@spreadsheet_dashboard/bundle/dashboard_action/dashboard_loader_service";
import { SpreadsheetDashboardAction } from "@spreadsheet_dashboard/bundle/dashboard_action/dashboard_action";
import { DashboardMobileSearchPanel } from "@spreadsheet_dashboard/bundle/dashboard_action/mobile_search_panel/mobile_search_panel";

class TpChartTooltip extends Component {
    static template = "tp_dashboard_privacy.ChartTooltip";
    props = useProps({ item: Object, percentage: String, id: String, keep: Function, leave: Function });
}

export class TpReportChart extends Component {
    static template = "tp_dashboard_privacy.ReportChart";
    props = useProps({ chart: Object, donut: Boolean, total: String, chartId: String, openSource: Function });

    setup() {
        this.state = proxy({ active: null });
        this.tooltip = usePopover(TpChartTooltip, {
            position: "top", role: "tooltip", popoverClass: "tp_chart_popover",
            animation: false, setActiveElement: false,
            onClose: () => { this.state.active = null; },
        });
        this.closeTimer = null;
        onWillDestroy(() => clearTimeout(this.closeTimer));
    }

    get slices() {
        // Geometry only. Exact amounts and totals always come from the backend.
        const total = this.props.chart.items.reduce((sum, item) => sum + item.value, 0);
        let offset = 0;
        return this.props.chart.items.map(item => {
            const share = total ? item.value / total * 100 : 0;
            const slice = { ...item, share, offset,
                percentage: new Intl.NumberFormat("vi-VN", { maximumFractionDigits: 1 }).format(share) + "%" };
            offset += share;
            return slice;
        });
    }

    get ticks() {
        const maximum = Math.max(0, ...this.props.chart.items.map(item => item.value));
        const divisor = this.props.chart.unit === "Triệu đồng" ? 1000000 : 1;
        return [0, 1, 2, 3, 4].map(index => new Intl.NumberFormat("vi-VN", {
            maximumFractionDigits: 2,
        }).format(maximum / divisor * index / 4));
    }

    get activeItem() { return this.slices[this.state.active]; }
    get tooltipId() { return this.props.chartId + "_tooltip"; }

    keep() { clearTimeout(this.closeTimer); }
    leave() {
        this.keep();
        this.closeTimer = setTimeout(() => this.tooltip.close(), 160);
    }

    show(index, ev) {
        if (ev.pointerType === "touch") return;
        this.keep();
        if (this.state.active === index && this.tooltip.isOpen) return;
        this.tooltip.open(ev.currentTarget, { item: this.props.chart.items[index],
            percentage: this.props.donut ? this.slices[index].percentage : "",
            id: this.tooltipId, keep: () => this.keep(), leave: () => this.leave() });
        this.state.active = index;
    }

    open(index) {
        this.keep();
        this.tooltip.close();
        const item = this.props.chart.items[index];
        return this.props.openSource(item.source, item.project_id, item.state);
    }
}

export class TpConnectedDashboard extends Component {
    static template = "tp_dashboard_privacy.ConnectedDashboard";
    static components = { TpReportChart };
    props = useProps({ dashboardId: Number, kind: String });

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = proxy({ loading: true, error: "", forbidden: false, data: null, projects: [],
            project: "", from: "", to: "", activeFilters: {}, filtersOpen: false });
        this.request = 0;
        this.opening = false;
        onMounted(() => this.refresh());
        onWillDestroy(() => { this.request++; });
    }

    async refresh() {
        const request = ++this.request;
        this.state.loading = true;
        this.state.error = "";
        this.state.data = null;
        const filters = { project_id: Number(this.state.project) || false,
            date_from: this.state.from || false, date_to: this.state.to || false };
        try {
            const data = await this.orm.call("spreadsheet.dashboard", "tp_dashboard_report",
                [[this.props.dashboardId], filters]);
            if (request !== this.request) return;
            this.state.data = data;
            this.state.projects = data.projects;
            this.state.activeFilters = filters;
        } catch (error) {
            if (request !== this.request) return;
            this.state.forbidden = /AccessError|AccessDenied/.test(error.data?.name || "");
            this.state.projects = [];
            this.state.error = this.state.forbidden
                ? "Không đủ quyền xem nguồn dữ liệu trong phạm vi này."
                : (error.data?.message || "Không thể tải số liệu. Kiểm tra kết nối rồi thử lại.");
        } finally {
            if (request === this.request) this.state.loading = false;
        }
    }

    // MOBILE-001: phones fold the filter form behind a "Bộ lọc" button; the count shows what is applied.
    get filterCount() {
        return [this.state.project, this.state.from, this.state.to].filter(Boolean).length;
    }

    get unlistedProject() {
        return Boolean(this.state.project) && !this.state.projects.some(item => item.id === Number(this.state.project));
    }

    get filterSummary() {
        const project = this.state.projects.find(item => item.id === Number(this.state.project));
        const day = value => value.split("-").reverse().join("/");
        // NATIVE-STABILIZE-001: after a failed load the list is cleared (no stale project names),
        // but the request still carries the chosen project; never claim "all projects" then.
        const parts = [project ? project.code : (this.state.project ? "Dự án đã chọn" : "Tất cả dự án được phép")];
        if (this.state.from || this.state.to) {
            parts.push((this.state.from ? "từ " + day(this.state.from) : "") +
                (this.state.from && this.state.to ? " " : "") + (this.state.to ? "đến " + day(this.state.to) : ""));
        } else {
            parts.push("toàn bộ thời gian");
        }
        return parts.join(" · ");
    }

    toggleFilters() {
        this.state.filtersOpen = !this.state.filtersOpen;
    }

    async reset() {
        this.state.project = this.state.from = this.state.to = "";
        await this.refresh();
    }

    change(field, ev) {
        this.state[field] = ev.target.value;
        return this.refresh();
    }

    submit(ev) {
        ev.preventDefault();
        return this.refresh();
    }

    async open(source, projectId = false, state = false) {
        // One navigation per tap: a double tap must not stack two source actions.
        if (!source || this.state.loading || this.opening) return;
        this.opening = true;
        try {
            const action = await this.orm.call("spreadsheet.dashboard", "tp_dashboard_action",
                [[this.props.dashboardId], source, this.state.activeFilters, projectId, state]);
            await this.action.doAction(action);
        } catch (error) {
            this.state.data = null;
            this.state.forbidden = /AccessError|AccessDenied/.test(error.data?.name || "");
            this.state.error = this.state.forbidden ? "Không đủ quyền mở chứng từ nguồn."
                : "Không thể mở chứng từ nguồn. Hãy làm mới và thử lại.";
        } finally {
            this.opening = false;
        }
    }
}

patch(DashboardLoader.prototype, {
    getModelConfig(result) {
        const config = super.getModelConfig(result);
        config.custom.tpDashboard = result.tp_dashboard;
        return config;
    },
    _createSpreadsheetModel(snapshot, revisions, config) {
        const model = super._createSpreadsheetModel(snapshot, revisions, config);
        model.tpDashboard = config.custom.tpDashboard;
        return model;
    },
});

SpreadsheetDashboardAction.components = { ...SpreadsheetDashboardAction.components, TpConnectedDashboard };
patch(SpreadsheetDashboardAction.prototype, {
    tpKind() { return this.loader.getActiveDashboard()?.model?.tpDashboard?.kind; },
    tpInternal() { return this.loader.getActiveDashboard()?.model?.tpDashboard?.internal; },
    tpSidebarKey(ev, id) {
        if (this.tpKind() && (ev.key === "Enter" || ev.key === " ")) {
            ev.preventDefault();
            this.openDashboard(id);
        }
    },
});

// MOBILE-001: the native phone dashboard picker, only when a TANPHAT dashboard is active.
// Keyboard/Escape/focus handling here; full-screen layout in dashboard.scss (.tp_mobile_dashboard_panel).
patch(DashboardMobileSearchPanel.prototype, {
    setup() {
        super.setup();
        useListener(window, "keydown", (ev) => {
            if (ev.key === "Escape" && this.state.isOpen && this.tpPanel()) {
                ev.preventDefault();
                ev.stopPropagation();
                this.tpClose();
            }
        }, true);
    },
    tpPanel() { return Boolean(this.props.activeDashboard?.model?.tpDashboard); },
    tpFocus(selector, frames = 20) {
        // The portal/toggle is re-rendered asynchronously; retry for a few frames instead of guessing a delay.
        const element = document.querySelector(selector);
        if (element) {
            element.focus();
        } else if (frames > 0) {
            requestAnimationFrame(() => this.tpFocus(selector, frames - 1));
        }
    },
    openDashboardSelection() {
        super.openDashboardSelection();
        if (this.state.isOpen && this.tpPanel()) this.tpFocus(".tp_mobile_dashboard_panel .o_mobile_search_button");
    },
    onDashboardSelected(dashboardId) {
        const tp = this.tpPanel();
        super.onDashboardSelected(dashboardId);
        if (tp) this.tpFocus(".tp_mobile_dashboard_toggle");
    },
    tpClose() {
        const tp = this.tpPanel();
        this.state.isOpen = false;
        if (tp) this.tpFocus(".tp_mobile_dashboard_toggle");
    },
    tpKey(ev, callback) {
        if (this.tpPanel() && (ev.key === "Enter" || ev.key === " ")) {
            ev.preventDefault();
            callback();
        }
    },
});
