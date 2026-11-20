// Part of TANPHAT ONE. License LGPL-3 (see LICENSE of the Odoo distribution).
/**
 * BRAND-WHITELABEL-002: dialog titles without the platform name.
 *
 * Only the fallback titles that read "Odoo ..." change; exception-specific
 * titles (`odooExceptionTitleMap`), messages, tracebacks and the "technical
 * details" button for support are kept as native.
 */

import { t } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { dialogProps } from "@web/core/dialog/dialog";
import {
    ClientErrorDialog,
    ErrorDialog,
    NetworkErrorDialog,
    RedirectWarningDialog,
    RPCErrorDialog,
    WarningDialog,
    odooExceptionTitleMap,
} from "@web/core/errors/error_dialogs";
import { patch } from "@web/core/utils/patch";
import { ActionDialog } from "@web/webclient/actions/action_dialog";
import { BRAND_NAME } from "@tp_branding/brand_urls";

const SERVER_ERROR = _t("Lỗi máy chủ");
const CLIENT_ERROR = _t("Lỗi phía trình duyệt");
const NETWORK_ERROR = _t("Lỗi kết nối mạng");
const SYSTEM_ERROR = _t("Lỗi hệ thống");
const SYSTEM_WARNING = _t("Cảnh báo hệ thống");

// Default title of every Dialog that does not pass one (native: "Odoo").
dialogProps.title = t.string().optional(BRAND_NAME);
ActionDialog.propsSchema.title = t.string().optional(BRAND_NAME);

ErrorDialog.title = SYSTEM_ERROR;
ClientErrorDialog.title = CLIENT_ERROR;
NetworkErrorDialog.title = NETWORK_ERROR;

patch(RPCErrorDialog.prototype, {
    inferTitle() {
        super.inferTitle();
        if (this.props.exceptionName && odooExceptionTitleMap.has(this.props.exceptionName)) {
            return;
        }
        switch (this.props.type) {
            case "server":
                this.title = SERVER_ERROR;
                break;
            case "script":
                this.title = CLIENT_ERROR;
                break;
            case "network":
                this.title = NETWORK_ERROR;
                break;
        }
    },
});

patch(WarningDialog.prototype, {
    inferTitle() {
        if (this.props.exceptionName && odooExceptionTitleMap.has(this.props.exceptionName)) {
            return super.inferTitle();
        }
        return this.props.title || SYSTEM_WARNING;
    },
});

patch(RedirectWarningDialog.prototype, {
    setup() {
        super.setup();
        if (!this.props.subType) {
            this.title = SYSTEM_WARNING;
        }
    },
});
