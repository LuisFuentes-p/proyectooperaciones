export function SummaryArea({ session, reports, onGenerateReport, generating, sessionLoading, accessCount }) {
  const latestReport = reports[0];

  return (
    <section className="area-card">
      <div className="area-card__head">
        <div>
          <p className="section-label">Reporte</p>
          <h2>Generar y revisar el PDF</h2>
        </div>
        <button type="button" onClick={onGenerateReport} disabled={generating || sessionLoading}>
          {generating ? 'Generando...' : 'Generar reporte'}
        </button>
      </div>

      <div className="metric-grid">
        <article className="metric-card">
          <span className="metric-card__label">Usuario</span>
          <strong>{session?.display_name ?? 'Cargando...'}</strong>
          <span className="metric-card__meta">{session?.role ?? '...'}</span>
        </article>
        <article className="metric-card">
          <span className="metric-card__label">Areas habilitadas</span>
          <strong>{accessCount}</strong>
          <span className="metric-card__meta">segun el rol activo</span>
        </article>
        <article className="metric-card">
          <span className="metric-card__label">Ultimo reporte</span>
          <strong>{latestReport ? latestReport.filename : 'Sin registros'}</strong>
          <span className="metric-card__meta">{latestReport ? new Date(latestReport.created_at).toLocaleString('es-ES') : 'Aun no se ha creado uno'}</span>
        </article>
      </div>

      <div className="notice">
        Los documentos se guardan como binario en PostgreSQL y se exponen para el tracking cuando el rol lo permite.
      </div>
    </section>
  );
}
