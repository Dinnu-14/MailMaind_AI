import axios, { AxiosError } from "axios";
import type {
  ChatMessage, ChatReply, EmailDetail, EmailList, EmailQuery, GoogleAuthStatus,
  Health, MLMetrics, MLPredictResult, Preferences, Profile, Stats,
} from "../types";

// Determine API base URL:
// In production on Vercel:
// - If VITE_API_BASE_URL or VITE_API_URL is specified, use that domain (e.g. separate backend deployment).
// - If not specified, default to "" (relative URL /api/...), matching same-domain serverless Vercel deployment.
// In development:
// - Default to http://localhost:8000
const rawBase = (import.meta.env.VITE_API_BASE_URL || import.meta.env.VITE_API_URL) as string | undefined;
const baseURL = rawBase !== undefined
  ? rawBase.replace(/\/$/, "")
  : (import.meta.env.PROD ? "" : "http://localhost:8000");

const http = axios.create({ baseURL, timeout: 60000 });

export function errorMessage(err: unknown): string {
  const e = err as AxiosError<{ detail?: unknown }>;
  if (e.response) {
    const d = e.response.data?.detail;
    if (typeof d === "string") return d;
    return `Request failed (HTTP ${e.response.status}).`;
  }
  if (e.code === "ECONNABORTED") return "The server took too long to respond. If it just woke up, try again in a few seconds.";
  return `Cannot reach the backend API${baseURL ? ` at ${baseURL}` : ""}. Please verify deployment and environment variables.`;
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
  classify: (engine: "auto" | "rules" | "gemini" | "ml" = "auto") =>
    http.post<{ engine: string; error?: string | null; important: number; total: number }>("/api/classify", { engine }).then((r) => r.data),
  stats: () => http.get<Stats>("/api/dashboard/stats").then((r) => r.data),
  feedback: (email_id: number, is_correct: boolean, expected_important?: boolean) =>
    http.post("/api/feedback", { email_id, is_correct, expected_important }).then((r) => r.data),
  profiles: () => http.get<Profile[]>("/api/profiles").then((r) => r.data),
  switchProfile: (key: Profile["key"], reset_conversation = false) =>
    http.post<Profile>("/api/profiles/switch", { key, reset_conversation }).then((r) => r.data),

  // Machine Learning Endpoints
  mlPredict: (text: string, subject: string = "") =>
    http.post<MLPredictResult>("/api/ml/predict", { text, subject }).then((r) => r.data),
  mlMetrics: () => http.get<MLMetrics>("/api/ml/metrics").then((r) => r.data),

  // Google OAuth & Gmail Sync
  googleAuthUrl: () => http.get<{ url: string; configured: boolean }>("/api/auth/google/url").then((r) => r.data),
  googleAuthStatus: () => http.get<GoogleAuthStatus>("/api/auth/google/status").then((r) => r.data),
  googleAuthDisconnect: () => http.post<{ status: string }>("/api/auth/google/disconnect").then((r) => r.data),
  gmailSync: () => http.post<{ status: string; synced: number; total_checked: number; last_synced_at?: string }>("/api/gmail/sync").then((r) => r.data),
};
