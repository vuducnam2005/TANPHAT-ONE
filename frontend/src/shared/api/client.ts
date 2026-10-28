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

export const api = {
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
