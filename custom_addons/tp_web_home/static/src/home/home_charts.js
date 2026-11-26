import { onWillUnmount, signal, useEffect } from "@odoo/owl";
import { loadBundle } from "@web/core/assets";
import { browser } from "@web/core/browser/browser";

export function prefersReducedMotion() {
    try {
        return Boolean(browser.matchMedia?.("(prefers-reduced-motion: reduce)").matches);
    } catch {
        return false;
    }
}

let chartLoadPromise = null;

export function ensureChartJs() {
    if (typeof Chart !== "undefined") {
        return Promise.resolve(true);
    }
    if (!chartLoadPromise) {
        chartLoadPromise = loadBundle("web.chartjs_lib").then(
            () => typeof Chart !== "undefined",
            () => {
                chartLoadPromise = null;
                return false;
            }
        );
    }
    return chartLoadPromise;
}

/**
 * Reactive Chart.js lifecycle hook for OWL 3 signals without redundant re-animations.
 */
export function useHomeChart(getSpec) {
    const ref = signal.ref();
    const ready = signal(false);
    const state = {
        chart: null,
        canvas: null,
        signature: "",
    };

    function destroy() {
        if (state.chart) {
            state.chart.destroy();
        }
        state.chart = null;
        state.canvas = null;
        state.signature = "";
    }

    let disposed = false;

    useEffect(() => {
        const canvas = ref();
        const isReady = ready();
        const spec = canvas ? getSpec() : null;
        if (!canvas || !spec) {
            destroy();
            return;
        }
        if (typeof Chart === "undefined") {
            destroy();
            ensureChartJs().then((ok) => {
                if (!disposed && ok && !ready()) {
                    ready.set(true);
                }
            });
            return;
        }
        if (!isReady) {
            ready.set(true);
        }
        const signature = spec.signature || JSON.stringify([spec.type, spec.data]);
        if (
            state.chart &&
            state.canvas === canvas &&
            state.chart.config.type === spec.type
        ) {
            if (signature !== state.signature) {
                state.signature = signature;
                state.chart.data = spec.data;
                state.chart.options = spec.options;
                state.chart.update(prefersReducedMotion() ? "none" : undefined);
            }
            return;
        }
        destroy();
        state.canvas = canvas;
        state.signature = signature;
        state.chart = new Chart(canvas, {
            type: spec.type,
            data: spec.data,
            options: spec.options,
        });
    });

    onWillUnmount(() => {
        disposed = true;
        destroy();
    });

    return { ref, ready };
}

/**
 * Build Chart.js spec for Stacked Bar Chart:
 * - Admin Mode (`bar.kind === "department"`): "Tình hình công việc" by department.
 * - Employee Mode (`bar.kind === "daily"`): "Công việc của tôi theo ngày" by deadline date
 *   (with explicit "Chưa đặt hạn" bar when undated tasks exist, and valid 0s on empty days).
 */
export function buildDepartmentBarSpec(chartsData, onBarClick) {
    if (!chartsData || chartsData.status !== "ok") {
        return null;
    }
    const rows = chartsData.bar?.rows || [];
    if (!rows.length) {
        return null;
    }
    const isDaily = chartsData.bar?.kind === "daily";
    const motion = !prefersReducedMotion();
    const labels = rows.map((r) => (isDaily ? r.day_label : r.department_name));
    const doneValues = rows.map((r) => r.done_count);
    const openValues = rows.map((r) => r.incomplete_count);
    const periodLabel = chartsData.period_label || "";
    const denseAxis = rows.length > 10;

    return {
        type: "bar",
        signature: JSON.stringify([
            "bar",
            isDaily ? "daily" : "dept",
            periodLabel,
            chartsData.scope_key,
            chartsData.department_key,
            rows,
        ]),
        data: {
            labels,
            datasets: [
                {
                    label: "Hoàn thành",
                    segmentKey: "done",
                    data: doneValues,
                    backgroundColor: "#4E7DE8",
                    hoverBackgroundColor: "#3A68D8",
                    borderRadius: (ctx) => {
                        const openVal = openValues[ctx.dataIndex] || 0;
                        return openVal > 0
                            ? { topLeft: 0, topRight: 0, bottomLeft: 4, bottomRight: 4 }
                            : 5;
                    },
                    borderSkipped: false,
                    maxBarThickness: denseAxis ? 20 : 38,
                    categoryPercentage: denseAxis ? 0.76 : 0.62,
                    barPercentage: 0.86,
                },
                {
                    label: "Chưa hoàn thành",
                    segmentKey: "incomplete",
                    data: openValues,
                    backgroundColor: "#BBD4FA",
                    hoverBackgroundColor: "#9EC1F7",
                    borderRadius: { topLeft: 5, topRight: 5, bottomLeft: 0, bottomRight: 0 },
                    borderSkipped: false,
                    maxBarThickness: denseAxis ? 20 : 38,
                    categoryPercentage: denseAxis ? 0.76 : 0.62,
                    barPercentage: 0.86,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: motion ? { duration: 200, easing: "easeOutCubic" } : false,
            interaction: { mode: "index", intersect: false },
            onHover: (event, elements) => {
                const target = event?.native?.target;
                if (target) {
                    const row = elements.length ? rows[elements[0].index] : null;
                    target.style.cursor = row && row.total_count > 0 ? "pointer" : "default";
                }
            },
            onClick: (_event, elements, chart) => {
                if (!elements?.length || typeof onBarClick !== "function") {
                    return;
                }
                const hit = elements[0];
                const row = rows[hit.index];
                const ds = chart.data.datasets[hit.datasetIndex];
                if (!row || row.total_count <= 0) {
                    return;
                }
                const seg = ds?.segmentKey || "";
                if (isDaily) {
                    onBarClick({ dayKey: row.day_key, departmentKey: "", segmentKey: seg });
                } else {
                    onBarClick({ departmentKey: row.department_key, dayKey: "", segmentKey: seg });
                }
            },
            scales: {
                x: {
                    stacked: true,
                    grid: { display: false },
                    border: { color: "#E2EAF5" },
                    ticks: {
                        color: "#344863",
                        font: { family: '"Segoe UI", system-ui, sans-serif', size: 11.5, weight: "600" },
                        maxRotation: 40,
                        minRotation: 0,
                        autoSkip: denseAxis,
                        maxTicksLimit: denseAxis ? 10 : undefined,
                    },
                },
                y: {
                    stacked: true,
                    beginAtZero: true,
                    suggestedMax: 4,
                    border: { display: false },
                    grid: { color: "#ECF2FA" },
                    ticks: {
                        precision: 0,
                        maxTicksLimit: 5,
                        color: "#526580",
                        font: { family: '"Segoe UI", system-ui, sans-serif', size: 11 },
                    },
                },
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: "rgba(23, 43, 77, 0.95)",
                    padding: 10,
                    cornerRadius: 9,
                    titleFont: { size: 12.5, weight: "700" },
                    bodyFont: { size: 12 },
                    callbacks: {
                        title: (items) => {
                            const idx = items?.[0]?.dataIndex ?? 0;
                            const row = rows[idx];
                            if (!row) {
                                return "";
                            }
                            return isDaily
                                ? row.full_label || row.day_label
                                : `${row.department_name} (${periodLabel})`;
                        },
                        label: (ctx) => {
                            const row = rows[ctx.dataIndex];
                            const val = ctx.parsed.y ?? 0;
                            const tot = row?.total_count || 0;
                            return ` ${ctx.dataset.label}: ${val} / ${tot} công việc`;
                        },
                        afterBody: () =>
                            isDaily
                                ? ["Phân bố theo hạn hoàn thành trong kỳ"]
                                : [],
                        footer: (items) => {
                            const idx = items?.[0]?.dataIndex ?? 0;
                            return (rows[idx]?.total_count || 0) > 0
                                ? "Bấm cột để mở danh sách công việc"
                                : "Ngày này chưa có công việc";
                        },
                    },
                },
            },
        },
    };
}

export const buildTaskBarSpec = buildDepartmentBarSpec;

/**
 * Build Chart.js spec for the Status Ratio Donut Chart ("Tỷ lệ công việc" / "Tỷ lệ công việc của tôi").
 */
export function buildStatusDonutSpec(chartsData, onSliceClick) {
    if (!chartsData || chartsData.status !== "ok") {
        return null;
    }
    const slices = chartsData.donut?.slices || [];
    const total = chartsData.donut?.center_count ?? 0;
    const motion = !prefersReducedMotion();
    const periodLabel = chartsData.period_label || "";
    const scopeLabel = chartsData.scope_label || "";
    const diffNote = chartsData.donut?.note || "";

    if (total <= 0) {
        return {
            type: "doughnut",
            signature: JSON.stringify(["donut-empty", chartsData.mode, periodLabel, scopeLabel]),
            data: {
                labels: ["Chưa có công việc"],
                datasets: [
                    {
                        data: [1],
                        backgroundColor: ["#E6EEF8"],
                        borderWidth: 0,
                        hoverOffset: 0,
                    },
                ],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: "68%",
                animation: false,
                events: [],
                plugins: {
                    legend: { display: false },
                    tooltip: { enabled: false },
                },
            },
        };
    }

    return {
        type: "doughnut",
        signature: JSON.stringify([
            "donut",
            chartsData.mode,
            periodLabel,
            scopeLabel,
            chartsData.department_key,
            slices,
        ]),
        data: {
            labels: slices.map((s) => s.label),
            datasets: [
                {
                    data: slices.map((s) => s.count),
                    backgroundColor: slices.map((s) => s.color),
                    borderColor: "#FFFFFF",
                    borderWidth: 2,
                    hoverOffset: 4,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: "68%",
            animation: motion ? { duration: 220, easing: "easeOutCubic" } : false,
            onHover: (event, elements) => {
                const target = event?.native?.target;
                if (target) {
                    target.style.cursor = elements.length ? "pointer" : "default";
                }
            },
            onClick: (_event, elements) => {
                if (!elements?.length || typeof onSliceClick !== "function") {
                    return;
                }
                const hit = elements[0];
                const slice = slices[hit.index];
                if (slice && slice.count > 0) {
                    onSliceClick(slice.key);
                }
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: "rgba(23, 43, 77, 0.95)",
                    padding: 10,
                    cornerRadius: 9,
                    titleFont: { size: 12.5, weight: "700" },
                    bodyFont: { size: 12 },
                    callbacks: {
                        title: (items) => {
                            const idx = items?.[0]?.dataIndex ?? 0;
                            return slices[idx]?.label || "";
                        },
                        label: (ctx) => {
                            const s = slices[ctx.dataIndex];
                            if (!s) {
                                return "";
                            }
                            return ` Số lượng: ${s.count} việc (${s.exact_percent}%)`;
                        },
                        afterLabel: () => ` Phạm vi: ${scopeLabel} · ${periodLabel}`,
                        footer: () =>
                            diffNote
                                ? "Bấm lát biểu đồ để mở danh sách tương ứng"
                                : "Bấm lát biểu đồ để mở danh sách",
                    },
                },
            },
        },
    };
}
