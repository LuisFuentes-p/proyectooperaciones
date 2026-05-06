export function UserSwitcher({ users, selectedUsername, onChange, session }) {
  return (
    <div className="user-switcher">
      <label className="user-switcher__field">
        <span className="user-switcher__label">Usuario activo</span>
        <select value={selectedUsername} onChange={(event) => onChange(event.target.value)}>
          {users.map((user) => (
            <option key={user.username} value={user.username}>
              {user.displayName}
            </option>
          ))}
        </select>
      </label>

      <div className="user-switcher__meta">
        <span className="pill">{session?.username ?? selectedUsername}</span>
        <span className="pill pill--soft">{session?.role ?? 'cargando'}</span>
      </div>
    </div>
  );
}
