import { useEffect, useState, type ReactElement } from 'react';
import { Icon, type IconName } from './icons';
import { useApp } from './store';
import { Badge, Button, Notice, Spinner } from './components/ui';
import { Dashboard } from './pages/Dashboard';
import { Parcels } from './pages/Parcels';
import { Sorting } from './pages/Sorting';
import { Knapsack } from './pages/Knapsack';
import { Network } from './pages/Network';
import { RoutePage } from './pages/Route';
import { Benchmarks } from './pages/Benchmarks';
import { Learn } from './pages/Learn';
import { Reports } from './pages/Reports';

const NAV: { id: string; label: string; icon: IconName; group: string; el: () => ReactElement }[] = [
  { id: 'dashboard', label: 'Dashboard', icon: 'dashboard', group: 'Operations', el: Dashboard },
  { id: 'parcels', label: 'Parcels', icon: 'package', group: 'Operations', el: Parcels },
  { id: 'sorting', label: 'Prioritisation', icon: 'sort', group: 'Optimisation', el: Sorting },
  { id: 'knapsack', label: 'Load planning', icon: 'scale', group: 'Optimisation', el: Knapsack },
  { id: 'network', label: 'Road network', icon: 'network', group: 'Optimisation', el: Network },
  { id: 'route', label: 'Route planner', icon: 'route', group: 'Optimisation', el: RoutePage },
  { id: 'benchmarks', label: 'Benchmark lab', icon: 'gauge', group: 'Analysis', el: Benchmarks },
  { id: 'learn', label: 'Learning centre', icon: 'book', group: 'Analysis', el: Learn },
  { id: 'reports', label: 'Reports & export', icon: 'file', group: 'Analysis', el: Reports },
];

const current = () => (window.location.hash.replace(/^#\/?/, '') || 'dashboard');

export function App() {
  const { state, result, loading, loadError, refresh, optimise, running } = useApp();
  const [route, setRoute] = useState(current());
  const [open, setOpen] = useState(false);
  useEffect(() => {
    const on = () => { setRoute(current()); setOpen(false); window.scrollTo(0, 0); };
    window.addEventListener('hashchange', on);
    return () => window.removeEventListener('hashchange', on);
  }, []);
  const page = NAV.find((n) => n.id === route) ?? NAV[0];
  const Page = page.el;
  const groups = [...new Set(NAV.map((n) => n.group))];

  return (
    <div className="flex min-h-full">
      <aside className={`fixed inset-y-0 left-0 z-40 w-60 shrink-0 border-r border-line bg-ink-900/95 backdrop-blur transition-transform lg:static lg:translate-x-0 ${open ? 'translate-x-0' : '-translate-x-full'}`}>
        <div className="flex h-16 items-center gap-2.5 px-5">
          <span className="grid h-8 w-8 place-items-center rounded-lg bg-gradient-to-br from-accent to-electric text-ink-950"><Icon name="truck" size={17} /></span>
          <div className="leading-tight"><div className="text-[14px] font-semibold tracking-tight">Mini-Courier</div><div className="text-[11px] text-fg3">Planner · DAA capstone</div></div>
        </div>
        <nav className="mt-2 px-3 pb-6">
          {groups.map((g) => (
            <div key={g} className="mb-4">
              <div className="px-2 pb-1.5 text-[10.5px] font-semibold uppercase tracking-[0.12em] text-fg3">{g}</div>
              {NAV.filter((n) => n.group === g).map((n) => (
                <a key={n.id} href={`#/${n.id}`} aria-current={page.id === n.id ? 'page' : undefined}
                  className={`nav-link ${page.id === n.id ? 'nav-active' : ''}`}><Icon name={n.icon} size={16} />{n.label}</a>
              ))}
            </div>
          ))}
        </nav>
      </aside>
      {open && <div className="fixed inset-0 z-30 bg-black/50 lg:hidden" onClick={() => setOpen(false)} />}

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-20 flex h-16 items-center gap-3 border-b border-line bg-ink-950/80 px-4 backdrop-blur lg:px-8">
          <button className="btn btn-ghost !p-2 lg:hidden" onClick={() => setOpen(true)} aria-label="Open navigation"><Icon name="menu" /></button>
          <div className="hidden items-center gap-2 text-[13px] text-fg3 sm:flex"><Icon name={page.icon} size={15} />{page.group}<span>/</span><span className="text-fg">{page.label}</span></div>
          <div className="ml-auto flex items-center gap-3">
            {result && <span className="hidden items-center gap-2 text-xs text-fg3 md:flex"><Icon name="clock" size={13} />Last run {result.ran_at}
              {result.stale ? <Badge tone="warn">data changed</Badge> : <Badge tone="good">up to date</Badge>}</span>}
            <Button variant="primary" icon="zap" busy={running} onClick={() => void optimise()}>Run optimisation</Button>
          </div>
        </header>
        <main className="mx-auto w-full max-w-[1400px] flex-1 px-4 py-6 lg:px-8">
          {loading ? <Spinner label="Loading planner data" /> : loadError || !state ? (
            <div className="max-w-xl"><Notice tone="bad" title="Cannot load data">{loadError ?? 'Unknown error'}</Notice><div className="mt-3"><Button icon="refresh" onClick={() => void refresh()}>Try again</Button></div></div>
          ) : <div key={page.id} className="rise"><Page /></div>}
        </main>
      </div>
    </div>
  );
}
