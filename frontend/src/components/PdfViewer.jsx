export function PdfViewer({ src }) {
  return (
    <section className="viewer-card">
      <div className="viewer-card__head">
        <div>
          <p className="section-label">Vista previa</p>
          <h2>PDF guardado</h2>
        </div>
      </div>

      <div className="viewer">
        {src ? <iframe title="Vista previa del PDF" src={src} loading="lazy" /> : <div className="empty-state">Selecciona un reporte para verlo.</div>}
      </div>
    </section>
  );
}
