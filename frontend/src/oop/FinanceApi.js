export class FinanceApi {
  constructor(baseUrl) {
    this.baseUrl = baseUrl.replace(/\/$/, '');
  }

  buildUrl(path) {
    return `${this.baseUrl}${path}`;
  }

  buildHeaders(username, extraHeaders = {}) {
    return {
      'Content-Type': 'application/json',
      ...(username ? { 'X-User-Name': username } : {}),
      ...extraHeaders,
    };
  }

  async request(path, { method = 'GET', username, body } = {}) {
    const response = await fetch(this.buildUrl(path), {
      method,
      headers: this.buildHeaders(username),
      body: body ? JSON.stringify(body) : undefined,
    });

    if (!response.ok) {
      let message = 'La solicitud no se pudo completar';
      try {
        const errorPayload = await response.json();
        message = errorPayload.detail ?? message;
      } catch {
        message = await response.text();
      }

      throw new Error(message || 'La solicitud no se pudo completar');
    }

    if (response.status === 204) {
      return null;
    }

    const contentType = response.headers.get('content-type') ?? '';
    if (contentType.includes('application/json')) {
      return response.json();
    }

    return response.text();
  }

  getCurrentUser(username) {
    return this.request(`/users/${username}`);
  }

  listUsers(username) {
    return this.request('/users', { username });
  }

  listReports(username) {
    return this.request('/reports/tracking', { username });
  }

  createReport(username) {
    return this.request('/reports/ingresos-totales', { method: 'POST', username });
  }

  deleteReport(reportId, username) {
    return this.request(`/reports/tracking/${reportId}`, { method: 'DELETE', username });
  }

  getTrackedReportPdfUrl(reportId) {
    return this.buildUrl(`/reports/tracking/${reportId}/pdf`);
  }

  getPublicReportPdfUrl() {
    return this.buildUrl('/reports/ingresos-totales/pdf');
  }
}
