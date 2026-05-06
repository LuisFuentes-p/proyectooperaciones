import { AccessMatrix } from '../oop/AccessMatrix';

export default function LoginPage({ onLogin }) {
  const users = AccessMatrix.demoUsers;

  function handleSubmit(e) {
    e.preventDefault();
    const username = e.target.username.value;
    if (!username) return;
    localStorage.setItem('app_username', username);
    onLogin(username);
    window.location.hash = '#/';
  }

  return (
    <main className="center-card">
      <section className="login-card">
        <h1>Login</h1>
        <form onSubmit={handleSubmit}>
          <label>
            Usuario
            <select name="username" defaultValue={users[0].username}>
              {users.map((u) => (
                <option key={u.username} value={u.username}>
                  {u.displayName}
                </option>
              ))}
            </select>
          </label>
          <div className="actions">
            <button type="submit">Entrar</button>
          </div>
        </form>
      </section>
    </main>
  );
}
