import React from 'react'

export default function Logistica({ role, permissions }){
  const canEdit = permissions?.canEdit
  return (
    <section className="module">
      <div className="module-header">
        <h2>Logística</h2>
        <div className="module-actions">
          <button disabled={!canEdit}>Nueva entrega</button>
        </div>
      </div>

      <div className="kpis">
        <div className="kpi">Entregas pendientes: <strong>3</strong></div>
      </div>

      <table className="list">
        <thead><tr><th>ID</th><th>Destino</th><th>Estado</th><th>Acciones</th></tr></thead>
        <tbody>
          <tr><td>DLV-200</td><td>Cliente demo</td><td>Pendiente</td><td><button>Ver</button></td></tr>
        </tbody>
      </table>
    </section>
  )
}
