import { useMemo, useRef, useState, type FormEvent } from 'react';
import { api, errorMessage, fieldErrors } from '../api';
import { Button, Card, Empty, Field, Modal, Notice, PageHeader, PriorityBadge, StatusBadge } from '../components/ui';
import { Icon } from '../icons';
import { fmt, fmtDate, PRIORITY_LABEL } from '../lib';
import { useApp } from '../store';
import type { ImportResponse, Parcel } from '../types';

type SortKey = 'deadline' | '-deadline' | 'priority' | 'weight' | 'value' | 'id';
const PAGE = 20;

interface Draft { id: string; destination: string; weight: string; priority: string; deadline: string; value: string; status: string }
const blank = (dest: string): Draft => ({ id: '', destination: dest, weight: '', priority: '3', deadline: '2026-12-02T12:00', value: '', status: 'pending' });

/** Client-side checks mirror the server rules so users get instant feedback; the server remains authoritative. */
function validate(d: Draft): Record<string, string> {
  const e: Record<string, string> = {};
  const whole = (s: string) => /^-?\d+$/.test(s.trim());
  if (!d.destination) e.destination = 'Choose a destination';
  if (!d.weight.trim()) e.weight = 'Weight is required'; else if (!whole(d.weight) || Number(d.weight) < 1) e.weight = 'Enter a whole number of kg, at least 1';
  if (!d.value.trim()) e.value = 'Delivery value is required'; else if (!whole(d.value) || Number(d.value) < 0) e.value = 'Enter a whole number, 0 or more';
  if (!d.deadline) e.deadline = 'Deadline is required';
  return e;
}

export function Parcels() {
  const { state, refresh, toast } = useApp();
  const parcels = state!.parcels;
  const locations = state!.graph.locations.map((l) => l.name);
  const [q, setQ] = useState('');
  const [prio, setPrio] = useState('all');
  const [dest, setDest] = useState('all');
  const [status, setStatus] = useState('all');
  const [sort, setSort] = useState<SortKey>('deadline');
  const [page, setPage] = useState(0);
  const [editing, setEditing] = useState<{ parcel: Parcel | null } | null>(null);
  const [deleting, setDeleting] = useState<Parcel | null>(null);
  const [importing, setImporting] = useState(false);
  const [dataset, setDataset] = useState(false);

  const rows = useMemo(() => {
    const needle = q.trim().toLowerCase();
    const list = parcels.filter((p) => (prio === 'all' || p.priority === Number(prio)) && (dest === 'all' || p.destination === dest)
      && (status === 'all' || p.status === status) && (!needle || p.id.toLowerCase().includes(needle) || p.destination.toLowerCase().includes(needle)));
    const cmp: Record<SortKey, (a: Parcel, b: Parcel) => number> = {
      deadline: (a, b) => a.deadline.localeCompare(b.deadline) || a.id.localeCompare(b.id),
      '-deadline': (a, b) => b.deadline.localeCompare(a.deadline) || a.id.localeCompare(b.id),
      priority: (a, b) => b.priority - a.priority || a.id.localeCompare(b.id),
      weight: (a, b) => b.weight - a.weight, value: (a, b) => b.value - a.value, id: (a, b) => a.id.localeCompare(b.id),
    };
    return [...list].sort(cmp[sort]);   // display ordering only; the algorithmic Merge Sort lives on the backend
  }, [parcels, q, prio, dest, status, sort]);
  const pages = Math.max(1, Math.ceil(rows.length / PAGE));
  const shown = rows.slice(Math.min(page, pages - 1) * PAGE, Math.min(page, pages - 1) * PAGE + PAGE);
  const reset = (fn: () => void) => { fn(); setPage(0); };

  const remove = async () => {
    if (!deleting) return;
    try { await api.del(`/api/parcels/${encodeURIComponent(deleting.id)}`); toast(`Deleted ${deleting.id}`, 'good'); setDeleting(null); await refresh(); }
    catch (e) { toast(errorMessage(e), 'bad'); }
  };

  return (
    <>
      <PageHeader title="Parcel management" subtitle="Create, edit, search and import delivery parcels. Weights and values are whole numbers because the knapsack DP is indexed by integer capacity."
        actions={<>
          <Button icon="database" onClick={() => setDataset(true)}>Datasets</Button>
          <Button icon="upload" onClick={() => setImporting(true)}>Import</Button>
          <a className="btn btn-secondary" href="/api/export/parcels.csv"><Icon name="download" />CSV</a>
          <a className="btn btn-secondary" href="/api/export/parcels.json"><Icon name="download" />JSON</a>
          <Button variant="primary" icon="plus" onClick={() => setEditing({ parcel: null })}>Add parcel</Button>
        </>} />
      <Card pad={false}>
        <div className="flex flex-wrap items-center gap-3 border-b border-line p-4">
          <div className="relative min-w-[220px] flex-1"><Icon name="search" className="absolute left-3 top-2.5 text-fg3" />
            <input className="input !pl-9" placeholder="Search by parcel ID or destination" value={q} onChange={(e) => reset(() => setQ(e.target.value))} aria-label="Search parcels" /></div>
          <select className="input !w-40" value={prio} onChange={(e) => reset(() => setPrio(e.target.value))} aria-label="Filter by priority">
            <option value="all">All priorities</option>{[5, 4, 3, 2, 1].map((p) => <option key={p} value={p}>P{p} · {PRIORITY_LABEL[p]}</option>)}</select>
          <select className="input !w-48" value={dest} onChange={(e) => reset(() => setDest(e.target.value))} aria-label="Filter by destination">
            <option value="all">All destinations</option>{locations.map((l) => <option key={l}>{l}</option>)}</select>
          <select className="input !w-36" value={status} onChange={(e) => reset(() => setStatus(e.target.value))} aria-label="Filter by status">
            <option value="all">Any status</option><option>pending</option><option>delivered</option><option>cancelled</option></select>
          <select className="input !w-44" value={sort} onChange={(e) => setSort(e.target.value as SortKey)} aria-label="Sort parcels">
            <option value="deadline">Deadline: earliest</option><option value="-deadline">Deadline: latest</option><option value="priority">Priority: highest</option>
            <option value="weight">Weight: heaviest</option><option value="value">Value: highest</option><option value="id">Parcel ID</option></select>
        </div>
        {shown.length === 0 ? <Empty icon="package" title={parcels.length ? 'No parcels match the filters' : 'No parcels yet'}>{parcels.length ? 'Clear a filter or search term.' : 'Add a parcel, import a file or generate a dataset.'}</Empty> : (
          <div className="overflow-x-auto"><table className="tbl">
            <thead><tr><th>Parcel ID</th><th>Destination</th><th className="num">Weight (kg)</th><th>Priority</th><th>Deadline</th><th className="num">Value</th><th className="num">Weighted</th><th>Status</th><th /></tr></thead>
            <tbody>{shown.map((p) => (
              <tr key={p.id}>
                <td className="font-medium text-fg">{p.id}</td><td>{p.destination}</td><td className="num">{p.weight}</td>
                <td><PriorityBadge p={p.priority} /></td><td>{fmtDate(p.deadline)}</td><td className="num">{fmt(p.value, 0)}</td>
                <td className="num text-fg3">{fmt(p.value * p.priority, 0)}</td><td><StatusBadge status={p.status} /></td>
                <td className="text-right"><div className="inline-flex gap-1">
                  <button className="btn btn-ghost !p-1.5" aria-label={`Edit ${p.id}`} onClick={() => setEditing({ parcel: p })}><Icon name="edit" /></button>
                  <button className="btn btn-ghost !p-1.5 hover:!text-bad" aria-label={`Delete ${p.id}`} onClick={() => setDeleting(p)}><Icon name="trash" /></button></div></td>
              </tr>))}</tbody></table></div>
        )}
        <div className="flex items-center justify-between border-t border-line px-4 py-3 text-xs text-fg3">
          <span>{rows.length} of {parcels.length} parcels</span>
          <div className="flex items-center gap-2"><Button onClick={() => setPage(Math.max(0, page - 1))} disabled={page === 0} icon="prev" aria-label="Previous page" />
            <span className="tabular-nums">Page {Math.min(page, pages - 1) + 1} / {pages}</span>
            <Button onClick={() => setPage(Math.min(pages - 1, page + 1))} disabled={page >= pages - 1} icon="next" aria-label="Next page" /></div>
        </div>
      </Card>

      {editing && <ParcelForm parcel={editing.parcel} locations={locations} onClose={() => setEditing(null)} onSaved={async () => { setEditing(null); await refresh(); }} />}
      {deleting && <Modal title="Delete parcel" onClose={() => setDeleting(null)} width="max-w-md">
        <p className="text-sm text-fg2">Delete <b className="text-fg">{deleting.id}</b> (to {deleting.destination}, {deleting.weight} kg)? This cannot be undone.</p>
        <div className="mt-5 flex justify-end gap-2"><Button onClick={() => setDeleting(null)}>Cancel</Button><Button variant="danger" icon="trash" onClick={() => void remove()}>Delete</Button></div></Modal>}
      {importing && <ImportModal onClose={() => setImporting(false)} onDone={refresh} />}
      {dataset && <DatasetModal onClose={() => setDataset(false)} onDone={refresh} />}
    </>
  );
}

function ParcelForm({ parcel, locations, onClose, onSaved }: { parcel: Parcel | null; locations: string[]; onClose: () => void; onSaved: () => Promise<void> }) {
  const { toast } = useApp();
  const [d, setD] = useState<Draft>(parcel ? { id: parcel.id, destination: parcel.destination, weight: String(parcel.weight), priority: String(parcel.priority),
    deadline: parcel.deadline, value: String(parcel.value), status: parcel.status } : blank(locations.find((l) => l !== 'Depot') ?? locations[0] ?? ''));
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [busy, setBusy] = useState(false);
  const set = (k: keyof Draft) => (e: { target: { value: string } }) => setD({ ...d, [k]: e.target.value });

  const submit = async (e: FormEvent) => {
    e.preventDefault();
    const local = validate(d);
    setErrors(local);
    if (Object.keys(local).length) return;
    setBusy(true);
    const body = { ...d, weight: Number(d.weight), priority: Number(d.priority), value: Number(d.value) };
    try {
      if (parcel) await api.put(`/api/parcels/${encodeURIComponent(parcel.id)}`, body); else await api.post('/api/parcels', body);
      toast(parcel ? `Updated ${parcel.id}` : 'Parcel added', 'good');
      await onSaved();
    } catch (err) {
      const fe = fieldErrors(err);
      if (Object.keys(fe).length) setErrors(fe); else toast(errorMessage(err), 'bad');
    } finally { setBusy(false); }
  };

  return (
    <Modal title={parcel ? `Edit ${parcel.id}` : 'Add parcel'} onClose={onClose}>
      <form onSubmit={submit} noValidate className="grid grid-cols-2 gap-4">
        <Field label="Parcel ID" error={errors.id} hint={parcel ? 'IDs cannot be changed' : 'Leave blank to generate one'}>{(id, bad) =>
          <input id={id} className="input" value={d.id} onChange={set('id')} disabled={!!parcel} placeholder="PKG-0025" aria-invalid={bad} />}</Field>
        <Field label="Destination" error={errors.destination}>{(id, bad) =>
          <select id={id} className="input" value={d.destination} onChange={set('destination')} aria-invalid={bad}>{locations.map((l) => <option key={l}>{l}</option>)}</select>}</Field>
        <Field label="Weight (kg)" error={errors.weight} hint="Whole kilograms">{(id, bad) =>
          <input id={id} className="input" inputMode="numeric" value={d.weight} onChange={set('weight')} aria-invalid={bad} />}</Field>
        <Field label="Priority" error={errors.priority}>{(id, bad) =>
          <select id={id} className="input" value={d.priority} onChange={set('priority')} aria-invalid={bad}>{[5, 4, 3, 2, 1].map((p) => <option key={p} value={p}>{p} · {PRIORITY_LABEL[p]}</option>)}</select>}</Field>
        <Field label="Delivery deadline" error={errors.deadline}>{(id, bad) =>
          <input id={id} type="datetime-local" className="input" value={d.deadline} onChange={set('deadline')} aria-invalid={bad} />}</Field>
        <Field label="Delivery value" error={errors.value} hint="Whole currency units">{(id, bad) =>
          <input id={id} className="input" inputMode="numeric" value={d.value} onChange={set('value')} aria-invalid={bad} />}</Field>
        <Field label="Status" error={errors.status}>{(id) => <select id={id} className="input" value={d.status} onChange={set('status')}><option>pending</option><option>delivered</option><option>cancelled</option></select>}</Field>
        <div className="flex items-end text-xs text-fg3">Priority-weighted value = value × priority = {fmt((Number(d.value) || 0) * Number(d.priority), 0)}</div>
        <div className="col-span-2 mt-1 flex justify-end gap-2"><Button type="button" onClick={onClose}>Cancel</Button><Button type="submit" variant="primary" busy={busy} icon="check">{parcel ? 'Save changes' : 'Add parcel'}</Button></div>
      </form>
    </Modal>
  );
}

function ImportModal({ onClose, onDone }: { onClose: () => void; onDone: () => Promise<void> }) {
  const { toast } = useApp();
  const [mode, setMode] = useState<'append' | 'replace'>('append');
  const [fileName, setFileName] = useState('');
  const [content, setContent] = useState('');
  const [format, setFormat] = useState<'json' | 'csv'>('csv');
  const [out, setOut] = useState<ImportResponse | null>(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const input = useRef<HTMLInputElement>(null);

  const pick = async (f: File | undefined) => {
    if (!f) return;
    setFileName(f.name); setContent(await f.text()); setOut(null); setError('');
    setFormat(f.name.toLowerCase().endsWith('.json') ? 'json' : 'csv');
  };
  const run = async () => {
    setBusy(true); setError('');
    try { const r = await api.post<ImportResponse>('/api/parcels/import', { format, content, mode }); setOut(r); await onDone();
      toast(`Imported ${r.added} parcel(s)${r.errors.length ? `, ${r.errors.length} row error(s)` : ''}`, r.errors.length ? 'info' : 'good'); }
    catch (e) { setError(errorMessage(e)); } finally { setBusy(false); }
  };
  return (
    <Modal title="Import parcels" onClose={onClose} width="max-w-2xl">
      <div className="space-y-4">
        <p className="text-[13px] text-fg2">Upload a <b>.csv</b> (columns: id, destination, weight, priority, deadline, value, status) or <b>.json</b> file. Rows with errors are reported and skipped; valid rows are still imported.</p>
        <div className="flex flex-wrap items-center gap-3">
          <input ref={input} type="file" accept=".csv,.json,application/json,text/csv" className="hidden" onChange={(e) => void pick(e.target.files?.[0])} />
          <Button icon="upload" onClick={() => input.current?.click()}>Choose file</Button><span className="text-sm text-fg3">{fileName || 'No file chosen'}</span>
          <select className="input !w-40" value={mode} onChange={(e) => setMode(e.target.value as 'append' | 'replace')} aria-label="Import mode"><option value="append">Add to existing</option><option value="replace">Replace all parcels</option></select>
        </div>
        {error && <Notice tone="bad" title="Import failed">{error}</Notice>}
        {out && <div><Notice tone={out.errors.length ? 'warn' : 'good'} title={`${out.added} imported, ${out.errors.length} rejected. ${out.total} parcels in total.`} />
          {out.errors.length > 0 && <div className="mt-3 max-h-48 overflow-auto rounded-lg border border-line"><table className="tbl"><thead><tr><th>Row</th><th>Field</th><th>Problem</th></tr></thead>
            <tbody>{out.errors.map((x, i) => <tr key={i}><td>{x.row}</td><td>{x.field}</td><td className="!whitespace-normal">{x.message}</td></tr>)}</tbody></table></div>}</div>}
        <div className="flex justify-end gap-2"><Button onClick={onClose}>Close</Button><Button variant="primary" icon="upload" busy={busy} disabled={!content} onClick={() => void run()}>Import</Button></div>
      </div>
    </Modal>
  );
}

function DatasetModal({ onClose, onDone }: { onClose: () => void; onDone: () => Promise<void> }) {
  const { toast } = useApp();
  const [size, setSize] = useState('50');
  const [seed, setSeed] = useState('2026');
  const [busy, setBusy] = useState(false);
  const go = async (fn: () => Promise<unknown>, msg: string) => {
    setBusy(true);
    try { await fn(); await onDone(); toast(msg, 'good'); onClose(); } catch (e) { toast(errorMessage(e), 'bad'); } finally { setBusy(false); }
  };
  return (
    <Modal title="Datasets" onClose={onClose} width="max-w-md">
      <div className="space-y-4 text-[13px] text-fg2">
        <p>Generate a reproducible parcel dataset for the current road network (same seed = same parcels). <b className="text-fg">This replaces all current parcels.</b></p>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Number of parcels">{(id) => <select id={id} className="input" value={size} onChange={(e) => setSize(e.target.value)}>{[10, 24, 50, 100, 500, 1000, 5000].map((n) => <option key={n}>{n}</option>)}</select>}</Field>
          <Field label="Random seed">{(id) => <input id={id} className="input" inputMode="numeric" value={seed} onChange={(e) => setSeed(e.target.value)} />}</Field>
        </div>
        <div className="flex flex-wrap justify-between gap-2">
          <Button busy={busy} icon="refresh" onClick={() => void go(() => api.post('/api/reset'), 'Sample data restored')}>Restore sample data</Button>
          <Button variant="primary" busy={busy} icon="database" onClick={() => void go(() => api.post('/api/datasets/load', { size: Number(size), seed: Number(seed) || 0 }), `Generated ${size} parcels`)}>Generate</Button>
        </div>
        <p className="text-xs text-fg3">With thousands of parcels the vehicle capacity bounds the DP size; capacity above roughly 12,000 kg for 5,000 parcels is refused with an explanation (see Benchmark lab).</p>
      </div>
    </Modal>
  );
}
