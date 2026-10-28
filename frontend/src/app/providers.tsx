import { QueryCache, QueryClient, QueryClientProvider } from '@tanstack/react-query';
import type { PropsWithChildren } from 'react';
import { ApiError } from '../shared/api/client';

const queryClient = new QueryClient({
  queryCache: new QueryCache({
    onError: (error) => {
      if (error instanceof ApiError && error.status === 401) {
        void queryClient.cancelQueries();
        queryClient.removeQueries({ predicate: (query) => query.queryKey[0] !== 'session' });
        queryClient.setQueryData(['session'], null);
      }
    },
  }),
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: true,
      retry: (attempt, error) => attempt < 1 && !(error instanceof ApiError && error.status < 500),
    },
  },
});

export function AppProviders({ children }: PropsWithChildren) {
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}
