// Phase 2 - box filling: 0/1 Knapsack dynamic programming with selected/rejected parcels and the DP table.
import { useCallback, useEffect, useState } from 'react';
import { api, errorMessage } from '../api';
import { DpTable, Recurrence } from '../components/viz';
import { Badge, Button, Card, Empty, Field, Meter, Notice, PageHeader, PriorityBadge, Spinner, Stat } from '../components/ui';
import { fmt, fmtMs } from '../lib';
import { useApp } from '../store';
import type { Parcel, RejectedParcel, Result } from '../types';

const ev = (p: Parcel) => p.value * p.priority;

export function Knapsack() {
  const { state, optimise, running } = useApp();
  const [cap, setCap] = useState(String(state!.settings.capacity));
  const [res, setRes] = useState<Result | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const capError = !/^\d+$/.test(cap.trim()) ? 'Enter a whole number of kg (0 or more)' : Number(cap) > 100000 ? 'Capacity cannot exceed 100,000 kg' : '';

  const run = useCallback(async (c: string) => {
    setBusy(true);
    try { setRes(await api.post<Result>('/api/knapsack', { capacity: Number(c) })); setError(null); }
    catch (e) { setError(errorMessage(e)); }
    finally { setBusy(false); }
  }, []);
  useEffect(() => { void run(String(state!.settings.capacity)); }, [run, state]);   // eslint-disable-line react-hooks/exhaustive-deps

  if (!res) return error ? <Notice tone="bad" title="Load planning failed">{error}</Notice> : <Spinner label="Solving knapsack" />;
  const dp = res.dp;

  return (
    <>
      <PageHeader title="Load planning - 0/1 Knapsack" subtitle="Choose the parcels that maximise total priority-weighted value (delivery value × priority) without exceeding the vehicle's weight capacity. Each parcel is loaded at most once."
        actions={<Button variant="primary" icon="zap" busy={running} onClick={() => void optimise({ capacity: Number(cap) })} disabled={!!capError}>Save capacity &amp; run full optimisation</Button>} />
      <Card className="mb-4">
        <form className="flex flex-wrap items-end gap-4" onSubmit={(e) => { e.preventDefault(); if (!capError) void run(cap); }}>
          <div className="w-48"><Field label="Vehicle capacity (kg)" error={capError} hint="What-if only until saved">
            {(id, bad) => <input id={id} className="input" inputMode="numeric" value={cap} aria-invalid={bad} onChange={(e) => setCap(e.target.value)} />}</Field></div>
          <Button type="submit" icon="scale" busy={busy} disabled={!!capError}>Solve</Button>
          <span className="pb-2 text-xs text-fg3">Saved capacity: {state!.settings.capacity} kg</span>
        </form>
      </Card>
      {error && <div className="mb-4"><Notice tone="bad" title="Could not solve">{error}</Notice></div>}
      {res.warnings.length > 0 && <div className="mb-4"><Notice tone="warn" title="Notes">{res.warnings.join(' ')}</Notice></div>}

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
        <div className="card p-4"><Stat label="Selected / deliverable" value={`${res.selected.length} / ${res.counts.deliverable}`} /></div>
        <div className="card p-4"><Stat label="Total weight" value={`${res.used_weight} kg`} /></div>
        <div className="card p-4"><Stat label="Remaining capacity" value={`${res.remaining_capacity} kg`} /></div>
        <div className="card p-4"><Stat label="Priority-weighted value" value={fmt(res.total_value, 0)} /></div>
        <div className="card p-4"><Stat label="Knapsack time" value={fmtMs(res.timings_ms.knapsack)} />
          <div className="mt-2"><Meter percent={res.utilisation} /></div><div className="mt-1 text-xs text-fg3">{fmt(res.utilisation, 1)}% of capacity used</div></div>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-2">
        <Card title={`Selected parcels (${res.selected.length})`} subtitle="Loaded onto the vehicle" pad={false}>
          {res.selected.length === 0 ? <Empty icon="box" title="Nothing selected">No pending parcel fits within {res.capacity} kg.</Empty> : (
            <div className="max-h-[380px] overflow-auto"><table className="tbl"><thead><tr><th>Parcel</th><th>Destination</th><th className="num">kg</th><th>Pri</th><th className="num">Value</th><th className="num">Weighted</th></tr></thead>
              <tbody>{res.selected.map((p) => <tr key={p.id}><td className="font-medium">{p.id}</td><td className="text-fg2">{p.destination}</td><td className="num">{p.weight}</td><td><PriorityBadge p={p.priority} /></td><td className="num">{fmt(p.value, 0)}</td><td className="num text-accent">{fmt(ev(p), 0)}</td></tr>)}</tbody></table></div>)}
        </Card>
        <Card title={`Rejected parcels (${res.rejected.length})`} subtitle="Left for a later trip" pad={false}>
          {res.rejected.length === 0 ? <Empty icon="check" title="Nothing rejected">Every deliverable parcel fits.</Empty> : (
            <div className="max-h-[380px] overflow-auto"><table className="tbl"><thead><tr><th>Parcel</th><th className="num">kg</th><th>Pri</th><th className="num">Weighted</th><th>Reason</th></tr></thead>
              <tbody>{res.rejected.map((p: RejectedParcel) => <tr key={p.id}><td className="font-medium">{p.id}</td><td className="num">{p.weight}</td><td><PriorityBadge p={p.priority} /></td><td className="num">{fmt(ev(p), 0)}</td><td className="whitespace-normal text-fg3">{p.reason}</td></tr>)}</tbody></table></div>)}
        </Card>
      </div>

      {res.undeliverable.length > 0 && (
        <Card className="mt-4" title={`Undeliverable parcels (${res.undeliverable.length})`} subtitle="Excluded before the knapsack: no road path from the depot. They use no capacity and add no value." pad={false}>
          <div className="max-h-[260px] overflow-auto"><table className="tbl"><thead><tr><th>Parcel</th><th>Destination</th><th className="num">kg</th><th>Pri</th><th>Reason</th></tr></thead>
            <tbody>{res.undeliverable.map((p: RejectedParcel) => <tr key={p.id}><td className="font-medium">{p.id}</td><td className="text-fg2">{p.destination}</td><td className="num">{p.weight}</td><td><PriorityBadge p={p.priority} /></td><td className="whitespace-normal text-fg3">{p.reason}</td></tr>)}</tbody></table></div>
        </Card>)}

      <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-3">
        <Card className="xl:col-span-2" title="Dynamic-programming table" subtitle="dp[i][w] = best weighted value using the first i parcels with capacity w; the highlighted path reconstructs the chosen parcels"
          actions={<Badge tone="neutral">{fmt(dp.cells, 0)} cells</Badge>}>
          {dp.table ? <DpTable table={dp.table} weights={dp.weights} values={dp.values} labels={dp.order} />
            : <Notice tone="info" title="Table not drawn">{dp.table_note}</Notice>}
        </Card>
        <Card title="Recurrence and complexity">
          <Recurrence />
          <ul className="mt-3 space-y-2 text-[13px] text-fg2">
            <li><b className="text-fg">Time</b> O(n · W) for n parcels and capacity W; here {res.counts.deliverable} × {res.capacity}.</li>
            <li><b className="text-fg">Space</b> O(W) for the values (one array) plus one decision byte per cell so the chosen parcels can be rebuilt.</li>
            <li><b className="text-fg">Why descending w?</b> The 1-D array is updated from high capacity to low so a parcel can never be counted twice (0/1, not unbounded).</li>
            <li className="text-fg3">Pseudo-polynomial: W is a number, not an input length. A size guard refuses decision matrices above 60 million cells.</li>
          </ul>
        </Card>
      </div>
    </>
  );
}
