import { QueryClient } from '@tanstack/react-query';
import { afterEach, describe, expect, it } from 'vitest';
import { isSessionExpired, watchSessionExpiry } from './sessionNotice';

const user = { user: { id: 7, name: 'Người lập kế hoạch' } };
let unsubscribe = () => {};

function watchedClient() {
  const queryClient = new QueryClient();
  unsubscribe = watchSessionExpiry(queryClient.getQueryCache());
  return queryClient;
}

describe('session expiry notice (L02)', () => {
  afterEach(() => {
    // The flag is module state, as in the app; a new session resets it for the next test.
    const queryClient = watchedClient();
    queryClient.setQueryData(['session'], user);
    unsubscribe();
  });

  it('marks the session as expired when a signed-in session turns into no session', () => {
    const queryClient = watchedClient();
    queryClient.setQueryData(['session'], user);
    expect(isSessionExpired()).toBe(false);

    queryClient.setQueryData(['session'], null);
    expect(isSessionExpired()).toBe(true);

    queryClient.setQueryData(['session'], user);
    expect(isSessionExpired()).toBe(false);
  });

  it('does not report an expiry when the tab opens without a session', () => {
    const queryClient = watchedClient();
    queryClient.setQueryData(['session'], null);
    expect(isSessionExpired()).toBe(false);
  });

  it('does not report an expiry after logout clears the cache', () => {
    const queryClient = watchedClient();
    queryClient.setQueryData(['session'], user);
    queryClient.clear();
    queryClient.setQueryData(['session'], null);
    expect(isSessionExpired()).toBe(false);
  });

  it('ignores queries other than the session', () => {
    const queryClient = watchedClient();
    queryClient.setQueryData(['projects'], [{ id: 1 }]);
    queryClient.setQueryData(['projects'], null);
    expect(isSessionExpired()).toBe(false);
  });
});
