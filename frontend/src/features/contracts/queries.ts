import { useQuery } from '@tanstack/react-query';
import { api } from '../../shared/api/client';
import { sessionScope, useCurrentSession } from '../../shared/api/session';

const validId = (id: number | undefined) => Number.isSafeInteger(id) && (id as number) > 0;

export function parseRouteId(value: string | null | undefined) {
  const id = /^\d+$/.test(value ?? '') ? Number(value) : 0;
  return validId(id) ? id : undefined;
}

export function useContracts(query: { q?: string; offset?: number; projectId?: number } = {}) {
  const session = useCurrentSession();
  return useQuery({
    queryKey: [...sessionScope(session), 'contracts', query],
    queryFn: ({ signal }) => api.contracts({ ...query, limit: 20 }, signal),
    staleTime: 30 * 1000,
  });
}

export function useContract(id: number | undefined, asOf: string | undefined) {
  const session = useCurrentSession();
  return useQuery({
    queryKey: [...sessionScope(session), 'contract', id, asOf ?? 'today'],
    queryFn: ({ signal }) => api.contract(id as number, asOf, signal),
    enabled: validId(id),
    staleTime: 30 * 1000,
  });
}

export function useContractRevision(contractId: number | undefined, revisionId: number | undefined) {
  const session = useCurrentSession();
  return useQuery({
    queryKey: [...sessionScope(session), 'contract-revision', contractId, revisionId],
    queryFn: ({ signal }) => api.contractRevision(contractId as number, revisionId as number, signal),
    enabled: validId(contractId) && validId(revisionId),
    staleTime: 30 * 1000,
  });
}
