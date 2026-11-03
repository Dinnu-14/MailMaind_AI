import { Check, Plus } from "lucide-react";
import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { PageHeader } from "../components/ui";
import { useApp } from "../context/AppContext";
import { api, errorMessage } from "../services/api";

export default function Categories() {
  const { stats, prefs, refresh, notify } = useApp();
  const [all, setAll] = useState<string[]>([]);
  const [busy, setBusy] = useState<string | null>(null);
  useEffect(() => { api.categories().then(setAll).catch(() => setAll([])); }, []);

  const toggle = async (cat: string) => {
    if (!prefs) return;
    setBusy(cat);
    try {
      const on = prefs.categories.includes(cat);
      await api.savePreferences({
        categories: on ? prefs.categories.filter((c) => c !== cat) : [...prefs.categories, cat],
        excluded_categories: on ? [...new Set([...prefs.excluded_categories, cat])] : prefs.excluded_categories.filter((c) => c !== cat),
      });
      await refresh();
      notify(on ? `Stopped prioritizing ${cat}` : `Now prioritizing ${cat}`);
    } catch (e) { notify(errorMessage(e), "error"); } finally { setBusy(null); }
  };

  return (
    <>
      <PageHeader title="Categories" subtitle="How the AI sees your inbox. Counts are personalized to the current profile; click a card to browse it." />
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {all.map((cat) => {
          const on = prefs?.categories.includes(cat);
          return (
            <div key={cat} className={`card flex items-center justify-between gap-3 p-4 ${on ? "border-brand-300 dark:border-brand-700" : ""}`}>
              <Link to={`/all?category=${encodeURIComponent(cat)}`} className="min-w-0 flex-1">
                <div className="truncate text-sm font-extrabold">{cat}</div>
                <div className="text-xs text-slate-500">{stats?.by_category[cat] ?? 0} email{(stats?.by_category[cat] ?? 0) !== 1 ? "s" : ""}</div>
              </Link>
              <button className={on ? "btn-primary !px-3 !py-1.5 text-xs" : "btn-outline !px-3 !py-1.5 text-xs"} disabled={busy === cat || !prefs}
                onClick={() => toggle(cat)} aria-pressed={on}>
                {on ? <><Check size={14} /> Prioritized</> : <><Plus size={14} /> Prioritize</>}
              </button>
            </div>
          );
        })}
      </div>
    </>
  );
}
