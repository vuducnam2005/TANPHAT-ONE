import { Link, useParams } from 'react-router-dom';
import { parseRouteId, useContractRevision } from '../queries';
import { ApiError } from '../../../shared/api/client';
import { StatusPanel } from '../../../shared/ui/StatusPanel';
import { BaseReferences } from '../components/BaseReferences';
import { MoneyValue } from '../components/MoneyValue';
import {
  changeKindLabels, effectivityLabels, formatDate, formatDateTime, reviewLabels, revisionKindLabels,
  signatureAuthorityLabels, signatureLabels,
} from '../format';

export function ContractRevisionPage() {
  const parameters = useParams();
  const contractId = parseRouteId(parameters.contractId);
  const revisionId = parseRouteId(parameters.revisionId);
  const query = useContractRevision(contractId, revisionId);
  const notFound = !contractId || !revisionId || (query.error instanceof ApiError && query.error.status === 404);

  if (notFound || query.isError) {
    return (
      <StatusPanel
        title={notFound ? 'Không mở được bản hợp đồng' : 'Chưa tải được bản hợp đồng'}
        description={notFound ? 'Bản hợp đồng không tồn tại hoặc nằm ngoài phạm vi được phân công.' : 'Kiểm tra kết nối rồi thử lại.'}
        error={query.error ?? undefined}
      >
        <Link className="tp-primary-button" to="/contracts">Danh sách hợp đồng</Link>
        {!notFound && <button onClick={() => query.refetch()}>Thử lại</button>}
      </StatusPanel>
    );
  }
  if (query.isPending) return <div role="status" aria-label="Đang tải bản hợp đồng" className="tp-skeleton" />;

  const revision = query.data.data;
  const financialRead = revision.permissions.financial_read;
  return (
    <section className="tp-page" aria-labelledby="revision-title">
      <Link className="tp-back-link" to={`/contracts/${revision.contract_id}`}>← Hồ sơ hợp đồng</Link>
      <div className="tp-detail-heading">
        <div>
          <span className="tp-code">Bản {revision.sequence} · {revisionKindLabels[revision.kind]}</span>
          <h2 id="revision-title">{revision.name}</h2>
          <p>{revision.reference ? `Số văn bản: ${revision.reference}` : 'Chưa ghi nhận số văn bản'}</p>
        </div>
        <span className="tp-state">{effectivityLabels[revision.effectivity_status]}</span>
      </div>
      {revision.legacy_unverified && <p className="tp-notice is-warning">Bản này nhập từ dữ liệu cũ và chưa được xác minh lại.</p>}
      <dl className="tp-fact-grid">
        <Fact label="Rà soát" value={reviewLabels[revision.review_state]} />
        <Fact label="Ký" value={`${signatureLabels[revision.signature_status]} · ${formatDate(revision.signed_date)}`} />
        <Fact label="Thẩm quyền ký" value={signatureAuthorityLabels[revision.signature_authority_status]} />
        <Fact label="Ngày hiệu lực đã ghi nhận" value={formatDate(revision.effective_date)} />
        <Fact label="Thời điểm ghi nhận" value={formatDateTime(revision.recorded_at)} />
        <Fact label="Số dòng phạm vi" value={String(revision.line_count)} />
      </dl>

      <section className="tp-panel" aria-labelledby="scope-title">
        <h3 id="scope-title">Phạm vi công việc</h3>
        {financialRead
          ? <p className="tp-muted-note">Bản sửa đổi ghi lại toàn bộ phạm vi sau sửa đổi; tổng của bản này không cộng dồn với bản trước.</p>
          : <p className="tp-notice">Bạn chưa được cấp quyền xem số tiền của dự án này. Phạm vi công việc vẫn hiển thị đầy đủ.</p>}
        {revision.lines.length ? (
          <table className="tp-table">
            <thead>
              <tr>
                <th scope="col">STT</th><th scope="col">Mã phạm vi</th><th scope="col">Nội dung</th>
                <th scope="col">Hạng mục</th><th scope="col">Thay đổi</th>
                {financialRead && <th scope="col" className="is-number">Giá trị</th>}
              </tr>
            </thead>
            <tbody>
              {revision.lines.map((line, index) => (
                <tr key={line.id}>
                  <td data-label="STT">{index + 1}</td>
                  <td data-label="Mã phạm vi"><span className="tp-code">{line.scope_key}</span></td>
                  <td data-label="Nội dung">{line.name}</td>
                  <td data-label="Hạng mục">{line.work_item ? [line.work_item.code, line.work_item.name].filter(Boolean).join(' · ') : 'Chưa gắn'}</td>
                  <td data-label="Thay đổi">{changeKindLabels[line.change_kind]}</td>
                  {financialRead && <td data-label="Giá trị" className="is-number"><MoneyValue money={line.amount} /></td>}
                </tr>
              ))}
            </tbody>
            {financialRead && (
              <tfoot>
                <tr><th scope="row" colSpan={5}>Tổng giá trị theo bản này</th><td data-label="Tổng" className="is-number"><MoneyValue money={revision.total} /></td></tr>
              </tfoot>
            )}
          </table>
        ) : <p className="tp-muted-note">Bản này chưa có dòng phạm vi công việc.</p>}
      </section>

      <section className="tp-panel" aria-labelledby="base-title">
        <h3 id="base-title">Kết quả BASE</h3>
        <p className="tp-muted-note">Kết quả duyệt trên BASE là căn cứ phê duyệt; không đồng nghĩa bản này đã ký hoặc đã có hiệu lực.</p>
        <BaseReferences references={revision.base_references} financialRead={financialRead} />
      </section>
    </section>
  );
}

function Fact({ label, value }: { label: string; value: string }) {
  return <div><dt>{label}</dt><dd>{value}</dd></div>;
}
