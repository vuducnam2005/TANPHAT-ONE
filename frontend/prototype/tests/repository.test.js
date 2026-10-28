import test from 'node:test';
import assert from 'node:assert/strict';
import { loadSnapshot, effectiveTransactions, summarizeItem, totalMetrics, getScope, allocations } from '../src/modules/planning-business/repository.js';
import { ratio, safeSum } from '../src/shared/formatters.js';
import { visibleTransactions } from '../src/modules/planning-business/pages/detail.js';

test('numeric sequence, project and side isolate effective roots; deletion removes root', () => {
    const rows = [
        { projectId: 'a', side: 'investor', rootId: 'r', sequence: 2 },
        { projectId: 'a', side: 'investor', rootId: 'r', sequence: 10 },
        { projectId: 'b', side: 'investor', rootId: 'r', sequence: 1 },
        { projectId: 'a', side: 'contractor', rootId: 'r', sequence: 1 },
        { projectId: 'a', side: 'investor', rootId: 'deleted', sequence: 1 },
        { projectId: 'a', side: 'investor', rootId: 'deleted', sequence: 2, operation: 'delete' },
    ];
    assert.deepEqual(effectiveTransactions(rows).map((row) => [row.projectId, row.side, row.sequence]), [['a', 'investor', 10], ['b', 'investor', 1], ['a', 'contractor', 1]]);
});

test('latest positive appendix in source order replaces contract, not adds to it', () => {
    const base = { projectId: 'a', side: 'investor', itemId: 'x', contractOriginal: 0, contractReplacement: 0, production: 0, accepted: 0, paid: 0, retention: 0 };
    const item = { projectId: 'a', side: 'investor', id: 'x', productionKnown: true };
    const summary = summarizeItem(item, [
        { ...base, contractOriginal: 100, sourceRow: 1 },
        { ...base, contractReplacement: 130, sourceRow: 2, date: '2026-10-01' },
        { ...base, contractReplacement: 120, sourceRow: 3, date: '2026-01-01' },
        { ...base, contractReplacement: 0, sourceRow: 4 },
    ]);
    assert.equal(summary.contract, 120);
    assert.equal(summary.unaccepted, null);
});

test('fixture reconciliation: sums use current versions and exclude cancelled payment', async () => {
    const snapshot = await loadSnapshot();
    const investor = totalMetrics(snapshot.items.filter((item) => item.projectId === 'dong-thanh' && item.side === 'investor'));
    assert.equal(investor.contract, 28_400_000_000);
    assert.equal(investor.accepted, 15_700_000_000);
    assert.equal(investor.paid, 14_000_000_000);
    assert.equal(investor.balance, 1_700_000_000);
    assert.equal(investor.retention, 785_000_000);
    assert.equal(investor.afterRetention, 915_000_000);
    assert.equal(investor.production, null);
    assert.equal(investor.unaccepted, null);
    assert.equal(investor.paidRatio, 14 / 15.7);
});

test('company level 1 excludes department children; parent allocation counted once', async () => {
    const snapshot = await loadSnapshot();
    const scope = getScope(snapshot, { projectId: 'dong-thanh', level: '1' }, 'contractor');
    assert.equal(totalMetrics(scope).contract, 19_200_000_000);
    assert.equal(totalMetrics(getScope(snapshot, { projectId: 'dong-thanh', level: '2' }, 'contractor')).contract, 8_800_000_000);
    const allocation = allocations(snapshot, 'dong-thanh');
    assert.equal(allocation.length, 1);
    assert.equal(allocation[0].remaining, -400_000_000);
});

test('negative balances and ratios above 100% are preserved', async () => {
    const snapshot = await loadSnapshot();
    const item = snapshot.items.find((entry) => entry.projectId === 'dong-thanh' && entry.id === 'basic');
    assert.equal(item.balance, -800_000_000);
    assert.ok(item.paidRatio > 1);
    assert.equal(ratio(20, 0), null);
    assert.equal(ratio(null, 20), null);
    assert.equal(safeSum([1, null]), null);
    assert.throws(() => safeSum([Number.MAX_SAFE_INTEGER, 1]), RangeError);
});

test('date and search filters affect transactions only; history includes replaced versions', async () => {
    const snapshot = await loadSnapshot();
    const state = { projectId: 'dong-thanh', detailSide: 'investor', entityId: 'survey', transactionTab: 'effective', from: '2026-10-01', to: '2026-10-27' };
    const rows = visibleTransactions(snapshot, state);
    assert.equal(rows.length, 1);
    assert.equal(rows[0].rootId, 'survey-payment-2');
    assert.equal(visibleTransactions(snapshot, { ...state, transactionTab: 'history' }).length, 3);
    assert.equal(snapshot.items.find((item) => item.projectId === 'dong-thanh' && item.id === 'survey').contract, 11_400_000_000);
    assert.equal(getScope(snapshot, { projectId: 'nam-son' }, 'investor').length, 0);
});
