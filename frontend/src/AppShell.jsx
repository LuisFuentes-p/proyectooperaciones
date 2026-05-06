import { useEffect, useState } from 'react';
import { FinanceArea } from './areas/FinanceArea';
import { InventarioArea } from './areas/InventarioArea';
import { ComprasArea } from './areas/ComprasArea';
import { VentasArea } from './areas/VentasArea';
import { DevolucionesArea } from './areas/DevolucionesArea';
import { UsersArea } from './areas/UsersArea';
import { TopTabs } from './components/TopTabs';
import { UserSwitcher } from './components/UserSwitcher';
import { AccessMatrix } from './oop/AccessMatrix';
import { FinanceApi } from './oop/FinanceApi';

const apiBaseUrl = import.meta.env.VITE_FINANZAS_API_URL ?? 'http://localhost:8000';
const api = new FinanceApi(apiBaseUrl);

export default function AppShell() {
  const [currentUsername, setCurrentUsername] = useState(AccessMatrix.demoUsers[0].username);
  const [session, setSession] = useState(null);
  const [activeTab, setActiveTab] = useState('finanzas');
  const [reports, setReports] = useState([]);
  const [users, setUsers] = useState([]);
  const [selectedPdfUrl, setSelectedPdfUrl] = useState(api.getPublicReportPdfUrl());
  const [sessionLoading, setSessionLoading] = useState(true);
  const [reportsLoading, setReportsLoading] = useState(false);
  const [usersLoading, setUsersLoading] = useState(false);
  const [creatingReport, setCreatingReport] = useState(false);
  const [workingReportId, setWorkingReportId] = useState(null);
  const [error, setError] = useState('');

  const currentRole = session?.role ?? AccessMatrix.getRole(currentUsername);
  const tabs = AccessMatrix.getTabs(currentRole);
  const accessibleAreaCount = tabs.filter((tab) => tab.enabled).length;

  useEffect(() => {
    void loadSession(currentUsername);
  }, [currentUsername]);

  async function loadSession(username) {
    setSessionLoading(true);
    setError('');

    try {
      const currentUser = await api.getCurrentUser(username);
      setSession(currentUser);
      setActiveTab((previousTab) => {
        const nextTab = AccessMatrix.getTabs(currentUser.role).find((tab) => tab.enabled && tab.id === previousTab);
        return nextTab?.id ?? AccessMatrix.getFirstEnabledTab(currentUser.role);
      });
      setSelectedPdfUrl(api.getPublicReportPdfUrl());

      if (currentUser.permissions.includes('finanzas')) {
        setReportsLoading(true);
        const trackingData = await api.listReports(username);
        setReports(trackingData.items ?? []);
      } else {
        setReports([]);
      }

      if (currentUser.permissions.includes('usuarios')) {
        setUsersLoading(true);
        const usersData = await api.listUsers(username);
        setUsers(usersData.items ?? []);
      } else {
        setUsers([]);
      }
    } catch (fetchError) {
      setSession(null);
      setReports([]);
      setUsers([]);
      setError(fetchError instanceof Error ? fetchError.message : 'Error desconocido');
    } finally {
      setSessionLoading(false);
      setReportsLoading(false);
      setUsersLoading(false);
    }
  }

  async function refreshTracking() {
    if (!session?.permissions.includes('finanzas')) {
      return [];
    }

    setReportsLoading(true);
    try {
      const trackingData = await api.listReports(currentUsername);
      setReports(trackingData.items ?? []);
      return trackingData.items ?? [];
    } finally {
      setReportsLoading(false);
    }
  }

  async function handleGenerateReport() {
    setCreatingReport(true);
    setError('');

    try {
      const createdReport = await api.createReport(currentUsername);
      if (session?.permissions.includes('finanzas')) {
        const refreshedReports = await refreshTracking();
        const trackedReport = refreshedReports.find((report) => report.id === createdReport.id);
        setSelectedPdfUrl(trackedReport ? api.getTrackedReportPdfUrl(trackedReport.id) : api.getPublicReportPdfUrl());
      } else {
        setSelectedPdfUrl(api.getPublicReportPdfUrl());
      }
      setActiveTab('finanzas');
    } catch (fetchError) {
      setError(fetchError instanceof Error ? fetchError.message : 'Error desconocido');
    } finally {
      setCreatingReport(false);
    }
  }

  function handleSelectReport(report) {
    setSelectedPdfUrl(api.getTrackedReportPdfUrl(report.id));
    setActiveTab('finanzas');
  }

  async function handleDeleteReport(reportId) {
    const shouldDelete = window.confirm('¿Borrar este reporte?');
    if (!shouldDelete) {
      return;
    }

    setWorkingReportId(reportId);
    setError('');

    try {
      await api.deleteReport(reportId, currentUsername);
      await refreshTracking();
      if (selectedPdfUrl.includes(`/reports/tracking/${reportId}/pdf`)) {
        setSelectedPdfUrl(api.getPublicReportPdfUrl());
      }
    } catch (fetchError) {
      setError(fetchError instanceof Error ? fetchError.message : 'Error desconocido');
    } finally {
      setWorkingReportId(null);
    }
  }

  function handleSelectTab(tabId) {
    const selectedTab = tabs.find((tab) => tab.id === tabId);
    if (selectedTab?.enabled) {
      setActiveTab(tabId);
    }
  }

  const visibleContent = {
    finanzas: (
      <FinanceArea
        session={session}
        reports={reports}
        onGenerateReport={handleGenerateReport}
        generating={creatingReport}
        sessionLoading={sessionLoading}
        accessCount={accessibleAreaCount}
        reportsLoading={reportsLoading}
        busyId={workingReportId}
        onViewReport={handleSelectReport}
        onDeleteReport={handleDeleteReport}
        allowed={session?.permissions.includes('finanzas')}
        previewUrl={selectedPdfUrl}
      />
    ),
    compras: (
      <ComprasArea
        allowed={session?.permissions.includes('compras')}
        username={currentUsername}
      />
    ),
    ventas: (
      <VentasArea
        allowed={session?.permissions.includes('ventas')}
        username={currentUsername}
      />
    ),
    inventario: (
      <InventarioArea
        allowed={session?.permissions.includes('inventario')}
        username={currentUsername}
      />
    ),
    devoluciones: (
      <DevolucionesArea
        allowed={session?.permissions.includes('devoluciones')}
        username={currentUsername}
      />
    ),
    usuarios: <UsersArea users={users} loading={usersLoading} allowed={session?.permissions.includes('usuarios')} />,
  };

  return (
    <main className="shell app-shell">
      <section className="panel app-panel">
        <header className="topbar">
          <div>
            <p className="eyebrow">Sistema de operaciones</p>
            <h1>Areas de la compania por rol</h1>
            <p className="description">
              Las tabs representan los modulos del sistema completo. Cada rol habilita solo las areas que puede acceder.
            </p>
          </div>

          <UserSwitcher users={AccessMatrix.demoUsers} selectedUsername={currentUsername} onChange={setCurrentUsername} session={session} />
        </header>

        <TopTabs tabs={tabs} activeTab={activeTab} onSelect={handleSelectTab} />

        {error ? <p className="error">{error}</p> : null}

        <div className="content-stack">{visibleContent[activeTab]}</div>
      </section>
    </main>
  );
}
