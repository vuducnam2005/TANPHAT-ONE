import { Link, useParams, useSearchParams } from 'react-router-dom';
import { parseRouteId, useContract } from '../queries';
import { api, ApiError } from '../../../shared/api/client';
import { StatusPanel } from '../../../shared/ui/StatusPanel';
import type { ContractDetail } from '../../../shared/api/types';
import { BaseReferences } from '../components/BaseReferences';
import { MoneyValue } from '../components/MoneyValue';
import {
  contractTypeLabels, documentKindLabels, effectivityLabels, formatDate, formatDateTime, lifecycleLabels,
  reviewLabels, revisionKindLabels, signatureAuthorityLabels, signatureLabels, warningLabels,
} from '../format';

export function ContractDetailPage() {
  const id = parseRouteId(useParams().contractId);
  const [parameters, setParameters] = useSearchParams();
  const rawAsOf = parameters.get('as_of');
  const asOf = rawAsOf && /^\d{4}-\d{2}-\d{2}$/.test(rawAsOf) ? rawAsOf : undefined;
  const query = useContract(id, asOf);
  const notFound = !id || (query.error instanceof ApiError && query.error.status === 404);
  const badDate = query.error instanceof ApiError && query.error.status === 400;

  if (notFound || query.isError) {
    return (
      <StatusPanel
        title={notFound ? 'Không mở được hợp đồng' : badDate ? 'Ngày xem không hợp lệ' : 'Chưa tải được hồ sơ hợp đồng'}
        description={notFound
          ? 'Hợp đồng không tồn tại hoặc thuộc dự án nằm ngoài phạm vi được phân công.'
          : badDate ? 'Chọn lại một ngày hợp lệ để xem bản áp dụng.' : 'Kiểm tra kết nối rồi thử lại.'}
        error={query.error ?? undefined}
      >
        <Link className="tp-primary-button" to="/contracts">Danh sách hợp đồng</Link>
        {badDate && <button onClick={() => setParameters({})}>Xem theo hôm nay</button>}
        {!notFound && !badDate && <button onClick={() => query.refetch()}>Thử lại</button>}
      </StatusPanel>
    );
  }
  if (query.isPending) return <div role="status" aria-label="Đang tải hồ sơ hợp đồng" className="tp-skeleton" />;

  const contract = query.data.data;
  const financialRead = contract.permissions.financial_read;
  return (
    <section className="tp-page" aria-labelledby="contract-title">
      <Link className="tp-back-link" to="/contracts">← Danh sách hợp đồng</Link>
      <div className="tp-detail-heading">
        <div>
          <span className="tp-code">{contract.code}</span>
          <h2 id="contract-title">{contract.name}</h2>
          <p>{contractTypeLabels[contract.contract_type]} · Dự án <Link to={`/projects/${contract.project.id}`}>{contract.project.code} · {contract.project.name}</Link></p>
        </div>
        <span className="tp-state">{contract.active ? lifecycleLabels[contract.lifecycle_state] : 'Đã lưu trữ'}</span>
      </div>
      {contract.legacy_unverified && <p className="tp-notice is-warning">Hồ sơ nhập từ dữ liệu cũ và chưa được xác minh lại.</p>}
      <dl className="tp-fact-grid">
        <Fact label="Đối tác" value={contract.counterparty?.name ?? 'Chưa cập nhật'} />
        <Fact label="Công ty quản lý" value={contract.company.name} />
        <Fact label="Số bản đã ghi nhận" value={String(contract.revision_count)} />
        <Fact label="Cập nhật gần nhất" value={formatDateTime(contract.updated_at)} />
      </dl>
      <EffectiveSnapshot contract={contract} asOf={asOf} onChange={(value) => setParameters(value ? { as_of: value } : {})} />

      <section className="tp-panel" aria-labelledby="revisions-title">
        <h3 id="revisions-title">Lịch sử bản hợp đồng</h3>
        <p className="tp-muted-note">Kết quả duyệt trên BASE là căn cứ phê duyệt; không đồng nghĩa hợp đồng đã ký hoặc đã có hiệu lực. Trạng thái ký và hiệu lực được ghi nhận riêng cho từng bản.</p>
        <ol className="tp-revision-list">
          {contract.revisions.map((revision) => {
            const current = revision.id === contract.effective_snapshot.revision_id;
            return (
              <li key={revision.id} className={`tp-revision${current ? ' is-current' : ''}`}>
                <div className="tp-revision-head">
                  <div>
                    <span className="tp-code">Bản {revision.sequence} · {revisionKindLabels[revision.kind]}</span>
                    <h4>{revision.name}</h4>
                    {revision.reference && <span className="tp-revision-meta">Số văn bản: {revision.reference}</span>}
                  </div>
                  {current && <span className="tp-badge is-current">Áp dụng tại ngày xem</span>}
                </div>
                <dl className="tp-inline-facts">
                  <div><dt>Rà soát</dt><dd>{reviewLabels[revision.review_state]}</dd></div>
                  <div><dt>Ký</dt><dd>{signatureLabels[revision.signature_status]}{revision.signed_date && ` · ${formatDate(revision.signed_date)}`}</dd></div>
                  <div><dt>Thẩm quyền ký</dt><dd>{signatureAuthorityLabels[revision.signature_authority_status]}</dd></div>
                  <div><dt>Hiệu lực</dt><dd>{effectivityLabels[revision.effectivity_status]}{revision.effective_date && ` · từ ${formatDate(revision.effective_date)}`}</dd></div>
                  <div><dt>Dòng phạm vi</dt><dd>{revision.line_count}</dd></div>
                </dl>
                {revision.legacy_unverified && <span className="tp-badge is-unverified">Dữ liệu cũ chưa xác minh</span>}
                <h5>Kết quả BASE</h5>
                <BaseReferences references={revision.base_references} financialRead={financialRead} />
                <Link className="tp-quiet-button tp-self-start" to={`/contracts/${contract.id}/revisions/${revision.id}`}>Xem phạm vi công việc</Link>
              </li>
            );
          })}
        </ol>
        {!contract.revisions.length && <p className="tp-muted-note">Chưa ghi nhận bản hợp đồng nào.</p>}
      </section>

      <section className="tp-panel" aria-labelledby="documents-title">
        <h3 id="documents-title">Tài liệu</h3>
        {contract.documents.length ? (
          <ul className="tp-document-list">
            {contract.documents.map((document) => (
              <li key={document.id}>
                <div>
                  <strong>{document.name}</strong>
                  <span>{documentKindLabels[document.kind]}{document.confidentiality === 'financial' ? ' · Có thông tin tài chính' : ''}</span>
                </div>
                {document.has_file
                  ? <a className="tp-quiet-button" href={api.contractDocumentUrl(contract.id, document.id)} download>Tải tệp</a>
                  : <span>Chưa có tệp</span>}
              </li>
            ))}
          </ul>
        ) : <p className="tp-muted-note">Chưa có tài liệu trong phạm vi bạn được xem.</p>}
        {!financialRead && <p className="tp-muted-note">Tài liệu có thông tin tài chính chỉ hiển thị khi bạn được cấp quyền xem số tiền của dự án.</p>}
      </section>
    </section>
  );
}

function EffectiveSnapshot({ contract, asOf, onChange }: { contract: ContractDetail; asOf?: string; onChange: (value?: string) => void }) {
  const snapshot = contract.effective_snapshot;
  const effective = contract.revisions.find((revision) => revision.id === snapshot.revision_id);
  const financialRead = contract.permissions.financial_read;
  return (
    <section className="tp-panel" aria-labelledby="snapshot-title">
      <div className="tp-panel-head">
        <h3 id="snapshot-title">Bản áp dụng theo ngày</h3>
        <form className="tp-date-form" key={snapshot.as_of} onSubmit={(event) => {
          event.preventDefault();
          onChange(String(new FormData(event.currentTarget).get('as_of') ?? '') || undefined);
        }}>
          <label><span>Ngày xem</span><input type="date" name="as_of" defaultValue={snapshot.as_of} required /></label>
          <button className="tp-quiet-button" type="submit">Xem bản áp dụng</button>
          {asOf && <button className="tp-quiet-button" type="button" onClick={() => onChange()}>Hôm nay</button>}
        </form>
      </div>
      <dl className="tp-snapshot">
        <div>
          <dt>Bản áp dụng ngày {formatDate(snapshot.as_of)}</dt>
          <dd>{effective ? [...new Set([effective.name, revisionKindLabels[effective.kind]])].join(' · ') : 'Chưa xác định được'}</dd>
        </div>
        {financialRead && (
          <div>
            <dt>Giá trị hợp đồng tại ngày này</dt>
            <dd>{effective ? <MoneyValue money={snapshot.total} /> : 'Không có bản áp dụng'}</dd>
          </div>
        )}
      </dl>
      {!financialRead && <p className="tp-notice">Bạn chưa được cấp quyền xem số tiền của dự án này. Hồ sơ, phạm vi công việc và trạng thái vẫn hiển thị đầy đủ.</p>}
      {snapshot.warnings.map((warning) => <p key={warning} className="tp-notice is-warning">{warningLabels[warning]}</p>)}
      <p className="tp-muted-note">Xác định theo ngày hiệu lực đã ghi nhận; giá trị của bản sửa đổi thay thế bản trước, không cộng dồn. Tra cứu lúc {formatDateTime(snapshot.known_at)}.</p>
    </section>
  );
}

function Fact({ label, value }: { label: string; value: string }) {
  return <div><dt>{label}</dt><dd>{value}</dd></div>;
}
