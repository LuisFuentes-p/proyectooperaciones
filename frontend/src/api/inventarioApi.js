// src/api/inventarioApi.js
// Base URL for the Inventario microservice
const BASE = import.meta.env.VITE_INVENTARIO_URL || 'http://localhost:8001';

import { fetchWithCache } from '../utils/offlineCache';

function headers(username = 'admin') {
  return {
    'Content-Type': 'application/json',
    'user_name': username,
  };
}

async function request(method, path, username = 'admin', params) {
  let url = `${BASE}${path}`;
  if (params) {
    const q = new URLSearchParams(
      Object.fromEntries(Object.entries(params).filter(([, v]) => v !== '' && v != null))
    ).toString();
    if (q) url += '?' + q;
  }
  const res = await fetch(url, { method, headers: headers(username) });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  return res.json();
}

// ── Health ───────────────────────────────────────────────────
export const getHealth = () => fetch(`${BASE}/health`).then(r => r.json());

// ── Items ────────────────────────────────────────────────────
export const listItems  = async (username, params) => {
  const key = `inventario:listItems:${username}:${JSON.stringify(params||{})}`;
  return fetchWithCache(key, () => request('GET', '/items', username, params));
};

export const getItem    = async (username, id) => {
  const key = `inventario:getItem:${username}:${id}`;
  return fetchWithCache(key, () => request('GET', `/items/${id}`, username));
};

// Stock update uses query params, not body
export async function updateStock(username, itemId, quantityChange, reason, referenceId) {
  const params = { quantity_change: quantityChange, reason };
  if (referenceId) params.reference_id = referenceId;
  return request('POST', `/items/${itemId}/stock/update`, username, params);
}

// ── Solicitudes Logísticas ───────────────────────────────────
export const listSolicitudes  = async (username, params) => {
  const key = `inventario:solicitudes:${username}:${JSON.stringify(params||{})}`;
  return fetchWithCache(key, () => request('GET', '/solicitudes-logistica', username, params));
};
export const createSolicitud  = (username, params)     => request('POST',  '/solicitudes-logistica',            username, params);
export const approveSolicitud = (username, id)         => request('PATCH', `/solicitudes-logistica/${id}/approve`, username);
export const fulfillSolicitud = (username, id)         => request('PATCH', `/solicitudes-logistica/${id}/fulfill`, username);

// ── Stock Alerts ─────────────────────────────────────────────
export const listAlerts       = async (username, unackOnly)  => {
  const params = unackOnly ? { unacknowledged_only: true } : {};
  const key = `inventario:alerts:${username}:${JSON.stringify(params)}`;
  return fetchWithCache(key, () => request('GET', '/stock-alerts', username, params));
};
export const acknowledgeAlert = (username, alertId)    => request('POST', `/stock-alerts/${alertId}/acknowledge`, username);

// ── Suppliers ────────────────────────────────────────────────
export const listSuppliers    = async (username)             => {
  const key = `inventario:suppliers:${username}`;
  return fetchWithCache(key, () => request('GET', '/suppliers', username));
};