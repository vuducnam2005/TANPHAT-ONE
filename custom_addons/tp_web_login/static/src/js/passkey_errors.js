import { ConnectionLostError, RPCError, rpc } from "@web/core/network/rpc";

/**
 * Vietnamese feedback for native WebAuthn ceremonies (SimpleWebAuthn errors).
 * NotAllowedError covers cancel, timeout and "no matching key on this device":
 * the browser does not tell them apart, so the message never claims "no key".
 */

export class PasskeyUnsupportedError extends Error {
    constructor() {
        super("WebAuthn is not supported in this browser");
        this.name = "PasskeyUnsupportedError";
    }
}

const CODE_KINDS = {
    ERROR_CEREMONY_ABORTED: "aborted",
    ERROR_INVALID_DOMAIN: "domain",
    ERROR_INVALID_RP_ID: "domain",
    ERROR_AUTHENTICATOR_PREVIOUSLY_REGISTERED: "duplicate",
    ERROR_AUTHENTICATOR_MISSING_DISCOVERABLE_CREDENTIAL_SUPPORT: "capability",
    ERROR_AUTHENTICATOR_MISSING_USER_VERIFICATION_SUPPORT: "capability",
    ERROR_AUTHENTICATOR_NO_SUPPORTED_PUBKEYCREDPARAMS_ALG: "capability",
    ERROR_AUTHENTICATOR_GENERAL_ERROR: "authenticator",
};
const NAME_KINDS = {
    NotAllowedError: "not_allowed",
    AbortError: "aborted",
    SecurityError: "domain",
    InvalidStateError: "duplicate",
    ConstraintError: "capability",
    NotSupportedError: "capability",
    UnknownError: "authenticator",
};

const MESSAGES = {
    login: {
        not_allowed: "Chưa hoàn tất xác thực bằng khóa truy cập. Có thể bạn đã hủy, hết thời gian chờ, hoặc thiết bị/trình quản lý mật khẩu đang dùng không lưu khóa của tài khoản này. Hãy thử lại và chọn đúng khóa, hoặc đăng nhập bằng mật khẩu.",
        aborted: "Thao tác khóa truy cập đã dừng trước khi hoàn tất. Hãy bấm lại “Đăng nhập bằng khóa truy cập”.",
        domain: "Địa chỉ trang hiện tại không khớp với khóa truy cập. Hãy mở hệ thống bằng địa chỉ chính thức (HTTPS) rồi thử lại.",
        capability: "Thiết bị hoặc trình duyệt này chưa đáp ứng yêu cầu khóa truy cập (cần mở khóa bằng vân tay, khuôn mặt hoặc mã PIN). Hãy dùng thiết bị khác hoặc đăng nhập bằng mật khẩu.",
        authenticator: "Thiết bị xác thực báo lỗi khi dùng khóa truy cập. Hãy thử lại hoặc đăng nhập bằng mật khẩu.",
        unsupported: "Trình duyệt này chưa hỗ trợ khóa truy cập. Hãy dùng Chrome, Edge hoặc Safari bản mới, hoặc đăng nhập bằng mật khẩu.",
        network: "Không kết nối được tới máy chủ. Kiểm tra mạng rồi thử lại.",
        server: "Máy chủ chưa tạo được phiên xác thực bằng khóa truy cập. Hãy tải lại trang rồi thử lại.",
        unknown: "Chưa hoàn tất đăng nhập bằng khóa truy cập. Hãy thử lại hoặc đăng nhập bằng mật khẩu.",
    },
    register: {
        not_allowed: "Chưa tạo được khóa truy cập: thao tác đã bị hủy, hết thời gian chờ hoặc thiết bị từ chối. Hãy thử lại.",
        aborted: "Thao tác tạo khóa truy cập đã dừng trước khi hoàn tất. Hãy thử lại.",
        domain: "Địa chỉ trang hiện tại không khớp với hệ thống nên không tạo được khóa truy cập. Hãy mở hệ thống bằng địa chỉ chính thức (HTTPS) rồi thử lại.",
        duplicate: "Thiết bị hoặc trình quản lý mật khẩu này đã lưu khóa truy cập cho tài khoản của bạn. Bạn có thể dùng khóa đó ở trang đăng nhập.",
        capability: "Thiết bị hoặc trình duyệt này chưa đáp ứng yêu cầu khóa truy cập (cần mở khóa bằng vân tay, khuôn mặt hoặc mã PIN). Hãy dùng thiết bị khác.",
        authenticator: "Thiết bị xác thực báo lỗi khi tạo khóa truy cập. Hãy thử lại.",
        unsupported: "Trình duyệt này chưa hỗ trợ khóa truy cập. Hãy dùng Chrome, Edge hoặc Safari bản mới.",
        network: "Không kết nối được tới máy chủ. Kiểm tra mạng rồi thử lại.",
        server: "Máy chủ chưa ghi nhận khóa truy cập. Hãy đóng hộp thoại và thử lại.",
        unknown: "Chưa tạo được khóa truy cập. Hãy thử lại.",
    },
    identity: {
        not_allowed: "Chưa xác nhận được bằng khóa truy cập: thao tác đã bị hủy, hết thời gian chờ, hoặc thiết bị đang dùng không lưu khóa của tài khoản này. Hãy thử lại hoặc chọn “Dùng mật khẩu”.",
        aborted: "Thao tác khóa truy cập đã dừng trước khi hoàn tất. Hãy thử lại.",
        domain: "Địa chỉ trang hiện tại không khớp với khóa truy cập. Hãy mở hệ thống bằng địa chỉ chính thức (HTTPS), hoặc chọn “Dùng mật khẩu”.",
        capability: "Thiết bị hoặc trình duyệt này chưa đáp ứng yêu cầu khóa truy cập. Hãy chọn “Dùng mật khẩu”.",
        authenticator: "Thiết bị xác thực báo lỗi. Hãy thử lại hoặc chọn “Dùng mật khẩu”.",
        unsupported: "Trình duyệt này chưa hỗ trợ khóa truy cập. Hãy chọn “Dùng mật khẩu”.",
        network: "Không kết nối được tới máy chủ. Kiểm tra mạng rồi thử lại.",
        server: "Máy chủ chưa tạo được phiên xác nhận. Hãy đóng hộp thoại và thử lại.",
        unknown: "Chưa xác nhận được bằng khóa truy cập. Hãy thử lại hoặc chọn “Dùng mật khẩu”.",
    },
};

const TOKEN = /^[A-Za-z_]{1,64}$/;

export function passkeyErrorKind(error) {
    if (!error) {
        return "unknown";
    }
    if (error instanceof PasskeyUnsupportedError || /not supported in this browser/i.test(error.message || "")) {
        return "unsupported";
    }
    if (error instanceof ConnectionLostError) {
        return "network";
    }
    if (error instanceof RPCError) {
        return "server";
    }
    return CODE_KINDS[error.code] || NAME_KINDS[error.name] || "unknown";
}

/** @returns {{kind: string, message: string}} */
export function describePasskeyError(error, phase = "login") {
    const kind = passkeyErrorKind(error);
    const messages = MESSAGES[phase] || MESSAGES.login;
    return { kind, message: messages[kind] || messages.unknown };
}

/** Best-effort, enum-only server breadcrumb; never blocks or throws. */
export function reportPasskeyFailure(phase, kind, error) {
    const name = TOKEN.test(error?.name || "") ? error.name : undefined;
    const code = TOKEN.test(error?.code || "") ? error.code : undefined;
    rpc("/tp_web_login/passkey/client-event", { phase, kind, name, code }, { silent: true }).catch(() => {});
}
