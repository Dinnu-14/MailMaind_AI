import { Cpu, Moon, RotateCcw, Save, Sun, X } from "lucide-react";
import { useEffect, useState } from "react";
import { EngineTag, PageHeader } from "../components/ui";
import { ProfileIcon } from "../components/ProfileSwitcher";
import { useApp } from "../context/AppContext";
import { api, errorMessage } from "../services/api";

export default function Settings() {
  const { prefs, profiles, switchProfile, refresh, notify, dark, toggleDark, health, stats } = useApp();
  const [all, setAll] = useState<string[]>([]);
  const [profession, setProfession] = useState("");
  const [cats, setCats] = useState<string[]>([]);
  const [boost, setBoost] = useState<string[]>([]);
  const [kws, setKws] = useState<string[]>([]);
  const [kw, setKw] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => { api.categories().then(setAll).catch(() => setAll([])); }, []);
  useEffect(() => {
    if (!prefs) return;
    setProfession(prefs.profession); setCats(prefs.categories); setBoost(prefs.boosted_categories); setKws(prefs.keywords);
  }, [prefs]);

  const flip = (list: string[], v: string) => (list.includes(v) ? list.filter((x) => x !== v) : [...list, v]);
  const addKw = () => { const v = kw.trim().toLowerCase(); if (v && !kws.includes(v)) setKws([...kws, v]); setKw(""); };

  const save = async () => {
    setBusy(true);
    try {
      await api.savePreferences({ profession, categories: cats, boosted_categories: boost.filter((b) => cats.includes(b)), keywords: kws });
      await refresh();
      notify("Preferences saved and emails reclassified");
    } catch (e) { notify(errorMessage(e), "error"); } finally { setBusy(false); }
  };
  const reclassify = async (engine: "auto" | "rules" | "gemini") => {
    setBusy(true);
    try {
      const r = await api.classify(engine);
      await refresh();
      notify(`Reclassified ${r.total} emails using ${r.engine === "gemini" ? "Gemini" : "local rules"}`);
    } catch (e) { notify(errorMessage(e), "error"); } finally { setBusy(false); }
  };
  const resetAll = async () => {
    try { await api.resetChat(); await refresh(); notify("Preferences reset to the profile defaults"); } catch (e) { notify(errorMessage(e), "error"); }
  };

  return (
    <>
      <PageHeader title="Settings" subtitle="Fine-tune preferences by hand. The chatbot edits the same data." />
      <div className="grid gap-5 lg:grid-cols-3">
        <div className="space-y-5 lg:col-span-2">
          <section className="card p-5">
            <h2 className="text-sm font-extrabold">Demo profile</h2>
            <p className="mt-1 text-xs text-slate-500">Switch to see the same emails ranked differently. Each profile keeps its own preferences and chat.</p>
            <div className="mt-3 grid gap-2 sm:grid-cols-2">
              {profiles.map((p) => (
                <button key={p.key} onClick={() => switchProfile(p.key)} aria-pressed={p.is_active}
                  className={`flex items-start gap-3 rounded-xl border p-3 text-left transition-colors ${p.is_active ? "border-brand-400 bg-brand-50 dark:border-brand-600 dark:bg-brand-900/30" : "border-slate-200 hover:bg-slate-50 dark:border-slate-700 dark:hover:bg-slate-800"}`}>
                  <span className="mt-0.5 text-brand-600 dark:text-brand-300"><ProfileIcon icon={p.icon} /></span>
                  <span><span className="block text-sm font-bold">{p.name}</span><span className="block text-xs text-slate-500">{p.description}</span></span>
                </button>
              ))}
            </div>
          </section>

          <section className="card p-5">
            <h2 className="text-sm font-extrabold">Preferences for {prefs?.profile_name}</h2>
            <label className="mt-3 block text-xs font-bold text-slate-500" htmlFor="prof">Profession</label>
            <input id="prof" className="field mt-1 w-full max-w-sm" value={profession} onChange={(e) => setProfession(e.target.value)} maxLength={120} />
            <div className="mt-4 text-xs font-bold text-slate-500">Topics to prioritize (click to toggle, star to boost)</div>
            <div className="mt-2 flex flex-wrap gap-2">
              {all.map((c) => {
                const on = cats.includes(c);
                return (
                  <span key={c} className={`chip !py-0 ${on ? "border-brand-300 bg-brand-50 text-brand-700 dark:border-brand-700 dark:bg-brand-900/30 dark:text-brand-200" : "border-slate-200 text-slate-500 dark:border-slate-700"}`}>
                    <button className="py-1" onClick={() => setCats(flip(cats, c))} aria-pressed={on}>{c}</button>
                    {on && <button className={`py-1 ${boost.includes(c) ? "text-amber-500" : "text-slate-300 hover:text-amber-400"}`} onClick={() => setBoost(flip(boost, c))} aria-label={`Boost ${c}`} aria-pressed={boost.includes(c)}>★</button>}
                  </span>
                );
              })}
            </div>
            <div className="mt-4 text-xs font-bold text-slate-500">Focus keywords (roles, skills)</div>
            <div className="mt-2 flex flex-wrap items-center gap-2">
              {kws.map((k) => <span key={k} className="chip border-slate-200 text-slate-700 dark:border-slate-700 dark:text-slate-200">{k}<button onClick={() => setKws(kws.filter((x) => x !== k))} aria-label={`Remove ${k}`}><X size={12} /></button></span>)}
              <form onSubmit={(e) => { e.preventDefault(); addKw(); }} className="flex gap-2">
                <input className="field !py-1 text-xs" placeholder="e.g. data engineering" value={kw} onChange={(e) => setKw(e.target.value)} aria-label="Add keyword" />
                <button className="btn-outline !py-1 text-xs" disabled={!kw.trim()}>Add</button>
              </form>
            </div>
            <div className="mt-5 flex flex-wrap gap-2">
              <button className="btn-primary" onClick={save} disabled={busy}><Save size={16} /> Save and reclassify</button>
              <button className="btn-outline" onClick={resetAll}><RotateCcw size={16} /> Reset to profile defaults</button>
            </div>
          </section>
        </div>

        <div className="space-y-5">
          <section className="card p-5">
            <h2 className="flex items-center gap-2 text-sm font-extrabold"><Cpu size={16} /> AI engine</h2>
            <dl className="mt-3 space-y-2 text-sm">
              <div className="flex justify-between"><dt className="text-slate-500">Mode</dt><dd className="font-semibold">{health?.mode ?? "..."}</dd></div>
              <div className="flex justify-between"><dt className="text-slate-500">Last classification</dt><dd><EngineTag engine={stats?.engine} /></dd></div>
            </dl>
            {(prefs?.last_error || health?.gemini_last_error) && <p className="mt-3 rounded-lg bg-amber-50 p-2.5 text-xs text-amber-800 dark:bg-amber-950/40 dark:text-amber-200">{prefs?.last_error || health?.gemini_last_error}</p>}
            <div className="mt-4 flex flex-col gap-2">
              <button className="btn-outline" disabled={busy} onClick={() => reclassify("auto")}>Reclassify (automatic)</button>
              <button className="btn-outline" disabled={busy} onClick={() => reclassify("rules")}>Reclassify with local rules</button>
              <button className="btn-outline" disabled={busy || !health?.gemini_configured} onClick={() => reclassify("gemini")}
                title={health?.gemini_configured ? "" : "Set GEMINI_API_KEY on the backend"}>Reclassify with Gemini</button>
            </div>
            {!health?.gemini_configured && <p className="mt-2 text-xs text-slate-500">Gemini is unavailable until GEMINI_API_KEY is set on the backend.</p>}
          </section>
          <section className="card p-5">
            <h2 className="text-sm font-extrabold">Appearance</h2>
            <button className="btn-outline mt-3" onClick={toggleDark}>{dark ? <Sun size={16} /> : <Moon size={16} />} {dark ? "Switch to light mode" : "Switch to dark mode"}</button>
            <p className="mt-4 break-all text-xs text-slate-500">Backend: {api.baseURL}</p>
          </section>
        </div>
      </div>
    </>
  );
}
