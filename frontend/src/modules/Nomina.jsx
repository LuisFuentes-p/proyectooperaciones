import React from 'react'

export default function Nomina({ role, permissions }){
  return (
    <section className="module">
      <div className="module-header">
        <h2>Nómina</h2>
        <div className="module-actions">
          <button>Calcular nómina</button>
        </div>
      </div>

      <div className="kpis">
        <div className="kpi">Empleados: <strong>42</strong></div>
      </div>

      <div className="placeholder">Gestión de empleados y pagos</div>
    </section>
  )
}
