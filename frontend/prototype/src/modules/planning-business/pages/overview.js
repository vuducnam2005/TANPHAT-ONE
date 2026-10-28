import { escapeHtml, fullMoney, money, safeSum, date, percent } from '../../../shared/formatters.js';
import { groupedBars, horizontalBars, trendLine, donutChart } from '../../../shared/charts.js';
import { panel, emptyState } from '../../../shared/ui.js';
import { ledger, legends, alertList } from '../components.js';
import { totalMetrics, allocations, getAlerts } from '../repository.js';

const investorColor = '#2858a3';
const contractorColor = '#128779';

function monthlyMovement(snapshot, projectId, side, contractorItems) {
    const months = [];
    const end = new Date(`${snapshot.asOf}T12:00:00`);
    for (let index = 5; index >= 0; index--) {
        const current = new Date(end.getFullYear(), end.getMonth() - index, 1);
        const key = `${current.getFullYear()}-${String(current.getMonth() + 1).padStart(2, '0')}`;
        const records = snapshot.effective.filter((row) => row.projectId === projectId && row.side === side && row.date.startsWith(key)
            && (side === 'investor' || contractorItems.has(row.itemId)));
        months.push({ label: `T${current.getMonth() + 1}`, accepted: safeSum(records.map((row) => row.accepted)), paid: safeSum(records.map((row) => row.paid)) });
    }
    return months;
}

export function renderOverview(snapshot, state) {
    const project = snapshot.projects.find((entry) => entry.id === state.projectId);
    const items = snapshot.items.filter((entry) => entry.projectId === project.id);
    const investorItems = items.filter((item) => item.side === 'investor');
    const contractorItems = items.filter((item) => item.side === 'contractor' && item.level === 1);
    const investor = totalMetrics(investorItems);
    const contractors = totalMetrics(contractorItems);
    const hero = `<section class="tp-project-banner"><div class="tp-project-banner-copy"><div class="tp-project-code">${escapeHtml(project.code)} <span class="tp-chip">${escapeHtml(project.phase)}</span></div><h2>${escapeHtml(project.name)}</h2><p>${escapeHtml(project.investor)}<span class="tp-project-location">${escapeHtml(project.location)}</span></p></div><button class="tp-button tp-project-detail-button" data-action="project-detail">Chi tiết dự án <span aria-hidden="true">↗</span></button></section>`;
    if (!items.length) return hero + panel('Sổ dự án', 'Dự án mẫu chưa có phát sinh', emptyState('Chưa có số liệu tài chính', 'Chọn dự án Đông Thành hoặc An Bình để xem dashboard có dữ liệu.'));
    const alerts = getAlerts(snapshot, project.id);
    const allocation = allocations(snapshot, project.id);
    const side = state.overviewSide || 'investor';
    const monthly = monthlyMovement(snapshot, project.id, side, new Set(contractorItems.map((item) => item.id)));
    const monthlyTable = `<details class="tp-chart-data"><summary>Xem số liệu theo tháng</summary><table class="tp-mini-table"><caption>Đơn vị: tỷ đồng · bản ghi hiệu lực hiện tại</caption><thead><tr><th scope="col">Tháng</th><th scope="col">Nghiệm thu</th><th scope="col">Thanh toán</th></tr></thead><tbody>${monthly.map((row) => `<tr><th scope="row">${row.label}</th><td>${money(row.accepted)}</td><td>${money(row.paid)}</td></tr>`).join('')}</tbody></table></details>`;
    const movementChart = `<section class="tp-panel tp-movement-panel"><div class="tp-panel-heading"><div><h3 class="tp-panel-title">Nhịp nghiệm thu & thanh toán</h3><p class="tp-panel-caption">6 tháng gần nhất · phát sinh theo tháng ghi sổ · tỷ đồng</p></div><div class="tp-segmented" role="group" aria-label="Sổ theo dõi trên biểu đồ"><button data-action="overview-side" data-side="investor" aria-pressed="${side === 'investor'}">Chủ đầu tư</button><button data-action="overview-side" data-side="contractor" aria-pressed="${side === 'contractor'}">Cấp 1</button></div></div><div class="tp-chart-wrap">${trendLine(monthly, { area: true, height: 225, colors: [investorColor, '#13a593'], label: `Nghiệm thu và thanh toán 6 tháng. ${side === 'investor' ? 'Sổ chủ đầu tư' : 'Sổ thầu phụ và khoán cấp 1'}. Đơn vị tỷ đồng.` })}</div>${legends(['Nghiệm thu', side === 'investor' ? 'Tiền đã thu' : 'Tiền đã trả'], [investorColor, '#13a593'])}${monthlyTable}<p class="tp-chart-footnote">Bản ghi hiệu lực phân bổ theo ngày ghi sổ; không phải số dư lịch sử.</p></section>`;
    const composition = investorItems.map((item, index) => ({ label: item.name, value: item.accepted, color: [investorColor, '#13a593', '#e0a43a'][index % 3], id: item.id, side: 'investor' }));
    const compositionChart = panel('Cơ cấu nghiệm thu', 'Theo hạng mục chủ đầu tư · tỷ đồng', `<div class="tp-donut-layout">${donutChart(composition, { total: investor.accepted, label: 'Tổng nghiệm thu' })}<div class="tp-donut-legend">${composition.map((row) => `<button class="tp-donut-legend-item" data-action="drill" data-side="investor" data-id="${escapeHtml(row.id)}"><span class="tp-legend-dot" style="background:${row.color}"></span><span>${escapeHtml(row.label)}</span><strong>${money(row.value)}</strong></button>`).join('')}</div></div>`, 'tp-composition-panel');
    const comparison = groupedBars(['Hợp đồng', 'Nghiệm thu', 'Thanh toán', 'Còn theo NT'].map((label, index) => ({ label, values: [investor[['contract', 'accepted', 'paid', 'balance'][index]], contractors[['contract', 'accepted', 'paid', 'balance'][index]]] })), { colors: [investorColor, contractorColor], seriesLabels: ['Chủ đầu tư', 'Thầu phụ & khoán cấp 1'], height: 230, label: 'So sánh chủ đầu tư và thầu phụ cấp 1. Đơn vị tỷ đồng.' });
    const comparisonChart = panel('Hợp đồng, nghiệm thu và dòng tiền', 'Hai sổ cùng phạm vi dự án · tỷ đồng', `<div class="tp-chart-wrap">${comparison}</div>${legends(['Chủ đầu tư', 'Thầu phụ & khoán cấp 1'], [investorColor, contractorColor])}<details class="tp-chart-data"><summary>Xem bảng số liệu biểu đồ</summary><table class="tp-mini-table"><caption>Đơn vị: tỷ đồng</caption><tr><th scope="col">Chỉ tiêu</th><th scope="col">CĐT</th><th scope="col">Cấp 1</th></tr>${['contract', 'accepted', 'paid', 'balance'].map((key, index) => `<tr><th scope="row">${['Hợp đồng', 'Nghiệm thu', 'Thanh toán', 'Còn theo NT'][index]}</th><td>${money(investor[key])}</td><td>${money(contractors[key])}</td></tr>`).join('')}</table></details>`);
    const allocationBody = allocation.map((entry) => `<div class="tp-allocation-title"><span class="tp-level-badge level-one">Khoán nội bộ</span><strong>${escapeHtml(entry.parent.name)}</strong></div>${horizontalBars([{ label: 'Khoán phòng', value: entry.parent.contract, color: contractorColor }, { label: 'Phòng ký cấp 2', value: entry.subcontracted, color: '#e0a43a' }], { width: 400, label: 'Khoán phòng và giá trị ký cấp 2, không cộng hai thanh' })}<div class="tp-allocation-balance"><span>Còn để giao khoán</span><strong class="${entry.remaining < 0 ? 'is-negative' : ''}">${money(entry.remaining)} tỷ</strong></div><p class="tp-panel-caption">Cấp 2 thuộc phần triển khai của phòng, theo dõi riêng với tổng công ty.</p>`).join('');
    const notesCard = panel('Chỉ tiêu & Khả dụng tiền', 'Đối soát tiền giữ lại & công nợ CĐT · tỷ đồng', `<div class="tp-split-list"><div class="tp-split-row"><span class="tp-split-label">Tiền giữ lại bảo hành CĐT</span><strong class="tp-split-value">${money(investor.retention)} tỷ</strong></div><div class="tp-split-row"><span class="tp-split-label">Khả dụng thu sau giữ lại</span><strong class="tp-split-value">${money(investor.afterRetention)} tỷ</strong></div><div class="tp-split-row"><span class="tp-split-label">Tỷ lệ thu hồi / Nghiệm thu</span><strong class="tp-split-value">${percent(investor.paidRatio)}</strong></div></div><div class="tp-notes-card-foot"><p class="tp-panel-caption">Số âm phản ánh tạm ứng hoặc nghiệm thu chưa ghi sổ.</p><button class="tp-button tp-btn-xs" data-action="formulas">Xem chú giải công thức ↗</button></div>`);
    return `${hero}<div class="tp-section-heading"><div><h2 class="tp-section-title">Tình hình dự án</h2><p class="tp-section-caption">Lũy kế đến ${date(snapshot.asOf)} · Đơn vị: tỷ đồng</p></div><button class="tp-text-button" data-action="formulas">Xem cách tính</button></div><div class="tp-dual-grid tp-overview-ledgers">${ledger('Chủ đầu tư', investor, 'investor', 'Hợp đồng, nghiệm thu và tiền đã thu')}${ledger('Thầu phụ & giao khoán', contractors, 'contractor', 'Tổng công ty · chỉ tính cấp 1')}</div><div class="tp-analytics-grid">${movementChart}${compositionChart}</div><div class="tp-chart-grid tp-secondary-charts">${comparisonChart}${panel('Phân bổ khoán nội bộ', 'Khoán mẹ và cấp 2 được đối chiếu riêng · tỷ đồng', allocationBody)}</div><div class="tp-section-heading"><div><h2 class="tp-section-title">Cần đối chiếu <span class="tp-count-badge">${alerts.length}</span></h2><p class="tp-section-caption">Các điểm cần giải thích từ số liệu đang chọn</p></div></div><div class="tp-dual-grid">${panel('Theo hạng mục và đơn vị', 'Mở một mục để xem giao dịch hiệu lực', alertList(alerts))}${notesCard}</div>`;
}
