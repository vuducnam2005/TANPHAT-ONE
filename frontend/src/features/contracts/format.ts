import type { ApprovalReference, ContractDetail, ContractDocument, ContractLine, EffectiveWarning, Money, RevisionStatus } from '../../shared/api/types';

// Labels describe what was recorded in Odoo; none of them asserts legal validity.
export const contractTypeLabels: Record<ContractDetail['contract_type'], string> = {
  owner: 'Hợp đồng với chủ đầu tư',
  general_contractor: 'Hợp đồng tổng thầu',
  subcontractor: 'Hợp đồng thầu phụ',
};

export const lifecycleLabels: Record<ContractDetail['lifecycle_state'], string> = {
  not_effective: 'Chưa ghi nhận hiệu lực',
  effective: 'Đã ghi nhận hiệu lực',
  suspended: 'Tạm dừng',
  execution_completed: 'Đã thực hiện xong',
  liquidated: 'Đã thanh lý',
  terminated: 'Đã chấm dứt',
};

export const revisionKindLabels: Record<RevisionStatus['kind'], string> = {
  original: 'Hợp đồng gốc',
  amendment: 'Phụ lục sửa đổi',
  correction: 'Đính chính',
};

export const reviewLabels: Record<RevisionStatus['review_state'], string> = {
  draft: 'Nháp',
  in_review: 'Đang rà soát',
  returned: 'Trả lại để sửa',
  review_complete: 'Đã rà soát xong',
  cancelled: 'Đã hủy',
};

export const signatureLabels: Record<RevisionStatus['signature_status'], string> = {
  unsigned: 'Chưa ghi nhận ký',
  signed_recorded: 'Đã ghi nhận ký',
};

export const effectivityLabels: Record<RevisionStatus['effectivity_status'], string> = {
  not_effective: 'Chưa ghi nhận hiệu lực',
  effective_recorded: 'Đã ghi nhận hiệu lực',
};

export const signatureAuthorityLabels = {
  pending: 'Thẩm quyền ký chưa xác nhận',
  confirmed: 'Thẩm quyền ký đã xác nhận',
} as const;

export const changeKindLabels: Record<ContractLine['change_kind'], string> = {
  original: 'Gốc',
  unchanged: 'Giữ nguyên',
  amended: 'Điều chỉnh',
  added: 'Bổ sung',
};

export const documentKindLabels: Record<ContractDocument['kind'], string> = {
  signed_contract: 'Hợp đồng đã ký',
  amendment: 'Phụ lục',
  base_evidence: 'Minh chứng BASE',
  technical_scope: 'Phạm vi kỹ thuật',
  other: 'Tài liệu khác',
};

export const warningLabels: Record<EffectiveWarning, string> = {
  future_revision_recorded: 'Đã có bản sửa đổi được ghi nhận hiệu lực sau ngày đang xem.',
  no_effective_revision: 'Chưa có bản nào được ghi nhận hiệu lực tại ngày đang xem.',
  effective_date_conflict: 'Có nhiều bản cùng ngày hiệu lực; hệ thống không tự chọn. Cần rà soát hồ sơ.',
};

export const decisionLabels: Record<ApprovalReference['decision'], string> = {
  pending: 'Chờ quyết định',
  approved: 'Đã duyệt',
  rejected: 'Từ chối',
  cancelled: 'Đã hủy',
};

export const verificationLabels: Record<ApprovalReference['verification_state'], string> = {
  pending: 'Minh chứng chưa xác minh',
  verified: 'Minh chứng đã xác minh',
  disputed: 'Minh chứng đang tranh chấp',
};

export const authorityLabels: Record<ApprovalReference['authority_status'], string> = {
  unconfirmed: 'Thẩm quyền chưa xác nhận',
  confirmed: 'Thẩm quyền đã xác nhận',
};

const taxBasisLabels: Record<Money['tax_basis'], string> = {
  unknown: 'chưa rõ thuế',
  excluding_tax: 'chưa gồm thuế',
  including_tax: 'đã gồm thuế',
  mixed: 'nhiều cơ sở thuế',
};

const unavailableMoneyLabels: Record<Money['status'], string> = {
  confirmed: 'Chưa có giá trị',
  unconfirmed: 'Chưa xác nhận',
  incomplete: 'Chưa đủ: có dòng chưa xác nhận',
  empty: 'Chưa có dòng phạm vi',
  mixed_basis: 'Không cộng được: khác cơ sở thuế',
};

/** Group a decimal string for display without converting it to a JavaScript number. */
export function formatDecimal(value: string) {
  const match = /^(-?)(\d+)(?:\.(\d+))?$/.exec(value);
  if (!match) return null;
  const [, sign, integer, fraction] = match;
  const grouped = integer.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
  return `${sign}${grouped}${fraction ? `,${fraction}` : ''}`;
}

/** A missing or unconfirmed value is described in words; it is never shown as 0. */
export function formatMoney(money: Money | null | undefined) {
  if (!money) return 'Chưa có dữ liệu giá trị';
  if (money.value === null) return unavailableMoneyLabels[money.status];
  const grouped = formatDecimal(money.value);
  return grouped === null ? 'Giá trị không hợp lệ' : `${grouped} ${money.currency}`;
}

export function taxBasisNote(money: Money | null | undefined) {
  return money?.value === null || !money ? null : taxBasisLabels[money.tax_basis];
}

/** Render an ISO date without timezone conversion. */
export function formatDate(value: string | null) {
  if (!value) return 'Chưa ghi nhận';
  const [year, month, day] = value.split('-');
  return `${day}/${month}/${year}`;
}

export function formatDateTime(value: string | null) {
  if (!value) return 'Chưa ghi nhận';
  return new Intl.DateTimeFormat('vi-VN', { timeZone: 'Asia/Ho_Chi_Minh', dateStyle: 'medium', timeStyle: 'short' }).format(new Date(value));
}
