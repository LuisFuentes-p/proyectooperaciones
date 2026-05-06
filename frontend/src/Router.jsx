import { useEffect, useState } from 'react';
import LoginPage from './pages/LoginPage';
import Dashboard from './pages/Dashboard';
import AreaPage from './pages/AreaPage';

function parseHash() {
  const hash = window.location.hash.replace(/^#/, '') || '/';
  const parts = hash.split('/').filter(Boolean);
  if (parts.length === 0) return { route: 'home' };
  if (parts[0] === 'area' && parts[1]) return { route: 'area', areaId: parts[1] };
  if (parts[0] === '') return { route: 'home' };
  return { route: parts[0] };
}

export default function Router() {
  const [route, setRoute] = useState(parseHash());
  const storedUser = localStorage.getItem('app_username') ?? null;

  useEffect(() => {
    function onHash() {
      setRoute(parseHash());
    }
    window.addEventListener('hashchange', onHash);
    return () => window.removeEventListener('hashchange', onHash);
  }, []);

  function handleLogin(username) {
    setRoute({ route: 'home' });
  }

  const username = localStorage.getItem('app_username') ?? storedUser;

  if (!username) {
    return <LoginPage onLogin={handleLogin} />;
  }

  if (route.route === 'home') {
    return <Dashboard username={username} />;
  }

  if (route.route === 'area') {
    return <AreaPage areaId={route.areaId} username={username} />;
  }

  // fallback
  return <Dashboard username={username} />;
}
