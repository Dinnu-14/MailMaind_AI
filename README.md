# MailMind AI – Personalized Intelligent Email Classification and Management System

MailMind AI is a full-stack, AI-powered email intelligence platform. It features an interactive onboarding & continuous preference chatbot, ML category classification (Scikit-Learn TF-IDF + Multinomial Naive Bayes), Google Gemini LLM reasoning, Gmail OAuth 2.0 integration, and a modern React Vite dashboard.

---

## 🚀 Live Vercel Deployment Architecture

MailMind AI is optimized for **Vercel Serverless Hosting**:

- **Frontend**: React 18, Vite, TypeScript, Tailwind CSS, Lucide Icons, React Router SPA.
- **Backend**: FastAPI running inside Vercel-compatible Python Serverless Functions.
- **Database**: Hosted PostgreSQL (Neon / Supabase) via SQLAlchemy serverless connection management (`NullPool`).
- **AI/ML**: Pretrained Scikit-Learn TF-IDF vectorizer + Multinomial Naive Bayes classifier (< 200KB) + hybrid personalized priority scoring + Google Gemini API.
- **Integrations**: Google OAuth 2.0 for Gmail with secure token storage.

---

## 🛠️ Step-by-Step Vercel Deployment Guide (Windows)

### Step 1: Initialize Git and Commit All Files
Open PowerShell in this project folder (`d:\Mailmaind_AI_project`):

```powershell
# 1. Initialize git repository
git init

# 2. Add all deployment files
git add .

# 3. Create initial commit
git commit -m "MailMind AI - Complete Vercel deployment ready"

# 4. Set default branch to main
git branch -M main
```

### Step 2: Push to GitHub
1. Create a new empty repository on [GitHub](https://github.com/new) named `mailmind-ai`.
2. Run the push commands:

```powershell
git remote add origin https://github.com/<YOUR_GITHUB_USERNAME>/mailmind-ai.git
git push -u origin main
```

---

### Step 3: Create a Free Hosted PostgreSQL Database
1. Go to [https://neon.tech](https://neon.tech) and create a free project named `mailmind-db`.
2. Under **Connection Details**, ensure **Pooled connection** is checked.
3. Copy the `postgresql://...` connection string.

---

### Step 4: Import and Deploy on Vercel
1. Go to [https://vercel.com/new](https://vercel.com/new).
2. Connect your GitHub account and click **Import** on your `mailmind-ai` repository.
3. **Project Settings**:
   - **Framework Preset**: Other (or Vite)
   - **Root Directory**: `./` (leave as repository root so Vercel deploys both frontend and `api/` serverless functions together)
   - **Build Command**: `cd frontend && npm install && npm run build` (handled automatically by `vercel.json`)
   - **Output Directory**: `frontend/dist`
4. **Environment Variables**:
   Click **Environment Variables** and add:

   | Variable Name | Value / Description | Required? |
   |---|---|---|
   | `DATABASE_URL` | Your Neon or Supabase PostgreSQL connection string | **Yes** |
   | `SECRET_KEY` | Any random 32-character string | **Yes** |
   | `ENVIRONMENT` | `production` | **Yes** |
   | `LLM_API_KEY` | Your Google Gemini API key from [AI Studio](https://aistudio.google.com/apikey) | Recommended |
   | `GOOGLE_CLIENT_ID` | Google Cloud OAuth Client ID | Optional (for Gmail sync) |
   | `GOOGLE_CLIENT_SECRET`| Google Cloud OAuth Client Secret | Optional (for Gmail sync) |
   | `GOOGLE_REDIRECT_URI` | `https://your-domain.vercel.app/api/auth/google/callback` | Optional |

5. Click **Deploy**.

---

## 🔍 Fixing the `frontend-p2u5.vercel.app` Error

If you previously deployed only the `frontend/` folder, you likely saw:
> `Cannot reach the backend at http://localhost:8000` or a CORS / Mixed Content failure.

### Why this happens:
1. When only the `frontend/` folder is selected as the Vercel root directory, Vercel only deploys the static files. The Python backend is not deployed.
2. In production, browsers block requests from an HTTPS website (`https://frontend-p2u5.vercel.app`) to an insecure `http://localhost:8000` address.

### The Fix:
- **Solution (Recommended)**: In Vercel Project Settings, change **Root Directory** from `frontend` to `./` (root). Redeploy the project. Vercel will build both the frontend and the Python serverless API under the same domain.
- **Alternative**: If you want to keep `frontend-p2u5` separate:
  1. Create a second Vercel project for the backend API from this repository root.
  2. In your `frontend-p2u5` project settings, add:
     `VITE_API_BASE_URL = https://<your-deployed-backend>.vercel.app`
  3. Redeploy `frontend-p2u5`.

---

## 🧪 Local Development (Windows)

```powershell
# 1. Start Backend API
& "D:\anaconda\python.exe" -m uvicorn app.main:app --app-dir backend --reload --port 8000

# 2. Start Frontend (in a second PowerShell terminal)
cd frontend
npm run dev
```

Visit [http://localhost:5173](http://localhost:5173). The Swagger documentation is at [http://localhost:8000/docs](http://localhost:8000/docs).

---

## 📋 Production Verification Checklist

- [x] Frontend builds cleanly without TypeScript errors (`npm run build`).
- [x] Vercel serverless entrypoint `api/index.py` configured with clean path resolution.
- [x] Database uses hosted PostgreSQL connection with `NullPool` serverless compatibility.
- [x] Scikit-Learn TF-IDF model loads into memory as a singleton without retraining on invocations.
- [x] Single-origin routing configured in `vercel.json` to prevent Mixed Content & CORS errors.
- [x] SPA client routing rewrites configured to avoid 404 on page refresh.
- [x] Google OAuth 2.0 endpoints for Gmail integration ready for production callback.
