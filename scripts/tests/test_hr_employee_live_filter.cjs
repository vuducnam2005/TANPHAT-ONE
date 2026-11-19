const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const root = path.resolve(__dirname, '../..');
const unmount = [];
class Domain {
    constructor(value) { this.value = value; }
    static and(values) { return new Domain(values.flatMap(v => v instanceof Domain ? v.value : v || [])); }
    static or(values) { return Domain.and(values); }
    toList() { return this.value; }
    toString() { return JSON.stringify(this.value); }
}
class Component {}
class AutoComplete { onInput() { this.inputCalls = (this.inputCalls || 0) + 1; } }
const context = vm.createContext({ Component, AutoComplete, Domain, console,
    useProps: () => ({}), signal: { ref: () => () => null }, toRaw: v => v,
    onWillUnmount: fn => unmount.push(fn), useDropdownState: () => ({}), SearchBarMenu: class {},
    resolveTableFilterProfile: () => ({ criteria: [{ key: 'name', field: 'name', type: 'char', label: 'Họ tên' }] }),
});
function load(rel, exports) {
    let source = fs.readFileSync(path.join(root, rel), 'utf8')
        .replace(/^import[\s\S]*?from\s+['"][^'"]+['"];?\r?\n/gm, '')
        .replace(/^export /gm, '');
    vm.runInContext(source + '\n' + exports.map(e => `globalThis.${e} = ${e};`).join('\n'), context);
}
load('custom_addons/tp_web_home/static/src/search/filter_domain.js',
    ['buildCriterionFilter', 'valuesEqual', 'cloneCriterionValue', 'createEmptyCriterionValue', 'isCriterionEmpty', 'validateCriterionValue']);
load('custom_addons/tp_web_home/static/src/search/table_filter_bar.js', ['TpTableFilterBar']);
load('custom_addons/tp_hr_workspace/static/src/table/live_name_filter.js', ['HrEmployeeFilterBar', 'HrNameAutoComplete']);
vm.runInContext(`registerTableFilterProfile('hr.employee', { criteria: [{ key: 'name', field: 'name', label: 'Họ tên', type: 'char' }, { key: 'department_id', field: 'department_id', label: 'Phòng ban', type: 'many2one' }] });`, context);
const { HrEmployeeFilterBar, HrNameAutoComplete } = context;
const plain = v => JSON.parse(JSON.stringify(v));

(async () => {
    const criterion = { key: 'name', field: 'name', label: 'Họ tên', type: 'char', recordSuggestions: true };
    assert.deepEqual(JSON.parse(context.buildCriterionFilter(criterion, 'Na').domain), [['name', 'ilike', 'Na']]);
    assert.deepEqual(JSON.parse(context.buildCriterionFilter(criterion, { id: 7, label: 'Nam' }).domain), [['id', '=', 7]]);
    assert.equal(context.valuesEqual(criterion, { id: 7, label: 'Nam' }, 'Nam'), false);
    assert.equal(context.valuesEqual(criterion, null, 'N'), false);

    const bar = new HrEmployeeFilterBar();
    const items = { 1: { tpFilterKey: 'name', groupId: 1 }, 2: { tpFilterKey: 'department_id', groupId: 2 } };
    const deactivated = [], added = [];
    bar.env = { searchModel: { resModel: 'hr.employee', searchViewFields: { name: { type: 'char' }, department_id: { type: 'many2one', relation: 'hr.department' } }, searchItems: items,
        query: [{ searchItemId: 1 }, { searchItemId: 2 }], facets: [], globalDomain: [['company_id', '=', 3]],
        context: { allowed_company_ids: [3] }, display: {}, domainEvalContext: {},
        _getGroups: () => [{ activeItems: [{ searchItemId: 1 }] }, { activeItems: [{ searchItemId: 2 }] }],
        _getSearchItemDomain: item => item.searchItemId === 1 ? [['id', '=', 7]] : [['department_id', '=', 4]],
        deactivateGroup: id => deactivated.push(id), createNewFilters: f => added.push(...f), _notify: async () => {},
    } };
    bar.props = { controller: { props: { resModel: 'hr.employee', context: {} }, model: {} } };
    bar.state = { pending: { name: 'Na', department_id: { id: 99, label: 'Pending department' } },
        applied: { name: { id: 7, label: 'Nam' }, department_id: { id: 4, label: 'Applied department' } } };
    bar.applySeq = 0; bar.nameRequest = 0;
    await bar.onNameInput({ inputValue: 'N' }, criterion);
    assert.deepEqual(deactivated, [1], 'live name must preserve the applied department');
    assert.equal(added.length, 1);
    assert.equal(bar.state.pending.department_id.id, 99, 'unfinished department must not be submitted');
    assert.deepEqual(plain(bar.nameSuggestionDomain(criterion)), [['company_id', '=', 3], ['department_id', '=', 4]],
        'suggestions must preserve action scope and other applied filters but remove previous exact employee');

    const requests = [];
    bar.orm = { searchRead: (...args) => new Promise((resolve, reject) => requests.push({ args, resolve, reject })) };
    const options = bar.nameSources(criterion)[0].options;
    const n = options('N'), na = options('Na');
    requests[1].resolve([{ id: 8, name: 'Nam', tp_employee_code: 'TP08' }]);
    const latest = await na;
    requests[0].resolve([{ id: 7, name: 'Ngọc', tp_employee_code: 'TP07' }]);
    assert.equal((await n).length, 0, 'late N response must not replace Na results');
    assert.equal(latest[0].label, 'Nam · TP08');
    assert.deepEqual(plain(requests[1].args[1]), [['company_id', '=', 3], ['department_id', '=', 4], ['name', 'ilike', 'Na']]);
    assert.deepEqual(plain(requests[1].args[3].context), { allowed_company_ids: [3] });
    latest[0].onSelect();
    assert.equal(bar.state.pending.name.id, 8);
    await bar.onNameInput({ inputValue: 'N' }, criterion);
    assert.equal(bar.state.pending.name, 'N', 'typing after selecting must clear the previous employee ID');
    const inflight = options('Nam');
    bar.nameRequest++;
    requests[2].resolve([{ id: 8, name: 'Nam' }]);
    assert.equal((await inflight).length, 0, 'clear/navigation must invalidate in-flight suggestions');
    const failed = options('Nam'); requests[3].reject(Error('offline'));
    assert.match((await failed)[0].label, /Không tải được/);
    assert.deepEqual(plain(await options('')), []);

    const input = new HrNameAutoComplete();
    input.debouncedProcessInput = { cancel() {} }; input.close = () => {};
    input.onCompositionStart(); input.onInput({ isComposing: true });
    assert.equal(input.inputCalls, undefined);
    input.onCompositionEnd();
    assert.equal(input.inputCalls, 1, 'Vietnamese composition queries only after compositionend');
    console.log('PASS: substring / exact ID / isolated criterion / scope / reverse response / clear / failure / Vietnamese composition');
})().catch(e => { console.error(e); process.exitCode = 1; });
