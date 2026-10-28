import { createFixtures } from './data.js';
import { ratio, safeSum, subtract } from '../../shared/formatters.js';

export const streamKey = (row) => `${row.projectId}:${row.side}:${row.rootId}`;

export function effectiveTransactions(transactions) {
    const latest = new Map();
    for (const row of transactions) {
        const current = latest.get(streamKey(row));
        if (!current || Number(row.sequence) > Number(current.sequence)) latest.set(streamKey(row), row);
    }
    return [...latest.values()].filter((row) => row.operation !== 'delete');
}

export function summarizeItem(item, transactions) {
    const rows = transactions.filter((row) => row.projectId === item.projectId && row.side === item.side && row.itemId === item.id);
    const sum = (field) => safeSum(rows.map((row) => row[field]));
    const latestReplacement = rows.filter((row) => row.contractReplacement > 0).sort((a, b) => b.sourceRow - a.sourceRow)[0];
    const contractOriginal = sum('contractOriginal');
    const contract = latestReplacement?.contractReplacement ?? contractOriginal;
    const accepted = sum('accepted');
    const paid = sum('paid');
    const production = item.productionKnown ? sum('production') : null;
    const retention = sum('retention');
    return { ...item, contractOriginal, contract, accepted, paid, production, retention,
        balance: subtract(accepted, paid), afterRetention: subtract(subtract(accepted, paid), retention),
        unaccepted: production === null || production === 0 ? null : subtract(production, accepted),
        contractBalance: subtract(contract, paid), paidRatio: ratio(paid, accepted) };
}

export function totalMetrics(items) {
    const totals = Object.fromEntries(['contractOriginal', 'contract', 'accepted', 'paid', 'production', 'retention', 'balance', 'afterRetention', 'unaccepted', 'contractBalance'].map((field) => [field, safeSum(items.map((item) => item[field]))]));
    return { ...totals, paidRatio: ratio(totals.paid, totals.accepted), contractRatio: ratio(totals.paid, totals.contract) };
}

export function getScope(snapshot, state, side) {
    const items = snapshot.items.filter((item) => item.projectId === state.projectId && item.side === side);
    return items.filter((item) => (!state.itemId || item.id === state.itemId) && (!state.contractorId || item.id === state.contractorId)
        && (!state.level || String(item.level) === state.level));
}

export function allocations(snapshot, projectId) {
    return snapshot.items.filter((item) => item.projectId === projectId && item.type === 'Khoán nội bộ').map((parent) => {
        const children = snapshot.items.filter((item) => item.projectId === projectId && item.parentId === parent.id);
        const subcontracted = safeSum(children.map((item) => item.contract));
        return { parent, subcontracted, remaining: subtract(parent.contract, subcontracted) };
    });
}

export function getAlerts(snapshot, projectId) {
    const items = snapshot.items.filter((item) => item.projectId === projectId);
    const alerts = [];
    for (const item of items.filter((row) => row.balance < 0)) alerts.push({ itemId: item.id, side: item.side, title: item.name,
        message: `${item.side === 'investor' ? 'Tiền đã thu' : 'Tiền đã trả'} vượt nghiệm thu. Có thể gồm tạm ứng hoặc nghiệm thu chưa cập nhật.`, amount: -item.balance, kind: 'warning' });
    for (const allocation of allocations(snapshot, projectId).filter((row) => row.remaining < 0)) alerts.push({ itemId: allocation.parent.id, side: 'contractor', title: allocation.parent.name,
        message: 'Giá trị ký cấp 2 vượt khoán phòng. Cần đối chiếu phạm vi giao khoán.', amount: -allocation.remaining, kind: 'danger' });
    for (const item of items.filter((row) => row.production === null)) alerts.push({ itemId: item.id, side: item.side, title: item.name,
        message: 'Chưa cập nhật sản lượng. Chỉ tiêu khối lượng chưa nghiệm thu chưa đủ dữ liệu.', amount: null, kind: 'warning' });
    return alerts;
}

export async function loadSnapshot() {
    // Odoo adapter belongs here. Keep raw ledger rules out of presentation components.
    const fixture = createFixtures();
    const effective = effectiveTransactions(fixture.transactions);
    const items = fixture.items.map((item) => summarizeItem(item, effective));
    return { ...fixture, items, effective, id: 'demo-20261027', asOf: '2026-10-27', loadedAt: new Date().toISOString(), source: 'synthetic-demo' };
}
