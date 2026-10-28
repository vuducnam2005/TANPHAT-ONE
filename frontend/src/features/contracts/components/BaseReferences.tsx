import type { ApprovalReference } from '../../../shared/api/types';
import { authorityLabels, decisionLabels, formatDateTime, verificationLabels } from '../format';
import { MoneyValue } from './MoneyValue';

const safeLink = (url: string | null) => (url && /^https?:\/\//i.test(url) ? url : null);

export function BaseReferences({ references, financialRead }: { references: ApprovalReference[]; financialRead: boolean }) {
  if (!references.length) return <p className="tp-muted-note">Chưa ghi nhận kết quả BASE cho bản này.</p>;
  return (
    <ul className="tp-base-list">
      {references.map((reference) => {
        const link = safeLink(reference.source_url);
        return (
          <li key={reference.id} className="tp-base-item">
            <div className="tp-base-head">
              <span className={`tp-badge ${reference.verified_result ? 'is-verified' : 'is-unverified'}`}>
                {reference.verified_result ? 'Kết quả BASE đã xác minh' : 'Kết quả BASE chưa xác minh'}
              </span>
              <strong>{reference.base_reference ?? 'Ghi nhận thủ công'}</strong>
              {link && <a href={link} target="_blank" rel="noopener noreferrer">Mở nguồn</a>}
            </div>
            <dl className="tp-inline-facts">
              <div><dt>Quyết định</dt><dd>{decisionLabels[reference.decision]}</dd></div>
              <div><dt>Minh chứng</dt><dd>{verificationLabels[reference.verification_state]}</dd></div>
              <div><dt>Thẩm quyền</dt><dd>{authorityLabels[reference.authority_status]}</dd></div>
              <div><dt>Người quyết định</dt><dd>{reference.decided_by_name ?? 'Chưa ghi nhận'}</dd></div>
              <div><dt>Thời điểm quyết định</dt><dd>{formatDateTime(reference.decided_at)}</dd></div>
              {financialRead && <div><dt>Giá trị được duyệt</dt><dd><MoneyValue money={reference.approved_amount} /></dd></div>}
            </dl>
            {reference.decision_reason && <p className="tp-muted-note">Lý do: {reference.decision_reason}</p>}
          </li>
        );
      })}
    </ul>
  );
}
