export function ModuleArea({ title, description, allowed }) {
  return (
    <section className="area-card">
      <div className="area-card__head">
        <div>
          <p className="section-label">{title}</p>
          <h2>{title}</h2>
        </div>
      </div>

      <div className={allowed ? 'notice' : 'notice notice--locked'}>
        {allowed
          ? `${title} esta habilitado para tu rol, pero el modulo aun esta en desarrollo.`
          : `${title} esta grisado porque tu rol no tiene acceso.`}
      </div>

      <p className="description">{description}</p>
    </section>
  );
}
