// Thin fetch wrapper. Every backend failure arrives as {"error": {code, message, details}}.

export interface FieldError { field: string; message: string }

export class ApiError extends Error {
  constructor(public status: number, public code: string, message: string, public details: unknown = null) {
    super(message);
  }
}

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  let res: Response;
  try {
    res = await fetch(path, {
      method,
      headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new ApiError(0, 'network', 'Cannot reach the server. Is the Mini-Courier backend still running?');
  }
  const text = await res.text();
  let data: unknown = null;
  try { data = text ? JSON.parse(text) : null; } catch { /* non-JSON response */ }
  if (!res.ok) {
    const err = (data as { error?: { code: string; message: string; details?: unknown } } | null)?.error;
    throw new ApiError(res.status, err?.code ?? 'http_error', err?.message ?? `Request failed (${res.status})`, err?.details ?? null);
  }
  return data as T;
}

export const api = {
  get: <T>(path: string) => request<T>('GET', path),
  post: <T>(path: string, body: unknown = {}) => request<T>('POST', path, body),
  put: <T>(path: string, body: unknown) => request<T>('PUT', path, body),
  del: <T>(path: string, body?: unknown) => request<T>('DELETE', path, body),
};

export const errorMessage = (e: unknown): string => (e instanceof Error ? e.message : 'Something went wrong');

/** Field-level messages from a 422 response, keyed by field name. */
export function fieldErrors(e: unknown): Record<string, string> {
  const out: Record<string, string> = {};
  if (e instanceof ApiError && Array.isArray(e.details)) {
    for (const d of e.details as FieldError[]) if (d?.field && !(d.field in out)) out[d.field] = d.message;
  }
  return out;
}
