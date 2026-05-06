import { useState } from 'react';

const defaultPdfUrl = import.meta.env.VITE_FINANZAS_PDF_URL ?? 'http://localhost:8000/reports/ingresos-totales/pdf';

export default function App() {
  const [pdfUrl] = useState(defaultPdfUrl);
  const [reloadKey, setReloadKey] = useState(0);

  return (
    <main className="shell">
      <section className="panel">
        <p className="eyebrow">Finanzas</p>
        <h1>Documento PDF de ingresos</h1>
        <p className="description">
          Vista simple para consumir el PDF generado por el microservicio de finanzas.
        </p>

        <div className="actions">
          <button type="button" onClick={() => setReloadKey((value) => value + 1)}>
            Recargar PDF
          </button>
          <a href={pdfUrl} target="_blank" rel="noreferrer">
            Abrir en nueva pestaña
          </a>
        </div>

        <div className="viewer">
          <iframe
            key={reloadKey}
            title="PDF de ingresos totales"
            src={pdfUrl}
            loading="lazy"
          />
        </div>
      </section>
    </main>
  );
}