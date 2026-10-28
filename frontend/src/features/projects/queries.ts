import { useQuery } from '@tanstack/react-query';
import { api } from '../../shared/api/client';
import { sessionScope, useCurrentSession } from '../../shared/api/session';

export function useProjects(query: { q?: string; offset?: number } = {}) {
  const session = useCurrentSession();
  return useQuery({
    queryKey: [...sessionScope(session), 'projects', query],
    queryFn: ({ signal }) => api.projects({ ...query, limit: 20 }, signal),
    staleTime: 30 * 1000,
  });
}

export function useProject(id: number | undefined) {
  const session = useCurrentSession();
  return useQuery({
    queryKey: [...sessionScope(session), 'project', id],
    queryFn: ({ signal }) => api.project(id as number, signal),
    enabled: Number.isInteger(id) && (id as number) > 0,
    staleTime: 30 * 1000,
  });
}
