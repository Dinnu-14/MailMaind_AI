# External Background Worker & Gmail Continuous Synchronization Guide

## 1. Why Serverless Cannot Run Infinite Background Loops
Vercel Serverless Functions are designed for short HTTP requests (10s - 60s timeout). When an HTTP response is sent, the serverless container is frozen or terminated.
* Never run `while True: sleep(60); sync_emails()` inside a FastAPI background thread on Vercel.
* Doing so will cause the function to hit the execution timeout or get abruptly terminated.

---

## 2. Recommended Production Architecture for Continuous Sync

### Option A: Vercel Cron Jobs (Easiest)
Vercel provides native Cron Jobs that invoke your serverless API on a schedule.

In `vercel.json`, add:
```json
{
  "crons": [
    {
      "path": "/api/gmail/sync",
      "schedule": "*/15 * * * *"
    }
  ]
}
```
* Every 15 minutes, Vercel triggers `POST /api/gmail/sync`.
* The serverless function wakes up, fetches the latest 25 emails, stores and classifies them in PostgreSQL, and finishes in ~2-3 seconds.

---

### Option B: GitHub Actions Scheduled Cron (100% Free)
Create `.github/workflows/gmail-sync.yml`:
```yaml
name: Gmail Periodic Sync
on:
  schedule:
    - cron: '*/30 * * * *'  # Runs every 30 minutes
  workflow_dispatch:

jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger MailMind Sync Endpoint
        run: |
          curl -X POST "https://your-domain.vercel.app/api/gmail/sync"
```

---

### Option C: Standalone Worker Service (Render / Railway)
If you require near real-time email streaming or webhooks, deploy a standalone Python worker on Render or Railway running:
```bash
python -m backend.worker
```
The worker reads from the shared Neon/Supabase PostgreSQL database and keeps tokens refreshed while the main frontend and API remain hosted on Vercel.

