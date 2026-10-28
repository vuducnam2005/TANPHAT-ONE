import { afterEach, describe, expect, it, vi } from 'vitest';
import { api, ApiError, LoginError } from './client';

afterEach(() => vi.unstubAllGlobals());

describe('business API transport', () => {
  it('sends only supported query parameters and cookie credentials', async () => {
    const response = { data: [], meta: { request_id: 'request', pagination: { limit: 20, offset: 20, has_more: false } } };
    const fetchMock = vi.fn().mockResolvedValue(Response.json(response));
    vi.stubGlobal('fetch', fetchMock);
    const controller = new AbortController();
    await expect(api.projects({ q: '  dự án / thử  ', limit: 20, offset: 20 }, controller.signal)).resolves.toEqual(response);
    const [url, options] = fetchMock.mock.calls[0];
    const parsed = new URL(url, 'http://test');
    expect(parsed.searchParams.get('q')).toBe('dự án / thử');
    expect([...parsed.searchParams.keys()]).toEqual(['q', 'limit', 'offset']);
    expect(options.credentials).toBe('include');
    controller.abort();
    expect(options.signal.aborted).toBe(true);
  });

  it('keeps status and server request ID without treating an auth error as data', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(Response.json({
      error: { code: 'unauthenticated', message: 'Sign in', details: null },
      meta: { request_id: 'trace-123' },
    }, { status: 401 })));
    await expect(api.session()).rejects.toMatchObject({ status: 401, code: 'unauthenticated', requestId: 'trace-123' });
  });

  it('builds contract list, detail and revision URLs from typed arguments only', async () => {
    const fetchMock = vi.fn().mockImplementation(() => Promise.resolve(Response.json({ data: [], meta: { request_id: 'r' } })));
    vi.stubGlobal('fetch', fetchMock);
    await api.contracts({ q: ' HD-01 ', limit: 20, offset: 40, projectId: 7 });
    await api.contract(12);
    await api.contract(12, '2026-11-01');
    await api.contractRevision(12, 34);
    const urls = fetchMock.mock.calls.map(([url]) => new URL(url, 'http://test'));
    expect([...urls[0].searchParams.entries()]).toEqual([['q', 'HD-01'], ['limit', '20'], ['offset', '40'], ['project_id', '7']]);
    expect(urls[0].pathname).toBe('/api/v1/contracts');
    expect(urls[1].pathname + urls[1].search).toBe('/api/v1/contracts/12');
    expect(urls[2].pathname + urls[2].search).toBe('/api/v1/contracts/12?as_of=2026-11-01');
    expect(urls[3].pathname + urls[3].search).toBe('/api/v1/contracts/12/revisions/34');
    expect(api.contractDocumentUrl(12, 56)).toBe('/api/v1/contracts/12/documents/56/content');
  });

  it('sends workflow writes as same-origin JSON with the CSRF token and idempotency key', async () => {
    const result = { data: { contract_id: 12, revision_id: 34, submission_id: 5, version: 3, review_state: 'in_review', replayed: false }, meta: { request_id: 'r' } };
    const fetchMock = vi.fn().mockImplementation(() => Promise.resolve(Response.json(result)));
    vi.stubGlobal('fetch', fetchMock);
    const options = { csrfToken: 'csrf-1', idempotencyKey: 'intent-0001' };
    await expect(api.submitReview(12, 34, { expected_version: 2, reviewer_id: 9 }, options)).resolves.toEqual(result);
    await api.editDraft(12, 34, { expected_version: 3, revision: { name: 'R1' } }, options);
    await api.createContract({ project_id: 7, code: 'HD-01', name: 'Draft', contract_type: 'owner', currency: 'VND' }, options);
    const calls = fetchMock.mock.calls.map(([url, init]) => [url, init.method, JSON.parse(init.body)]);
    expect(calls).toEqual([
      ['/api/v1/contracts/12/revisions/34/submit', 'POST', { expected_version: 2, reviewer_id: 9 }],
      ['/api/v1/contracts/12/revisions/34', 'PATCH', { expected_version: 3, revision: { name: 'R1' } }],
      ['/api/v1/contracts', 'POST', { project_id: 7, code: 'HD-01', name: 'Draft', contract_type: 'owner', currency: 'VND' }],
    ]);
    const [, init] = fetchMock.mock.calls[0];
    expect(init).toMatchObject({ credentials: 'same-origin', cache: 'no-store' });
    expect(init.headers).toMatchObject({ 'Content-Type': 'application/json', 'X-CSRF-Token': 'csrf-1', 'Idempotency-Key': 'intent-0001' });
  });

  it('keeps the error code and details of a rejected write', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(Response.json({
      error: { code: 'stale_version', message: 'Changed', details: { current_version: 4 } }, meta: { request_id: 'trace-9' },
    }, { status: 409 })));
    await expect(api.beginRework(1, 2, { expected_version: 3, reason: 'x' }, { csrfToken: 't', idempotencyKey: 'intent-0002' }))
      .rejects.toMatchObject({ status: 409, code: 'stale_version', details: { current_version: 4 }, requestId: 'trace-9' });
  });

  it('handles an HTML gateway failure without exposing the HTML', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('<html>internal proxy details</html>', { status: 502 })));
    await expect(api.projects()).rejects.toBeInstanceOf(ApiError);
    await expect(api.projects()).rejects.toMatchObject({ status: 502, message: 'Không thể đọc dữ liệu.' });
  });
});

describe('Odoo session authentication', () => {
  it('uses the same-origin session endpoint and preserves password whitespace', async () => {
    const fetchMock = vi.fn().mockResolvedValue(Response.json({ result: { uid: 7 } }));
    vi.stubGlobal('fetch', fetchMock);
    await expect(api.authenticate('  planner.dev  ', ' sample password ')).resolves.toEqual({ requiresVerification: false });
    const [url, options] = fetchMock.mock.calls[0];
    expect(url).toBe('/web/session/authenticate');
    expect(options).toMatchObject({ method: 'POST', credentials: 'same-origin', cache: 'no-store' });
    expect(JSON.parse(options.body)).toMatchObject({
      jsonrpc: '2.0', method: 'call', params: { login: 'planner.dev', password: ' sample password ' },
    });
  });

  it('treats HTTP 200 JSON-RPC credential errors as failed authentication', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(Response.json({
      error: { data: { name: 'odoo.exceptions.AccessDenied', debug: 'private server traceback' } },
    })));
    await expect(api.authenticate('planner.dev', 'invalid')).rejects.toMatchObject({ code: 'credentials' });
  });

  it('keeps MFA as an explicit verification step instead of granting access', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(Response.json({ result: { uid: null } })));
    await expect(api.authenticate('planner.dev', 'sample')).resolves.toEqual({ requiresVerification: true });
  });

  it('returns a useful rate-limit message', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('', { status: 429 })));
    await expect(api.authenticate('planner.dev', 'sample')).rejects.toMatchObject({ code: 'rate_limit' });
  });

  it('does not expose proxy HTML or internal errors', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response('<html>private gateway details</html>', { status: 502 })));
    await expect(api.authenticate('planner.dev', 'sample')).rejects.toMatchObject({ code: 'connection' });
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(Response.json({ error: { data: { name: 'InternalError', debug: 'private stack' } } })));
    await expect(api.authenticate('planner.dev', 'sample')).rejects.toMatchObject({ code: 'connection' });
  });

  it('rejects malformed success responses', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(Response.json({ result: {} })));
    await expect(api.authenticate('planner.dev', 'sample')).rejects.toBeInstanceOf(LoginError);
  });

  it('handles a lost connection without retaining network error details', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new TypeError('network details')));
    await expect(api.authenticate('planner.dev', 'sample')).rejects.toMatchObject({ code: 'connection' });
  });
});
