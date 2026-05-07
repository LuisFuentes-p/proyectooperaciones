import React from 'react'

export default function Compras({ role, permissions }){
  const canEdit = permissions?.canEdit
  return (
    <section className="module">
      <div className="module-header">
        <h2>Compras</h2>
        <div className="module-actions">
          <button disabled={!canEdit}>Nueva orden</button>
          <button>Importar</button>
        </div>
      </div>

      <div className="kpis">
        <div className="kpi">Órdenes abiertas: <strong>5</strong></div>
      </div>

      <table className="list">
        <thead><tr><th>ID</th><th>Proveedor</th><th>Estado</th><th>Acciones</th></tr></thead>
        <tbody>
          <tr><td>OC-100</td><td>Proveedor demo</td><td>En tránsito</td><td><button>Ver</button></td></tr>
        </tbody>
      </table>
    </section>
  )
}
