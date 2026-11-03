import { Bot } from "lucide-react";
import ChatPanel from "../components/ChatPanel";
import { ProfileIcon } from "../components/ProfileSwitcher";
import { PageHeader } from "../components/ui";
import { useApp } from "../context/AppContext";

export default function Assistant() {
  const { prefs, profiles, switchProfile, notify } = useApp();
  return (
    <>
      <PageHeader title="AI Assistant" subtitle="Describe what matters to you in plain language. Your Priority Inbox updates right away." />
      <div className="grid gap-5 lg:grid-cols-3">
        <section className="card flex h-[calc(100vh-15rem)] min-h-[420px] flex-col overflow-hidden lg:col-span-2" aria-label="Conversation">
          <div className="flex items-center gap-2 border-b border-slate-100 px-4 py-3 text-sm font-extrabold dark:border-slate-800"><Bot size={16} className="text-brand-600" /> Conversation</div>
          <div className="min-h-0 flex-1"><ChatPanel /></div>
        </section>
        <div className="space-y-5">
          <section className="card p-5">
            <h2 className="text-sm font-extrabold">What I understood so far</h2>
            <dl className="mt-3 space-y-3 text-sm">
              <div><dt className="text-xs font-bold text-slate-500">Profession</dt><dd>{prefs?.profession || "Not set yet"}</dd></div>
              <div><dt className="text-xs font-bold text-slate-500">Prioritized topics</dt>
                <dd className="mt-1 flex flex-wrap gap-1.5">{prefs?.categories.length ? prefs.categories.map((c) => <span key={c} className="chip border-brand-200 bg-brand-50 text-brand-700 dark:border-brand-800 dark:bg-brand-900/30 dark:text-brand-200">{c}{prefs.boosted_categories.includes(c) ? " ★" : ""}</span>) : "None yet"}</dd></div>
              {!!prefs?.keywords.length && <div><dt className="text-xs font-bold text-slate-500">Focus keywords</dt><dd className="mt-1 flex flex-wrap gap-1.5">{prefs.keywords.map((k) => <span key={k} className="chip border-slate-200 text-slate-600 dark:border-slate-700 dark:text-slate-300">{k}</span>)}</dd></div>}
              {!!prefs?.excluded_categories.length && <div><dt className="text-xs font-bold text-slate-500">Not prioritized</dt><dd>{prefs.excluded_categories.join(", ")}</dd></div>}
            </dl>
          </section>
          <section className="card p-5">
            <h2 className="text-sm font-extrabold">Or start from a demo profile</h2>
            <div className="mt-3 space-y-2">
              {profiles.filter((p) => p.key !== "custom").map((p) => (
                <button key={p.key} className="btn-outline w-full !justify-start" onClick={async () => { await switchProfile(p.key); notify(`Switched to ${p.name}`); }}>
                  <ProfileIcon icon={p.icon} /> {p.name}
                </button>
              ))}
            </div>
          </section>
        </div>
      </div>
    </>
  );
}
