import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";
import { saveError } from "@tp_web_home/validation/validation";
import { TpHrMyProfile } from "@tp_hr_workspace/my_profile/my_profile";
import { bankHolderName, formatAccountNumber, TpBankBadge, TpBankPicker } from "./bank_picker";

const NUMBER_RE = /^[0-9]{6,20}$/;
const HOLDER_RE = /^[A-Z][A-Z .'-]{1,119}$/;

function cleanNumber(value) {
    return String(value || "").replace(/[\s.-]/g, "");
}

function maskNumber(value) {
    const number = cleanNumber(value);
    return number.length > 4 ? `••••${number.slice(-4)}` : number;
}

patch(TpHrMyProfile, {
    components: { ...TpHrMyProfile.components, TpBankBadge, TpBankPicker },
});

/** BANK-001: own bank accounts in "Thông tin cá nhân" (server: res.users.tp_save_my_bank_account). */
patch(TpHrMyProfile.prototype, {
    setup() {
        super.setup(...arguments);
        Object.assign(this.state, {
            bankDraft: null,
            bankAttempted: false,
            bankAttempt: 0,
            bankSaveError: null,
        });
    },

    get bankInfo() {
        return this.state.data?.bank || null;
    },

    get canAddBankAccount() {
        const info = this.bankInfo;
        return Boolean(info?.available && info.accounts.length < info.max_accounts);
    },

    formatAccountNumber(number) {
        return formatAccountNumber(number);
    },

    openBankModal(account = null) {
        this.state.actionError = null;
        Object.assign(this.state, {
            bankAttempted: false,
            bankSaveError: null,
            bankDraft: {
                id: account?.id || null,
                bank_id: account?.bank?.id || false,
                account_number: account?.account_number || "",
                holder_name: account?.holder_name || this.bankInfo?.default_holder || "",
            },
        });
    },

    closeBankModal() {
        this.state.bankDraft = null;
    },

    onBankSelect(bank) {
        this.state.bankDraft.bank_id = bank.id;
    },

    onBankDraftInput(key, ev) {
        this.state.bankDraft[key] = ev.target.value;
    },

    onBankHolderChange(ev) {
        this.state.bankDraft.holder_name = bankHolderName(ev.target.value);
    },

    get bankErrors() {
        const draft = this.state.bankDraft;
        if (!this.state.bankAttempted || !draft) {
            return [];
        }
        const errors = [];
        const add = (id, label, message) => errors.push({ id, label, message, location: "Tài khoản ngân hàng" });
        // Mirrors tp_save_my_bank_account; the server stays authoritative.
        if (!draft.bank_id) {
            add("tp_bank_bank_id", "Ngân hàng", "Vui lòng chọn ngân hàng trong danh sách.");
        }
        const number = cleanNumber(draft.account_number);
        if (!number) {
            add("tp_bank_account_number", "Số tài khoản", "Vui lòng nhập số tài khoản.");
        } else if (!NUMBER_RE.test(number)) {
            add("tp_bank_account_number", "Số tài khoản", "Số tài khoản chỉ gồm chữ số, từ 6 đến 20 số.");
        }
        if (!HOLDER_RE.test(bankHolderName(draft.holder_name))) {
            add(
                "tp_bank_holder_name",
                "Tên chủ tài khoản",
                "Tên chủ tài khoản chỉ gồm chữ cái không dấu và khoảng trắng, tối đa 120 ký tự."
            );
        }
        return errors;
    },

    bankFieldError(id) {
        return this.bankErrors.find((error) => error.id === id)?.message || "";
    },

    async saveBankDraft() {
        const draft = this.state.bankDraft;
        if (!draft || this.state.saving) {
            return;
        }
        this.state.bankAttempted = true;
        this.state.bankSaveError = null;
        if (this.bankErrors.length) {
            this.state.bankAttempt++;
            return;
        }
        this.state.saving = true;
        try {
            const payload = await this.orm.call("res.users", "tp_save_my_bank_account", [
                draft.id || false,
                {
                    bank_id: Number(draft.bank_id),
                    account_number: cleanNumber(draft.account_number),
                    holder_name: bankHolderName(draft.holder_name),
                },
            ]);
            this.applyProfilePayload(payload);
            this.state.bankDraft = null;
            this.notification.add(
                draft.id ? _t("Đã cập nhật tài khoản ngân hàng.") : _t("Đã thêm tài khoản ngân hàng."),
                { type: "success" }
            );
        } catch (err) {
            this.state.bankSaveError = saveError(err);
            this.state.bankAttempt++;
        } finally {
            this.state.saving = false;
        }
    },

    async removeBankAccount(account) {
        const ok = await this.confirmDiscard(
            _t("Gỡ tài khoản ngân hàng?"),
            _t("Tài khoản %(bank)s %(number)s sẽ được gỡ khỏi hồ sơ của bạn.", {
                bank: account.bank_label,
                number: maskNumber(account.account_number),
            }),
            _t("Gỡ tài khoản")
        );
        if (!ok) {
            return;
        }
        this.state.actionError = null;
        try {
            const payload = await this.orm.call("res.users", "tp_remove_my_bank_account", [account.id]);
            this.applyProfilePayload(payload);
            this.notification.add(_t("Đã gỡ tài khoản ngân hàng."), { type: "success" });
        } catch (err) {
            this.showActionError("bank", err, { verb: "gỡ", note: "Danh sách chưa thay đổi." });
        }
    },
});
