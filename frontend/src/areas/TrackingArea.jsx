export function TrackingArea({ reports, loading, busyId, onView, onDelete, allowed }) {
  if (!allowed) {
    return (
      <section className="area-card">
        <div className="notice notice--locked">Esta area esta restringida para tu rol.</div>
      </section>
    );
  }

  return (
    <section className="area-card">
      <div className="area-card__head">
        <div>
          <p className="section-label">Tracking</p>
          <h2>Archivos guardados</h2>
        </div>
      </div>

      <div className="table-shell">
        <div className="table-head table-grid">
          <span>Reporte</span>
          <span>Archivo</span>
          <span>Fecha</span>
          <span>Acciones</span>
        </div>

        <div className="table-body">
          {loading ? <div className="empty-state">Cargando tracking...</div> : null}
          {!loading && reports.length === 0 ? <div className="empty-state">No hay archivos guardados todavia.</div> : null}

          {reports.map((report) => (
            <article className="table-row table-grid" key={report.id}>
              <div>
                <p className="row-title">{report.title}</p>
                <p className="row-subtitle">ID {report.id}</p>
              </div>
              <div>
                <p className="row-title">{report.filename}</p>
                <p className="row-subtitle">{Math.round((report.file_size ?? 0) / 1024)} KB</p>
              </div>
              <div>
                <p className="row-title">{new Date(report.created_at).toLocaleString('es-ES')}</p>
                <p className="row-subtitle">{report.report_key}</p>
              </div>
              <div className="row-actions">
                <button type="button" className="button button--ghost" onClick={() => onView(report)}>
                  VER
                </button>
                <button type="button" className="button button--danger" onClick={() => onDelete(report.id)} disabled={busyId === report.id}>
                  BORRAR
                </button>
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
