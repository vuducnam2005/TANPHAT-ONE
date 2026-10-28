import { ApiError } from '../../../shared/api/client';
import { needsReload, workflowErrorMessage } from '../workflow';

/** Error of a workflow action; offers a reload when the record changed underneath the form. */
export function WorkflowError({ error, onReload }: { error: unknown; onReload?: () => void }) {
  if (!error) return null;
  return (
    <div className="tp-notice is-warning tp-form-error" role="alert">
      <span>{typeof error === 'string' ? error : workflowErrorMessage(error)}</span>
      {error instanceof ApiError && error.requestId && <small>Mã yêu cầu: {error.requestId}</small>}
      {onReload && needsReload(error) && <button className="tp-quiet-button" type="button" onClick={onReload}>Tải lại bản mới nhất</button>}
    </div>
  );
}
