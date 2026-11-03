import { AlertTriangle, CheckCircle2, Cpu, Loader2, Sparkles } from "lucide-react";
import type { ReactNode } from "react";
import { useApp } from "../context/AppContext";
import type { Priority } from "../types";

export const PRIORITY_STYLE: Record<Priority, { rail: string; badge: string; label: string }> = {
  High: { rail: "bg-rose-500", badge: "border-rose-200 bg-rose-50 text-rose-700 dark:border-rose-900 dark:bg-rose-950/50 dark:text-rose-300", label: "High" },
  Medium: { rail: "bg-amber-500", badge: "border-amber-200 bg-amber-50 text-amber-700 dark:border-amber-900 dark:bg-amber-950/50 dark:text-amber-300", label: "Medium" },
  Low: { rail: "bg-sky-500", badge: "border-sky-200 bg-sky-50 text-sky-700 dark:border-sky-900 dark:bg-sky-950/50 dark:text-sky-300", label: "Low" },
  Other: { rail: "bg-slate-300 dark:bg-slate-700", badge: "border-slate-200 bg-slate-50 text-slate-500 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-400", label: "Other" },
};

export function PriorityBadge({ priority }: { priority: Priority }) {
  const s = PRIORITY_STYLE[priority];
  return <span className={`chip ${s.badge}`}>{s.label}</span>;
}

export function ScoreMeter({ score, priority, wide = false }: { score: number; priority: Priority; wide?: boolean }) {
  return (
    <div className={`flex items-center gap-2 ${wide ? "w-full" : "w-24"}`} title={`Relevance ${score}/100`}>
      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-slate-100 dark:bg-slate-800" role="meter" aria-valuemin={0} aria-valuemax={100} aria-valuenow={score} aria-label="Relevance score">
        <div className={`h-full rounded-full ${PRIORITY_STYLE[priority].rail}`} style={{ width: `${Math.max(score, 3)}%` }} />
      </div>
      <span className="w-7 text-right text-xs font-bold tabular-nums text-slate-600 dark:text-slate-300">{score}</span>
    </div>
  );
}

export function EngineTag({ engine }: { engine?: string | null }) {
  if (!engine) return null;
  const gem = engine === "gemini";
  return (
    <span className={`chip ${gem ? "border-brand-200 bg-brand-50 text-brand-700 dark:border-brand-800 dark:bg-brand-900/40 dark:text-brand-200" : "border-slate-200 bg-slate-50 text-slate-600 dark:border-slate-700 dark:bg-slate-800 dark:text-slate-300"}`}
      title={gem ? "Produced by the Gemini API" : "Produced by the built-in rule-based engine (demo mode)"}>
      {gem ? <Sparkles size={12} /> : <Cpu size={12} />}
      {gem ? "Gemini" : "Local rules"}
    </span>
  );
}

export function Spinner({ label = "Loading" }: { label?: string }) {
  return (
    <div className="flex items-center justify-center gap-2 py-16 text-sm text-slate-500" role="status">
      <Loader2 className="animate-spin" size={18} /> {label}
    </div>
  );
}

export function ErrorBanner({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="flex items-start gap-3 rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800 dark:border-rose-900 dark:bg-rose-950/40 dark:text-rose-200" role="alert">
      <AlertTriangle size={18} className="mt-0.5 shrink-0" />
      <div className="flex-1">{message}</div>
      {onRetry && <button className="btn-outline !py-1" onClick={onRetry}>Try again</button>}
    </div>
  );
}

export function Empty({ title, children, icon }: { title: string; children?: ReactNode; icon?: ReactNode }) {
  return (
    <div className="flex flex-col items-center gap-2 px-6 py-16 text-center">
      {icon && <div className="text-slate-300 dark:text-slate-600">{icon}</div>}
      <h3 className="text-base font-bold">{title}</h3>
      <p className="max-w-sm text-sm text-slate-500">{children}</p>
    </div>
  );
}

export function PageHeader({ title, subtitle, actions }: { title: string; subtitle?: ReactNode; actions?: ReactNode }) {
  return (
    <div className="mb-5 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h1 className="text-2xl font-extrabold tracking-tight">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-slate-500">{subtitle}</p>}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  );
}

export function ToastHost() {
  const { toasts } = useApp();
  return (
    <div className="pointer-events-none fixed bottom-4 left-1/2 z-[60] flex -translate-x-1/2 flex-col gap-2" aria-live="polite">
      {toasts.map((t) => (
        <div key={t.id} className={`pointer-events-auto flex animate-pop items-center gap-2 rounded-xl px-4 py-2.5 text-sm font-semibold text-white shadow-lg ${t.kind === "ok" ? "bg-slate-900 dark:bg-slate-700" : "bg-rose-600"}`}>
          {t.kind === "ok" ? <CheckCircle2 size={16} /> : <AlertTriangle size={16} />} {t.text}
        </div>
      ))}
    </div>
  );
}

export function formatDate(iso: string, long = false): string {
  const d = new Date(iso);
  if (long) return d.toLocaleString("en-IN", { weekday: "short", day: "numeric", month: "short", year: "numeric", hour: "numeric", minute: "2-digit" });
  return d.toLocaleDateString("en-IN", { day: "numeric", month: "short" });
}

export function initials(name: string): string {
  return name.split(/\s+/).filter(Boolean).slice(0, 2).map((w) => w[0]?.toUpperCase()).join("") || "?";
}
