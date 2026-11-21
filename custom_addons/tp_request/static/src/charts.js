/** @odoo-module **/
import { onMounted, onPatched, onWillStart, onWillUnmount, signal } from "@odoo/owl";
import { loadBundle } from "@web/core/assets";
import { browser } from "@web/core/browser/browser";

export function isReducedMotion() {
    try {
        return Boolean(
            browser.matchMedia?.("(prefers-reduced-motion: reduce)").matches ||
                document.body.classList.contains("o_tp_req_reduce_motion")
        );
    } catch {
        return false;
    }
}

let chartLoadPromise = null;

export function loadChartJs() {
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

export function baseChartOptions(extra = {}) {
    const motion = !isReducedMotion();
    return {
        responsive: true,
        maintainAspectRatio: false,
        animation: motion ? { duration: 220, easing: "easeOutCubic" } : false,
        ...extra,
        plugins: {
            legend: { display: false },
            tooltip: {
                backgroundColor: "rgba(15, 23, 42, 0.94)",
                padding: 10,
                cornerRadius: 8,
                titleFont: { weight: "600", size: 13 },
                bodyFont: { size: 13 },
            },
            ...(extra.plugins || {}),
        },
    };
}

export function useRequestChart(getSpec) {
    const ref = signal.ref();
    const state = { chart: null, canvas: null, signature: "", ready: false };

    function destroy() {
        if (state.chart) {
            state.chart.destroy();
        }
        Object.assign(state, { chart: null, canvas: null, signature: "" });
    }

    function sync() {
        const canvas = state.ready ? ref() : null;
        const spec = canvas ? getSpec() : null;
        if (!canvas || !spec) {
            destroy();
            return;
        }
        const signature = JSON.stringify([
            spec.type,
            spec.data?.labels || [],
            (spec.data?.datasets || []).map((ds) => [ds.data, ds.backgroundColor]),
        ]);
        if (state.chart && state.canvas === canvas && state.chart.config.type === spec.type) {
            if (signature !== state.signature) {
                state.signature = signature;
                state.chart.data.labels = spec.data.labels;
                state.chart.data.datasets = spec.data.datasets;
                state.chart.options = spec.options;
                state.chart.update();
            }
            return;
        }
        destroy();
        Object.assign(state, { canvas, signature, chart: new Chart(canvas, spec) });
    }

    onWillStart(async () => {
        state.ready = await loadChartJs();
    });
    onMounted(sync);
    onPatched(sync);
    onWillUnmount(destroy);
    return { ref, ready: () => state.ready };
}
