import { money, fullMoney, escapeHtml } from './formatters.js';

const max = (values) => Math.max(...values.map((value) => value || 0), 1);
const chartWidth = () => typeof window !== 'undefined' && window.innerWidth <= 560 ? 380 : 650;

export function groupedBars(series, options = {}) {
    const width = options.width || chartWidth(); const height = options.height || 235; const left = 46; const top = 18; const bottom = 33;
    const values = series.flatMap((item) => item.values).filter((value) => value !== null);
    const domainMin = Math.min(0, ...values);
    const domainMax = max(values);
    const chartHeight = height - top - bottom; const barGroup = (width - left - 8) / Math.max(series.length, 1); const scale = chartHeight / (domainMax - domainMin);
    const zeroY = top + domainMax * scale;
    const colors = options.colors || ['#17324d', '#2f6a76'];
    const groups = series.map((item, index) => {
        const barWidth = Math.max(8, Math.min(24, barGroup / (item.values.length + 1.6)));
        const groupWidth = item.values.length * barWidth + (item.values.length - 1) * 7;
        const x = left + index * barGroup + (barGroup - groupWidth) / 2;
        return `<g><text x="${left + index * barGroup + barGroup / 2}" y="${height - 10}" text-anchor="middle" class="chart-label">${escapeHtml(item.label)}</text>${item.values.map((value, valueIndex) => {
            const barHeight = Math.abs(value || 0) * scale; const bx = x + valueIndex * (barWidth + 7); const by = value < 0 ? zeroY : zeroY - barHeight;
            const description = `${item.label}${options.seriesLabels?.[valueIndex] ? ` · ${options.seriesLabels[valueIndex]}` : ''}: ${fullMoney(value)}`;
            const valY = value < 0 ? zeroY + barHeight + 11 : by - 4;
            const valLabel = value !== null && barWidth >= 12 ? `<text x="${bx + barWidth / 2}" y="${valY}" text-anchor="middle" class="chart-axis chart-bar-num" font-size="9">${money(value)}</text>` : '';
            return `<rect class="chart-bar" tabindex="0" x="${bx}" y="${by}" width="${barWidth}" height="${Math.max(2, barHeight)}" rx="3" fill="${colors[valueIndex % colors.length]}"><title>${escapeHtml(description)}</title></rect>${valLabel}`;
        }).join('')}</g>`;
    }).join('');
    const grid = [0, .25, .5, .75, 1].map((tick) => { const y = top + chartHeight - tick * chartHeight; return `<line x1="${left}" x2="${width - 6}" y1="${y}" y2="${y}" class="chart-grid-line"/><text x="${left - 8}" y="${y + 4}" text-anchor="end" class="chart-axis">${money(domainMin + (domainMax - domainMin) * tick)}</text>`; }).join('');
    return `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${escapeHtml(options.label || 'Biểu đồ cột nhóm')}">${grid}${groups}</svg>`;
}

export function horizontalBars(rows, options = {}) {
    const width = options.width || chartWidth(); const rowHeight = 31; const height = Math.max(95, rows.length * rowHeight + 18); const labelWidth = options.labelWidth || (width < 500 ? 116 : 152); const barWidth = width - labelWidth - 55; const scale = barWidth / max(rows.map((row) => row.value));
    return `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${escapeHtml(options.label || 'Biểu đồ thanh ngang')}">${rows.map((row, index) => { const y = index * rowHeight + 7; return `<text x="0" y="${y + 14}" class="chart-axis">${escapeHtml(row.label)}</text><rect class="chart-bar" tabindex="0" x="${labelWidth}" y="${y}" width="${Math.max(2, (row.value || 0) * scale)}" height="18" rx="2" fill="${row.color || '#1d98ae'}"><title>${escapeHtml(row.label)}: ${money(row.value)} tỷ</title></rect><text x="${Math.min(width - 3, labelWidth + (row.value || 0) * scale + 8)}" y="${y + 14}" class="chart-axis chart-value">${money(row.value)}</text>`; }).join('')}</svg>`;
}

export function donutChart(rows, options = {}) {
    const size = options.size || 190;
    const center = size / 2;
    const radius = options.radius || 62;
    const circumference = 2 * Math.PI * radius;
    const total = options.total || rows.reduce((sum, row) => sum + (row.value || 0), 0);
    let offset = 0;
    const arcs = rows.map((row) => {
        const length = total > 0 ? circumference * (row.value || 0) / total : 0;
        const arc = `<circle class="donut-segment" tabindex="0" cx="${center}" cy="${center}" r="${radius}" fill="none" stroke="${row.color || '#0c9fb5'}" stroke-width="22" stroke-dasharray="${length} ${circumference - length}" stroke-dashoffset="${-offset}" transform="rotate(-90 ${center} ${center})"><title>${escapeHtml(row.label)}: ${money(row.value)} tỷ</title></circle>`;
        offset += length;
        return arc;
    }).join('');
    return `<svg class="tp-donut" viewBox="0 0 ${size} ${size}" role="img" aria-label="${escapeHtml(options.label || 'Cơ cấu theo hạng mục')}"><circle cx="${center}" cy="${center}" r="${radius}" fill="none" stroke="#dce7ea" stroke-width="22"/>${arcs}<text x="${center}" y="${center - 3}" text-anchor="middle" class="donut-total">${money(total)}</text><text x="${center}" y="${center + 17}" text-anchor="middle" class="donut-label">tỷ đồng</text></svg>`;
}

export function trendLine(rows, options = {}) {
    const width = options.width || chartWidth(); const height = options.height || 220; const left = 40; const right = 12; const top = 16; const bottom = 32; const maxValue = max(rows.flatMap((row) => [row.accepted || 0, row.paid || 0])); const innerW = width - left - right; const innerH = height - top - bottom;
    const pointPairs = (key) => rows.map((row, index) => [left + (rows.length === 1 ? innerW / 2 : index * innerW / (rows.length - 1)), top + innerH - ((row[key] || 0) / maxValue) * innerH]);
    const points = (key) => pointPairs(key).map(([x, y]) => `${x},${y}`).join(' ');
    const xlabels = rows.map((row, index) => `<text x="${left + (rows.length === 1 ? innerW / 2 : index * innerW / (rows.length - 1))}" y="${height - 10}" text-anchor="middle" class="chart-axis">${escapeHtml(row.label)}</text>`).join('');
    const grid = [0, .25, .5, .75, 1].map((tick) => { const y = top + innerH - tick * innerH; return `<line x1="${left}" x2="${width - right}" y1="${y}" y2="${y}" class="chart-grid-line"/><text x="${left - 8}" y="${y + 4}" text-anchor="end" class="chart-axis">${money(maxValue * tick)}</text>`; }).join('');
    const acceptedPoints = pointPairs('accepted');
    const acceptedColor = options.colors?.[0] || '#0c9fb5';
    const paidColor = options.colors?.[1] || '#132f45';
    const gradId = 'tpTrendGradient';
    const defs = `<defs><linearGradient id="${gradId}" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="${acceptedColor}" stop-opacity="0.32"/><stop offset="100%" stop-color="${acceptedColor}" stop-opacity="0.02"/></linearGradient></defs>`;
    const area = options.area ? `<polygon points="${acceptedPoints.map(([x, y]) => `${x},${y}`).join(' ')} ${left + innerW},${top + innerH} ${left},${top + innerH}" fill="url(#${gradId})"/>` : '';
    return `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="${escapeHtml(options.label || 'Xu hướng nghiệm thu và thanh toán')}">${defs}${grid}${area}<polyline points="${points('accepted')}" fill="none" stroke="${acceptedColor}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/><polyline points="${points('paid')}" fill="none" stroke="${paidColor}" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>${rows.map((row, index) => { const x = left + (rows.length === 1 ? innerW / 2 : index * innerW / (rows.length - 1)); return `<circle class="chart-point" tabindex="0" cx="${x}" cy="${top + innerH - ((row.accepted || 0) / maxValue) * innerH}" r="4.5" fill="${acceptedColor}" stroke="#ffffff" stroke-width="2"><title>${escapeHtml(row.label)} · nghiệm thu: ${money(row.accepted)} tỷ</title></circle><circle class="chart-point" tabindex="0" cx="${x}" cy="${top + innerH - ((row.paid || 0) / maxValue) * innerH}" r="4.5" fill="${paidColor}" stroke="#ffffff" stroke-width="2"><title>${escapeHtml(row.label)} · thanh toán: ${money(row.paid)} tỷ</title></circle>`; }).join('')}${xlabels}</svg>`;
}
