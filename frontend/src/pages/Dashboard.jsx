import { AccessMatrix } from '../oop/AccessMatrix';

export default function Dashboard({ username }) {
  const role = AccessMatrix.getRole(username);
  const tabs = AccessMatrix.getTabs(role).filter((t) => t.enabled);

  return (
    <main className="dashboard">
      <header className="dashboard__head">
        <h1>Bienvenido, {username}</h1>
        <p>Selecciona un area para entrar</p>
      </header>

      <div className="cards-grid">
        {tabs.map((tab) => (
          <article className="card" key={tab.id}>
            <h3>{tab.label}</h3>
            <p>{tab.description}</p>
            <div>
              <a href={`#/area/${tab.id}`} className="button">
                Ir a {tab.label}
              </a>
            </div>
          </article>
        ))}
      </div>
    </main>
  );
}
