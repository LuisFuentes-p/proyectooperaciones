import { AccessMatrix } from '../oop/AccessMatrix';
import { FinanceArea } from '../areas/FinanceArea';
import { InventarioArea } from '../areas/InventarioArea';
import { ComprasArea } from '../areas/ComprasArea';
import { VentasArea } from '../areas/VentasArea';
import { DevolucionesArea } from '../areas/DevolucionesArea';
import { UsersArea } from '../areas/UsersArea';

const areaMap = {
  finanzas: FinanceArea,
  inventario: InventarioArea,
  compras: ComprasArea,
  ventas: VentasArea,
  devoluciones: DevolucionesArea,
  usuarios: UsersArea,
};

export default function AreaPage({ areaId, username }) {
  const role = AccessMatrix.getRole(username);
  const allowed = AccessMatrix.hasPermission(role, areaId);
  const AreaComponent = areaMap[areaId];

  if (!AreaComponent) {
    return (
      <main className="center-card">
        <p>Area no encontrada.</p>
        <a href="#/">Volver</a>
      </main>
    );
  }

  return (
    <main className="area-page">
      <div className="area-page__nav">
        <a href="#/">← Volver al tablero</a>
      </div>

      {!allowed ? (
        <section className="area-card">
          <div className="notice notice--locked">Esta area esta restringida para tu rol.</div>
        </section>
      ) : (
        <AreaComponent allowed={allowed} username={username} />
      )}
    </main>
  );
}
