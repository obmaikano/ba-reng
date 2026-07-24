const BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function request<T = unknown>(path: string, options: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json', ...options.headers as Record<string, string> },
    ...options,
  });
  if (!res.ok) {
    const body = await res.text().catch(() => '');
    const detail = body ? (() => { try { return JSON.parse(body).detail; } catch { return body.slice(0, 200); } })() : res.statusText;
    throw new Error(detail || `HTTP ${res.status}`);
  }
  const text = await res.text();
  if (!text || !text.trim()) {
    throw new Error('Empty response from server');
  }
  return JSON.parse(text);
}

export function get<T = unknown>(path: string): Promise<T> {
  return request<T>(path);
}

export function post<T = unknown>(path: string, body: unknown): Promise<T> {
  return request<T>(path, { method: 'POST', body: JSON.stringify(body) });
}

export function put<T = unknown>(path: string, body: unknown): Promise<T> {
  return request<T>(path, { method: 'PUT', body: JSON.stringify(body) });
}

export function del(path: string): Promise<void> {
  return request<void>(path, { method: 'DELETE' });
}
