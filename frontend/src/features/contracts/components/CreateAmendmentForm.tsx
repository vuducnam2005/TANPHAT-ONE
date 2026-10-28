import { useState } from 'react';
import type { FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../../../shared/api/client';
import type { ContractDetail, CreateAmendmentRequest } from '../../../shared/api/types';
import { useWorkflowAction } from '../mutations';
import { WorkflowError } from './WorkflowError';

/** Opens an amendment draft that copies the scope of the latest revision; the version is fixed when the form opens. */
export function CreateAmendmentForm({ contract, onClose, onReload }: { contract: ContractDetail; onClose: () => void; onReload: () => void }) {
  const navigate = useNavigate();
  const [baseVersion] = useState(contract.version);
  const [name, setName] = useState('');
  const [reference, setReference] = useState('');
  const action = useWorkflowAction((body: CreateAmendmentRequest, options) => api.createAmendment(contract.id, body, options));

  async function submit(event: FormEvent) {
    event.preventDefault();
    try {
      const result = await action.mutateAsync({ expected_version: baseVersion, name: name.trim(), reference: reference.trim() || null });
      navigate(`/contracts/${result.data.contract_id}/revisions/${result.data.revision_id}`);
    } catch {
      // Shown by WorkflowError below.
    }
  }

  return (
    <section className="tp-panel" aria-labelledby="amendment-title">
      <h3 id="amendment-title">Tạo phụ lục nháp</h3>
      <p className="tp-muted-note">Phụ lục nháp sao chép phạm vi của bản gần nhất để chỉnh sửa. Phụ lục chỉ là bản nháp nội bộ cho đến khi được rà soát, duyệt và ký theo quy trình riêng.</p>
      <form className="tp-form" onSubmit={submit}>
        <div className="tp-form-grid">
          <label className="tp-field tp-field-wide">
            <span>Tên phụ lục</span>
            <input value={name} onChange={(event) => setName(event.target.value)} required maxLength={255} />
          </label>
          <label className="tp-field">
            <span>Số văn bản (nếu có)</span>
            <input value={reference} onChange={(event) => setReference(event.target.value)} maxLength={128} />
          </label>
        </div>
        <WorkflowError error={action.error} onReload={onReload} />
        <div className="tp-form-actions">
          <button className="tp-primary-button" type="submit" disabled={action.isPending}>{action.isPending ? 'Đang lưu…' : 'Tạo phụ lục nháp'}</button>
          <button className="tp-quiet-button" type="button" onClick={onClose} disabled={action.isPending}>Đóng</button>
        </div>
      </form>
    </section>
  );
}
