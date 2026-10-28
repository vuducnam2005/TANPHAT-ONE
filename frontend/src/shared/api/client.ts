import type { ApiEnvelope, ApiErrorBody, Project, SessionBootstrap } from './types';

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
};
