// Small stroke icon set (24x24 grid, Lucide-style geometry), drawn as inline SVG so no icon package is needed.
import type { ReactNode } from 'react';

const P = (d: string) => <path d={d} />;
const C = (cx: number, cy: number, r: number) => <circle cx={cx} cy={cy} r={r} />;

const ICONS: Record<string, ReactNode> = {
  dashboard: <>{P('M3 3h7v9H3z')}{P('M14 3h7v5h-7z')}{P('M14 12h7v9h-7z')}{P('M3 16h7v5H3z')}</>,
  package: <>{P('M21 8l-9-5-9 5 9 5 9-5z')}{P('M3 8v8l9 5 9-5V8')}{P('M12 13v8')}</>,
  sort: <>{P('M7 4v16')}{P('M3 8l4-4 4 4')}{P('M17 20V4')}{P('M13 16l4 4 4-4')}</>,
  scale: <>{P('M12 3v18')}{P('M5 21h14')}{P('M5 7h14')}{P('M5 7l-3 8a3 3 0 0 0 6 0L5 7z')}{P('M19 7l-3 8a3 3 0 0 0 6 0l-3-8z')}</>,
  network: <>{C(12, 5, 2)}{C(5, 19, 2)}{C(19, 19, 2)}{P('M12 7v4')}{P('M12 11l-6 6')}{P('M12 11l6 6')}</>,
  route: <>{C(6, 19, 3)}{C(18, 5, 3)}{P('M9 19h8.5a3.5 3.5 0 0 0 0-7h-11a3.5 3.5 0 0 1 0-7H15')}</>,
  gauge: <>{P('M12 14l4-4')}{P('M3.3 18a10 10 0 1 1 17.4 0')}</>,
  book: <>{P('M4 19.5A2.5 2.5 0 0 1 6.5 17H20')}{P('M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z')}</>,
  file: <>{P('M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z')}{P('M14 2v6h6')}{P('M8 13h8')}{P('M8 17h8')}</>,
  plus: <>{P('M12 5v14')}{P('M5 12h14')}</>,
  trash: <>{P('M3 6h18')}{P('M8 6V4h8v2')}{P('M19 6l-1 14H6L5 6')}{P('M10 11v6')}{P('M14 11v6')}</>,
  edit: <>{P('M12 20h9')}{P('M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z')}</>,
  search: <>{C(11, 11, 7)}{P('M21 21l-4.3-4.3')}</>,
  download: <>{P('M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4')}{P('M7 10l5 5 5-5')}{P('M12 15V3')}</>,
  upload: <>{P('M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4')}{P('M17 8l-5-5-5 5')}{P('M12 3v12')}</>,
  play: P('M6 4l14 8-14 8z'),
  pause: <>{P('M6 4h4v16H6z')}{P('M14 4h4v16h-4z')}</>,
  prev: P('M15 18l-6-6 6-6'),
  next: P('M9 18l6-6-6-6'),
  x: <>{P('M18 6L6 18')}{P('M6 6l12 12')}</>,
  check: P('M20 6L9 17l-5-5'),
  alert: <>{P('M10.3 3.9L1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z')}{P('M12 9v4')}{P('M12 17h.01')}</>,
  info: <>{C(12, 12, 10)}{P('M12 16v-4')}{P('M12 8h.01')}</>,
  zap: P('M13 2L3 14h9l-1 8 10-12h-9z'),
  refresh: <>{P('M3 12a9 9 0 0 1 15-6.7L21 8')}{P('M21 3v5h-5')}{P('M21 12a9 9 0 0 1-15 6.7L3 16')}{P('M3 21v-5h5')}</>,
  clock: <>{C(12, 12, 10)}{P('M12 6v6l4 2')}</>,
  pin: <>{P('M20 10c0 6-8 12-8 12S4 16 4 10a8 8 0 0 1 16 0z')}{C(12, 10, 3)}</>,
  truck: <>{P('M1 3h15v13H1z')}{P('M16 8h4l3 3v5h-7z')}{C(5.5, 18.5, 2.5)}{C(18.5, 18.5, 2.5)}</>,
  menu: <>{P('M4 6h16')}{P('M4 12h16')}{P('M4 18h16')}</>,
  database: <>{<ellipse cx="12" cy="5" rx="9" ry="3" />}{P('M21 5v14c0 1.7-4 3-9 3s-9-1.3-9-3V5')}{P('M3 12c0 1.7 4 3 9 3s9-1.3 9-3')}</>,
  layers: <>{P('M12 2L2 7l10 5 10-5-10-5z')}{P('M2 17l10 5 10-5')}{P('M2 12l10 5 10-5')}</>,
  flag: <>{P('M4 22V4')}{P('M4 4h13l-2 4 2 4H4')}</>,
  box: <>{P('M21 16V8a2 2 0 0 0-1-1.7l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.7l7 4a2 2 0 0 0 2 0l7-4a2 2 0 0 0 1-1.7z')}{P('M3.3 7L12 12l8.7-5')}{P('M12 22V12')}</>,
};

export type IconName = keyof typeof ICONS;

export function Icon({ name, size = 16, className = '' }: { name: IconName; size?: number; className?: string }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2}
      strokeLinecap="round" strokeLinejoin="round" className={`shrink-0 ${className}`} aria-hidden="true">
      {ICONS[name]}
    </svg>
  );
}
