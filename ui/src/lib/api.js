const BASE = '/api';

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  health: () => request('/health'),
  specs: () => request('/specs'),
  parse: (body) => request('/parse', { method: 'POST', body: JSON.stringify(body) }),
  riskScore: (body) => request('/risk-score', { method: 'POST', body: JSON.stringify(body) }),
  generate: (body) => request('/generate', { method: 'POST', body: JSON.stringify(body) }),
};
