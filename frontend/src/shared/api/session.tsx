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

export function loginUrl() {
  const redirect = window.location.pathname.startsWith('/work/')
    ? window.location.pathname + window.location.search
    : '/work/';
  return `/web/login?${new URLSearchParams({ redirect })}`;
}
