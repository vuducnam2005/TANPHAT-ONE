import { useQuery } from '@tanstack/react-query';
import { api, ApiError } from './client';

export function useSession() {
  return useQuery({
    queryKey: ['session'],
    queryFn: async ({ signal }) => {
      try { return await api.session(signal); }
      catch (error) {
        if (error instanceof ApiError && error.status === 401) return null;
        throw error;
      }
    },
    retry: false,
    staleTime: 60 * 1000,
    refetchOnWindowFocus: 'always',
  });
}
