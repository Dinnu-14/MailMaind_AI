import { Inbox, Search, X } from "lucide-react";
import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useEmails } from "../hooks/useEmails";
import { api } from "../services/api";
import type { EmailQuery } from "../types";
import EmailRow from "./EmailRow";
import { Empty, ErrorBanner, Spinner } from "./ui";

type Mode = "priority" | "all";

export default function EmailList({ mode }: { mode: Mode }) {
  const [params, setParams] = useSearchParams();
  const [categories, setCategories] = useState<string[]>([]);
  const q = params.get("q") ?? "";
  const category = params.get("category") ?? "";
  const priority = params.get("priority") ?? "";
  const status = params.get("status") ?? "";
  const sort = (params.get("sort") ?? (mode === "priority" ? "score_desc" : "date_desc")) as NonNullable<EmailQuery["sort"]>;
  const [text, setText] = useState(q);

  useEffect(() => { setText(q); }, [q]);
  useEffect(() => { api.categories().then(setCategories).catch(() => setCategories([])); }, []);

  const set = (key: string, value: string) => {
    const next = new URLSearchParams(params);
    if (value) next.set(key, value); else next.delete(key);
    setParams(next, { replace: true });
  };
  useEffect(() => {
    if (text === q) return;
    const t = setTimeout(() => set("q", text.trim()), 300);
    return () => clearTimeout(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [text]);

  const query: EmailQuery = {
    q: q || undefined, category: category || undefined, priority: priority || undefined, sort,
    unread: status === "unread" || undefined,
    important: mode === "all" && (status === "important" || status === "other") ? status === "important" : undefined,
  };
  const { data, loading, error, reload } = useEmails(mode, query);
  const filtered = Boolean(q || category || priority || status);
  const clear = () => { setText(""); setParams({}, { replace: true }); };

  const sel = "field !py-1.5 !pr-8 text-xs font-semibold";
  return (
    <div className="card overflow-hidden">
      <div className="flex flex-wrap items-center gap-2 border-b border-slate-100 p-3 dark:border-slate-800 sm:p-4">
        <label className="relative min-w-[200px] flex-1">
          <span className="sr-only">Search emails</span>
          <Search size={16} className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input className="field w-full !pl-9" value={text} onChange={(e) => setText(e.target.value)}
            placeholder='Search sender, subject or content, e.g. "unread interviews"' />
        </label>
        <select className={sel} value={category} onChange={(e) => set("category", e.target.value)} aria-label="Filter by category">
          <option value="">All categories</option>
          {categories.map((c) => <option key={c}>{c}</option>)}
        </select>
        <select className={sel} value={priority} onChange={(e) => set("priority", e.target.value)} aria-label="Filter by priority">
          <option value="">Any priority</option>
          {(mode === "priority" ? ["High", "Medium", "Low"] : ["High", "Medium", "Low", "Other"]).map((p) => <option key={p}>{p}</option>)}
        </select>
        <select className={sel} value={status} onChange={(e) => set("status", e.target.value)} aria-label="Filter by status">
          <option value="">Read and unread</option>
          <option value="unread">Unread only</option>
          {mode === "all" && <option value="important">Important only</option>}
          {mode === "all" && <option value="other">Not important only</option>}
        </select>
        <select className={sel} value={sort} onChange={(e) => set("sort", e.target.value)} aria-label="Sort emails">
          <option value="date_desc">Latest first</option>
          <option value="date_asc">Oldest first</option>
          <option value="score_desc">Most relevant first</option>
        </select>
        {filtered && <button className="btn-ghost !py-1.5 text-xs" onClick={clear}><X size={14} /> Clear</button>}
      </div>
      {data && (
        <div className="flex flex-wrap items-center gap-2 border-b border-slate-100 px-4 py-2 text-xs text-slate-500 dark:border-slate-800 sm:px-5">
          <span className="font-bold text-slate-700 dark:text-slate-300">{data.total} email{data.total !== 1 ? "s" : ""}</span>
          {data.query_description && <span>understood as: {data.query_description}</span>}
        </div>
      )}
      {error && <div className="p-4"><ErrorBanner message={error} onRetry={reload} /></div>}
      {loading && !data && <Spinner label="Loading emails" />}
      {data && data.items.length === 0 && (
        <Empty title={filtered ? "No emails match these filters" : mode === "priority" ? "Nothing is prioritized yet" : "No emails"}
          icon={<Inbox size={36} />}>
          {filtered ? "Nothing was deleted. Clear the filters to see everything again."
            : mode === "priority" ? "Tell the AI assistant what matters to you, or pick a demo profile, and relevant emails will appear here."
              : "Use Sync in the top bar to reload the sample emails."}
        </Empty>
      )}
      {data && data.items.length > 0 && (
        <ul className={loading ? "opacity-60 transition-opacity" : "transition-opacity"}>
          {data.items.map((e) => <EmailRow key={e.id} email={e} showReason={mode === "priority" || Boolean(e.classification?.is_important)} />)}
        </ul>
      )}
    </div>
  );
}
