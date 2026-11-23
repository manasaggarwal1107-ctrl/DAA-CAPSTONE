// Interactive SVG road-network canvas: roads, locations, highlighted paths and numbered route stops.
import { useState } from 'react';
import type { Location } from '../types';

export interface PathHighlight { path: string[]; color: string; width?: number }
interface RoadLike { a: string; b: string; weight: number; bidirectional?: boolean }

interface Props {
  locations: Location[];
  roads: RoadLike[];
  paths?: PathHighlight[];
  depot?: string;
  stops?: string[];            // route order; stops are numbered 1..n
  emphasised?: string[];       // locations drawn highlighted (e.g. delivery destinations)
  dimOthers?: boolean;
  selected?: string[];
  showWeights?: boolean;
  onNodeClick?: (name: string) => void;
  onCanvasClick?: (x: number, y: number) => void;
  settled?: string[];          // Dijkstra demo: settled nodes
  labels?: Record<string, string>;   // extra text under a node (e.g. distance labels)
}

const SX = 1.4;                // horizontal stretch so a 0..100 plane fills a wide card
const W = 100 * SX + 20, H = 120;

export function GraphCanvas({ locations, roads, paths = [], depot, stops = [], emphasised = [], dimOthers = false, selected = [],
  showWeights = true, onNodeClick, onCanvasClick, settled = [], labels = {} }: Props) {
  const [hover, setHover] = useState<string | null>(null);
  const pos = new Map(locations.map((l) => [l.name, { x: l.x * SX + 10, y: l.y + 10 }]));
  const stopIndex = new Map(stops.map((s, i) => [s, i + 1]));
  const emph = new Set([...emphasised, ...stops]);
  const sel = new Set(selected);
  const done = new Set(settled);
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className={`w-full rounded-xl border border-line bg-ink-900/60 ${onCanvasClick ? 'cursor-crosshair' : ''}`}
      style={{ aspectRatio: `${W} / ${H}` }} role="img" aria-label="Road network graph"
      onClick={(e) => {
        if (!onCanvasClick) return;
        const r = e.currentTarget.getBoundingClientRect();
        const x = ((e.clientX - r.left) / r.width) * W, y = ((e.clientY - r.top) / r.height) * H;
        onCanvasClick(Math.round(Math.min(100, Math.max(0, (x - 10) / SX)) * 10) / 10, Math.round(Math.min(100, Math.max(0, y - 10)) * 10) / 10);
      }}>
      <defs>
        <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="4" markerHeight="4" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#4b6190" /></marker>
        <pattern id="dots" width="10" height="10" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r="0.35" fill="rgba(127,145,179,0.18)" /></pattern>
      </defs>
      <rect width={W} height={H} fill="url(#dots)" />
      {roads.map((r) => {
        const a = pos.get(r.a), b = pos.get(r.b);
        if (!a || !b) return null;
        const mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2;
        return (
          <g key={`${r.a}|${r.b}`}>
            <line x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke="#2b3f66" strokeWidth={0.7} markerEnd={r.bidirectional === false ? 'url(#arrow)' : undefined} />
            {showWeights && <text x={mx} y={my - 0.8} textAnchor="middle" fontSize={2.3} fill="#6a7fa6" stroke="#0a1224" strokeWidth={0.8} paintOrder="stroke">{r.weight}</text>}
          </g>
        );
      })}
      {paths.map((p, pi) => p.path.slice(1).map((n, i) => {
        const a = pos.get(p.path[i]), b = pos.get(n);
        return a && b ? <line key={`${pi}-${i}`} x1={a.x} y1={a.y} x2={b.x} y2={b.y} stroke={p.color} strokeWidth={p.width ?? 1.5} strokeLinecap="round" opacity={0.95} /> : null;
      }))}
      {locations.map((l) => {
        const p = pos.get(l.name)!;
        const isDepot = l.name === depot, idx = stopIndex.get(l.name);
        const lit = isDepot || emph.has(l.name) || sel.has(l.name) || done.has(l.name);
        const faded = dimOthers && !lit;
        const r = isDepot ? 3.4 : idx ? 3 : 2.3;
        const fill = isDepot ? '#3b82f6' : idx ? '#22d3ee' : sel.has(l.name) ? '#fbbf24' : done.has(l.name) ? '#34d399' : emph.has(l.name) ? '#22d3ee' : '#3a5183';
        return (
          <g key={l.name} opacity={faded ? 0.4 : 1} className={onNodeClick ? 'cursor-pointer' : ''}
            onClick={(e) => { if (onNodeClick) { e.stopPropagation(); onNodeClick(l.name); } }}
            onMouseEnter={() => setHover(l.name)} onMouseLeave={() => setHover(null)}>
            <circle cx={p.x} cy={p.y} r={r + (hover === l.name ? 1.2 : 0)} fill={fill} stroke={isDepot ? '#93c5fd' : '#0a1224'} strokeWidth={isDepot ? 0.9 : 0.6} />
            {idx && <text x={p.x} y={p.y + 1.1} textAnchor="middle" fontSize={3} fontWeight={700} fill="#04121f">{idx}</text>}
            {isDepot && <text x={p.x} y={p.y + 1.1} textAnchor="middle" fontSize={3} fontWeight={700} fill="#fff">D</text>}
            <text x={p.x} y={p.y + r + 3.4} textAnchor="middle" fontSize={2.7} fill={lit ? '#e6edf8' : '#a9b8d2'} stroke="#0a1224" strokeWidth={0.9} paintOrder="stroke">{l.name}</text>
            {labels[l.name] && <text x={p.x} y={p.y - r - 1.4} textAnchor="middle" fontSize={2.7} fontWeight={600} fill="#fbbf24" stroke="#0a1224" strokeWidth={0.9} paintOrder="stroke">{labels[l.name]}</text>}
          </g>
        );
      })}
    </svg>
  );
}
