import { Bot, RotateCcw, Send } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useApp } from "../context/AppContext";
import { api, errorMessage } from "../services/api";
import type { ChatMessage } from "../types";
import { EngineTag } from "./ui";

const SUGGESTIONS = [
  "Show only college emails", "Prioritize placement notifications", "Include internships",
  "Show Data Engineering jobs", "Stop prioritizing shopping emails", "Show business proposals",
  "Find interview invitations",
];

export default function ChatPanel({ onNavigate }: { onNavigate?: () => void }) {
  const { activeProfile, refresh, notify, prefs } = useApp();
  const navigate = useNavigate();
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [notice, setNotice] = useState<string | null>(null);
  const endRef = useRef<HTMLDivElement>(null);
  const key = activeProfile?.key;

  useEffect(() => {
    setLoading(true);
    api.history().then(setMessages).catch((e) => notify(errorMessage(e), "error")).finally(() => setLoading(false));
  }, [key, notify]);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" }); }, [messages, busy]);

  const send = useCallback(async (text: string) => {
    const t = text.trim();
    if (!t || busy) return;
    setInput(""); setNotice(null); setBusy(true);
    setMessages((m) => [...m, { id: -Date.now(), role: "user", content: t, created_at: new Date().toISOString() }]);
    try {
      const r = await api.chat(t);
      setMessages((m) => [...m, { id: -Date.now() - 1, role: "assistant", content: r.reply, engine: r.engine, created_at: new Date().toISOString() }]);
      if (r.ai_error) setNotice(r.ai_error);
      if (r.preferences_changed) await refresh();
      if (r.action?.type === "search") {
        navigate(`/all?q=${encodeURIComponent(r.action.query)}`);
        onNavigate?.();
      }
    } catch (e) {
      setMessages((m) => [...m, { id: -Date.now() - 2, role: "assistant", content: `Sorry, that failed. ${errorMessage(e)}`, created_at: new Date().toISOString() }]);
    } finally {
      setBusy(false);
    }
  }, [busy, refresh, navigate, onNavigate]);

  const reset = async () => {
    try {
      setMessages(await api.resetChat());
      await refresh();
      notify("Conversation and preferences reset");
    } catch (e) { notify(errorMessage(e), "error"); }
  };

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div className="flex-1 space-y-3 overflow-y-auto px-4 py-4" aria-live="polite">
        {loading && <p className="text-center text-sm text-slate-400">Loading conversation</p>}
        {messages.map((m) => (
          <div key={m.id} className={`flex animate-pop gap-2 ${m.role === "user" ? "justify-end" : ""}`}>
            {m.role === "assistant" && <div className="mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-brand-600 text-white"><Bot size={15} /></div>}
            <div className={`max-w-[85%] rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed ${m.role === "user" ? "rounded-br-md bg-brand-600 text-white" : "rounded-bl-md bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-100"}`}>
              {m.content}
              {m.role === "assistant" && m.engine === "gemini" && <div className="mt-1.5"><EngineTag engine="gemini" /></div>}
            </div>
          </div>
        ))}
        {busy && (
          <div className="flex gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-brand-600 text-white"><Bot size={15} /></div>
            <div className="flex items-center gap-1 rounded-2xl bg-slate-100 px-4 py-3 dark:bg-slate-800" role="status" aria-label="Assistant is typing">
              {[0, 1, 2].map((i) => <span key={i} className="h-1.5 w-1.5 animate-bounce rounded-full bg-slate-400" style={{ animationDelay: `${i * 120}ms` }} />)}
            </div>
          </div>
        )}
        <div ref={endRef} />
      </div>
      {notice && <p className="mx-4 mb-2 rounded-lg bg-amber-50 px-3 py-2 text-xs text-amber-800 dark:bg-amber-950/40 dark:text-amber-200">{notice}</p>}
      <div className="border-t border-slate-100 p-3 dark:border-slate-800">
        <div className="mb-2 flex gap-1.5 overflow-x-auto pb-1">
          {SUGGESTIONS.map((s) => (
            <button key={s} onClick={() => send(s)} disabled={busy}
              className="chip shrink-0 border-slate-200 bg-white text-slate-600 hover:border-brand-300 hover:text-brand-700 disabled:opacity-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-300">{s}</button>
          ))}
        </div>
        <form className="flex items-center gap-2" onSubmit={(e) => { e.preventDefault(); void send(input); }}>
          <input className="field flex-1" value={input} onChange={(e) => setInput(e.target.value)} maxLength={1000}
            placeholder={prefs?.onboarded ? "Tell me what to prioritize" : "Type your answer"} aria-label="Message to the AI assistant" />
          <button className="btn-primary !px-3" disabled={busy || !input.trim()} aria-label="Send message"><Send size={16} /></button>
          <button type="button" className="btn-ghost !px-2.5" onClick={reset} title="Reset conversation and preferences" aria-label="Reset conversation"><RotateCcw size={16} /></button>
        </form>
      </div>
    </div>
  );
}
