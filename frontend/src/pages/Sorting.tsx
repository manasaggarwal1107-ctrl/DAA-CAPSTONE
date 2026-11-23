// Phase 2 - package prioritisation: Merge Sort of pending parcels with a step-by-step explanation.
import { useCallback, useEffect, useState } from 'react';
import { api, errorMessage } from '../api';
import { MergeTrace } from '../components/viz';
import { Badge, Button, Card, Empty, Notice, PageHeader, PriorityBadge, Spinner, Stat } from '../components/ui';
import { fmt, fmtDate, fmtMs } from '../lib';
import { useApp } from '../store';
import type { Parcel, SortResponse } from '../types';

const LIMIT = 40;

function ParcelTable({ rows, total, ranked }: { rows: Parcel[]; total: number; ranked: boolean }) {
  return (
    <>
      <div className="max-h-[460px] overflow-auto rounded-lg border border-line">
        <table className="tbl">
          <thead><tr><th className="num">#</th><th>Parcel</th><th>Priority</th><th>Deadline</th><th>Destination</th></tr></thead>
          <tbody>
            {rows.slice(0, LIMIT).map((p, i) => (
              <tr key={p.id}><td className="num text-fg3">{i + 1}</td><td className="font-medium">{p.id}</td><td><PriorityBadge p={p.priority} /></td>
                <td className="text-fg2">{fmtDate(p.deadline)}</td><td className="text-fg2">{p.destination}</td></tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="mt-2 text-xs text-fg3">{total > LIMIT ? `Showing the first ${LIMIT} of ${total} parcels. ` : ''}{ranked ? 'Sorted: priority high to low, then earlier deadline, then ID.' : 'Original order: as stored (insertion order).'}</p>
    </>
  );
}

export function Sorting() {
  const { state, optimise, running } = useApp();
  const [data, setData] = useState<SortResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const run = useCallback(async () => {
    setBusy(true);
    try { setData(await api.post<SortResponse>('/api/sort', { sorter: 'merge' })); setError(null); }
    catch (e) { setError(errorMessage(e)); }
    finally { setBusy(false); }
  }, []);
  useEffect(() => { void run(); }, [run, state?.parcels]);

  if (!data) return error ? <Notice tone="bad" title="Sorting failed">{error}</Notice> : <Spinner label="Sorting parcels" />;
  const byId = new Map(data.original.map((p) => [p.id, p]));
  const describe = (id: string | number) => { const p = byId.get(String(id)); return p ? `${p.id} · P${p.priority} · ${fmtDate(p.deadline)}` : String(id); };

  return (
    <>
      <PageHeader title="Prioritisation engine" subtitle="Pending parcels are ordered by a hand-written Merge Sort: higher priority first, then earlier deadline, then parcel ID as a deterministic tie-breaker."
        actions={<>
          <Button icon="refresh" busy={busy} onClick={() => void run()}>Re-run sort</Button>
          <Button variant="primary" icon="zap" busy={running} onClick={() => void optimise()}>Run full optimisation</Button>
        </>} />
      {error && <div className="mb-4"><Notice tone="bad" title="Sorting failed">{error}</Notice></div>}

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
        <div className="card p-4"><Stat label="Pending parcels" value={fmt(data.n, 0)} /></div>
        <div className="card p-4"><Stat label={`Sort time (median of ${data.repeats})`} value={fmtMs(data.time_ms)} /></div>
        <div className="card p-4"><Stat label="Key comparisons" value={fmt(data.comparisons, 0)} /></div>
        <div className="card p-4"><Stat label="Time complexity" value={<Badge tone="info">O(n log n)</Badge>} /></div>
        <div className="card p-4"><Stat label="Extra space" value={<Badge tone="info">O(n)</Badge>} /></div>
      </div>

      {data.n === 0 ? (
        <div className="mt-4"><Card><Empty icon="package" title="No pending parcels">Add parcels on the Parcels page, or load a sample dataset.</Empty></Card></div>
      ) : (
        <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-2">
          <Card title="Original order" subtitle="Before sorting"><ParcelTable rows={data.original} total={data.n} ranked={false} /></Card>
          <Card title="Prioritised order" subtitle="After Merge Sort"><ParcelTable rows={data.sorted} total={data.n} ranked /></Card>
        </div>
      )}

      <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-3">
        <Card className="xl:col-span-2" title="Step-by-step Merge Sort" subtitle={`Trace of the real implementation on the first ${data.trace_parcels.length} parcels of the queue`}>
          {data.trace_parcels.length > 1
            ? <MergeTrace events={data.trace} input={data.trace_parcels} describe={describe} />
            : <Empty icon="sort" title="Need at least two parcels">A trace needs two or more pending parcels.</Empty>}
        </Card>
        <Card title="How it works and why O(n log n)">
          <ol className="list-decimal space-y-2 pl-4 text-[13px] text-fg2">
            <li><b className="text-fg">Divide</b> the list into two halves until each part holds one parcel (about log₂ n levels).</li>
            <li><b className="text-fg">Merge</b> two sorted halves by repeatedly taking the smaller front element: at most n - 1 comparisons per level.</li>
            <li>Total work: <span className="font-mono text-accent">T(n) = 2T(n/2) + O(n)</span> = <b className="text-fg">O(n log n)</b> in the best, average and worst case.</li>
            <li>Equal keys keep their input order, so Merge Sort is <b className="text-fg">stable</b>; the ID tie-breaker makes the order fully deterministic.</li>
          </ol>
          <p className="mt-3 text-xs text-fg3">The sorter is registered by name on the backend ({data.complexity.time}); another lab algorithm can be added with one registry entry.</p>
        </Card>
      </div>
    </>
  );
}
