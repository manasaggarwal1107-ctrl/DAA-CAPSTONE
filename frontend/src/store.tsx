// Global application state: parcels, road network, settings, latest optimisation result and toasts.
import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import { api, errorMessage } from './api';
import { Icon } from './icons';
import type { AppState, Result } from './types';

type ToastTone = 'good' | 'bad' | 'info';
interface Toast { id: number; message: string; tone: ToastTone }

interface Ctx {
  state: AppState | null;
  result: Result | null;
  loading: boolean;
  loadError: string | null;
  refresh: () => Promise<void>;
  optimise: (body?: { capacity?: number; depot?: string }) => Promise<Result | null>;
  toast: (message: string, tone?: ToastTone) => void;
  running: boolean;
}

const AppCtx = createContext<Ctx | null>(null);

export function useApp(): Ctx {
  const c = useContext(AppCtx);
  if (!c) throw new Error('useApp must be used inside AppProvider');
  return c;
}

export function AppProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AppState | null>(null);
  const [result, setResult] = useState<Result | null>(null);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [running, setRunning] = useState(false);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const nextId = useRef(1);

  const toast = useCallback((message: string, tone: ToastTone = 'info') => {
    const id = nextId.current++;
    setToasts((t) => [...t, { id, message, tone }]);
    window.setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), tone === 'bad' ? 7000 : 3800);
  }, []);

  const refresh = useCallback(async () => {
    try {
      const [s, r] = await Promise.all([api.get<AppState>('/api/state'), api.get<{ result: Result | null }>('/api/result')]);
      setState(s); setResult(r.result); setLoadError(null);
    } catch (e) {
      setLoadError(errorMessage(e));
    } finally {
      setLoading(false);
    }
  }, []);

  const optimise = useCallback(async (body: { capacity?: number; depot?: string } = {}) => {
    setRunning(true);
    try {
      const r = await api.post<Result>('/api/optimise', body);
      await refresh();
      toast(r.status === 'optimised' ? 'Optimisation complete' : 'Optimisation finished with warnings', r.status === 'optimised' ? 'good' : 'info');
      return r;
    } catch (e) {
      toast(errorMessage(e), 'bad');
      return null;
    } finally {
      setRunning(false);
    }
  }, [refresh, toast]);

  useEffect(() => { void refresh(); }, [refresh]);

  const value = useMemo(() => ({ state, result, loading, loadError, refresh, optimise, toast, running }),
    [state, result, loading, loadError, refresh, optimise, toast, running]);

  return (
    <AppCtx.Provider value={value}>
      {children}
      <div className="pointer-events-none fixed bottom-4 right-4 z-[60] flex w-80 flex-col gap-2" aria-live="polite">
        {toasts.map((t) => (
          <div key={t.id} className={`toast rise pointer-events-auto toast-${t.tone}`}>
            <Icon name={t.tone === 'good' ? 'check' : t.tone === 'bad' ? 'alert' : 'info'} size={16} className="mt-0.5" />
            <span className="text-[13px]">{t.message}</span>
          </div>
        ))}
      </div>
    </AppCtx.Provider>
  );
}
