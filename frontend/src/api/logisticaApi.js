// src/api/logisticaApi.js
// Base URL for the Logistica microservice
const BASE = import.meta.env.VITE_LOGISTICA_URL || 'http://localhost:8002';

import { fetchWithCache } from '../utils/offlineCache';

function headers(username = 'admin') {
  return {
    'Content-Type': 'application/json',
    'X-User-Name': username,
    user_name: username,
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

  if (res.status === 204) return null;
  return res.json();
}

// Health
export const getHealth = () => fetch(`${BASE}/health`).then((r) => r.json());

// Monitoring
export const getItemsBelowMinimum = async (username) => {
  const key = `logistica:itemsBelow:${username}`;
  return fetchWithCache(key, () => request('GET', '/monitor/items-below-minimum', username));
};
export const getStockoutItems = async (username) => {
  const key = `logistica:stockout:${username}`;
  return fetchWithCache(key, () => request('GET', '/monitor/stockout-items', username));
};
export const getStockStatusDashboard = async (username) => {
  const key = `logistica:stockStatus:${username}`;
  return fetchWithCache(key, () => request('GET', '/monitor/stock-status-dashboard', username));
};
export const checkAndAlert = (username) => request('POST', '/monitor/check-and-alert', username);

// Solicitudes
export const getPendingSolicitudes = (username) => request('GET', '/solicitudes/pending', username);
export const getInProgressSolicitudes = (username) => request('GET', '/solicitudes/in-progress', username);
export const getCompletedSolicitudes = (username, days = 7) => request('GET', `/solicitudes/completed?days=${days}`, username);

// Purchase orders
export const getPendingPurchaseOrders = (username) => request('GET', '/purchase-orders/pending', username);
export const getOverduePurchaseOrders = (username) => request('GET', '/purchase-orders/overdue', username);

// Deliveries
export const listDeliveries = (username, params = {}) => {
  const q = new URLSearchParams(
    Object.fromEntries(Object.entries(params).filter(([, v]) => v !== '' && v != null))
  ).toString();
  return request('GET', `/deliveries${q ? `?${q}` : ''}`, username);
};

export const createDelivery = (username, payload) => request('POST', '/deliveries', username, payload);
export const assignDelivery = (username, deliveryId, payload) => request('PATCH', `/deliveries/${deliveryId}/assign`, username, payload);
export const updateDeliveryStatus = (username, deliveryId, status) =>
  request('PATCH', `/deliveries/${deliveryId}/status`, username, { status });
export const getDelivery = (username, deliveryId) => request('GET', `/deliveries/${deliveryId}`, username);
