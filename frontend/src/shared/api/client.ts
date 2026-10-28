import type {
  ApiEnvelope, ApiErrorBody, BeginReworkRequest, ContractDetail, ContractSummary, CreateAmendmentRequest,
  CreateContractRequest, EditDraftRequest, NameRef, Project, ReturnReviewRequest, RevisionDetail, SessionBootstrap,
  SubmitReviewRequest, WorkflowResult,
} from './types';

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly details: unknown;
  readonly requestId?: string;

  constructor(status: number, body: ApiErrorBody | undefined, fallback: string) {
    super(body?.error?.message ?? fallback);
    this.name = 'ApiError';
    this.status = status;
    this.code = body?.error?.code ?? 'http_error';
    this.details = body?.error?.details;
    this.requestId = body?.meta?.request_id;
  }
}

function requestId() {
  return globalThis.crypto?.randomUUID?.() ?? `tp-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

async function readJson<T>(response: Response): Promise<T | undefined> {
  const contentType = response.headers.get('content-type') ?? '';
  if (!contentType.includes('application/json')) return undefined;
  try { return await response.json() as T; } catch { return undefined; }
}

async function get<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(path, {
    method: 'GET',
    credentials: 'include',
    headers: { Accept: 'application/json', 'X-Request-ID': requestId() },
    signal: signal ? AbortSignal.any([signal, AbortSignal.timeout(15000)]) : AbortSignal.timeout(15000),
  });
  const body = await readJson<T | ApiErrorBody>(response);
  if (!response.ok) {
    const errorBody = body && typeof body === 'object' && 'error' in body ? body as ApiErrorBody : undefined;
    throw new ApiError(response.status, errorBody, 'Không thể đọc dữ liệu.');
  }
  if (body === undefined) throw new ApiError(response.status, undefined, 'API trả về dữ liệu không hợp lệ.');
  return body as T;
}

/** One key per user intent: a retry of the same intent reuses it so the server applies it once. */
export interface WriteOptions {
  csrfToken: string;
  idempotencyKey: string;
}

// Writes go only to the /api/v1 business endpoints; the server rechecks scope,
// capability, state and version on every call.
async function send<T>(method: 'POST' | 'PATCH', path: string, body: object, options: WriteOptions): Promise<T> {
  const response = await fetch(path, {
    method,
    credentials: 'same-origin',
    cache: 'no-store',
    headers: {
      Accept: 'application/json',
      'Content-Type': 'application/json',
      'X-Request-ID': requestId(),
      'X-CSRF-Token': options.csrfToken,
      'Idempotency-Key': options.idempotencyKey,
    },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(30000),
  });
  const parsed = await readJson<T | ApiErrorBody>(response);
  if (!response.ok) {
    const errorBody = parsed && typeof parsed === 'object' && 'error' in parsed ? parsed as ApiErrorBody : undefined;
    throw new ApiError(response.status, errorBody, 'Chưa lưu được thay đổi.');
  }
  if (parsed === undefined) throw new ApiError(response.status, undefined, 'API trả về dữ liệu không hợp lệ.');
  return parsed as T;
}

type WorkflowResponse = Promise<ApiEnvelope<WorkflowResult>>;
const revisionPath = (contractId: number, revisionId: number) => `/api/v1/contracts/${contractId}/revisions/${revisionId}`;

type LoginResult = { requiresVerification: boolean };
type OdooLoginResponse = {
  result?: { uid?: number | null };
  error?: { data?: { name?: string } };
};

export class LoginError extends Error {
  constructor(readonly code: 'credentials' | 'connection' | 'rate_limit') {
    super(code === 'credentials'
      ? 'Tên đăng nhập hoặc mật khẩu chưa đúng. Vui lòng kiểm tra và thử lại.'
      : code === 'rate_limit'
        ? 'Đã thử đăng nhập quá nhiều lần. Vui lòng chờ một lúc rồi thử lại.'
        : 'Chưa kết nối được hệ thống. Vui lòng thử lại sau.');
    this.name = 'LoginError';
  }
}

// Authentication alone uses Odoo's native endpoint. Business data stays on /api/v1.
async function authenticate(login: string, password: string): Promise<LoginResult> {
  let response: Response;
  try {
    response = await fetch('/web/session/authenticate', {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      cache: 'no-store',
      signal: AbortSignal.timeout(30000),
      body: JSON.stringify({
        jsonrpc: '2.0', method: 'call', id: requestId(),
        params: {
          db: import.meta.env.VITE_ODOO_DATABASE?.trim() || (import.meta.env.DEV ? 'tp_tanphat_dev' : ''),
          login: login.trim(), password,
        },
      }),
    });
  } catch {
    throw new LoginError('connection');
  }
  if (response.status === 429) throw new LoginError('rate_limit');
  if (!response.ok) throw new LoginError('connection');
  const body = await readJson<OdooLoginResponse>(response);
  if (body?.error) {
    if (body.error.data?.name === 'odoo.exceptions.AccessDenied') throw new LoginError('credentials');
    throw new LoginError('connection');
  }
  if (body?.result?.uid === null) return { requiresVerification: true };
  if (typeof body?.result?.uid !== 'number' || body.result.uid <= 0) throw new LoginError('connection');
  return { requiresVerification: false };
}

export const api = {
  authenticate,
  session: (signal?: AbortSignal) => get<ApiEnvelope<SessionBootstrap>>('/api/v1/me', signal),
  projects: (query: { q?: string; limit?: number; offset?: number } = {}, signal?: AbortSignal) => {
    const params = new URLSearchParams();
    if (query.q?.trim()) params.set('q', query.q.trim());
    if (query.limit) params.set('limit', String(query.limit));
    if (query.offset) params.set('offset', String(query.offset));
    const suffix = params.toString() ? `?${params}` : '';
    return get<ApiEnvelope<Project[]>>(`/api/v1/projects${suffix}`, signal);
  },
  project: (id: number, signal?: AbortSignal) => get<ApiEnvelope<Project>>(`/api/v1/projects/${id}`, signal),
  contracts: (query: { q?: string; limit?: number; offset?: number; projectId?: number } = {}, signal?: AbortSignal) => {
    const params = new URLSearchParams();
    if (query.q?.trim()) params.set('q', query.q.trim());
    if (query.limit) params.set('limit', String(query.limit));
    if (query.offset) params.set('offset', String(query.offset));
    if (query.projectId) params.set('project_id', String(query.projectId));
    const suffix = params.toString() ? `?${params}` : '';
    return get<ApiEnvelope<ContractSummary[]>>(`/api/v1/contracts${suffix}`, signal);
  },
  // Without asOf the backend resolves "today" in the user's timezone.
  contract: (id: number, asOf?: string, signal?: AbortSignal) => {
    const suffix = asOf ? `?${new URLSearchParams({ as_of: asOf })}` : '';
    return get<ApiEnvelope<ContractDetail>>(`/api/v1/contracts/${id}${suffix}`, signal);
  },
  contractRevision: (contractId: number, revisionId: number, signal?: AbortSignal) =>
    get<ApiEnvelope<RevisionDetail>>(`/api/v1/contracts/${contractId}/revisions/${revisionId}`, signal),
  // Downloads are plain same-origin links so the browser sends the Odoo session cookie.
  contractDocumentUrl: (contractId: number, documentId: number) =>
    `/api/v1/contracts/${contractId}/documents/${documentId}/content`,
  contractReviewers: (contractId: number, signal?: AbortSignal) =>
    get<ApiEnvelope<NameRef[]>>(`/api/v1/contracts/${contractId}/reviewers`, signal),
  createContract: (body: CreateContractRequest, options: WriteOptions): WorkflowResponse =>
    send('POST', '/api/v1/contracts', body, options),
  createAmendment: (contractId: number, body: CreateAmendmentRequest, options: WriteOptions): WorkflowResponse =>
    send('POST', `/api/v1/contracts/${contractId}/amendments`, body, options),
  editDraft: (contractId: number, revisionId: number, body: EditDraftRequest, options: WriteOptions): WorkflowResponse =>
    send('PATCH', revisionPath(contractId, revisionId), body, options),
  submitReview: (contractId: number, revisionId: number, body: SubmitReviewRequest, options: WriteOptions): WorkflowResponse =>
    send('POST', `${revisionPath(contractId, revisionId)}/submit`, body, options),
  returnReview: (contractId: number, revisionId: number, body: ReturnReviewRequest, options: WriteOptions): WorkflowResponse =>
    send('POST', `${revisionPath(contractId, revisionId)}/return`, body, options),
  beginRework: (contractId: number, revisionId: number, body: BeginReworkRequest, options: WriteOptions): WorkflowResponse =>
    send('POST', `${revisionPath(contractId, revisionId)}/rework`, body, options),
};
