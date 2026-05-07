// src/api/finanzasApi.js
// Base URL for the Finanzas microservice
const BASE = import.meta.env.VITE_FINANZAS_URL || 'http://localhost:8000';

import { fetchWithCache } from '../utils/offlineCache';

function headers(username = 'admin') {
  return {
    'Content-Type': 'application/json',
    'X-User-Name': username,
  };
}

async function request(method, path, username = 'admin', body) {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: headers(username),
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  const ct = res.headers.get('content-type') || '';
  if (ct.includes('application/pdf')) return res.blob();
  return res.json();
}

// ── Health ───────────────────────────────────────────────────
export const getHealth = () => fetch(`${BASE}/health`).then(r => r.json());

// ── Users ────────────────────────────────────────────────────
export const getMe       = (username)          => request('GET', '/users/me', username);
export const getUser     = (username, target)  => request('GET', `/users/${target}`, username);
export const getUsers    = async (username)          => {
  const key = `finanzas:users:${username}`;
  return fetchWithCache(key, () => request('GET', '/users', username));
};

// ── Reports ──────────────────────────────────────────────────
export const generateReport  = (username)      => request('POST', '/reports/ingresos-totales', username);
export const getTracking     = async (username)      => {
  const key = `finanzas:tracking:${username}`;
  return fetchWithCache(key, () => request('GET', '/reports/tracking', username));
};
export const downloadReport  = (username, id)  => request('GET',  `/reports/tracking/${id}/pdf`, username);
export const deleteReport    = (username, id)  => request('DELETE', `/reports/tracking/${id}`, username);
export const getReportPdfDirect = ()           =>
  fetch(`${BASE}/reports/ingresos-totales/pdf`).then(r => {
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    return r.blob();
  });

// ── PDF download helper ──────────────────────────────────────
export function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a   = document.createElement('a');
  a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
}

// ── Role / permission helpers ────────────────────────────────
export const ROLES = {
  admin:      ['finanzas','compras','inventario','devoluciones','usuarios'],
  compras:    ['finanzas','compras'],
  inventario: ['finanzas','inventario'],
  auditor:    ['finanzas','devoluciones'],
  viewer:     ['finanzas'],
};

export function hasPermission(user, area) {
  return user?.permissions?.includes(area) ?? false;
}
