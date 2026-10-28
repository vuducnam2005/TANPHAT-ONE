import { escapeHtml, fullMoney, money } from './formatters.js';

export const kpiCard = (label, value, detail = '', className = '') => `<article class="tp-kpi-card ${className}"><span class="tp-kpi-label">${escapeHtml(label)}</span><strong class="tp-kpi-value">${value}</strong><span class="tp-kpi-detail">${escapeHtml(detail)}</span></article>`;

export const panel = (title, caption, body, className = '') => `<section class="tp-panel ${className}"><div class="tp-panel-heading"><div><h3 class="tp-panel-title">${escapeHtml(title)}</h3>${caption ? `<p class="tp-panel-caption">${escapeHtml(caption)}</p>` : ''}</div></div>${body}</section>`;

export const sourceBadge = () => '<span class="tp-source-badge">Bản xem thử · dữ liệu mẫu</span>';
export const emptyState = (title, copy) => `<div class="tp-empty"><strong>${escapeHtml(title)}</strong><span>${escapeHtml(copy)}</span></div>`;
export const moneyCell = (value, className = '') => `<span class="${className}">${value === null ? '—' : `${money(value)} tỷ`}</span>`;
export function statusFor(item) {
    const [kind, text] = item.balance === null ? ['warning', 'Chưa đủ dữ liệu']
        : item.balance < 0 ? ['warning', 'Vượt NT · cần giải thích']
        : item.accepted === 0 && item.contract > 0 ? ['warning', 'Chưa nghiệm thu']
        : item.afterRetention > 0 ? ['warning', 'Còn theo NT']
        : item.balance > 0 ? ['warning', 'Chỉ còn giữ lại'] : ['success', 'Đã đủ theo NT'];
    return `<span class="tp-status-badge ${kind}">${text}</span>`;
}
export const detailSummary = (item) => `<div class="tp-split-list"><div class="tp-split-row"><span class="tp-split-label">HĐ cập nhật</span><strong class="tp-split-value">${fullMoney(item.contract)}</strong></div><div class="tp-split-row"><span class="tp-split-label">Nghiệm thu</span><strong class="tp-split-value">${fullMoney(item.accepted)}</strong></div><div class="tp-split-row"><span class="tp-split-label">Đã thanh toán</span><strong class="tp-split-value">${fullMoney(item.paid)}</strong></div><div class="tp-split-row"><span class="tp-split-label">Còn theo NT</span><strong class="tp-split-value">${fullMoney(item.balance)}</strong></div></div>`;
