// Simple offline cache helper using localStorage
export function isOnline() {
  return typeof navigator !== 'undefined' ? navigator.onLine : true;
}

function cacheKey(key) {
  return `offline:${key}`;
}

export function saveCache(key, data) {
  try {
    const payload = { ts: Date.now(), data };
    localStorage.setItem(cacheKey(key), JSON.stringify(payload));
  } catch (e) {
    // ignore storage errors
    console.warn('saveCache failed', e);
  }
}

export function loadCache(key, maxAgeMs = 1000 * 60 * 60 * 24) {
  try {
    const raw = localStorage.getItem(cacheKey(key));
    if (!raw) return null;
    const { ts, data } = JSON.parse(raw);
    if (maxAgeMs && Date.now() - ts > maxAgeMs) return data; // still return stale data to support offline
    return data;
  } catch (e) {
    return null;
  }
}

export function removeCache(key) {
  try { localStorage.removeItem(cacheKey(key)); } catch (e) {}
}

export async function fetchWithCache(key, fetcher, options = {}) {
  const { ttlMs = 1000 * 60 * 60 * 24 } = options;
  // If offline, return cached immediately (if any)
  if (!isOnline()) {
    const cached = loadCache(key, ttlMs);
    if (cached) return cached;
    throw new Error('Offline and no cache available');
  }

  try {
    const data = await fetcher();
    try { saveCache(key, data); } catch (e) {}
    return data;
  } catch (err) {
    const cached = loadCache(key, ttlMs);
    if (cached) return cached;
    throw err;
  }
}
