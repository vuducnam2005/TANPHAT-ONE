import { Component, onMounted, onWillStart, onWillUnmount, proxy } from "@odoo/owl";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { user } from "@web/core/user";
import { useService } from "@web/core/utils/hooks";
import { navigateBack } from "@tp_web_home/back/back_navigation";
import { InlineErrors } from "@tp_web_home/validation/inline_errors";
import { saveError } from "@tp_web_home/validation/validation";

const MAX_AVATAR_BYTES = 5 * 1024 * 1024;

const TABS = [
    { id: "overview", label: "Tổng quan", icon: "grid_view" },
    { id: "personal", label: "Thông tin cá nhân", icon: "person" },
    { id: "resume", label: "Hồ sơ và năng lực", icon: "work" },
    { id: "contract", label: "Hợp đồng lao động", icon: "description" },
    { id: "account", label: "Tài khoản và phân quyền", icon: "verified_user" },
    { id: "history", label: "Lịch sử hoạt động", icon: "history" },
];

const HISTORY_FILTERS = [
    { id: "all", label: "Tất cả" },
    { id: "profile", label: "Hồ sơ & Cá nhân" },
    { id: "role", label: "Vai trò & Phòng ban" },
    { id: "account", label: "Tài khoản" },
];

const EDITABLE_KEYS = [
    "work_email",
    "work_phone",
    "mobile_phone",
    "private_email",
    "private_phone",
    "private_street",
    "private_street2",
    "private_city",
    "private_zip",
    "private_country_id",
    "private_state_id",
    "birthday",
    "birthday_public_display",
    "sex",
    "place_of_birth",
    "country_of_birth",
    "country_id",
    "identification_id",
    "passport_id",
    "passport_expiration_date",
    "emergency_contact",
    "emergency_phone",
    "tp_personal_defaults_confirmed",
    "marital",
    "spouse_complete_name",
    "spouse_birthdate",
    "children",
    "distance_home_work",
    "certificate",
    "study_field",
    "additional_note",
];

function cloneEditableValues(values) {
    const out = {};
    for (const key of EDITABLE_KEYS) {
        out[key] = values?.[key] ?? "";
    }
    return out;
}

export class TpHrMyProfile extends Component {
    static template = "tp_hr_workspace.MyProfile";
    static components = { InlineErrors };

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        this.dialog = useService("dialog");
        this.tpIdentity = useService("tp_identity");

        this.tabs = TABS;
        this.historyFilters = HISTORY_FILTERS;
        this.state = proxy({
            loading: true,
            saving: false,
            editing: false,
            activeTab: "overview",
            historyFilter: "all",
            historyQuery: "",
            docKindFilter: "all",
            docQuery: "",
            data: null,
            form: {},
            initialForm: {},
            states: [],
            pendingImageB64: undefined,
            previewImageUrl: "",
            resumeDraft: null,
            skillDraft: null,
            error: "",
            profileSaveError: null,
            profileAttempt: 0,
            draftAttempted: false,
            draftAttempt: 0,
            draftSaveError: null,
            actionError: null,
            actionAttempt: 0,
        });

        const onBeforeUnload = (ev) => {
            if (this.isDirty) {
                ev.preventDefault();
                ev.returnValue = "";
            }
        };
        onWillStart(() => this.loadProfile());
        onMounted(() => window.addEventListener("beforeunload", onBeforeUnload));
        onWillUnmount(() => window.removeEventListener("beforeunload", onBeforeUnload));
    }

    get isDirty() {
        if (!this.state.editing || !this.state.data?.has_employee) {
            return false;
        }
        if (this.state.pendingImageB64 !== undefined) {
            return true;
        }
        return EDITABLE_KEYS.some(
            (key) => String(this.state.form[key] ?? "") !== String(this.state.initialForm[key] ?? "")
        );
    }

    get avatarSrc() {
        if (this.state.pendingImageB64 === false) {
            return "";
        }
        if (this.state.previewImageUrl) {
            return this.state.previewImageUrl;
        }
        if (this.state.data?.has_employee) {
            return this.tpIdentity.avatarUrl || this.state.data.header?.avatar_url || "";
        }
        return this.tpIdentity.avatarUrl || this.state.data?.user?.avatar_url || "";
    }

    async loadProfile() {
        this.state.loading = true;
        this.state.error = "";
        try {
            const payload = await this.orm.call("res.users", "tp_get_my_profile", []);
            this.applyProfilePayload(payload);
        } catch (err) {
            this.state.error = err?.data?.message || _t("Không thể tải thông tin cá nhân.");
        } finally {
            this.state.loading = false;
        }
    }

    applyProfilePayload(payload) {
        this.state.data = payload;
        if (payload?.has_employee) {
            const snap = cloneEditableValues(payload.values);
            this.state.form = { ...snap };
            this.state.initialForm = { ...snap };
            this.state.states = payload.options?.states || [];
            this.state.pendingImageB64 = undefined;
            this.state.previewImageUrl = "";
        }
    }

    optionLabel(group, value) {
        if (!value) {
            return "Chưa khai báo";
        }
        const list = this.state.data?.options?.[group] || [];
        return list.find((item) => item.value === value)?.label || value;
    }

    countryName(id, fallbackName) {
        if (!id) {
            return "Chưa khai báo";
        }
        const found = (this.state.data?.options?.countries || []).find((c) => c.id === Number(id));
        return found?.name || fallbackName || "Chưa khai báo";
    }

    stateName(id, fallbackName) {
        if (!id) {
            return "Chưa khai báo";
        }
        const found = (this.state.states || []).find((s) => s.id === Number(id));
        return found?.name || fallbackName || "Chưa khai báo";
    }

    setTab(tabId) {
        this.state.activeTab = tabId;
        this.state.actionError = null;
    }

    setHistoryFilter(filterId) {
        this.state.historyFilter = filterId;
    }

    onHistoryQueryInput(ev) {
        this.state.historyQuery = ev.target.value;
    }

    clearHistoryFilters() {
        this.state.historyFilter = "all";
        this.state.historyQuery = "";
    }

    onDocKindChange(ev) {
        this.state.docKindFilter = ev.target.value;
    }

    onDocQueryInput(ev) {
        this.state.docQuery = ev.target.value;
    }

    clearContractDocFilters() {
        this.state.docKindFilter = "all";
        this.state.docQuery = "";
    }

    get filteredContractDocuments() {
        const docs = this.state.data?.contracts?.documents || [];
        const kind = this.state.docKindFilter;
        const q = (this.state.docQuery || "").trim().toLowerCase();
        return docs.filter((doc) => {
            if (kind !== "all" && doc.kind !== kind) {
                return false;
            }
            if (!q) return true;
            const hay = `${doc.number || ""} ${doc.name || ""} ${doc.note || ""} ${doc.signed_date || ""}`.toLowerCase();
            return hay.includes(q);
        });
    }

    get filteredHistory() {
        const items = this.state.data?.history || [];
        const q = (this.state.historyQuery || "").trim().toLowerCase();
        return items.filter((item) => {
            if (this.state.historyFilter !== "all" && item.filter_group !== this.state.historyFilter) {
                return false;
            }
            if (!q) return true;
            const summaryText = Array.isArray(item.summary_lines) ? item.summary_lines.join(" ") : (item.summary || "");
            const hay = `${item.category_label || ""} ${item.title || ""} ${summaryText} ${item.author || ""} ${item.date || ""} ${item.effective_date || ""}`.toLowerCase();
            return hay.includes(q);
        });
    }

    startEdit() {
        if (!this.state.data?.has_employee) {
            return;
        }
        this.state.editing = true;
    }

    onFormInput(field, ev) {
        this.state.form[field] = ev.target.value;
    }

    onDraftInput(draftKey, field, ev) {
        if (this.state[draftKey]) {
            this.state[draftKey][field] = ev.target.value;
        }
    }

    confirmDiscard(title, body, confirmLabel) {
        return new Promise((resolve) => {
            this.dialog.add(ConfirmationDialog, {
                title,
                body,
                confirmLabel,
                cancelLabel: _t("Tiếp tục chỉnh sửa"),
                confirm: () => resolve(true),
                cancel: () => resolve(false),
                dismiss: () => resolve(false),
            });
        });
    }

    async cancelEdit() {
        if (
            this.isDirty &&
            !(await this.confirmDiscard(
                _t("Bỏ thay đổi chưa lưu?"),
                _t("Các thay đổi của bạn chưa được lưu."),
                _t("Bỏ thay đổi")
            ))
        ) {
            return;
        }
        this.state.form = { ...this.state.initialForm };
        this.state.pendingImageB64 = undefined;
        this.state.previewImageUrl = "";
        this.state.profileSaveError = null;
        this.state.editing = false;
    }

    async onPrivateCountryChange(ev) {
        const countryId = ev.target.value ? Number(ev.target.value) : false;
        this.state.form.private_country_id = countryId;
        this.state.form.private_state_id = false;
        if (!countryId) {
            this.state.states = [];
            return;
        }
        try {
            const rows = await this.orm.searchRead(
                "res.country.state",
                [["country_id", "=", countryId]],
                ["id", "name", "country_id"],
                { order: "name, id" }
            );
            this.state.states = rows.map((r) => ({
                id: r.id,
                name: r.name,
                country_id: Array.isArray(r.country_id) ? r.country_id[0] : r.country_id,
            }));
        } catch {
            this.state.states = [];
        }
    }

    onAvatarFileChange(ev) {
        const file = ev.target.files?.[0];
        ev.target.value = "";
        if (!file) {
            return;
        }
        if (!["image/png", "image/jpeg", "image/gif", "image/webp"].includes(file.type)) {
            this.notification.add(_t("Chỉ hỗ trợ tệp ảnh PNG, JPG, GIF hoặc WebP."), { type: "warning" });
            return;
        }
        if (file.size > MAX_AVATAR_BYTES) {
            this.notification.add(_t("Dung lượng ảnh tối đa là 5 MB."), { type: "warning" });
            return;
        }
        const reader = new FileReader();
        reader.onload = () => {
            const dataUrl = String(reader.result || "");
            const idx = dataUrl.indexOf(",");
            if (idx === -1) {
                return;
            }
            this.state.pendingImageB64 = dataUrl.slice(idx + 1);
            this.state.previewImageUrl = dataUrl;
        };
        reader.readAsDataURL(file);
    }

    clearAvatarSelection() {
        this.state.pendingImageB64 = false;
        this.state.previewImageUrl = "";
    }

    async saveProfile() {
        if (this.state.saving || !this.state.data?.has_employee) {
            return;
        }
        const diff = {};
        if (this.state.pendingImageB64 !== undefined) {
            diff.image_1920 = this.state.pendingImageB64;
        }
        for (const key of EDITABLE_KEYS) {
            const cur = this.state.form[key];
            const prev = this.state.initialForm[key];
            if (String(cur ?? "") !== String(prev ?? "")) {
                if (
                    ["private_country_id", "private_state_id", "country_of_birth", "country_id"].includes(key)
                ) {
                    diff[key] = cur ? Number(cur) : false;
                } else if (["children", "distance_home_work"].includes(key)) {
                    diff[key] = cur === "" || cur === false ? 0 : Number(cur);
                } else if (["birthday_public_display", "tp_personal_defaults_confirmed"].includes(key)) {
                    diff[key] = Boolean(cur);
                } else {
                    diff[key] = cur === "" ? false : cur;
                }
            }
        }
        if (!Object.keys(diff).length) {
            this.state.editing = false;
            return;
        }
        this.state.saving = true;
        this.state.profileSaveError = null;
        try {
            const payload = await this.orm.call("res.users", "tp_save_my_profile", [diff]);
            this.applyProfilePayload(payload);
            this.state.editing = false;
            if ("image_1920" in diff) {
                this.tpIdentity.resetAvatarFailure();
                this.tpIdentity.state.revision += 1;
            }
            this.notification.add(_t("Đã cập nhật và đồng bộ với Hồ sơ nhân sự."), {
                title: _t("Lưu thành công"),
                type: "success",
            });
        } catch (err) {
            this.state.profileSaveError = saveError(err);
            this.state.profileAttempt++;
        } finally {
            this.state.saving = false;
        }
    }

    openResumeModal(line = null) {
        this.state.draftAttempted = false; this.state.draftSaveError = null;
        const types = this.state.data?.resume?.resume_types || [];
        this.state.resumeDraft = {
            id: line?.id || null,
            name: line?.name || "",
            line_type_id: line?.line_type_id || (types[0]?.id || ""),
            date_start: line?.date_start || new Date().toISOString().slice(0, 10),
            date_end: line?.date_end || "",
            description: line?.description || "",
        };
    }

    closeResumeModal() {
        this.state.resumeDraft = null;
    }

    async saveResumeDraft() {
        const d = this.state.resumeDraft;
        if (!d) {
            return;
        }
        this.state.draftAttempted = true; this.state.draftSaveError = null;
        if (this.draftErrors.length) { this.state.draftAttempt++; return; }
        this.state.saving = true;
        try {
            const payload = await this.orm.call("res.users", "tp_save_my_resume_line", [
                d.id,
                {
                    name: d.name,
                    line_type_id: d.line_type_id ? Number(d.line_type_id) : false,
                    date_start: d.date_start,
                    date_end: d.date_end || false,
                    description: d.description,
                },
            ]);
            this.applyProfilePayload(payload);
            this.state.resumeDraft = null;
            this.notification.add(_t("Đã cập nhật mục hồ sơ năng lực."), { type: "success" });
        } catch (err) {
            this.state.draftSaveError = saveError(err);
            this.state.draftAttempt++;
        } finally {
            this.state.saving = false;
        }
    }

    async deleteResumeLine(line) {
        const ok = await this.confirmDiscard(
            _t("Xóa mục hồ sơ năng lực?"),
            _t("Mục \"%s\" sẽ bị xóa khỏi hồ sơ của bạn.", line.name),
            _t("Xóa")
        );
        if (!ok) {
            return;
        }
        this.state.actionError = null;
        try {
            const payload = await this.orm.call("res.users", "tp_delete_my_resume_line", [line.id]);
            this.applyProfilePayload(payload);
            this.notification.add(_t("Đã xóa mục hồ sơ năng lực."), { type: "success" });
        } catch (err) {
            this.showActionError("resume", err, { verb: "xóa", note: "Danh sách chưa thay đổi." });
        }
    }

    get filteredSkillsForDraft() {
        const typeId = Number(this.state.skillDraft?.skill_type_id || 0);
        return (this.state.data?.resume?.skills_catalog || []).filter((s) => s.skill_type_id === typeId);
    }

    get filteredLevelsForDraft() {
        const typeId = Number(this.state.skillDraft?.skill_type_id || 0);
        return (this.state.data?.resume?.skill_levels || []).filter((l) => l.skill_type_id === typeId);
    }

    openSkillModal() {
        this.state.draftAttempted = false; this.state.draftSaveError = null;
        const types = this.state.data?.resume?.skill_types || [];
        const firstTypeId = types[0]?.id || "";
        const firstSkill = (this.state.data?.resume?.skills_catalog || []).find(
            (s) => s.skill_type_id === Number(firstTypeId)
        );
        const firstLevel = (this.state.data?.resume?.skill_levels || []).find(
            (l) => l.skill_type_id === Number(firstTypeId)
        );
        this.state.skillDraft = {
            id: null,
            skill_type_id: firstTypeId,
            skill_id: firstSkill?.id || "",
            skill_level_id: firstLevel?.id || "",
        };
    }

    onSkillTypeChange(ev) {
        const typeId = Number(ev.target.value || 0);
        this.state.skillDraft.skill_type_id = typeId;
        const firstSkill = (this.state.data?.resume?.skills_catalog || []).find(
            (s) => s.skill_type_id === typeId
        );
        const firstLevel = (this.state.data?.resume?.skill_levels || []).find(
            (l) => l.skill_type_id === typeId
        );
        this.state.skillDraft.skill_id = firstSkill?.id || "";
        this.state.skillDraft.skill_level_id = firstLevel?.id || "";
    }

    closeSkillModal() {
        this.state.skillDraft = null;
    }

    async saveSkillDraft() {
        const d = this.state.skillDraft;
        if (!d) {
            return;
        }
        this.state.draftAttempted = true; this.state.draftSaveError = null;
        if (this.draftErrors.length) { this.state.draftAttempt++; return; }
        this.state.saving = true;
        try {
            const payload = await this.orm.call("res.users", "tp_save_my_skill", [
                d.id,
                {
                    skill_type_id: Number(d.skill_type_id),
                    skill_id: Number(d.skill_id),
                    skill_level_id: Number(d.skill_level_id),
                },
            ]);
            this.applyProfilePayload(payload);
            this.state.skillDraft = null;
            this.notification.add(_t("Đã cập nhật kỹ năng cá nhân."), { type: "success" });
        } catch (err) {
            this.state.draftSaveError = saveError(err);
            this.state.draftAttempt++;
        } finally {
            this.state.saving = false;
        }
    }

    get draftErrors() {
        if (!this.state.draftAttempted) return [];
        const errors = [], resume = this.state.resumeDraft, skill = this.state.skillDraft;
        const add = (id, label, message) => errors.push({id, label, message, location: "Hồ sơ và năng lực"});
        // These mirror tp_save_my_resume_line/tp_save_my_skill; backend remains authoritative.
        if (resume) {
            if (!resume.name.trim()) add("tp_resume_name", "Tiêu đề / Chức danh / Bằng cấp", "Vui lòng nhập tiêu đề mục hồ sơ năng lực.");
            if (!resume.date_start) add("tp_resume_start", "Từ ngày", "Vui lòng chọn ngày bắt đầu.");
            if (resume.date_start && resume.date_end && resume.date_end < resume.date_start) add("tp_resume_end", "Đến ngày", "Ngày kết thúc phải lớn hơn hoặc bằng ngày bắt đầu.");
        }
        if (skill) for (const [key, label] of [["skill_type_id", "Loại kỹ năng"], ["skill_id", "Kỹ năng"], ["skill_level_id", "Mức độ"]]) {
            if (!Number(skill[key])) add("tp_skill_" + key, label, "Vui lòng chọn " + label + ".");
        }
        return errors;
    }
    draftFieldError(id) { return this.draftErrors.find(e => e.id === id)?.message || ""; }

    async deleteSkill(skillRec) {
        const ok = await this.confirmDiscard(
            _t("Xóa kỹ năng?"),
            _t("Kỹ năng \"%s\" sẽ bị xóa khỏi hồ sơ của bạn.", skillRec.skill_name),
            _t("Xóa")
        );
        if (!ok) {
            return;
        }
        this.state.actionError = null;
        try {
            const payload = await this.orm.call("res.users", "tp_delete_my_skill", [skillRec.id]);
            this.applyProfilePayload(payload);
            this.notification.add(_t("Đã xóa kỹ năng."), { type: "success" });
        } catch (err) {
            this.showActionError("skill", err, { verb: "xóa", note: "Danh sách chưa thay đổi." });
        }
    }

    async openAccountSecurityPreferences() {
        this.state.actionError = null;
        try {
            const actionDescription = await this.orm.call("res.users", "action_get", []);
            actionDescription.res_id = user.userId;
            await this.action.doAction(actionDescription);
        } catch (err) {
            this.showActionError("security", err, {
                verb: "mở cài đặt bảo mật", write: false, note: "Tài khoản chưa thay đổi.",
            });
        }
    }

    /** FORM-VALIDATION-002: a failed action is explained inside the card the user acted on. */
    showActionError(area, error, options) {
        this.state.actionError = { area, ...saveError(error, options) };
        this.state.actionAttempt++;
    }
    actionErrorFor(area) {
        return this.state.actionError?.area === area ? this.state.actionError : null;
    }

    async goBack() {
        if (
            this.isDirty &&
            !(await this.confirmDiscard(
                _t("Bỏ thay đổi chưa lưu?"),
                _t("Bạn có thay đổi chưa lưu. Vẫn rời khỏi trang này?"),
                _t("Rời trang")
            ))
        ) {
            return;
        }
        this.state.editing = false;
        // UI-BACK-001: same return rule as the shared detail-screen button (previous screen, else Home).
        return navigateBack(this.env, this.action);
    }
}

registry.category("actions").add("tp_hr_workspace.my_profile", TpHrMyProfile);
registry.category("tp_personal_profile").add("handler", async (env) => {
    return await env.services.action.doAction("tp_hr_workspace.action_my_profile");
});
