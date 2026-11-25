/** @odoo-module **/
import { Component, onWillStart, proxy } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useBus, useService } from "@web/core/utils/hooks";
import { baseChartOptions, useRequestChart } from "../charts";
import { TpRequestCreateModal } from "../create/create_modal";
import {
    APPROVAL_BADGE,
    EXEC_BADGE,
    MODE_TO_ACTION,
    PRIORITY_BADGE,
    extractErrorMessage,
    openRequestDetail,
    writeListState,
} from "../prefs";

export class TpRequestDashboard extends Component {
    static template = "tp_request.Dashboard";
    static components = { TpRequestCreateModal };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.APPROVAL_BADGE = APPROVAL_BADGE;
        this.EXEC_BADGE = EXEC_BADGE;
        this.PRIORITY_BADGE = PRIORITY_BADGE;

        this.state = proxy({
            loading: true,
            error: "",
            data: null,
            showCreate: false,
            filterTypeId: "",
            dateFrom: "",
            dateTo: "",
        });

        this.statusChart = useRequestChart(() => this.buildStatusChartSpec());
        this.typeChart = useRequestChart(() => this.buildTypeChartSpec());

        useBus(this.env.bus, "TP_REQUEST:LIVE_UPDATED", () => this.load(true));
        onWillStart(() => this.load());
    }

    async load(silent = false) {
        if (!silent) {
            this.state.loading = true;
            this.state.error = "";
        }
        try {
            const params = {};
            if (this.state.filterTypeId) params.type_id = Number(this.state.filterTypeId);
            if (this.state.dateFrom) params.date_from = this.state.dateFrom;
            if (this.state.dateTo) params.date_to = this.state.dateTo;
            this.state.data = await (silent ? this.orm.silent : this.orm).call(
                "tp.request",
                "tp_dashboard_data",
                [params]
            );
            this.state.error = "";
        } catch (err) {
            if (!silent) {
                this.state.error = extractErrorMessage(err, "Không tải được tổng quan Yêu cầu phê duyệt.");
            }
        } finally {
            this.state.loading = false;
        }
    }

    get counts() {
        return (
            this.state.data?.counts || {
                to_approve: 0,
                mine_pending: 0,
                mine_returned: 0,
                to_execute: 0,
                overdue: 0,
            }
        );
    }

    buildStatusChartSpec() {
        const items = this.state.data?.status_chart || [];
        if (!items.length) return null;
        return {
            type: "doughnut",
            data: {
                labels: items.map((i) => i.label),
                datasets: [
                    {
                        data: items.map((i) => i.count),
                        backgroundColor: items.map((i) => i.color),
                        borderWidth: 2,
                        borderColor: "#ffffff",
                        hoverOffset: 6,
                    },
                ],
            },
            options: baseChartOptions({
                cutout: "64%",
                onClick: (_ev, elements) => {
                    if (elements?.length) {
                        const item = items[elements[0].index];
                        if (item) {
                            this.openFilteredList("watching", { tab: item.key, approval_state: item.key });
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: (ctx) => {
                                const item = items[ctx.dataIndex];
                                return `${item.label}: ${item.count} hồ sơ (${item.percent}%)`;
                            },
                        },
                    },
                },
            }),
        };
    }

    buildTypeChartSpec() {
        const items = this.state.data?.type_chart || [];
        if (!items.length) return null;
        return {
            type: "bar",
            data: {
                labels: items.map((i) => i.label),
                datasets: [
                    {
                        label: "Số đề nghị",
                        data: items.map((i) => i.count),
                        backgroundColor: items.map((i) => i.color),
                        borderRadius: 6,
                        maxBarThickness: 44,
                    },
                ],
            },
            options: baseChartOptions({
                onClick: (_ev, elements) => {
                    if (elements?.length) {
                        const item = items[elements[0].index];
                        if (item) {
                            this.openFilteredList("mine", { type_id: String(item.type_id) });
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: { precision: 0, color: "#475569" },
                        grid: { color: "#e2e8f0" },
                    },
                    x: {
                        ticks: { color: "#334155" },
                        grid: { display: false },
                    },
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: (ctx) => `${ctx.parsed.y} hồ sơ`,
                        },
                    },
                },
            }),
        };
    }

    openFilteredList(mode, filters = {}) {
        writeListState(mode, {
            tab: filters.tab || "all",
            search: "",
            type_id: filters.type_id || "",
            department_id: "",
            requester_user_id: "",
            priority: "",
            approval_state: filters.approval_state || "",
            date_from: this.state.dateFrom || "",
            date_to: this.state.dateTo || "",
            overdue_only: Boolean(filters.overdue_only),
            page: 1,
            page_size: 100,
            scrollTop: 0,
        });
        this.action.doAction(MODE_TO_ACTION[mode] || "tp_request.action_mine");
    }

    openDetail(row) {
        openRequestDetail(this.action, row.id, "overview");
    }

    openCreate() {
        this.state.showCreate = true;
    }

    onCreated(res) {
        this.state.showCreate = false;
        if (res?.id) {
            openRequestDetail(this.action, res.id, "overview");
        } else {
            this.load();
        }
    }

    onFilterChange(field, ev) {
        this.state[field] = ev.target.value;
        this.load();
    }

    clearDateFilter() {
        this.state.filterTypeId = "";
        this.state.dateFrom = "";
        this.state.dateTo = "";
        this.load();
    }
}

registry.category("actions").add("tp_request.dashboard", TpRequestDashboard);
