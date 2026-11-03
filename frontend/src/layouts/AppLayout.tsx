import {
  Bell, Bot, LayoutDashboard, Inbox, Layers, MailOpen, Menu, Moon, RefreshCw, Search, Settings, Sparkles, Star, Sun, X,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { NavLink, Outlet, useLocation, useNavigate } from "react-router-dom";
import ChatPanel from "../components/ChatPanel";
import ProfileSwitcher, { ProfileIcon } from "../components/ProfileSwitcher";
import { ErrorBanner, ToastHost } from "../components/ui";
import { useApp } from "../context/AppContext";

const NAV = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/priority", label: "Priority Inbox", icon: Star, badge: "important" as const },
  { to: "/all", label: "All Inbox", icon: Inbox, badge: "total" as const },
  { to: "/assistant", label: "AI Assistant", icon: Bot },
  { to: "/categories", label: "Categories", icon: Layers },
  { to: "/settings", label: "Settings", icon: Settings },
];

function Sidebar({ onClose }: { onClose?: () => void }) {
  const { stats, activeProfile, prefs } = useApp();
  return (
    <aside className="flex h-full w-64 flex-col border-r border-slate-200 bg-white dark:border-slate-800 dark:bg-slate-900">
      <div className="flex h-16 items-center justify-between px-5">
        <div className="flex items-center gap-2.5">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600 text-white"><MailOpen size={19} /></div>
          <div className="leading-tight"><div className="text-sm font-extrabold">Smart Email</div><div className="text-xs font-semibold text-brand-600 dark:text-brand-300">AI Assistant</div></div>
        </div>
        {onClose && <button className="btn-ghost !p-2 lg:hidden" onClick={onClose} aria-label="Close menu"><X size={18} /></button>}
      </div>
      <nav className="flex-1 space-y-1 px-3 py-2" aria-label="Main">
        {NAV.map(({ to, label, icon: I, end, badge }) => (
          <NavLink key={to} to={to} end={end} onClick={onClose}
            className={({ isActive }) => `flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm font-semibold transition-colors ${isActive ? "bg-brand-50 text-brand-700 dark:bg-brand-900/40 dark:text-brand-200" : "text-slate-600 hover:bg-slate-100 dark:text-slate-400 dark:hover:bg-slate-800"}`}>
            <I size={18} /> <span className="flex-1">{label}</span>
            {badge && stats && <span className="rounded-full bg-slate-100 px-2 py-0.5 text-xs font-bold text-slate-600 dark:bg-slate-800 dark:text-slate-300">{stats[badge]}</span>}
          </NavLink>
        ))}
      </nav>
      <div className="m-3 flex items-center gap-3 rounded-2xl border border-slate-200 p-3 dark:border-slate-800">
        <div className="flex h-10 w-10 items-center justify-center rounded-full bg-brand-100 text-brand-700 dark:bg-brand-900/50 dark:text-brand-200"><ProfileIcon icon={activeProfile?.icon ?? "user"} size={18} /></div>
        <div className="min-w-0 text-sm"><div className="truncate font-bold">{activeProfile?.name ?? "Profile"}</div><div className="truncate text-xs text-slate-500">{prefs?.profession || "Set up in chat"}</div></div>
      </div>
    </aside>
  );
}

function Notifications() {
  const { stats } = useApp();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const h = (e: MouseEvent) => { if (!ref.current?.contains(e.target as Node)) setOpen(false); };
    document.addEventListener("mousedown", h);
    return () => document.removeEventListener("mousedown", h);
  }, []);
  const count = stats?.unread_important ?? 0;
  return (
    <div className="relative" ref={ref}>
      <button className="btn-ghost relative !p-2.5" onClick={() => setOpen(!open)} aria-label={`Notifications, ${count} unread priority emails`} aria-expanded={open}>
        <Bell size={18} />
        {count > 0 && <span className="absolute right-1 top-1 flex h-4 min-w-4 items-center justify-center rounded-full bg-rose-500 px-1 text-[10px] font-bold text-white">{count}</span>}
      </button>
      {open && (
        <div className="card absolute right-0 z-30 mt-2 w-80 animate-pop p-3 shadow-xl">
          <p className="mb-2 text-sm font-bold">{count} unread priority email{count !== 1 ? "s" : ""}</p>
          <ul className="space-y-2">
            {stats?.recent_activity.slice(0, 5).map((a, i) => <li key={i} className="text-xs text-slate-500">{a.text}</li>)}
            {!stats?.recent_activity.length && <li className="text-xs text-slate-500">No recent activity.</li>}
          </ul>
        </div>
      )}
    </div>
  );
}

export default function AppLayout() {
  const { dark, toggleDark, syncEmails, chatOpen, setChatOpen, error, refresh, health } = useApp();
  const [menu, setMenu] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const loc = useLocation();
  const navigate = useNavigate();
  const [q, setQ] = useState("");

  useEffect(() => { setMenu(false); }, [loc.pathname]);

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const base = loc.pathname === "/priority" ? "/priority" : "/all";
    navigate(q.trim() ? `${base}?q=${encodeURIComponent(q.trim())}` : base);
  };
  const sync = async () => { setSyncing(true); await syncEmails(); setSyncing(false); };

  return (
    <div className="flex h-screen overflow-hidden">
      <div className="hidden lg:block"><Sidebar /></div>
      {menu && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="absolute inset-0 bg-slate-900/40" onClick={() => setMenu(false)} />
          <div className="absolute inset-y-0 left-0 animate-slidein"><Sidebar onClose={() => setMenu(false)} /></div>
        </div>
      )}
      <div className="flex min-w-0 flex-1 flex-col">
        <header className="flex h-16 shrink-0 items-center gap-2 border-b border-slate-200 bg-white px-3 dark:border-slate-800 dark:bg-slate-900 sm:gap-3 sm:px-5">
          <button className="btn-ghost !p-2.5 lg:hidden" onClick={() => setMenu(true)} aria-label="Open menu"><Menu size={19} /></button>
          <form onSubmit={submit} className="relative max-w-xl flex-1" role="search">
            <Search size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input className="field w-full !bg-slate-50 !pl-9 dark:!bg-slate-800" value={q} onChange={(e) => setQ(e.target.value)}
              placeholder="Search all emails" aria-label="Search emails" />
          </form>
          <div className="ml-auto flex items-center gap-1 sm:gap-2">
            <button className="btn-ghost !p-2.5" onClick={sync} disabled={syncing} aria-label="Sync: reload sample emails" title="Reload sample emails">
              <RefreshCw size={18} className={syncing ? "animate-spin" : ""} />
            </button>
            <Notifications />
            <button className="btn-ghost !p-2.5" onClick={toggleDark} aria-label="Toggle dark mode">{dark ? <Sun size={18} /> : <Moon size={18} />}</button>
            <button className="btn-primary hidden sm:inline-flex" onClick={() => setChatOpen(true)}><Sparkles size={16} /> Ask AI</button>
            <ProfileSwitcher />
          </div>
        </header>
        <main className="flex-1 overflow-y-auto">
          <div className="mx-auto max-w-6xl px-4 py-6 sm:px-6">
            {health && !health.gemini_configured && (
              <p className="mb-4 rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs text-slate-500 dark:border-slate-800 dark:bg-slate-900">
                Demo mode: no Gemini API key is configured, so the built-in rule-based AI is classifying emails. Add GEMINI_API_KEY on the backend to use Gemini.
              </p>
            )}
            {error && <div className="mb-4"><ErrorBanner message={error} onRetry={refresh} /></div>}
            <Outlet />
          </div>
        </main>
      </div>
      <button className="btn-primary fixed bottom-4 right-4 z-30 !rounded-full !p-3.5 shadow-lg sm:hidden" onClick={() => setChatOpen(true)} aria-label="Open AI assistant"><Bot size={20} /></button>
      {chatOpen && (
        <div className="fixed inset-0 z-50">
          <div className="absolute inset-0 bg-slate-900/40" onClick={() => setChatOpen(false)} />
          <section className="absolute inset-y-0 right-0 flex w-full max-w-md animate-slidein flex-col bg-white shadow-2xl dark:bg-slate-900" aria-label="AI assistant">
            <div className="flex h-16 items-center justify-between border-b border-slate-100 px-4 dark:border-slate-800">
              <div className="flex items-center gap-2 font-extrabold"><Bot size={18} className="text-brand-600" /> AI Assistant</div>
              <button className="btn-ghost !p-2" onClick={() => setChatOpen(false)} aria-label="Close assistant"><X size={18} /></button>
            </div>
            <div className="min-h-0 flex-1"><ChatPanel onNavigate={() => setChatOpen(false)} /></div>
          </section>
        </div>
      )}
      <ToastHost />
    </div>
  );
}
