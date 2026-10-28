import { Link } from 'react-router-dom';
import type { ContractSummary } from '../../../shared/api/types';
import { contractTypeLabels, lifecycleLabels, signatureLabels } from '../format';

export function ContractCard({ contract }: { contract: ContractSummary }) {
  const latest = contract.latest_revision;
  return (
    <Link className="tp-project-card" to={`/contracts/${contract.id}`}>
      <div className="tp-project-card-top">
        <span className="tp-code">{contract.code}</span>
        <span className="tp-state">{contract.active ? lifecycleLabels[contract.lifecycle_state] : 'Đã lưu trữ'}</span>
      </div>
      <h3>{contract.name}</h3>
      <dl>
        <div><dt>Dự án</dt><dd>{contract.project.code} · {contract.project.name}</dd></div>
        <div><dt>Loại</dt><dd>{contractTypeLabels[contract.contract_type]}</dd></div>
        <div><dt>Đối tác</dt><dd>{contract.counterparty?.name ?? 'Chưa cập nhật'}</dd></div>
        <div><dt>Bản mới nhất</dt><dd>{latest ? `${latest.name} · ${signatureLabels[latest.signature_status]}` : 'Chưa có bản'}</dd></div>
      </dl>
      {contract.legacy_unverified && <span className="tp-badge is-unverified">Dữ liệu cũ chưa xác minh</span>}
      <span className="tp-card-action">Mở hồ sơ hợp đồng <b>→</b></span>
    </Link>
  );
}
