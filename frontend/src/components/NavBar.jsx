import React, { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";

const Theme = {
  bg: '#0f1117',
  surface: '#181c27',
  border: '#2a3045',
  accent: '#4f8ef7',
  text: '#e8ecf4',
  muted: '#6b7896',
};

export default function Navbar({ activeTab, setActiveTab }) {
  const { user, logout } = useAuth();
  const [online, setOnline] = useState(typeof navigator !== 'undefined' ? navigator.onLine : true);
  const tabs = ["inventario", "comercial", "logistica", "nomina", "finanzas"];

  const barStyle = {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '14px 20px',
    background: `linear-gradient(90deg, ${Theme.surface}, ${Theme.bg})`,
    borderBottom: `1px solid ${Theme.border}`,
    color: Theme.text,
  };

  const tabsStyle = { display: 'flex', gap: 8, alignItems: 'center' };
  const tabBtn = (active) => ({
    padding: '8px 14px',
    borderRadius: 8,
    cursor: 'pointer',
    border: 'none',
    fontSize: 13,
    fontWeight: 700,
    color: active ? '#081126' : Theme.muted,
    background: active ? `linear-gradient(180deg, ${Theme.accent}, ${Theme.accent}cc)` : 'transparent',
    boxShadow: active ? '0 4px 10px rgba(79,142,247,0.12)' : 'none',
    transition: 'all .15s',
  });

  const rightStyle = { display: 'flex', gap: 12, alignItems: 'center' };
  const userBadge = { padding: '6px 10px', borderRadius: 999, background: Theme.surface, border: `1px solid ${Theme.border}`, color: Theme.text, fontWeight: 700 };
  const logoutBtn = { padding: '8px 12px', borderRadius: 8, background: '#ef4444', color: '#fff', border: 'none', cursor: 'pointer' };

  useEffect(() => {
    function goOnline() { setOnline(true); }
    function goOffline() { setOnline(false); }
    window.addEventListener('online', goOnline);
    window.addEventListener('offline', goOffline);
    return () => {
      window.removeEventListener('online', goOnline);
      window.removeEventListener('offline', goOffline);
    };
  }, []);

  return (
    <div style={barStyle}>
      <div style={tabsStyle}>
        <div style={{ fontWeight: 800, fontSize: 18, marginRight: 12, letterSpacing: '-0.5px' }}>ERP</div>
        {tabs.map(tab => (
          <button key={tab} onClick={() => setActiveTab(tab)} style={tabBtn(activeTab === tab)}>
            {tab}
          </button>
        ))}
      </div>

      <div style={rightStyle}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{ width: 10, height: 10, borderRadius: 999, background: online ? '#22c55e' : '#f59e0b', boxShadow: online ? '0 0 8px rgba(34,197,94,0.3)' : 'none' }} title={online ? 'Online' : 'Offline'} />
          <div style={userBadge}>{user?.username || 'Invitado'}</div>
        </div>
        <button onClick={logout} style={logoutBtn}>Salir</button>
      </div>
    </div>
  );
}