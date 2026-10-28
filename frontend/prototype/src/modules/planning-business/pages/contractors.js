import { escapeHtml, money } from '../../../shared/formatters.js';
import { horizontalBars } from '../../../shared/charts.js';
import { panel, emptyState } from '../../../shared/ui.js';
import { ledger, option, tableRows, financeTable, alertList } from '../components.js';
import { getScope, totalMetrics, allocations, getAlerts } from '../repository.js';

export function renderContractors(snapshot, state) {
    const all = snapshot.items.filter((item) => item.projectId === state.projectId && item.side === 'contractor');
    if (!all.length) return panel('Thầu phụ và giao khoán', '', emptyState('Chưa có giao khoán', 'Chọn dự án khác để xem dữ liệu mẫu.'));
    const scope = getScope(snapshot, state, 'contractor');
    const totals = totalMetrics(scope.filter((item) => item.level === 1));
    const childTotal = totalMetrics(scope.filter((item) => item.level === 2));
    const rows = tableRows(scope, state, 'contractor');
    const ids = new Set(scope.map((item) => item.id));
    const alerts = getAlerts(snapshot, state.projectId).filter((alert) => alert.side === 'contractor' && ids.has(alert.itemId));
    const allocation = allocations(snapshot, state.projectId).filter((entry) => ids.has(entry.parent.id) || scope.some((item) => item.parentId === entry.parent.id));

    const topFilterBar = `
        <div class="tp-page-filter-bar">
            <div class="tp-field">
                <label for="unit-filter">Phạm vi đơn vị</label>
                <select class="tp-select" id="unit-filter" data-field="contractorId">
                    ${option('', 'Tất cả đơn vị', state.contractorId)}
                    ${all.map((item) => option(item.id, item.name, state.contractorId)).join('')}
                </select>
            </div>
            <div class="tp-field">
                <label for="level-filter">Cấp giao khoán</label>
                <select class="tp-select" id="level-filter" data-field="level">
                    ${option('', 'Tất cả các cấp', state.level)}
                    ${option('1', 'Cấp 1 · tổng công ty', state.level)}
                    ${option('2', 'Cấp 2 · của phòng', state.level)}
                </select>
            </div>
        </div>
    `;

    const charts = allocation.length ? allocation.map((entry) => `
        <div class="tp-allocation-card">
            <div class="tp-allocation-header">
                <span class="tp-allocation-badge">Khoán nội bộ phòng</span>
                <h4 class="tp-allocation-name">${escapeHtml(entry.parent.name)}</h4>
            </div>
            ${horizontalBars([
                { label: 'Khoán phòng (Cấp 1)', value: entry.parent.contract, color: '#16526d' },
                { label: 'Phòng ký cấp 2', value: entry.subcontracted, color: '#0c9fb5' }
            ])}
            <div class="tp-allocation-balance">
                <span>Còn để giao khoán tiếp</span>
                <strong class="${entry.remaining < 0 ? 'is-negative' : ''}">
                    ${entry.remaining < 0 ? 'Vượt khoán ' : ''}${money(entry.remaining)} tỷ
                </strong>
            </div>
        </div>
    `).join('') : emptyState('Không có khoán nội bộ trong phạm vi chọn', 'Chọn phòng giao khoán hoặc đơn vị cấp 2 để xem phân bổ.');

    const tableHeading = `
        <div class="tp-table-section-head">
            <div>
                <h2 class="tp-section-title">Sổ thầu phụ và giao khoán</h2>
                <p class="tp-section-caption">Hiển thị ${rows.length}/${scope.length} dòng. Cấp 1 tính vào tổng công ty; Cấp 2 theo dõi riêng.</p>
            </div>
            <div class="tp-table-controls">
                <div class="tp-field">
                    <label for="table-search">Tìm kiếm</label>
                    <input type="search" id="table-search" class="tp-input" data-field="search" value="${escapeHtml(state.search)}" placeholder="Tên đơn vị, hạng mục…">
                </div>
                <div class="tp-field">
                    <label for="table-sort">Sắp xếp</label>
                    <select id="table-sort" class="tp-select" data-field="sort">
                        ${option('name', 'Tên đơn vị', state.sort)}
                        ${option('balance', 'Còn theo NT giảm dần', state.sort)}
                        ${option('contract', 'Hợp đồng giảm dần', state.sort)}
                    </select>
                </div>
                <button class="tp-button" data-action="reset-filters">Xóa lọc</button>
            </div>
        </div>
    `;

    return `
        ${topFilterBar}
        <div class="tp-dual-grid">
            ${ledger('Cấp 1 · tổng công ty trong phạm vi chọn', totals, 'contractor', 'Thầu phụ trực tiếp và khoán nội bộ · tỷ đồng')}
            ${ledger('Cấp 2 · theo dõi riêng trong phạm vi chọn', childTotal, 'contractor', 'Không cộng thêm vào tổng công ty · tỷ đồng')}
        </div>
        <div class="tp-section-heading">
            <h2 class="tp-section-title">Phân cấp và đối chiếu</h2>
        </div>
        <div class="tp-chart-grid">
            ${panel('Khoán của phòng', 'Toàn bộ khoán mẹ và cấp 2 thuộc phòng được chọn; không thay đổi bởi tìm kiếm bảng', charts)}
            ${panel('Điểm cần giải thích', 'Trong phạm vi đơn vị và cấp đang chọn', alertList(alerts))}
        </div>
        ${tableHeading}
        ${panel('Cấu trúc giao khoán', 'Tổng cấp 1 và cấp 2 được tính riêng, không cộng cha và con', financeTable(rows, totals, 'contractor', 'Đơn vị và hạng mục trong phạm vi chọn', { hierarchy: true, allItems: all }))}
    `;
}

