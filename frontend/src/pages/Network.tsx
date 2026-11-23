// Phase 3 - road network: weighted graph editor, adjacency list and Dijkstra shortest-path finder.
import { useEffect, useState, type FormEvent } from 'react';
import { api, errorMessage } from '../api';
import { GraphCanvas } from '../components/GraphCanvas';
import { Badge, Button, Card, Empty, Field, Notice, PageHeader, Stat } from '../components/ui';
import { fmt } from '../lib';
import { useApp } from '../store';
import type { GraphWithAdjacency, PathResponse } from '../types';

export function Network() {
  const { state, refresh, toast } = useApp();
  const graphState = state!.graph, depot = state!.settings.depot;
  const names = graphState.locations.map((l) => l.name);
  const [adj, setAdj] = useState<GraphWithAdjacency | null>(null);
  const [locForm, setLocForm] = useState({ name: '', x: '50', y: '50' });
  const [roadForm, setRoadForm] = useState({ a: names[0] ?? '', b: names[1] ?? '', weight: '', bidirectional: true });
  const [pathForm, setPathForm] = useState({ source: depot, target: names.find((n) => n !== depot) ?? '' });
  const [path, setPath] = useState<PathResponse | null>(null);
  const [err, setErr] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);

  useEffect(() => { void api.get<GraphWithAdjacency>('/api/graph').then(setAdj).catch((e) => toast(errorMessage(e), 'bad')); }, [state?.graph, toast]);
  const stale = (n: string) => !names.includes(n);
  useEffect(() => {
    setRoadForm((f) => ({ ...f, a: stale(f.a) ? names[0] ?? '' : f.a, b: stale(f.b) ? names[1] ?? '' : f.b }));
    setPathForm((f) => ({ source: stale(f.source) ? depot : f.source, target: stale(f.target) ? names.find((n) => n !== depot) ?? '' : f.target }));
  }, [graphState.locations.length]);   // eslint-disable-line react-hooks/exhaustive-deps

  const act = async (fn: () => Promise<unknown>, ok: string) => {
    setBusy(true);
    try { await fn(); toast(ok, 'good'); setPath(null); await refresh(); return true; }
    catch (e) { toast(errorMessage(e), 'bad'); return false; }
    finally { setBusy(false); }
  };

  const addLocation = async (e: FormEvent) => {
    e.preventDefault();
    const problems: Record<string, string> = {};
    const x = Number(locForm.x), y = Number(locForm.y);
    if (!locForm.name.trim()) problems.name = 'Enter a location name';
    else if (names.some((n) => n.toLowerCase() === locForm.name.trim().toLowerCase())) problems.name = 'A location with this name already exists';
    if (locForm.x.trim() === '' || Number.isNaN(x) || x < 0 || x > 100) problems.x = '0 to 100';
    if (locForm.y.trim() === '' || Number.isNaN(y) || y < 0 || y > 100) problems.y = '0 to 100';
    setErr(problems);
    if (Object.keys(problems).length) return;
    if (await act(() => api.post('/api/graph/locations', { name: locForm.name.trim(), x, y }), `Added ${locForm.name.trim()}`)) setLocForm({ name: '', x: '50', y: '50' });
  };

  const roadProblem = () => {
    const w = Number(roadForm.weight);
    if (!roadForm.a || !roadForm.b) return 'Choose two locations';
    if (roadForm.a === roadForm.b) return 'A road must join two different locations';
    if (roadForm.weight.trim() === '' || Number.isNaN(w)) return 'Enter the road length in km';
    if (w < 0) return 'Negative road lengths are not allowed: Dijkstra requires non-negative weights';
    return '';
  };
  const addRoad = async (e: FormEvent) => {
    e.preventDefault();
    const p = roadProblem();
    setErr({ road: p });
    if (p) return;
    await act(() => api.post('/api/graph/roads', { a: roadForm.a, b: roadForm.b, weight: Number(roadForm.weight), bidirectional: roadForm.bidirectional }), `Road ${roadForm.a} - ${roadForm.b} saved`);
  };

  const findPath = async (e: FormEvent) => {
    e.preventDefault();
    setBusy(true);
    try { setPath(await api.post<PathResponse>('/api/graph/shortest-path', pathForm)); }
    catch (er) { toast(errorMessage(er), 'bad'); }
    finally { setBusy(false); }
  };

  const setDepot = async (name: string) => { await act(() => api.put('/api/settings', { depot: name }), `Depot set to ${name}`); };
  const removeLocation = async (name: string) => {
    setBusy(true);
    try {
      const r = await api.del<{ affected_parcels: number }>(`/api/graph/locations/${encodeURIComponent(name)}`);
      toast(r.affected_parcels ? `Removed ${name}; ${r.affected_parcels} parcel(s) now point to an unknown location` : `Removed ${name}`, r.affected_parcels ? 'info' : 'good');
      setPath(null); await refresh();
    } catch (er) { toast(errorMessage(er), 'bad'); } finally { setBusy(false); }
  };

  return (
    <>
      <PageHeader title="Road network" subtitle="Roads are stored as a weighted adjacency list. Dijkstra's algorithm (binary min-heap) finds the shortest road path between any two locations; negative lengths are rejected." />
      <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        <div className="space-y-4 xl:col-span-2">
          <Card title="Network map" subtitle="Click a location to use it as path source (then target). Click an empty spot of the map to fill the coordinates of the new location."
            actions={<span className="flex items-center gap-2 text-xs text-fg3"><Badge tone="info">{names.length} locations</Badge><Badge>{graphState.roads.length} roads</Badge></span>}>
            <GraphCanvas locations={graphState.locations} roads={graphState.roads} depot={depot}
              paths={path?.reachable ? [{ path: path.path, color: '#22d3ee', width: 1.6 }] : []}
              selected={[pathForm.source, pathForm.target]}
              onNodeClick={(n) => setPathForm((f) => (f.source === depot || f.source === n ? { ...f, source: n } : { ...f, target: n }))}
              onCanvasClick={(x, y) => setLocForm((f) => ({ ...f, x: String(x), y: String(y) }))} />
          </Card>
          <Card title="Shortest path (Dijkstra)" subtitle="Single-source shortest path with early exit at the target">
            <form className="flex flex-wrap items-end gap-3" onSubmit={findPath}>
              <div className="w-48"><Field label="From">{(id) => <select id={id} className="input" value={pathForm.source} onChange={(e) => setPathForm({ ...pathForm, source: e.target.value })}>{names.map((n) => <option key={n}>{n}</option>)}</select>}</Field></div>
              <div className="w-48"><Field label="To">{(id) => <select id={id} className="input" value={pathForm.target} onChange={(e) => setPathForm({ ...pathForm, target: e.target.value })}>{names.map((n) => <option key={n}>{n}</option>)}</select>}</Field></div>
              <Button type="submit" variant="primary" icon="route" busy={busy} disabled={!pathForm.source || !pathForm.target}>Find shortest path</Button>
            </form>
            {path && (path.reachable ? (
              <div className="mt-4">
                <div className="flex flex-wrap items-center gap-6"><Stat label="Total distance" value={`${fmt(path.distance, 2)} km`} /><Stat label="Roads used" value={path.hops?.length ?? 0} /></div>
                <div className="mt-3 flex flex-wrap items-center gap-1.5 text-[13px]">{path.path.map((n, i) => <span key={i} className="flex items-center gap-1.5"><Badge tone={i === 0 ? 'good' : i === path.path.length - 1 ? 'info' : 'neutral'}>{n}</Badge>{i < path.path.length - 1 && <span className="text-fg3">→</span>}</span>)}</div>
                {path.hops && path.hops.length > 0 && <table className="tbl mt-3"><thead><tr><th>From</th><th>To</th><th className="num">Road length (km)</th></tr></thead><tbody>{path.hops.map((h, i) => <tr key={i}><td>{h.from}</td><td>{h.to}</td><td className="num">{fmt(h.distance, 2)}</td></tr>)}</tbody></table>}
              </div>
            ) : <div className="mt-4"><Notice tone="warn" title="No route exists">{path.message}</Notice></div>)}
          </Card>
        </div>

        <div className="space-y-4">
          <Card title="Add a location">
            <form className="space-y-3" onSubmit={addLocation} noValidate>
              <Field label="Name" error={err.name}>{(id, bad) => <input id={id} className="input" aria-invalid={bad} value={locForm.name} onChange={(e) => setLocForm({ ...locForm, name: e.target.value })} placeholder="e.g. Airport" />}</Field>
              <div className="grid grid-cols-2 gap-3">
                <Field label="X (0-100)" error={err.x}>{(id, bad) => <input id={id} className="input" aria-invalid={bad} inputMode="decimal" value={locForm.x} onChange={(e) => setLocForm({ ...locForm, x: e.target.value })} />}</Field>
                <Field label="Y (0-100)" error={err.y}>{(id, bad) => <input id={id} className="input" aria-invalid={bad} inputMode="decimal" value={locForm.y} onChange={(e) => setLocForm({ ...locForm, y: e.target.value })} />}</Field>
              </div>
              <Button type="submit" icon="plus" busy={busy}>Add location</Button>
            </form>
          </Card>
          <Card title="Add a road" subtitle="Adding a road between two connected locations replaces its length">
            <form className="space-y-3" onSubmit={addRoad} noValidate>
              <div className="grid grid-cols-2 gap-3">
                <Field label="From">{(id) => <select id={id} className="input" value={roadForm.a} onChange={(e) => setRoadForm({ ...roadForm, a: e.target.value })}>{names.map((n) => <option key={n}>{n}</option>)}</select>}</Field>
                <Field label="To">{(id) => <select id={id} className="input" value={roadForm.b} onChange={(e) => setRoadForm({ ...roadForm, b: e.target.value })}>{names.map((n) => <option key={n}>{n}</option>)}</select>}</Field>
              </div>
              <Field label="Length (km)" error={err.road}>{(id, bad) => <input id={id} className="input" aria-invalid={bad} inputMode="decimal" value={roadForm.weight} onChange={(e) => setRoadForm({ ...roadForm, weight: e.target.value })} />}</Field>
              <label className="flex items-center gap-2 text-[13px] text-fg2"><input type="checkbox" className="accent-cyan-400" checked={roadForm.bidirectional} onChange={(e) => setRoadForm({ ...roadForm, bidirectional: e.target.checked })} />Two-way road</label>
              <Button type="submit" icon="plus" busy={busy}>Save road</Button>
            </form>
          </Card>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-2">
        <Card title="Locations" subtitle="Choose the depot; remove locations you no longer serve" pad={false}>
          {names.length === 0 ? <Empty icon="pin" title="No locations">Add a location to begin.</Empty> : (
            <div className="max-h-[360px] overflow-auto"><table className="tbl"><thead><tr><th>Location</th><th className="num">x</th><th className="num">y</th><th /><th /></tr></thead>
              <tbody>{graphState.locations.map((l) => (
                <tr key={l.name}><td className="font-medium">{l.name} {l.name === depot && <Badge tone="info">Depot</Badge>}</td><td className="num">{l.x}</td><td className="num">{l.y}</td>
                  <td>{l.name !== depot && <Button className="!py-1 text-xs" onClick={() => void setDepot(l.name)}>Make depot</Button>}</td>
                  <td>{l.name !== depot && <button className="btn btn-ghost !p-1.5 text-bad" aria-label={`Remove ${l.name}`} onClick={() => void removeLocation(l.name)}>Remove</button>}</td></tr>))}</tbody></table></div>)}
        </Card>
        <Card title="Roads and adjacency list" subtitle="Each location lists its neighbours with road length (km)" pad={false}>
          <div className="max-h-[360px] overflow-auto">
            <table className="tbl"><thead><tr><th>Location</th><th>Neighbours (km)</th></tr></thead>
              <tbody>{adj && names.map((n) => <tr key={n}><td className="font-medium">{n}</td><td className="whitespace-normal text-fg2">{adj.adjacency[n]?.length ? adj.adjacency[n].map((e) => `${e.to} (${e.weight})`).join(', ') : <span className="text-fg3">isolated</span>}</td></tr>)}</tbody></table>
            <table className="tbl"><thead><tr><th>Road</th><th className="num">km</th><th>Direction</th><th /></tr></thead>
              <tbody>{graphState.roads.map((r) => (
                <tr key={`${r.a}|${r.b}`}><td>{r.a} — {r.b}</td><td className="num">{r.weight}</td><td className="text-fg3">{r.bidirectional === false ? 'one-way' : 'two-way'}</td>
                  <td><button className="btn btn-ghost !p-1.5 text-bad" aria-label={`Remove road ${r.a} to ${r.b}`} onClick={() => void act(() => api.del('/api/graph/roads', { a: r.a, b: r.b, bidirectional: r.bidirectional !== false }), 'Road removed')}>Remove</button></td></tr>))}</tbody></table>
          </div>
        </Card>
      </div>
    </>
  );
}
