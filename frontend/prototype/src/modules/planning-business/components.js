import { escapeHtml, money, percent, normalize } from '../../shared/formatters.js';
import { emptyState, kpiCard, statusFor } from '../../shared/ui.js';

export function ledger(title, totals, side = 'investor', note = '') {
    const isInvestor = side === 'investor';
    const balanceSub = isInvestor ? 'NT − Đã thu · tỷ đồng' : 'NT − Đã trả · tỷ đồng';
    const balanceClass = totals.balance < 0 ? 'attention' : '';
    const progressPercent = Math.min(100, Math.max(0, Math.round((totals.contractRatio || 0) * 100)));
    return `<section class="tp-ledger-block ${isInvestor ? '' : 'contractor'}"><div class="tp-ledger-head"><div><h3 class="tp-ledger-name">${escapeHtml(title)}</h3><p class="tp-ledger-note">${escapeHtml(note || (isInvestor ? 'Giá trị công việc và tiền nhận từ chủ đầu tư' : 'Tổng công ty chỉ tính cấp 1'))}</p></div><span class="tp-ledger-mark" aria-hidden="true"></span></div><div class="tp-kpi-grid">${kpiCard('Hợp đồng cập nhật', money(totals.contract), 'Tỷ đồng')}${kpiCard('Đã nghiệm thu', money(totals.accepted), 'Tỷ đồng')}${kpiCard(isInvestor ? 'Tiền đã thu' : 'Tiền đã trả', money(totals.paid), `Tiền / nghiệm thu: ${percent(totals.paidRatio)}`)}${kpiCard('Còn theo nghiệm thu', money(totals.balance), balanceSub, balanceClass)}</div><div class="tp-ledger-footer"><div class="tp-ledger-progress-meta"><span>${isInvestor ? 'Tiền thu' : 'Tiền trả'} / hợp đồng</span><div class="tp-ledger-progress-bar"><div class="tp-ledger-progress-fill" style="width:${progressPercent}%"></div></div></div><strong>${percent(totals.contractRatio)}</strong></div></section>`;
}

export function option(value, label, current) {
    return `<option value="${escapeHtml(value)}"${String(value) === String(current) ? ' selected' : ''}>${escapeHtml(label)}</option>`;
}

export function tableRows(items, state, side) {
    let rows = items.filter((item) => normalize(`${item.name} ${item.work || ''}`).includes(normalize(state.search || '')));
    if (state.sort === 'balance') rows = [...rows].sort((a, b) => b.balance - a.balance);
    else if (state.sort === 'contract') rows = [...rows].sort((a, b) => b.contract - a.contract);
    else rows = [...rows].sort((a, b) => a.name.localeCompare(b.name, 'vi'));
    return rows;
}

export function financeTable(rows, totals, side, caption = '', options = {}) {
    if (!rows.length) return emptyState('Không có dòng phù hợp', 'Thử đổi lựa chọn hoặc xóa nội dung tìm kiếm.');
    const isInvestor = side === 'investor';
    const row = (item) => `<tr class="${item.level === 2 ? 'row-child' : ''}"><th scope="row"><button class="tp-text-button" data-action="drill" data-side="${side}" data-id="${escapeHtml(item.id)}">${escapeHtml(item.name)}</button>${item.work ? `<span class="tp-table-subtext">${escapeHtml(item.work)}</span>` : ''}</th>${!isInvestor ? `<td class="tp-cell-label"><span class="tp-level-badge ${item.level === 2 ? 'level-two' : 'level-one'}">Cấp ${item.level}</span><span class="tp-table-subtext">${escapeHtml(item.type)}</span></td>` : ''}<td>${money(item.contract)}</td><td>${money(item.accepted)}</td><td>${money(item.paid)}</td>${isInvestor ? `<td>${money(item.retention)}</td>` : ''}<td class="${item.balance < 0 ? 'is-negative' : ''}">${money(item.balance)}</td><td class="tp-cell-label">${statusFor(item)}</td></tr>`;
    let body = '';
    if (options.hierarchy) {
        const shown = new Set();
        for (const item of rows) {
            if (shown.has(item.id)) continue;
            if (item.parentId && !shown.has(item.parentId)) {
                const parent = rows.find((entry) => entry.id === item.parentId);
                if (parent) { body += row(parent); shown.add(parent.id); }
                else { const context = options.allItems.find((entry) => entry.id === item.parentId); body += `<tr class="tp-context-row"><th colspan="8">Thuộc ${escapeHtml(context?.name || 'phòng giao khoán')} <span class="tp-table-subtext">Ngữ cảnh cấp 1 · không nằm trong tổng phạm vi chọn</span></th></tr>`; shown.add(item.parentId); }
            }
            body += row(item); shown.add(item.id);
            if (item.level === 1) for (const child of rows.filter((entry) => entry.parentId === item.id)) { body += row(child); shown.add(child.id); }
        }
    } else body = rows.map(row).join('');
    return `<div class="tp-table-wrap" tabindex="0" role="region" aria-label="Bảng số liệu tài chính, có thể cuộn ngang"><table class="tp-table"><caption>${escapeHtml(caption)} · Đơn vị: tỷ đồng</caption><thead><tr><th scope="col">${isInvestor ? 'Hạng mục' : 'Đơn vị / hạng mục'}</th>${!isInvestor ? '<th scope="col">Phân cấp</th>' : ''}<th scope="col">HĐ cập nhật</th><th scope="col">Nghiệm thu</th><th scope="col">${isInvestor ? 'Đã thu' : 'Đã trả'}</th>${isInvestor ? '<th scope="col">Giữ lại</th>' : ''}<th scope="col">Còn theo NT</th><th scope="col">Trạng thái</th></tr></thead><tbody>${body}</tbody><tfoot><tr><th scope="row">${isInvestor ? 'Tổng phạm vi chọn' : 'Tổng cấp 1 trong phạm vi chọn'}</th>${!isInvestor ? '<td></td>' : ''}<td>${money(totals.contract)}</td><td>${money(totals.accepted)}</td><td>${money(totals.paid)}</td>${isInvestor ? `<td>${money(totals.retention)}</td>` : ''}<td class="${totals.balance < 0 ? 'is-negative' : ''}">${money(totals.balance)}</td><td class="tp-cell-label"><span class="tp-status-badge ${totals.balance < 0 ? 'warning' : 'success'}">${totals.balance < 0 ? 'Cần giải thích' : 'Cân đối'}</span></td></tr></tfoot></table></div>`;
}

export const legends = (labels, colors = ['#17324d', '#2f6a76']) => `<div class="tp-chart-legend">${labels.map((label, index) => `<span class="tp-legend-item"><span class="tp-legend-dot" style="background:${colors[index]}"></span>${escapeHtml(label)}</span>`).join('')}</div>`;

export function alertList(alerts) {
    return alerts.length ? `<ul class="tp-alert-list">${alerts.map((alert) => `<li class="tp-alert-item ${alert.kind}"><div><p class="tp-alert-title"><button class="tp-text-button" data-action="drill" data-side="${alert.side}" data-id="${escapeHtml(alert.itemId)}">${escapeHtml(alert.title)}</button>${alert.amount === null ? '' : ` <span class="tp-alert-amount">${money(alert.amount)} tỷ</span>`}</p><p class="tp-alert-copy">${escapeHtml(alert.message)}</p></div></li>`).join('')}</ul>` : emptyState('Chưa có điểm cần đối chiếu', 'Các kiểm tra hiện tại chưa phát hiện chênh lệch cần giải thích.');
}
