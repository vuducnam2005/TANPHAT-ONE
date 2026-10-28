import { planningBusiness } from '../modules/planning-business/module.js';
import { shell } from './shell.js';
import { emptyState } from '../shared/ui.js';
import { setupChartTooltips } from '../shared/chart-interactions.js';

// Register future departments here; each owns its own pages and repository.
const modules = new Map([[planningBusiness.id, planningBusiness]]);
const app = document.querySelector('#app');
const hideChartTooltip = setupChartTooltips(app);
let module = planningBusiness;
let snapshot;
let request = 0;
let state = { ...module.initialState, projectId: 'dong-thanh', page: 'overview' };

function readRoute() {
    const [path, query = ''] = location.hash.slice(1).split('?');
    const [moduleId, pageId] = path.split('/');
    module = modules.get(moduleId) || planningBusiness;
    const parameters = new URLSearchParams(query);
    state = { ...module.initialState, projectId: parameters.get('project') || 'dong-thanh', page: module.pages.some((page) => page.id === pageId) ? pageId : 'overview',
        detailSide: ['investor', 'contractor'].includes(parameters.get('side')) ? parameters.get('side') : 'all', entityId: parameters.get('entity') || '' };
    validateRoute();
}

function validateRoute() {
    if (!snapshot) return;
    if (!snapshot.projects.some((project) => project.id === state.projectId)) state.projectId = snapshot.projects[0].id;
    if (state.entityId && !snapshot.items.some((item) => item.projectId === state.projectId && item.id === state.entityId && (state.detailSide === 'all' || item.side === state.detailSide))) state.entityId = '';
}

function writeRoute() {
    const query = new URLSearchParams({ project: state.projectId });
    if (state.page === 'detail' && state.detailSide !== 'all') query.set('side', state.detailSide);
    if (state.page === 'detail' && state.entityId) query.set('entity', state.entityId);
    history.pushState(null, '', `#${module.id}/${state.page}?${query}`);
}

function render({ loading = false, error = '', focusTitle = false } = {}) {
    hideChartTooltip();
    const active = document.activeElement;
    const savedFocus = active?.id;
    const selection = active?.type === 'search' ? active.selectionStart : null;
    const page = module.pages.find((entry) => entry.id === state.page);
    const body = error ? `${emptyState('Chưa nạp được dữ liệu mẫu', error)}<button class="tp-button" data-action="refresh">Thử nạp lại</button>` : snapshot ? page.render(snapshot, state) : emptyState('Đang nạp dashboard', 'Chuẩn bị sổ dự án và dữ liệu mẫu…');
    app.innerHTML = shell(module, snapshot, state, body, { loading });
    app.classList.remove('sidebar-open');
    document.title = `${page.name} · Kế hoạch Kinh doanh · Tấn Phát`;
    if (focusTitle) document.querySelector('#page-title')?.focus();
    else if (savedFocus) {
        const target = document.getElementById(savedFocus);
        target?.focus({ preventScroll: true });
        if (selection !== null && target?.type === 'search') target.setSelectionRange(selection, selection);
    }
}

async function load() {
    const current = ++request;
    render({ loading: true });
    try {
        const next = await module.load();
        if (current !== request) return;
        snapshot = next; validateRoute(); render();
        document.querySelector('#announcement').textContent = 'Đã nạp dữ liệu mẫu. Số liệu lũy kế đến ngày 27 tháng 10 năm 2026.';
    } catch (error) {
        if (current === request) render({ error: `Không đọc được bộ dữ liệu mẫu. Bấm Thử nạp lại. (${error.message})` });
    }
}

function navigate(page, overrides = {}) {
    state = { ...module.initialState, projectId: state.projectId, page, ...overrides };
    writeRoute(); render({ focusTitle: true }); window.scrollTo({ top: 0 });
}

app.addEventListener('click', (event) => {
    if (event.target.closest('.tp-skip-link')) { event.preventDefault(); document.querySelector('#main-content').focus(); return; }
    const control = event.target.closest('[data-action]');
    if (!control) return;
    switch (control.dataset.action) {
        case 'navigate': navigate(control.dataset.page); break;
        case 'drill': navigate('detail', { detailSide: control.dataset.side, entityId: control.dataset.id }); break;
        case 'project-detail': navigate('detail'); break;
        case 'refresh': load(); break;
        case 'menu': app.classList.toggle('sidebar-open'); control.setAttribute('aria-expanded', app.classList.contains('sidebar-open')); if (app.classList.contains('sidebar-open')) document.querySelector('.tp-nav-button[aria-current]')?.focus(); break;
        case 'close-menu': app.classList.remove('sidebar-open'); document.querySelector('[data-action="menu"]')?.setAttribute('aria-expanded', 'false'); document.querySelector('[data-action="menu"]')?.focus(); break;
        case 'formulas': document.querySelector('#formula-dialog').showModal(); break;
        case 'close-dialog': document.querySelector('#formula-dialog').close(); break;
        case 'reset-filters': Object.assign(state, { itemId: '', contractorId: '', level: '', search: '', sort: 'name' }); render(); break;
        case 'reset-dates': Object.assign(state, { from: '', to: '', transactionSearch: '' }); render(); break;
        case 'overview-side': state.overviewSide = control.dataset.side; render(); document.querySelector(`[data-action="overview-side"][data-side="${state.overviewSide}"]`)?.focus({ preventScroll: true }); break;
        case 'tab': state.transactionTab = control.dataset.tab; render(); document.querySelector(`[data-tab="${state.transactionTab}"]`)?.focus({ preventScroll: true }); break;
    }
});

function updateField(event) {
    const field = event.target.dataset.field;
    if (!field) return;
    if (event.type === 'input' && event.target.type !== 'search') return;
    if (event.type === 'change' && event.target.type === 'search') return;
    if (field === 'projectId') {
        state = { ...module.initialState, page: state.page, projectId: event.target.value };
        writeRoute(); render(); return;
    }
    state[field] = event.target.value;
    if (field === 'detailSide') state.entityId = '';
    if (field === 'detailSide' || field === 'entityId') writeRoute();
    render();
}
app.addEventListener('input', updateField);
app.addEventListener('change', updateField);
app.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && app.classList.contains('sidebar-open')) {
        app.classList.remove('sidebar-open');
        const toggle = document.querySelector('[data-action="menu"]'); toggle.setAttribute('aria-expanded', 'false'); toggle.focus();
    }
    if (event.key === 'Tab' && app.classList.contains('sidebar-open')) {
        const nodes = [...document.querySelectorAll('.tp-sidebar button, .tp-mobile-nav')];
        const index = nodes.indexOf(document.activeElement);
        if (event.shiftKey && index === 0) { event.preventDefault(); nodes.at(-1).focus(); }
        else if (!event.shiftKey && index === nodes.length - 1) { event.preventDefault(); nodes[0].focus(); }
    }
});

// This live region survives page rerenders.
const announcement = document.createElement('div');
announcement.id = 'announcement'; announcement.className = 'tp-visually-hidden'; announcement.setAttribute('role', 'status'); document.body.append(announcement);
function routeChanged() {
    const previousModule = module.id;
    readRoute();
    if (previousModule !== module.id) { snapshot = undefined; load(); }
    else render({ focusTitle: true });
}
window.addEventListener('popstate', routeChanged);
window.addEventListener('hashchange', routeChanged);
let narrowCharts = window.innerWidth <= 560;
window.addEventListener('resize', () => {
    const narrow = window.innerWidth <= 560;
    if (narrow !== narrowCharts) { narrowCharts = narrow; render(); }
});
readRoute(); load();
