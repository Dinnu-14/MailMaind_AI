export type Priority = "High" | "Medium" | "Low" | "Other";

export interface Classification {
  email_id: number;
  is_important: boolean;
  category: string;
  priority: Priority;
  relevance_score: number;
  reason: string;
  engine: "rules" | "gemini";
}

export interface EmailItem {
  id: number;
  sender_name: string;
  sender_email: string;
  subject: string;
  preview: string;
  date: string;
  dataset_category: string;
  is_read: boolean;
  classification: Classification | null;
}

export interface EmailList {
  total: number;
  items: EmailItem[];
  query_description: string;
}

export interface Summary {
  purpose: string;
  important_information: string[];
  deadlines: string[];
  required_action: string;
  sender_request: string;
  engine: "rules" | "gemini";
}

export interface EmailDetail extends EmailItem {
  body: string;
  summary: Summary;
}

export interface ChatMessage {
  id: number;
  role: "user" | "assistant";
  content: string;
  engine?: string | null;
  created_at: string;
}

export interface ChatReply {
  reply: string;
  engine: string;
  preferences_changed: boolean;
  classification?: Record<string, unknown> | null;
  action?: { type: "search"; query: string; count: number } | null;
  ai_error?: string | null;
}

export interface Preferences {
  profile_key: string;
  profile_name: string;
  profession: string;
  categories: string[];
  boosted_categories: string[];
  excluded_categories: string[];
  keywords: string[];
  onboarded: boolean;
  last_engine: string;
  last_error?: string | null;
  classified_at?: string | null;
}

export interface Profile {
  key: "student" | "businessperson" | "job_seeker" | "professional" | "custom";
  name: string;
  description: string;
  icon: string;
  is_active: boolean;
}

export interface Stats {
  profile: { key: string; name: string };
  total: number;
  important: number;
  other: number;
  unread: number;
  unread_important: number;
  by_priority: Record<Priority, number>;
  by_category: Record<string, number>;
  engine: string;
  engine_error?: string | null;
  gemini_configured: boolean;
  onboarded: boolean;
  recent_activity: { kind: string; text: string; created_at: string }[];
}

export interface Health {
  status: string;
  gemini_configured: boolean;
  mode: string;
  gemini_last_error?: string | null;
}

export interface EmailQuery {
  q?: string;
  category?: string;
  priority?: string;
  important?: boolean;
  unread?: boolean;
  sort?: "date_desc" | "date_asc" | "score_desc";
}
