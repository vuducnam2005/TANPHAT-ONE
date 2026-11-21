/** @odoo-module **/
import { Component, onWillStart, proxy, useProps } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { InlineErrors } from "@tp_web_home/validation/inline_errors";
import { saveError } from "@tp_web_home/validation/validation";
import { TpRequestList } from "../list/request_list";
import { extractErrorMessage, foldText } from "../prefs";

const ICON_CHOICES = [
    { key: "assignment", label: "Hồ sơ" },
    { key: "schedule", label: "Chấm công" },
    { key: "laptop_mac", label: "Thiết bị" },
    { key: "swap_horiz", label: "Đổi máy" },
    { key: "build", label: "Sửa chữa" },
    { key: "shopping_cart", label: "Mua sắm" },
    { key: "support_agent", label: "Hỗ trợ IT" },
    { key: "description", label: "Văn bản" },
    { key: "work_history", label: "Công tác" },
    { key: "payments", label: "Chi phí" },
];

const COLOR_CHOICES = [
    "#2563EB", "#0284C7", "#0D9488", "#059669",
    "#D97706", "#DC2626", "#7C3AED", "#475569",
];

function emptyTypeForm() {
    return {
        id: null,
        code: "",
        name: "",
        description: "",
        guidance: "",
        icon: "assignment",
        color: "#2563EB",
        sequence: 50,
        handler_kind: "general",
        submitter_scope: "all_internal",
        allowed_department_ids: [],
        allowed_user_ids: [],
        require_reason: true,
        require_attachment: false,
        allow_attachment: true,
        max_attachments: 10,
        require_needed_date: false,
        show_project_field: false,
        allow_reject: true,
        allow_return: true,
        allow_withdraw: true,
        sla_hours: 24,
        default_priority: "normal",
        requires_execution: false,
        executor_mode: "none",
        executor_user_ids: [],
        executor_department_id: "",
        steps: [
            {
                sequence: 10,
                name: "Phê duyệt bước 1",
                approver_rule: "specific_users",
                approver_user_ids: [],
                sla_hours: 24,
                can_return: true,
                can_reject: true,
            },
        ],
    };
}

export class TpRequestAdmin extends Component {
    static template = "tp_request.Admin";
    static components = { TpRequestList, InlineErrors };
    props = useProps();

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.ICON_CHOICES = ICON_CHOICES;
        this.COLOR_CHOICES = COLOR_CHOICES;

        this.state = proxy({
            activeTab: "types", // 'types' | 'all_requests'
            loading: true,
            error: "",
            data: null,
            searchText: "",
            statusFilter: "all", // 'all' | 'active' | 'missing' | 'inactive'
            // Editor modal
            showEditor: false,
            saving: false,
            editAttempt: 0,
            fieldErrors: [],
            serverError: null,
            form: null,
        });

        onWillStart(() => this.load());
    }

    async load() {
        this.state.loading = true;
        this.state.error = "";
        try {
            this.state.data = await this.orm.call("tp.request", "tp_admin_data", []);
        } catch (err) {
            this.state.error = extractErrorMessage(
                err,
                "Bạn không có quyền truy cập khu vực Quản trị Đề nghị & Phê duyệt."
            );
        } finally {
            this.state.loading = false;
        }
    }

    get missingConfigTypes() {
        return (this.state.data?.types || []).filter((t) => t.active && !t.is_config_ready);
    }

    get filteredTypes() {
        const list = this.state.data?.types || [];
        const needle = foldText(this.state.searchText);
        return list.filter((t) => {
            if (this.state.statusFilter === "active" && !t.active) return false;
            if (this.state.statusFilter === "inactive" && t.active) return false;
            if (this.state.statusFilter === "missing" && (!t.active || t.is_config_ready)) return false;
            if (needle) {
                const hay = foldText(`${t.code} ${t.name} ${t.description} ${t.handler_label}`);
                if (!hay.includes(needle)) return false;
            }
            return true;
        });
    }

    openCreateType() {
        this.state.form = emptyTypeForm();
        this.state.fieldErrors = [];
        this.state.serverError = null;
        this.state.showEditor = true;
    }

    openEditType(t) {
        this.state.form = {
            id: t.id,
            code: t.code,
            name: t.name,
            description: t.description || "",
            guidance: t.guidance || "",
            icon: t.icon || "assignment",
            color: t.color || "#2563EB",
            sequence: t.sequence || 50,
            handler_kind: t.handler_kind || "general",
            submitter_scope: t.submitter_scope || "all_internal",
            allowed_department_ids: [...(t.allowed_department_ids || [])],
            allowed_user_ids: [...(t.allowed_user_ids || [])],
            require_reason: Boolean(t.require_reason),
            require_attachment: Boolean(t.require_attachment),
            allow_attachment: Boolean(t.allow_attachment),
            max_attachments: t.max_attachments || 10,
            require_needed_date: Boolean(t.require_needed_date),
            show_project_field: Boolean(t.show_project_field),
            allow_reject: Boolean(t.allow_reject),
            allow_return: Boolean(t.allow_return),
            allow_withdraw: Boolean(t.allow_withdraw),
            sla_hours: t.sla_hours || 24,
            default_priority: t.default_priority || "normal",
            requires_execution: Boolean(t.requires_execution),
            executor_mode: t.executor_mode || "none",
            executor_user_ids: [...(t.executor_user_ids || [])],
            executor_department_id: t.executor_department_id ? String(t.executor_department_id) : "",
            steps: (t.steps || []).map((s, idx) => ({
                sequence: s.sequence || (idx + 1) * 10,
                name: s.name || `Bước ${idx + 1}`,
                approver_rule: s.approver_rule || "specific_users",
                approver_user_ids: [...(s.approver_user_ids || [])],
                sla_hours: s.sla_hours || 24,
                can_return: Boolean(s.can_return),
                can_reject: Boolean(s.can_reject),
            })),
        };
        this.state.fieldErrors = [];
        this.state.serverError = null;
        this.state.showEditor = true;
    }

    closeEditor() {
        this.state.showEditor = false;
        this.state.form = null;
    }

    onFormInput(key, ev) {
        if (!this.state.form) return;
        const val = ev.target.type === "checkbox" ? ev.target.checked : ev.target.value;
        this.state.form[key] = val;
        if (key === "requires_execution" && !val) {
            this.state.form.executor_mode = "none";
        } else if (key === "requires_execution" && val && this.state.form.executor_mode === "none") {
            this.state.form.executor_mode = "specific_users";
        }
    }

    toggleIdInList(listKey, id, ev) {
        if (!this.state.form) return;
        const set = new Set(this.state.form[listKey] || []);
        if (ev.target.checked) set.add(id);
        else set.delete(id);
        this.state.form[listKey] = [...set];
    }

    addStep() {
        if (!this.state.form) return;
        const nextIdx = this.state.form.steps.length + 1;
        this.state.form.steps.push({
            sequence: nextIdx * 10,
            name: `Phê duyệt bước ${nextIdx}`,
            approver_rule: "specific_users",
            approver_user_ids: [],
            sla_hours: 24,
            can_return: true,
            can_reject: true,
        });
    }

    removeStep(index) {
        if (!this.state.form) return;
        this.state.form.steps.splice(index, 1);
    }

    moveStep(index, delta) {
        if (!this.state.form) return;
        const steps = this.state.form.steps;
        const target = index + delta;
        if (target < 0 || target >= steps.length) return;
        const [item] = steps.splice(index, 1);
        steps.splice(target, 0, item);
        steps.forEach((s, i) => {
            s.sequence = (i + 1) * 10;
        });
    }

    onStepInput(index, key, ev) {
        const st = this.state.form?.steps?.[index];
        if (!st) return;
        st[key] = ev.target.type === "checkbox" ? ev.target.checked : ev.target.value;
    }

    toggleStepUser(index, uid, ev) {
        const st = this.state.form?.steps?.[index];
        if (!st) return;
        const set = new Set(st.approver_user_ids || []);
        if (ev.target.checked) set.add(uid);
        else set.delete(uid);
        st.approver_user_ids = [...set];
    }

    async saveType() {
        const f = this.state.form;
        if (!f || this.state.saving) return;
        this.state.editAttempt += 1;
        this.state.fieldErrors = [];
        this.state.serverError = null;

        const errs = [];
        if (!f.code.trim()) {
            errs.push({ id: "adm_type_code", label: "Mã loại đề nghị", location: "Thông tin cơ bản", message: "Vui lòng nhập Mã loại đề nghị." });
        }
        if (!f.name.trim()) {
            errs.push({ id: "adm_type_name", label: "Tên loại đề nghị", location: "Thông tin cơ bản", message: "Vui lòng nhập Tên loại đề nghị." });
        }
        if (f.handler_kind !== "attendance_correction") {
            f.steps.forEach((s, idx) => {
                if (!s.name.trim()) {
                    errs.push({ id: `adm_step_name_${idx}`, label: `Tên bước ${idx + 1}`, location: "Tuyến phê duyệt", message: `Vui lòng nhập tên cho Bước ${idx + 1}.` });
                }
            });
        }
        if (errs.length) {
            this.state.fieldErrors = errs;
            return;
        }

        this.state.saving = true;
        try {
            const payload = {
                ...f,
                sequence: Number(f.sequence) || 50,
                max_attachments: Number(f.max_attachments) || 10,
                sla_hours: Number(f.sla_hours) || 24,
                executor_department_id: f.executor_department_id ? Number(f.executor_department_id) : false,
                steps: f.steps.map((s, i) => ({
                    ...s,
                    sequence: (i + 1) * 10,
                    sla_hours: Number(s.sla_hours) || 24,
                })),
            };
            const res = await this.orm.call("tp.request", "tp_admin_save_type", [payload]);
            this.notification.add(
                `Đã lưu cấu hình loại đề nghị (phiên bản v${res?.config_version || 1}). Hồ sơ đã gửi trước đó vẫn giữ nguyên tuyến cũ.`,
                { type: "success" }
            );
            this.closeEditor();
            await this.load();
        } catch (err) {
            this.state.serverError = saveError(err, { verb: "lưu cấu hình loại đề nghị" });
        } finally {
            this.state.saving = false;
        }
    }

    async toggleActive(t) {
        try {
            await this.orm.call("tp.request", "tp_admin_toggle_type", [t.id, !t.active]);
            this.notification.add(
                !t.active ? `Đã kích hoạt lại loại "${t.name}".` : `Đã ngừng sử dụng loại "${t.name}" (hồ sơ cũ vẫn giữ nguyên).`,
                { type: "info" }
            );
            await this.load();
        } catch (err) {
            this.notification.add(extractErrorMessage(err, "Không thể đổi trạng thái loại đề nghị."), { type: "danger" });
        }
    }

    userNamesFromIds(ids) {
        const users = this.state.data?.users || [];
        const map = new Map(users.map((u) => [u.id, u.name]));
        return (ids || []).map((id) => map.get(id)).filter(Boolean).join(", ");
    }
}

registry.category("actions").add("tp_request.admin", TpRequestAdmin);
