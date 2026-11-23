// Algorithm learning centre: concept, pseudocode, recurrence, complexity, viva questions and live demos that call the real algorithms.
import { useCallback, useEffect, useState, type ReactElement } from 'react';
import { api, errorMessage } from '../api';
import { GraphCanvas } from '../components/GraphCanvas';
import { DpTable, MergeTrace, StepControls } from '../components/viz';
import { Badge, Button, Card, Field, Notice, PageHeader, Spinner, Tabs } from '../components/ui';
import { fmt } from '../lib';
import type { DijkstraDemo, KnapsackDemo, LearnAlgo, MergeDemo, NnDemo } from '../types';

const nums = (s: string) => s.split(/[\s,]+/).filter(Boolean).map(Number);
const validInts = (a: number[], min: number) => a.length > 0 && a.every((n) => Number.isInteger(n) && n >= min);

function MergeDemoPanel() {
  const [text, setText] = useState('38, 27, 43, 3, 9, 82, 10');
  const [demo, setDemo] = useState<MergeDemo | null>(null);
  const [err, setErr] = useState('');
  const run = useCallback(async (t: string) => {
    const v = nums(t);
    if (!validInts(v, -1_000_000) || v.length > 16) { setErr('Enter 1 to 16 whole numbers separated by commas'); return; }
    try { setDemo(await api.post<MergeDemo>('/api/learn/merge-sort', { values: v })); setErr(''); } catch (e) { setErr(errorMessage(e)); }
  }, []);
  useEffect(() => { void run('38, 27, 43, 3, 9, 82, 10'); }, [run]);
  return (
    <div>
      <form className="flex flex-wrap items-end gap-3" onSubmit={(e) => { e.preventDefault(); void run(text); }}>
        <div className="w-96 max-w-full"><Field label="Numbers to sort (max 16)" error={err}>{(id, bad) => <input id={id} className="input" aria-invalid={bad} value={text} onChange={(e) => setText(e.target.value)} />}</Field></div>
        <Button type="submit" variant="primary" icon="sort">Trace Merge Sort</Button>
      </form>
      {demo && <div className="mt-4"><div className="mb-3 text-[13px] text-fg2">Sorted: <b className="font-mono text-fg">{demo.output.join(', ')}</b> · {demo.comparisons} comparisons</div>
        <MergeTrace key={demo.input.join(',')} events={demo.steps} input={demo.input} /></div>}
    </div>
  );
}

function KnapsackDemoPanel() {
  const [f, setF] = useState({ w: '1, 3, 4, 5', v: '1, 4, 5, 7', c: '7' });
  const [demo, setDemo] = useState<KnapsackDemo | null>(null);
  const [err, setErr] = useState('');
  const run = useCallback(async (w: string, v: string, c: string) => {
    const W = nums(w), V = nums(v), cap = Number(c);
    if (!validInts(W, 1) || W.length > 8) return setErr('Weights: 1 to 8 whole numbers, each at least 1');
    if (!validInts(V, 0) || V.length !== W.length) return setErr('Values: whole numbers, one per weight');
    if (!Number.isInteger(cap) || cap < 0 || cap > 30) return setErr('Capacity: a whole number from 0 to 30');
    try { setDemo(await api.post<KnapsackDemo>('/api/learn/knapsack', { weights: W, values: V, capacity: cap })); setErr(''); } catch (e) { setErr(errorMessage(e)); }
  }, []);
  useEffect(() => { void run('1, 3, 4, 5', '1, 4, 5, 7', '7'); }, [run]);
  return (
    <div>
      <form className="flex flex-wrap items-end gap-3" onSubmit={(e) => { e.preventDefault(); void run(f.w, f.v, f.c); }}>
        <div className="w-56"><Field label="Weights">{(id) => <input id={id} className="input" value={f.w} onChange={(e) => setF({ ...f, w: e.target.value })} />}</Field></div>
        <div className="w-56"><Field label="Values">{(id) => <input id={id} className="input" value={f.v} onChange={(e) => setF({ ...f, v: e.target.value })} />}</Field></div>
        <div className="w-28"><Field label="Capacity">{(id) => <input id={id} className="input" value={f.c} onChange={(e) => setF({ ...f, c: e.target.value })} />}</Field></div>
        <Button type="submit" variant="primary" icon="scale">Fill DP table</Button>
      </form>
      {err && <div className="mt-3"><Notice tone="bad" title="Check the inputs">{err}</Notice></div>}
      {demo && <div className="mt-4 space-y-3">
        <div className="text-[13px] text-fg2">Best value <b className="text-fg">{demo.best_value}</b> using items <b className="text-fg">{demo.selected.map((i) => i + 1).join(', ') || 'none'}</b> (total weight {demo.total_weight} of {demo.capacity}). The highlighted cells are the backtracking path.</div>
        {demo.table && <DpTable table={demo.table} weights={demo.weights} values={demo.values} labels={demo.weights.map((_, i) => `item ${i + 1}`)} />}
      </div>}
    </div>
  );
}

function DijkstraDemoPanel() {
  const [src, setSrc] = useState('A');
  const [dst, setDst] = useState('F');
  const [demo, setDemo] = useState<DijkstraDemo | null>(null);
  const [step, setStep] = useState(0);
  const [err, setErr] = useState('');
  useEffect(() => { setStep(0); api.post<DijkstraDemo>('/api/learn/dijkstra', { source: src, target: dst }).then((d) => { setDemo(d); setErr(''); }).catch((e) => setErr(errorMessage(e))); }, [src, dst]);
  if (!demo) return err ? <Notice tone="bad" title="Demo failed">{err}</Notice> : <Spinner />;
  const names = demo.locations.map((l) => l.name);
  const cur = step > 0 ? demo.steps[step - 1] : null;
  const done = step >= demo.steps.length;
  const labels = cur ? Object.fromEntries(Object.entries(cur.distances).map(([k, v]) => [k, fmt(v, 1)])) : { [src]: '0' };
  return (
    <div>
      <div className="flex flex-wrap items-end gap-3">
        <div className="w-32"><Field label="Source">{(id) => <select id={id} className="input" value={src} onChange={(e) => setSrc(e.target.value)}>{names.map((n) => <option key={n}>{n}</option>)}</select>}</Field></div>
        <div className="w-32"><Field label="Target">{(id) => <select id={id} className="input" value={dst} onChange={(e) => setDst(e.target.value)}>{names.map((n) => <option key={n}>{n}</option>)}</select>}</Field></div>
        <StepControls step={step} max={demo.steps.length} onChange={setStep} />
      </div>
      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
        <GraphCanvas locations={demo.locations} roads={demo.roads} settled={cur?.settled ?? []} selected={[src]} labels={labels}
          paths={done && demo.path ? [{ path: demo.path, color: '#22d3ee', width: 1.8 }] : []} />
        <div className="text-[13px] text-fg2">
          {!cur ? <p>Press Play or Next. The source starts at distance 0; all other distances are unknown (infinity). Amber labels are the current best-known distances, green nodes are settled.</p> : (
            <>
              <p><b className="text-fg">Step {step}:</b> the closest unsettled location is <b className="text-fg">{cur.visit}</b> at distance <b className="text-fg">{fmt(cur.distance, 1)}</b>; its distance is now final.</p>
              {cur.relaxed.length === 0 ? <p className="mt-2 text-fg3">No unsettled neighbours to relax.</p> : (
                <table className="tbl mt-2"><thead><tr><th>Edge to</th><th className="num">Candidate</th><th className="num">Previous</th><th>Result</th></tr></thead>
                  <tbody>{cur.relaxed.map((r) => <tr key={r.to}><td>{cur.visit} → {r.to}</td><td className="num">{fmt(r.candidate, 1)}</td><td className="num">{r.previous === null ? '∞' : fmt(r.previous, 1)}</td><td>{r.improved ? <Badge tone="good">updated</Badge> : <Badge>kept</Badge>}</td></tr>)}</tbody></table>)}
            </>)}
          {done && <p className="mt-3">{demo.path ? <>Shortest path <b className="text-fg">{demo.path.join(' → ')}</b>, distance <b className="text-fg">{fmt(demo.distance, 1)}</b>.</> : 'The target is not reachable from the source.'}</p>}
        </div>
      </div>
    </div>
  );
}

function NnDemoPanel() {
  const all = ['B', 'C', 'D', 'E', 'F'];
  const [stops, setStops] = useState<string[]>(['B', 'D', 'F']);
  const [demo, setDemo] = useState<NnDemo | null>(null);
  const [step, setStep] = useState(0);
  const [err, setErr] = useState('');
  useEffect(() => {
    setStep(0);
    if (!stops.length) { setErr('Pick at least one stop'); return; }
    api.post<NnDemo>('/api/learn/nearest-neighbour', { source: 'A', stops }).then((d) => { setDemo(d); setErr(''); }).catch((e) => setErr(errorMessage(e)));
  }, [stops]);
  const toggle = (n: string) => setStops((s) => (s.includes(n) ? s.filter((x) => x !== n) : [...s, n]));
  const cur = demo && step > 0 ? demo.steps[step - 1] : null;
  const shown = demo ? demo.legs.slice(0, step) : [];
  return (
    <div>
      <div className="flex flex-wrap items-center gap-4">
        <fieldset className="flex items-center gap-2"><legend className="sr-only">Stops to visit</legend><span className="text-xs font-medium text-fg2">Stops (depot = A):</span>
          {all.map((n) => <label key={n} className={`cursor-pointer rounded-lg border px-3 py-1 text-[13px] ${stops.includes(n) ? 'border-accent-strong bg-accent/10 text-accent' : 'border-line text-fg2'}`}><input type="checkbox" className="sr-only" checked={stops.includes(n)} onChange={() => toggle(n)} />{n}</label>)}</fieldset>
        {demo && !err && <StepControls step={step} max={demo.steps.length} onChange={setStep} />}
      </div>
      {err && <div className="mt-3"><Notice tone="warn" title="Cannot trace">{err}</Notice></div>}
      {demo && !err && (
        <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
          <GraphCanvas locations={demo.locations} roads={demo.roads} depot="A" stops={demo.order.slice(0, step)} emphasised={stops}
            paths={[...shown, ...(step >= demo.steps.length && demo.return_leg ? [demo.return_leg] : [])].map((l) => ({ path: l.path, color: '#22d3ee', width: 1.7 }))} />
          <div className="text-[13px] text-fg2">
            {!cur ? <p>The tour starts at depot A. At each step the nearest unvisited stop (by Dijkstra road distance) is chosen.</p> : (
              <>
                <p><b className="text-fg">Step {step}:</b> from <b className="text-fg">{cur.from}</b> the candidate distances are
                  {' '}{cur.candidates.map((c) => `${c.stop} = ${fmt(c.distance, 1)}`).join(', ') || 'none'}; the nearest is <b className="text-fg">{cur.chosen ?? 'none'}</b>.</p>
                {cur.unreachable.length > 0 && <p className="mt-2 text-warn">Unreachable: {cur.unreachable.join(', ')}</p>}
              </>)}
            {step >= demo.steps.length && <p className="mt-3">Order <b className="text-fg">A → {demo.order.join(' → ')}{demo.return_leg ? ' → A' : ''}</b>, total <b className="text-fg">{fmt(demo.total_distance, 1)}</b>. Nearest Neighbour is a heuristic; a different order may be shorter.</p>}
          </div>
        </div>)}
    </div>
  );
}

const DEMOS: Record<string, () => ReactElement> = { 'merge-sort': MergeDemoPanel, knapsack: KnapsackDemoPanel, dijkstra: DijkstraDemoPanel, 'nearest-neighbour': NnDemoPanel };

export function Learn() {
  const [algos, setAlgos] = useState<LearnAlgo[] | null>(null);
  const [id, setId] = useState('merge-sort');
  const [error, setError] = useState('');
  const [open, setOpen] = useState<number | null>(0);
  useEffect(() => { api.get<{ algorithms: LearnAlgo[] }>('/api/learn/content').then((r) => setAlgos(r.algorithms)).catch((e) => setError(errorMessage(e))); }, []);
  if (error) return <Notice tone="bad" title="Cannot load the learning centre">{error}</Notice>;
  if (!algos) return <Spinner />;
  const a = algos.find((x) => x.id === id) ?? algos[0];
  const Demo = DEMOS[a.id];
  return (
    <>
      <PageHeader title="Algorithm learning centre" subtitle="Everything needed to explain each algorithm in a viva: concept, working principle, pseudocode, recurrence, complexity, an interactive trace and likely questions." />
      <Tabs tabs={algos.map((x) => ({ id: x.id, label: x.name.split(' (')[0] }))} value={a.id} onChange={(v) => { setId(v); setOpen(0); }} />
      <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-3">
        <div className="space-y-4 xl:col-span-2">
          <Card title={a.name} actions={<Badge tone="info">{a.phase}</Badge>} subtitle={a.role}>
            <p className="text-[13.5px] text-fg2">{a.concept}</p>
            <h4 className="mb-1.5 mt-4 text-xs font-semibold uppercase tracking-wider text-fg3">Working principle</h4>
            <ol className="list-decimal space-y-1 pl-5 text-[13px] text-fg2">{a.principle.map((p, i) => <li key={i}>{p}</li>)}</ol>
          </Card>
          <Card title="Interactive example" subtitle="Runs the same implementation the planner uses">{Demo && <Demo key={a.id} />}</Card>
          <Card title="Pseudocode"><pre className="overflow-x-auto rounded-lg border border-line bg-ink-900/80 p-3 font-mono text-[12.5px] leading-6 text-fg2">{a.pseudocode}</pre></Card>
        </div>
        <div className="space-y-4">
          <Card title="Recurrence"><pre className="overflow-x-auto whitespace-pre-wrap font-mono text-[12.5px] leading-6 text-accent">{a.recurrence}</pre></Card>
          <Card title="Complexity" pad={false}>
            <table className="tbl"><tbody>
              <tr><td className="text-fg3">Best case</td><td>{a.time.best}</td></tr><tr><td className="text-fg3">Average case</td><td>{a.time.average}</td></tr>
              <tr><td className="text-fg3">Worst case</td><td>{a.time.worst}</td></tr><tr><td className="text-fg3">Space</td><td className="whitespace-normal">{a.space}</td></tr></tbody></table>
          </Card>
          <Card title="Notes"><ul className="list-disc space-y-1.5 pl-4 text-[13px] text-fg2">{a.notes.map((n, i) => <li key={i}>{n}</li>)}</ul></Card>
          <Card title="Viva questions" subtitle="Click a question to reveal the answer" pad={false}>
            <div className="divide-y divide-line">{a.viva.map((v, i) => (
              <div key={i}><button className="flex w-full items-start justify-between gap-3 px-5 py-3 text-left text-[13px] font-medium hover:bg-white/[0.02]" aria-expanded={open === i} onClick={() => setOpen(open === i ? null : i)}>{v.q}<span className="text-fg3">{open === i ? '−' : '+'}</span></button>
                {open === i && <p className="px-5 pb-4 text-[13px] text-fg2">{v.a}</p>}</div>))}</div>
          </Card>
        </div>
      </div>
    </>
  );
}
