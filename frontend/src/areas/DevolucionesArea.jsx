import { useState, useEffect } from 'react';

export function DevolucionesArea({ allowed, username }) {
  // Placeholder - usaría import.meta.env.VITE_OPERACIONES_API_URL cuando se implemente

  useEffect(() => {
    if (allowed) {
      loadReturns();
    }
  }, [allowed, activeTab]);

  async function loadReturns() {
    setLoading(true);
    setError('');
    // Placeholder - en el futuro se conectará a la API de devoluciones
    setLoading(false);
  }

  if (!allowed) {
    return (
      <div className="locked-area">
        <div className="lock-icon">🔒</div>
        <h2>Acceso Restringido</h2>
        <p>Devoluciones está grisado porque tu rol no tiene acceso.</p>
        <p className="lock-description">Registro y seguimiento de devoluciones.</p>
      </div>
    );
  }

  return (
    <div className="module-area">
      <div className="area-header">
        <h2>↩ Devoluciones</h2>
        <p>Registro y seguimiento de devoluciones.</p>
      </div>

      <div className="sub-tabs">
        <button
          className={`sub-tab ${activeTab === 'devoluciones' ? 'active' : ''}`}
          onClick={() => setActiveTab('devoluciones')}
        >
          Devoluciones
        </button>
        <button
          className={`sub-tab ${activeTab === 'historial' ? 'active' : ''}`}
          onClick={() => setActiveTab('historial')}
        >
          Historial
        </button>
        <button
          className={`sub-tab ${activeTab === 'estadisticas' ? 'active' : ''}`}
          onClick={() => setActiveTab('estadisticas')}
        >
          Estadísticas
        </button>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {activeTab === 'devoluciones' && (
        <div className="tab-content">
          <div className="section-header">
            <h3>Solicitudes de Devolución</h3>
            <button className="btn btn-primary" onClick={loadReturns} disabled={loading}>
              {loading ? '⟳ Cargando...' : '↻ Refrescar'}
            </button>
          </div>

          {returns.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📦</div>
              <p>No hay devoluciones registradas</p>
              <p className="text-muted">Las devoluciones pendientes aparecerán aquí</p>
            </div>
          ) : (
            <div className="table-wrapper">
              <table className="returns-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Cliente</th>
                    <th>Item</th>
                    <th>Motivo</th>
                    <th>Estado</th>
                    <th>Fecha</th>
                    <th>Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {returns.map((ret) => (
                    <tr key={ret.id}>
                      <td>{ret.id}</td>
                      <td>{ret.customer}</td>
                      <td>{ret.item}</td>
                      <td>{ret.reason}</td>
                      <td>
                        <span className={`badge badge-${ret.status}`}>{ret.status}</span>
                      </td>
                      <td>{ret.date}</td>
                      <td>
                        <button className="btn-sm btn-info">Ver</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {activeTab === 'historial' && (
        <div className="tab-content">
          <h3>Historial de Devoluciones</h3>
          <div className="coming-soon">📜 Historial completo - Próximamente</div>
        </div>
      )}

      {activeTab === 'estadisticas' && (
        <div className="tab-content">
          <h3>Estadísticas</h3>
          <div className="stats-grid">
            <div className="stat-card">
              <h4>Devoluciones Totales</h4>
              <div className="stat-value">0</div>
            </div>
            <div className="stat-card">
              <h4>Pendientes</h4>
              <div className="stat-value">0</div>
            </div>
            <div className="stat-card">
              <h4>Completadas</h4>
              <div className="stat-value">0</div>
            </div>
            <div className="stat-card">
              <h4>Rechazadas</h4>
              <div className="stat-value">0</div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
