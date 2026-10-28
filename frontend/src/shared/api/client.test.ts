import { afterEach, describe, expect, it, vi } from 'vitest';
import { api, ApiError } from './client';

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
