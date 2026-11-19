const API_BASE = (import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api').replace(/\/$/, '');

export function saveTokens(tokens) {
  sessionStorage.setItem('cc_access', tokens.access);
  if (tokens.refresh) sessionStorage.setItem('cc_refresh', tokens.refresh);
}

export function clearTokens() {
  sessionStorage.removeItem('cc_access');
  sessionStorage.removeItem('cc_refresh');
}

export async function api(path, options = {}, retry = true) {
  const headers = new Headers(options.headers || {});
  const token = sessionStorage.getItem('cc_access');
  if (token) headers.set('Authorization', `Bearer ${token}`);
  if (!(options.body instanceof FormData) && options.body !== undefined) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  if (response.status === 401 && retry) {
    const refresh = sessionStorage.getItem('cc_refresh');
    if (refresh && path !== '/token/refresh/') {
      const refreshed = await fetch(`${API_BASE}/token/refresh/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh }),
      });
      if (refreshed.ok) {
        const tokens = await refreshed.json();
        saveTokens({ access: tokens.access, refresh });
        return api(path, options, false);
      }
    }
    clearTokens();
  }

  const payload = response.status === 204 ? null : await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = payload?.detail || Object.entries(payload || {}).map(([key, value]) =>
      `${key}: ${Array.isArray(value) ? value.join(', ') : value}`
    ).join(' · ') || 'Something went wrong.';
    throw new Error(detail);
  }
  return payload;
}

export const apiBaseUrl = API_BASE;


export async function downloadProtectedFile(path, filename) {
  const request = () => fetch(`${API_BASE}${path}`, {
    headers: { Authorization: `Bearer ${sessionStorage.getItem('cc_access') || ''}` },
  });
  let response = await request();
  if (response.status === 401) {
    const refresh = sessionStorage.getItem('cc_refresh');
    if (refresh) {
      const refreshed = await fetch(`${API_BASE}/token/refresh/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh }),
      });
      if (refreshed.ok) {
        const tokens = await refreshed.json();
        saveTokens({ access: tokens.access, refresh });
        response = await request();
      }
    }
  }
  if (!response.ok) throw new Error('You are not allowed to download this resume, or it is no longer available.');
  const blob = await response.blob();
  const objectUrl = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = objectUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(objectUrl);
}
