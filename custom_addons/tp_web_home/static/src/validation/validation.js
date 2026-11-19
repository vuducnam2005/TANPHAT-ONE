import { Component, onMounted, onPatched, onWillUnmount, signal, t, useProps } from "@odoo/owl";
import { ConnectionLostError } from "@web/core/network/rpc";
import { evaluateBooleanExpr } from "@web/core/py_js/py";
import { patch } from "@web/core/utils/patch";
import { createElement } from "@web/core/utils/xml";
import { Notebook } from "@web/core/notebook/notebook";
import { Record } from "@web/model/relational_model/record";
import { Field } from "@web/views/fields/field";
import { FormArchParser } from "@web/views/form/form_arch_parser";
import { FormCompiler } from "@web/views/form/form_compiler";
import { FormLabel } from "@web/views/form/form_label";
import { FormRenderer } from "@web/views/form/form_renderer";
import { ListRenderer } from "@web/views/list/list_renderer";

// One presenter for Odoo's own validity state: it never decides what is required.
// Required/invalid fields come from Record._checkValidity and widget parsing; save
// errors come from the server. Odoo still validates every save on the backend.

const presenters = new WeakMap();
const listRenderers = new WeakMap();
const X2MANY = new Set(["one2many", "many2many"]);
const CHOICE = new Set(["many2one", "many2many", "one2many", "selection", "reference", "date", "datetime"]);
// Odoo never blocks these types for "required": 0 and False are real values.
const NEVER_EMPTY = new Set(["boolean", "integer", "float", "monetary"]);
const DUPLICATE = /trùng|đã tồn tại|đã được sử dụng|đã được dùng|duplicate|already exists|must be unique|unique/i;
const MISSING = /vui lòng (nhập|chọn)|bắt buộc|còn thiếu|is required|required field|missing/i;
const DATE = /ngày|date|thời gian|thời hạn/i;
const nextFrame = () => new Promise((resolve) => requestAnimationFrame(resolve));

async function waitFor(find, timeout = 1500) {
    const end = Date.now() + timeout;
    for (let found = find(); ; found = find()) {
        if (found || Date.now() > end) return found;
        await nextFrame();
    }
}

/** True once a save/validation of this record (or a parent holding it) failed. */
export function attempted(record) {
    return Boolean(record && (record._tpValidationAttempted || attempted(record._parentRecord)));
}

export function fieldMessage(record, name, label, info) {
    const field = record.fields[name];
    if (record._isInvisible(name)) {
        return "Thông tin bắt buộc này không hiển thị nên không thể nhập. Vui lòng liên hệ người quản trị.";
    }
    // The node the user sees may be read-only even when another copy of the field is not.
    if (record._isReadonly(name) || (info && evaluateBooleanExpr(info.readonly, record.evalContextWithVirtualIds))) {
        return "Thông tin bắt buộc này đang khóa với tài khoản của bạn. Vui lòng liên hệ người quản trị.";
    }
    if (X2MANY.has(field.type)) {
        const list = record.data[name];
        return record._unsetRequiredFields.has(name) && !list?.count
            ? `Vui lòng thêm ít nhất một dòng ${label}.`
            : `Bảng ${label} có dòng chưa hợp lệ. Mở bảng để kiểm tra các dòng được đánh dấu.`;
    }
    if (record._unsetRequiredFields.has(name)) {
        return `Vui lòng ${CHOICE.has(field.type) ? "chọn" : "nhập"} ${label}.`;
    }
    // Not a missing value: the widget could not parse what was typed.
    if (["date", "datetime"].includes(field.type)) {
        return "Ngày chưa đúng định dạng. Vui lòng nhập lại theo mẫu ngày đang dùng hoặc chọn trong lịch.";
    }
    if (NEVER_EMPTY.has(field.type)) {
        return `Vui lòng nhập ${label} là số hợp lệ.`;
    }
    return `Giá trị ${label} chưa đúng định dạng. Vui lòng kiểm tra lại.`;
}

/**
 * Classify a failed server call; business messages from the backend are kept verbatim.
 * `verb` names what the user tried ("lưu", "xóa", "mở hồ sơ"…). `write: false` marks a call
 * that changes nothing, so a lost connection leaves no doubt about the outcome. `note`
 * replaces the closing line when the screen has no typed data to keep.
 */
export function saveError(error, { verb = "lưu", write = true, note = "" } = {}) {
    const name = error?.data?.name || error?.exceptionName || "";
    const backend = (error?.data?.message || "").trim();
    const result = (kind, title, message) => (note ? { kind, title, message, note } : { kind, title, message });
    if (error instanceof ConnectionLostError || /ConnectionLost|ConnectionAborted|NetworkError/.test(name)) {
        return result("connection", "Lỗi kết nối", write
            ? `Chưa xác nhận được kết quả ${verb}. Kiểm tra kết nối rồi tải lại để xem dữ liệu hiện tại trước khi thử lại.`
            : `Chưa kết nối được máy chủ nên chưa ${verb} được. Kiểm tra kết nối rồi thử lại.`);
    }
    if (/AccessError|AccessDenied/.test(name)) {
        return result("access", `Không có quyền ${verb}`,
            backend || "Tài khoản của bạn không có quyền thực hiện thao tác này. Vui lòng liên hệ người quản trị.");
    }
    if (/MissingError/.test(name)) {
        return result("missing", "Bản ghi không còn tồn tại",
            backend || "Bản ghi có thể đã bị xóa. Vui lòng tải lại trang trước khi thử lại.");
    }
    if (/ValidationError/.test(name)) {
        const kind = DUPLICATE.test(backend) ? "duplicate" : MISSING.test(backend) ? "required"
            : DATE.test(backend) ? "date" : "validation";
        const title = { duplicate: "Giá trị bị trùng", required: "Còn thiếu thông tin bắt buộc",
            date: "Ngày tháng không hợp lệ", validation: "Dữ liệu chưa hợp lệ" }[kind];
        return result(kind, title, backend || "Máy chủ từ chối dữ liệu. Vui lòng kiểm tra lại thông tin đã nhập.");
    }
    if (/UserError|RedirectWarning/.test(name)) {
        return result("business", `Máy chủ từ chối ${verb}`, backend || "Thao tác chưa được chấp nhận.");
    }
    return result("system", `Lỗi hệ thống khi ${verb}`,
        `Hệ thống chưa ${verb} được. Thử lại sau ít phút hoặc liên hệ người quản trị kèm thời điểm xảy ra lỗi.`);
}

/** The label the user reads beside a field: its separate visible <label for>, else the field string. */
function labelFor(info, record, name) {
    const context = record.evalContextWithVirtualIds;
    const labels = info?.tpLabels || [];
    const label = labels.find((l) => !evaluateBooleanExpr(l.invisible || "False", context)) || labels[0];
    return label?.string || info?.string || record.fields[name]?.string || "Thông tin";
}

/** The view node the user actually sees for a field: [fieldId, fieldInfo]. */
function infoFor(arch, name, record) {
    const candidates = Object.entries(arch?.fieldNodes || {}).filter(([, f]) => f.name === name);
    const context = record.evalContextWithVirtualIds;
    return candidates.find(([, f]) => !evaluateBooleanExpr(f.invisible, context)) || candidates[0] || [];
}

function locationFor(arch, name, fieldId) {
    const nodes = [...(arch?.xmlDoc?.querySelectorAll("field") || [])].filter(
        (el) => el.getAttribute("name") === name && !el.parentElement?.closest("field"));
    const node = nodes.find((el) => fieldId && el.getAttribute("field_id") === fieldId) || nodes[0];
    const parts = [];
    for (let el = node?.parentElement; el; el = el.parentElement) {
        if (["page", "group"].includes(el.tagName) && el.getAttribute("string")) {
            parts.unshift(el.getAttribute("string"));
        }
    }
    return parts;
}

function subArch(info) {
    return info?.views?.[info.viewMode] || info?.views?.list || info?.views?.kanban || info?.views?.form;
}

/**
 * Every invalid field of a record, including all invalid loaded x2many rows.
 * Labels come from the view the user sees; hidden fields never expose their name.
 */
export function collectErrors(record, arch, prefix = [], path = [], seen = new Set(), inRow = false) {
    if (!record || seen.has(record)) return [];
    seen.add(record);
    const errors = [];
    for (const name of Object.keys(record.activeFields)) {
        const field = record.fields[name];
        if (!field) continue;
        const invalid = record._invalidFields.has(name);
        const list = X2MANY.has(field.type) ? record.data[name] : null;
        const rows = list?.records?.filter((row) => row._invalidFields?.size) || [];
        if (!invalid && !rows.length) continue;
        const [fieldId, info] = infoFor(arch, name, record);
        const hidden = record._isInvisible(name);
        const label = hidden ? "Thông tin không hiển thị" : labelFor(info, record, name);
        const location = [...prefix, ...(hidden ? [] : locationFor(arch, name, fieldId))];
        const nested = [];
        for (const row of rows) {
            const rowLabel = `${label} — dòng ${(list.offset || 0) + list.records.indexOf(row) + 1}`;
            // The table label already names where the row lives; do not repeat it as a location.
            const rowPrefix = location.filter((part) => part !== label);
            for (const error of collectErrors(row, subArch(info), rowPrefix, [...path, { name, record: row, list }], seen, true)) {
                nested.push({ ...error, label: `${rowLabel}: ${error.label}` });
            }
        }
        if (nested.length) {
            errors.push(...nested);
        } else if (invalid) {
            errors.push({ key: `${record.id}:${name}`, record, name, label, hidden, path,
                location: location.join(" / ") || (inRow ? "" : "Thông tin chung"), message: fieldMessage(record, name, label, info) });
        }
    }
    return errors;
}

export class ValidationSummary extends Component {
    static template = "tp_web_home.ValidationSummary";
    props = useProps({ record: t.any(), arch: t.any().optional(), scope: t.string().optional() });
    section = signal.ref();

    setup() {
        let shownAttempt = 0;
        const reveal = () => {
            const attempt = this.props.record?._tpAttempts || 0;
            if (attempt !== shownAttempt && this.section()) {
                // Bring the summary into view once per failed save, without moving focus.
                this.section().scrollIntoView({ block: "nearest", inline: "nearest" });
            }
            shownAttempt = attempt;
        };
        onMounted(reveal);
        onPatched(reveal);
    }

    get isList() {
        return this.props.scope === "list";
    }

    get errors() {
        const { record } = this.props;
        if (!record) return [];
        // In editable lists, the row summary yields to the parent form summary.
        const shown = this.isList ? record._tpValidationAttempted && !attempted(record._parentRecord) : attempted(record);
        return shown ? collectErrors(record, this.props.arch) : [];
    }

    get server() {
        return this.props.record?._tpSaveError;
    }

    get showHint() {
        const { record } = this.props;
        if (this.isList || !record?.isNew || !record.isInEdition) return false;
        return Object.keys(record.activeFields).some((name) =>
            !NEVER_EMPTY.has(record.fields[name]?.type) && record._isRequired(name) &&
            !record._isInvisible(name) && !record._isReadonly(name));
    }

    async focusError(error, ev) {
        if (error.hidden) return;
        let region = ev.currentTarget.closest(".o_form_renderer, .o_list_renderer");
        for (const step of [...error.path, { name: error.name }]) {
            const find = () => [...region.querySelectorAll(".o_field_widget[name], td[name]")].find(
                (el) => el.getAttribute("name") === step.name && el.isConnected);
            // Notebooks only render the active page: open the page that holds the field.
            for (let depth = 0; depth < 6 && !find(); depth++) {
                const tab = [...region.querySelectorAll('[role="tab"][data-tp-fields]')].find((el) =>
                    !el.classList.contains("active") && el.dataset.tpFields.split(" ").includes(step.name));
                if (!tab) break;
                tab.click();
                await waitFor(find, 300);
            }
            const field = find();
            if (!field) return;
            for (let parent = field.parentElement; parent && parent !== region; parent = parent.parentElement) {
                if (parent.tagName === "DETAILS") parent.open = true;
            }
            if (!step.record) {
                field.scrollIntoView({ block: "center", inline: "nearest" });
                const input = field.querySelector(
                    'input:not([type="hidden"]):not(:disabled), select:not(:disabled), textarea:not(:disabled), [contenteditable="true"]');
                (input || Object.assign(field, { tabIndex: -1 })).focus({ preventScroll: true });
                return;
            }
            const renderer = listRenderers.get(step.list);
            const rowId = step.record.id;
            if (!renderer) {
                field.scrollIntoView({ block: "center", inline: "nearest" });
                return;
            }
            if (renderer.props.editable) {
                await step.list.enterEditMode(step.record);
                region = await waitFor(() => [...field.querySelectorAll("tr[data-id]")].find((el) => el.dataset.id === rowId));
            } else {
                await renderer.props.openRecord(step.record);
                region = await waitFor(() => [...document.querySelectorAll(".modal .o_form_renderer")].find((el) =>
                    [...el.querySelectorAll("[data-tp-record]")].some((node) => node.dataset.tpRecord === rowId)));
            }
            if (!region) return;
        }
    }
}

function registerPresenter(model) {
    onMounted(() => presenters.set(model, (presenters.get(model) || 0) + 1));
    onWillUnmount(() => presenters.set(model, Math.max(0, (presenters.get(model) || 0) - 1)));
}

patch(Record.prototype, {
    _displayInvalidFieldNotification() {
        this._tpValidationAttempted = true;
        this._tpAttempts = (this._tpAttempts || 0) + 1;
        // Multi-edit discards the record right away, so keep Odoo's notification there.
        const multiEdit = this.model.multiEdit && this.selected;
        return presenters.get(this.model) && !multiEdit ? () => {} : super._displayInvalidFieldNotification(...arguments);
    },
    _checkValidity(options = {}) {
        const valid = super._checkValidity(...arguments);
        if (!valid && !options.silent && (options.displayNotification || attempted(this))) {
            // Native every() stops at the first invalid row: check the other dirty rows too.
            for (const name of this._invalidFields) {
                if (X2MANY.has(this.fields[name]?.type)) {
                    for (const row of this.data[name].records) {
                        if (row.dirty) row._checkValidity({ ...options, displayNotification: false });
                    }
                }
            }
        }
        return valid;
    },
    async _save(options = {}) {
        this._tpSaveError = null;
        const params = { ...options };
        if (options.onError) {
            // Only wrap an existing handler, so Odoo's own reload-then-throw path is unchanged.
            params.onError = (error, handlers) => {
                this._tpFailSave(error);
                return options.onError(error, handlers);
            };
        }
        try {
            const saved = await super._save(params);
            if (saved) this._tpValidationAttempted = false;
            return saved;
        } catch (error) {
            this._tpFailSave(error);
            throw error;
        }
    },
    _tpFailSave(error) {
        this._tpSaveError = saveError(error);
        this._tpAttempts = (this._tpAttempts || 0) + 1;
    },
    _discard() {
        const result = super._discard(...arguments);
        this._tpValidationAttempted = false;
        this._tpSaveError = null;
        return result;
    },
});

patch(FormRenderer.prototype, {
    setup() {
        super.setup(...arguments);
        registerPresenter(this.props.record.model);
    },
    get tpValidationSummary() {
        return ValidationSummary;
    },
});

patch(FormCompiler.prototype, {
    compileForm() {
        const form = super.compileForm(...arguments);
        const summary = createElement("t", {
            "t-component": "__comp__.tpValidationSummary",
            record: "__comp__.props.record",
            arch: "__comp__.props.archInfo",
            scope: "'form'",
        });
        const sheet = [...form.querySelectorAll("div")].find((el) =>
            (el.getAttribute("class") || "").split(/\s+/).includes("o_form_sheet"));
        (sheet || form).prepend(summary);
        return form;
    },
});

patch(ListRenderer.prototype, {
    setup() {
        super.setup(...arguments);
        registerPresenter(this.props.list.model);
        onMounted(() => listRenderers.set(this.props.list, this));
        onWillUnmount(() => listRenderers.delete(this.props.list));
    },
    get tpValidationSummary() {
        return ValidationSummary;
    },
});

patch(Field.prototype, {
    get tpValidationMessage() {
        const { record, name, fieldInfo } = this.props;
        if (fieldInfo?.viewType !== "form" || !attempted(record) || !record.isFieldInvalid(name)) return "";
        return fieldMessage(record, name, labelFor(fieldInfo, record, name));
    },
});

patch(FormArchParser.prototype, {
    parse() {
        const archInfo = super.parse(...arguments);
        // A separate <label for="field"> is what the user reads (e.g. "Danh xưng"), not the model string.
        const labels = [...archInfo.xmlDoc.querySelectorAll("label[for][string]")].filter(
            (el) => !el.parentElement?.closest("field"));
        for (const info of Object.values(archInfo.fieldNodes)) {
            const own = labels.filter((el) => el.getAttribute("for") === info.name);
            if (own.length) {
                info.tpLabels = own.map((el) => ({ string: el.getAttribute("string"), invisible: el.getAttribute("invisible") }));
            }
        }
        return archInfo;
    },
});

patch(FormLabel.prototype, {
    get tpRequired() {
        const { record, fieldName, fieldInfo } = this.props;
        if (!record.isInEdition || NEVER_EMPTY.has(record.fields[fieldName]?.type)) return false;
        const context = record.evalContextWithVirtualIds;
        return evaluateBooleanExpr(fieldInfo.required, context) && !evaluateBooleanExpr(fieldInfo.readonly, context);
    },
});

patch(Notebook.prototype, {
    tpTabFields(navItem) {
        return (navItem[1].fieldNames || []).join(" ");
    },
    tpErrorCount(navItem) {
        const record = this.env.model?.root;
        const names = navItem[1].fieldNames || [];
        if (!attempted(record) || !names.every((name) => name in record.activeFields)) return 0;
        return names.reduce((count, name) => {
            const rows = X2MANY.has(record.fields[name]?.type) ? record.data[name].records : [];
            const rowErrors = rows.reduce((sum, row) => sum + collectErrors(row).length, 0);
            return count + (rowErrors || (record.isFieldInvalid(name) ? 1 : 0));
        }, 0);
    },
});
