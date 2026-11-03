import { MutationCache, QueryCache, QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { PropsWithChildren } from 'react';
import { ApiError } from '../shared/api/client';
import { watchSessionExpiry } from '../features/auth';

function handleUnauthorized(error: unknown, queryClient: QueryClient) {
  if (!(error instanceof ApiError) || error.status !== 401) return;
  void queryClient.cancelQueries();
  queryClient.removeQueries({ predicate: (query) => query.queryKey[0] !== 'session' });
  queryClient.setQueryData(['session'], null);
}

const queryClient: QueryClient = new QueryClient({
  queryCache: new QueryCache({
    onError: (error) => handleUnauthorized(error, queryClient),
  }),
  mutationCache: new MutationCache({
    // A write may be the first request to discover that the Odoo session expired.
    // Mutation defaults remain retry=false, so this only returns the user to login.
    onError: (error) => handleUnauthorized(error, queryClient),
  }),
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: true,
      retry: (attempt, error) => attempt < 1 && !(error instanceof ApiError && error.status < 500),
    },
  },
});
watchSessionExpiry(queryClient.getQueryCache());

export function AppProviders({ children }: PropsWithChildren) {
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}
