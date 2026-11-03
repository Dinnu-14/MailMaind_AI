import { useCallback, useEffect, useState } from "react";
import { useApp } from "../context/AppContext";
import { api, errorMessage } from "../services/api";
import type { EmailList, EmailQuery } from "../types";

export function useEmails(mode: "priority" | "all", query: EmailQuery) {
  const { version } = useApp();
  const [data, setData] = useState<EmailList>();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const key = JSON.stringify(query);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const q = JSON.parse(key) as EmailQuery;
      setData(await (mode === "priority" ? api.priority(q) : api.emails(q)));
      setError(null);
    } catch (e) {
      setError(errorMessage(e));
    } finally {
      setLoading(false);
    }
  }, [mode, key]);

  useEffect(() => { void load(); }, [load, version]);
  return { data, loading, error, reload: load };
}
