import React from 'react';

const C = {
  bg: '#0f1117',
  surface: '#181c27',
  card: '#1e2333',
  border: '#2a3045',
  accent: '#4f8ef7',
  accentLo: '#1a2d54',
  green: '#22c55e',
  greenLo: '#14321f',
  yellow: '#f59e0b',
  yellowLo: '#39280d',
  purple: '#a78bfa',
  purpleLo: '#2d1b69',
  text: '#e8ecf4',
  muted: '#6b7896',
};

const s = {
  page: {
    minHeight: '100%',
    background: C.bg,
    color: C.text,
    fontFamily: "'IBM Plex Sans', 'Segoe UI', sans-serif",
  },
  header: {
    background: C.surface,
    border: `1px solid ${C.border}`,
    borderRadius: 10,
    padding: '18px 22px',
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  titleWrap: { display: 'flex', alignItems: 'center', gap: 12 },
  dot: {
    width: 10,
    height: 10,
    borderRadius: '50%',
    background: C.green,
    boxShadow: '0 0 10px rgba(34,197,94,0.35)',
  },
  title: { margin: 0, fontSize: 20, fontWeight: 800, letterSpacing: '-0.3px' },
  subtitle: { fontSize: 11, color: C.muted, marginTop: 2 },
  actionBtn: {
    border: 'none',
    borderRadius: 8,
    padding: '9px 14px',
    fontSize: 12,
    fontWeight: 700,
    cursor: 'pointer',
    background: C.accent,
    color: '#041126',
  },
  grid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
    gap: 12,
    marginBottom: 16,
  },
  kpi: (accent) => ({
    background: C.card,
    border: `1px solid ${C.border}`,
    borderRadius: 10,
    padding: 16,
    borderLeft: `3px solid ${accent || C.accent}`,
  }),
  kpiLabel: { fontSize: 10, color: C.muted, textTransform: 'uppercase', letterSpacing: 1.1, marginBottom: 6 },
  kpiValue: (color) => ({ fontSize: 24, fontWeight: 800, color: color || C.accent }),
  card: {
    background: C.card,
    border: `1px solid ${C.border}`,
    borderRadius: 10,
    padding: 18,
    marginBottom: 16,
  },
  sectionTitle: { margin: 0, fontSize: 13, fontWeight: 800, color: C.muted, textTransform: 'uppercase', letterSpacing: 1 },
  table: { width: '100%', borderCollapse: 'collapse', fontSize: 13 },
  th: {
    textAlign: 'left',
    padding: '8px 10px',
    color: C.muted,
    fontSize: 11,
    fontWeight: 700,
    textTransform: 'uppercase',
    letterSpacing: 0.8,
    borderBottom: `1px solid ${C.border}`,
  },
  td: { padding: '10px 10px', borderBottom: `1px solid ${C.border}22` },
  badge: (tone) => ({
    display: 'inline-block',
    padding: '2px 8px',
    borderRadius: 999,
    fontSize: 10,
    fontWeight: 700,
    letterSpacing: 0.5,
    textTransform: 'uppercase',
    background: tone === 'green' ? C.greenLo : tone === 'yellow' ? C.yellowLo : C.purpleLo,
    color: tone === 'green' ? C.green : tone === 'yellow' ? C.yellow : C.purple,
    border: `1px solid ${tone === 'green' ? C.green + '44' : tone === 'yellow' ? C.yellow + '44' : C.purple + '44'}`,
  }),
  muted: { color: C.muted, fontSize: 12, lineHeight: 1.6 },
};

export default function Nomina({ role, permissions }) {
  const hasPayrollAccess = permissions?.includes('nomina') ?? true;

  return (
    <section style={s.page}>
      <div style={s.header}>
        <div style={s.titleWrap}>
          <div style={s.dot} />
          <div>
            <h1 style={s.title}>Nómina & Personal</h1>
            <div style={s.subtitle}>Gestión de empleados, pagos y asistencias</div>
          </div>
        </div>
        <button style={s.actionBtn}>Calcular nómina</button>
      </div>

      <div style={s.grid}>
        <div style={s.kpi(C.accent)}>
          <div style={s.kpiLabel}>Empleados</div>
          <div style={s.kpiValue(C.accent)}>42</div>
        </div>
        <div style={s.kpi(C.green)}>
          <div style={s.kpiLabel}>Asistencia hoy</div>
          <div style={s.kpiValue(C.green)}>38</div>
        </div>
        <div style={s.kpi(C.yellow)}>
          <div style={s.kpiLabel}>Pendientes de pago</div>
          <div style={s.kpiValue(C.yellow)}>6</div>
        </div>
        <div style={s.kpi(C.purple)}>
          <div style={s.kpiLabel}>Rol activo</div>
          <div style={{ ...s.kpiValue(C.purple), fontSize: 16 }}>{role || '—'}</div>
        </div>
      </div>

      <div style={s.card}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <h2 style={s.sectionTitle}>Estado del módulo</h2>
          <span style={s.badge(hasPayrollAccess ? 'green' : 'yellow')}>
            {hasPayrollAccess ? 'activo' : 'limitado'}
          </span>
        </div>
        <div style={s.muted}>
          Este panel está preparado para integrarse con el microservicio de nómina. De momento muestra
          una vista base consistente con el resto del sistema para empleados, asistencias y pagos.
        </div>
      </div>

      <div style={s.card}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
          <h2 style={s.sectionTitle}>Resumen rápido</h2>
          <span style={s.badge('green')}>operativo</span>
        </div>
        <table style={s.table}>
          <thead>
            <tr>
              <th style={s.th}>Indicador</th>
              <th style={s.th}>Valor</th>
              <th style={s.th}>Estado</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td style={s.td}>Empleados activos</td>
              <td style={s.td}>42</td>
              <td style={s.td}><span style={s.badge('green')}>ok</span></td>
            </tr>
            <tr>
              <td style={s.td}>Horas registradas</td>
              <td style={s.td}>1,280</td>
              <td style={s.td}><span style={s.badge('green')}>ok</span></td>
            </tr>
            <tr>
              <td style={s.td}>Pagos pendientes</td>
              <td style={s.td}>6</td>
              <td style={s.td}><span style={s.badge('yellow')}>revisar</span></td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  );
}
