# Deployment guide

Frontend on **Vercel**, backend on **Render**. Deploy the backend first so you have its URL.

## 1. Push to GitHub
Follow the commands in the README. Confirm no `.env` file was committed.

## 2. Backend on Render
**Option A: Blueprint (recommended).** Render dashboard > New > Blueprint > pick the repo. It reads `render.yaml`, creates the web service (root `backend`) and a Postgres database, and wires `DATABASE_URL`. Then set:
- `CORS_ORIGINS` = your Vercel URL, e.g. `https://my-app.vercel.app` (no trailing slash)
- `GEMINI_API_KEY` = your key (optional; without it the app runs in demo mode)

**Option B: manual.** New > Web Service > repo. Root directory `backend`, build `pip install -r requirements.txt`, start `uvicorn app.main:app --host 0.0.0.0 --port $PORT`, health check `/api/health`, and add the environment variables above.

Check `https://<service>.onrender.com/api/health`. It should return `"status":"ok"`.

`CORS_ORIGIN_REGEX=https://.*\.vercel\.app` is preset so Vercel preview URLs also work.

## 3. Frontend on Vercel
Vercel > Add New Project > pick the repo.
- Root directory: `frontend`
- Framework: Vite (auto-detected; `vercel.json` is included, with an SPA rewrite so deep links work)
- Environment variable: `VITE_API_URL` = `https://<service>.onrender.com` (no trailing slash)

Deploy, then make sure that exact Vercel URL is in the backend's `CORS_ORIGINS`. `VITE_API_URL` is baked in at build time, so redeploy after changing it.

## Persistence limitation
SQLite is a file on the server's disk. Render's free web services have an **ephemeral filesystem**: the file is wiped on every redeploy and whenever the service restarts (including waking from idle). When that happens the app re-creates and re-seeds the database, so the emails come back but your chat history, preferences and feedback are lost.

Options:
1. **Postgres (recommended for anything beyond a one-off demo).** `render.yaml` provisions one and sets `DATABASE_URL`; the code converts `postgres://` URLs automatically. Render's free Postgres has had an expiry window, so check the current plan terms. Neon or Supabase free Postgres also work: set `DATABASE_URL` to their connection string. I verified the app against SQLite only; the same SQLAlchemy models are used for Postgres, so run through the demo once after deploying.
2. **Render persistent disk** (paid): mount at `/var/data` and set `DATABASE_URL=sqlite:////var/data/app.db`.
3. **Accept it for a short demo.** The app still works, it just starts fresh each time.

## Cold starts
Free Render services sleep after inactivity; the first request can take 30-60 seconds. Open the backend `/api/health` URL a minute before presenting. The UI shows a clear error and a retry button if the server is not ready.
