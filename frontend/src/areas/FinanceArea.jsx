import { SummaryArea } from './SummaryArea';
import { TrackingArea } from './TrackingArea';
import { PdfViewer } from '../components/PdfViewer';

export function FinanceArea({ session, reports, onGenerateReport, generating, sessionLoading, accessCount, reportsLoading, busyId, onViewReport, onDeleteReport, allowed, previewUrl }) {
  return (
    <section className="content-stack">
      {!allowed ? (
        <div className="notice notice--locked">Esta area esta restringida para tu rol.</div>
      ) : null}

      <SummaryArea
        session={session}
        reports={reports}
        onGenerateReport={onGenerateReport}
        generating={generating}
        sessionLoading={sessionLoading}
        accessCount={accessCount}
      />

      <TrackingArea
        reports={reports}
        loading={reportsLoading}
        busyId={busyId}
        onView={onViewReport}
        onDelete={onDeleteReport}
        allowed={allowed}
      />

      <PdfViewer src={previewUrl} />
    </section>
  );
}
