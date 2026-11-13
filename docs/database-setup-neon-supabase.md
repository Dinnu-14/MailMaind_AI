# Hosted PostgreSQL Database Setup Guide (Neon & Supabase)

Vercel functions run in an ephemeral serverless environment. A local SQLite file (`app.db`) will be wiped every time a serverless container restarts or scales down.

**You must use a persistent hosted PostgreSQL database in production.**

---

## Provider Option 1: Neon Serverless Postgres (Recommended)

Neon provides free, instant, serverless PostgreSQL with built-in connection pooling.

### Step 1: Create a Neon Database
1. Go to [https://neon.tech](https://neon.tech) and sign up for free (using GitHub or Google).
2. Click **Create Project**.
3. Name your project: `mailmind-ai-db`.
4. Select the region closest to your Vercel deployment region (e.g., `AWS us-east-1` or `AWS us-east-2`).
5. Click **Create Project**.

### Step 2: Copy Connection String
1. In your Neon dashboard, under **Connection Details**, ensure **Pooled connection** is checked (recommended for serverless).
2. Copy the connection string:
   ```
   postgresql://neondb_owner:npg_xyz...@ep-cool-dawn-12345-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```

### Step 3: Add to Vercel
1. Open your Vercel Project Dashboard.
2. Go to **Settings > Environment Variables**.
3. Add key: `DATABASE_URL` with your connection string as value.

---

## Provider Option 2: Supabase

### Step 1: Create a Supabase Project
1. Go to [https://supabase.com](https://supabase.com) and create a free account.
2. Click **New Project** and name it `mailmind-ai`.
3. Set a strong database password (keep this safe).
4. Select your preferred region.

### Step 2: Copy Connection String (Transaction Pooler)
1. Go to **Project Settings > Database > Connection string**.
2. Select the **URI** tab and choose **Mode: Transaction** (port 6543) for serverless compatibility.
3. Replace `[YOUR-PASSWORD]` with your actual password.
4. Copy the connection string:
   ```
   postgresql://postgres.yourprojectref:yourpassword@aws-0-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require
   ```

### Step 3: Add to Vercel
1. In Vercel Project Settings > Environment Variables, add:
   ```
   DATABASE_URL = postgresql://postgres.yourprojectref:...
   ```

---

## Automatic Table Initialization

MailMind AI automatically initializes all required tables and seeds default user profiles on first startup:
- `users`
- `user_profiles`
- `user_preferences`
- `emails`
- `email_classifications`
- `gmail_tokens`
- `conversations`
- `chat_messages`
- `feedback`
- `activity`

No manual SQL file execution is required!

