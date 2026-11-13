# Vercel Deployment Architecture & Production Guide

This guide details how **MailMind AI** is structured and deployed onto Vercel.

---

## 1. Why Did `frontend-p2u5.vercel.app` Have an Error?

When deploying only the `frontend/` folder to Vercel, the following errors occur:
1. **Missing Backend API**: Vercel deployed only the static React Vite bundle. The FastAPI backend and Scikit-Learn serverless endpoints were not part of that deployment.
2. **Localhost Fallback Blocked in Production**: The frontend code defaulted to `http://localhost:8000`. When loaded in a browser over HTTPS (`https://frontend-p2u5.vercel.app`), the browser blocks calls to `http://localhost:8000` due to **Mixed Content Security Restrictions** and connection timeouts.
3. **Missing Environment Variables**: `DATABASE_URL`, `LLM_API_KEY`, and `VITE_API_BASE_URL` were not configured.

---

## 2. Supported Deployment Architectures

You have two clean options on Vercel:

### Option A: Unified Full-Stack Vercel Deployment (RECOMMENDED)
Both the React frontend and the Python serverless API are hosted together under **one single domain** (e.g. `https://mailmind-ai.vercel.app`).

* **Frontend**: Served from `/`
* **Backend API**: Handled by Vercel Python Serverless Function (`api/index.py`) at `/api/*`
* **Swagger Docs**: Available at `/docs`
* **Benefits**:
  - No CORS configuration needed.
  - No Mixed Content errors.
  - Zero localhost URLs in production.
  - One single project to manage in Vercel.

**Root Configuration (`vercel.json`)**:
```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "buildCommand": "cd frontend && npm install && npm run build",
  "outputDirectory": "frontend/dist",
  "functions": {
    "api/index.py": {
      "memory": 1024,
      "maxDuration": 30
    }
  },
  "rewrites": [
    { "source": "/api/(.*)", "destination": "/api/index.py" },
    { "source": "/docs", "destination": "/api/index.py" },
    { "source": "/openapi.json", "destination": "/api/index.py" },
    { "source": "/((?!api/|docs|openapi.json).*)", "destination": "/index.html" }
  ]
}
```

---

### Option B: Split Deployments (Frontend Project + Backend API Project)
If you keep your existing `frontend-p2u5.vercel.app` frontend:

1. **Deploy Backend API on Vercel**:
   - Create a second project on Vercel importing this repository.
   - Set the root directory to repository root (or `/backend`).
   - Add environment variable `DATABASE_URL` pointing to hosted PostgreSQL.
   - Note the backend deployment URL (e.g., `https://mailmind-backend.vercel.app`).

2. **Configure Frontend**:
   - In your frontend project (`frontend-p2u5`), go to **Settings > Environment Variables**.
   - Add:
     ```
     VITE_API_BASE_URL = https://mailmind-backend.vercel.app
     ```
   - Go to **Deployments** and click **Redeploy**.
   - In backend project settings, set `CORS_ORIGINS = https://frontend-p2u5.vercel.app`.

---

## 3. Serverless Lifecycle & Limitations

| Constraint | Vercel Serverless Rule | How MailMind AI Handles It |
|---|---|---|
| **Execution Time** | Max 10-60s per invocation | All email classification, search, and chatbot endpoints execute in < 200ms. |
| **Filesystem** | Ephemeral, read-only except `/tmp` | Persistent data is stored exclusively in hosted PostgreSQL (Neon / Supabase). Never in SQLite files. |
| **Connection Limits** | Lambdas open concurrent connections | SQLAlchemy uses `poolclass=NullPool` and `pool_pre_ping=True` so connections close cleanly. |
| **ML Models** | Bundle size limit (< 250MB) | Uses lightweight TF-IDF and Multinomial Naive Bayes artifacts (< 200KB total) loaded into memory once during module import. |
| **Background Sync** | Background threads terminate on HTTP return | Gmail sync is triggered on-demand via `/api/gmail/sync` or via external scheduled cron workers. |

