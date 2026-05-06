export function UsersArea({ users, loading, allowed }) {
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
          <p className="section-label">Usuarios</p>
          <h2>Tabla de usuarios y roles</h2>
        </div>
      </div>

      <div className="table-shell">
        <div className="table-head table-grid users-grid">
          <span>Usuario</span>
          <span>Nombre</span>
          <span>Rol</span>
          <span>Permisos</span>
        </div>

        <div className="table-body">
          {loading ? <div className="empty-state">Cargando usuarios...</div> : null}
          {!loading && users.length === 0 ? <div className="empty-state">No hay usuarios registrados.</div> : null}

          {users.map((user) => (
            <article className="table-row table-grid users-grid" key={user.id}>
              <div>
                <p className="row-title">{user.username}</p>
                <p className="row-subtitle">{user.active ? 'Activo' : 'Inactivo'}</p>
              </div>
              <div>
                <p className="row-title">{user.display_name}</p>
                <p className="row-subtitle">ID {user.id}</p>
              </div>
              <div>
                <p className="row-title">{user.role}</p>
                <p className="row-subtitle">rol</p>
              </div>
              <div className="chips">
                {(user.permissions ?? []).map((permission) => (
                  <span className="chip" key={`${user.id}-${permission}`}>
                    {permission}
                  </span>
                ))}
              </div>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
