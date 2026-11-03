import { createContext, useContext } from 'react';
import type { SessionBootstrap } from './types';

export const SessionContext = createContext<SessionBootstrap | null>(null);

export function useCurrentSession() {
  const session = useContext(SessionContext);
  if (!session) throw new Error('Authenticated session is required.');
  return session;
}

export function sessionScope(session: SessionBootstrap) {
  return ['v1', session.user.id, session.company.id, session.companies.map((company) => company.id).sort((a, b) => a - b).join(',')];
}

function workspaceRedirect() {
  // Build from the browser's own location, never a query-supplied destination.
  return window.location.pathname.startsWith('/work/')
    ? window.location.pathname + window.location.search + window.location.hash
    : '/work/';
}

// Explicit native sign-in/passkey entry, before Odoo has authenticated a password.
export function loginUrl() {
  return `/web/login?${new URLSearchParams({ redirect: workspaceRedirect() })}`;
}

// Only after native authenticate returned uid: null and kept pre_uid in its session.
export function totpLoginUrl() {
  return `/web/login/totp?${new URLSearchParams({ redirect: workspaceRedirect() })}`;
}
