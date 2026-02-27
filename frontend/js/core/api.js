/**
 * API client with JWT injection and error handling.
 */
import { getToken, clearTokens } from './auth.js';

const BASE = '/api/v1';

async function request(method, path, body = null, query = null) {
  const url = new URL(path.startsWith('/') ? path : `${BASE}/${path}`, window.location.origin);
  if (query) {
    Object.entries(query).forEach(([k, v]) => {
      if (v !== null && v !== undefined && v !== '') url.searchParams.set(k, v);
    });
  }

  const headers = { 'Content-Type': 'application/json' };
  const token = getToken();
  if (token) headers['Authorization'] = `Bearer ${token}`;

  const opts = { method, headers };
  if (body && method !== 'GET') opts.body = JSON.stringify(body);

  const res = await fetch(url.toString(), opts);
  const urlStr = url.toString();
  const isLogin = urlStr.includes('/auth/login');

  if (res.status === 401 && !isLogin) {
    clearTokens();
    window.location.hash = '#/login';
    throw new Error('Session expired');
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    const msg = Array.isArray(err.detail) ? (err.detail[0]?.msg || err.detail[0]?.loc?.join(' ') || String(err.detail)) : (err.detail || `HTTP ${res.status}`);
    throw new Error(typeof msg === 'string' ? msg : JSON.stringify(msg));
  }

  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  get:    (path, query) => request('GET', path, null, query),
  post:   (path, body)  => request('POST', path, body),
  put:    (path, body)  => request('PUT', path, body),
  delete: (path)        => request('DELETE', path),
};
