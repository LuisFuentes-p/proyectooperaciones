import React, { useEffect, useState, useCallback } from 'react';
import * as api from '../api/finanzasApi';

// ─── Design tokens ───────────────────────────────────────────────────────────
const C = {
  bg:      '#0f1117',
  surface: '#181c27',
  card:    '#1e2333',
  border:  '#2a3045',
  accent:  '#4f8ef7',
  accentLo:'#1a2d54',
  green:   '#22c55e',
  greenLo: '#14321f',
  red:     '#f43f5e',
  redLo:   '#3a1020',
  yellow:  '#f59e0b',
  purple:  '#a78bfa',
  purpleLo:'#2d1b69',
  text:    '#e8ecf4',
  muted:   '#6b7896',
};

const s = {
  page: {
    background: C.bg,
    minHeight: '100vh',
    fontFamily: "'IBM Plex Sans', 'Segoe UI', sans-serif",
    color: C.text,
  },
  header: {
    background: C.surface, borderBottom: `1px solid ${C.border}`,
    padding: '18px 28px', display: 'flex', justifyContent: 'space-between', alignItems: 'center',
  },
  titleWrap: { display: 'flex', alignItems: 'center', gap: 12 },
  dot: (color) => ({
    width: 8, height: 8, borderRadius: '50%', background: color,
    boxShadow: `0 0 8px ${color}`,
  }),
  title: { margin: 0, fontSize: 20, fontWeight: 800, letterSpacing: '-0.3px' },
  subtitle: { fontSize: 11, color: C.muted, marginTop: 2 },
  tabs: {
    display: 'flex', gap: 4, background: C.bg, padding: '10px 28px',
    borderBottom: `1px solid ${C.border}`,
  },
  tab: (active) => ({
    padding: '7px 15px', borderRadius: 7, border: 'none', cursor: 'pointer',
    fontSize: 12, fontWeight: 700, letterSpacing: 0.3,
    background: active ? C.accent : 'transparent',
    color: active ? '#041126' : C.muted,
    transition: 'all .15s',
  }),
  body: { padding: '24px 28px' },
  kpiRow: { display: 'flex', gap: 12, marginBottom: 20, flexWrap: 'wrap' },
  kpi: (accent) => ({
    background: C.card, border: `1px solid ${C.border}`, borderRadius: 10,
    padding: '14px 18px', flex: '1 1 140px', borderLeft: `3px solid ${accent || C.accent}`,
  }),
  kpiLabel: { fontSize: 10, color: C.muted, textTransform: 'uppercase', letterSpacing: 1.2, marginBottom: 6 },
  kpiValue: (color) => ({ fontSize: 24, fontWeight: 700, color: color || C.accent, fontFamily: 'inherit' }),
  card: {
    background: C.card, border: `1px solid ${C.border}`, borderRadius: 10,
    padding: 18, marginBottom: 16,
  },
  sectionHeader: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14,
  },
  sectionTitle: { fontSize: 13, fontWeight: 800, margin: 0, textTransform: 'uppercase', letterSpacing: 1, color: C.muted },
  btn: (variant = 'primary') => ({
    padding: '7px 14px', borderRadius: 7, border: 'none', cursor: 'pointer',
    fontSize: 11, fontWeight: 700, letterSpacing: 0.5,
    background: variant === 'primary'  ? C.accent
              : variant === 'danger'   ? C.red
              : variant === 'success'  ? C.green
              : variant === 'purple'   ? C.purple
              : variant === 'ghost'    ? 'transparent'
              : C.border,
    color: variant === 'ghost' ? C.muted : '#041126',
    transition: 'opacity .15s',
  }),
  table: { width: '100%', borderCollapse: 'collapse', fontSize: 12 },
  th: {
    textAlign: 'left', padding: '7px 10px', color: C.muted,
    fontSize: 10, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.8,
    borderBottom: `1px solid ${C.border}`,
  },
  td: { padding: '10px 10px', borderBottom: `1px solid ${C.border}22` },
  badge: (color) => ({
    display: 'inline-block', padding: '2px 8px', borderRadius: 999, fontSize: 10, fontWeight: 700,
    letterSpacing: 0.5, textTransform: 'uppercase',
    background: color === 'green'  ? C.greenLo
              : color === 'red'    ? C.redLo
              : color === 'purple' ? C.purpleLo
              : C.accentLo,
    color: color === 'green'  ? C.green
         : color === 'red'    ? C.red
         : color === 'purple' ? C.purple
         : C.accent,
    border: `1px solid ${
      color === 'green' ? C.green + '44' : color === 'red' ? C.red + '44' :
      color === 'purple' ? C.purple + '44' : C.accent + '44'
    }`,
  }),
  input: {
    width: '100%', background: C.surface, border: `1px solid ${C.border}`, borderRadius: 7,
    padding: '7px 10px', color: C.text, fontSize: 12, outline: 'none',
    boxSizing: 'border-box', fontFamily: 'inherit',
  },
  label: {
    display: 'block', fontSize: 10, color: C.muted, marginBottom: 4,
    fontWeight: 700, textTransform: 'uppercase', letterSpacing: 0.8,
  },
  overlay: {
    position: 'fixed', inset: 0, background: 'rgba(0,0,0,.75)',
    display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000,
  },
  modal: {
    background: C.card, border: `1px solid ${C.border}`, borderRadius: 10,
    padding: 24, width: 480, maxHeight: '80vh', overflowY: 'auto',
  },
  empty: { textAlign: 'center', padding: '32px 0', color: C.muted, fontSize: 12 },
  success: {
    color: C.green, fontSize: 11, padding: '8px 12px', background: C.greenLo,
    border: `1px solid ${C.green}44`, borderRadius: 7, marginBottom: 12,
  },
  permTag: (has) => ({
    display: 'inline-block', padding: '2px 8px', borderRadius: 999, fontSize: 10,
    fontWeight: 700, margin: '2px 3px',
    background: has ? C.greenLo : C.surface,
    color: has ? C.green : C.muted,
    border: `1px solid ${has ? C.green + '44' : C.border}`,
  }),
};

// ─── Helpers ─────────────────────────────────────────────────────────────────
function Modal({ title, onClose, children }) {
  return (
    <div style={s.overlay} onClick={onClose}>
      <div style={s.modal} onClick={e => e.stopPropagation()}>
        <div style={{ display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:16 }}>
          <span style={{ fontSize:14, fontWeight:700 }}>{title}</span>
          <button style={s.btn('ghost')} onClick={onClose}>✕</button>
        </div>
        {children}
      </div>
    </div>
  );
}

function Field({ label, children }) {
  return (
    <div style={{ marginBottom: 12 }}>
      <label style={s.label}>{label}</label>
      {children}
    </div>
  );
}

function formatBytes(b) {
  if (!b) return '—';
  if (b < 1024) return `${b} B`;
  if (b < 1024*1024) return `${(b/1024).toFixed(1)} KB`;
  return `${(b/1024/1024).toFixed(1)} MB`;
}

const ALL_AREAS = ['finanzas','compras','inventario','devoluciones','usuarios'];

// ══════════════════════════════════════════════════════════════
// TAB: Dashboard financiero  (HU-FIN-01, HU-FIN-02)
// ══════════════════════════════════════════════════════════════
function TabDashboard({ currentUser }) {
  const [health, setHealth] = useState(null);
  const [generating, setGenerating] = useState(false);
  const [msg, setMsg] = useState(null);

  useEffect(() => {
    api.getHealth().then(setHealth).catch(() => setHealth({ status: 'unknown' }));
  }, []);

  async function handleGenerate() {
    setGenerating(true); setMsg(null);
    try {
      const res = await api.generateReport(currentUser?.username || 'admin');
      setMsg({ type:'success', text: `Reporte "${res.title}" generado. Tamaño: ${formatBytes(res.file_size)}` });
    } catch(err) {
      setMsg({ type:'error', text: err.message });
    } finally { setGenerating(false); }
  }

  async function handleDirectPdf() {
    try {
      const blob = await api.getReportPdfDirect();
      api.downloadBlob(blob, 'ingresos_totales.pdf');
    } catch(err) {
      setMsg({ type:'error', text: 'PDF no disponible: ' + err.message });
    }
  }

  return (
    <div>
      {/* KPIs */}
      <div style={s.kpiRow}>
        <div style={s.kpi(C.green)}>
          <div style={s.kpiLabel}>Estado del servicio</div>
          <div style={s.kpiValue(health?.status === 'ok' ? C.green : C.red)}>
            {health ? health.status.toUpperCase() : '...'}
          </div>
        </div>
        <div style={s.kpi(C.accent)}>
          <div style={s.kpiLabel}>Puerto</div>
          <div style={s.kpiValue(C.accent)}>8000</div>
        </div>
        <div style={s.kpi(C.purple)}>
          <div style={s.kpiLabel}>Usuario activo</div>
          <div style={{ ...s.kpiValue(C.purple), fontSize: 16 }}>{currentUser?.display_name || '—'}</div>
        </div>
        <div style={s.kpi(C.yellow)}>
          <div style={s.kpiLabel}>Rol</div>
          <div style={{ ...s.kpiValue(C.yellow), fontSize: 16 }}>{currentUser?.role || '—'}</div>
        </div>
      </div>

      {/* Permisos del usuario */}
      {currentUser && (
        <div style={s.card}>
          <div style={s.sectionHeader}>
            <span style={s.sectionTitle}>Permisos del usuario</span>
          </div>
          <div style={{ display:'flex', flexWrap:'wrap', gap:4 }}>
            {ALL_AREAS.map(area => (
              <span key={area} style={s.permTag(currentUser.permissions?.includes(area))}>
                {currentUser.permissions?.includes(area) ? '✓' : '✗'} {area}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Generar reporte */}
      <div style={s.card}>
        <div style={s.sectionHeader}>
          <span style={s.sectionTitle}>Reporte de Ingresos Totales</span>
        </div>
        <p style={{ fontSize:12, color:C.muted, marginBottom:14, lineHeight:1.6 }}>
          Genera un PDF financiero con métricas de ingresos, fuentes de datos, eventos relacionados,
          fórmulas de cálculo y uso empresarial. El reporte se almacena en base de datos y queda
          disponible en el historial.
        </p>
        {msg && msg.type !== 'error' && <div style={s.success}>{msg.text}</div>}
        <div style={{ display:'flex', gap:8 }}>
          <button style={s.btn()} onClick={handleGenerate} disabled={generating}>
            {generating ? 'Generando...' : '⊕ Generar y guardar reporte'}
          </button>
          <button style={s.btn('ghost')} onClick={handleDirectPdf}>
            ↓ PDF directo (sin guardar)
          </button>
        </div>
      </div>

      {/* Architecture info */}
      <div style={s.card}>
        <div style={s.sectionHeader}>
          <span style={s.sectionTitle}>Arquitectura financiera</span>
        </div>
        <div style={{ display:'flex', gap: 8, alignItems:'center', flexWrap:'wrap' }}>
          {['Frontend React', 'FastAPI Finanzas :8000', 'PostgreSQL', 'ReportLab PDF Engine'].map((node, i, arr) => (
            <React.Fragment key={node}>
              <div style={{
                background: C.surface, border: `1px solid ${C.border}`, borderRadius: 4,
                padding: '6px 12px', fontSize: 11, color: C.accent,
              }}>{node}</div>
              {i < arr.length - 1 && <span style={{ color: C.muted }}>→</span>}
            </React.Fragment>
          ))}
        </div>
      </div>
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
// TAB: Historial de reportes  (HU-FIN-03)
// ══════════════════════════════════════════════════════════════
function TabReportes({ currentUser }) {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState(null);

  const load = useCallback(async () => {
    setLoading(true); setMsg(null);
    try {
      const res = await api.getTracking(currentUser?.username || 'admin');
      setReports(Array.isArray(res) ? res : res.items || []);
    } catch(err) {
      setMsg({ type:'error', text: err.message });
      setReports([
        { id:1, report_key:'ingresos_totales', title:'Ingresos Totales', filename:'ingresos_totales.pdf', file_size:15234, content_type:'application/pdf' },
      ]);
    } finally { setLoading(false); }
  }, [currentUser]);

  useEffect(() => { load(); }, [load]);

  async function handleDownload(r) {
    try {
      const blob = await api.downloadReport(currentUser?.username || 'admin', r.id);
      api.downloadBlob(blob, r.filename || `reporte_${r.id}.pdf`);
    } catch(err) {
      setMsg({ type:'error', text: 'No se pudo descargar: ' + err.message });
    }
  }

  async function handleDelete(r) {
    if (!window.confirm(`¿Eliminar reporte "${r.title}"?`)) return;
    try {
      await api.deleteReport(currentUser?.username || 'admin', r.id);
      setMsg({ type:'success', text: 'Reporte eliminado.' });
      load();
    } catch(err) {
      setMsg({ type:'error', text: err.message });
    }
  }

  return (
    <div>
      <div style={s.sectionHeader}>
        <span style={{ fontSize:13, fontWeight:700 }}>Historial de Reportes</span>
        <button style={s.btn()} onClick={load}>↺ Actualizar</button>
      </div>
      {msg && msg.type !== 'error' && <div style={s.success}>{msg.text}</div>}
      <div style={s.card}>
        {loading ? <div style={s.empty}>Cargando...</div> : (
          <table style={s.table}>
            <thead><tr>
              <th style={s.th}>#</th>
              <th style={s.th}>Reporte</th>
              <th style={s.th}>Archivo</th>
              <th style={s.th}>Tamaño</th>
              <th style={s.th}>Tipo</th>
              <th style={s.th}>Acciones</th>
            </tr></thead>
            <tbody>
              {reports.length === 0
                ? <tr><td colSpan={6} style={{ ...s.td, ...s.empty }}>Sin reportes generados</td></tr>
                : reports.map((r, i) => (
                  <tr key={r.id || i}>
                    <td style={s.td}>{r.id}</td>
                    <td style={s.td}>{r.title}</td>
                    <td style={{ ...s.td, color: C.accent }}>{r.filename}</td>
                    <td style={s.td}>{formatBytes(r.file_size)}</td>
                    <td style={s.td}><span style={s.badge('purple')}>PDF</span></td>
                    <td style={s.td}>
                      <div style={{ display:'flex', gap:6 }}>
                        <button style={s.btn('success')} onClick={() => handleDownload(r)}>↓ Descargar</button>
                        <button style={s.btn('danger')} onClick={() => handleDelete(r)}>✕ Eliminar</button>
                      </div>
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
// TAB: Usuarios y permisos  (HU-AUTH-02, HU-AUTH-03)
// ══════════════════════════════════════════════════════════════
function TabUsuarios({ currentUser }) {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState(null);
  const [msg, setMsg] = useState(null);

  const canSeeUsers = currentUser?.permissions?.includes('usuarios');

  const load = useCallback(async () => {
    if (!canSeeUsers) return;
    setLoading(true); setMsg(null);
    try {
      const res = await api.getUsers(currentUser?.username || 'admin');
      setUsers(Array.isArray(res) ? res : res.users || []);
    } catch(err) {
      setMsg({ type:'error', text: err.message });
      setUsers([
        { id:1, username:'admin',     display_name:'Administrador',     role:'admin',     permissions:['finanzas','compras','inventario','devoluciones','usuarios'] },
        { id:2, username:'compras',   display_name:'Jefe de Compras',   role:'compras',   permissions:['finanzas','compras'] },
        { id:3, username:'inventario',display_name:'Jefe de Inventario',role:'inventario',permissions:['finanzas','inventario'] },
        { id:4, username:'auditor',   display_name:'Auditor Operativo', role:'auditor',   permissions:['finanzas','devoluciones'] },
        { id:5, username:'viewer',    display_name:'Consulta General',  role:'viewer',    permissions:['finanzas'] },
      ]);
    } finally { setLoading(false); }
  }, [currentUser, canSeeUsers]);

  useEffect(() => { load(); }, [load]);

  async function handleSelect(u) {
    try {
      const full = await api.getUser(currentUser?.username || 'admin', u.username);
      setSelected(full);
    } catch { setSelected(u); }
  }

  if (!canSeeUsers) {
    return (
      <div style={{ ...s.card, textAlign:'center', padding:40 }}>
        <div style={{ fontSize:32, marginBottom:12 }}>🔒</div>
        <div style={{ color: C.muted, fontSize:13, fontWeight:700 }}>Acceso denegado</div>
        <div style={{ color: C.muted, fontSize:12, marginTop:6 }}>
          Se requiere permiso <span style={{ color:C.accent }}>usuarios</span> para ver esta sección.
        </div>
      </div>
    );
  }

  const roleColor = (role) =>
    role === 'admin' ? 'purple' : role === 'auditor' ? 'green' : 'blue';

  return (
    <div>
      <div style={s.sectionHeader}>
        <span style={{ fontSize:13, fontWeight:700 }}>Usuarios del sistema</span>
        <button style={s.btn()} onClick={load}>↺ Actualizar</button>
      </div>
      {msg && msg.type !== 'error' && <div style={s.success}>{msg.text}</div>}

      <div style={s.card}>
        {loading ? <div style={s.empty}>Cargando...</div> : (
          <table style={s.table}>
            <thead><tr>
              <th style={s.th}>Username</th>
              <th style={s.th}>Nombre</th>
              <th style={s.th}>Rol</th>
              <th style={s.th}>Permisos</th>
              <th style={s.th}>Detalle</th>
            </tr></thead>
            <tbody>
              {users.map((u, i) => (
                <tr key={u.id || i}>
                  <td style={{ ...s.td, color: C.accent, fontFamily:'monospace' }}>{u.username}</td>
                  <td style={s.td}>{u.display_name}</td>
                  <td style={s.td}><span style={s.badge(roleColor(u.role))}>{u.role}</span></td>
                  <td style={s.td}>
                    <div style={{ display:'flex', flexWrap:'wrap', gap:3 }}>
                      {(u.permissions || []).map(p => (
                        <span key={p} style={s.permTag(true)}>{p}</span>
                      ))}
                    </div>
                  </td>
                  <td style={s.td}>
                    <button style={s.btn('ghost')} onClick={() => handleSelect(u)}>Ver</button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {selected && (
        <Modal title={`Usuario: ${selected.username}`} onClose={() => setSelected(null)}>
          <div style={{ display:'grid', gap:12 }}>
            <Field label="ID"><div style={{ color:C.text, fontSize:13 }}>{selected.id}</div></Field>
            <Field label="Username">
              <div style={{ color:C.accent, fontFamily:'monospace', fontSize:13 }}>{selected.username}</div>
            </Field>
            <Field label="Nombre">
              <div style={{ color:C.text, fontSize:13 }}>{selected.display_name}</div>
            </Field>
            <Field label="Rol">
              <span style={s.badge(roleColor(selected.role))}>{selected.role}</span>
            </Field>
            <Field label="Permisos">
              <div style={{ display:'flex', flexWrap:'wrap', gap:4, marginTop:4 }}>
                {ALL_AREAS.map(area => (
                  <span key={area} style={s.permTag(selected.permissions?.includes(area))}>
                    {selected.permissions?.includes(area) ? '✓' : '✗'} {area}
                  </span>
                ))}
              </div>
            </Field>
          </div>
          <div style={{ display:'flex', justifyContent:'flex-end', marginTop:16 }}>
            <button style={s.btn('ghost')} onClick={() => setSelected(null)}>Cerrar</button>
          </div>
        </Modal>
      )}
    </div>
  );
}

// ══════════════════════════════════════════════════════════════
// MAIN: Finanzas module
// ══════════════════════════════════════════════════════════════
const TABS = [
  { key:'dashboard', label:'Dashboard' },
  { key:'reportes',  label:'Historial Reportes' },
  { key:'usuarios',  label:'Usuarios y Permisos' },
];

export default function Finanzas({ role, permissions }) {
  const [tab, setTab] = useState('dashboard');
  const [currentUser, setCurrentUser] = useState(null);
  const [userInput, setUserInput] = useState('admin');
  const [userError, setUserError] = useState(null);
  const [loading, setLoading] = useState(true);

  async function loadUser(username) {
    setLoading(true); setUserError(null);
    try {
      const u = await api.getMe(username);
      setCurrentUser(u);
      setUserInput(username);
    } catch(err) {
      // fallback mock user
      setCurrentUser({
        id: 1, username: 'admin', display_name: 'Administrador (local)',
        role: 'admin', permissions: ['finanzas','compras','inventario','devoluciones','usuarios'],
      });
      setUserError('Servicio no disponible, usando datos mock.');
    } finally { setLoading(false); }
  }

  useEffect(() => { loadUser('admin'); }, []);

  return (
    <div style={s.page}>
      {/* Header */}
      <div style={s.header}>
        <div style={s.titleWrap}>
          <div style={s.dot(C.green)} />
          <div>
            <h1 style={s.title}>Finanzas & Reportes</h1>
            <div style={s.subtitle}>Microservicio Finanzas · localhost:8000</div>
          </div>
        </div>

        {/* User switcher */}
        <div style={{ display:'flex', gap:8, alignItems:'center' }}>
          <span style={{ fontSize:11, color:C.muted }}>Usuario activo:</span>
          <select
            style={{ ...s.input, width:'auto', fontSize:11, padding:'5px 8px' }}
            value={userInput}
            onChange={e => loadUser(e.target.value)}
          >
            {['admin','compras','inventario','auditor','viewer'].map(u => (
              <option key={u} value={u}>{u}</option>
            ))}
          </select>
          {currentUser && (
            <span style={s.badge(currentUser.role === 'admin' ? 'purple' : 'blue')}>
              {currentUser.role}
            </span>
          )}
        </div>
      </div>

      {userError ? null : null}

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
        {loading
          ? <div style={s.empty}>Conectando con el servicio...</div>
          : (
            <>
              {tab === 'dashboard' && <TabDashboard currentUser={currentUser} />}
              {tab === 'reportes'  && <TabReportes  currentUser={currentUser} />}
              {tab === 'usuarios'  && <TabUsuarios  currentUser={currentUser} />}
            </>
          )
        }
      </div>
    </div>
  );
}
