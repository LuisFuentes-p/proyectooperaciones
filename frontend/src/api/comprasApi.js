// src/api/comprasApi.js
// Base URL for the Compras microservice
import { fetchWithCache } from '../utils/offlineCache';

const BASE = import.meta.env.VITE_COMPRAS_URL || 'http://localhost:8003';
const HEADERS = {
  'Content-Type': 'application/json',
  'user_name': 'admin',
};

async function request(method, path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: HEADERS,
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `HTTP ${res.status}`);
  }
  // PDF endpoints return binary
  const ct = res.headers.get('content-type') || '';
  if (ct.includes('application/pdf')) return res.blob();
  return res.json();
}

// ── Suppliers ────────────────────────────────────────────────
export const getSuppliers  = async ()           => {
  const key = `compras:suppliers`;
  return fetchWithCache(key, () => request('GET', '/suppliers'));
};
export const createSupplier = (data)      => request('POST', '/suppliers', data);

// ── Customers ────────────────────────────────────────────────
export const getCustomers  = async ()           => {
  const key = `compras:customers`;
  return fetchWithCache(key, () => request('GET', '/customers'));
};
export const createCustomer = (data)      => request('POST', '/customers', data);

// ── Items ────────────────────────────────────────────────────
export const getItems      = async ()           => {
  const key = `compras:items`;
  return fetchWithCache(key, () => request('GET', '/items'));
};
export const getItem       = async (id)         => {
  const key = `compras:item:${id}`;
  return fetchWithCache(key, () => request('GET', `/items/${id}`));
};
export const createItem    = (data)       => request('POST', '/items', data);

// ── Purchase Orders ──────────────────────────────────────────
export const getPurchaseOrders = async ()       => {
  const key = `compras:purchaseOrders`;
  return fetchWithCache(key, () => request('GET', '/purchase-orders'));
};
export const getPurchaseOrder  = (id)     => request('GET',  `/purchase-orders/${id}`);
export const createPurchaseOrder = (data) => request('POST', '/purchase-orders', data);
export const updatePOStatus = (id, status)=> request('PATCH', `/purchase-orders/${id}/status?new_status=${status}`);
export const getPOPdf       = (id)        => request('GET',  `/purchase-orders/${id}/pdf`);

// ── Sales Orders ─────────────────────────────────────────────
export const getSalesOrders = async ()          => {
  const key = `compras:salesOrders`;
  return fetchWithCache(key, () => request('GET', '/sales-orders'));
};
export const getSalesOrder  = (id)        => request('GET',  `/sales-orders/${id}`);
export const createSalesOrder = (data)    => request('POST', '/sales-orders', data);
export const updateSOStatus = (id, status)=> request('PATCH', `/sales-orders/${id}/status?new_status=${status}`);
export const getInvoicePdf  = (id)        => request('GET',  `/sales-orders/${id}/invoice`);

// ── Payments ─────────────────────────────────────────────────
export const payCustomer  = (data)        => request('POST', '/payments/customer', data);
export const paySupplier  = (data)        => request('POST', '/payments/supplier', data);

// ── History & Stats ──────────────────────────────────────────
export const getHistory = async (filters = {}) => {
  const q = new URLSearchParams(filters).toString();
  const key = `compras:history:${q}`;
  return fetchWithCache(key, () => request('GET', `/transactions/history${q ? '?' + q : ''}`));
};
export const getStats = async ()               => {
  const key = `compras:stats`;
  return fetchWithCache(key, () => request('GET',  '/stats/commercial-summary'));
};

// ── PDF download helper ──────────────────────────────────────
export function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a   = document.createElement('a');
  a.href = url; a.download = filename; a.click();
  URL.revokeObjectURL(url);
}
