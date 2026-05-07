import React, { useCallback, useEffect, useMemo, useState } from 'react';
import * as api from '../api/logisticaApi';

const C = {
  bg: '#0b1220',
  surface: '#101a2e',
  card: '#17223a',
  border: '#243456',
  accent: '#38bdf8',
  accentLo: '#0d3042',
  green: '#22c55e',
  greenLo: '#113222',
  red: '#f43f5e',
  redLo: '#3a1120',
  yellow: '#f59e0b',
  yellowLo: '#39280d',
  text: '#e7edf7',
  muted: '#7f8da8',
};

const s = {
  page: {
    background: C.bg,
    minHeight: '100vh',
    color: C.text,
    fontFamily: "'IBM Plex Sans', 'Segoe UI', sans-serif",
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    background: C.surface,
    borderBottom: `1px solid ${C.border}`,
    padding: '18px 28px',
  },
  title: { margin: 0, fontSize: 22, fontWeight: 700 },
  subtitle: { fontSize: 12, color: C.muted, marginTop: 4 },
  tabs: {
    display: 'flex',
    gap: 4,
    padding: '10px 28px',
    background: C.bg,
    borderBottom: `1px solid ${C.border}`,
    flexWrap: 'wrap',
  },
  tab: (active) => ({
    background: active ? C.accent : 'transparent',
    color: active ? '#00141d' : C.muted,
    border: 'none',
    borderRadius: 7,
    fontWeight: 700,
    fontSize: 12,
    padding: '7px 13px',
    cursor: 'pointer',
  }),
  body: { padding: '22px 28px' },
  kpiRow: { display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 16 },
  kpi: {
    background: C.card,
    border: `1px solid ${C.border}`,
    borderRadius: 10,
    padding: '14px 16px',
    minWidth: 160,
    flex: '1 1 160px',
  },
  kpiLabel: {
    color: C.muted,
    fontSize: 10,
    textTransform: 'uppercase',
    letterSpacing: 0.8,
    marginBottom: 5,
  },
  kpiValue: { fontSize: 24, fontWeight: 700, color: C.accent },
  card: {
    background: C.card,
    border: `1px solid ${C.border}`,
    borderRadius: 10,
    padding: 16,
    marginBottom: 14,
  },
  cardHeader: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
    gap: 8,
    flexWrap: 'wrap',
  },
  cardTitle: { margin: 0, fontSize: 14, fontWeight: 700 },
  table: { width: '100%', borderCollapse: 'collapse', fontSize: 13 },
  th: {
    borderBottom: `1px solid ${C.border}`,
    textAlign: 'left',
    color: C.muted,
    fontSize: 11,
    textTransform: 'uppercase',
    padding: '8px 10px',
  },
  td: { borderBottom: `1px solid ${C.border}`, padding: '10px' },
  btn: (variant = 'primary') => ({
    border: 'none',
    borderRadius: 7,
    padding: '7px 12px',
    fontSize: 12,
    fontWeight: 700,
    cursor: 'pointer',
    background:
      variant === 'primary'
        ? C.accent
        : variant === 'danger'
          ? C.red
          : variant === 'success'
            ? C.green
            : variant === 'warning'
              ? C.yellow
              : variant === 'ghost'
                ? 'transparent'
                : C.border,
    color: variant === 'ghost' ? C.muted : variant === 'warning' ? '#18120a' : '#fff',
  }),
  input: {
    width: '100%',
    background: C.surface,
    border: `1px solid ${C.border}`,
    borderRadius: 7,
    color: C.text,
    padding: '7px 10px',
    fontSize: 12,
    boxSizing: 'border-box',
  },
  select: {
    width: '100%',
    background: C.surface,
    border: `1px solid ${C.border}`,
    borderRadius: 7,
    color: C.text,
    padding: '7px 10px',
    fontSize: 12,
    boxSizing: 'border-box',
  },
  formGrid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 },
  formActions: { marginTop: 14, display: 'flex', justifyContent: 'flex-end', gap: 8 },
  badge: (kind) => ({
    display: 'inline-block',
    borderRadius: 999,
    fontSize: 10,
    fontWeight: 700,
    letterSpacing: 0.4,
    textTransform: 'uppercase',
    padding: '3px 8px',
    background:
      kind === 'green'
        ? C.greenLo
        : kind === 'red'
          ? C.redLo
          : kind === 'yellow'
            ? C.yellowLo
            : C.accentLo,
    color: kind === 'green' ? C.green : kind === 'red' ? C.red : kind === 'yellow' ? C.yellow : C.accent,
  }),
  empty: { textAlign: 'center', color: C.muted, fontSize: 12, padding: '26px 0' },
  msg: (type) => ({
    borderRadius: 8,
    border: `1px solid ${type === 'error' ? C.border : C.green + '44'}`,
    background: type === 'error' ? C.surface : C.greenLo,
    color: type === 'error' ? C.muted : C.green,
    fontSize: 12,
    padding: '8px 10px',
    marginBottom: 12,
    opacity: type === 'error' ? 0.72 : 1,
  }),
};

function Field({ label, children }) {
  return (
    <div>
      <label style={{ fontSize: 11, color: C.muted, display: 'block', marginBottom: 4 }}>{label}</label>
      {children}
    </div>
  );
}

function HealthBadge({ health }) {
  if (!health) return <span style={s.badge('yellow')}>Desconocido</span>;
  return <span style={s.badge(health.status === 'ok' ? 'green' : 'red')}>{health.status}</span>;
}

function DeliveryStatusBadge({ status }) {
  if (status === 'delivered') return <span style={s.badge('green')}>delivered</span>;
  if (status === 'in_transit') return <span style={s.badge('yellow')}>in_transit</span>;
  return <span style={s.badge('blue')}>pending</span>;
}

function TabDashboard({ username }) {
  const [health, setHealth] = useState(null);
  const [summary, setSummary] = useState(null);
  const [pendingReq, setPendingReq] = useState([]);
  const [inProgressReq, setInProgressReq] = useState([]);
  const [pendingOrders, setPendingOrders] = useState([]);
  const [deliveries, setDeliveries] = useState([]);

  const load = useCallback(async () => {
    const [h, s, p, ip, po, d] = await Promise.all([
      api.getHealth(),
      api.getStockStatusDashboard(username),
      api.getPendingSolicitudes(username),
      api.getInProgressSolicitudes(username),
      api.getPendingPurchaseOrders(username),
      api.listDeliveries(username, { limit: 100 }),
    ]);
    setHealth(h);
    setSummary(s);
    setPendingReq(Array.isArray(p) ? p : []);
    setInProgressReq(Array.isArray(ip) ? ip : []);
    setPendingOrders(Array.isArray(po) ? po : []);
    setDeliveries(Array.isArray(d) ? d : []);
  }, [username]);

  useEffect(() => {
    load().catch(() => {
      setHealth({ status: 'offline' });
      setSummary({ total_items: 0, stockout_count: 0, below_minimum_count: 0, critical_items: 0, total_inventory_value: 0 });
      setPendingReq([]);
      setInProgressReq([]);
      setPendingOrders([]);
      setDeliveries([]);
    });
  }, [load]);

  const inTransitCount = useMemo(
    () => deliveries.filter((d) => d.status === 'in_transit').length,
    [deliveries]
  );

  return (
    <div>
      <div style={s.kpiRow}>
        <div style={s.kpi}>
          <div style={s.kpiLabel}>Servicio</div>
          <div style={{ ...s.kpiValue, fontSize: 16 }}><HealthBadge health={health} /></div>
        </div>
        <div style={s.kpi}>
          <div style={s.kpiLabel}>Solicitudes pendientes</div>
          <div style={s.kpiValue}>{pendingReq.length}</div>
        </div>
        <div style={s.kpi}>
          <div style={s.kpiLabel}>Solicitudes en progreso</div>
          <div style={s.kpiValue}>{inProgressReq.length}</div>
        </div>
        <div style={s.kpi}>
          <div style={s.kpiLabel}>Entregas en tránsito</div>
          <div style={s.kpiValue}>{inTransitCount}</div>
        </div>
      </div>

      <div style={s.kpiRow}>
        <div style={s.kpi}>
          <div style={s.kpiLabel}>Items totales</div>
          <div style={s.kpiValue}>{summary?.total_items ?? 0}</div>
        </div>
        <div style={s.kpi}>
          <div style={s.kpiLabel}>Stockout</div>
          <div style={{ ...s.kpiValue, color: C.red }}>{summary?.stockout_count ?? 0}</div>
        </div>
        <div style={s.kpi}>
          <div style={s.kpiLabel}>Bajo mínimo</div>
          <div style={{ ...s.kpiValue, color: C.yellow }}>{summary?.below_minimum_count ?? 0}</div>
        </div>
        <div style={s.kpi}>
          <div style={s.kpiLabel}>Órdenes activas</div>
          <div style={{ ...s.kpiValue, color: C.green }}>{pendingOrders.length}</div>
        </div>
      </div>
    </div>
  );
}

function TabMonitoreo({ username }) {
  const [below, setBelow] = useState([]);
  const [stockout, setStockout] = useState([]);
  const [msg, setMsg] = useState(null);

  const load = useCallback(async () => {
    const [b, s] = await Promise.all([api.getItemsBelowMinimum(username), api.getStockoutItems(username)]);
    setBelow(Array.isArray(b) ? b : []);
    setStockout(Array.isArray(s) ? s : []);
  }, [username]);

  useEffect(() => {
    load().catch(() => {
      setBelow([]);
      setStockout([]);
    });
  }, [load]);

  async function handleCheckAlerts() {
    try {
      const res = await api.checkAndAlert(username);
      setMsg({ type: 'success', text: `${res.message}. Alertas nuevas: ${res.alerts_created}` });
      load();
    } catch (err) {
      setMsg({ type: 'error', text: err.message });
    }
  }

  return (
    <div>
      {msg && msg.type !== 'error' && <div style={s.msg(msg.type)}>{msg.text}</div>}
      <div style={s.card}>
        <div style={s.cardHeader}>
          <h3 style={s.cardTitle}>Productos bajo mínimo</h3>
          <button style={s.btn()} onClick={handleCheckAlerts}>Ejecutar revisión de alertas</button>
        </div>
        <table style={s.table}>
          <thead>
            <tr>
              <th style={s.th}>SKU</th>
              <th style={s.th}>Producto</th>
              <th style={s.th}>Actual</th>
              <th style={s.th}>Mínimo</th>
              <th style={s.th}>Faltante</th>
              <th style={s.th}>Proveedor</th>
            </tr>
          </thead>
          <tbody>
            {below.length === 0 ? (
              <tr><td colSpan={6} style={{ ...s.td, ...s.empty }}>Sin productos bajo mínimo</td></tr>
            ) : below.map((it) => (
              <tr key={it.id}>
                <td style={s.td}>{it.sku}</td>
                <td style={s.td}>{it.name}</td>
                <td style={{ ...s.td, color: C.red, fontWeight: 700 }}>{it.current_quantity}</td>
                <td style={s.td}>{it.minimum_threshold}</td>
                <td style={s.td}>{it.shortage}</td>
                <td style={s.td}>{it.supplier_name || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div style={s.card}>
        <div style={s.cardHeader}>
          <h3 style={s.cardTitle}>Productos agotados (stockout)</h3>
        </div>
        <table style={s.table}>
          <thead>
            <tr>
              <th style={s.th}>SKU</th>
              <th style={s.th}>Producto</th>
              <th style={s.th}>Reorden sugerido</th>
              <th style={s.th}>Proveedor</th>
              <th style={s.th}>Urgencia</th>
            </tr>
          </thead>
          <tbody>
            {stockout.length === 0 ? (
              <tr><td colSpan={5} style={{ ...s.td, ...s.empty }}>Sin stockouts activos</td></tr>
            ) : stockout.map((it) => (
              <tr key={it.id}>
                <td style={s.td}>{it.sku}</td>
                <td style={s.td}>{it.name}</td>
                <td style={s.td}>{it.reorder_quantity}</td>
                <td style={s.td}>{it.supplier_name || '—'}</td>
                <td style={s.td}><span style={s.badge('red')}>{it.urgency || 'critical'}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function TabSolicitudes({ username }) {
  const [days, setDays] = useState(7);
  const [pending, setPending] = useState([]);
  const [inProgress, setInProgress] = useState([]);
  const [completed, setCompleted] = useState([]);

  const load = useCallback(async () => {
    const [p, ip, c] = await Promise.all([
      api.getPendingSolicitudes(username),
      api.getInProgressSolicitudes(username),
      api.getCompletedSolicitudes(username, days),
    ]);
    setPending(Array.isArray(p) ? p : []);
    setInProgress(Array.isArray(ip) ? ip : []);
    setCompleted(Array.isArray(c) ? c : []);
  }, [username, days]);

  useEffect(() => {
    load().catch(() => {
      setPending([]);
      setInProgress([]);
      setCompleted([]);
    });
  }, [load]);

  return (
    <div>
      <div style={s.card}>
        <div style={s.cardHeader}>
          <h3 style={s.cardTitle}>Solicitudes pendientes</h3>
          <button style={s.btn('secondary')} onClick={load}>Actualizar</button>
        </div>
        <table style={s.table}>
          <thead><tr>
            <th style={s.th}>#</th><th style={s.th}>Producto</th><th style={s.th}>Cant.</th><th style={s.th}>Razón</th><th style={s.th}>Prioridad</th><th style={s.th}>Proveedor</th>
          </tr></thead>
          <tbody>
            {pending.length === 0 ? (
              <tr><td colSpan={6} style={{ ...s.td, ...s.empty }}>Sin pendientes</td></tr>
            ) : pending.map((r) => (
              <tr key={r.id}>
                <td style={s.td}>SOL-{r.id}</td>
                <td style={s.td}>{r.item_name}</td>
                <td style={s.td}>{r.requested_quantity}</td>
                <td style={s.td}>{r.reason}</td>
                <td style={s.td}><span style={s.badge(r.priority === 'high' ? 'red' : 'yellow')}>{r.priority}</span></td>
                <td style={s.td}>{r.supplier_name || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div style={s.card}>
        <div style={s.cardHeader}><h3 style={s.cardTitle}>Solicitudes en progreso</h3></div>
        <table style={s.table}>
          <thead><tr>
            <th style={s.th}>#</th><th style={s.th}>Producto</th><th style={s.th}>Aprobado por</th><th style={s.th}>Días esperando</th>
          </tr></thead>
          <tbody>
            {inProgress.length === 0 ? (
              <tr><td colSpan={4} style={{ ...s.td, ...s.empty }}>Sin solicitudes aprobadas</td></tr>
            ) : inProgress.map((r) => (
              <tr key={r.id}>
                <td style={s.td}>SOL-{r.id}</td>
                <td style={s.td}>{r.item_name}</td>
                <td style={s.td}>{r.approved_by || '—'}</td>
                <td style={s.td}>{r.days_waiting}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div style={s.card}>
        <div style={s.cardHeader}>
          <h3 style={s.cardTitle}>Solicitudes completadas</h3>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ fontSize: 11, color: C.muted }}>Últimos días:</span>
            <input
              style={{ ...s.input, width: 74 }}
              type="number"
              min="1"
              max="365"
              value={days}
              onChange={(e) => setDays(Number(e.target.value) || 7)}
            />
          </div>
        </div>
        <table style={s.table}>
          <thead><tr><th style={s.th}>#</th><th style={s.th}>Producto</th><th style={s.th}>Cant.</th><th style={s.th}>Fecha</th></tr></thead>
          <tbody>
            {completed.length === 0 ? (
              <tr><td colSpan={4} style={{ ...s.td, ...s.empty }}>Sin completadas</td></tr>
            ) : completed.map((r) => (
              <tr key={r.id}>
                <td style={s.td}>SOL-{r.id}</td>
                <td style={s.td}>{r.item_name}</td>
                <td style={s.td}>{r.requested_quantity}</td>
                <td style={s.td}>{r.fulfilled_at ? new Date(r.fulfilled_at).toLocaleString('es-MX') : '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function TabOrdenes({ username }) {
  const [pendingOrders, setPendingOrders] = useState([]);
  const [overdueOrders, setOverdueOrders] = useState([]);

  const load = useCallback(async () => {
    const [p, o] = await Promise.all([api.getPendingPurchaseOrders(username), api.getOverduePurchaseOrders(username)]);
    setPendingOrders(Array.isArray(p) ? p : []);
    setOverdueOrders(Array.isArray(o) ? o : []);
  }, [username]);

  useEffect(() => {
    load().catch(() => {
      setPendingOrders([]);
      setOverdueOrders([]);
    });
  }, [load]);

  return (
    <div>
      <div style={s.card}>
        <div style={s.cardHeader}><h3 style={s.cardTitle}>Órdenes de compra activas</h3></div>
        <table style={s.table}>
          <thead><tr><th style={s.th}>#OC</th><th style={s.th}>Producto</th><th style={s.th}>Proveedor</th><th style={s.th}>Estado</th><th style={s.th}>Entrega estimada</th></tr></thead>
          <tbody>
            {pendingOrders.length === 0 ? (
              <tr><td colSpan={5} style={{ ...s.td, ...s.empty }}>Sin órdenes activas</td></tr>
            ) : pendingOrders.map((o) => (
              <tr key={o.id}>
                <td style={s.td}>OC-{o.id}</td>
                <td style={s.td}>{o.item_name}</td>
                <td style={s.td}>{o.supplier_name}</td>
                <td style={s.td}><span style={s.badge(o.status === 'shipped' ? 'yellow' : 'blue')}>{o.status}</span></td>
                <td style={s.td}>{o.expected_delivery ? new Date(o.expected_delivery).toLocaleDateString('es-MX') : '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div style={s.card}>
        <div style={s.cardHeader}><h3 style={s.cardTitle}>Órdenes retrasadas</h3></div>
        <table style={s.table}>
          <thead><tr><th style={s.th}>#OC</th><th style={s.th}>Producto</th><th style={s.th}>Proveedor</th><th style={s.th}>Días retraso</th></tr></thead>
          <tbody>
            {overdueOrders.length === 0 ? (
              <tr><td colSpan={4} style={{ ...s.td, ...s.empty }}>Sin órdenes vencidas</td></tr>
            ) : overdueOrders.map((o) => (
              <tr key={o.id}>
                <td style={s.td}>OC-{o.id}</td>
                <td style={s.td}>{o.item_name}</td>
                <td style={s.td}>{o.supplier_name}</td>
                <td style={{ ...s.td, color: C.red, fontWeight: 700 }}>{o.days_overdue}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function TabEntregas({ username }) {
  const [deliveries, setDeliveries] = useState([]);
  const [selected, setSelected] = useState(null);
  const [msg, setMsg] = useState(null);
  const [newDelivery, setNewDelivery] = useState({ order_id: '', delivery_address: '', assigned_to: '', vehicle: '' });
  const [assignForm, setAssignForm] = useState({ assigned_to: '', vehicle: '' });

  const load = useCallback(async () => {
    const rows = await api.listDeliveries(username, { limit: 100 });
    setDeliveries(Array.isArray(rows) ? rows : []);
  }, [username]);

  useEffect(() => {
    load().catch(() => setDeliveries([]));
  }, [load]);

  async function handleCreate(e) {
    e.preventDefault();
    setMsg(null);
    try {
      await api.createDelivery(username, {
        order_id: Number(newDelivery.order_id),
        delivery_address: newDelivery.delivery_address,
        assigned_to: newDelivery.assigned_to || null,
        vehicle: newDelivery.vehicle || null,
      });
      setMsg({ type: 'success', text: 'Entrega creada.' });
      setNewDelivery({ order_id: '', delivery_address: '', assigned_to: '', vehicle: '' });
      load();
    } catch (err) {
      setMsg({ type: 'error', text: err.message });
    }
  }

  async function handleAssign(deliveryId) {
    try {
      await api.assignDelivery(username, deliveryId, assignForm);
      setMsg({ type: 'success', text: `Entrega ${deliveryId} asignada.` });
      setAssignForm({ assigned_to: '', vehicle: '' });
      load();
    } catch (err) {
      setMsg({ type: 'error', text: err.message });
    }
  }

  async function handleStatus(deliveryId, status) {
    try {
      await api.updateDeliveryStatus(username, deliveryId, status);
      setMsg({ type: 'success', text: `Estado de entrega ${deliveryId} actualizado.` });
      load();
    } catch (err) {
      setMsg({ type: 'error', text: err.message });
    }
  }

  async function handleDetail(deliveryId) {
    try {
      const full = await api.getDelivery(username, deliveryId);
      setSelected(full);
    } catch (err) {
      setMsg({ type: 'error', text: err.message });
    }
  }

  return (
    <div>
      {msg && msg.type !== 'error' && <div style={s.msg(msg.type)}>{msg.text}</div>}
      <div style={s.card}>
        <div style={s.cardHeader}><h3 style={s.cardTitle}>Crear entrega</h3></div>
        <form onSubmit={handleCreate}>
          <div style={s.formGrid}>
            <Field label="Order ID">
              <input style={s.input} type="number" required value={newDelivery.order_id} onChange={(e) => setNewDelivery({ ...newDelivery, order_id: e.target.value })} />
            </Field>
            <Field label="Dirección de entrega">
              <input style={s.input} required value={newDelivery.delivery_address} onChange={(e) => setNewDelivery({ ...newDelivery, delivery_address: e.target.value })} />
            </Field>
            <Field label="Conductor asignado">
              <input style={s.input} value={newDelivery.assigned_to} onChange={(e) => setNewDelivery({ ...newDelivery, assigned_to: e.target.value })} />
            </Field>
            <Field label="Vehículo">
              <input style={s.input} value={newDelivery.vehicle} onChange={(e) => setNewDelivery({ ...newDelivery, vehicle: e.target.value })} />
            </Field>
          </div>
          <div style={s.formActions}>
            <button type="submit" style={s.btn('primary')}>Crear entrega</button>
          </div>
        </form>
      </div>

      <div style={s.card}>
        <div style={s.cardHeader}>
          <h3 style={s.cardTitle}>Entregas</h3>
          <button style={s.btn('secondary')} onClick={load}>Actualizar</button>
        </div>
        <table style={s.table}>
          <thead>
            <tr>
              <th style={s.th}>#</th>
              <th style={s.th}>Order</th>
              <th style={s.th}>Dirección</th>
              <th style={s.th}>Asignado</th>
              <th style={s.th}>Vehículo</th>
              <th style={s.th}>Estado</th>
              <th style={s.th}>Acciones</th>
            </tr>
          </thead>
          <tbody>
            {deliveries.length === 0 ? (
              <tr><td colSpan={7} style={{ ...s.td, ...s.empty }}>Sin entregas registradas</td></tr>
            ) : deliveries.map((d) => (
              <tr key={d.id}>
                <td style={s.td}>DEL-{d.id}</td>
                <td style={s.td}>{d.order_id}</td>
                <td style={s.td}>{d.delivery_address}</td>
                <td style={s.td}>{d.assigned_to || '—'}</td>
                <td style={s.td}>{d.vehicle || '—'}</td>
                <td style={s.td}><DeliveryStatusBadge status={d.status} /></td>
                <td style={s.td}>
                  <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                    <select style={{ ...s.select, width: 112 }} defaultValue="" onChange={(e) => e.target.value && handleStatus(d.id, e.target.value)}>
                      <option value="">Estado...</option>
                      <option value="pending">pending</option>
                      <option value="in_transit">in_transit</option>
                      <option value="delivered">delivered</option>
                    </select>
                    <button style={s.btn('warning')} onClick={() => handleDetail(d.id)}>Detalle</button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        <div style={{ marginTop: 14, borderTop: `1px solid ${C.border}`, paddingTop: 12 }}>
          <h4 style={{ margin: '0 0 10px', fontSize: 13 }}>Asignar conductor/vehículo</h4>
          <div style={{ ...s.formGrid, gridTemplateColumns: '120px 1fr 1fr auto' }}>
            <Field label="Delivery ID">
              <input style={s.input} id="deliveryIdAssign" type="number" placeholder="ID" />
            </Field>
            <Field label="Conductor">
              <input style={s.input} value={assignForm.assigned_to} onChange={(e) => setAssignForm({ ...assignForm, assigned_to: e.target.value })} />
            </Field>
            <Field label="Vehículo">
              <input style={s.input} value={assignForm.vehicle} onChange={(e) => setAssignForm({ ...assignForm, vehicle: e.target.value })} />
            </Field>
            <div style={{ display: 'flex', alignItems: 'flex-end' }}>
              <button
                style={s.btn('success')}
                type="button"
                onClick={() => {
                  const input = document.getElementById('deliveryIdAssign');
                  const id = Number(input?.value);
                  if (!id) return setMsg({ type: 'error', text: 'Indica un Delivery ID válido.' });
                  handleAssign(id);
                }}
              >
                Asignar
              </button>
            </div>
          </div>
        </div>
      </div>

      {selected && (
        <div style={s.card}>
          <div style={s.cardHeader}>
            <h3 style={s.cardTitle}>Detalle entrega DEL-{selected.id}</h3>
            <button style={s.btn('ghost')} onClick={() => setSelected(null)}>Cerrar</button>
          </div>
          <table style={s.table}>
            <tbody>
              {[
                ['Order', selected.order_id],
                ['Dirección', selected.delivery_address],
                ['Conductor', selected.assigned_to || '—'],
                ['Vehículo', selected.vehicle || '—'],
                ['Estado', selected.status],
                ['Creado por', selected.created_by || '—'],
                ['Creado', selected.created_at ? new Date(selected.created_at).toLocaleString('es-MX') : '—'],
                ['Asignado', selected.assigned_at ? new Date(selected.assigned_at).toLocaleString('es-MX') : '—'],
                ['Entregado', selected.delivered_at ? new Date(selected.delivered_at).toLocaleString('es-MX') : '—'],
              ].map(([k, v]) => (
                <tr key={k}>
                  <td style={{ ...s.td, color: C.muted, width: '38%' }}>{k}</td>
                  <td style={s.td}>{String(v)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

const TABS = [
  { key: 'dashboard', label: 'Dashboard' },
  { key: 'monitoreo', label: 'Monitoreo Inventario' },
  { key: 'solicitudes', label: 'Solicitudes' },
  { key: 'ordenes', label: 'Órdenes Compra' },
  { key: 'entregas', label: 'Entregas' },
];

export default function Logistica({ username = 'admin' }) {
  const [tab, setTab] = useState('dashboard');

  return (
    <div style={s.page}>
      <div style={s.header}>
        <div>
          <h1 style={s.title}>Logística</h1>
          <div style={s.subtitle}>HU-LOG-01 · HU-LOG-02 · HU-LOG-03 · Microservicio en localhost:8002</div>
        </div>
      </div>

      <div style={s.tabs}>
        {TABS.map((t) => (
          <button key={t.key} style={s.tab(tab === t.key)} onClick={() => setTab(t.key)}>
            {t.label}
          </button>
        ))}
      </div>

      <div style={s.body}>
        {tab === 'dashboard' && <TabDashboard username={username} />}
        {tab === 'monitoreo' && <TabMonitoreo username={username} />}
        {tab === 'solicitudes' && <TabSolicitudes username={username} />}
        {tab === 'ordenes' && <TabOrdenes username={username} />}
        {tab === 'entregas' && <TabEntregas username={username} />}
      </div>
    </div>
  );
}
