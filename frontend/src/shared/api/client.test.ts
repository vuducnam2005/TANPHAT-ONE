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
