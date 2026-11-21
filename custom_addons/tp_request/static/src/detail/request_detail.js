/** @odoo-module **/
import { Component, onWillStart, proxy, useProps } from "@odoo/owl";
import { browser } from "@web/core/browser/browser";
import { router } from "@web/core/browser/router";
import { registry } from "@web/core/registry";
import { useBus, useService } from "@web/core/utils/hooks";
import { InlineErrors } from "@tp_web_home/validation/inline_errors";
import { saveError } from "@tp_web_home/validation/validation";
import {
    APPROVAL_BADGE,
    EXEC_BADGE,
    MODE_TO_ACTION,
    PRIORITY_BADGE,
    extractErrorMessage,
    formatFileSize,
    openRequestDetail,
    readLastListMode,
} from "../prefs";

function resolveRequestId(props) {
    const candidates = [
        props?.resId,
        props?.action?.context?.tp_request_id,
        props?.action?.params?.request_id,
        props?.action?.params?.resId,
        router.current?.resId,
    ];
    for (const c of candidates) {
        const n = Number(c);
        if (Number.isInteger(n) && n > 0) {
            return n;
        }
    }
    const match = (browser.location?.pathname || "").match(/\/app\/de-nghi\/(?:ho-so|[^/]+)\/(\d+)/);
    if (match) {
        return Number(match[1]);
    }
    return 0;
}

export class TpRequestDetail extends Component {
    static template = "tp_request.Detail";
    static components = { InlineErrors };
    props = useProps();

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.notification = useService("notification");
        this.APPROVAL_BADGE = APPROVAL_BADGE;
        this.EXEC_BADGE = EXEC_BADGE;
        this.PRIORITY_BADGE = PRIORITY_BADGE;
        this.formatFileSize = formatFileSize;

        const requestId = resolveRequestId(this.props);

        this.state = proxy({
            requestId,
            loading: true,
            error: "",
            data: null,
            busy: false,
            bannerMessage: "",
            // Inline edit mode (owner on draft / returned)
            editing: false,
            bootstrap: null,
            editForm: null,
            editAttempt: 0,
            editFieldErrors: [],
            editServerError: null,
            // Approval panel
            decisionNote: "",
            decisionError: "",
            // Withdraw panel
            showWithdraw: false,
            withdrawReason: "",
            // Transfer approver panel (manager)
            showTransfer: false,
            transferUserIds: [],
            transferReason: "",
            transferError: "",
            // Execution panel
            execProgressNote: "",
            execResultNote: "",
            execCancelReason: "",
            showExecCancel: false,
            execFulfilledEquipId: "",
            execOldCondition: "",
            execError: "",
            // Upload & comments
            uploading: false,
            commentBody: "",
            commentBusy: false,
            commentError: "",
            activeBottomTab: "comments", // 'comments' | 'history'
        });

        useBus(this.env.bus, "TP_REQUEST:LIVE_UPDATED", (ev) => {
            const rid = ev?.detail?.request_id;
            if (!rid || Number(rid) === this.state.requestId) {
                this.load(true);
            }
        });

        onWillStart(() => this.load());
    }

    syncCanonicalUrl() {
        if (this.state.requestId && Number(router.current?.resId) !== this.state.requestId) {
            try {
                router.replaceState({ resId: this.state.requestId });
            } catch {
                // ignore router sync failure
            }
        }
    }

    async load(silent = false) {
        if (!this.state.requestId) {
            this.state.loading = false;
            this.state.error = "Không xác định được mã hồ sơ đề nghị từ đường dẫn.";
            return;
        }
        if (!silent) {
            this.state.loading = true;
            this.state.error = "";
        }
        try {
            const data = await (silent ? this.orm.silent : this.orm).call("tp.request", "tp_detail_data", [
                this.state.requestId,
            ]);
            this.state.data = data;
            this.state.error = "";
            this.syncCanonicalUrl();
            // Pre-select first eligible stock machine if only 1 matches or none selected
            if (!this.state.execFulfilledEquipId && data.equipment?.eligible_stock?.length === 1) {
                this.state.execFulfilledEquipId = String(data.equipment.eligible_stock[0].id);
            }
        } catch (err) {
            if (!silent) {
                this.state.error = extractErrorMessage(
                    err,
                    "Không tìm thấy hồ sơ đề nghị hoặc bạn không có quyền xem."
                );
            }
        } finally {
            this.state.loading = false;
        }
    }

    goBack() {
        const fromMode = this.props.action?.context?.tp_from_mode || readLastListMode();
        if (browser.history.length > 1 && document.referrer?.includes(browser.location.origin)) {
            browser.history.back();
            return;
        }
        const targetAction = MODE_TO_ACTION[fromMode] || "tp_request.action_mine";
        this.action.doAction(targetAction);
    }

    openRelatedRequest(reqId) {
        if (reqId) {
            openRequestDetail(this.action, reqId);
        }
    }

    openInternalUrl(url) {
        if (!url) return;
        browser.location.assign(url);
    }

    // --------------------------------------------------------- Inline Edit (Draft / Returned)
    async startEdit() {
        const d = this.state.data;
        if (!d || !d.permissions?.can_edit) return;
        this.state.editFieldErrors = [];
        this.state.editServerError = null;
        if (!this.state.bootstrap) {
            try {
                this.state.bootstrap = await this.orm.call("tp.request", "tp_create_bootstrap", []);
            } catch (err) {
                this.state.editServerError = saveError(err, { verb: "tải dữ liệu biểu mẫu", write: false });
                return;
            }
        }
        this.state.editForm = {
            id: d.id,
            type_id: d.type_id,
            title: d.title || "",
            description: d.description || "",
            priority: d.priority || "normal",
            needed_date: d.needed_date || "",
            project_id: d.project_id ? String(d.project_id) : "",
            follower_user_ids: (d.followers || []).map((f) => f.id),
            equipment_id: d.equipment?.equipment_id ? String(d.equipment.equipment_id) : "",
            equipment_category_id: d.equipment?.category_id ? String(d.equipment.category_id) : "",
            equipment_quantity: d.equipment?.quantity || 1,
            equipment_desired_spec: d.equipment?.desired_spec || "",
            equipment_issue_detail: d.equipment?.issue_detail || "",
            it_category: d.it_support?.category || "",
            it_device_id: d.it_support?.device_id ? String(d.it_support.device_id) : "",
            it_urgency_impact: d.it_support?.impact || "self",
            att_work_date: d.attendance?.work_date || "",
            att_requested_in: d.attendance?.requested_in || "08:30",
            att_requested_out: d.attendance?.requested_out || "17:00",
        };
        this.state.editing = true;
    }

    cancelEdit() {
        this.state.editing = false;
        this.state.editFieldErrors = [];
        this.state.editServerError = null;
    }

    onEditField(field, ev) {
        if (!this.state.editForm) return;
        this.state.editForm[field] = ev.target.value;
    }

    onEditFollowerToggle(uid, ev) {
        if (!this.state.editForm) return;
        const set = new Set(this.state.editForm.follower_user_ids || []);
        if (ev.target.checked) set.add(uid);
        else set.delete(uid);
        this.state.editForm.follower_user_ids = [...set];
    }

    async saveEdit(submitAfter = false) {
        if (!this.state.editForm || this.state.busy) return;
        this.state.busy = true;
        this.state.editAttempt += 1;
        this.state.editFieldErrors = [];
        this.state.editServerError = null;
        try {
            const res = await this.orm.call("tp.request", "tp_save_request", [
                {
                    ...this.state.editForm,
                    project_id: this.state.editForm.project_id ? Number(this.state.editForm.project_id) : false,
                    equipment_id: this.state.editForm.equipment_id ? Number(this.state.editForm.equipment_id) : false,
                    equipment_category_id: this.state.editForm.equipment_category_id
                        ? Number(this.state.editForm.equipment_category_id)
                        : false,
                    equipment_quantity: Number(this.state.editForm.equipment_quantity) || 1,
                    it_device_id: this.state.editForm.it_device_id ? Number(this.state.editForm.it_device_id) : false,
                },
                submitAfter,
            ]);
            if (res && res.ok === false && res.field_errors) {
                this.state.editFieldErrors = res.field_errors;
                return;
            }
            this.state.editing = false;
            this.state.bannerMessage = submitAfter
                ? "Đã lưu cập nhật và gửi đề nghị phê duyệt thành công."
                : "Đã lưu thay đổi bản nháp.";
            this.notification.add(this.state.bannerMessage, { type: "success" });
            await this.load();
            this.env.bus.trigger("TP_REQUEST:LIVE_UPDATED", { request_id: this.state.requestId });
        } catch (err) {
            this.state.editServerError = saveError(err, { verb: submitAfter ? "gửi đề nghị" : "lưu thay đổi" });
        } finally {
            this.state.busy = false;
        }
    }

    async submitDirectly() {
        const d = this.state.data;
        if (!d || this.state.busy) return;
        this.state.busy = true;
        this.state.decisionError = "";
        try {
            await this.orm.call("tp.request", "action_submit", [[d.id]], {
                expected_version: d.version,
            });
            this.state.bannerMessage = "Đã gửi hồ sơ đề nghị thành công và thông báo đến người duyệt bước đầu tiên.";
            this.notification.add("Đã gửi đề nghị phê duyệt.", { type: "success" });
            await this.load();
            this.env.bus.trigger("TP_REQUEST:LIVE_UPDATED", { request_id: this.state.requestId });
        } catch (err) {
            this.state.decisionError = extractErrorMessage(err, "Chưa thể gửi đề nghị.");
        } finally {
            this.state.busy = false;
        }
    }

    async confirmWithdraw() {
        const d = this.state.data;
        if (!d || this.state.busy) return;
        this.state.busy = true;
        this.state.decisionError = "";
        try {
            await this.orm.call("tp.request", "action_withdraw", [[d.id]], {
                reason: this.state.withdrawReason,
                expected_version: d.version,
            });
            this.state.showWithdraw = false;
            this.state.withdrawReason = "";
            this.state.bannerMessage = "Hồ sơ đã được rút / hủy.";
            this.notification.add("Đã rút đề nghị.", { type: "info" });
            await this.load();
            this.env.bus.trigger("TP_REQUEST:LIVE_UPDATED", { request_id: this.state.requestId });
        } catch (err) {
            this.state.decisionError = extractErrorMessage(err, "Không thể rút hồ sơ.");
        } finally {
            this.state.busy = false;
        }
    }

    async cloneFromRejected() {
        const d = this.state.data;
        if (!d || this.state.busy) return;
        this.state.busy = true;
        try {
            const newId = await this.orm.call("tp.request", "action_clone_from_rejected", [[d.id]]);
            this.notification.add("Đã tạo bản nháp mới từ hồ sơ cũ.", { type: "success" });
            if (newId) {
                openRequestDetail(this.action, newId);
            }
        } catch (err) {
            this.state.decisionError = extractErrorMessage(err, "Không thể tạo bản đề nghị mới.");
        } finally {
            this.state.busy = false;
        }
    }

    // --------------------------------------------------------- Approval Actions
    async doApprove() {
        const d = this.state.data;
        if (!d || this.state.busy) return;
        this.state.busy = true;
        this.state.decisionError = "";
        try {
            const res = await this.orm.call("tp.request", "action_approve_step", [[d.id]], {
                note: this.state.decisionNote,
                expected_version: d.version,
            });
            this.state.decisionNote = "";
            this.state.bannerMessage = res?.next_label || "Đã phê duyệt bước hiện tại thành công.";
            this.notification.add(this.state.bannerMessage, { type: "success" });
            await this.load();
            this.env.bus.trigger("TP_REQUEST:LIVE_UPDATED", { request_id: this.state.requestId });
        } catch (err) {
            this.state.decisionError = extractErrorMessage(err, "Không thể phê duyệt hồ sơ.");
        } finally {
            this.state.busy = false;
        }
    }

    async doReturn() {
        const d = this.state.data;
        if (!d || this.state.busy) return;
        if (!this.state.decisionNote.trim()) {
            this.state.decisionError = "Bắt buộc nhập lý do trả lại bổ sung trước khi xác nhận.";
            return;
        }
        this.state.busy = true;
        this.state.decisionError = "";
        try {
            await this.orm.call("tp.request", "action_return", [[d.id]], {
                reason: this.state.decisionNote,
                expected_version: d.version,
            });
            this.state.decisionNote = "";
            this.state.bannerMessage = "Đã trả lại hồ sơ để người gửi bổ sung thông tin.";
            this.notification.add(this.state.bannerMessage, { type: "warning" });
            await this.load();
            this.env.bus.trigger("TP_REQUEST:LIVE_UPDATED", { request_id: this.state.requestId });
        } catch (err) {
            this.state.decisionError = extractErrorMessage(err, "Không thể trả lại hồ sơ.");
        } finally {
            this.state.busy = false;
        }
    }

    async doReject() {
        const d = this.state.data;
        if (!d || this.state.busy) return;
        if (!this.state.decisionNote.trim()) {
            this.state.decisionError = "Bắt buộc nhập lý do từ chối đề nghị trước khi xác nhận.";
            return;
        }
        this.state.busy = true;
        this.state.decisionError = "";
        try {
            await this.orm.call("tp.request", "action_reject", [[d.id]], {
                reason: this.state.decisionNote,
                expected_version: d.version,
            });
            this.state.decisionNote = "";
            this.state.bannerMessage = "Đã từ chối hồ sơ đề nghị.";
            this.notification.add(this.state.bannerMessage, { type: "warning" });
            await this.load();
            this.env.bus.trigger("TP_REQUEST:LIVE_UPDATED", { request_id: this.state.requestId });
        } catch (err) {
            this.state.decisionError = extractErrorMessage(err, "Không thể từ chối hồ sơ.");
        } finally {
            this.state.busy = false;
        }
    }

    // --------------------------------------------------------- Manager Transfer Approver
    toggleTransferUser(uid, ev) {
        const set = new Set(this.state.transferUserIds);
        if (ev.target.checked) set.add(uid);
        else set.delete(uid);
        this.state.transferUserIds = [...set];
    }

    async submitTransfer() {
        const d = this.state.data;
        if (!d || this.state.busy) return;
        if (!this.state.transferUserIds.length) {
            this.state.transferError = "Vui lòng chọn ít nhất một người duyệt thay thế.";
            return;
        }
        if (!this.state.transferReason.trim()) {
            this.state.transferError = "Bắt buộc nhập lý do chuyển giao người duyệt.";
            return;
        }
        this.state.busy = true;
        this.state.transferError = "";
        try {
            await this.orm.call("tp.request", "action_transfer_approver", [[d.id]], {
                new_user_ids: this.state.transferUserIds,
                reason: this.state.transferReason,
                expected_version: d.version,
            });
            this.state.showTransfer = false;
            this.state.transferUserIds = [];
            this.state.transferReason = "";
            this.state.bannerMessage = "Đã chuyển giao bước duyệt hiện tại và ghi nhận lịch sử.";
            this.notification.add(this.state.bannerMessage, { type: "success" });
            await this.load();
            this.env.bus.trigger("TP_REQUEST:LIVE_UPDATED", { request_id: this.state.requestId });
        } catch (err) {
            this.state.transferError = extractErrorMessage(err, "Không thể chuyển giao người duyệt.");
        } finally {
            this.state.busy = false;
        }
    }

    // --------------------------------------------------------- Execution Actions
    async startExecution() {
        const d = this.state.data;
        if (!d || this.state.busy) return;
        this.state.busy = true;
        this.state.execError = "";
        try {
            await this.orm.call("tp.request", "action_start_execution", [[d.id]], {
                note: this.state.execProgressNote,
                expected_version: d.version,
            });
            this.state.execProgressNote = "";
            this.state.bannerMessage = "Đã tiếp nhận và bắt đầu thực hiện hồ sơ.";
            this.notification.add(this.state.bannerMessage, { type: "success" });
            await this.load();
            this.env.bus.trigger("TP_REQUEST:LIVE_UPDATED", { request_id: this.state.requestId });
        } catch (err) {
            this.state.execError = extractErrorMessage(err, "Không thể nhận việc.");
        } finally {
            this.state.busy = false;
        }
    }

    async updateProgress() {
        const d = this.state.data;
        if (!d || this.state.busy) return;
        if (!this.state.execProgressNote.trim()) {
            this.state.execError = "Nhập ghi chú cập nhật tiến độ trước khi lưu.";
            return;
        }
        this.state.busy = true;
        this.state.execError = "";
        try {
            await this.orm.call("tp.request", "action_update_execution_progress", [[d.id]], {
                note: this.state.execProgressNote,
                expected_version: d.version,
            });
            this.state.execProgressNote = "";
            this.notification.add("Đã cập nhật tiến độ thực hiện.", { type: "success" });
            await this.load();
        } catch (err) {
            this.state.execError = extractErrorMessage(err, "Không thể cập nhật tiến độ.");
        } finally {
            this.state.busy = false;
        }
    }

    async createRepairRecord() {
        const d = this.state.data;
        if (!d || this.state.busy) return;
        this.state.busy = true;
        this.state.execError = "";
        try {
            const res = await this.orm.call("tp.request", "action_create_equipment_repair", [[d.id]], {
                expected_version: d.version,
            });
            this.state.bannerMessage = `Đã tạo phiếu sửa chữa thực tế ${res?.repair_code || ""} trong Kho thiết bị.`;
            this.notification.add(this.state.bannerMessage, { type: "success" });
            await this.load();
        } catch (err) {
            this.state.execError = extractErrorMessage(err, "Không thể tạo phiếu sửa chữa.");
        } finally {
            this.state.busy = false;
        }
    }

    async createPurchaseProposal() {
        const d = this.state.data;
        if (!d || this.state.busy) return;
        this.state.busy = true;
        this.state.execError = "";
        try {
            const res = await this.orm.call("tp.request", "action_create_equipment_proposal", [[d.id]], {
                expected_version: d.version,
            });
            this.state.bannerMessage = `Đã lập đề xuất mua sắm ${res?.proposal_code || ""} trong Kho thiết bị.`;
            this.notification.add(this.state.bannerMessage, { type: "success" });
            await this.load();
        } catch (err) {
            this.state.execError = extractErrorMessage(err, "Không thể lập đề xuất mua sắm.");
        } finally {
            this.state.busy = false;
        }
    }

    async completeExecution() {
        const d = this.state.data;
        if (!d || this.state.busy) return;
        if (!this.state.execResultNote.trim()) {
            this.state.execError = "Bắt buộc nhập kết quả thực hiện trước khi xác nhận hoàn thành.";
            return;
        }
        const extra = {};
        if (d.handler_kind === "equipment_assign") {
            if (!this.state.execFulfilledEquipId) {
                this.state.execError = "Vui lòng chọn thiết bị đủ điều kiện trong kho để cấp phát.";
                return;
            }
            extra.fulfilled_equipment_id = Number(this.state.execFulfilledEquipId);
        } else if (d.handler_kind === "equipment_swap") {
            if (!this.state.execFulfilledEquipId) {
                this.state.execError = "Vui lòng chọn thiết bị mới đủ điều kiện trong kho để đổi.";
                return;
            }
            if (!this.state.execOldCondition) {
                this.state.execError = "Bắt buộc xác nhận tình trạng thực tế của thiết bị cũ khi thu hồi.";
                return;
            }
            extra.fulfilled_equipment_id = Number(this.state.execFulfilledEquipId);
            extra.old_equipment_condition = this.state.execOldCondition;
        }

        this.state.busy = true;
        this.state.execError = "";
        try {
            const res = await this.orm.call("tp.request", "action_complete_execution", [[d.id]], {
                result_note: this.state.execResultNote,
                expected_version: d.version,
                extra_payload: extra,
            });
            this.state.execResultNote = "";
            this.state.bannerMessage = res?.result_ref
                ? `Đã hoàn thành thực hiện và ghi nhận kết quả (${res.result_ref}).`
                : "Đã hoàn thành thực hiện đề nghị.";
            this.notification.add(this.state.bannerMessage, { type: "success" });
            await this.load();
            this.env.bus.trigger("TP_REQUEST:LIVE_UPDATED", { request_id: this.state.requestId });
        } catch (err) {
            this.state.execError = extractErrorMessage(err, "Không thể hoàn thành thực hiện.");
        } finally {
            this.state.busy = false;
        }
    }

    async cancelExecution() {
        const d = this.state.data;
        if (!d || this.state.busy) return;
        if (!this.state.execCancelReason.trim()) {
            this.state.execError = "Bắt buộc nhập lý do không thể thực hiện.";
            return;
        }
        this.state.busy = true;
        this.state.execError = "";
        try {
            await this.orm.call("tp.request", "action_cancel_execution", [[d.id]], {
                reason: this.state.execCancelReason,
                expected_version: d.version,
            });
            this.state.showExecCancel = false;
            this.state.execCancelReason = "";
            this.state.bannerMessage = "Đã ghi nhận hủy thực hiện đề nghị.";
            this.notification.add(this.state.bannerMessage, { type: "warning" });
            await this.load();
            this.env.bus.trigger("TP_REQUEST:LIVE_UPDATED", { request_id: this.state.requestId });
        } catch (err) {
            this.state.execError = extractErrorMessage(err, "Không thể hủy thực hiện.");
        } finally {
            this.state.busy = false;
        }
    }

    // --------------------------------------------------------- Attachments & Comments
    async onUploadAttachment(ev) {
        const files = [...(ev.target.files || [])];
        ev.target.value = "";
        if (!files.length || !this.state.requestId) return;
        this.state.uploading = true;
        try {
            for (const file of files) {
                const fd = new FormData();
                fd.append("file", file);
                fd.append("request_id", String(this.state.requestId));
                fd.append("csrf_token", odoo.csrf_token);
                const resp = await fetch("/tp_request/attachment/upload", {
                    method: "POST",
                    body: fd,
                    credentials: "same-origin",
                });
                const payload = await resp.json();
                if (!resp.ok || !payload.ok) {
                    throw new Error(payload.error || "Tải tệp thất bại.");
                }
            }
            this.notification.add("Đã tải tệp đính kèm thành công.", { type: "success" });
            await this.load(true);
        } catch (err) {
            this.notification.add(extractErrorMessage(err, "Không tải được tệp đính kèm."), { type: "danger" });
        } finally {
            this.state.uploading = false;
        }
    }

    async deleteAttachment(att) {
        if (!att?.id || this.state.busy) return;
        this.state.busy = true;
        try {
            const fd = new FormData();
            fd.append("csrf_token", odoo.csrf_token);
            const resp = await fetch(`/tp_request/attachment/${att.id}/delete`, {
                method: "POST",
                body: fd,
                credentials: "same-origin",
            });
            const payload = await resp.json();
            if (!resp.ok || !payload.ok) {
                throw new Error(payload.error || "Không xóa được tệp đính kèm.");
            }
            this.notification.add("Đã xóa tệp đính kèm.", { type: "info" });
            await this.load(true);
        } catch (err) {
            this.notification.add(extractErrorMessage(err, "Không thể xóa tệp."), { type: "danger" });
        } finally {
            this.state.busy = false;
        }
    }

    async postComment() {
        const body = this.state.commentBody.trim();
        if (!body || this.state.commentBusy) return;
        this.state.commentBusy = true;
        this.state.commentError = "";
        try {
            await this.orm.call("tp.request", "tp_post_comment", [this.state.requestId, body]);
            this.state.commentBody = "";
            await this.load(true);
        } catch (err) {
            this.state.commentError = extractErrorMessage(err, "Không gửi được trao đổi.");
        } finally {
            this.state.commentBusy = false;
        }
    }

    get latestSteps() {
        const steps = this.state.data?.steps || [];
        if (!steps.length) return [];
        const maxVer = Math.max(...steps.map((s) => s.request_version || 1));
        return steps.filter((s) => (s.request_version || 1) === maxVer);
    }

    get archivedSteps() {
        const steps = this.state.data?.steps || [];
        if (!steps.length) return [];
        const maxVer = Math.max(...steps.map((s) => s.request_version || 1));
        return steps.filter((s) => (s.request_version || 1) < maxVer);
    }
}

registry.category("actions").add("tp_request.detail", TpRequestDetail);
