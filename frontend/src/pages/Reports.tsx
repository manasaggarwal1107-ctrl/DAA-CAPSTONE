// Reports and exports: CSV downloads for every stage plus the PDF report.
import { Badge, Card, Notice, PageHeader } from '../components/ui';
import { Icon, type IconName } from '../icons';
import { useApp } from '../store';

interface Item { file: string; title: string; text: string; icon: IconName; needs: 'none' | 'result' | 'benchmark' }

const ITEMS: Item[] = [
  { file: 'parcels.csv', title: 'Parcel list (CSV)', text: 'Every parcel with destination, weight, priority, deadline, value and status.', icon: 'package', needs: 'none' },
  { file: 'parcels.json', title: 'Parcel list (JSON)', text: 'The same data in the format accepted by the importer.', icon: 'package', needs: 'none' },
  { file: 'packing-plan.csv', title: 'Packing plan (CSV)', text: 'Selected, rejected and undeliverable parcels with weights, weighted values and reasons.', icon: 'scale', needs: 'result' },
  { file: 'route.csv', title: 'Delivery route (CSV)', text: 'Route legs with road paths, distances and the estimated arrival at each stop.', icon: 'route', needs: 'result' },
  { file: 'summary.csv', title: 'Optimisation summary (CSV)', text: 'Capacity, utilisation, value, distance and stage timings of the latest run.', icon: 'flag', needs: 'result' },
  { file: 'benchmark.csv', title: 'Benchmark results (CSV)', text: 'All measured medians, minima, means and peak memory per dataset size.', icon: 'gauge', needs: 'benchmark' },
  { file: 'report.pdf', title: 'PDF report', text: 'Formatted report: summary, packing plan, route, timings and benchmark charts (when available).', icon: 'file', needs: 'result' },
];

export function Reports() {
  const { result } = useApp();
  return (
    <>
      <PageHeader title="Reports and export" subtitle="Download the data behind every stage. Plan and route exports use the latest optimisation (a fresh one is run automatically if none exists)." />
      {result?.stale && <div className="mb-4"><Notice tone="warn" title="The latest optimisation is out of date">Exports of the plan, route and PDF describe the previous run. Run the optimisation again for current figures.</Notice></div>}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        {ITEMS.map((it) => (
          <Card key={it.file}>
            <div className="flex items-start gap-3">
              <span className="kpi-icon kpi-info"><Icon name={it.icon} size={16} /></span>
              <div className="min-w-0 flex-1">
                <h3 className="text-[14px] font-semibold">{it.title}</h3>
                <p className="mt-1 text-[13px] text-fg2">{it.text}</p>
                <div className="mt-3 flex items-center gap-2">
                  <a className="btn btn-secondary" href={`/api/export/${it.file}`}><Icon name="download" />Download</a>
                  {it.needs === 'benchmark' && <Badge tone="neutral">needs a benchmark run</Badge>}
                </div>
              </div>
            </div>
          </Card>
        ))}
      </div>
    </>
  );
}
