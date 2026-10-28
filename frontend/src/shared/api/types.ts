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
