const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const base = path.join(__dirname, '../../custom_addons/tp_hr_workspace/static/src/table/');
const context = {
    Component: class {}, RelationalModel: class {}, ListController: class {},
    ListRenderer: class { setup() {} }, listView: {}, TpTableFilterBar: class {},
    registry: { category: () => ({ add() {} }) }, render() {}, session: {},
    onWillUnmount() {}, onPatched() {}, useSortable: (options) => { context.sortable = options; return {}; },
};
vm.createContext(context);
vm.runInContext(fs.readFileSync(base + 'employee_reorder_rules.js', 'utf8').replace(/export /g, '') +
    '\nglobalThis.analyze = analyzeEmployeeReorderState;', context);
vm.runInContext(fs.readFileSync(base + 'table.js', 'utf8').replace(/^import [\s\S]*?;\r?\n/gm, '').replace(/export /g, '') +
    '\nglobalThis.Renderer = HrListRenderer;', context);
const state = {
    resModel: 'hr.employee', isGrouped: true, groupBy: ['department_id'],
    orderBy: [{name: 'sequence', asc: true}, {name: 'id', asc: true}],
    domain: [['active', '=', true]], context: {}, canReorderSession: true, canEditView: true,
};
assert.equal(context.analyze(state).canDrag, true);
for (const patch of [
    {domain: [['name', 'ilike', 'A']]}, {domain: [['job_id', '=', 5]]},
    {orderBy: [{name: 'name', asc: true}]}, {groupBy: ['department_id', 'job_id']},
]) {
    assert.equal(context.analyze({...state, ...patch}).canDrag, false);
    assert.equal(context.analyze({...state, ...patch}).showLockBanner, true);
}
for (const domain of [[['department_id', '=', 4]], [['department_id', 'child_of', 4]], []]) {
    assert.equal(context.analyze({...state, domain}).canDrag, true);
}
for (const patch of [{canReorderSession: false}, {readonly: true}, {context: {tp_hr_missing: true}}, {context: {active_test: false}, domain: []}]) {
    assert.equal(context.analyze({...state, ...patch}).showHandleColumn, false);
}
const row = id => ({dataset: {resId: String(id)}, classList: {contains: () => true}});
(async () => {
    const renderer = Object.create(context.Renderer.prototype);
    Object.defineProperty(renderer, 'canDragEmployeesNow', {value: true});
    renderer.tableRef = () => ({querySelectorAll: () => []});
    context.browser = {};
    let loads = 0;
    const calls = [], notices = [];
    const groupRecords = [7, 8, 9].map(resId => ({resId, data: {}, _applyValues(values) {Object.assign(this.data, values);}}));
    renderer.props = {list: {groups: [{value: 4, list: {records: groupRecords}}], model: {root: {load: async () => {loads++;}}}}};
    renderer.orm = {call: async (...args) => calls.push(args)};
    renderer.notificationService = {add: (...args) => notices.push(args)};
    // Middle-page anchors preserve unseen employees; never send a visible-page list.
    await renderer.onEmployeeDropInDepartment({element: row(8), group: {dataset: {deptId: '4'}}, previous: row(7), next: row(9)});
    assert.deepEqual(Array.from(calls[0][2]), [8, 4, 9, 7]);
    assert.equal(notices[0][0], 'Đã cập nhật thứ tự nhân viên');
    assert.equal(loads, 0);
    renderer.orm.call = async () => {throw new Error('Denied');};
    await renderer.onEmployeeDropInDepartment({element: row(8), group: {dataset: {deptId: '4'}}, next: row(9)});
    assert.equal(loads, 1);
    assert.equal(notices[1][1].type, 'danger');
    assert.equal(renderer.tpReorderBusy, false);
    let resolveDeferred;
    renderer.orm.call = (...args) => {calls.push(args); return new Promise(resolve => {resolveDeferred = resolve;});};
    const optimistic = renderer.onEmployeeDropInDepartment({element: row(9), group: {dataset: {deptId: '4'}}, next: row(7)});
    assert.deepEqual(Array.from(groupRecords, record => record.resId), [9, 7, 8]);
    assert.equal(renderer.tpReorderBusy, true);
    const callCount = calls.length;
    await renderer.onEmployeeDropInDepartment({element: row(8), group: {dataset: {deptId: '4'}}, next: row(7)});
    assert.equal(calls.length, callCount);
    resolveDeferred({ok: true, ordered_ids: [9, 7, 8]});
    await optimistic;
    assert.deepEqual(Array.from(groupRecords, record => record.data.sequence), [10, 20, 30]);
    assert.equal(loads, 1, 'Successful save must not reload whole root');
    assert.equal(renderer.tpReorderBusy, false);
    function edgeRenderer() {
        const subject = Object.create(context.Renderer.prototype);
        Object.defineProperty(subject, 'canDragEmployeesNow', {value: true});
        const records = [7, 8, 9].map(resId => ({resId, data: {}, _applyValues(values) {Object.assign(this.data, values);}}));
        const department = {records, offset: 0, load: async () => {throw Error('Reload failed');}};
        subject.props = {list: {groups: [{value: 4, list: department}], model: {root: {load: async () => {throw Error('Reload failed');}}}}};
        subject.tableRef = () => ({querySelectorAll: () => []});
        subject.notices = [];
        subject.notificationService = {add: (...args) => subject.notices.push(args)};
        return {subject, records};
    }
    const dropArgs = {element: row(9), group: {dataset: {deptId: '4'}}, next: row(7)};
    const changedPage = edgeRenderer();
    changedPage.subject.orm = {call: async () => ({ok: true, ordered_ids: [99, 7, 8]})};
    await changedPage.subject.onEmployeeDropInDepartment(dropArgs);
    assert.deepEqual(Array.from(changedPage.records, r => r.resId), [9, 7, 8]);
    assert.equal(changedPage.subject.notices[0][1].type, 'warning');
    const failedReload = edgeRenderer();
    failedReload.subject.orm = {call: async () => {throw Error('Save rejected');}};
    await failedReload.subject.onEmployeeDropInDepartment(dropArgs);
    assert.deepEqual(Array.from(failedReload.records, r => r.resId), [7, 8, 9]);
    assert.equal(failedReload.subject.notices[0][1].type, 'danger');
    for (const disappear of ['navigation', 'unmount']) {
        const pending = edgeRenderer();
        let finish;
        pending.subject.orm = {call: () => new Promise(resolve => {finish = resolve;})};
        let renders = 0;
        context.render = () => {renders++;};
        const saving = pending.subject.onEmployeeDropInDepartment(dropArgs);
        assert.equal(renders, 1);
        if (disappear === 'navigation') pending.subject.props.list = {groups: []};
        else pending.subject._tpUnmounted = true;
        finish({ok: true, ordered_ids: [9, 7, 8]});
        await saving;
        assert.equal(renders, 1);
        assert.equal(pending.subject.notices.length, 0);
    }
    for (const disappear of ['navigation', 'unmount']) {
        const pending = edgeRenderer();
        let finishReload;
        pending.subject.props.list.groups[0].list.load = () => new Promise(resolve => {finishReload = resolve;});
        pending.subject.orm = {call: async () => ({ok: true, ordered_ids: [99, 7, 8]})};
        let renders = 0;
        context.render = () => {renders++;};
        const saving = pending.subject.onEmployeeDropInDepartment(dropArgs);
        await new Promise(setImmediate);
        assert.equal(typeof finishReload, 'function');
        if (disappear === 'navigation') pending.subject.props.list = {groups: []};
        else pending.subject._tpUnmounted = true;
        finishReload();
        await saving;
        assert.equal(renders, 1);
        assert.equal(pending.subject.notices.length, 0);
    }
    context.render = () => {};
    let suppressed = 0;
    renderer._tpSuppressClickUntil = Date.now() + 500;
    assert.equal(renderer._shouldSuppressAfterDrag({preventDefault() {suppressed++;}, stopPropagation() {suppressed++;}}), true);
    assert.equal(suppressed, 2);
    const baseCalls = {capture: 0, cell: 0, selection: 0};
    Object.assign(context.ListRenderer.prototype, {
        onClickCapture() {baseCalls.capture++;},
        onCellClicked() {baseCalls.cell++;},
        toggleRecordSelection() {baseCalls.selection++;},
    });
    renderer._tpSuppressClickUntil = 0;
    renderer.tpDragState = {dragging: false};
    const clickEvent = {preventDefault() {}, stopPropagation() {}};
    renderer.onClickCapture({}, clickEvent);
    await renderer.onCellClicked({}, {}, clickEvent);
    renderer.toggleRecordSelection({}, clickEvent);
    assert.deepEqual(baseCalls, {capture: 1, cell: 1, selection: 1});
    renderer.tpDragState.dragging = true;
    renderer.onClickCapture({}, clickEvent);
    await renderer.onCellClicked({}, {}, clickEvent);
    renderer.toggleRecordSelection({}, clickEvent);
    assert.deepEqual(baseCalls, {capture: 1, cell: 1, selection: 1});
    const dragRenderer = Object.create(context.Renderer.prototype);
    dragRenderer.setup();
    let drops = 0;
    dragRenderer.onEmployeeDropInDepartment = async () => {drops++;};
    const listeners = {};
    context.browser = {addEventListener: (name, fn) => {listeners[name] = fn;}, removeEventListener() {}};
    const classes = {add() {}, remove() {}, toggle() {}};
    const group = {value: 4, dataset: {deptId: '4'}, classList: classes, getBoundingClientRect: () => ({left: 0, right: 500, top: 100, bottom: 400})};
    dragRenderer.tableRef = () => ({classList: classes, querySelectorAll: () => []});
    dragRenderer.sortStart = () => {};
    context.sortable.onDragStart({group});
    listeners.pointerup({clientX: 200, clientY: 200});
    await context.sortable.onDrop({element: row(8), group, parent: {dataset: {deptId: '5'}}});
    assert.equal(drops, 0);
    await context.sortable.onDrop({element: row(8), group, parent: group});
    assert.equal(drops, 1);
    listeners.pointerup({clientX: 200, clientY: 500});
    await context.sortable.onDrop({element: row(8), group, parent: group});
    assert.equal(drops, 1);
    assert.equal(dragRenderer.hrGroupDeptId({value: 26}), 26);
    assert.equal(dragRenderer.hrGroupDeptId({value: false}), 0);
    assert.equal(context.sortable.handle, undefined);
    assert.match(context.sortable.ignore, /button/);
    console.log('PASS HR employee order: eligibility, filters, viewer, anchors, success/failure, click guard');
})().catch(err => {console.error(err); process.exitCode = 1;});
