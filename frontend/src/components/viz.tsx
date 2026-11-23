// Shared algorithm visualisations: merge-sort step player and the knapsack DP table.
import { useEffect, useState } from 'react';
import { Icon } from '../icons';
import type { MergeEvent } from '../types';
import { Button } from './ui';

/** Prev / play / next controls driving a step index. */
export function StepControls({ step, max, onChange, label = 'Step' }: { step: number; max: number; onChange: (n: number) => void; label?: string }) {
  const [playing, setPlaying] = useState(false);
  useEffect(() => {
    if (!playing) return;
    if (step >= max) { setPlaying(false); return; }
    const t = window.setTimeout(() => onChange(step + 1), 750);
    return () => window.clearTimeout(t);
  }, [playing, step, max, onChange]);
  return (
    <div className="flex flex-wrap items-center gap-2">
      <Button onClick={() => { setPlaying(false); onChange(0); }} icon="refresh" aria-label="Reset">Reset</Button>
      <Button onClick={() => { setPlaying(false); onChange(Math.max(0, step - 1)); }} disabled={step <= 0} icon="prev" aria-label="Previous step" />
      <Button variant="primary" onClick={() => { if (step >= max) onChange(0); setPlaying((p) => !p); }} icon={playing ? 'pause' : 'play'}>{playing ? 'Pause' : 'Play'}</Button>
      <Button onClick={() => { setPlaying(false); onChange(Math.min(max, step + 1)); }} disabled={step >= max} icon="next" aria-label="Next step" />
      <input type="range" min={0} max={max} value={step} onChange={(e) => { setPlaying(false); onChange(Number(e.target.value)); }} className="w-40 accent-cyan-400" aria-label={`${label} slider`} />
      <span className="text-xs tabular-nums text-fg3">{label} {step} / {max}</span>
    </div>
  );
}

const chip = (v: string | number, extra = '') => (
  <span key={`${v}-${extra}`} className={`rounded-md border px-1.5 py-0.5 text-[12px] tabular-nums ${extra || 'border-line bg-ink-800 text-fg2'}`}>{v}</span>
);

/** Walks through the recorded split/merge events of a Merge Sort run. */
export function MergeTrace({ events, input, describe }: { events: MergeEvent[]; input: (string | number)[]; describe?: (id: string | number) => string }) {
  const [step, setStep] = useState(0);
  const shown = events.slice(0, step);
  const cur = shown[shown.length - 1];
  const fmt = (v: string | number) => (describe ? describe(v) : String(v));
  const row = (items: (string | number)[], cls?: string) => <div className="flex flex-wrap gap-1">{items.map((v, i) => <span key={`${v}-${i}`} className={`rounded-md border px-1.5 py-0.5 text-[12px] tabular-nums ${cls ?? 'border-line bg-ink-800 text-fg2'}`}>{fmt(v)}</span>)}</div>;
  return (
    <div className="space-y-3">
      <StepControls step={step} max={events.length} onChange={setStep} />
      <div className="rounded-lg border border-line bg-ink-900/70 p-3 text-[13px]">
        {!cur && <div className="text-fg3">Press Play or Next. The input is split in halves (divide), then merged back in order (combine).</div>}
        {cur?.type === 'split' && (<div><span className="font-semibold text-accent">Split</span> <span className="text-fg3">(depth {cur.depth})</span> into two halves:
          <div className="mt-2 flex flex-wrap items-center gap-3">{row(cur.left)}<span className="text-fg3">|</span>{row(cur.right)}</div></div>)}
        {cur?.type === 'merge' && (<div><span className="font-semibold text-good">Merge</span> <span className="text-fg3">(depth {cur.depth})</span>: repeatedly take the smaller front element
          <div className="mt-2 flex flex-wrap items-center gap-3">{row(cur.left)}<span className="text-fg3">+</span>{row(cur.right)}<span className="text-fg3">=</span>{row(cur.result ?? [], 'border-good/50 bg-good/10 text-good')}</div></div>)}
      </div>
      <div className="max-h-64 space-y-1 overflow-auto pr-1">
        <div className="flex items-center gap-2 text-xs text-fg3"><span className="w-20 shrink-0">Input</span>{row(input)}</div>
        {shown.map((e, i) => (
          <div key={i} className={`flex items-start gap-2 rounded-md px-1 py-0.5 text-xs ${i === shown.length - 1 ? 'bg-accent/10' : ''}`} style={{ paddingLeft: 4 + e.depth * 14 }}>
            <span className={`w-16 shrink-0 font-medium ${e.type === 'split' ? 'text-accent' : 'text-good'}`}>{e.type === 'split' ? 'split' : 'merge'} d{e.depth}</span>
            {e.type === 'split' ? <><span className="text-fg3">{e.left.length} + {e.right.length} items</span></> : row(e.result ?? [], 'border-good/40 bg-good/10 text-good')}
          </div>
        ))}
      </div>
    </div>
  );
}

/** Colour-coded dp[i][w] table with the reconstruction path highlighted. */
export function DpTable({ table, weights, values, labels }: { table: number[][]; weights: number[]; values: number[]; labels: string[] }) {
  const n = weights.length, cap = table[0].length - 1;
  // Walk back from (n, cap): item i was taken when dp[i][w] differs from dp[i-1][w].
  const taken = new Set<number>(), path = new Set<string>();
  let w = cap;
  for (let i = n; i >= 1; i--) {
    path.add(`${i},${w}`);
    if (table[i][w] !== table[i - 1][w]) { taken.add(i); w -= weights[i - 1]; }
  }
  path.add(`0,${w}`);
  const max = Math.max(1, table[n][cap]);
  return (
    <div className="max-h-[420px] overflow-auto rounded-lg border border-line">
      <table className="border-collapse text-[11px] tabular-nums">
        <thead>
          <tr>
            <th className="sticky left-0 top-0 z-20 min-w-[150px] bg-[#0d1730] px-2 py-1.5 text-left text-fg3">item (wt, value) \ capacity</th>
            {table[0].map((_, c) => <th key={c} className="sticky top-0 z-10 min-w-[34px] bg-[#0d1730] px-1 py-1.5 text-center font-medium text-fg3">{c}</th>)}
          </tr>
        </thead>
        <tbody>
          {table.map((row, i) => (
            <tr key={i}>
              <th className={`sticky left-0 z-10 whitespace-nowrap bg-[#0d1730] px-2 py-1 text-left font-medium ${taken.has(i) ? 'text-good' : 'text-fg2'}`}>
                {i === 0 ? 'no items' : `${labels[i - 1]} (${weights[i - 1]}, ${values[i - 1]})`}{taken.has(i) && ' ✓'}
              </th>
              {row.map((v, c) => (
                <td key={c} className={`px-1 py-1 text-center ${path.has(`${i},${c}`) ? 'font-semibold text-white ring-1 ring-inset ring-accent' : 'text-fg2'}`}
                  style={{ background: `rgba(34,211,238,${(v / max) * 0.32})` }} title={`dp[${i}][${c}] = ${v}`}>{v}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export const Recurrence = () => (
  <div className="rounded-lg border border-line bg-ink-900/70 p-3 font-mono text-[12.5px] leading-6 text-fg2">
    <div><span className="text-fg3">if</span> wt<sub>i</sub> &gt; w :   dp[i][w] = dp[i-1][w]</div>
    <div><span className="text-fg3">else</span>      :   dp[i][w] = max( dp[i-1][w],  dp[i-1][w - wt<sub>i</sub>] + val<sub>i</sub> )</div>
    <div className="text-fg3">dp[0][w] = 0 &nbsp;·&nbsp; answer = dp[n][capacity] &nbsp;·&nbsp; val<sub>i</sub> = delivery value × priority</div>
  </div>
);
