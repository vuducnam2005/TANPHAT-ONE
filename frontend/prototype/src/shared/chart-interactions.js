// Delegated events keep tooltips working after page rerenders without chart instances.
export function setupChartTooltips(root) {
    const tooltip = document.createElement('div');
    tooltip.id = 'tp-chart-tooltip';
    tooltip.className = 'tp-chart-tooltip';
    tooltip.setAttribute('role', 'tooltip');
    tooltip.hidden = true;
    document.body.append(tooltip);
    let activeMark;
    const marks = '.chart-bar, .chart-point, .donut-segment';

    function hide() {
        activeMark?.removeAttribute('aria-describedby');
        activeMark = undefined;
        tooltip.hidden = true;
    }

    function position(x, y) {
        const box = tooltip.getBoundingClientRect();
        const left = Math.max(12, Math.min(x + 12, window.innerWidth - box.width - 12));
        const top = y + box.height + 25 < window.innerHeight ? y + 16 : Math.max(12, y - box.height - 12);
        tooltip.style.left = `${left}px`;
        tooltip.style.top = `${top}px`;
    }

    function show(event) {
        const mark = event.target.closest(marks);
        if (!mark) return;
        activeMark?.removeAttribute('aria-describedby');
        activeMark = mark;
        const title = mark.querySelector('title');
        tooltip.textContent = title?.textContent || '';
        tooltip.hidden = !tooltip.textContent;
        mark.setAttribute('aria-describedby', tooltip.id);
        const bounds = mark.getBoundingClientRect();
        position(event.clientX ?? bounds.left + bounds.width / 2, event.clientY ?? bounds.top);
    }

    root.addEventListener('pointerover', show);
    root.addEventListener('focusin', show);
    root.addEventListener('pointermove', (event) => { if (activeMark && !tooltip.hidden) position(event.clientX, event.clientY); });
    root.addEventListener('pointerout', (event) => { if (event.target.closest(marks) && !event.relatedTarget?.closest?.(marks)) hide(); });
    root.addEventListener('focusout', hide);
    root.addEventListener('keydown', (event) => { if (event.key === 'Escape') hide(); });
    window.addEventListener('scroll', () => {
        if (!activeMark) return;
        const bounds = activeMark.getBoundingClientRect();
        if (bounds.bottom < 0 || bounds.top > window.innerHeight) hide();
        else position(bounds.left + bounds.width / 2, bounds.top + bounds.height / 2);
    }, { passive: true });
    window.addEventListener('resize', hide);
    return hide;
}
