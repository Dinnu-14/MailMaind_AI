import { ArrowLeft, CalendarClock, CheckCircle2, Info, ListChecks, MessageSquareQuote, ThumbsDown, ThumbsUp } from "lucide-react";
import { ReactNode, useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { EngineTag, ErrorBanner, formatDate, initials, PriorityBadge, ScoreMeter, Spinner } from "../components/ui";
import { useApp } from "../context/AppContext";
import { api, errorMessage } from "../services/api";
import type { EmailDetail as Detail } from "../types";

function Block({ icon, title, children }: { icon: ReactNode; title: string; children: ReactNode }) {
  return (
    <div>
      <h3 className="flex items-center gap-2 text-xs font-extrabold text-slate-500">{icon} {title}</h3>
      <div className="mt-1.5 text-sm leading-relaxed">{children}</div>
    </div>
  );
}

export default function EmailDetail() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { refresh, notify, version } = useApp();
  const [email, setEmail] = useState<Detail>();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setEmail(undefined); setError(null);
    api.email(Number(id)).then((e) => { setEmail(e); void refresh(); }).catch((e) => setError(errorMessage(e)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  // if preferences changed while viewing, refetch the classification
  useEffect(() => {
    if (email && version > 0) api.email(email.id).then(setEmail).catch(() => undefined);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [version]);

  const back = () => (window.history.length > 1 ? navigate(-1) : navigate("/all"));
  if (error) return <><button className="btn-ghost mb-3" onClick={back}><ArrowLeft size={16} /> Back</button><ErrorBanner message={error} /></>;
  if (!email) return <Spinner label="Opening email" />;

  const c = email.classification;
  const s = email.summary;
  const none = (t: string) => t.toLowerCase().startsWith("none mentioned");

  const feedback = async (correct: boolean) => {
    try {
      await api.feedback(email.id, correct, correct ? undefined : !c?.is_important);
      await refresh();
      setEmail(await api.email(email.id));
      notify(correct ? "Thanks, noted as correct." : `Moved to ${c?.is_important ? "Other" : "your Priority Inbox"}.`);
    } catch (e) { notify(errorMessage(e), "error"); }
  };

  return (
    <>
      <button className="btn-ghost mb-3 -ml-2" onClick={back}><ArrowLeft size={16} /> Back</button>
      <div className="grid gap-5 lg:grid-cols-5">
        <article className="card p-5 sm:p-7 lg:col-span-3">
          <h1 className="text-xl font-extrabold leading-snug sm:text-2xl">{email.subject}</h1>
          <div className="mt-4 flex items-center gap-3 border-b border-slate-100 pb-4 dark:border-slate-800">
            <div className="flex h-11 w-11 items-center justify-center rounded-full bg-brand-100 text-sm font-bold text-brand-700 dark:bg-brand-900/50 dark:text-brand-200">{initials(email.sender_name)}</div>
            <div className="min-w-0">
              <div className="truncate text-sm font-bold">{email.sender_name}</div>
              <div className="truncate text-xs text-slate-500">&lt;{email.sender_email}&gt;</div>
            </div>
            <time className="ml-auto text-right text-xs text-slate-500" dateTime={email.date}>{formatDate(email.date, true)}</time>
          </div>
          <div className="mt-5 max-w-prose whitespace-pre-wrap text-[15px] leading-7 text-slate-700 dark:text-slate-300">{email.body}</div>
        </article>

        <aside className="space-y-5 lg:col-span-2">
          {c && (
            <section className="card p-5">
              <div className="flex flex-wrap items-center gap-2">
                <PriorityBadge priority={c.priority} />
                <span className="chip border-slate-200 bg-white text-slate-600 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300">{c.category}</span>
                <span className="ml-auto"><EngineTag engine={c.engine} /></span>
              </div>
              <div className="mt-4"><div className="mb-1 text-xs font-extrabold text-slate-500">Relevance score</div><ScoreMeter score={c.relevance_score} priority={c.priority} wide /></div>
              <div className="mt-4">
                <div className="text-xs font-extrabold text-slate-500">Why the AI classified it this way</div>
                <p className="mt-1 text-sm leading-relaxed">{c.reason}</p>
                <p className="mt-2 text-xs text-slate-500">{c.is_important ? "Shown in Priority Inbox." : "Only shown in All Inbox."}</p>
              </div>
              <div className="mt-4 flex flex-wrap gap-2 border-t border-slate-100 pt-4 dark:border-slate-800">
                <button className="btn-outline !py-1.5 text-xs" onClick={() => feedback(true)}><ThumbsUp size={14} /> Looks right</button>
                <button className="btn-outline !py-1.5 text-xs" onClick={() => feedback(false)}><ThumbsDown size={14} /> {c.is_important ? "Not important to me" : "This is important"}</button>
              </div>
            </section>
          )}
          <section className="card space-y-4 p-5">
            <div className="flex items-center justify-between"><h2 className="text-sm font-extrabold">AI summary</h2><EngineTag engine={s.engine} /></div>
            <Block icon={<Info size={14} />} title="Main purpose">{s.purpose}</Block>
            {s.important_information.length > 0 && (
              <Block icon={<CheckCircle2 size={14} />} title="Important information">
                <ul className="list-disc space-y-1 pl-5">{s.important_information.map((x, i) => <li key={i}>{x}</li>)}</ul>
              </Block>
            )}
            <Block icon={<CalendarClock size={14} />} title="Deadlines">
              {s.deadlines.length ? <div className="flex flex-wrap gap-1.5">{s.deadlines.map((d, i) => <span key={i} className="chip border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-900 dark:bg-amber-950/40 dark:text-amber-200">{d}</span>)}</div> : <span className="text-slate-500">None mentioned in the email.</span>}
            </Block>
            <Block icon={<ListChecks size={14} />} title="Required action"><span className={none(s.required_action) ? "text-slate-500" : ""}>{s.required_action}</span></Block>
            <Block icon={<MessageSquareQuote size={14} />} title="Sender's request"><span className={none(s.sender_request) ? "text-slate-500" : ""}>{s.sender_request}</span></Block>
          </section>
        </aside>
      </div>
    </>
  );
}
