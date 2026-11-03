import type { QueryCache } from '@tanstack/react-query';

// Why the login page replaced this tab's workspace (AUTH-002 L02). Kept only in
// memory: a reload forgets it, and nothing goes to browser storage, cookies or the URL.
let sessionExpired = false;

export function isSessionExpired() {
  return sessionExpired;
}

/**
 * Marks the session as expired when the session query goes from a signed-in user to
 * null, which only a 401 does: either a business query was rejected or /me was. A
 * first load without a session and a logout (which clears the cache) are not expiries.
 */
export function watchSessionExpiry(queryCache: QueryCache) {
  let signedIn = false;
  return queryCache.subscribe(({ type, query }) => {
    if (query.queryKey[0] !== 'session') return;
    if (type === 'removed') {
      signedIn = false;
      return;
    }
    if (type !== 'updated') return;
    const hasSession = Boolean(query.state.data);
    if (signedIn && !hasSession) sessionExpired = true;
    if (hasSession) sessionExpired = false;
    signedIn = hasSession;
  });
}
