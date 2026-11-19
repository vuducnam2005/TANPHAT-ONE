import { onMounted, onPatched, onWillStart, onWillUnmount, signal } from "@odoo/owl";
import { loadBundle } from "@web/core/assets";
import { browser } from "@web/core/browser/browser";

/**
 * ENTI-ATTENDANCE-002: Chart.js for the attendance screens, loaded lazily (Odoo's own ``web.chartjs_lib``
 * bundle, only when a screen with charts opens). Unlike ``useChart`` (which destroys and re-creates the chart on
 * every patch), a chart here is created once and then updated in place, so an automatic refresh moves the bars
 * instead of redrawing the whole canvas; animation is off for "giảm chuyển động" / prefers-reduced-motion.
 */
export const CHART_COLORS = {
    main: "#2563EB", in: "#0D9488", out: "#7C3AED", warn: "#D97706", danger: "#DC2626", none: "#64748B",
    grid: "#E2E8F0", text: "#334155", muted: "#64748B",
};

export function reducedMotion() {
    try {
        return Boolean(browser.matchMedia?.("(prefers-reduced-motion: reduce)").matches
            || document.querySelector(".o_tp_hr_reduce_motion"));
    } catch {
        return false;
    }
}

/** Shared look: Odoo font, quiet grid, 240 ms motion (none when reduced). */
export function baseOptions(extra = {}) {
    const motion = !reducedMotion();
    return {
        responsive: true,
        maintainAspectRatio: false,
        animation: motion ? { duration: 240, easing: "easeOutCubic" } : false,
        transitions: { active: { animation: { duration: motion ? 120 : 0 } } },
        interaction: { mode: "index", intersect: false },
        ...extra,
        plugins: {
            legend: { display: false },
            tooltip: {
                backgroundColor: "rgba(15, 23, 42, 0.92)", padding: 10, cornerRadius: 8, boxPadding: 4,
                titleFont: { weight: "600" }, bodyFont: { size: 13 },
            },
            ...(extra.plugins || {}),
        },
    };
}

let chartLoad = null;

/** Load Chart.js once per page; ``false`` when it cannot be loaded (the screens keep their text figures). */
export function loadCharts() {
    if (!chartLoad) {
        chartLoad = loadBundle("web.chartjs_lib").then(() => typeof Chart !== "undefined", () => {
            chartLoad = null;
            return false;
        });
    }
    return chartLoad;
}

/**
 * One live chart bound to a canvas ref. ``getSpec()`` returns ``{type, data, options}`` or ``null`` (nothing to
 * draw). The chart is created once and its data are patched in place on later renders; it is re-created only
 * when the canvas element or the chart type changes.
 */
export function useLiveChart(getSpec) {
    const ref = signal.ref();
    const live = { chart: null, canvas: null, json: "", ready: false };

    function destroy() {
        if (live.chart) {
            live.chart.destroy();
        }
        Object.assign(live, { chart: null, canvas: null, json: "" });
    }

    function sync() {
        const canvas = live.ready ? ref() : null;
        const spec = canvas ? getSpec() : null;
        if (!canvas || !spec) {
            destroy();
            return;
        }
        const json = JSON.stringify([spec.data.labels, spec.data.datasets.map((set) => [set.data, set.backgroundColor])]);
        if (live.chart && live.canvas === canvas && live.chart.config.type === spec.type) {
            if (json !== live.json) {
                live.json = json;
                const target = live.chart.data;
                target.labels = spec.data.labels;
                spec.data.datasets.forEach((set, index) => {
                    if (target.datasets[index]) {
                        Object.assign(target.datasets[index], set);
                    } else {
                        target.datasets.push(set);
                    }
                });
                target.datasets.length = spec.data.datasets.length;
                live.chart.options = spec.options;
                live.chart.update();
            }
            return;
        }
        destroy();
        Object.assign(live, { canvas, json, chart: new Chart(canvas, spec) });
    }

    onWillStart(async () => {
        live.ready = await loadCharts();
    });
    onMounted(sync);
    onPatched(sync);
    onWillUnmount(destroy);
    return { ref, instance: () => live.chart, ready: () => live.ready };
}
