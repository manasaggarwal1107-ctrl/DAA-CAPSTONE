// Dependency-free SVG charts (bar + line with optional log axes) sized to their container.
import { useEffect, useRef, useState, type RefObject } from 'react';

function useWidth(): [RefObject<HTMLDivElement | null>, number] {
  const ref = useRef<HTMLDivElement | null>(null);
  const [w, setW] = useState(480);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const ro = new ResizeObserver(() => setW(Math.max(220, Math.floor(el.clientWidth))));
    ro.observe(el);
    setW(Math.max(220, Math.floor(el.clientWidth)));
    return () => ro.disconnect();
  }, []);
  return [ref, w];
}

const AXIS = '#7f91b3';
const GRID = 'rgba(127,145,179,0.16)';

const niceMax = (v: number): number => {
  if (v <= 0) return 1;
  const exp = Math.pow(10, Math.floor(Math.log10(v)));
  const f = v / exp;
  return (f <= 1 ? 1 : f <= 2 ? 2 : f <= 5 ? 5 : 10) * exp;
};

export const compact = (v: number): string =>
  v >= 1e6 ? `${+(v / 1e6).toFixed(1)}M` : v >= 1e3 ? `${+(v / 1e3).toFixed(1)}k` : `${+v.toFixed(v < 10 ? 2 : 0)}`;

export interface BarDatum { label: string; value: number; color?: string; note?: string }

export function BarChart({ data, height = 200, color = 'var(--color-s1)', unit = '', formatValue = compact }:
  { data: BarDatum[]; height?: number; color?: string; unit?: string; formatValue?: (v: number) => string }) {
  const [ref, width] = useWidth();
  const [hover, setHover] = useState<number | null>(null);
  const m = { t: 14, r: 8, b: 30, l: 38 };
  const iw = width - m.l - m.r, ih = height - m.t - m.b;
  const max = niceMax(Math.max(0, ...data.map((d) => d.value)));
  const slot = iw / Math.max(1, data.length);
  const bw = Math.min(46, slot * 0.62);
  const ticks = [0, 0.25, 0.5, 0.75, 1].map((f) => f * max);
  const skip = Math.ceil(data.length / Math.max(1, Math.floor(iw / 54)));
  return (
    <div ref={ref} className="relative w-full">
      <svg width={width} height={height} role="img" aria-label="Bar chart">
        {ticks.map((t) => {
          const y = m.t + ih - (t / max) * ih;
          return <g key={t}><line x1={m.l} x2={width - m.r} y1={y} y2={y} stroke={GRID} /><text x={m.l - 6} y={y + 3.5} textAnchor="end" fontSize="10.5" fill={AXIS}>{compact(t)}</text></g>;
        })}
        {data.map((d, i) => {
          const h = (d.value / max) * ih;
          const x = m.l + slot * i + (slot - bw) / 2;
          return (
            <g key={d.label + i} onMouseEnter={() => setHover(i)} onMouseLeave={() => setHover(null)}>
              <rect x={m.l + slot * i} y={m.t} width={slot} height={ih} fill="transparent" />
              <rect x={x} y={m.t + ih - h} width={bw} height={Math.max(h, d.value > 0 ? 1.5 : 0)} rx={3}
                fill={d.color ?? color} opacity={hover === null || hover === i ? 1 : 0.55} />
              {i % skip === 0 && <text x={x + bw / 2} y={height - 10} textAnchor="middle" fontSize="10.5" fill={AXIS}>{d.label}</text>}
            </g>
          );
        })}
      </svg>
      {hover !== null && data[hover] && (
        <div className="pointer-events-none absolute z-10 -translate-x-1/2 rounded-md border border-line bg-ink-900 px-2 py-1 text-xs shadow-lg"
          style={{ left: m.l + slot * hover + slot / 2, top: 0 }}>
          <span className="text-fg3">{data[hover].label}: </span><span className="font-semibold tabular-nums">{formatValue(data[hover].value)}{unit}</span>
          {data[hover].note && <span className="text-fg3"> · {data[hover].note}</span>}
        </div>
      )}
    </div>
  );
}

export interface LineSeries { name: string; color: string; points: { x: number; y: number }[]; dashed?: boolean }

export function LineChart({ series, height = 280, xLog = true, yLog = true, xLabel, yLabel, formatY = compact }:
  { series: LineSeries[]; height?: number; xLog?: boolean; yLog?: boolean; xLabel?: string; yLabel?: string; formatY?: (v: number) => string }) {
  const [ref, width] = useWidth();
  const [hover, setHover] = useState<number | null>(null);
  const m = { t: 12, r: 14, b: 40, l: 52 };
  const iw = width - m.l - m.r, ih = height - m.t - m.b;
  const xs = [...new Set(series.flatMap((s) => s.points.map((p) => p.x)))].sort((a, b) => a - b);
  const ysAll = series.flatMap((s) => s.points.map((p) => p.y)).filter((y) => y > 0);
  if (xs.length === 0 || ysAll.length === 0) return <div ref={ref} className="py-8 text-center text-sm text-fg3">No data</div>;
  const tx = (x: number) => (xLog ? Math.log10(Math.max(x, 1e-9)) : x);
  const ty = (y: number) => (yLog ? Math.log10(Math.max(y, 1e-9)) : y);
  const x0 = tx(xs[0]), x1 = tx(xs[xs.length - 1]);
  const y0 = Math.min(...ysAll), y1 = Math.max(...ysAll);
  let lo: number, hi: number;
  if (yLog) { lo = Math.floor(ty(y0)); hi = Math.ceil(ty(y1)); if (hi === lo) hi = lo + 1; } else { lo = 0; hi = niceMax(y1); }
  const px = (x: number) => m.l + (x1 === x0 ? iw / 2 : ((tx(x) - x0) / (x1 - x0)) * iw);
  const py = (y: number) => m.t + ih - ((ty(Math.max(y, yLog ? Math.pow(10, lo) : 0)) - lo) / (hi - lo)) * ih;
  const yTicks: number[] = yLog ? Array.from({ length: hi - lo + 1 }, (_, i) => Math.pow(10, lo + i)) : [0, 0.25, 0.5, 0.75, 1].map((f) => f * hi);
  const near = (clientX: number, rect: DOMRect) => {
    const mx = clientX - rect.left;
    let best = 0, bd = Infinity;
    xs.forEach((x, i) => { const d = Math.abs(px(x) - mx); if (d < bd) { bd = d; best = i; } });
    return best;
  };
  return (
    <div ref={ref} className="relative w-full">
      <svg width={width} height={height} role="img" aria-label="Line chart"
        onMouseMove={(e) => setHover(near(e.clientX, e.currentTarget.getBoundingClientRect()))} onMouseLeave={() => setHover(null)}>
        {yTicks.map((t) => <g key={t}><line x1={m.l} x2={width - m.r} y1={py(t)} y2={py(t)} stroke={GRID} /><text x={m.l - 7} y={py(t) + 3.5} textAnchor="end" fontSize="10.5" fill={AXIS}>{formatY(t)}</text></g>)}
        {xs.map((x) => <g key={x}><line x1={px(x)} x2={px(x)} y1={m.t} y2={m.t + ih} stroke={GRID} strokeDasharray="2 4" /><text x={px(x)} y={height - 20} textAnchor="middle" fontSize="10.5" fill={AXIS}>{x.toLocaleString()}</text></g>)}
        {xLabel && <text x={m.l + iw / 2} y={height - 3} textAnchor="middle" fontSize="11" fill={AXIS}>{xLabel}</text>}
        {yLabel && <text transform={`translate(12 ${m.t + ih / 2}) rotate(-90)`} textAnchor="middle" fontSize="11" fill={AXIS}>{yLabel}</text>}
        {hover !== null && <line x1={px(xs[hover])} x2={px(xs[hover])} y1={m.t} y2={m.t + ih} stroke={AXIS} strokeOpacity="0.5" />}
        {series.map((s) => (
          <g key={s.name}>
            <polyline fill="none" stroke={s.color} strokeWidth={2} strokeDasharray={s.dashed ? '5 4' : undefined} strokeLinejoin="round"
              points={s.points.map((p) => `${px(p.x)},${py(p.y)}`).join(' ')} opacity={s.dashed ? 0.8 : 1} />
            {!s.dashed && s.points.map((p) => <circle key={p.x} cx={px(p.x)} cy={py(p.y)} r={hover !== null && xs[hover] === p.x ? 4.5 : 3} fill={s.color} />)}
          </g>
        ))}
      </svg>
      {hover !== null && (
        <div className="pointer-events-none absolute z-10 rounded-md border border-line bg-ink-900/95 px-2.5 py-1.5 text-xs shadow-lg"
          style={{ left: Math.min(px(xs[hover]) + 10, width - 190), top: 4 }}>
          <div className="mb-1 font-semibold text-fg">n = {xs[hover].toLocaleString()}</div>
          {series.map((s) => {
            const p = s.points.find((q) => q.x === xs[hover]);
            return p ? <div key={s.name} className="flex items-center gap-2 text-fg2"><span className="h-0.5 w-3" style={{ background: s.color }} />{s.name}<span className="ml-auto pl-3 font-medium tabular-nums text-fg">{formatY(p.y)}</span></div> : null;
          })}
        </div>
      )}
      <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 pl-12 text-xs text-fg2">
        {series.map((s) => <span key={s.name} className="inline-flex items-center gap-1.5"><span className="inline-block h-0 w-4 border-t-2" style={{ borderColor: s.color, borderStyle: s.dashed ? 'dashed' : 'solid' }} />{s.name}</span>)}
      </div>
    </div>
  );
}
