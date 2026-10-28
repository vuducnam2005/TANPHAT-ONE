import { useRef } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { api, ApiError } from '../../shared/api/client';
import type { WriteOptions } from '../../shared/api/client';
import { sessionScope, useCurrentSession } from '../../shared/api/session';
import type { ApiEnvelope, WorkflowResult } from '../../shared/api/types';
import { newIdempotencyKey } from './workflow';

type WorkflowCall<TBody> = (body: TBody, options: WriteOptions) => Promise<ApiEnvelope<WorkflowResult>>;

/**
 * Run one contract workflow action. The Idempotency-Key belongs to the intent:
 * retrying the same body after a network or server error reuses it, so the
 * server applies the action at most once; any changed body gets a new key.
 */
export function useWorkflowAction<TBody extends object>(call: WorkflowCall<TBody>) {
  const session = useCurrentSession();
  const queryClient = useQueryClient();
  const intent = useRef<{ body: string; key: string } | null>(null);
  return useMutation({
    mutationFn: (body: TBody) => {
      const serialized = JSON.stringify(body);
      if (intent.current?.body !== serialized) intent.current = { body: serialized, key: newIdempotencyKey() };
      return call(body, { csrfToken: session.csrf_token, idempotencyKey: intent.current.key });
    },
    onSuccess: async () => {
      intent.current = null;
      const scope = sessionScope(session);
      await Promise.all(['contracts', 'contract', 'contract-revision', 'contract-reviewers'].map((key) =>
        queryClient.invalidateQueries({ queryKey: [...scope, key] })));
    },
    onError: (error) => {
      if (!(error instanceof ApiError) || error.status >= 500) return;
      // A rejected request changed nothing on the server, so the next attempt is a new intent.
      intent.current = null;
      if (error.code === 'csrf_invalid') void queryClient.invalidateQueries({ queryKey: ['session'] });
    },
  });
}

export function useContractReviewers(contractId: number, enabled: boolean) {
  const session = useCurrentSession();
  return useQuery({
    queryKey: [...sessionScope(session), 'contract-reviewers', contractId],
    queryFn: ({ signal }) => api.contractReviewers(contractId, signal),
    enabled,
    staleTime: 30 * 1000,
  });
}
