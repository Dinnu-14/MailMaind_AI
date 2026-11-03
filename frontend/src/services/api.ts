import axios, { AxiosError } from "axios";
import type {
  ChatMessage, ChatReply, EmailDetail, EmailList, EmailQuery, Health, Preferences, Profile, Stats,
} from "../types";

const baseURL = (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, "") || "http://localhost:8000";

const http = axios.create({ baseURL, timeout: 60000 });

export function errorMessage(err: unknown): string {
  const e = err as AxiosError<{ detail?: unknown }>;
  if (e.response) {
    const d = e.response.data?.detail;
    if (typeof d === "string") return d;
    return `Request failed (HTTP ${e.response.status}).`;
  }
  if (e.code === "ECONNABORTED") return "The server took too long to respond. If it just woke up, try again in a few seconds.";
  return `Cannot reach the backend at ${baseURL}. Start it, or check VITE_API_URL.`;
}

const clean = (o: Record<string, unknown>) =>
  Object.fromEntries(Object.entries(o).filter(([, v]) => v !== undefined && v !== "" && v !== false));

export const api = {
  baseURL,
  health: () => http.get<Health>("/api/health").then((r) => r.data),
  emails: (p: EmailQuery = {}) => http.get<EmailList>("/api/emails", { params: clean({ ...p }) }).then((r) => r.data),
  priority: (p: EmailQuery = {}) =>
    http.get<EmailList>("/api/emails/priority", { params: clean({ ...p }) }).then((r) => r.data),
  email: (id: number) => http.get<EmailDetail>(`/api/emails/${id}`).then((r) => r.data),
  reload: () => http.post<{ loaded: number }>("/api/emails/reload").then((r) => r.data),
  categories: () => http.get<string[]>("/api/categories").then((r) => r.data),
  chat: (message: string) => http.post<ChatReply>("/api/chat", { message }).then((r) => r.data),
  history: () => http.get<ChatMessage[]>("/api/chat/history").then((r) => r.data),
  resetChat: () => http.post<ChatMessage[]>("/api/chat/reset").then((r) => r.data),
  preferences: () => http.get<Preferences>("/api/preferences").then((r) => r.data),
  savePreferences: (p: Partial<Pick<Preferences, "profession" | "categories" | "boosted_categories" | "excluded_categories" | "keywords">>) =>
    http.put<Preferences>("/api/preferences", p).then((r) => r.data),
  classify: (engine: "auto" | "rules" | "gemini" = "auto") =>
    http.post<{ engine: string; error?: string | null; important: number; total: number }>("/api/classify", { engine }).then((r) => r.data),
  stats: () => http.get<Stats>("/api/dashboard/stats").then((r) => r.data),
  feedback: (email_id: number, is_correct: boolean, expected_important?: boolean) =>
    http.post("/api/feedback", { email_id, is_correct, expected_important }).then((r) => r.data),
  profiles: () => http.get<Profile[]>("/api/profiles").then((r) => r.data),
  switchProfile: (key: Profile["key"], reset_conversation = false) =>
    http.post<Profile>("/api/profiles/switch", { key, reset_conversation }).then((r) => r.data),
};
