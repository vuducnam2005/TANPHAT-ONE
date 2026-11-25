/** @odoo-module **/
import { Component, onWillStart, proxy, useProps } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { InlineErrors } from "@tp_web_home/validation/inline_errors";
import { saveError } from "@tp_web_home/validation/validation";
import { formatFileSize } from "../prefs";

export class TpRequestCreateModal extends Component {
    static template = "tp_request.CreateModal";
    static components = { InlineErrors };
    props = useProps();

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.formatFileSize = formatFileSize;

        this.state = proxy({
            loading: true,
            step: "pick", // 'pick' | 'form'
            bootstrap: null,
            selectedType: null,
            preview: null,
            previewLoading: false,
            submitting: false,
            uploading: false,
            attempt: 0,
            fieldErrors: [],
            serverError: null,
            form: {
                title: "",
                description: "",
                priority: "normal",
                needed_date: "",
                project_id: "",
                follower_user_ids: [],
                equipment_id: "",
                equipment_category_id: "",
                equipment_quantity: 1,
                equipment_desired_spec: "",
                equipment_issue_detail: "",
                it_category: "",
                it_device_id: "",
                it_urgency_impact: "self",
                att_work_date: "",
                att_requested_in: "08:30",
                att_requested_out: "17:00",
                leave_kind: "annual",
                leave_date_from: "",
                leave_date_to: "",
                leave_days_count: 1,
                leave_handover_note: "",
                trip_destination: "",
                trip_transport: "",
                expense_kind: "advance",
                requested_amount: "",
                beneficiary_note: "",
            },
            attachments: [],
        });

        onWillStart(() => this.loadBootstrap());
    }

    async loadBootstrap() {
        this.state.loading = true;
        this.state.serverError = null;
        try {
            const data = await this.orm.call("tp.request", "tp_create_bootstrap", []);
            this.state.bootstrap = data;
            if (this.props.initialTypeId) {
                const found = (data.types || []).find((t) => t.id === Number(this.props.initialTypeId));
                if (found) {
                    await this.selectType(found);
                }
            }
        } catch (err) {
            this.state.serverError = saveError(err, { verb: "tải biểu mẫu đề nghị", write: false });
        } finally {
            this.state.loading = false;
        }
    }

    async selectType(typeCard) {
        this.state.selectedType = typeCard;
        this.state.step = "form";
        this.state.fieldErrors = [];
        this.state.serverError = null;
        this.state.form.priority = typeCard.default_priority || "normal";
        if (typeCard.handler_kind === "attendance_correction" && !this.state.form.att_work_date) {
            const today = new Date().toISOString().slice(0, 10);
            this.state.form.att_work_date = today;
            if (!this.state.form.title) {
                this.state.form.title = `Đề nghị điều chỉnh công ngày ${today.split("-").reverse().join("/")}`;
            }
        } else if (["leave_request", "business_trip"].includes(typeCard.handler_kind) && !this.state.form.leave_date_from) {
            const today = new Date().toISOString().slice(0, 10);
            this.state.form.leave_date_from = today;
            this.state.form.leave_date_to = today;
            this.state.form.leave_days_count = 1;
        }
        await this.loadPreview();
    }

    backToPick() {
        this.state.step = "pick";
        this.state.fieldErrors = [];
        this.state.serverError = null;
    }

    async loadPreview() {
        if (!this.state.selectedType) return;
        this.state.previewLoading = true;
        try {
            this.state.preview = await this.orm.call("tp.request", "tp_preview_route", [
                this.state.selectedType.id,
                this.state.form.project_id ? Number(this.state.form.project_id) : false,
            ]);
        } catch (err) {
            this.state.preview = null;
            this.state.serverError = saveError(err, { verb: "xem trước tuyến duyệt", write: false });
        } finally {
            this.state.previewLoading = false;
        }
    }

    onFieldInput(field, ev) {
        this.state.form[field] = ev.target.value;
        this.clearFieldError(field);
        if (field === "project_id") {
            this.loadPreview();
        } else if (field === "leave_date_from" || field === "leave_date_to") {
            const lf = this.state.form.leave_date_from;
            const lt = this.state.form.leave_date_to;
            if (lf && lt && lt >= lf) {
                const diffDays = Math.round((new Date(lt) - new Date(lf)) / 86400000) + 1;
                if (diffDays > 0) {
                    this.state.form.leave_days_count = diffDays;
                }
            }
        }
    }

    clearFieldError(fieldKey) {
        const idMap = {
            title: "req_title",
            description: "req_description",
            needed_date: "req_needed_date",
            att_work_date: "req_att_work_date",
            att_requested_in: "req_att_in",
            att_requested_out: "req_att_out",
            equipment_id: "req_equipment_id",
            equipment_category_id: "req_equip_category",
            equipment_desired_spec: "req_equip_category",
            equipment_issue_detail: "req_equip_issue",
            equipment_quantity: "req_equip_qty",
            it_category: "req_it_category",
            leave_date_from: "req_leave_from",
            leave_date_to: "req_leave_to",
            leave_days_count: "req_leave_days",
            trip_destination: "req_trip_dest",
            requested_amount: "req_expense_amount",
        };
        const targetId = idMap[fieldKey];
        if (targetId && this.state.fieldErrors.length) {
            this.state.fieldErrors = this.state.fieldErrors.filter((e) => e.id !== targetId);
        }
    }

    hasError(fieldId) {
        return this.state.fieldErrors.some((e) => e.id === fieldId);
    }

    errorMessage(fieldId) {
        return this.state.fieldErrors.find((e) => e.id === fieldId)?.message || "";
    }

    toggleFollower(uid) {
        const list = [...this.state.form.follower_user_ids];
        const idx = list.indexOf(uid);
        if (idx >= 0) {
            list.splice(idx, 1);
        } else {
            list.push(uid);
        }
        this.state.form.follower_user_ids = list;
    }

    isFollowerSelected(uid) {
        return this.state.form.follower_user_ids.includes(uid);
    }

    async onFileSelected(ev) {
        const files = [...(ev.target.files || [])];
        ev.target.value = "";
        if (!files.length) return;
        this.state.uploading = true;
        this.state.serverError = null;
        try {
            const csrf = odoo?.csrf_token || "";
            for (const file of files) {
                const fd = new FormData();
                fd.append("file", file);
                fd.append("csrf_token", csrf);
                const resp = await fetch("/tp_request/attachment/upload", { method: "POST", body: fd });
                const json = await resp.json();
                if (!resp.ok || !json.ok) {
                    this.state.serverError = {
                        kind: "validation",
                        title: "Không tải lên được tệp đính kèm",
                        message: json.error || "Định dạng hoặc dung lượng tệp không hợp lệ.",
                    };
                    break;
                }
                this.state.attachments.push(json.attachment);
                this.state.fieldErrors = this.state.fieldErrors.filter((e) => e.id !== "req_attachments");
            }
        } catch (err) {
            this.state.serverError = saveError(err, { verb: "tải tệp đính kèm" });
        } finally {
            this.state.uploading = false;
        }
    }

    async removeAttachment(att) {
        try {
            const fd = new FormData();
            fd.append("csrf_token", odoo?.csrf_token || "");
            await fetch(`/tp_request/attachment/${att.id}/delete`, { method: "POST", body: fd });
        } catch {
            // ignore network error on draft cleanup
        }
        this.state.attachments = this.state.attachments.filter((a) => a.id !== att.id);
    }

    focusFirstError(errors) {
        if (!errors?.length) return;
        const firstId = errors[0].id;
        setTimeout(() => {
            const el = document.getElementById(firstId);
            if (el) {
                el.scrollIntoView({ block: "center", behavior: "smooth" });
                el.focus({ preventScroll: true });
            }
        }, 30);
    }

    async save(submit = false) {
        if (this.state.submitting || !this.state.selectedType) return;
        this.state.submitting = true;
        this.state.attempt += 1;
        this.state.fieldErrors = [];
        this.state.serverError = null;
        try {
            const payload = {
                ...this.state.form,
                type_id: this.state.selectedType.id,
                attachment_ids: this.state.attachments.map((a) => a.id),
            };
            const res = await this.orm.call("tp.request", "tp_save_request", [payload, submit]);
            if (!res?.ok) {
                this.state.fieldErrors = res?.field_errors || [];
                this.focusFirstError(this.state.fieldErrors);
                return;
            }
            this.notification.add(
                submit
                    ? `Đã gửi đề nghị ${res.code} thành công.`
                    : `Đã lưu nháp đề nghị ${res.code}.`,
                { type: "success" }
            );
            this.env.bus.trigger("TP_REQUEST:REFRESH_COUNTS");
            if (this.props.onCreated) {
                this.props.onCreated(res);
            }
        } catch (err) {
            this.state.serverError = saveError(err, { verb: submit ? "gửi đề nghị" : "lưu nháp" });
        } finally {
            this.state.submitting = false;
        }
    }

    close() {
        if (this.props.onClose) {
            this.props.onClose();
        }
    }
}
