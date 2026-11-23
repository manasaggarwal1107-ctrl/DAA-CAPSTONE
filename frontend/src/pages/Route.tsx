// Phase 3 - route maker: Nearest Neighbour tour built from Dijkstra shortest paths between selected destinations.
import { useState, type FormEvent } from 'react';
import { api, errorMessage } from '../api';
import { GraphCanvas } from '../components/GraphCanvas';
import { Badge, Button, Card, Empty, Field, Notice, PageHeader, Stat } from '../components/ui';
import { fmt, fmtDate, fmtMs } from '../lib';
import { useApp } from '../store';

export function RoutePage() {
  const { state, result, optimise, running, refresh, toast } = useApp();
  const s = state!.settings, names = state!.graph.locations.map((l) => l.name);
  const [form, setForm] = useState({ capacity: String(s.capacity), depot: s.depot, dispatch_time: s.dispatch_time, speed_kmph: String(s.speed_kmph), service_minutes: String(s.service_minutes) });
  const [errors, setErrors] = useState<Record<string, string>>({});

  const check = () => {
    const e: Record<string, string> = {};
    if (!/^\d+$/.test(form.capacity.trim())) e.capacity = 'Whole number of kg, 0 or more';
    const sp = Number(form.speed_kmph);
    if (form.speed_kmph.trim() === '' || Number.isNaN(sp) || sp <= 0 || sp > 200) e.speed_kmph = 'Between 0 and 200 km/h';
    if (!/^\d+$/.test(form.service_minutes.trim()) || Number(form.service_minutes) > 240) e.service_minutes = '0 to 240 minutes';
    if (!form.dispatch_time) e.dispatch_time = 'Choose a dispatch time';
    return e;
  };

  const submit = async (ev: FormEvent) => {
    ev.preventDefault();
    const e = check();
    setErrors(e);
    if (Object.keys(e).length) return;
    try {
      await api.put('/api/settings', { dispatch_time: form.dispatch_time, speed_kmph: Number(form.speed_kmph), service_minutes: Number(form.service_minutes) });
      await refresh();
      await optimise({ capacity: Number(form.capacity), depot: form.depot });
    } catch (er) { toast(errorMessage(er), 'bad'); }
  };

  const route = result?.route;
  const paths = route ? [...route.legs, ...(route.return_leg ? [route.return_leg] : [])].map((l, i) => ({ path: l.path, color: i === route.legs.length ? '#a78bfa' : '#22d3ee', width: 1.7 })) : [];

  return (
    <>
      <PageHeader title="Route planner" subtitle="Starting at the depot, the vehicle repeatedly drives to the nearest unvisited delivery location (by Dijkstra road distance), then returns to the depot when a road back exists." />
      <Card className="mb-4" title="Dispatch settings" subtitle="Saved and used by the next optimisation run">
        <form className="grid grid-cols-2 items-end gap-4 md:grid-cols-3 xl:grid-cols-6" onSubmit={submit} noValidate>
          <Field label="Vehicle capacity (kg)" error={errors.capacity}>{(id, bad) => <input id={id} className="input" aria-invalid={bad} value={form.capacity} onChange={(e) => setForm({ ...form, capacity: e.target.value })} />}</Field>
          <Field label="Depot">{(id) => <select id={id} className="input" value={form.depot} onChange={(e) => setForm({ ...form, depot: e.target.value })}>{names.map((n) => <option key={n}>{n}</option>)}</select>}</Field>
          <Field label="Dispatch time" error={errors.dispatch_time}>{(id, bad) => <input id={id} type="datetime-local" className="input" aria-invalid={bad} value={form.dispatch_time} onChange={(e) => setForm({ ...form, dispatch_time: e.target.value })} />}</Field>
          <Field label="Average speed (km/h)" error={errors.speed_kmph}>{(id, bad) => <input id={id} className="input" aria-invalid={bad} value={form.speed_kmph} onChange={(e) => setForm({ ...form, speed_kmph: e.target.value })} />}</Field>
          <Field label="Minutes per stop" error={errors.service_minutes}>{(id, bad) => <input id={id} className="input" aria-invalid={bad} value={form.service_minutes} onChange={(e) => setForm({ ...form, service_minutes: e.target.value })} />}</Field>
          <Button type="submit" variant="primary" icon="zap" busy={running}>Save &amp; optimise</Button>
        </form>
      </Card>

      {!result || !route ? (
        <Card><Empty icon="route" title="No route yet">Press “Save &amp; optimise” to select parcels and build the delivery route.</Empty></Card>
      ) : (
        <>
          {result.stale && <div className="mb-4"><Notice tone="warn" title="Data changed since this route was built">Run the optimisation again to refresh it.</Notice></div>}
          {result.warnings.length > 0 && <div className="mb-4"><Notice tone="warn" title="Warnings">{result.warnings.join(' ')}</Notice></div>}
          {result.undeliverable.length > 0 && <div className="mb-4"><Notice tone="bad" title="Undeliverable parcels">No road path connects the depot to: {result.unreachable.join(', ')}. Their {result.undeliverable.length} parcel(s) were excluded before the knapsack, so they are not loaded, not counted in the selected weight or value, and not on the route.</Notice></div>}
          {!route.returned_to_depot && route.order.length > 0 && <div className="mb-4"><Notice tone="warn" title="No road back to the depot">The tour ends at the last stop because no return path exists in the road network.</Notice></div>}
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-5">
            <div className="card p-4"><Stat label="Total route distance" value={`${fmt(route.total_distance, 1)} km`} /></div>
            <div className="card p-4"><Stat label="Delivery stops" value={route.order.length} /></div>
            <div className="card p-4"><Stat label="Dijkstra runs" value={route.dijkstra_runs} /></div>
            <div className="card p-4"><Stat label="Routing time" value={fmtMs(result.timings_ms.routing)} /></div>
            <div className="card p-4"><Stat label="Estimated on time / late" value={<span><span className="text-good">{route.on_time}</span> / <span className={route.late ? 'text-bad' : ''}>{route.late}</span></span>} /></div>
          </div>
          <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-3">
            <Card className="xl:col-span-2" title="Delivery route" subtitle="Cyan = outbound legs, violet = return to depot; numbered circles are delivery stops in visiting order">
              <GraphCanvas locations={state!.graph.locations} roads={state!.graph.roads} depot={route.depot} stops={route.order} paths={paths} dimOthers />
            </Card>
            <Card title="An approximation, not the optimum">
              <p className="text-[13px] text-fg2">{route.note}</p>
              <ul className="mt-3 list-disc space-y-1.5 pl-4 text-[13px] text-fg2">
                <li>The Travelling Salesman Problem is NP-hard: exact tours need exponential time as stops grow.</li>
                <li>Nearest Neighbour needs only one Dijkstra run per stop, about O(k · (V + E) log V) for k stops, but a greedy early choice can force a long detour later.</li>
                <li>Locations without selected parcels are not visited unless a road passes through them.</li>
              </ul>
            </Card>
          </div>
          <div className="mt-4 grid grid-cols-1 gap-4 xl:grid-cols-2">
            <Card title="Route legs" subtitle="Shortest road path between consecutive stops" pad={false}>
              {route.legs.length === 0 ? <Empty icon="route" title="No legs">{result.status === 'no_parcels' ? 'There are no pending parcels.' : 'No delivery location needs a visit.'}</Empty> : (
                <div className="max-h-[400px] overflow-auto"><table className="tbl"><thead><tr><th>#</th><th>From → To</th><th>Road path</th><th className="num">km</th><th className="num">Total</th></tr></thead>
                  <tbody>{[...route.legs, ...(route.return_leg ? [route.return_leg] : [])].map((l, i) => (
                    <tr key={i}><td className="text-fg3">{i < route.legs.length ? i + 1 : <Badge tone="info">back</Badge>}</td><td className="font-medium">{l.from} → {l.to}</td>
                      <td className="whitespace-normal text-fg2">{l.path.join(' → ')}</td><td className="num">{fmt(l.distance, 2)}</td><td className="num text-fg3">{fmt(l.cumulative, 2)}</td></tr>))}</tbody></table></div>)}
            </Card>
            <Card title="Deliveries and estimated arrival" subtitle="ETA = dispatch + distance ÷ speed + stop time; an estimate, not a measurement" pad={false}>
              {route.deliveries.length === 0 ? <Empty icon="package" title="No deliveries">Nothing was selected.</Empty> : (
                <div className="max-h-[400px] overflow-auto"><table className="tbl"><thead><tr><th>Stop</th><th>Parcels</th><th>ETA</th><th>Deadline check</th></tr></thead>
                  <tbody>{route.deliveries.map((d, i) => (
                    <tr key={d.destination}><td className="font-medium">{i + 1}. {d.destination}</td><td className="whitespace-normal text-fg2">{d.parcels.join(', ')}</td><td className="text-fg2">{fmtDate(d.eta)}</td>
                      <td>{d.late.length ? <Badge tone="bad">{d.late.length} late: {d.late.join(', ')}</Badge> : <Badge tone="good">on time</Badge>}</td></tr>))}</tbody></table></div>)}
            </Card>
          </div>
        </>
      )}
    </>
  );
}
