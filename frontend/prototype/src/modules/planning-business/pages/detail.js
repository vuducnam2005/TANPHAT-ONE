import { escapeHtml, money, date, normalize, safeSum } from '../../../shared/formatters.js';
import { trendLine } from '../../../shared/charts.js';
import { panel, emptyState } from '../../../shared/ui.js';
import { ledger, option, legends } from '../components.js';
import { streamKey, totalMetrics } from '../repository.js';

export function detailScope(snapshot, state) {
    return snapshot.items.filter((item) => item.projectId === state.projectId && (state.detailSide === 'all' || item.side === state.detailSide) && (!state.entityId || item.id === state.entityId));
}

export function visibleTransactions(snapshot, state) {
    const scope = detailScope(snapshot, state);
    const keys = new Set(scope.map((item) => `${item.side}:${item.id}`));
    const transactions = state.transactionTab === 'history' ? snapshot.transactions : snapshot.effective;
    return transactions.filter((row) => row.projectId === state.projectId && keys.has(`${row.side}:${row.itemId}`) && (!state.from || row.date >= state.from) && (!state.to || row.date <= state.to) && normalize(`${row.description} ${row.rootId}`).includes(normalize(state.transactionSearch || ''))).sort((a, b) => b.date.localeCompare(a.date) || b.sourceRow - a.sourceRow);
}

export function renderDetail(snapshot, state) {
    const project = snapshot.projects.find((entry) => entry.id === state.projectId);
    const all = snapshot.items.filter((item) => item.projectId === state.projectId);
    if (!all.length) return panel('Chi tiết dự án', '', emptyState('Dự án chưa có phát sinh', 'Chọn Đông Thành hoặc An Bình để thử xem giao dịch.'));
    const scope = detailScope(snapshot, state);
    const entity = all.find((item) => item.id === state.entityId);
    const heading = entity?.name || project.name;
    const caption = entity ? `${entity.side === 'investor' ? 'Chủ đầu tư' : `${entity.type} · Cấp ${entity.level}`} · ${entity.work || 'Chi tiết hạng mục'}` : 'Hai sổ được trình bày riêng · không cộng chủ đầu tư với thầu phụ';

    const heroBadge = entity
        ? `<span class="tp-hero-status-pill"><span class="tp-live-dot"></span>${entity.side === 'investor' ? 'Hạng mục CĐT' : `Đơn vị Cấp ${entity.level}`}</span>`
        : `<span class="tp-hero-status-pill"><span class="tp-live-dot"></span>Hồ sơ toàn dự án</span>`;

    const backButton = entity
        ? `<button class="tp-btn-hero" data-action="project-detail">← Về toàn dự án</button>`
        : '';

    const hero = `
        <div class="tp-hero-banner tp-detail-hero">
            <div class="tp-hero-content">
                <div class="tp-hero-meta">
                    ${heroBadge}
                    <span class="tp-hero-code">${escapeHtml(project.code || 'DA-2601')}</span>
                </div>
                <h2 class="tp-hero-title">${escapeHtml(heading)}</h2>
                <p class="tp-hero-sub">${escapeHtml(caption)}</p>
            </div>
            ${backButton ? `<div class="tp-hero-action">${backButton}</div>` : ''}
        </div>
        <div class="tp-page-filter-bar">
            <div class="tp-field">
                <label for="detail-side">Sổ theo dõi</label>
                <select class="tp-select" id="detail-side" data-field="detailSide">
                    ${option('all', 'Cả hai sổ', state.detailSide)}
                    ${option('investor', 'Sổ Chủ đầu tư', state.detailSide)}
                    ${option('contractor', 'Sổ Thầu phụ & giao khoán', state.detailSide)}
                </select>
            </div>
            <div class="tp-field">
                <label for="detail-entity">Hạng mục / đơn vị</label>
                <select class="tp-select" id="detail-entity" data-field="entityId">
                    ${option('', 'Tất cả trong sổ đã chọn', state.entityId)}
                    ${all.filter((item) => state.detailSide === 'all' || item.side === state.detailSide).map((item) => option(item.id, `${item.side === 'investor' ? 'CĐT' : `Cấp ${item.level}`} · ${item.name}`, state.entityId)).join('')}
                </select>
            </div>
            <button class="tp-button" data-action="project-detail">Xem toàn dự án</button>
        </div>
    `;

    const investor = scope.filter((item) => item.side === 'investor');
    const contractors = scope.filter((item) => item.side === 'contractor' && item.level === 1);
    const children = scope.filter((item) => item.side === 'contractor' && item.level === 2);
    const ledgers = `${investor.length ? ledger('Sổ chủ đầu tư', totalMetrics(investor)) : ''}${contractors.length ? ledger('Thầu phụ & khoán cấp 1', totalMetrics(contractors), 'contractor') : ''}${children.length ? ledger('Cấp 2 · theo dõi riêng', totalMetrics(children), 'contractor', 'Không cộng cấp 2 vào tổng công ty') : ''}`;

    const tabs = `
        <div class="tp-tabs" role="group" aria-label="Chọn loại dữ liệu giao dịch">
            ${[
                ['effective', 'Giao dịch hiệu lực', 'Bản ghi mới nhất'],
                ['history', 'Lịch sử phiên bản', 'Vết sửa đổi & huỷ'],
                ['documents', 'Hồ sơ chứng từ', 'Đồng bộ Odoo']
            ].map(([id, title, sub]) => `
                <button class="tp-tab ${state.transactionTab === id ? 'is-active' : ''}" aria-pressed="${state.transactionTab === id}" data-action="tab" data-tab="${id}">
                    <span class="tp-tab-title">${title}</span>
                    <span class="tp-tab-sub">${sub}</span>
                </button>
            `).join('')}
        </div>
    `;

    const topSection = `
        ${hero}
        <p class="tp-section-caption tp-snapshot-note">KPI lũy kế đến 27/10/2026. Bộ lọc ngày và tìm kiếm bên dưới áp dụng trực tiếp cho giao dịch và biểu đồ trong tab.</p>
        <div class="tp-dual-grid">${ledgers}</div>
        <div class="tp-section-heading">
            <h2 class="tp-section-title">Hồ sơ phát sinh & giao dịch</h2>
        </div>
        ${tabs}
    `;

    if (state.transactionTab === 'documents') {
        const docEmpty = `
            <div class="tp-doc-empty-state">
                <div class="tp-doc-icon-wrap">
                    <svg width="42" height="42" viewBox="0 0 24 24" fill="none" stroke="#0c9fb5" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                        <polyline points="14 2 14 8 20 8"></polyline>
                        <line x1="16" y1="13" x2="8" y2="13"></line>
                        <line x1="16" y1="17" x2="8" y2="17"></line>
                        <polyline points="10 9 9 9 8 9"></polyline>
                    </svg>
                </div>
                <h3 class="tp-doc-empty-title">Kho chứng từ liên kết trực tiếp với Odoo</h3>
                <p class="tp-doc-empty-desc">Khi triển khai vào phân hệ Odoo, toàn bộ hợp đồng gốc, phụ lục, biên bản nghiệm thu (BBNT) và chứng từ ngân hàng sẽ được tự động đính kèm theo mã giao dịch.</p>
                <div class="tp-doc-preview-grid">
                    <div class="tp-doc-preview-card">
                        <span class="tp-doc-tag tag-contract">Hợp đồng</span>
                        <strong>HĐ-2601/ĐT-Tổ hợp</strong>
                        <span>Bản scan ký số · PDF (4.2 MB)</span>
                    </div>
                    <div class="tp-doc-preview-card">
                        <span class="tp-doc-tag tag-bbnt">Biên bản nghiệm thu</span>
                        <strong>BBNT đợt 2 - Khảo sát</strong>
                        <span>Đã ký 3 bên · PDF (2.1 MB)</span>
                    </div>
                    <div class="tp-doc-preview-card">
                        <span class="tp-doc-tag tag-unc">Ủy nhiệm chi</span>
                        <strong>UNC-BIDV-99214</strong>
                        <span>Xác nhận hạch toán (1.2 MB)</span>
                    </div>
                </div>
            </div>
        `;
        return topSection + panel('Hồ sơ & Chứng từ đính kèm', 'Chứng từ quét thực tế tương ứng với các mã giao dịch', docEmpty);
    }

    const invalidRange = state.from && state.to && state.from > state.to;
    const rows = invalidRange ? [] : visibleTransactions(snapshot, state);
    const txFilters = `
        <div class="tp-transaction-filter-card">
            <div class="tp-tx-filter-group">
                <div class="tp-field">
                    <label for="date-from">Từ ngày</label>
                    <input class="tp-input" type="date" id="date-from" data-field="from" value="${escapeHtml(state.from)}">
                </div>
                <div class="tp-field">
                    <label for="date-to">Đến ngày</label>
                    <input class="tp-input" type="date" id="date-to" data-field="to" value="${escapeHtml(state.to)}">
                </div>
                <div class="tp-field tp-search-field">
                    <label for="transaction-search">Tìm giao dịch</label>
                    <input class="tp-input" type="search" id="transaction-search" data-field="transactionSearch" value="${escapeHtml(state.transactionSearch)}" placeholder="Nội dung hoặc mã gốc…">
                </div>
            </div>
            <button class="tp-button tp-btn-reset-tx" data-action="reset-dates">Xóa lọc giao dịch</button>
        </div>
        ${invalidRange ? '<p class="tp-validation" role="alert">Ngày bắt đầu phải trước hoặc bằng ngày kết thúc.</p>' : ''}
    `;

    const effectiveKeys = new Set(snapshot.effective.map((row) => `${streamKey(row)}:${row.sequence}`));
    const names = new Map(all.map((item) => [`${item.side}:${item.id}`, `${item.name}${item.level ? ` · Cấp ${item.level}` : ''}`]));

    const table = rows.length ? `
        <div class="tp-table-wrap" tabindex="0" role="region" aria-label="Bảng giao dịch, có thể cuộn ngang">
            <table class="tp-table tp-transaction-table">
                <caption>${rows.length} bản ghi · Đơn vị: tỷ đồng${state.transactionTab === 'history' ? ' · Lịch sử không dùng để cộng số tài chính' : ''}</caption>
                <thead>
                    <tr>
                        <th scope="col">Ngày / nội dung</th>
                        <th scope="col">Sổ / hạng mục</th>
                        <th scope="col">HĐ gốc</th>
                        <th scope="col">HĐ thay thế</th>
                        <th scope="col">Nghiệm thu</th>
                        <th scope="col">Thanh toán</th>
                        <th scope="col">Phiên bản</th>
                    </tr>
                </thead>
                <tbody>
                    ${rows.map((row) => {
                        const active = effectiveKeys.has(`${streamKey(row)}:${row.sequence}`);
                        let statusClass = 'success';
                        let statusText = 'Hiệu lực';
                        if (row.operation === 'delete') {
                            statusClass = 'danger';
                            statusText = 'Đã hủy';
                        } else if (!active) {
                            statusClass = 'warning';
                            statusText = 'Đã thay / hủy';
                        }
                        const isInvestor = row.side === 'investor';
                        return `
                            <tr>
                                <th scope="row">
                                    <span class="tp-tx-date">${date(row.date)}</span>
                                    <span class="tp-tx-description">${escapeHtml(row.description)}</span>
                                    <span class="tp-table-subtext tp-code-tag">${escapeHtml(row.rootId)}</span>
                                </th>
                                <td class="tp-cell-label">
                                    <span class="tp-chip ${isInvestor ? 'tp-chip-investor' : 'tp-chip-contractor'}">${isInvestor ? 'Chủ đầu tư' : 'Thầu phụ / khoán'}</span>
                                    <span class="tp-table-subtext">${escapeHtml(names.get(`${row.side}:${row.itemId}`))}</span>
                                </td>
                                <td>${row.contractOriginal > 0 ? `<strong class="tp-val-primary">${money(row.contractOriginal)}</strong>` : '<span class="tp-val-muted">0</span>'}</td>
                                <td>${row.contractReplacement > 0 ? `<strong class="tp-val-primary">${money(row.contractReplacement)}</strong>` : '<span class="tp-val-muted">—</span>'}</td>
                                <td>${row.accepted > 0 ? `<strong class="tp-val-accepted">${money(row.accepted)}</strong>` : '<span class="tp-val-muted">0</span>'}</td>
                                <td>${row.paid > 0 ? `<strong class="tp-val-paid">${money(row.paid)}</strong>` : '<span class="tp-val-muted">0</span>'}</td>
                                <td class="tp-cell-label">
                                    <span class="tp-table-subtext">Lần ${row.sequence}</span>
                                    <span class="tp-status-badge ${statusClass}">${statusText}</span>
                                </td>
                            </tr>
                        `;
                    }).join('')}
                </tbody>
            </table>
        </div>
    ` : emptyState('Không có giao dịch phù hợp', invalidRange ? 'Sửa khoảng ngày để tiếp tục.' : 'Xóa bộ lọc ngày hoặc nội dung tìm kiếm để xem lại giao dịch.');

    let chart = '';
    if (state.detailSide !== 'all' && state.transactionTab === 'effective' && rows.length) {
        const levelOneOnly = state.detailSide === 'contractor' && !state.entityId;
        const chartRows = levelOneOnly ? rows.filter((row) => all.some((item) => item.id === row.itemId && item.side === row.side && item.level === 1)) : rows;
        const months = [...new Set(chartRows.map((row) => row.date.slice(0, 7)))].sort();
        const series = months.map((month) => ({
            label: `T${Number(month.slice(5))}`,
            accepted: safeSum(chartRows.filter((row) => row.date.startsWith(month)).map((row) => row.accepted)),
            paid: safeSum(chartRows.filter((row) => row.date.startsWith(month)).map((row) => row.paid))
        }));
        chart = panel(
            levelOneOnly ? 'Phát sinh cấp 1 theo tháng ghi sổ' : 'Phát sinh theo tháng ghi sổ',
            'Các bản hiệu lực hiện tại trong phạm vi ngày và tìm kiếm · tỷ đồng',
            `
                <div class="tp-chart-wrap">${trendLine(series)}</div>
                ${legends(['Nghiệm thu', 'Thanh toán'], ['#1d98ae', '#17324d'])}
                <details class="tp-chart-data">
                    <summary>Xem số liệu theo tháng</summary>
                    <table class="tp-mini-table">
                        <caption>Đơn vị: tỷ đồng</caption>
                        <tr><th scope="col">Tháng</th><th scope="col">NT</th><th scope="col">Thanh toán</th></tr>
                        ${series.map((row) => `<tr><th scope="row">${row.label}</th><td>${money(row.accepted)}</td><td>${money(row.paid)}</td></tr>`).join('')}
                    </table>
                </details>
                <p class="tp-panel-caption">Biểu đồ phân bổ bản ghi hiệu lực theo ngày ghi sổ, không phải số dư đã biết ở từng thời điểm.${levelOneOnly ? ' Chỉ tính cấp 1; giao dịch cấp 2 vẫn hiện riêng trong bảng để đối chiếu.' : ''}</p>
            `
        );
    }

    return `
        ${topSection}
        ${txFilters}
        ${chart}
        ${panel(
            state.transactionTab === 'history' ? 'Lịch sử đầy đủ các phiên bản' : 'Các giao dịch đang có hiệu lực',
            state.transactionTab === 'history' ? 'Bản thay thế và bản hủy vẫn được giữ để đối chiếu; không cộng các dòng lịch sử.' : 'Mỗi mã gốc chỉ lấy phiên bản có số thứ tự lớn nhất; mã đã hủy được loại khỏi số liệu.',
            table
        )}
    `;
}

