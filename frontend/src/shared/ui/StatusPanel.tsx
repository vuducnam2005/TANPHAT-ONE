import type { PropsWithChildren } from 'react';
import { ApiError } from '../api/client';

export function StatusPanel({ title, description, error, children }: PropsWithChildren<{ title: string; description: string; error?: Error }>) {
  return (
    <div className="tp-status-panel" role={error ? 'alert' : 'status'}>
      <h2>{title}</h2>
      <p>{description}</p>
      {error instanceof ApiError && error.requestId && <small>Mã tra cứu: {error.requestId}</small>}
      {children && <div className="tp-status-actions">{children}</div>}
    </div>
  );
}
