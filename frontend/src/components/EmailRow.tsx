import { Link } from "react-router-dom";
import type { EmailItem } from "../types";
import { formatDate, initials, PRIORITY_STYLE, PriorityBadge, ScoreMeter } from "./ui";

export default function EmailRow({ email, showReason }: { email: EmailItem; showReason: boolean }) {
  const c = email.classification;
  const priority = c?.priority ?? "Other";
  return (
    <li>
      <Link to={`/email/${email.id}`}
        className="group relative flex gap-3 border-b border-slate-100 px-4 py-3.5 transition-colors last:border-0 hover:bg-slate-50 dark:border-slate-800 dark:hover:bg-slate-800/50 sm:px-5">
        <span className={`absolute inset-y-2 left-0 w-1 rounded-r-full ${PRIORITY_STYLE[priority].rail}`} aria-hidden />
        <div className={`mt-0.5 hidden h-9 w-9 shrink-0 items-center justify-center rounded-full text-xs font-bold sm:flex ${email.is_read ? "bg-slate-100 text-slate-500 dark:bg-slate-800" : "bg-brand-100 text-brand-700 dark:bg-brand-900/50 dark:text-brand-200"}`}>
          {initials(email.sender_name)}
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            {!email.is_read && <span className="h-2 w-2 shrink-0 rounded-full bg-brand-600" aria-label="Unread" />}
            <span className={`truncate text-sm ${email.is_read ? "font-medium text-slate-600 dark:text-slate-400" : "font-extrabold text-slate-900 dark:text-white"}`}>{email.sender_name}</span>
            <span className="ml-auto shrink-0 text-xs font-medium text-slate-400">{formatDate(email.date)}</span>
          </div>
          <div className={`truncate text-sm ${email.is_read ? "" : "font-bold text-slate-900 dark:text-slate-100"}`}>{email.subject}</div>
          <div className="truncate text-sm text-slate-500">{email.preview}</div>
          {showReason && c && (
            <p className="mt-1.5 line-clamp-2 text-xs leading-relaxed text-slate-500 dark:text-slate-400">
              <span className="font-bold text-slate-700 dark:text-slate-300">Why: </span>{c.reason}
            </p>
          )}
          <div className="mt-2 flex flex-wrap items-center gap-2">
            {c && <PriorityBadge priority={priority} />}
            <span className="chip border-slate-200 bg-white text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300">{c?.category ?? email.dataset_category}</span>
            {c && <ScoreMeter score={c.relevance_score} priority={priority} />}
          </div>
        </div>
      </Link>
    </li>
  );
}
