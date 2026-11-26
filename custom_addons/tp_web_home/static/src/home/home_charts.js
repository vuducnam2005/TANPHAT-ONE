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
 * Build Chart.js spec for the Stacked Department Bar Chart ("Tình hình công việc", Section 10.1).
 */
export function buildDepartmentBarSpec(chartsData, onBarClick) {
    if (!chartsData || chartsData.status !== "ok") {
        return null;
    }
    const rows = chartsData.bar?.rows || [];
    if (!rows.length) {
        return null;
    }
    const motion = !prefersReducedMotion();
    const labels = rows.map((r) => r.department_name);
    const doneValues = rows.map((r) => r.done_count);
    const openValues = rows.map((r) => r.incomplete_count);
    const periodLabel = chartsData.period_label || "";

    return {
        type: "bar",
        signature: JSON.stringify(["bar", periodLabel, chartsData.scope_key, chartsData.department_key, rows]),
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
                            ? { topLeft: 0, topRight: 0, bottomLeft: 5, bottomRight: 5 }
                            : 6;
                    },
                    borderSkipped: false,
                    maxBarThickness: 44,
                    categoryPercentage: 0.62,
                    barPercentage: 0.85,
                },
                {
                    label: "Chưa hoàn thành",
                    segmentKey: "incomplete",
                    data: openValues,
                    backgroundColor: "#BBD4FA",
                    hoverBackgroundColor: "#9EC1F7",
                    borderRadius: { topLeft: 6, topRight: 6, bottomLeft: 0, bottomRight: 0 },
                    borderSkipped: false,
                    maxBarThickness: 44,
                    categoryPercentage: 0.62,
                    barPercentage: 0.85,
                },
            ],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: motion ? { duration: 220, easing: "easeOutCubic" } : false,
            interaction: { mode: "index", intersect: false },
            onHover: (event, elements) => {
                const target = event?.native?.target;
                if (target) {
                    target.style.cursor = elements.length ? "pointer" : "default";
                }
            },
            onClick: (_event, elements, chart) => {
                if (!elements?.length || typeof onBarClick !== "function") {
                    return;
                }
                const hit = elements[0];
                const row = rows[hit.index];
                const ds = chart.data.datasets[hit.datasetIndex];
                if (row) {
                    onBarClick(row.department_key, ds?.segmentKey || "");
                }
            },
            scales: {
                x: {
                    stacked: true,
                    grid: { display: false },
                    border: { color: "#E2EAF5" },
                    ticks: {
                        color: "#344863",
                        font: { family: '"Segoe UI", system-ui, sans-serif', size: 12.5, weight: "600" },
                        maxRotation: 0,
                        autoSkip: false,
                    },
                },
                y: {
                    stacked: true,
                    beginAtZero: true,
                    border: { display: false },
                    grid: { color: "#ECF2FA" },
                    ticks: {
                        precision: 0,
                        color: "#526580",
                        font: { family: '"Segoe UI", system-ui, sans-serif', size: 12 },
                    },
                },
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: "rgba(23, 43, 77, 0.95)",
                    padding: 11,
                    cornerRadius: 10,
                    titleFont: { size: 13, weight: "700" },
                    bodyFont: { size: 12.5 },
                    callbacks: {
                        title: (items) => {
                            const idx = items?.[0]?.dataIndex ?? 0;
                            const row = rows[idx];
                            return row
                                ? `${row.department_name} (${periodLabel})`
                                : "";
                        },
                        label: (ctx) => {
                            const row = rows[ctx.dataIndex];
                            const val = ctx.parsed.y ?? 0;
                            const tot = row?.total_count || 0;
                            return ` ${ctx.dataset.label}: ${val} / ${tot} công việc`;
                        },
                        footer: () => "Bấm cột để mở danh sách công việc",
                    },
                },
            },
        },
    };
}

/**
 * Build Chart.js spec for the Status Ratio Donut Chart ("Tỷ lệ công việc", Section 10.2).
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

    if (total <= 0) {
        return {
            type: "doughnut",
            signature: JSON.stringify(["donut-empty", periodLabel, scopeLabel]),
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
        signature: JSON.stringify(["donut", periodLabel, scopeLabel, chartsData.department_key, slices]),
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
            animation: motion ? { duration: 240, easing: "easeOutCubic" } : false,
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
                    padding: 11,
                    cornerRadius: 10,
                    titleFont: { size: 13, weight: "700" },
                    bodyFont: { size: 12.5 },
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
                        footer: () => "Bấm lát biểu đồ để mở danh sách",
                    },
                },
            },
        },
    };
}
