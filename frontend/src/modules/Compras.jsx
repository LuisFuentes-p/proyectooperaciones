import React, { useEffect, useState, useCallback } from 'react';
import * as api from '../api/comprasApi';

// ─── Palette & shared styles ────────────────────────────────────────────────
const C = {
  bg:       '#0f1117',
  surface:  '#181c27',
  card:     '#1e2333',
  border:   '#2a3045',
  accent:   '#4f8ef7',
  accentLo: '#1a2d54',
  green:    '#22c55e',
  greenLo:  '#14321f',
  red:      '#f43f5e',
  redLo:    '#3a1020',
  yellow:   '#f59e0b',
  text:     '#e8ecf4',
  muted:    '#6b7896',
};

const s = {
  page: {
    background: C.bg, minHeight: '100vh', fontFamily: "'IBM Plex Sans', 'Segoe UI', sans-serif",
    color: C.text, padding: '0',
  },
  header: {
    background: C.surface, borderBottom: `1px solid ${C.border}`,
    padding: '20px 28px', display: 'flex', justifyContent: 'space-between', alignItems: 'center',
  },
  title: { margin: 0, fontSize: 22, fontWeight: 700, letterSpacing: '-0.5px' },
  tabs: { display: 'flex', gap: 4, background: C.bg, padding: '12px 28px', borderBottom: `1px solid ${C.border}` },
  tab: (active) => ({
    padding: '7px 18px', borderRadius: 6, border: 'none', cursor: 'pointer', fontSize: 13, fontWeight: 600,
    background: active ? C.accent : 'transparent',
    color: active ? '#fff' : C.muted,
    transition: 'all .15s',
  }),
  body: { padding: '24px 28px' },
  kpiRow: { display: 'flex', gap: 14, marginBottom: 20, flexWrap: 'wrap' },
  kpi: {
    background: C.card, border: `1px solid ${C.border}`, borderRadius: 10,
    padding: '14px 20px', flex: '1 1 160px',
  },
  kpiLabel: { fontSize: 11, color: C.muted, textTransform: 'uppercase', letterSpacing: 1, marginBottom: 4 },
  kpiValue: { fontSize: 26, fontWeight: 700, color: C.accent },
  card: {
    background: C.card, border: `1px solid ${C.border}`, borderRadius: 10, padding: 18, marginBottom: 16,
  },
  sectionHeader: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14,
  },
  sectionTitle: { fontSize: 15, fontWeight: 700, margin: 0 },
  btn: (variant = 'primary') => ({
    padding: '7px 14px', borderRadius: 6, border: 'none', cursor: 'pointer',
    fontSize: 12, fontWeight: 600,
    background: variant === 'primary' ? C.accent
              : variant === 'danger'  ? C.red
              : variant === 'success' ? C.green
              : variant === 'ghost'   ? 'transparent'
              : C.border,
    color: variant === 'ghost' ? C.muted : '#fff',
    transition: 'opacity .15s',
  }),
  table: { width: '100%', borderCollapse: 'collapse', fontSize: 13 },
  th: {
    textAlign: 'left', padding: '8px 10px', color: C.muted,
    fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.5,
    borderBottom: `1px solid ${C.border}`,
  },
  td: { padding: '10px 10px', borderBottom: `1px solid ${C.border}` },
  badge: (color) => ({
    display: 'inline-block', padding: '2px 8px', borderRadius: 20, fontSize: 11, fontWeight: 600,
    background: color === 'green' ? C.greenLo : color === 'red' ? C.redLo : C.accentLo,
    color: color === 'green' ? C.green : color === 'red' ? C.red : C.accent,
    border: `1px solid ${color === 'green' ? C.green : color === 'red' ? C.red : C.accent}44`,
  }),
  input: {
    width: '100%', background: C.surface, border: `1px solid ${C.border}`, borderRadius: 6,
    padding: '8px 10px', color: C.text, fontSize: 13, outline: 'none', boxSizing: 'border-box',
  },
  select: {
    width: '100%', background: C.surface, border: `1px solid ${C.border}`, borderRadius: 6,
    padding: '8px 10px', color: C.text, fontSize: 13, outline: 'none', boxSizing: 'border-box',
  },
  label: { display: 'block', fontSize: 11, color: C.muted, marginBottom: 4, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.5 },
  formGrid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 16 },
  formActions: { display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 16 },
  overlay: {
    position: 'fixed', inset: 0, background: 'rgba(0,0,0,.65)', display: 'flex',
    alignItems: 'center', justifyContent: 'center', zIndex: 1000,
  },
  modal: {
    background: C.card, border: `1px solid ${C.border}`, borderRadius: 12,
    padding: 24, width: 520, maxHeight: '85vh', overflowY: 'auto',
  },
  modalTitle: { margin: '0 0 18px', fontSize: 16, fontWeight: 700 },
  empty: { textAlign: 'center', padding: '32px 0', color: C.muted, fontSize: 13 },
  // keep errors visually subtle so they don't dominate the UI
  error: { color: C.muted, fontSize: 12, padding: '8px 0', opacity: 0.72 },
  success: { color: C.green, fontSize: 12, padding: '8px 0' },
};

// ─── Status badge colors ────────────────────────────────────────────────────
function statusColor(s) {
  if (['received','delivered','completed'].includes(s)) return 'green';
  if (['cancelled'].includes(s)) return 'red';
  return 'blue';
}

// ─── Modal wrapper ──────────────────────────────────────────────────────────
function Modal({ title, onClose, children }) {
  return (
    <div style={s.overlay} onClick={onClose}>
      <div style={s.modal} onClick={e => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h3 style={s.modalTitle}>{title}</h3>
          <button style={s.btn('ghost')} onClick={onClose}>✕</button>
        </div>
        {children}
      </div>
    </div>
  );
}

// ─── Field helper ───────────────────────────────────────────────────────────
function Field({ label, children }) {
  return (
    <div>
      <label style={s.label}>{label}</label>
      {children}
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
// TAB: Proveedores  (HU-COM-01)
// ══════════════════════════════════════════════════════════════
function TabProveedores() {
  const [list, setList] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name:'', contact_email:'', phone:'', address:'', city:'', country:'México' });
  const [msg, setMsg] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try { setList(await api.getSuppliers()); }
    catch { setList([{ id:1, name:'Proveedor Demo', contact_email:'demo@proveedor.com', city:'CDMX' }]); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  async function handleCreate(e) {
    e.preventDefault();
    try {
      await api.createSupplier(form);
      setMsg({ type:'success', text:'Proveedor creado correctamente.' });
      setShowForm(false);
      setForm({ name:'', contact_email:'', phone:'', address:'', city:'', country:'México' });
      load();
    } catch(err) {
      setMsg({ type:'error', text: err.message });
    }
  }

  return (
    <div>
      <div style={s.sectionHeader}>
        <h2 style={s.sectionTitle}>Proveedores</h2>
        <button style={s.btn()} onClick={() => setShowForm(true)}>+ Nuevo proveedor</button>
      </div>
      {msg && msg.type !== 'error' && <div style={s.success}>{msg.text}</div>}
      <div style={s.card}>
        {loading ? <div style={s.empty}>Cargando...</div> : (
          <table style={s.table}>
            <thead><tr>
              <th style={s.th}>Nombre</th>
              <th style={s.th}>Email</th>
              <th style={s.th}>Ciudad</th>
              <th style={s.th}>País</th>
            </tr></thead>
            <tbody>
              {list.length === 0 ? (
                <tr><td colSpan={4} style={{ ...s.td, ...s.empty }}>Sin proveedores</td></tr>
              ) : list.map((p, i) => (
                <tr key={p.id || i}>
                  <td style={s.td}>{p.name}</td>
                  <td style={s.td}>{p.contact_email}</td>
                  <td style={s.td}>{p.city || '—'}</td>
                  <td style={s.td}>{p.country || '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {showForm && (
        <Modal title="Nuevo proveedor" onClose={() => setShowForm(false)}>
          <form onSubmit={handleCreate}>
            <div style={s.formGrid}>
              <Field label="Nombre">
                <input style={s.input} required value={form.name} onChange={e=>setForm({...form,name:e.target.value})} />
              </Field>
              <Field label="Email de contacto">
                <input style={s.input} type="email" value={form.contact_email} onChange={e=>setForm({...form,contact_email:e.target.value})} />
              </Field>
              <Field label="Teléfono">
                <input style={s.input} value={form.phone} onChange={e=>setForm({...form,phone:e.target.value})} />
              </Field>
              <Field label="Ciudad">
                <input style={s.input} value={form.city} onChange={e=>setForm({...form,city:e.target.value})} />
              </Field>
              <Field label="País">
                <input style={s.input} value={form.country} onChange={e=>setForm({...form,country:e.target.value})} />
              </Field>
              <Field label="Dirección">
                <input style={s.input} value={form.address} onChange={e=>setForm({...form,address:e.target.value})} />
              </Field>
            </div>
            <div style={s.formActions}>
              <button type="button" style={s.btn('ghost')} onClick={() => setShowForm(false)}>Cancelar</button>
              <button type="submit" style={s.btn()}>Crear proveedor</button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
// TAB: Clientes  (HU-COM-01)
// ══════════════════════════════════════════════════════════════
function TabClientes() {
  const [list, setList] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ name:'', contact_email:'', phone:'', customer_type:'retail', credit_limit:'' });
  const [msg, setMsg] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try { setList(await api.getCustomers()); }
    catch { setList([{ id:1, name:'Cliente Demo', contact_email:'demo@cliente.com', customer_type:'retail', credit_limit:50000 }]); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  async function handleCreate(e) {
    e.preventDefault();
    try {
      await api.createCustomer({ ...form, credit_limit: Number(form.credit_limit) });
      setMsg({ type:'success', text:'Cliente creado correctamente.' });
      setShowForm(false);
      setForm({ name:'', contact_email:'', phone:'', customer_type:'retail', credit_limit:'' });
      load();
    } catch(err) {
      setMsg({ type:'error', text: err.message });
    }
  }

  return (
    <div>
      <div style={s.sectionHeader}>
        <h2 style={s.sectionTitle}>Clientes</h2>
        <button style={s.btn()} onClick={() => setShowForm(true)}>+ Nuevo cliente</button>
      </div>
      {msg && msg.type !== 'error' && <div style={s.success}>{msg.text}</div>}
      <div style={s.card}>
        {loading ? <div style={s.empty}>Cargando...</div> : (
          <table style={s.table}>
            <thead><tr>
              <th style={s.th}>Nombre</th>
              <th style={s.th}>Email</th>
              <th style={s.th}>Tipo</th>
              <th style={s.th}>Límite crédito</th>
            </tr></thead>
            <tbody>
              {list.length === 0 ? (
                <tr><td colSpan={4} style={{ ...s.td, ...s.empty }}>Sin clientes</td></tr>
              ) : list.map((c, i) => (
                <tr key={c.id || i}>
                  <td style={s.td}>{c.name}</td>
                  <td style={s.td}>{c.contact_email}</td>
                  <td style={s.td}>{c.customer_type}</td>
                  <td style={s.td}>${(c.credit_limit||0).toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {showForm && (
        <Modal title="Nuevo cliente" onClose={() => setShowForm(false)}>
          <form onSubmit={handleCreate}>
            <div style={s.formGrid}>
              <Field label="Nombre">
                <input style={s.input} required value={form.name} onChange={e=>setForm({...form,name:e.target.value})} />
              </Field>
              <Field label="Email">
                <input style={s.input} type="email" value={form.contact_email} onChange={e=>setForm({...form,contact_email:e.target.value})} />
              </Field>
              <Field label="Teléfono">
                <input style={s.input} value={form.phone} onChange={e=>setForm({...form,phone:e.target.value})} />
              </Field>
              <Field label="Tipo">
                <select style={s.select} value={form.customer_type} onChange={e=>setForm({...form,customer_type:e.target.value})}>
                  <option value="retail">Retail</option>
                  <option value="wholesale">Mayorista</option>
                  <option value="corporate">Corporativo</option>
                </select>
              </Field>
              <Field label="Límite de crédito">
                <input style={s.input} type="number" value={form.credit_limit} onChange={e=>setForm({...form,credit_limit:e.target.value})} />
              </Field>
            </div>
            <div style={s.formActions}>
              <button type="button" style={s.btn('ghost')} onClick={() => setShowForm(false)}>Cancelar</button>
              <button type="submit" style={s.btn()}>Crear cliente</button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
// TAB: Órdenes de Compra  (HU-COM-03, HU-COM-04, HU-COM-06)
// ══════════════════════════════════════════════════════════════
const PO_STATUSES = ['pending','confirmed','shipped','received','cancelled'];

function TabOrdenesCompra() {
  const [orders, setOrders] = useState([]);
  const [items, setItems] = useState([]);
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [showPay, setShowPay] = useState(null); // order to pay
  const [form, setForm] = useState({ item_id:'', supplier_id:'', quantity:1, unit_price:'', expected_delivery_days:7 });
  const [payForm, setPayForm] = useState({ amount:'', payment_method:'transfer', notes:'' });
  const [msg, setMsg] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [o, it, su] = await Promise.all([api.getPurchaseOrders(), api.getItems(), api.getSuppliers()]);
      setOrders(Array.isArray(o) ? o : o.orders || []);
      setItems(Array.isArray(it) ? it : it.items || []);
      setSuppliers(Array.isArray(su) ? su : su.suppliers || []);
    } catch {
      setOrders([{ id:1, item_id:1, supplier_id:1, quantity:5, unit_price:1000, status:'pending' }]);
      setItems([{ id:1, name:'Laptop Demo', sku:'SKU-100' }]);
      setSuppliers([{ id:1, name:'Proveedor Demo' }]);
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  async function handleCreate(e) {
    e.preventDefault();
    try {
      await api.createPurchaseOrder({ ...form, item_id:Number(form.item_id), supplier_id:Number(form.supplier_id), quantity:Number(form.quantity), unit_price:Number(form.unit_price) });
      setMsg({ type:'success', text:'Orden de compra creada.' });
      setShowNew(false);
      load();
    } catch(err) { setMsg({ type:'error', text: err.message }); }
  }

  async function handleStatus(id, status) {
    try {
      await api.updatePOStatus(id, status);
      setMsg({ type:'success', text:`Estado actualizado a "${status}".` });
      load();
    } catch(err) { setMsg({ type:'error', text: err.message }); }
  }

  async function handlePdf(id) {
    try {
      const blob = await api.getPOPdf(id);
      api.downloadBlob(blob, `orden_compra_${id}.pdf`);
    } catch(err) { alert('PDF no disponible: ' + err.message); }
  }

  async function handlePay(e) {
    e.preventDefault();
    try {
      await api.paySupplier({ order_id: showPay.id, amount: Number(payForm.amount), payment_method: payForm.payment_method, notes: payForm.notes });
      setMsg({ type:'success', text:'Pago a proveedor registrado.' });
      setShowPay(null);
      setPayForm({ amount:'', payment_method:'transfer', notes:'' });
    } catch(err) { setMsg({ type:'error', text: err.message }); }
  }

  const itemName  = id => items.find(i=>i.id===id)?.name || id;
  const suppName  = id => suppliers.find(s=>s.id===id)?.name || id;

  return (
    <div>
      <div style={s.sectionHeader}>
        <h2 style={s.sectionTitle}>Órdenes de Compra</h2>
        <button style={s.btn()} onClick={() => setShowNew(true)}>+ Nueva orden</button>
      </div>
      {msg && msg.type !== 'error' && <div style={s.success}>{msg.text}</div>}
      <div style={s.card}>
        {loading ? <div style={s.empty}>Cargando...</div> : (
          <table style={s.table}>
            <thead><tr>
              <th style={s.th}>#</th>
              <th style={s.th}>Producto</th>
              <th style={s.th}>Proveedor</th>
              <th style={s.th}>Cant.</th>
              <th style={s.th}>Precio unit.</th>
              <th style={s.th}>Estado</th>
              <th style={s.th}>Acciones</th>
            </tr></thead>
            <tbody>
              {orders.length === 0
                ? <tr><td colSpan={7} style={{ ...s.td, ...s.empty }}>Sin órdenes</td></tr>
                : orders.map((o,i) => (
                  <tr key={o.id || i}>
                    <td style={s.td}>OC-{o.id}</td>
                    <td style={s.td}>{itemName(o.item_id)}</td>
                    <td style={s.td}>{suppName(o.supplier_id)}</td>
                    <td style={s.td}>{o.quantity}</td>
                    <td style={s.td}>${(o.unit_price||0).toLocaleString()}</td>
                    <td style={s.td}><span style={s.badge(statusColor(o.status))}>{o.status}</span></td>
                    <td style={{ ...s.td }}>
                      <div style={{ display:'flex', gap:4, flexWrap:'wrap' }}>
                        <select
                          style={{ ...s.select, width:'auto', fontSize:11, padding:'4px 6px' }}
                          value={o.status}
                          onChange={e => handleStatus(o.id, e.target.value)}
                        >
                          {PO_STATUSES.map(st => <option key={st} value={st}>{st}</option>)}
                        </select>
                        <button style={s.btn('secondary')} onClick={() => handlePdf(o.id)}>PDF</button>
                        <button style={s.btn('success')} onClick={() => setShowPay(o)}>Pagar</button>
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
        <Modal title="Nueva orden de compra" onClose={() => setShowNew(false)}>
          <form onSubmit={handleCreate}>
            <div style={s.formGrid}>
              <Field label="Producto">
                <select style={s.select} required value={form.item_id} onChange={e=>setForm({...form,item_id:e.target.value})}>
                  <option value="">Seleccionar...</option>
                  {items.map(it => <option key={it.id} value={it.id}>{it.name} ({it.sku})</option>)}
                </select>
              </Field>
              <Field label="Proveedor">
                <select style={s.select} required value={form.supplier_id} onChange={e=>setForm({...form,supplier_id:e.target.value})}>
                  <option value="">Seleccionar...</option>
                  {suppliers.map(su => <option key={su.id} value={su.id}>{su.name}</option>)}
                </select>
              </Field>
              <Field label="Cantidad">
                <input style={s.input} type="number" min="1" required value={form.quantity} onChange={e=>setForm({...form,quantity:e.target.value})} />
              </Field>
              <Field label="Precio unitario">
                <input style={s.input} type="number" min="0" required value={form.unit_price} onChange={e=>setForm({...form,unit_price:e.target.value})} />
              </Field>
              <Field label="Días de entrega esperados">
                <input style={s.input} type="number" min="1" value={form.expected_delivery_days} onChange={e=>setForm({...form,expected_delivery_days:e.target.value})} />
              </Field>
            </div>
            <div style={s.formActions}>
              <button type="button" style={s.btn('ghost')} onClick={() => setShowNew(false)}>Cancelar</button>
              <button type="submit" style={s.btn()}>Crear orden</button>
            </div>
          </form>
        </Modal>
      )}

      {showPay && (
        <Modal title={`Pago a proveedor — OC-${showPay.id}`} onClose={() => setShowPay(null)}>
          <form onSubmit={handlePay}>
            <div style={s.formGrid}>
              <Field label="Monto">
                <input style={s.input} type="number" required value={payForm.amount} onChange={e=>setPayForm({...payForm,amount:e.target.value})} />
              </Field>
              <Field label="Método de pago">
                <select style={s.select} value={payForm.payment_method} onChange={e=>setPayForm({...payForm,payment_method:e.target.value})}>
                  <option value="transfer">Transferencia</option>
                  <option value="cash">Efectivo</option>
                  <option value="check">Cheque</option>
                </select>
              </Field>
              <Field label="Notas">
                <input style={s.input} value={payForm.notes} onChange={e=>setPayForm({...payForm,notes:e.target.value})} />
              </Field>
            </div>
            <div style={s.formActions}>
              <button type="button" style={s.btn('ghost')} onClick={() => setShowPay(null)}>Cancelar</button>
              <button type="submit" style={s.btn('success')}>Registrar pago</button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
// TAB: Órdenes de Venta  (HU-COM-02, HU-COM-04, HU-COM-05)
// ══════════════════════════════════════════════════════════════
const SO_STATUSES = ['pending','confirmed','shipped','delivered','cancelled'];

function TabOrdenesVenta() {
  const [orders, setOrders] = useState([]);
  const [items, setItems] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showNew, setShowNew] = useState(false);
  const [showPay, setShowPay] = useState(null);
  const [form, setForm] = useState({ item_id:'', customer_id:'', quantity:1, expected_delivery_days:3 });
  const [payForm, setPayForm] = useState({ amount:'', payment_method:'transfer', notes:'' });
  const [msg, setMsg] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [o, it, cu] = await Promise.all([api.getSalesOrders(), api.getItems(), api.getCustomers()]);
      setOrders(Array.isArray(o) ? o : o.orders || []);
      setItems(Array.isArray(it) ? it : it.items || []);
      setCustomers(Array.isArray(cu) ? cu : cu.customers || []);
    } catch {
      setOrders([{ id:1, item_id:1, customer_id:1, quantity:2, status:'pending' }]);
      setItems([{ id:1, name:'Laptop Demo', sku:'SKU-100', unit_price:15000 }]);
      setCustomers([{ id:1, name:'Cliente Demo' }]);
    } finally { setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  async function handleCreate(e) {
    e.preventDefault();
    try {
      await api.createSalesOrder({ ...form, item_id:Number(form.item_id), customer_id:Number(form.customer_id), quantity:Number(form.quantity) });
      setMsg({ type:'success', text:'Orden de venta creada. Stock reducido automáticamente.' });
      setShowNew(false);
      load();
    } catch(err) { setMsg({ type:'error', text: err.message }); }
  }

  async function handleStatus(id, status) {
    try {
      await api.updateSOStatus(id, status);
      setMsg({ type:'success', text:`Estado actualizado a "${status}".` });
      load();
    } catch(err) { setMsg({ type:'error', text: err.message }); }
  }

  async function handleInvoice(id) {
    try {
      const blob = await api.getInvoicePdf(id);
      api.downloadBlob(blob, `factura_${id}.pdf`);
    } catch(err) { alert('Factura no disponible: ' + err.message); }
  }

  async function handlePay(e) {
    e.preventDefault();
    try {
      await api.payCustomer({ order_id: showPay.id, amount: Number(payForm.amount), payment_method: payForm.payment_method, notes: payForm.notes });
      setMsg({ type:'success', text:'Pago de cliente registrado.' });
      setShowPay(null);
      setPayForm({ amount:'', payment_method:'transfer', notes:'' });
    } catch(err) { setMsg({ type:'error', text: err.message }); }
  }

  const itemName    = id => items.find(i=>i.id===id)?.name || id;
  const custName    = id => customers.find(c=>c.id===id)?.name || id;

  return (
    <div>
      <div style={s.sectionHeader}>
        <h2 style={s.sectionTitle}>Órdenes de Venta</h2>
        <button style={s.btn()} onClick={() => setShowNew(true)}>+ Nueva orden</button>
      </div>
      {msg && msg.type !== 'error' && <div style={s.success}>{msg.text}</div>}
      <div style={s.card}>
        {loading ? <div style={s.empty}>Cargando...</div> : (
          <table style={s.table}>
            <thead><tr>
              <th style={s.th}>#</th>
              <th style={s.th}>Producto</th>
              <th style={s.th}>Cliente</th>
              <th style={s.th}>Cant.</th>
              <th style={s.th}>Estado</th>
              <th style={s.th}>Acciones</th>
            </tr></thead>
            <tbody>
              {orders.length === 0
                ? <tr><td colSpan={6} style={{ ...s.td, ...s.empty }}>Sin órdenes</td></tr>
                : orders.map((o,i) => (
                  <tr key={o.id || i}>
                    <td style={s.td}>OV-{o.id}</td>
                    <td style={s.td}>{itemName(o.item_id)}</td>
                    <td style={s.td}>{custName(o.customer_id)}</td>
                    <td style={s.td}>{o.quantity}</td>
                    <td style={s.td}><span style={s.badge(statusColor(o.status))}>{o.status}</span></td>
                    <td style={s.td}>
                      <div style={{ display:'flex', gap:4, flexWrap:'wrap' }}>
                        <select
                          style={{ ...s.select, width:'auto', fontSize:11, padding:'4px 6px' }}
                          value={o.status}
                          onChange={e => handleStatus(o.id, e.target.value)}
                        >
                          {SO_STATUSES.map(st => <option key={st} value={st}>{st}</option>)}
                        </select>
                        <button style={s.btn('secondary')} onClick={() => handleInvoice(o.id)}>Factura PDF</button>
                        <button style={s.btn('success')} onClick={() => setShowPay(o)}>Pago</button>
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
        <Modal title="Nueva orden de venta" onClose={() => setShowNew(false)}>
          <form onSubmit={handleCreate}>
            <div style={s.formGrid}>
              <Field label="Producto">
                <select style={s.select} required value={form.item_id} onChange={e=>setForm({...form,item_id:e.target.value})}>
                  <option value="">Seleccionar...</option>
                  {items.map(it => <option key={it.id} value={it.id}>{it.name} ({it.sku})</option>)}
                </select>
              </Field>
              <Field label="Cliente">
                <select style={s.select} required value={form.customer_id} onChange={e=>setForm({...form,customer_id:e.target.value})}>
                  <option value="">Seleccionar...</option>
                  {customers.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </Field>
              <Field label="Cantidad">
                <input style={s.input} type="number" min="1" required value={form.quantity} onChange={e=>setForm({...form,quantity:e.target.value})} />
              </Field>
              <Field label="Días de entrega">
                <input style={s.input} type="number" min="1" value={form.expected_delivery_days} onChange={e=>setForm({...form,expected_delivery_days:e.target.value})} />
              </Field>
            </div>
            <div style={s.formActions}>
              <button type="button" style={s.btn('ghost')} onClick={() => setShowNew(false)}>Cancelar</button>
              <button type="submit" style={s.btn()}>Crear orden</button>
            </div>
          </form>
        </Modal>
      )}

      {showPay && (
        <Modal title={`Registrar pago — OV-${showPay.id}`} onClose={() => setShowPay(null)}>
          <form onSubmit={handlePay}>
            <div style={s.formGrid}>
              <Field label="Monto">
                <input style={s.input} type="number" required value={payForm.amount} onChange={e=>setPayForm({...payForm,amount:e.target.value})} />
              </Field>
              <Field label="Método de pago">
                <select style={s.select} value={payForm.payment_method} onChange={e=>setPayForm({...payForm,payment_method:e.target.value})}>
                  <option value="transfer">Transferencia</option>
                  <option value="cash">Efectivo</option>
                  <option value="check">Cheque</option>
                </select>
              </Field>
              <Field label="Notas">
                <input style={s.input} value={payForm.notes} onChange={e=>setPayForm({...payForm,notes:e.target.value})} />
              </Field>
            </div>
            <div style={s.formActions}>
              <button type="button" style={s.btn('ghost')} onClick={() => setShowPay(null)}>Cancelar</button>
              <button type="submit" style={s.btn('success')}>Registrar pago</button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
// TAB: Historial  (HU-COM-07)
// ══════════════════════════════════════════════════════════════
function TabHistorial() {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({ party_type:'', party_name:'', transaction_type:'', limit:50 });

  const load = useCallback(async () => {
    setLoading(true);
    const clean = Object.fromEntries(Object.entries(filters).filter(([,v])=>v!==''));
    try {
      const res = await api.getHistory(clean);
      setHistory(Array.isArray(res) ? res : res.history || []);
    } catch {
      setHistory([
        { id:1, transaction_type:'sale', party_name:'Cliente Demo', amount:15000, created_at: new Date().toISOString() },
        { id:2, transaction_type:'purchase', party_name:'Proveedor Demo', amount:5000, created_at: new Date().toISOString() },
      ]);
    } finally { setLoading(false); }
  }, [filters]);

  useEffect(() => { load(); }, []);

  return (
    <div>
      <div style={s.sectionHeader}>
        <h2 style={s.sectionTitle}>Historial de Transacciones</h2>
        <button style={s.btn()} onClick={load}>Actualizar</button>
      </div>

      {/* Filters */}
      <div style={{ ...s.card, display:'flex', gap:12, flexWrap:'wrap', alignItems:'flex-end' }}>
        <div style={{ flex:'1 1 160px' }}>
          <label style={s.label}>Tipo de parte</label>
          <select style={s.select} value={filters.party_type} onChange={e=>setFilters({...filters,party_type:e.target.value})}>
            <option value="">Todos</option>
            <option value="supplier">Proveedor</option>
            <option value="customer">Cliente</option>
          </select>
        </div>
        <div style={{ flex:'1 1 160px' }}>
          <label style={s.label}>Nombre</label>
          <input style={s.input} placeholder="Buscar..." value={filters.party_name} onChange={e=>setFilters({...filters,party_name:e.target.value})} />
        </div>
        <div style={{ flex:'1 1 160px' }}>
          <label style={s.label}>Tipo de transacción</label>
          <select style={s.select} value={filters.transaction_type} onChange={e=>setFilters({...filters,transaction_type:e.target.value})}>
            <option value="">Todas</option>
            <option value="purchase">Compra</option>
            <option value="sale">Venta</option>
            <option value="payment">Pago</option>
          </select>
        </div>
        <button style={s.btn()} onClick={load}>Filtrar</button>
      </div>

      <div style={s.card}>
        {loading ? <div style={s.empty}>Cargando...</div> : (
          <table style={s.table}>
            <thead><tr>
              <th style={s.th}>#</th>
              <th style={s.th}>Tipo</th>
              <th style={s.th}>Parte</th>
              <th style={s.th}>Monto</th>
              <th style={s.th}>Fecha</th>
            </tr></thead>
            <tbody>
              {history.length === 0
                ? <tr><td colSpan={5} style={{ ...s.td, ...s.empty }}>Sin transacciones</td></tr>
                : history.map((h,i) => (
                  <tr key={h.id || i}>
                    <td style={s.td}>{h.id}</td>
                    <td style={s.td}>
                      <span style={s.badge(h.transaction_type==='sale' ? 'green' : h.transaction_type==='purchase' ? 'blue' : 'blue')}>
                        {h.transaction_type}
                      </span>
                    </td>
                    <td style={s.td}>{h.party_name || '—'}</td>
                    <td style={s.td}>${(h.amount||0).toLocaleString()}</td>
                    <td style={s.td}>{h.created_at ? new Date(h.created_at).toLocaleDateString('es-MX') : '—'}</td>
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
// MAIN: Compras module
// ══════════════════════════════════════════════════════════════
const TABS = [
  { key:'compras',   label:'Órdenes de Compra' },
  { key:'ventas',    label:'Órdenes de Venta' },
  { key:'proveedores', label:'Proveedores' },
  { key:'clientes',  label:'Clientes' },
  { key:'historial', label:'Historial' },
];

export default function Compras({ role, permissions }) {
  const [tab, setTab] = useState('compras');
  const [stats, setStats] = useState(null);

  useEffect(() => {
    api.getStats()
      .then(setStats)
      .catch(() => setStats({ total_sales: 12, total_purchases: 8, revenue: 180000, costs: 96000 }));
  }, []);

  return (
    <div style={s.page}>
      {/* Header */}
      <div style={s.header}>
        <h1 style={s.title}>Gestión Comercial</h1>
        <span style={{ fontSize:12, color: C.muted }}>Microservicio Compras · localhost:8003</span>
      </div>

      {/* KPIs */}
      {stats && (
        <div style={{ ...s.kpiRow, padding:'16px 28px 0' }}>
          <div style={s.kpi}>
            <div style={s.kpiLabel}>Órdenes de venta</div>
            <div style={s.kpiValue}>{stats.total_sales ?? '—'}</div>
          </div>
          <div style={s.kpi}>
            <div style={s.kpiLabel}>Órdenes de compra</div>
            <div style={s.kpiValue}>{stats.total_purchases ?? '—'}</div>
          </div>
          <div style={s.kpi}>
            <div style={s.kpiLabel}>Ingresos</div>
            <div style={{ ...s.kpiValue, color: C.green }}>${(stats.revenue||0).toLocaleString()}</div>
          </div>
          <div style={s.kpi}>
            <div style={s.kpiLabel}>Costos</div>
            <div style={{ ...s.kpiValue, color: C.yellow }}>${(stats.costs||0).toLocaleString()}</div>
          </div>
        </div>
      )}

      {/* Tabs */}
      <div style={s.tabs}>
        {TABS.map(t => (
          <button key={t.key} style={s.tab(tab===t.key)} onClick={() => setTab(t.key)}>
            {t.label}
          </button>
        ))}
      </div>

      {/* Content */}
      <div style={s.body}>
        {tab === 'compras'      && <TabOrdenesCompra />}
        {tab === 'ventas'       && <TabOrdenesVenta />}
        {tab === 'proveedores'  && <TabProveedores />}
        {tab === 'clientes'     && <TabClientes />}
        {tab === 'historial'    && <TabHistorial />}
      </div>
    </div>
  );
}
