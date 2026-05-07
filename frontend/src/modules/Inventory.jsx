import React, { useEffect, useState, useCallback } from 'react';
import * as api from '../api/inventarioApi';

// ─── Design tokens ───────────────────────────────────────────────────────────
const C = {
  bg:      '#0d1117',
  surface: '#131920',
  card:    '#161f2a',
  border:  '#1e2d3d',
  accent:  '#58a6ff',
  accentLo:'#0d2044',
  green:   '#3fb950',
  greenLo: '#0d2e14',
  red:     '#f85149',
  redLo:   '#2d0f0e',
  yellow:  '#e3b341',
  yellowLo:'#2d2200',
  orange:  '#f0883e',
  orangeLo:'#2d1800',
  purple:  '#bc8cff',
  purpleLo:'#2a1060',
  text:    '#c9d1d9',
  muted:   '#4a5568',
  dim:     '#30363d',
};

const font = "'IBM Plex Mono', 'Fira Code', 'Consolas', monospace";

const s = {
  page:   { background: C.bg, minHeight: '100vh', fontFamily: font, color: C.text, fontSize: 13 },
  header: {
    background: C.surface, borderBottom: `1px solid ${C.border}`,
    padding: '16px 28px', display: 'flex', justifyContent: 'space-between', alignItems: 'center',
  },
  title:    { margin: 0, fontSize: 18, fontWeight: 700, letterSpacing: '-0.3px', color: '#fff' },
  subtitle: { fontSize: 10, color: C.muted, marginTop: 3, letterSpacing: 0.5 },
  tabs: {
    display: 'flex', gap: 0, background: C.surface,
    borderBottom: `1px solid ${C.border}`, padding: '0 28px',
  },
  tab: (active) => ({
    padding: '10px 18px', border: 'none', cursor: 'pointer', fontSize: 12, fontWeight: 600,
    background: 'transparent',
    color: active ? C.accent : C.muted,
    borderBottom: active ? `2px solid ${C.accent}` : '2px solid transparent',
    transition: 'all .15s',
  }),
  body:  { padding: '20px 28px' },
  kpiRow: { display: 'flex', gap: 10, marginBottom: 18, flexWrap: 'wrap' },
  kpi: (accent) => ({
    background: C.card, border: `1px solid ${C.border}`, borderRadius: 6,
    padding: '12px 16px', flex: '1 1 120px', borderTop: `2px solid ${accent || C.accent}`,
  }),
  kpiLabel: { fontSize: 9, color: C.muted, textTransform: 'uppercase', letterSpacing: 1.2, marginBottom: 5 },
  kpiValue: (color) => ({ fontSize: 22, fontWeight: 700, color: color || C.accent }),
  card: {
    background: C.card, border: `1px solid ${C.border}`, borderRadius: 6,
    padding: 16, marginBottom: 14,
  },
  row: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 },
  sectionTitle: { fontSize: 11, fontWeight: 700, color: C.muted, textTransform: 'uppercase', letterSpacing: 1 },
  btn: (v = 'primary') => ({
    padding: '6px 12px', borderRadius: 4, border: 'none', cursor: 'pointer',
    fontSize: 11, fontWeight: 700, letterSpacing: 0.4,
    background: v === 'primary' ? C.accent
              : v === 'danger'  ? C.red
              : v === 'success' ? C.green
              : v === 'warning' ? C.yellow
              : v === 'orange'  ? C.orange
              : v === 'ghost'   ? 'transparent'
              : C.dim,
    color: v === 'ghost' ? C.muted : v === 'warning' ? C.bg : '#fff',
    transition: 'opacity .15s',
  }),
  table: { width: '100%', borderCollapse: 'collapse', fontSize: 12 },
  th: {
    textAlign: 'left', padding: '7px 10px', color: C.muted, fontSize: 10,
    fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.8,
    borderBottom: `1px solid ${C.border}`,
  },
  td: { padding: '10px 10px', borderBottom: `1px solid ${C.border}22`, verticalAlign: 'middle' },
  badge: (color) => ({
    display: 'inline-block', padding: '2px 7px', borderRadius: 3,
    fontSize: 9, fontWeight: 700, letterSpacing: 0.6, textTransform: 'uppercase',
    background: color === 'green'  ? C.greenLo
              : color === 'red'    ? C.redLo
              : color === 'yellow' ? C.yellowLo
              : color === 'orange' ? C.orangeLo
              : color === 'purple' ? C.purpleLo
              : C.accentLo,
    color: color === 'green'  ? C.green
         : color === 'red'    ? C.red
         : color === 'yellow' ? C.yellow
         : color === 'orange' ? C.orange
         : color === 'purple' ? C.purple
         : C.accent,
  }),
  input: {
    width: '100%', background: C.surface, border: `1px solid ${C.border}`, borderRadius: 4,
    padding: '7px 10px', color: C.text, fontSize: 12, outline: 'none',
    boxSizing: 'border-box', fontFamily: font,
  },
  select: {
    width: '100%', background: C.surface, border: `1px solid ${C.border}`, borderRadius: 4,
    padding: '7px 10px', color: C.text, fontSize: 12, outline: 'none',
    boxSizing: 'border-box', fontFamily: font,
  },
  label: { display: 'block', fontSize: 9, color: C.muted, marginBottom: 4, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.8 },
  formGrid: (cols = 2) => ({ display: 'grid', gridTemplateColumns: `repeat(${cols}, 1fr)`, gap: 10, marginBottom: 14 }),
  formActions: { display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 14 },
  overlay: {
    position: 'fixed', inset: 0, background: 'rgba(0,0,0,.8)',
    display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000,
  },
  modal: {
    background: C.card, border: `1px solid ${C.border}`, borderRadius: 8,
    padding: 22, width: 500, maxHeight: '85vh', overflowY: 'auto',
  },
  empty: { textAlign: 'center', padding: '30px 0', color: C.muted, fontSize: 12 },
  msg: (type) => ({
    fontSize: 11, padding: '8px 12px', borderRadius: 4, marginBottom: 12,
    background: type === 'error' ? C.surface : type === 'warning' ? C.yellowLo : C.greenLo,
    color:      type === 'error' ? C.muted : type === 'warning' ? C.yellow   : C.green,
    border:     `1px solid ${type === 'error' ? C.border : type === 'warning' ? C.yellow + '44' : C.green + '44'}`,
    opacity: type === 'error' ? 0.72 : 1,
  }),
  stockBar: (pct, color) => ({
    height: 4, borderRadius: 2, background: C.dim, position: 'relative', width: '100%', minWidth: 80,
  }),
  stockFill: (pct, color) => ({
    height: '100%', borderRadius: 2, width: `${Math.min(pct, 100)}%`,
    background: color === 'red' ? C.red : color === 'yellow' ? C.yellow : C.green,
    transition: 'width .4s',
  }),
};

// ─── Helpers ─────────────────────────────────────────────────────────────────
function Modal({ title, onClose, children, width = 500 }) {
  return (
    <div style={s.overlay} onClick={onClose}>
      <div style={{ ...s.modal, width }} onClick={e => e.stopPropagation()}>
        <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:16 }}>
          <span style={{ fontSize:13, fontWeight:700, color:'#fff' }}>{title}</span>
          <button style={s.btn('ghost')} onClick={onClose}>✕</button>
        </div>
        {children}
      </div>
    </div>
  );
}

function Field({ label, children, span }) {
  return (
    <div style={span ? { gridColumn: `span ${span}` } : {}}>
      <label style={s.label}>{label}</label>
      {children}
    </div>
  );
}

function Msg({ msg }) {
  if (!msg) return null;
  if (msg.type === 'error') return null;
  return <div style={s.msg(msg.type)}>{msg.text}</div>;
}

function stockColor(item) {
  if (!item.quantity_on_hand && item.quantity_on_hand !== 0) return 'blue';
  if (item.quantity_on_hand === 0) return 'red';
  if (item.below_minimum || item.quantity_on_hand <= item.minimum_threshold) return 'yellow';
  return 'green';
}

function stockPct(item) {
  if (!item.minimum_threshold) return 100;
  return Math.round((item.quantity_on_hand / (item.minimum_threshold * 3)) * 100);
}

const PRIORITY_COLORS = { low:'blue', normal:'green', high:'orange', urgent:'red' };
const ALERT_COLORS    = { critical:'red', warning:'yellow', info:'blue' };

// ══════════════════════════════════════════════════════════════
// TAB: Catálogo de Productos  (HU-INV-01, HU-INV-02)
// ══════════════════════════════════════════════════════════════
function TabCatalogo({ username }) {
  const [items,     setItems]     = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [loading,   setLoading]   = useState(false);
  const [msg,       setMsg]       = useState(null);
  const [filter,    setFilter]    = useState({ category:'', search:'' });
  const [detail,    setDetail]    = useState(null); // item detail modal

  const load = useCallback(async () => {
    setLoading(true); setMsg(null);
    try {
      const params = {};
      if (filter.category) params.category = filter.category;
      const [it, su] = await Promise.all([api.listItems(username, params), api.listSuppliers(username)]);
      setItems(Array.isArray(it) ? it : []);
      setSuppliers(Array.isArray(su) ? su : []);
    } catch {
      setMsg({ type:'warning', text:'Servicio no disponible — mostrando datos mock.' });
      setItems([
        { id:1, sku:'SKU-001', name:'Laptop Dell XPS 13', quantity_on_hand:5,  minimum_threshold:3, reorder_quantity:10, unit_cost:1200, category:'Electrónica', active:true, below_minimum:false },
        { id:2, sku:'SKU-002', name:'Monitor LG 27"',     quantity_on_hand:2,  minimum_threshold:5, reorder_quantity:8,  unit_cost:350,  category:'Electrónica', active:true, below_minimum:true  },
        { id:3, sku:'SKU-003', name:'Silla Ergonómica',   quantity_on_hand:0,  minimum_threshold:2, reorder_quantity:5,  unit_cost:280,  category:'Mobiliario',  active:true, below_minimum:true  },
      ]);
      setSuppliers([{ id:1, name:'TechSupply Inc' }]);
    } finally { setLoading(false); }
  }, [username, filter.category]);

  useEffect(() => { load(); }, [load]);

  async function handleDetail(item) {
    try { setDetail(await api.getItem(username, item.id)); }
    catch { setDetail(item); }
  }

  const displayed = items.filter(it =>
    !filter.search || it.name?.toLowerCase().includes(filter.search.toLowerCase()) || it.sku?.includes(filter.search)
  );

  const categories = [...new Set(items.map(i => i.category).filter(Boolean))];

  // KPIs
  const total     = items.length;
  const stockOk   = items.filter(i => !i.below_minimum && i.quantity_on_hand > 0).length;
  const lowStock  = items.filter(i => i.below_minimum).length;
  const stockout  = items.filter(i => i.quantity_on_hand === 0).length;

  return (
    <div>
      <div style={s.kpiRow}>
        <div style={s.kpi(C.accent)}>
          <div style={s.kpiLabel}>Total productos</div>
          <div style={s.kpiValue(C.accent)}>{total}</div>
        </div>
        <div style={s.kpi(C.green)}>
          <div style={s.kpiLabel}>Stock OK</div>
          <div style={s.kpiValue(C.green)}>{stockOk}</div>
        </div>
        <div style={s.kpi(C.yellow)}>
          <div style={s.kpiLabel}>Stock bajo</div>
          <div style={s.kpiValue(C.yellow)}>{lowStock}</div>
        </div>
        <div style={s.kpi(C.red)}>
          <div style={s.kpiLabel}>Agotado</div>
          <div style={s.kpiValue(C.red)}>{stockout}</div>
        </div>
      </div>

      <div style={{ ...s.card, display:'flex', gap:10, alignItems:'flex-end', flexWrap:'wrap' }}>
        <div style={{ flex:'1 1 180px' }}>
          <label style={s.label}>Buscar</label>
          <input style={s.input} placeholder="Nombre o SKU..." value={filter.search}
            onChange={e => setFilter({ ...filter, search: e.target.value })} />
        </div>
        <div style={{ flex:'1 1 140px' }}>
          <label style={s.label}>Categoría</label>
          <select style={s.select} value={filter.category}
            onChange={e => setFilter({ ...filter, category: e.target.value })}>
            <option value="">Todas</option>
            {categories.map(c => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>
        <button style={s.btn()} onClick={load}>↺ Actualizar</button>
      </div>

      <Msg msg={msg} />

      <div style={s.card}>
        {loading ? <div style={s.empty}>Cargando productos...</div> : (
          <table style={s.table}>
            <thead><tr>
              <th style={s.th}>SKU</th>
              <th style={s.th}>Nombre</th>
              <th style={s.th}>Categoría</th>
              <th style={s.th}>Stock</th>
              <th style={s.th}>Mínimo</th>
              <th style={s.th}>Nivel</th>
              <th style={s.th}>Estado</th>
              <th style={s.th}>Costo unit.</th>
              <th style={s.th}>Acciones</th>
            </tr></thead>
            <tbody>
              {displayed.length === 0
                ? <tr><td colSpan={9} style={{ ...s.td, ...s.empty }}>Sin productos</td></tr>
                : displayed.map((item, i) => {
                  const color = stockColor(item);
                  const pct   = stockPct(item);
                  return (
                    <tr key={item.id || i}>
                      <td style={{ ...s.td, color: C.accent, fontFamily:'monospace' }}>{item.sku}</td>
                      <td style={s.td}>{item.name}</td>
                      <td style={s.td}>{item.category || '—'}</td>
                      <td style={{ ...s.td, fontWeight:700, color: color === 'red' ? C.red : color === 'yellow' ? C.yellow : C.text }}>
                        {item.quantity_on_hand ?? '—'}
                      </td>
                      <td style={{ ...s.td, color: C.muted }}>{item.minimum_threshold ?? '—'}</td>
                      <td style={{ ...s.td, minWidth: 90 }}>
                        <div style={s.stockBar(pct, color)}>
                          <div style={s.stockFill(pct, color)} />
                        </div>
                        <div style={{ fontSize:9, color:C.muted, marginTop:2 }}>{pct}%</div>
                      </td>
                      <td style={s.td}>
                        {item.quantity_on_hand === 0
                          ? <span style={s.badge('red')}>Agotado</span>
                          : item.below_minimum
                            ? <span style={s.badge('yellow')}>Stock bajo</span>
                            : <span style={s.badge('green')}>OK</span>
                        }
                      </td>
                      <td style={s.td}>${(item.unit_cost || 0).toLocaleString()}</td>
                      <td style={s.td}>
                        <button style={s.btn('ghost')} onClick={() => handleDetail(item)}>Detalle</button>
                      </td>
                    </tr>
                  );
                })
              }
            </tbody>
          </table>
        )}
      </div>

      {detail && (
        <Modal title={`Detalle — ${detail.name}`} onClose={() => setDetail(null)}>
          <table style={{ ...s.table, fontSize:12 }}>
            <tbody>
              {[
                ['ID', detail.id], ['SKU', detail.sku], ['Nombre', detail.name],
                ['Descripción', detail.description || '—'], ['Categoría', detail.category || '—'],
                ['Stock actual', detail.quantity_on_hand], ['Mínimo', detail.minimum_threshold],
                ['Reorden', detail.reorder_quantity], ['Costo unitario', `$${(detail.unit_cost||0).toLocaleString()}`],
                ['Medida', detail.unit_of_measure || '—'],
                ['Activo', detail.active ? 'Sí' : 'No'],
                ['Bajo mínimo', detail.below_minimum ? 'Sí' : 'No'],
                ['Última actualización', detail.last_updated ? new Date(detail.last_updated).toLocaleString('es-MX') : '—'],
              ].map(([k, v]) => (
                <tr key={k}>
                  <td style={{ ...s.td, color: C.muted, fontSize:10, width:'40%' }}>{k}</td>
                  <td style={{ ...s.td, fontWeight:600 }}>{String(v)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div style={s.formActions}>
            <button style={s.btn('ghost')} onClick={() => setDetail(null)}>Cerrar</button>
          </div>
        </Modal>
      )}
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
// TAB: Movimientos de Stock  (HU-INV-03, HU-INV-04, HU-INV-05, HU-INV-06)
// ══════════════════════════════════════════════════════════════
function TabMovimientos({ username }) {
  const [items,   setItems]   = useState([]);
  const [loading, setLoading] = useState(false);
  const [msg,     setMsg]     = useState(null);
  const [form,    setForm]    = useState({ item_id:'', movement_type:'in', quantity:'', reason:'restock', reference_id:'' });
  const [result,  setResult]  = useState(null);

  useEffect(() => {
    api.listItems(username, {})
      .then(r => setItems(Array.isArray(r) ? r : []))
      .catch(() => setItems([
        { id:1, sku:'SKU-001', name:'Laptop Dell XPS 13', quantity_on_hand:5 },
        { id:2, sku:'SKU-002', name:'Monitor LG 27"',     quantity_on_hand:2 },
      ]));
  }, [username]);

  async function handleSubmit(e) {
    e.preventDefault();
    setMsg(null); setResult(null); setLoading(true);
    try {
      const qty = form.movement_type === 'out' ? -Math.abs(Number(form.quantity)) : Math.abs(Number(form.quantity));
      const res = await api.updateStock(username, form.item_id, qty, form.reason, form.reference_id || undefined);
      setResult(res);
      setMsg({ type:'success', text:`Stock actualizado. Nuevo stock: ${res.new_quantity} unidades.` });
    } catch(err) {
      setMsg({ type:'error', text: err.message });
    } finally { setLoading(false); }
  }

  const MOVEMENT_TYPES = [
    { value:'in',         label:'Entrada (+)' },
    { value:'out',        label:'Salida (−)' },
    { value:'adjustment', label:'Ajuste' },
    { value:'return',     label:'Devolución (+)' },
    { value:'damage',     label:'Daño (−)' },
  ];

  const REASONS = {
    in:         ['restock', 'purchase_received', 'return'],
    out:        ['sale', 'transfer', 'damage', 'loss'],
    adjustment: ['correction', 'count_adjustment'],
    return:     ['customer_return', 'supplier_return'],
    damage:     ['damage', 'expired'],
  };

  const currentReasons = REASONS[form.movement_type] || ['other'];

  return (
    <div>
      <div style={s.row}>
        <span style={s.sectionTitle}>Registrar movimiento de stock</span>
      </div>

      <div style={s.card}>
        <form onSubmit={handleSubmit}>
          <div style={s.formGrid(2)}>
            <Field label="Producto">
              <select style={s.select} required value={form.item_id}
                onChange={e => setForm({ ...form, item_id: e.target.value })}>
                <option value="">Seleccionar producto...</option>
                {items.map(it => (
                  <option key={it.id} value={it.id}>
                    {it.sku} — {it.name} (stock: {it.quantity_on_hand ?? '?'})
                  </option>
                ))}
              </select>
            </Field>

            <Field label="Tipo de movimiento">
              <select style={s.select} value={form.movement_type}
                onChange={e => setForm({ ...form, movement_type: e.target.value, reason: REASONS[e.target.value]?.[0] || '' })}>
                {MOVEMENT_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
              </select>
            </Field>

            <Field label="Cantidad">
              <input style={s.input} type="number" min="1" required value={form.quantity}
                onChange={e => setForm({ ...form, quantity: e.target.value })} placeholder="Ej: 10" />
            </Field>

            <Field label="Motivo">
              <select style={s.select} value={form.reason}
                onChange={e => setForm({ ...form, reason: e.target.value })}>
                {currentReasons.map(r => <option key={r} value={r}>{r}</option>)}
              </select>
            </Field>

            <Field label="Referencia (opcional)" span={2}>
              <input style={s.input} value={form.reference_id}
                onChange={e => setForm({ ...form, reference_id: e.target.value })}
                placeholder="Ej: PO-1001, SO-500..." />
            </Field>
          </div>

          <Msg msg={msg} />

          {result && (
            <div style={{ ...s.card, background: C.greenLo, border:`1px solid ${C.green}44`, marginBottom:0 }}>
              <div style={{ display:'flex', gap:24, fontSize:12 }}>
                <span>Item ID: <strong style={{ color:C.text }}>{result.item_id}</strong></span>
                <span>Cambio: <strong style={{ color: result.change >= 0 ? C.green : C.red }}>
                  {result.change >= 0 ? '+' : ''}{result.change}
                </strong></span>
                <span>Nuevo stock: <strong style={{ color:C.accent }}>{result.new_quantity}</strong></span>
              </div>
            </div>
          )}

          <div style={{ ...s.formActions, marginTop: result ? 12 : 0 }}>
            <button type="submit" style={s.btn()} disabled={loading}>
              {loading ? 'Procesando...' : '↑↓ Registrar movimiento'}
            </button>
          </div>
        </form>
      </div>

      {/* Quick reference */}
      <div style={s.card}>
        <div style={{ ...s.row, marginBottom: 8 }}>
          <span style={s.sectionTitle}>Tipos de movimiento</span>
        </div>
        <div style={{ display:'flex', gap:8, flexWrap:'wrap' }}>
          {[
            { type:'in', label:'Entrada', color:'green', desc:'Recepción de compra, devolución de cliente' },
            { type:'out', label:'Salida', color:'red', desc:'Venta, transferencia, daño' },
            { type:'adjustment', label:'Ajuste', color:'blue', desc:'Corrección por conteo físico' },
            { type:'return', label:'Devolución', color:'purple', desc:'Retorno a proveedor o de cliente' },
            { type:'damage', label:'Daño', color:'orange', desc:'Producto dañado o vencido' },
          ].map(item => (
            <div key={item.type} style={{
              background: C.surface, border:`1px solid ${C.border}`, borderRadius:4,
              padding:'8px 12px', flex:'1 1 140px',
            }}>
              <div style={{ marginBottom:4 }}><span style={s.badge(item.color)}>{item.label}</span></div>
              <div style={{ fontSize:10, color:C.muted, lineHeight:1.4 }}>{item.desc}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
// TAB: Alertas de Stock
// ══════════════════════════════════════════════════════════════
function TabAlertas({ username }) {
  const [alerts,   setAlerts]   = useState([]);
  const [loading,  setLoading]  = useState(false);
  const [msg,      setMsg]      = useState(null);
  const [unackOnly, setUnackOnly] = useState(false);

  const load = useCallback(async () => {
    setLoading(true); setMsg(null);
    try {
      const res = await api.listAlerts(username, unackOnly);
      setAlerts(Array.isArray(res) ? res : []);
    } catch {
      setMsg({ type:'warning', text:'Mock — servicio no disponible.' });
      setAlerts([
        { id:1, item_id:2, alert_type:'below_minimum', current_quantity:2, threshold:5, severity:'critical', acknowledged:false },
        { id:2, item_id:3, alert_type:'stockout',      current_quantity:0, threshold:2, severity:'critical', acknowledged:false },
        { id:3, item_id:1, alert_type:'below_minimum', current_quantity:3, threshold:3, severity:'warning',  acknowledged:true  },
      ]);
    } finally { setLoading(false); }
  }, [username, unackOnly]);

  useEffect(() => { load(); }, [load]);

  async function handleAck(alert) {
    try {
      await api.acknowledgeAlert(username, alert.id);
      setMsg({ type:'success', text:`Alerta #${alert.id} reconocida.` });
      load();
    } catch(err) { setMsg({ type:'error', text: err.message }); }
  }

  const alertTypeLabel = { below_minimum:'Bajo mínimo', stockout:'Sin stock', overstock:'Sobre stock' };

  return (
    <div>
      <div style={s.row}>
        <span style={s.sectionTitle}>Alertas de inventario</span>
        <div style={{ display:'flex', gap:8, alignItems:'center' }}>
          <label style={{ ...s.label, display:'flex', alignItems:'center', gap:6, cursor:'pointer', marginBottom:0 }}>
            <input type="checkbox" checked={unackOnly} onChange={e => setUnackOnly(e.target.checked)} />
            Solo no reconocidas
          </label>
          <button style={s.btn()} onClick={load}>↺ Actualizar</button>
        </div>
      </div>

      <Msg msg={msg} />

      {/* Summary */}
      <div style={s.kpiRow}>
        <div style={s.kpi(C.red)}>
          <div style={s.kpiLabel}>Críticas</div>
          <div style={s.kpiValue(C.red)}>{alerts.filter(a => a.severity==='critical').length}</div>
        </div>
        <div style={s.kpi(C.yellow)}>
          <div style={s.kpiLabel}>Advertencia</div>
          <div style={s.kpiValue(C.yellow)}>{alerts.filter(a => a.severity==='warning').length}</div>
        </div>
        <div style={s.kpi(C.muted)}>
          <div style={s.kpiLabel}>Reconocidas</div>
          <div style={s.kpiValue(C.muted)}>{alerts.filter(a => a.acknowledged).length}</div>
        </div>
        <div style={s.kpi(C.accent)}>
          <div style={s.kpiLabel}>Total</div>
          <div style={s.kpiValue(C.accent)}>{alerts.length}</div>
        </div>
      </div>

      <div style={s.card}>
        {loading ? <div style={s.empty}>Cargando alertas...</div> : (
          <table style={s.table}>
            <thead><tr>
              <th style={s.th}>#</th>
              <th style={s.th}>Item ID</th>
              <th style={s.th}>Tipo</th>
              <th style={s.th}>Stock actual</th>
              <th style={s.th}>Umbral</th>
              <th style={s.th}>Severidad</th>
              <th style={s.th}>Estado</th>
              <th style={s.th}>Acción</th>
            </tr></thead>
            <tbody>
              {alerts.length === 0
                ? <tr><td colSpan={8} style={{ ...s.td, ...s.empty }}>Sin alertas activas</td></tr>
                : alerts.map((a, i) => (
                  <tr key={a.id || i} style={{ opacity: a.acknowledged ? 0.5 : 1 }}>
                    <td style={s.td}>{a.id}</td>
                    <td style={{ ...s.td, color:C.accent }}>{a.item_id}</td>
                    <td style={s.td}>{alertTypeLabel[a.alert_type] || a.alert_type}</td>
                    <td style={{ ...s.td, fontWeight:700, color: a.current_quantity === 0 ? C.red : C.yellow }}>
                      {a.current_quantity}
                    </td>
                    <td style={{ ...s.td, color:C.muted }}>{a.threshold}</td>
                    <td style={s.td}>
                      <span style={s.badge(ALERT_COLORS[a.severity] || 'blue')}>{a.severity}</span>
                    </td>
                    <td style={s.td}>
                      {a.acknowledged
                        ? <span style={s.badge('green')}>Reconocida</span>
                        : <span style={s.badge('red')}>Pendiente</span>
                      }
                    </td>
                    <td style={s.td}>
                      {!a.acknowledged && (
                        <button style={s.btn('success')} onClick={() => handleAck(a)}>✓ Reconocer</button>
                      )}
                    </td>
                  </tr>
                ))
              }
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
// TAB: Solicitudes Logísticas  (HU-INV-05 — reabastecimiento, devoluciones, daños)
// ══════════════════════════════════════════════════════════════
function TabSolicitudes({ username }) {
  const [solicitudes, setSolicitudes] = useState([]);
  const [items,       setItems]       = useState([]);
  const [loading,     setLoading]     = useState(false);
  const [msg,         setMsg]         = useState(null);
  const [showNew,     setShowNew]     = useState(false);
  const [statusFilter, setStatusFilter] = useState('');
  const [form, setForm] = useState({ item_id:'', requested_quantity:'', reason:'restock', priority:'normal', notes:'' });

  const load = useCallback(async () => {
    setLoading(true); setMsg(null);
    try {
      const params = {};
      if (statusFilter) params.status = statusFilter;
      const [s, it] = await Promise.all([api.listSolicitudes(username, params), api.listItems(username, {})]);
      setSolicitudes(Array.isArray(s) ? s : []);
      setItems(Array.isArray(it) ? it : []);
    } catch {
      setMsg({ type:'warning', text:'Mock — servicio no disponible.' });
      setSolicitudes([
        { id:10, item_id:2, requested_quantity:50, reason:'restock',  priority:'high',   status:'pending',   created_by:'admin' },
        { id:11, item_id:3, requested_quantity:10, reason:'damage',   priority:'urgent',  status:'approved',  created_by:'admin' },
        { id:12, item_id:1, requested_quantity:5,  reason:'return',   priority:'normal',  status:'fulfilled', created_by:'admin' },
      ]);
      setItems([
        { id:1, sku:'SKU-001', name:'Laptop Dell XPS 13' },
        { id:2, sku:'SKU-002', name:'Monitor LG 27"' },
        { id:3, sku:'SKU-003', name:'Silla Ergonómica' },
      ]);
    } finally { setLoading(false); }
  }, [username, statusFilter]);

  useEffect(() => { load(); }, [load]);

  async function handleCreate(e) {
    e.preventDefault();
    try {
      await api.createSolicitud(username, {
        item_id: Number(form.item_id),
        requested_quantity: Number(form.requested_quantity),
        reason: form.reason,
        priority: form.priority,
        notes: form.notes,
      });
      setMsg({ type:'success', text:'Solicitud logística creada.' });
      setShowNew(false);
      setForm({ item_id:'', requested_quantity:'', reason:'restock', priority:'normal', notes:'' });
      load();
    } catch(err) { setMsg({ type:'error', text: err.message }); }
  }

  async function handleApprove(sol) {
    try {
      await api.approveSolicitud(username, sol.id);
      setMsg({ type:'success', text:`Solicitud #${sol.id} aprobada.` });
      load();
    } catch(err) { setMsg({ type:'error', text: err.message }); }
  }

  async function handleFulfill(sol) {
    try {
      await api.fulfillSolicitud(username, sol.id);
      setMsg({ type:'success', text:`Solicitud #${sol.id} completada. Stock actualizado.` });
      load();
    } catch(err) { setMsg({ type:'error', text: err.message }); }
  }

  const itemName = id => items.find(i => i.id === id)?.name || `Item #${id}`;

  const STATUS_COLORS = { pending:'yellow', approved:'blue', fulfilled:'green', rejected:'red' };

  return (
    <div>
      <div style={s.row}>
        <span style={s.sectionTitle}>Solicitudes logísticas</span>
        <div style={{ display:'flex', gap:8 }}>
          <select style={{ ...s.select, width:'auto', fontSize:11, padding:'5px 8px' }}
            value={statusFilter} onChange={e => setStatusFilter(e.target.value)}>
            <option value="">Todos los estados</option>
            <option value="pending">Pendientes</option>
            <option value="approved">Aprobadas</option>
            <option value="fulfilled">Completadas</option>
            <option value="rejected">Rechazadas</option>
          </select>
          <button style={s.btn()} onClick={() => setShowNew(true)}>+ Nueva solicitud</button>
        </div>
      </div>

      <Msg msg={msg} />

      <div style={s.card}>
        {loading ? <div style={s.empty}>Cargando...</div> : (
          <table style={s.table}>
            <thead><tr>
              <th style={s.th}>#</th>
              <th style={s.th}>Producto</th>
              <th style={s.th}>Cantidad</th>
              <th style={s.th}>Motivo</th>
              <th style={s.th}>Prioridad</th>
              <th style={s.th}>Estado</th>
              <th style={s.th}>Creado por</th>
              <th style={s.th}>Acciones</th>
            </tr></thead>
            <tbody>
              {solicitudes.length === 0
                ? <tr><td colSpan={8} style={{ ...s.td, ...s.empty }}>Sin solicitudes</td></tr>
                : solicitudes.map((sol, i) => (
                  <tr key={sol.id || i}>
                    <td style={s.td}>{sol.id}</td>
                    <td style={s.td}>{itemName(sol.item_id)}</td>
                    <td style={{ ...s.td, fontWeight:700 }}>{sol.requested_quantity}</td>
                    <td style={s.td}>{sol.reason}</td>
                    <td style={s.td}>
                      <span style={s.badge(PRIORITY_COLORS[sol.priority] || 'blue')}>{sol.priority}</span>
                    </td>
                    <td style={s.td}>
                      <span style={s.badge(STATUS_COLORS[sol.status] || 'blue')}>{sol.status}</span>
                    </td>
                    <td style={{ ...s.td, color:C.muted }}>{sol.created_by || '—'}</td>
                    <td style={s.td}>
                      <div style={{ display:'flex', gap:4 }}>
                        {sol.status === 'pending'  && <button style={s.btn('warning')} onClick={() => handleApprove(sol)}>✓ Aprobar</button>}
                        {sol.status === 'approved' && <button style={s.btn('success')} onClick={() => handleFulfill(sol)}>✓ Completar</button>}
                      </div>
                    </td>
                  </tr>
                ))
              }
            </tbody>
          </table>
        )}
      </div>

      {showNew && (
        <Modal title="Nueva solicitud logística" onClose={() => setShowNew(false)}>
          <form onSubmit={handleCreate}>
            <div style={s.formGrid(2)}>
              <Field label="Producto" span={2}>
                <select style={s.select} required value={form.item_id}
                  onChange={e => setForm({ ...form, item_id: e.target.value })}>
                  <option value="">Seleccionar...</option>
                  {items.map(it => <option key={it.id} value={it.id}>{it.name} ({it.sku})</option>)}
                </select>
              </Field>
              <Field label="Cantidad solicitada">
                <input style={s.input} type="number" min="1" required value={form.requested_quantity}
                  onChange={e => setForm({ ...form, requested_quantity: e.target.value })} />
              </Field>
              <Field label="Motivo">
                <select style={s.select} value={form.reason}
                  onChange={e => setForm({ ...form, reason: e.target.value })}>
                  {['restock','return','damage','adjustment','transfer'].map(r => (
                    <option key={r} value={r}>{r}</option>
                  ))}
                </select>
              </Field>
              <Field label="Prioridad">
                <select style={s.select} value={form.priority}
                  onChange={e => setForm({ ...form, priority: e.target.value })}>
                  {['low','normal','high','urgent'].map(p => <option key={p} value={p}>{p}</option>)}
                </select>
              </Field>
              <Field label="Notas">
                <input style={s.input} value={form.notes}
                  onChange={e => setForm({ ...form, notes: e.target.value })}
                  placeholder="Información adicional..." />
              </Field>
            </div>
            <div style={s.formActions}>
              <button type="button" style={s.btn('ghost')} onClick={() => setShowNew(false)}>Cancelar</button>
              <button type="submit" style={s.btn()}>Crear solicitud</button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
// MAIN: Inventory module
// ══════════════════════════════════════════════════════════════
const TABS = [
  { key:'catalogo',    label:'Catálogo' },
  { key:'movimientos', label:'Movimientos' },
  { key:'alertas',     label:'Alertas' },
  { key:'solicitudes', label:'Solicitudes Logísticas' },
];

export default function Inventory({ role, permissions }) {
  const [tab,      setTab]      = useState('catalogo');
  const [username, setUsername] = useState('admin');
  const [health,   setHealth]   = useState(null);

  useEffect(() => {
    api.getHealth().then(setHealth).catch(() => setHealth({ status:'offline' }));
  }, []);

  const statusColor = health?.status === 'ok' ? C.green : health?.status === 'offline' ? C.red : C.yellow;

  return (
    <div style={s.page}>
      {/* Header */}
      <div style={s.header}>
        <div style={{ display:'flex', alignItems:'center', gap:12 }}>
          <div style={{ width:8, height:8, borderRadius:'50%', background:statusColor, boxShadow:`0 0 8px ${statusColor}` }} />
          <div>
            <h1 style={s.title}>Inventario</h1>
            <div style={s.subtitle}>Microservicio Inventario · localhost:8001</div>
          </div>
        </div>
        <div style={{ display:'flex', gap:8, alignItems:'center' }}>
          <span style={{ fontSize:10, color:C.muted }}>Usuario:</span>
          <select style={{ ...s.select, width:'auto', fontSize:11, padding:'5px 8px' }}
            value={username} onChange={e => setUsername(e.target.value)}>
            {['admin','compras','inventario','auditor','viewer'].map(u => (
              <option key={u} value={u}>{u}</option>
            ))}
          </select>
        </div>
      </div>

      {/* Tabs */}
      <div style={s.tabs}>
        {TABS.map(t => (
          <button key={t.key} style={s.tab(tab === t.key)} onClick={() => setTab(t.key)}>
            {t.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div style={s.body}>
        {tab === 'catalogo'    && <TabCatalogo    username={username} />}
        {tab === 'movimientos' && <TabMovimientos username={username} />}
        {tab === 'alertas'     && <TabAlertas     username={username} />}
        {tab === 'solicitudes' && <TabSolicitudes username={username} />}
      </div>
    </div>
  );
}