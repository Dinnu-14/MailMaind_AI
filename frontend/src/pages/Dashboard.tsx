import { Activity, ArrowRight, Cpu, Inbox, MailWarning, Sparkles, Star } from "lucide-react";
import { Link } from "react-router-dom";
import EmailRow from "../components/EmailRow";
import { Empty, EngineTag, formatDate, PageHeader, PRIORITY_STYLE, Spinner } from "../components/ui";
import { useApp } from "../context/AppContext";
import { useEmails } from "../hooks/useEmails";
import type { Priority } from "../types";

function Stat({ label, value, icon, to, hint }: { label: string; value: number; icon: React.ReactNode; to: string; hint: string }) {
  return (
    <Link to={to} className="card group p-4 transition-colors hover:border-brand-300 dark:hover:border-brand-700">
      <div className="flex items-center justify-between text-slate-500"><span className="text-sm font-semibold">{label}</span>{icon}</div>
      <div className="mt-2 text-3xl font-extrabold tabular-nums">{value}</div>
      <div className="mt-1 text-xs text-slate-500">{hint}</div>
    </Link>
  );
}

export default function Dashboard() {
  const { stats, prefs, activeProfile, setChatOpen, loading } = useApp();
  const { data } = useEmails("priority", { sort: "score_desc" });
  if (loading || !stats) return <Spinner label="Loading dashboard" />;

  const prios: Priority[] = ["High", "Medium", "Low", "Other"];
  const cats = Object.entries(stats.by_category).slice(0, 8);
  const maxCat = Math.max(1, ...cats.map(([, n]) => n));

  return (
    <>
      <PageHeader title={`Welcome, ${prefs?.profession || activeProfile?.name || "there"}`}
        subtitle={prefs?.onboarded ? <>Ranking {stats.total} emails for the <b>{activeProfile?.name}</b> profile.</> : "Tell the assistant what matters to you to start ranking your inbox."}
        actions={<button className="btn-primary" onClick={() => setChatOpen(true)}><Sparkles size={16} /> Update my preferences</button>} />

      {!prefs?.onboarded && (
        <div className="card mb-5 flex flex-wrap items-center justify-between gap-3 border-brand-200 bg-brand-50 p-4 dark:border-brand-800 dark:bg-brand-900/20">
          <p className="text-sm font-semibold">Nothing is prioritized yet. Chat with the assistant, or pick a demo profile from the top bar.</p>
          <Link to="/assistant" className="btn-primary">Start the chat <ArrowRight size={16} /></Link>
        </div>
      )}

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <Stat label="Total emails" value={stats.total} icon={<Inbox size={18} />} to="/all" hint="Always kept in All Inbox" />
        <Stat label="Important" value={stats.important} icon={<Star size={18} />} to="/priority" hint={`${stats.unread_important} unread`} />
        <Stat label="Other" value={stats.other} icon={<Inbox size={18} />} to="/all?status=other" hint="Not relevant to you right now" />
        <Stat label="Unread" value={stats.unread} icon={<MailWarning size={18} />} to="/all?status=unread" hint="Across all emails" />
      </div>

      <div className="mt-5 grid gap-5 lg:grid-cols-3">
        <section className="card p-5 lg:col-span-2">
          <h2 className="text-sm font-extrabold">Priority breakdown</h2>
          <div className="mt-3 flex h-3 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800" role="img"
            aria-label={prios.map((p) => `${p}: ${stats.by_priority[p]}`).join(", ")}>
            {prios.map((p) => stats.by_priority[p] > 0 && <div key={p} className={PRIORITY_STYLE[p].rail} style={{ width: `${(stats.by_priority[p] / stats.total) * 100}%` }} />)}
          </div>
          <div className="mt-3 flex flex-wrap gap-x-5 gap-y-1 text-xs">
            {prios.map((p) => (
              <Link key={p} to={`/all?priority=${p}`} className="flex items-center gap-1.5 font-semibold text-slate-600 hover:underline dark:text-slate-300">
                <span className={`h-2.5 w-2.5 rounded-full ${PRIORITY_STYLE[p].rail}`} /> {p} <span className="tabular-nums text-slate-400">{stats.by_priority[p]}</span>
              </Link>
            ))}
          </div>
          <h2 className="mt-6 text-sm font-extrabold">Categories found in your inbox</h2>
          <ul className="mt-3 space-y-2">
            {cats.map(([name, n]) => (
              <li key={name}>
                <Link to={`/all?category=${encodeURIComponent(name)}`} className="flex items-center gap-3 text-sm hover:text-brand-700">
                  <span className="w-44 shrink-0 truncate font-semibold">{name}</span>
                  <span className="h-2 flex-1 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800"><span className="block h-full rounded-full bg-brand-500" style={{ width: `${(n / maxCat) * 100}%` }} /></span>
                  <span className="w-5 text-right text-xs font-bold tabular-nums text-slate-500">{n}</span>
                </Link>
              </li>
            ))}
          </ul>
        </section>

        <div className="space-y-5">
          <section className="card p-5">
            <h2 className="flex items-center gap-2 text-sm font-extrabold"><Cpu size={16} /> AI engine</h2>
            <div className="mt-3 flex items-center gap-2"><EngineTag engine={stats.engine} /><span className="text-xs text-slate-500">{stats.gemini_configured ? "Gemini key configured" : "Demo mode, no Gemini key"}</span></div>
            {stats.engine_error && <p className="mt-3 rounded-lg bg-amber-50 p-2.5 text-xs text-amber-800 dark:bg-amber-950/40 dark:text-amber-200">{stats.engine_error}</p>}
          </section>
          <section className="card p-5">
            <h2 className="flex items-center gap-2 text-sm font-extrabold"><Activity size={16} /> Recent activity</h2>
            <ul className="mt-3 space-y-2.5">
              {stats.recent_activity.map((a, i) => (
                <li key={i} className="text-xs"><span className="font-semibold">{a.text}</span><span className="ml-2 text-slate-400">{formatDate(a.created_at)}</span></li>
              ))}
              {!stats.recent_activity.length && <li className="text-xs text-slate-500">Nothing yet.</li>}
            </ul>
          </section>
        </div>
      </div>

      <section className="card mt-5 overflow-hidden">
        <div className="flex items-center justify-between px-5 py-4">
          <h2 className="text-sm font-extrabold">Top of your Priority Inbox</h2>
          <Link to="/priority" className="text-sm font-semibold text-brand-600 hover:underline dark:text-brand-300">View all {stats.important}</Link>
        </div>
        {data && data.items.length === 0 && <Empty title="No priority emails yet" icon={<Star size={32} />}>Set your preferences in the assistant to fill this list.</Empty>}
        <ul className="border-t border-slate-100 dark:border-slate-800">{data?.items.slice(0, 5).map((e) => <EmailRow key={e.id} email={e} showReason />)}</ul>
      </section>
    </>
  );
}
