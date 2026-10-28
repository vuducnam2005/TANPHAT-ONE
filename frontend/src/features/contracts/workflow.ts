import { ApiError } from '../../shared/api/client';
import type { AmountInput, ContractLine, ContractSubmission, LineInput } from '../../shared/api/types';

export const outcomeLabels: Record<ContractSubmission['outcome'], string> = {
  pending: 'Đang chờ rà soát',
  returned: 'Đã trả lại để sửa',
};

const problemLabels: Record<string, string> = {
  no_lines: 'bản nháp chưa có dòng phạm vi',
  amounts_not_confirmed: 'còn dòng chưa xác nhận giá trị',
  tax_basis_mixed: 'các dòng khác cơ sở thuế',
};

// Server codes the UI explains in Vietnamese; anything else falls back to the server message.
const errorLabels: Record<string, string> = {
  stale_version: 'Hồ sơ vừa được cập nhật ở nơi khác. Tải lại bản mới nhất rồi thực hiện lại; thay đổi chưa được lưu.',
  invalid_state: 'Trạng thái bản hợp đồng đã thay đổi. Tải lại để xem trạng thái hiện tại.',
  duplicate_code: 'Số hợp đồng này đã được dùng trong công ty.',
  idempotency_conflict: 'Thao tác trùng với một yêu cầu khác. Vui lòng thử lại.',
  forbidden: 'Bạn chưa được cấp quyền cho thao tác này trong phạm vi hợp đồng.',
  not_assigned_reviewer: 'Chỉ người rà soát được giao cho lần gửi này mới trả lại được.',
  csrf_invalid: 'Phiên làm việc cần làm mới. Vui lòng thực hiện lại.',
  cross_origin: 'Yêu cầu không đến từ trang TANPHAT ONE nên không được chấp nhận.',
  not_found: 'Không tìm thấy hồ sơ, hoặc hồ sơ nằm ngoài phạm vi được phân công.',
  scope_incomplete: 'Dự án chưa có phòng ban chủ trì nên chưa tạo được hợp đồng.',
  header_locked: 'Thông tin chung của hợp đồng chỉ sửa được ở bản gốc.',
  reviewer_ineligible: 'Người rà soát đã chọn không còn đủ quyền rà soát hợp đồng này.',
  fix_summary_required: 'Cần mô tả nội dung đã sửa so với lần bị trả lại.',
  reason_required: 'Cần nhập lý do.',
  issue_note_required: 'Mỗi ý kiến cần có nội dung.',
  unknown_scope_key: 'Ý kiến tham chiếu dòng phạm vi không có trong lần gửi.',
  code_required: 'Cần nhập số hợp đồng.',
  name_required: 'Cần nhập tên.',
  unknown_currency: 'Đơn vị tiền tệ không có hoặc chưa được kích hoạt.',
  unknown_partner: 'Đối tác không có hoặc thuộc công ty khác.',
  amount_value_required: 'Giá trị đã xác nhận cần có số tiền.',
  amount_value_not_allowed: 'Giá trị chưa xác nhận thì để trống số tiền.',
  amount_negative: 'Giá trị dòng phạm vi không được âm.',
  amount_too_large: 'Số tiền có quá nhiều chữ số.',
  amount_precision: 'Số tiền có nhiều chữ số thập phân hơn đơn vị tiền tệ cho phép.',
  unsupported_media_type: 'Dữ liệu gửi lên không đúng định dạng.',
  invalid_request: 'Dữ liệu gửi lên chưa hợp lệ.',
  unauthenticated: 'Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.',
};

export function workflowErrorMessage(error: unknown) {
  if (!(error instanceof ApiError)) return 'Chưa kết nối được hệ thống. Thay đổi chưa được lưu; vui lòng thử lại.';
  const label = errorLabels[error.code] ?? error.message;
  const details = error.details as { problems?: string[]; field?: string } | null | undefined;
  if (error.code === 'submission_incomplete' && details?.problems?.length) {
    return `Chưa gửi rà soát được: ${details.problems.map((problem) => problemLabels[problem] ?? problem).join('; ')}.`;
  }
  return details?.field && error.status === 400 ? `${label} (${details.field})` : label;
}

/** Errors after which the user must reload before trying again. */
export function needsReload(error: unknown) {
  return error instanceof ApiError && ['stale_version', 'invalid_state'].includes(error.code);
}

export function newIdempotencyKey() {
  return globalThis.crypto?.randomUUID?.() ?? `tp-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

/** Amount entry is kept as text; it is sent as a decimal string and never parsed into a JavaScript number. */
export interface AmountDraft {
  state: AmountInput['state'];
  value: string;
  taxBasis: AmountInput['tax_basis'];
}

export interface LineDraft {
  scopeKey: string;
  name: string;
  /** Null when amounts are not editable for this user. */
  amount: AmountDraft | null;
  /** Amount as loaded; an unchanged amount is not sent, so the server keeps it as is. */
  original: AmountDraft | null;
  isNew: boolean;
}

const DECIMAL_INPUT = /^\d{1,20}([.,]\d{1,10})?$/;

export function normalizeDecimal(value: string) {
  const trimmed = value.trim().replace(/\s/g, '');
  return DECIMAL_INPUT.test(trimmed) ? trimmed.replace(',', '.') : null;
}

export const emptyAmount = (): AmountDraft => ({ state: 'unconfirmed', value: '', taxBasis: 'unknown' });

export function newLineDraft(withAmounts: boolean): LineDraft {
  return { scopeKey: '', name: '', amount: withAmounts ? emptyAmount() : null, original: null, isNew: true };
}

export function lineDrafts(lines: ContractLine[], withAmounts: boolean): LineDraft[] {
  return lines.map((line) => {
    const amount: AmountDraft | null = withAmounts && line.amount
      ? { state: line.amount.status === 'confirmed' ? 'confirmed' : 'unconfirmed', value: line.amount.value ?? '', taxBasis: amountTaxBasis(line.amount.tax_basis) }
      : null;
    return { scopeKey: line.scope_key, name: line.name, amount, original: amount, isNew: false };
  });
}

function amountTaxBasis(value: string): AmountInput['tax_basis'] {
  return value === 'excluding_tax' || value === 'including_tax' ? value : 'unknown';
}

function sameAmount(left: AmountDraft | null, right: AmountDraft | null) {
  if (!left || !right) return left === right;
  return left.state === right.state && left.taxBasis === right.taxBasis
    && (left.state === 'unconfirmed' || normalizeDecimal(left.value) === normalizeDecimal(right.value));
}

/**
 * Build the full line set for an edit. Amounts are sent only when edited, and
 * never without the financial edit grant, so the server keeps the rest as is.
 */
export function lineInputs(drafts: LineDraft[], withAmounts: boolean): { lines: LineInput[] } | { error: string } {
  const lines: LineInput[] = [];
  const seen = new Set<string>();
  for (const [index, draft] of drafts.entries()) {
    const scopeKey = draft.scopeKey.trim();
    const name = draft.name.trim();
    if (!scopeKey || !name) return { error: `Dòng ${index + 1}: cần nhập mã phạm vi và nội dung.` };
    if (seen.has(scopeKey)) return { error: `Mã phạm vi ${scopeKey} bị trùng.` };
    seen.add(scopeKey);
    const line: LineInput = { scope_key: scopeKey, name };
    if (withAmounts && draft.amount && !sameAmount(draft.amount, draft.original)) {
      if (draft.amount.state === 'unconfirmed') {
        line.amount = { state: 'unconfirmed', value: null, tax_basis: draft.amount.taxBasis };
      } else {
        const value = normalizeDecimal(draft.amount.value);
        if (value === null) return { error: `Dòng ${index + 1}: giá trị phải là số không âm, dùng dấu phẩy hoặc chấm cho phần thập phân.` };
        line.amount = { state: 'confirmed', value, tax_basis: draft.amount.taxBasis };
      }
    }
    lines.push(line);
  }
  return { lines };
}
