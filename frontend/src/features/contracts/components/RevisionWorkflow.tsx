import { useState } from 'react';
import type { FormEvent } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { api } from '../../../shared/api/client';
import { sessionScope, useCurrentSession } from '../../../shared/api/session';
import type {
  ContractDetail, ContractSubmission, EditDraftRequest, ReturnIssue, RevisionDetail, WorkflowAction, WorkflowResult,
} from '../../../shared/api/types';
import { contractTypeLabels, formatDateTime } from '../format';
import { useContractReviewers, useWorkflowAction } from '../mutations';
import { useContract } from '../queries';
import { emptyAmount, lineDrafts, lineInputs, newLineDraft, outcomeLabels } from '../workflow';
import type { AmountDraft, LineDraft } from '../workflow';
import { WorkflowError } from './WorkflowError';

type RevisionAction = Exclude<WorkflowAction, 'create_amendment'>;
type FormProps = { revision: RevisionDetail; onDone: (result: WorkflowResult, message: string) => void; onReload: () => void };

// Mirrors the request limits in the API contract; the server enforces them.
const MAX_LINES = 500;
const MAX_ISSUES = 100;

const actionLabels: Record<RevisionAction, string> = {
  edit_draft: 'Sửa bản nháp',
  submit_review: 'Gửi rà soát',
  return_review: 'Trả lại để sửa',
  begin_rework: 'Mở lại để sửa',
};

/**
 * Actions offered here come only from the server's allowed_actions; the server
 * rechecks scope, capability, state and version on every call.
 */
export function RevisionWorkflow({ revision }: { revision: RevisionDetail }) {
  const session = useCurrentSession();
  const queryClient = useQueryClient();
  const [open, setOpen] = useState<RevisionAction | null>(null);
  const [generation, setGeneration] = useState(0);
  const [notice, setNotice] = useState<string | null>(null);
  const actions = revision.allowed_actions.filter((action): action is RevisionAction => action !== 'create_amendment');
  const active = open && actions.includes(open) ? open : null;

  async function reload() {
    const scope = sessionScope(session);
    await Promise.all(['contract', 'contract-revision'].map((key) => queryClient.invalidateQueries({ queryKey: [...scope, key] })));
    setGeneration((value) => value + 1);
  }

  function done(result: WorkflowResult, message: string) {
    setNotice(result.replayed ? `${message} Yêu cầu này đã được ghi nhận trước đó nên không thực hiện lại.` : message);
    setOpen(null);
    setGeneration((value) => value + 1);
  }

  if (!actions.length && !revision.submissions.length) return null;
  const props: FormProps = { revision, onDone: done, onReload: () => void reload() };
  return (
    <section className="tp-panel" aria-labelledby="workflow-title">
      <div className="tp-panel-head">
        <h3 id="workflow-title">Soạn thảo và rà soát</h3>
        {actions.length > 0 && (
          <div className="tp-form-actions" role="group" aria-label="Thao tác với bản hợp đồng">
            {actions.map((action) => (
              <button key={action} type="button" aria-pressed={active === action}
                className={active === action ? 'tp-primary-button' : 'tp-quiet-button'}
                onClick={() => { setNotice(null); setOpen(active === action ? null : action); }}>
                {actionLabels[action]}
              </button>
            ))}
          </div>
        )}
      </div>
      <p className="tp-muted-note">Rà soát nội bộ chỉ ghi nhận góp ý thương mại; không thay cho kết quả duyệt trên BASE, chữ ký hay hiệu lực của hợp đồng.</p>
      {notice && <p className="tp-notice" role="status">{notice}</p>}
      {active === 'edit_draft' && (revision.kind === 'original'
        ? <OriginalDraftEditor key={generation} {...props} />
        : <DraftEditor key={generation} {...props} header={null} />)}
      {active === 'submit_review' && <SubmitReviewForm key={generation} {...props} />}
      {active === 'return_review' && <ReturnReviewForm key={generation} {...props} />}
      {active === 'begin_rework' && <BeginReworkForm key={generation} {...props} />}
      {revision.submissions.length > 0 && <SubmissionHistory submissions={revision.submissions} />}
    </section>
  );
}

/** The contract header is edited together with the original revision, against the same contract version. */
function OriginalDraftEditor(props: FormProps) {
  const contract = useContract(props.revision.contract_id, undefined);
  if (contract.isPending) return <div role="status" aria-label="Đang tải thông tin chung" className="tp-skeleton tp-skeleton-small" />;
  if (contract.isError) return <WorkflowError error={contract.error} />;
  if (contract.data.data.version !== props.revision.contract_version) {
    return (
      <div className="tp-notice is-warning" role="alert">
        Thông tin chung và bản nháp đang khác phiên bản. <button className="tp-quiet-button" type="button" onClick={props.onReload}>Tải lại bản mới nhất</button>
      </div>
    );
  }
  return <DraftEditor {...props} header={contract.data.data} />;
}

function DraftEditor({ revision, onDone, onReload, header }: FormProps & { header: ContractDetail | null }) {
  const withAmounts = revision.permissions.financial_read && revision.permissions.financial_draft_edit;
  // Fixed when the form opens, so a background refresh never silently replaces what the user is editing.
  const [base] = useState(() => ({
    version: revision.contract_version,
    code: header?.code ?? '', contractName: header?.name ?? '', contractType: header?.contract_type ?? 'owner',
    name: revision.name, reference: revision.reference ?? '', lines: lineDrafts(revision.lines, withAmounts),
  }));
  const [code, setCode] = useState(base.code);
  const [contractName, setContractName] = useState(base.contractName);
  const [contractType, setContractType] = useState(base.contractType);
  const [name, setName] = useState(base.name);
  const [reference, setReference] = useState(base.reference);
  const [lines, setLines] = useState<LineDraft[]>(base.lines);
  const [localError, setLocalError] = useState<string | null>(null);
  const action = useWorkflowAction((body: EditDraftRequest, options) => api.editDraft(revision.contract_id, revision.id, body, options));

  function updateLine(index: number, patch: Partial<LineDraft>) {
    setLines((current) => current.map((line, position) => position === index ? { ...line, ...patch } : line));
  }
  function updateAmount(index: number, patch: Partial<AmountDraft>) {
    setLines((current) => current.map((line, position) =>
      position === index ? { ...line, amount: { ...(line.amount ?? emptyAmount()), ...patch } } : line));
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    setLocalError(null);
    action.reset();
    const body: EditDraftRequest = { expected_version: base.version };
    if (header) {
      const contract: NonNullable<EditDraftRequest['contract']> = {};
      if (code.trim() !== base.code) contract.code = code.trim();
      if (contractName.trim() !== base.contractName) contract.name = contractName.trim();
      if (contractType !== base.contractType) contract.contract_type = contractType;
      if (Object.keys(contract).length) body.contract = contract;
    }
    const revisionFields: NonNullable<EditDraftRequest['revision']> = {};
    if (name.trim() !== base.name) revisionFields.name = name.trim();
    if (reference.trim() !== base.reference) revisionFields.reference = reference.trim() || null;
    if (Object.keys(revisionFields).length) body.revision = revisionFields;
    const edited = lineInputs(lines, withAmounts);
    if ('error' in edited) return setLocalError(edited.error);
    const loaded = lineInputs(base.lines, withAmounts);
    if (!('lines' in loaded) || JSON.stringify(edited.lines) !== JSON.stringify(loaded.lines)) body.lines = edited.lines;
    if (!body.contract && !body.revision && !body.lines) return setLocalError('Chưa có thay đổi để lưu.');
    try {
      onDone(await action.mutateAsync(body).then((result) => result.data), 'Đã lưu bản nháp.');
    } catch {
      // Shown by WorkflowError below.
    }
  }

  return (
    <form className="tp-form" onSubmit={submit} aria-label="Sửa bản nháp">
      {header && (
        <fieldset className="tp-fieldset">
          <legend>Thông tin chung của hợp đồng</legend>
          <div className="tp-form-grid">
            <label className="tp-field"><span>Số hợp đồng</span><input value={code} onChange={(event) => setCode(event.target.value)} required maxLength={64} /></label>
            <label className="tp-field tp-field-wide"><span>Tên hợp đồng</span><input value={contractName} onChange={(event) => setContractName(event.target.value)} required maxLength={255} /></label>
            <label className="tp-field">
              <span>Loại hợp đồng</span>
              <select value={contractType} onChange={(event) => setContractType(event.target.value as ContractDetail['contract_type'])}>
                {Object.entries(contractTypeLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
              </select>
            </label>
          </div>
        </fieldset>
      )}
      <fieldset className="tp-fieldset">
        <legend>Bản hợp đồng</legend>
        <div className="tp-form-grid">
          <label className="tp-field tp-field-wide"><span>Tên bản</span><input value={name} onChange={(event) => setName(event.target.value)} required maxLength={255} /></label>
          <label className="tp-field"><span>Số văn bản</span><input value={reference} onChange={(event) => setReference(event.target.value)} maxLength={128} /></label>
        </div>
      </fieldset>
      <fieldset className="tp-fieldset">
        <legend>Phạm vi công việc</legend>
        {withAmounts
          ? <p className="tp-muted-note">Giá trị nhập dạng số, không dấu phân cách hàng nghìn; dùng dấu phẩy hoặc chấm cho phần thập phân. Chưa xác nhận thì để trạng thái “Chưa xác nhận”, không nhập 0.</p>
          : <p className="tp-notice">Bạn sửa được nội dung và mã phạm vi; giá trị đã ghi nhận được giữ nguyên. Xóa dòng đã có giá trị cần quyền sửa giá trị của dự án.</p>}
        <table className="tp-table tp-line-editor">
          <thead>
            <tr>
              <th scope="col">Mã phạm vi</th><th scope="col">Nội dung</th>
              {withAmounts && <><th scope="col">Giá trị</th><th scope="col">Số tiền</th><th scope="col">Cơ sở thuế</th></>}
              <th scope="col"><span className="tp-visually-hidden">Xóa dòng</span></th>
            </tr>
          </thead>
          <tbody>
            {lines.map((line, index) => (
              <tr key={index}>
                <td data-label="Mã phạm vi">
                  <input aria-label={`Mã phạm vi dòng ${index + 1}`} value={line.scopeKey} readOnly={!line.isNew} maxLength={64}
                    onChange={(event) => updateLine(index, { scopeKey: event.target.value })} />
                </td>
                <td data-label="Nội dung">
                  <input aria-label={`Nội dung dòng ${index + 1}`} value={line.name} maxLength={255}
                    onChange={(event) => updateLine(index, { name: event.target.value })} />
                </td>
                {withAmounts && <AmountCells index={index} amount={line.amount ?? emptyAmount()} onChange={(patch) => updateAmount(index, patch)} />}
                <td data-label="Xóa">
                  <button className="tp-quiet-button" type="button" onClick={() => setLines((current) => current.filter((_, position) => position !== index))}>Xóa</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!lines.length && <p className="tp-muted-note">Bản nháp chưa có dòng phạm vi.</p>}
        <button className="tp-quiet-button tp-self-start" type="button" disabled={lines.length >= MAX_LINES}
          onClick={() => setLines((current) => [...current, newLineDraft(withAmounts)])}>Thêm dòng phạm vi</button>
      </fieldset>
      <WorkflowError error={localError ?? action.error} onReload={onReload} />
      <div className="tp-form-actions">
        <button className="tp-primary-button" type="submit" disabled={action.isPending}>{action.isPending ? 'Đang lưu…' : 'Lưu bản nháp'}</button>
      </div>
    </form>
  );
}

function AmountCells({ index, amount, onChange }: { index: number; amount: AmountDraft; onChange: (patch: Partial<AmountDraft>) => void }) {
  const confirmed = amount.state === 'confirmed';
  return (
    <>
      <td data-label="Giá trị">
        <select aria-label={`Trạng thái giá trị dòng ${index + 1}`} value={amount.state}
          onChange={(event) => onChange({ state: event.target.value as AmountDraft['state'] })}>
          <option value="unconfirmed">Chưa xác nhận</option>
          <option value="confirmed">Đã xác nhận</option>
        </select>
      </td>
      <td data-label="Số tiền">
        <input aria-label={`Số tiền dòng ${index + 1}`} inputMode="decimal" value={confirmed ? amount.value : ''}
          disabled={!confirmed} placeholder={confirmed ? '' : 'Chưa xác nhận'} required={confirmed}
          onChange={(event) => onChange({ value: event.target.value })} />
      </td>
      <td data-label="Cơ sở thuế">
        <select aria-label={`Cơ sở thuế dòng ${index + 1}`} value={amount.taxBasis}
          onChange={(event) => onChange({ taxBasis: event.target.value as AmountDraft['taxBasis'] })}>
          <option value="unknown">Chưa rõ</option>
          <option value="excluding_tax">Chưa gồm thuế</option>
          <option value="including_tax">Đã gồm thuế</option>
        </select>
      </td>
    </>
  );
}

function SubmitReviewForm({ revision, onDone, onReload }: FormProps) {
  const [baseVersion] = useState(revision.contract_version);
  const reviewers = useContractReviewers(revision.contract_id, true);
  const [reviewerId, setReviewerId] = useState('');
  const [fixSummary, setFixSummary] = useState('');
  const resubmission = revision.submissions.length > 0;
  const action = useWorkflowAction((body: { expected_version: number; reviewer_id: number; fix_summary?: string | null }, options) =>
    api.submitReview(revision.contract_id, revision.id, body, options));

  async function submit(event: FormEvent) {
    event.preventDefault();
    try {
      const result = await action.mutateAsync({
        expected_version: baseVersion, reviewer_id: Number(reviewerId),
        ...(resubmission ? { fix_summary: fixSummary.trim() } : {}),
      });
      onDone(result.data, 'Đã gửi rà soát. Bản hợp đồng được khóa cho đến khi người rà soát trả lại.');
    } catch {
      // Shown by WorkflowError below.
    }
  }

  const options = reviewers.data?.data ?? [];
  return (
    <form className="tp-form" onSubmit={submit} aria-label="Gửi rà soát">
      <p className="tp-muted-note">Gửi rà soát ghi lại nguyên phạm vi và giá trị hiện tại. Sau khi gửi, bản nháp không sửa được cho đến khi bị trả lại.</p>
      <div className="tp-form-grid">
        <label className="tp-field">
          <span>Người rà soát</span>
          <select value={reviewerId} onChange={(event) => setReviewerId(event.target.value)} required disabled={reviewers.isPending}>
            <option value="">{reviewers.isPending ? 'Đang tải…' : 'Chọn người rà soát'}</option>
            {options.map((reviewer) => <option key={reviewer.id} value={reviewer.id}>{reviewer.name}</option>)}
          </select>
        </label>
        {resubmission && (
          <label className="tp-field tp-field-wide">
            <span>Nội dung đã sửa so với lần bị trả lại</span>
            <textarea value={fixSummary} onChange={(event) => setFixSummary(event.target.value)} required maxLength={2000} />
          </label>
        )}
      </div>
      {reviewers.isSuccess && !options.length && <p className="tp-notice is-warning">Dự án chưa có người được cấp quyền rà soát thương mại và xem số tiền.</p>}
      {reviewers.isError && <WorkflowError error={reviewers.error} />}
      <WorkflowError error={action.error} onReload={onReload} />
      <div className="tp-form-actions">
        <button className="tp-primary-button" type="submit" disabled={action.isPending || !options.length}>{action.isPending ? 'Đang gửi…' : 'Gửi rà soát'}</button>
      </div>
    </form>
  );
}

function ReturnReviewForm({ revision, onDone, onReload }: FormProps) {
  const [baseVersion] = useState(revision.contract_version);
  const [reason, setReason] = useState('');
  const [issues, setIssues] = useState<{ scopeKey: string; note: string }[]>([]);
  const action = useWorkflowAction((body: { expected_version: number; reason: string; issues: ReturnIssue[] }, options) =>
    api.returnReview(revision.contract_id, revision.id, body, options));

  async function submit(event: FormEvent) {
    event.preventDefault();
    try {
      const result = await action.mutateAsync({
        expected_version: baseVersion, reason: reason.trim(),
        issues: issues.map((issue) => ({ scope_key: issue.scopeKey || null, note: issue.note.trim() })),
      });
      onDone(result.data, 'Đã trả lại bản hợp đồng để sửa.');
    } catch {
      // Shown by WorkflowError below.
    }
  }

  return (
    <form className="tp-form" onSubmit={submit} aria-label="Trả lại để sửa">
      <label className="tp-field">
        <span>Lý do trả lại</span>
        <textarea value={reason} onChange={(event) => setReason(event.target.value)} required maxLength={2000} />
      </label>
      <fieldset className="tp-fieldset">
        <legend>Ý kiến theo dòng phạm vi (không bắt buộc)</legend>
        {issues.map((issue, index) => (
          <div className="tp-issue-row" key={index}>
            <label className="tp-field">
              <span>Dòng phạm vi</span>
              <select value={issue.scopeKey} onChange={(event) => setIssues((current) => current.map((item, position) => position === index ? { ...item, scopeKey: event.target.value } : item))}>
                <option value="">Ý kiến chung</option>
                {revision.lines.map((line) => <option key={line.id} value={line.scope_key}>{line.scope_key} · {line.name}</option>)}
              </select>
            </label>
            <label className="tp-field tp-field-wide">
              <span>Nội dung</span>
              <input value={issue.note} required maxLength={1000} onChange={(event) => setIssues((current) => current.map((item, position) => position === index ? { ...item, note: event.target.value } : item))} />
            </label>
            <button className="tp-quiet-button" type="button" onClick={() => setIssues((current) => current.filter((_, position) => position !== index))}>Xóa</button>
          </div>
        ))}
        <button className="tp-quiet-button tp-self-start" type="button" disabled={issues.length >= MAX_ISSUES}
          onClick={() => setIssues((current) => [...current, { scopeKey: '', note: '' }])}>Thêm ý kiến</button>
      </fieldset>
      <WorkflowError error={action.error} onReload={onReload} />
      <div className="tp-form-actions">
        <button className="tp-primary-button" type="submit" disabled={action.isPending}>{action.isPending ? 'Đang lưu…' : 'Trả lại để sửa'}</button>
      </div>
    </form>
  );
}

function BeginReworkForm({ revision, onDone, onReload }: FormProps) {
  const [baseVersion] = useState(revision.contract_version);
  const [reason, setReason] = useState('');
  const action = useWorkflowAction((body: { expected_version: number; reason: string }, options) =>
    api.beginRework(revision.contract_id, revision.id, body, options));

  async function submit(event: FormEvent) {
    event.preventDefault();
    try {
      const result = await action.mutateAsync({ expected_version: baseVersion, reason: reason.trim() });
      onDone(result.data, 'Đã mở lại bản nháp để sửa.');
    } catch {
      // Shown by WorkflowError below.
    }
  }

  return (
    <form className="tp-form" onSubmit={submit} aria-label="Mở lại để sửa">
      <label className="tp-field">
        <span>Lý do mở lại để sửa</span>
        <textarea value={reason} onChange={(event) => setReason(event.target.value)} required maxLength={2000} />
      </label>
      <WorkflowError error={action.error} onReload={onReload} />
      <div className="tp-form-actions">
        <button className="tp-primary-button" type="submit" disabled={action.isPending}>{action.isPending ? 'Đang lưu…' : 'Mở lại để sửa'}</button>
      </div>
    </form>
  );
}

function SubmissionHistory({ submissions }: { submissions: ContractSubmission[] }) {
  return (
    <section aria-labelledby="submissions-title">
      <h4 id="submissions-title" className="tp-subheading">Lịch sử gửi rà soát</h4>
      <ol className="tp-revision-list">
        {[...submissions].reverse().map((submission) => (
          <li key={submission.id} className="tp-revision">
            <div className="tp-revision-head">
              <strong>Lần gửi {submission.sequence}</strong>
              <span className={`tp-badge ${submission.outcome === 'returned' ? 'is-unverified' : 'is-current'}`}>{outcomeLabels[submission.outcome]}</span>
            </div>
            <dl className="tp-inline-facts">
              <div><dt>Người gửi</dt><dd>{submission.submitted_by?.name ?? 'Không rõ'} · {formatDateTime(submission.submitted_at)}</dd></div>
              <div><dt>Người rà soát</dt><dd>{submission.reviewer?.name ?? 'Không rõ'}</dd></div>
              {submission.fix_summary && <div><dt>Nội dung đã sửa</dt><dd>{submission.fix_summary}</dd></div>}
              {submission.outcome === 'returned' && (
                <div><dt>Trả lại</dt><dd>{submission.returned_by?.name ?? 'Không rõ'} · {formatDateTime(submission.returned_at)}</dd></div>
              )}
              {submission.return_reason && <div><dt>Lý do trả lại</dt><dd>{submission.return_reason}</dd></div>}
              {submission.rework_reason && (
                <div><dt>Mở lại để sửa</dt><dd>{submission.rework_started_by?.name ?? 'Không rõ'} · {formatDateTime(submission.rework_started_at)} · {submission.rework_reason}</dd></div>
              )}
            </dl>
            {submission.return_issues.length > 0 && (
              <ul className="tp-issue-list">
                {submission.return_issues.map((issue, index) => (
                  <li key={index}><span className="tp-code">{issue.scope_key ?? 'Chung'}</span> {issue.note}</li>
                ))}
              </ul>
            )}
          </li>
        ))}
      </ol>
    </section>
  );
}
