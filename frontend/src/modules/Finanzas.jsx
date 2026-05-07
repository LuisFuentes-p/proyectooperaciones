import React from 'react'

export default function Finanzas({ role, permissions }){
  return (
    <section className="module">
      <div className="module-header">
        <h2>Finanzas</h2>
        <div className="module-actions">
          <button>Ver reportes</button>
        </div>
      </div>

      <div className="kpis">
        <div className="kpi">Ingresos: <strong>$12.345</strong></div>
        <div className="kpi">Egresos: <strong>$8.000</strong></div>
      </div>

      <div className="placeholder">Panel financiero y reportes</div>
    </section>
  )
}
