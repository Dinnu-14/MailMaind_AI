# Architecture

```
React (Vite)  --Axios-->  FastAPI  -->  services  -->  SQLite / Postgres
 pages, context            routes       classifier        users, preferences,
                                        chatbot           emails, classifications,
                                        summarizer        conversations, messages,
                                        search            feedback, activity
                                        gemini (REST)
```

## Backend (`backend/app`)
- `routes/` HTTP layer and validation. `emails.py` (lists, detail, reload), `assistant.py` (chat, preferences, classify, stats, feedback, profiles).
- `schemas/` Pydantic request and response models.
- `models/` SQLAlchemy tables: `UserProfile`, `UserPreference`, `Email`, `EmailClassification` (unique per email and profile), `Conversation`, `ChatMessage`, `Feedback`, `Activity`.
- `services/classifier.py` the core. Loads emails and the active profile's preferences, classifies each one, applies feedback overrides, persists the result.
- `services/chatbot.py` a small state machine (`ask_profession`, `ask_interests`, `ask_followup`, `ready`) fed by an "understanding" step that returns the same structure from either Gemini or a rule-based parser. The rest (preference updates, reclassification, replies) is deterministic, so demo mode behaves like Gemini mode.
- `services/gemini.py` minimal REST client. Raises on every failure so callers can report it honestly.
- `services/lexicon.py` categories, profile presets, keyword topics, chat aliases.

## Classification
1. Infer the email's category from its **content** (the dataset label only breaks ties).
2. Compare with the profile: wanted categories, boosted, excluded, focus keywords (for example "data engineering").
3. Score 0-100 and map to priority: High 80+, Medium 60-79, Low 40-59, Other below 40 (not important).
4. Write a reason that cites the user's preferences.

The Gemini engine receives the same preferences and must return JSON per email; each row is validated (known category, integer score) and any email Gemini fails to return is filled by the rules. The result records which engine produced it.

Preferences carry a `version`. Any change bumps it, and any request that finds stale classifications reclassifies once (guarded by a lock so parallel requests cannot race).

## Frontend (`frontend/src`)
- `context/AppContext` holds profiles, preferences, stats, theme, toasts, and a `version` counter that tells lists to reload after preferences change.
- `services/api.ts` is the only place that talks to the backend; the base URL comes from `VITE_API_URL`.
- `pages/` Dashboard, Inbox (priority and all), EmailDetail, Assistant, Categories, Settings. `components/ChatPanel` is shared by the Assistant page and the slide-over chat available on every page.

## Honesty rules
No fake AI success. Engine badges show "Gemini" or "Local rules" for each classification, summary and reply. Gemini failures surface as a notice and fall back; a short cool-down avoids hammering a failing API.
