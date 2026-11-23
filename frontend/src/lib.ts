import { useCallback, useEffect, useRef, useState } from 'react';
import { api, errorMessage } from './api';

export const fmt = (n: number | null | undefined, digits = 1): string =>
  n === null || n === undefined || Number.isNaN(n) ? '-' : n.toLocaleString('en-IN', { maximumFractionDigits: digits, minimumFractionDigits: 0 });

/** Milliseconds with sensible precision for sub-millisecond values. */
export const fmtMs = (ms: number | null | undefined): string => {
  if (ms === null || ms === undefined) return '-';
  if (ms >= 100) return `${ms.toFixed(0)} ms`;
  if (ms >= 1) return `${ms.toFixed(2)} ms`;
  return `${ms.toFixed(3)} ms`;
};

export const fmtDate = (iso: string | null | undefined): string => {
  if (!iso) return '-';
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString('en-GB', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' });
};

export const PRIORITY_LABEL: Record<number, string> = { 5: 'Critical', 4: 'High', 3: 'Medium', 2: 'Low', 1: 'Minimal' };

/** Generic data hook: loads on mount, exposes reload and the friendly error. */
export function useApi<T>(path: string | null) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(path !== null);
  const alive = useRef(true);
  useEffect(() => { alive.current = true; return () => { alive.current = false; }; }, []);
  const reload = useCallback(async () => {
    if (path === null) return;
    setLoading(true);
    try {
      const result = await api.get<T>(path);
      if (alive.current) { setData(result); setError(null); }
    } catch (e) {
      if (alive.current) setError(errorMessage(e));
    } finally {
      if (alive.current) setLoading(false);
    }
  }, [path]);
  useEffect(() => { void reload(); }, [reload]);
  return { data, error, loading, reload, setData };
}

export function useLocalState<T>(key: string, initial: T): [T, (v: T) => void] {
  const [value, setValue] = useState<T>(() => {
    try { const raw = localStorage.getItem(key); return raw ? (JSON.parse(raw) as T) : initial; } catch { return initial; }
  });
  const set = (v: T) => { setValue(v); try { localStorage.setItem(key, JSON.stringify(v)); } catch { /* storage unavailable */ } };
  return [value, set];
}

export const clamp = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v));
