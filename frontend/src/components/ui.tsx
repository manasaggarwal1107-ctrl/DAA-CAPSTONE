// Reusable interface primitives: buttons, cards, badges, form fields, modal, tabs, notices.
import { useEffect, useId, type ButtonHTMLAttributes, type ReactNode } from 'react';
import { Icon, type IconName } from '../icons';

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger';

export function Button({ variant = 'secondary', icon, busy, children, className = '', ...rest }:
  ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant; icon?: IconName; busy?: boolean }) {
  return (
    <button {...rest} disabled={rest.disabled || busy} className={`btn btn-${variant} ${className}`}>
      {busy ? <Icon name="refresh" className="spin" /> : icon ? <Icon name={icon} /> : null}
      {children}
    </button>
  );
}

export function Card({ title, subtitle, actions, children, className = '', pad = true }:
  { title?: ReactNode; subtitle?: ReactNode; actions?: ReactNode; children: ReactNode; className?: string; pad?: boolean }) {
  return (
    <section className={`card ${className}`}>
      {(title || actions) && (
        <header className="flex items-start justify-between gap-3 px-5 pt-4">
          <div className="min-w-0">
            <h3 className="text-[13.5px] font-semibold text-fg">{title}</h3>
            {subtitle && <p className="mt-0.5 text-xs text-fg3">{subtitle}</p>}
          </div>
          {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
        </header>
      )}
      <div className={pad ? 'px-5 pb-5 pt-3' : ''}>{children}</div>
    </section>
  );
}

export function PageHeader({ title, subtitle, actions }: { title: string; subtitle?: ReactNode; actions?: ReactNode }) {
  return (
    <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="text-[22px] font-semibold tracking-tight text-fg">{title}</h1>
        {subtitle && <p className="mt-1 max-w-3xl text-[13px] text-fg2">{subtitle}</p>}
      </div>
      {actions && <div className="flex flex-wrap items-center gap-2">{actions}</div>}
    </div>
  );
}

type Tone = 'neutral' | 'good' | 'warn' | 'bad' | 'info';
export function Badge({ tone = 'neutral', children }: { tone?: Tone; children: ReactNode }) {
  return <span className={`badge badge-${tone}`}>{children}</span>;
}

export function Kpi({ label, value, sub, icon, tone }: { label: string; value: ReactNode; sub?: ReactNode; icon: IconName; tone?: Tone }) {
  return (
    <div className="card p-4">
      <div className="flex items-center justify-between text-fg3">
        <span className="text-[11.5px] font-medium uppercase tracking-wider">{label}</span>
        <span className={`kpi-icon kpi-${tone ?? 'info'}`}><Icon name={icon} size={15} /></span>
      </div>
      <div className="mt-2 text-[26px] font-semibold leading-none tracking-tight text-fg tabular-nums">{value}</div>
      {sub && <div className="mt-2 text-xs text-fg3">{sub}</div>}
    </div>
  );
}

export function Meter({ percent, tone = 'accent' }: { percent: number; tone?: 'accent' | 'warn' }) {
  const p = Math.max(0, Math.min(100, percent));
  return (
    <div className="h-1.5 w-full overflow-hidden rounded-full bg-ink-700" role="progressbar" aria-valuenow={Math.round(p)} aria-valuemin={0} aria-valuemax={100}>
      <div className={`h-full rounded-full transition-all duration-500 ${tone === 'warn' ? 'bg-warn' : 'bg-accent'}`} style={{ width: `${p}%` }} />
    </div>
  );
}

export function Field({ label, error, hint, children }: { label: string; error?: string; hint?: string; children: (id: string, invalid: boolean) => ReactNode }) {
  const id = useId();
  return (
    <div>
      <label htmlFor={id} className="mb-1 block text-xs font-medium text-fg2">{label}</label>
      {children(id, !!error)}
      {error ? <p className="mt-1 text-xs text-bad" role="alert">{error}</p> : hint ? <p className="mt-1 text-xs text-fg3">{hint}</p> : null}
    </div>
  );
}

export function Notice({ tone = 'info', title, children }: { tone?: 'info' | 'warn' | 'bad' | 'good'; title?: string; children?: ReactNode }) {
  const icon: IconName = tone === 'good' ? 'check' : tone === 'info' ? 'info' : 'alert';
  return (
    <div className={`notice notice-${tone}`} role={tone === 'bad' ? 'alert' : 'status'}>
      <Icon name={icon} size={16} className="mt-0.5" />
      <div className="min-w-0 text-[13px]">{title && <div className="font-semibold">{title}</div>}{children && <div className="text-fg2">{children}</div>}</div>
    </div>
  );
}

export function Modal({ title, onClose, children, width = 'max-w-lg' }: { title: string; onClose: () => void; children: ReactNode; width?: string }) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose(); };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [onClose]);
  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/60 p-4 pt-[8vh] backdrop-blur-sm" onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div className={`card rise w-full ${width} p-0`} role="dialog" aria-modal="true" aria-label={title}>
        <header className="flex items-center justify-between border-b border-line px-5 py-3.5">
          <h2 className="text-[15px] font-semibold">{title}</h2>
          <button className="btn btn-ghost !p-1.5" onClick={onClose} aria-label="Close"><Icon name="x" /></button>
        </header>
        <div className="p-5">{children}</div>
      </div>
    </div>
  );
}

export function Tabs<T extends string>({ tabs, value, onChange }: { tabs: { id: T; label: string }[]; value: T; onChange: (v: T) => void }) {
  return (
    <div className="inline-flex gap-1 rounded-xl border border-line bg-ink-900/70 p-1" role="tablist">
      {tabs.map((t) => (
        <button key={t.id} role="tab" aria-selected={value === t.id} onClick={() => onChange(t.id)}
          className={`rounded-lg px-3 py-1.5 text-[13px] font-medium transition-colors ${value === t.id ? 'bg-ink-600 text-fg shadow' : 'text-fg3 hover:text-fg'}`}>
          {t.label}
        </button>
      ))}
    </div>
  );
}

export function Empty({ icon, title, children }: { icon: IconName; title: string; children?: ReactNode }) {
  return (
    <div className="flex flex-col items-center justify-center gap-2 px-4 py-10 text-center">
      <span className="grid h-10 w-10 place-items-center rounded-full bg-ink-700 text-fg3"><Icon name={icon} size={18} /></span>
      <div className="text-sm font-medium text-fg">{title}</div>
      {children && <div className="max-w-sm text-xs text-fg3">{children}</div>}
    </div>
  );
}

export function Spinner({ label = 'Loading' }: { label?: string }) {
  return <div className="flex items-center gap-2 p-6 text-sm text-fg3"><Icon name="refresh" className="spin" />{label}</div>;
}

export const Stat = ({ label, value }: { label: string; value: ReactNode }) => (
  <div><div className="text-[11px] uppercase tracking-wider text-fg3">{label}</div><div className="mt-0.5 text-[15px] font-semibold tabular-nums">{value}</div></div>
);

export function PriorityBadge({ p }: { p: number }) {
  const tone: Tone = p >= 5 ? 'bad' : p === 4 ? 'warn' : p === 3 ? 'info' : 'neutral';
  return <Badge tone={tone}>P{p}</Badge>;
}

export function StatusBadge({ status }: { status: string }) {
  const tone: Tone = status === 'pending' ? 'info' : status === 'delivered' ? 'good' : 'neutral';
  return <Badge tone={tone}>{status}</Badge>;
}
