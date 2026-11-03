import { createContext, ReactNode, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api, errorMessage } from "../services/api";
import type { Health, Preferences, Profile, Stats } from "../types";

interface Toast { id: number; text: string; kind: "ok" | "error" }

interface Ctx {
  profiles: Profile[];
  activeProfile?: Profile;
  prefs?: Preferences;
  stats?: Stats;
  health?: Health;
  loading: boolean;
  error: string | null;
  /** bumps whenever classifications may have changed, so lists reload */
  version: number;
  refresh: () => Promise<void>;
  switchProfile: (key: Profile["key"], resetChat?: boolean) => Promise<void>;
  syncEmails: () => Promise<void>;
  dark: boolean;
  toggleDark: () => void;
  chatOpen: boolean;
  setChatOpen: (v: boolean) => void;
  toasts: Toast[];
  notify: (text: string, kind?: Toast["kind"]) => void;
}

const AppCtx = createContext<Ctx | null>(null);

export function AppProvider({ children }: { children: ReactNode }) {
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [prefs, setPrefs] = useState<Preferences>();
  const [stats, setStats] = useState<Stats>();
  const [health, setHealth] = useState<Health>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [version, setVersion] = useState(0);
  const [chatOpen, setChatOpen] = useState(false);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const [dark, setDark] = useState(() => document.documentElement.classList.contains("dark"));

  const notify = useCallback((text: string, kind: Toast["kind"] = "ok") => {
    const id = Date.now() + Math.random();
    setToasts((t) => [...t, { id, text, kind }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), 4500);
  }, []);

  const refresh = useCallback(async () => {
    try {
      const [h, p, pr, s] = await Promise.all([api.health(), api.profiles(), api.preferences(), api.stats()]);
      setHealth(h); setProfiles(p); setPrefs(pr); setStats(s);
      setError(null);
      setVersion((v) => v + 1);
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { void refresh(); }, [refresh]);

  const switchProfile = useCallback(async (key: Profile["key"], resetChat = false) => {
    try {
      await api.switchProfile(key, resetChat);
      await refresh();
    } catch (e) {
      notify(errorMessage(e), "error");
    }
  }, [refresh, notify]);

  const syncEmails = useCallback(async () => {
    try {
      const r = await api.reload();
      await refresh();
      notify(`Reloaded ${r.loaded} sample emails. Read status was reset.`);
    } catch (e) {
      notify(errorMessage(e), "error");
    }
  }, [refresh, notify]);

  const toggleDark = useCallback(() => {
    setDark((d) => {
      const next = !d;
      document.documentElement.classList.toggle("dark", next);
      try { localStorage.setItem("theme", next ? "dark" : "light"); } catch { /* ignore */ }
      return next;
    });
  }, []);

  const value = useMemo<Ctx>(() => ({
    profiles, activeProfile: profiles.find((p) => p.is_active), prefs, stats, health, loading, error, version,
    refresh, switchProfile, syncEmails, dark, toggleDark, chatOpen, setChatOpen, toasts, notify,
  }), [profiles, prefs, stats, health, loading, error, version, refresh, switchProfile, syncEmails, dark, toggleDark, chatOpen, toasts, notify]);

  return <AppCtx.Provider value={value}>{children}</AppCtx.Provider>;
}

export function useApp(): Ctx {
  const c = useContext(AppCtx);
  if (!c) throw new Error("useApp must be used inside AppProvider");
  return c;
}
