import { useEffect, useState } from 'react';
import { api } from '../api';
import { BarChart, LineChart } from '../components/charts';
import { Badge, Card, Empty, Kpi, Meter, Notice, PageHeader, Spinner } from '../components/ui';
import { fmt, fmtMs } from '../lib';
import { useApp } from '../store';
import type { Dashboard as Dash } from '../types';

const STATUS: Record<string, { label: string; tone: 'good' | 'warn' | 'neutral' | 'bad' }> = {
  optimised: { label: 'Optimised', tone: 'good' }, partial_route: { label: 'Partial route', tone: 'warn' },
  nothing_selected: { label: 'Nothing selected', tone: 'warn' }, nothing_deliverable: { label: 'Nothing deliverable', tone: 'bad' }, no_parcels: { label: 'No parcels', tone: 'neutral' },
};
const STAGE_COLOURS = ['var(--color-s1)', 'var(--color-s2)', 'var(--color-s3)', 'var(--color-s4)'];

export function Dashboard() {
  const { result, state } = useApp();
  const [d, setD] = useState<Dash | null>(null);
  useEffect(() => { void api.get<Dash>('/api/dashboard').then(setD); }, [result, state]);
  if (!d) return <Spinner />;
  const r = d.result;
  const status = r ? STATUS[r.status] : null;

  const stages = r ? (['sorting', 'knapsack', 'routing'] as const).map((k) => ({ label: k, value: r.timings_ms[k] })) : [];
  const perf = r ? r.deliveries.map((x, i) => ({ label: `${i + 1}`, value: x.cumulative_km, color: x.late.length ? 'var(--color-bad)' : 'var(--color-good)',
    note: `${x.destination} · ETA ${x.eta.replace('T', ' ')}${x.late.length ? ` · ${x.late.length} late` : ''}` })) : [];
  const bench = d.benchmark?.rows;

  return (
    <>
      <PageHeader title="Operations dashboard" subtitle="Live view of the parcel queue, the latest load plan and delivery route, and algorithm performance."
        />
      {r?.stale && <div className="mb-4"><Notice tone="warn" title="Parcels, roads or settings changed since the last optimisation">The figures below describe the previous run. Run the optimisation again to refresh them.</Notice></div>}
      {r && r.warnings.length > 0 && !r.stale && <div className="mb-4"><Notice tone="warn" title="Optimisation warnings">{r.warnings.join(' ')}</Notice></div>}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Kpi label="Total parcels" value={fmt(d.total_parcels, 0)} sub={`${d.pending_parcels} pending dispatch`} icon="package" />
        <Kpi label="Pending parcels" value={fmt(d.pending_parcels, 0)} sub="status = pending" icon="clock" tone="warn" />
        <Kpi label="Selected for load" value={r ? fmt(r.selected, 0) : '-'} sub={r ? `of ${d.pending_parcels} pending · value ${fmt(r.total_value, 0)}` : 'Run an optimisation'} icon="check" tone="good" />
        <div className="card p-4">
          <div className="flex items-center justify-between text-fg3"><span className="text-[11.5px] font-medium uppercase tracking-wider">Vehicle utilisation</span><span className="kpi-icon kpi-info"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><path d="M12 14l4-4M3.3 18a10 10 0 1 1 17.4 0" /></svg></span></div>
          <div className="mt-2 text-[26px] font-semibold leading-none tracking-tight tabular-nums">{r ? `${fmt(r.utilisation, 1)}%` : '-'}</div>
          <div className="mt-3"><Meter percent={r?.utilisation ?? 0} /></div>
          <div className="mt-2 text-xs text-fg3">{r ? `${r.used_weight} of ${r.capacity} kg` : 'No plan yet'}</div>
        </div>
        <Kpi label="Route distance" value={r ? `${fmt(r.route_distance, 1)} km` : '-'} sub={r ? `${r.deliveries.length} delivery stops` : 'No route yet'} icon="route" />
        <Kpi label="Delivery locations" value={fmt(d.locations, 0)} sub={`${d.roads} road connections`} icon="pin" />
        <Kpi label="Optimisation status" value={status ? <Badge tone={status.tone}>{status.label}</Badge> : <Badge>Not run</Badge>} sub={r ? `Ran ${r.ran_at}` : 'Press Run optimisation'} icon="flag" tone={status?.tone === 'good' ? 'good' : 'info'} />
        <Kpi label="Algorithm time" value={r ? fmtMs(r.timings_ms.total) : '-'} sub={r ? `sort ${fmtMs(r.timings_ms.sorting)} · knapsack ${fmtMs(r.timings_ms.knapsack)} · route ${fmtMs(r.timings_ms.routing)}` : 'Measured with perf_counter'} icon="zap" />
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card title="Parcel priority distribution" subtitle="Number of parcels per priority level (5 = most urgent)">
          <BarChart data={d.priority_distribution.map((p) => ({ label: `P${p.priority}`, value: p.count }))} />
        </Card>
        <Card title="Parcel weight distribution" subtitle="Parcels by weight band (kg)">
          <BarChart data={d.weight_distribution.map((p) => ({ label: p.label, value: p.count }))} color="var(--color-s3)" />
        </Card>
        <Card title="Delivery performance" subtitle="Cumulative distance at each stop; red = at least one parcel estimated late"
          actions={r && <span className="text-xs text-fg3">{r.on_time} on time · {r.late} late (estimate)</span>}>
          {perf.length ? <BarChart data={perf} unit=" km" formatValue={(v) => fmt(v, 1)} /> : <Empty icon="route" title="No route yet">Run an optimisation to see delivery stops.</Empty>}
        </Card>
        <Card title="Algorithm runtime comparison" subtitle={bench ? `Measured medians from the benchmark lab (${d.benchmark?.generated_at})` : 'Stage timings of the latest optimisation run'}>
          {bench ? (
            <LineChart xLabel="parcels (n)" yLabel="ms (log)" formatY={(v) => (v >= 1 ? fmt(v, 0) : v.toString())}
              series={(['sorting', 'knapsack', 'dijkstra', 'routing'] as const).map((k, i) => ({ name: k, color: STAGE_COLOURS[i], points: bench.map((b) => ({ x: b.n, y: b[k].median_ms })) }))} height={230} />
          ) : stages.length ? <BarChart data={stages.map((s, i) => ({ ...s, color: STAGE_COLOURS[i] }))} unit=" ms" formatValue={(v) => v.toFixed(3)} /> :
            <Empty icon="gauge" title="No timings yet">Run an optimisation or open the Benchmark lab.</Empty>}
        </Card>
      </div>
    </>
  );
}
