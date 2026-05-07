import React from 'react'

export default function Usuarios({ role, permissions }){
  const canEdit = permissions?.canEdit
  return (
    <section className="module">
      <div className="module-header">
        <h2>Usuarios</h2>
        <div className="module-actions">
          <button disabled={!canEdit}>Nuevo usuario</button>
        </div>
      </div>

      <table className="list">
        <thead><tr><th>Nombre</th><th>Rol</th><th>Estado</th><th>Acciones</th></tr></thead>
        <tbody>
          <tr><td>Admin Demo</td><td>Admin</td><td>Activo</td><td><button>Ver</button></td></tr>
        </tbody>
      </table>
    </section>
  )
}
