import { Component, proxy, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
export const HR_COLORS = ['#287fc0','#17a99a','#8a68cc','#dc9930','#d2657b','#659a3e','#5369c3','#c47836','#3a9ebc','#a964a1','#899d34','#587f9e','#c34c69','#368c71'];
export function departmentColor(id, catalog = []) {
    if (!id) return '#8493a5';
    // Allocate once across the full catalog so filtered subsets keep distinct colors.
    const ids = [...new Set(catalog.map(row => row.id).filter(Boolean))].sort((a,b) => a-b);
    const index = ids.indexOf(id);
    return index >= 0 && index < HR_COLORS.length ? HR_COLORS[index] : `hsl(${(Number(id) * 137.508 % 360).toFixed(3)} 62% 47%)`;
}
export function donutPath(percent, offset) {
    const point = (radius, angle) => {
        const radians = (angle - 90) * Math.PI / 180;
        return `${160 + radius * Math.cos(radians)},${160 + radius * Math.sin(radians)}`;
    };
    const start = offset * 3.6, end = (offset + percent) * 3.6;
    if (percent >= 100) {
        return 'M160,14 A146,146 0 1 1 160,306 A146,146 0 1 1 160,14 M160,56 A104,104 0 1 0 160,264 A104,104 0 1 0 160,56 Z';
    }
    const large = percent > 50 ? 1 : 0;
    return `M${point(146,start)} A146,146 0 ${large} 1 ${point(146,end)} L${point(104,end)} A104,104 0 ${large} 0 ${point(104,start)} Z`;
}
export const MISSING_BASIC = ['|', '|', ['tp_employee_code', '=', false], ['department_id', '=', false], '&', ['tp_source_title', '=', false], ['job_id', '=', false]];
export function chartSegments(rows, total, catalog = []) {
    let offset = 0;
    return rows.map(row => {
        const percent = total ? row.count / total * 100 : 0;
        const result = {...row, percent, offset, color: departmentColor(row.id,catalog), path: donutPath(percent, offset)};
        offset += percent;
        return result;
    });
}
export class HrOverview extends Component {
    static template = "tp_hr_workspace.Overview";
    setup() {
        this.orm = useService("orm"); this.action = useService("action");
        this.state = proxy({loading: true, error: "", data: null, department: "", job: "", status: "active", catalog: [], jobs: [], search: "", page: 1, pageSize: 10, highlight: null, tooltip: null});
        this.request = 0; this.loadedFilters = null;
        onWillStart(() => this.load());
    }
    get filters() { return {department_id: Number(this.state.department) || false, job_id: Number(this.state.job) || false, status: this.state.status}; }
    get ready() { return !this.state.loading && !this.state.error && Boolean(this.state.data); }
    get segments() { return chartSegments(this.state.data?.departments || [], this.state.data?.total || 0, this.state.catalog); }
    get jobs() { return [...(this.state.data?.jobs || [])].sort((a,b) => b.count-a.count || a.name.localeCompare(b.name,'vi') || a.id-b.id); }
    get maxCount() { return Math.max(1, ...this.jobs.map(row => row.count)); }
    get axisMax() { const max=this.maxCount; const step=10 ** Math.floor(Math.log10(max)); return Math.ceil(max/step)*step; }
    get axisTicks() { return this.axisMax < 4 ? [0, this.axisMax] : [0, Math.floor(this.axisMax / 2), this.axisMax]; }
    get linkPercent() { return this.state.data?.total ? this.state.data.linked / this.state.data.total * 100 : 0; }
    get tableRows() { const term = this.state.search.toLocaleLowerCase('vi'); return this.segments.filter(row => row.name.toLocaleLowerCase('vi').includes(term)); }
    get pageCount() { return Math.max(1, Math.ceil(this.tableRows.length / this.state.pageSize)); }
    get visibleRows() { return this.tableRows.slice((this.state.page - 1) * this.state.pageSize, this.state.page * this.state.pageSize); }
    get checklist() {
        return [
            {key:'missing_basic', label:'Thiếu thông tin cơ bản', domain:MISSING_BASIC, note:'Mã TP, đơn vị hoặc cả chức vụ nguồn và chức vụ khai báo.'},
            {key:'missing_code', label:'Chưa có mã nhân viên', domain:[['tp_employee_code','=',false]]},
            {key:'missing_department', label:'Chưa khai báo đơn vị', domain:[['department_id','=',false]]},
            {key:'missing_job', label:'Chưa khai báo chức vụ', domain:[['job_id','=',false]], note:'Tách riêng khỏi chức vụ nguồn.'},
            {key:'missing_contact', label:'Chưa có liên hệ công việc', domain:[['work_email','=',false],['work_phone','=',false],['mobile_phone','=',false]], note:'Chưa có email hoặc số điện thoại nào.'},
        ].map(item => ({...item, count:this.state.data?.[item.key] || 0}));
    }
    async load() {
        const request = ++this.request; const filters = {...this.filters};
        this.state.loading = true; this.state.error = "";
        this.clearHighlight();
        try {
            const data = await this.orm.call("tp.hr.workspace", "get_overview", [filters]);
            if (request !== this.request) return;
            this.state.data = data; this.loadedFilters = filters;
            this.state.catalog = data.catalog_departments || data.departments;
            this.state.jobs = data.catalog_jobs || data.jobs || [];
            this.state.page = 1;
        } catch (error) {
            if (request !== this.request) return;
            if (/SessionExpired/.test(error.data?.name || error.name || '')) throw error;
            this.state.error = error.data?.name === 'odoo.exceptions.AccessError' ? 'Bạn không có quyền xem tổng quan nhân sự.' : 'Không tải được tổng quan. Vui lòng thử lại.';
        } finally { if (request === this.request) this.state.loading = false; }
    }
    async changeFilter(ev, key) { this.state[key] = ev.target.value; await this.load(); }
    resetFilters() { Object.assign(this.state, {department:'',job:'',status:'active',search:'',page:1}); return this.load(); }
    searchTable(ev) { this.state.search = ev.target.value; this.state.page = 1; }
    changePageSize(ev) { this.state.pageSize = Number(ev.target.value); this.state.page = 1; }
    async openEmployees(extra = []) {
        if (!this.ready) return;
        const action = await this.orm.call("tp.hr.workspace", "action_employees", [{...this.loadedFilters}, extra]);
        return this.action.doAction(action);
    }
    onSliceKey(ev, row) { if (['Enter', ' '].includes(ev.key)) { ev.preventDefault(); return this.openDepartment(row); } }
    highlight(ev, row, kind) {
        const rect = ev.currentTarget.getBoundingClientRect();
        const width = Math.min(288, window.innerWidth - 24);
        this.state.highlight = `${kind}-${row.id}`;
        this.state.tooltip = {
            name: row.name, count: row.count,
            percent: this.state.data.total ? row.count / this.state.data.total * 100 : 0,
            left: Math.max(12, Math.min(rect.left, window.innerWidth - width - 12)),
            top: rect.top > 120 ? rect.top - 100 : Math.min(rect.bottom + 8, window.innerHeight - 110),
        };
    }
    clearHighlight() { this.state.highlight = null; this.state.tooltip = null; }
    onKeydown(ev) { if (ev.key === 'Escape') this.clearHighlight(); }
    openDepartment(row) { return this.openEmployees([["department_id", "=", row.id || false]]); }
    openJob(row) { return this.openEmployees([["job_id", "=", row.id || false]]); }
    openMissing() { return this.openEmployees(MISSING_BASIC); }
    openSummary() { document.getElementById('hr-department-summary')?.scrollIntoView({block:'start'}); }
    createEmployee() {
        if (!this.ready || !this.state.data.can_create) return;
        return this.action.doAction({type: "ir.actions.act_window", name: "Thêm nhân viên", res_model: "hr.employee", views: [[this.state.data.employee_form_id || false,"form"]], target: "current"});
    }
    exportFile() {
        if (!this.ready) return;
        const filters = this.loadedFilters;
        window.location.assign('/tp_hr/export?' + new URLSearchParams({department_id: filters.department_id || '', job_id: filters.job_id || '', status: filters.status}));
    }
}
registry.category("actions").add("tp_hr_workspace.overview", HrOverview);

