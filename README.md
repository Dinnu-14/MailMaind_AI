# AI Smart Email Assistant

A personalized email classification demo. You chat with an AI assistant about who you are and what emails matter to you. It then splits a fixed set of 44 sample emails into a **Priority Inbox** (relevant to you) and an **All Inbox** (everything, never deleted). Switch profile or change your mind in chat and the *same emails* are re-ranked instantly.

- **Frontend:** React, Vite, TypeScript, Tailwind CSS, React Router, Axios, Lucide
- **Backend:** FastAPI, Pydantic, SQLAlchemy, SQLite (Postgres optional)
- **AI:** Gemini API when `GEMINI_API_KEY` is set, otherwise a built-in rule-based engine (demo mode). Every classification, summary and chat reply is labelled with the engine that produced it. If Gemini fails, the app says so and falls back. It never pretends a call succeeded.

## Features

| Area | What it does |
|---|---|
| Onboarding chatbot | Asks profession, then interests, then a follow-up; extracts categories and keywords; saves everything |
| Continuous chatbot | "Show only college emails", "Include internships", "Show Data Engineering jobs", "Stop prioritizing shopping emails", "Find interview invitations" and more; reclassifies immediately |
| Classification | Per email: `is_important`, category, priority (High / Medium / Low / Other), relevance score 0-100, plain-language reason; stored in the database |
| Inboxes | Priority Inbox and All Inbox with category, priority, status and sort filters, plus natural-language search (`unread interviews`, `from placement`) |
| Email detail | Full body, AI summary (purpose, key info, deadlines, action, request), category, priority, score, reason, feedback buttons |
| Profiles | Student, Businessperson, Job Seeker, Working Professional, Custom; each keeps its own preferences and chat |
| Dashboard | Totals, important, other, unread, priority breakdown, categories, engine status, recent activity |
| Extras | Dark mode, responsive layout, Settings page for manual preference edits, Categories page, feedback that overrides the AI |

## Run locally

Requires Python 3.10+ and Node 18+.

```bash
# 1. Backend  (http://localhost:8000, API docs at /docs)
cd backend
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                   # optional: add GEMINI_API_KEY
uvicorn app.main:app --reload --port 8000

# 2. Frontend  (http://localhost:5173), in a second terminal
cd frontend
npm install
cp .env.example .env                                   # VITE_API_URL=http://localhost:8000
npm run dev
```

The database and sample emails are created automatically on first start (`backend/data/app.db`). Delete that file to reset the demo.

### Tests and build

```bash
cd backend && pip install pytest && pytest -q      # 17 API tests, run in demo mode
cd frontend && npm run build                       # type-check + production build
```

## Gemini configuration

1. Create a key at https://aistudio.google.com/apikey
2. Put it in `backend/.env`: `GEMINI_API_KEY=your-key` (optionally `GEMINI_MODEL`, default `gemini-2.5-flash`)
3. Restart the backend. The top banner disappears, and results are tagged **Gemini** instead of **Local rules**.

The key lives only on the backend; the frontend never sees it. Settings has buttons to reclassify with a chosen engine, and forcing Gemini without a key returns a clear error.

## Deploy

See [docs/deployment-guide.md](docs/deployment-guide.md) for Vercel (frontend), Render (backend) and the SQLite persistence limitation.

## GitHub

```bash
git init
git add .
git commit -m "AI Smart Email Assistant"
git branch -M main
git remote add origin https://github.com/<your-username>/ai-smart-email-assistant.git
git push -u origin main
```

`.env` files are git-ignored. Only the `.env.example` files are committed.

## Docs

- [Architecture](docs/architecture.md)
- [Project documentation and demo guide](docs/project-documentation.md)
- [Deployment guide](docs/deployment-guide.md)
