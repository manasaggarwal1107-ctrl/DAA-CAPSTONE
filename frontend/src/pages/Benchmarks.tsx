// Phase 4 - performance laboratory: reproducible datasets, repeated perf_counter measurements, theory vs measurement.
import { useEffect, useState } from 'react';
import { api, errorMessage } from '../api';
import { LineChart } from '../components/charts';
import { Button, Card, Empty, Field, Notice, PageHeader, Stat } from '../components/ui';
import { Icon } from '../icons';
import { fmt, fmtMs } from '../lib';
import { useApp } from '../store';
import type { Benchmark } from '../types';

const SIZES = [10, 50, 100, 500, 1000, 5000];
const STAGES = ['sorting', 'knapsack', 'dijkstra', 'routing'] as const;
const COLOURS = ['var(--color-s1)', 'var(--color-s2)', 'var(--color-s3)', 'var(--color-s4)'];
const LABEL: Record<(typeof STAGES)[number], string> = { sorting: 'Merge Sort', knapsack: '0/1 Knapsack DP', dijkstra: 'Dijkstra (one source)', routing: 'Nearest Neighbour route' };

export function Benchmarks() {
  const { toast } = useApp();
  const [data, setData] = useState<Benchmark | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [sizes, setSizes] = useState<number[]>([10, 50, 100, 500, 1000]);
  const [repeats, setRepeats] = useState('5');
  const [seed, setSeed] = useState('42');
  const [running, setRunning] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => { void api.get<{ benchmark: Benchmark | null }>('/api/benchmark/latest').then((r) => setData(r.benchmark)).finally(() => setLoaded(true)); }, []);

  const problem = !sizes.length ? 'Select at least one dataset size' : !/^\d+$/.test(repeats) || Number(repeats) < 1 || Number(repeats) > 15 ? 'Repeats must be between 1 and 15'
    : !/^-?\d+$/.test(seed.trim()) ? 'The random seed must be a whole number' : '';

  const run = async () => {
    if (problem) { setError(problem); return; }
    setError(''); setRunning(true);
    try { setData(await api.post<Benchmark>('/api/benchmark/run', { sizes: [...sizes].sort((a, b) => a - b), repeats: Number(repeats), seed: Number(seed) })); toast('Benchmark finished', 'good'); }
    catch (e) { setError(errorMessage(e)); toast(errorMessage(e), 'bad'); }
    finally { setRunning(false); }
  };
  const toggle = (n: number) => setSizes((s) => (s.includes(n) ? s.filter((x) => x !== n) : [...s, n]));
  const rows = data?.rows ?? [];

  return (
    <>
      <PageHeader title="Benchmark lab" subtitle="Every figure on this page is measured on this computer with time.perf_counter(); theoretical complexities are listed separately and are never presented as measurements."
        actions={<a className={`btn btn-secondary ${data ? '' : 'pointer-events-none opacity-50'}`} href="/api/export/benchmark.csv" aria-disabled={!data}><Icon name="download" />Export CSV</a>} />
      <Card title="Run a benchmark" subtitle="Datasets are generated from a fixed random seed, so the same inputs are reproduced on every run">
        <div className="flex flex-wrap items-end gap-6">
          <fieldset><legend className="mb-1 text-xs font-medium text-fg2">Parcels per dataset</legend>
            <div className="flex flex-wrap gap-2">{SIZES.map((n) => (
              <label key={n} className={`cursor-pointer rounded-lg border px-3 py-1.5 text-[13px] tabular-nums transition-colors ${sizes.includes(n) ? 'border-accent-strong bg-accent/10 text-accent' : 'border-line text-fg2 hover:border-ink-600'}`}>
                <input type="checkbox" className="sr-only" checked={sizes.includes(n)} onChange={() => toggle(n)} />{n.toLocaleString('en-IN')}</label>))}</div></fieldset>
          <div className="w-28"><Field label="Repeats (1-15)">{(id) => <input id={id} className="input" value={repeats} onChange={(e) => setRepeats(e.target.value)} />}</Field></div>
          <div className="w-28"><Field label="Random seed">{(id) => <input id={id} className="input" value={seed} onChange={(e) => setSeed(e.target.value)} />}</Field></div>
          <Button variant="primary" icon="gauge" busy={running} onClick={() => void run()}>{running ? 'Measuring…' : 'Run benchmark'}</Button>
        </div>
        {error && <div className="mt-3"><Notice tone="bad" title="Cannot run benchmark">{error}</Notice></div>}
        {running && <p className="mt-3 text-xs text-fg3">The 1,000 and 5,000 parcel datasets take several seconds because the pure-Python knapsack performs n × W steps per repeat.</p>}
      </Card>

      {!loaded ? null : !data ? (
        <div className="mt-4"><Card><Empty icon="gauge" title="No measurements yet">Choose dataset sizes and press “Run benchmark”. Nothing is shown until real measurements exist.</Empty></Card></div>
      ) : (
        <>
          <div className="mt-4 grid grid-cols-2 gap-4 lg:grid-cols-4">
            <div className="card p-4"><Stat label="Measured" value={data.generated_at} /></div>
            <div className="card p-4"><Stat label="Datasets" value={data.parameters.sizes.map((n) => n.toLocaleString('en-IN')).join(', ')} /></div>
            <div className="card p-4"><Stat label="Repeats · seed" value={`${data.parameters.repeats} · ${data.parameters.seed}`} /></div>
            <div className="card p-4"><Stat label="Python" value={data.environment.python} /></div>
          </div>
          <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-2">
            <Card title="Runtime by dataset size" subtitle="Median of the repeats, log-log axes (a straight line means a power law)">
              <LineChart xLabel="parcels (n)" yLabel="ms" series={STAGES.map((k, i) => ({ name: LABEL[k], color: COLOURS[i], points: rows.map((r) => ({ x: r.n, y: r[k].median_ms })) }))} />
            </Card>
            <Card title="Peak memory by dataset size" subtitle="tracemalloc peak of one separate run (KiB); timing runs are never traced">
              <LineChart xLabel="parcels (n)" yLabel="KiB" series={STAGES.map((k, i) => ({ name: LABEL[k], color: COLOURS[i], points: rows.map((r) => ({ x: r.n, y: Math.max(r[k].peak_kb, 0.1) })) }))} />
            </Card>
          </div>
          <Card className="mt-4" title="Benchmark table" subtitle="Median (min) milliseconds per stage" pad={false}>
            <div className="overflow-x-auto"><table className="tbl">
              <thead><tr><th className="num">Parcels</th><th className="num">Locations</th><th className="num">Capacity kg</th><th className="num">Selected</th><th className="num">Stops</th><th className="num">DP cells</th>
                {STAGES.map((k) => <th key={k} className="num">{LABEL[k]}</th>)}</tr></thead>
              <tbody>{rows.map((r) => (
                <tr key={r.n}><td className="num font-medium">{r.n.toLocaleString('en-IN')}</td><td className="num">{r.locations}</td><td className="num">{r.capacity}</td><td className="num">{r.selected}</td><td className="num">{r.stops}</td><td className="num text-fg3">{fmt(r.dp_cells, 0)}</td>
                  {STAGES.map((k) => <td key={k} className="num">{fmtMs(r[k].median_ms)} <span className="text-fg3">({fmtMs(r[k].min_ms)})</span></td>)}</tr>))}</tbody></table></div>
          </Card>
          <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-2">
            <Card title="Theory versus measurement">
              <table className="tbl"><thead><tr><th>Stage</th><th>Theoretical complexity (not measured)</th></tr></thead>
                <tbody>{Object.entries(data.theory).map(([k, v]) => <tr key={k}><td className="font-medium capitalize">{k}</td><td className="whitespace-normal text-fg2">{v}</td></tr>)}</tbody></table>
              <p className="mt-3 text-xs text-fg3">Reading the chart: doubling n should roughly double knapsack time and slightly more than double sorting time. Dijkstra and routing depend on the graph size V, E and the number of stops, which grow with n only through the generator rules below.</p>
            </Card>
            <Card title="Dataset rules and resource limits">
              <ul className="list-disc space-y-1.5 pl-4 text-[13px] text-fg2">
                <li><b className="text-fg">Locations</b>: {data.parameters.locations_rule}; every graph is connected and generated from the same seed.</li>
                <li><b className="text-fg">Vehicle capacity</b>: {data.parameters.capacity_rule}. The cap keeps the knapsack decision matrix at n × W bytes (3 million cells at n = 5,000) instead of growing without bound.</li>
                <li><b className="text-fg">Memory guard</b>: the application refuses any knapsack above 60 million decision cells and tells the user to reduce capacity or parcel count.</li>
                <li><b className="text-fg">Variance</b>: timings vary between runs with CPU load; compare medians, and rerun with more repeats for tighter results.</li>
              </ul>
              <p className="mt-3 text-xs text-fg3">{data.note}</p>
            </Card>
          </div>
        </>
      )}
    </>
  );
}
