import { Component, onWillStart, proxy, useProps, useEffect } from '@odoo/owl';
import { registry } from '@web/core/registry';
import { browser } from '@web/core/browser/browser';
import { useService } from '@web/core/utils/hooks';
import { session } from '@web/session';
import { user } from '@web/core/user';
import { deserializeDateTime, formatDateTime } from '@web/core/l10n/dates';
import { statusTone } from '../table/status_badge';

const projectKey = () => `tp-kd-current-project:${session.db || ''}:${user.userId || 0}`;

export class ProjectPerspective extends Component {
    static template = 'tp_kd_workspace.ProjectPerspective';
    props = useProps();
    setup() {
        this.orm = useService('orm');
        this.action = useService('action');
        this.mode = this.props.context?.tp_perspective || 'management';
        let selected = this.props.context?.default_project_id || false;
        if (!selected) { try { selected = Number(browser.sessionStorage.getItem(projectKey())) || false; } catch {} }
        this.state = proxy({ project: selected, limit: 20, offset: 0, busy: false, error: '', data: null });
        this.sequence = 0;
        onWillStart(() => this.load());
        useEffect(() => {
            const mode = this.props.context?.tp_perspective || 'management';
            if (mode !== this.mode) {
                this.mode = mode;
                this.state.project = this.props.context?.default_project_id || this.state.project;
                this.state.offset = 0;
                this.load();
            }
        });
    }
    async load() {
        const seq = ++this.sequence;
        this.state.busy = true;
        this.state.error = '';
        try {
            const data = await this.orm.call('tp.project.perspective', 'get_perspective', [this.mode, this.state.project, this.state.limit, this.state.offset]);
            if (seq === this.sequence) this.state.data = data;
        } catch (e) {
            if (seq === this.sequence) {
                this.state.data = null;
                this.state.error = e.data?.message || 'Không tải được dữ liệu. Thử tải lại.';
                // A revoked selection must not prevent choosing another project.
                if (this.state.project && e.data?.name === 'odoo.exceptions.AccessError') {
                    this.state.project = false;
                    this.state.offset = 0;
                    try { browser.sessionStorage.removeItem(projectKey()); } catch {}
                    await this.load();
                }
            }
        } finally { if (seq === this.sequence) this.state.busy = false; }
    }
    deadline(value) { return value ? formatDateTime(deserializeDateTime(value), { format: 'dd/MM/yyyy HH:mm' }) : 'Chưa xác định'; }
    taskLabel(row) { return { '01_in_progress': 'Đang thực hiện', '04_waiting_normal': 'Chờ xử lý', '1_done': 'Hoàn tất công việc' }[row.state_key] || row.state; }
    taskTone(row) { return `tp_kd_badge tp_kd_tone_${statusTone('project.task', 'state', row.state_key)}`; }
    async selectProject(ev) {
        this.state.project = Number(ev.target.value) || false;
        this.state.offset = 0;
        try { browser.sessionStorage.setItem(projectKey(), String(this.state.project || '')); } catch {}
        await this.load();
    }
    async size(ev) { this.state.limit = Number(ev.target.value); this.state.offset = 0; await this.load(); }
    async page(delta) { this.state.offset = Math.max(0, this.state.offset + delta * this.state.limit); await this.load(); }
    async open(key, id = false) {
        try {
            const action = await this.orm.call('tp.project.perspective', 'open_perspective_source', [this.mode, key, this.state.project, id]);
            if (!action.views) action.views = (action.view_mode || 'list,form').split(',').map(t => [false, t]);
            await this.action.doAction(action);
        } catch (e) { this.state.error = e.data?.message || 'Hồ sơ không còn trong quyền.'; }
    }
    async navigate(mode, detail = false) {
        try {
            const action = await this.orm.call('tp.project.perspective', 'switch_perspective', [mode, this.state.project, detail]);
            if (!action.views) action.views = [[action.view_id?.[0] || action.view_id || false, 'form']];
            await this.action.doAction(action);
        } catch (e) { this.state.error = e.data?.message || 'Không mở được hồ sơ.'; }
    }
}
registry.category('views').add('tp_project_perspective', { type: 'form', Controller: ProjectPerspective });
