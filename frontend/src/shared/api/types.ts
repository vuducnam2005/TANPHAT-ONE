import type { components, operations } from './openapi.generated';

export type NameRef = components['schemas']['NameRef'];
export type Project = components['schemas']['Project'];

export interface ApiMeta {
  request_id: string;
  pagination?: { limit: number; offset: number; has_more: boolean };
}

export interface ApiEnvelope<T> {
  data: T;
  meta: ApiMeta;
}

export type ApiErrorBody = components['schemas']['ErrorEnvelope'];

export type SessionBootstrap = operations['getCurrentSession']['responses'][200]['content']['application/json']['data'];

type Schemas = components['schemas'];
export type Money = Schemas['Money'];
export type ContractSummary = Schemas['ContractSummary'];
export type ContractDetail = Schemas['ContractDetail'];
export type ContractRevision = Schemas['Revision'];
export type RevisionDetail = Schemas['RevisionDetail'];
export type RevisionStatus = Schemas['RevisionStatus'];
export type ApprovalReference = Schemas['ApprovalReference'];
export type ContractDocument = Schemas['ContractDocument'];
export type ContractLine = Schemas['ContractLine'];
export type EffectiveWarning = Schemas['EffectiveSnapshot']['warnings'][number];
export type ContractPermissions = Schemas['ContractPermissions'];
export type WorkflowAction = Schemas['WorkflowAction'];
export type ContractSubmission = Schemas['ContractSubmission'];
export type ReturnIssue = Schemas['ReturnIssue'];
export type AmountInput = NonNullable<Schemas['AmountInput']>;
export type LineInput = Schemas['LineInput'];
export type CreateContractRequest = Schemas['CreateContractRequest'];
export type CreateAmendmentRequest = Schemas['CreateAmendmentRequest'];
export type EditDraftRequest = Schemas['EditDraftRequest'];
export type SubmitReviewRequest = Schemas['SubmitReviewRequest'];
export type ReturnReviewRequest = Schemas['ReturnReviewRequest'];
export type BeginReworkRequest = Schemas['BeginReworkRequest'];
export type WorkflowResult = Schemas['WorkflowResultData'];
