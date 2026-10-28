import { useState } from 'react';
import type { FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { api } from '../../../shared/api/client';
import type { ContractDetail, CreateContractRequest } from '../../../shared/api/types';
import { useProjects } from '../../projects/queries';
import { contractTypeLabels } from '../format';
import { useWorkflowAction } from '../mutations';
import { WorkflowError } from './WorkflowError';

type ContractType = ContractDetail['contract_type'];

/**
 * Header-only draft creation; scope lines are added in the draft editor. The
 * server decides whether the user may draft contracts for the chosen project.
 */
export function CreateContractForm({ defaultProjectId, onClose }: { defaultProjectId?: number; onClose: () => void }) {
  const navigate = useNavigate();
  const projects = useProjects();
  const action = useWorkflowAction(api.createContract);
  const [projectId, setProjectId] = useState(defaultProjectId ? String(defaultProjectId) : '');
  const [code, setCode] = useState('');
  const [name, setName] = useState('');
  const [contractType, setContractType] = useState<ContractType>('owner');
  const [currency, setCurrency] = useState('VND');
  const [reference, setReference] = useState('');

  async function submit(event: FormEvent) {
    event.preventDefault();
    const body: CreateContractRequest = {
      project_id: Number(projectId), code: code.trim(), name: name.trim(), contract_type: contractType,
      currency: currency.trim().toUpperCase(),
      ...(reference.trim() ? { revision: { reference: reference.trim() } } : {}),
    };
    try {
      const result = await action.mutateAsync(body);
      navigate(`/contracts/${result.data.contract_id}/revisions/${result.data.revision_id}`);
    } catch {
      // Shown by WorkflowError below.
    }
  }

  const options = projects.data?.data ?? [];
  return (
    <section className="tp-panel" aria-labelledby="create-contract-title">
      <h3 id="create-contract-title">Tạo hợp đồng nháp</h3>
      <p className="tp-muted-note">Bản nháp chỉ lưu thông tin để soạn và rà soát nội bộ; chưa phải hợp đồng đã duyệt, đã ký hay có hiệu lực. Phạm vi công việc và giá trị nhập ở bước soạn bản nháp.</p>
      <form className="tp-form" onSubmit={submit}>
        <div className="tp-form-grid">
          <label className="tp-field">
            <span>Dự án</span>
            <select value={projectId} onChange={(event) => setProjectId(event.target.value)} required disabled={projects.isPending}>
              <option value="">{projects.isPending ? 'Đang tải dự án…' : 'Chọn dự án'}</option>
              {options.map((project) => <option key={project.id} value={project.id}>{project.code} · {project.name}</option>)}
            </select>
          </label>
          <label className="tp-field">
            <span>Số hợp đồng</span>
            <input value={code} onChange={(event) => setCode(event.target.value)} required maxLength={64} autoComplete="off" />
          </label>
          <label className="tp-field tp-field-wide">
            <span>Tên hợp đồng</span>
            <input value={name} onChange={(event) => setName(event.target.value)} required maxLength={255} />
          </label>
          <label className="tp-field">
            <span>Loại hợp đồng</span>
            <select value={contractType} onChange={(event) => setContractType(event.target.value as ContractType)}>
              {Object.entries(contractTypeLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
            </select>
          </label>
          <label className="tp-field">
            <span>Đơn vị tiền tệ</span>
            <input value={currency} onChange={(event) => setCurrency(event.target.value)} required maxLength={3} pattern="[A-Za-z]{3}" />
          </label>
          <label className="tp-field">
            <span>Số văn bản (nếu có)</span>
            <input value={reference} onChange={(event) => setReference(event.target.value)} maxLength={128} />
          </label>
        </div>
        {projects.isError && <WorkflowError error={projects.error} />}
        {projects.data?.meta.pagination?.has_more && <p className="tp-muted-note">Danh sách hiển thị 20 dự án đầu tiên trong phạm vi được phân công.</p>}
        <WorkflowError error={action.error} />
        <div className="tp-form-actions">
          <button className="tp-primary-button" type="submit" disabled={action.isPending}>{action.isPending ? 'Đang lưu…' : 'Tạo bản nháp'}</button>
          <button className="tp-quiet-button" type="button" onClick={onClose} disabled={action.isPending}>Đóng</button>
        </div>
      </form>
    </section>
  );
}
