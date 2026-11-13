# Google OAuth 2.0 & Gmail Integration Setup Guide

Follow these exact steps to enable Google OAuth and Gmail synchronization in MailMind AI.

---

## Step 1: Open Google Cloud Console
1. Go to [https://console.cloud.google.com](https://console.cloud.google.com).
2. Sign in with your Google account.
3. Click the Project dropdown at the top and click **New Project**.
4. Name your project: `MailMind-AI` and click **Create**.

---

## Step 2: Enable the Gmail API
1. In the left navigation menu, go to **APIs & Services > Library**.
2. Search for `Gmail API`.
3. Click on **Gmail API** and click **Enable**.

---

## Step 3: Configure the OAuth Consent Screen
1. In the left navigation menu, click **APIs & Services > OAuth consent screen**.
2. Select **External** and click **Create**.
3. Fill in the required fields:
   - **App name**: `MailMind AI`
   - **User support email**: Your email address
   - **Developer contact information**: Your email address
4. Click **Save and Continue**.
5. On the **Scopes** page:
   - Click **Add or Remove Scopes**.
   - Search for and add:
     - `https://www.googleapis.com/auth/gmail.readonly`
     - `https://www.googleapis.com/auth/userinfo.email`
     - `https://www.googleapis.com/auth/userinfo.profile`
   - Click **Update** and then **Save and Continue**.
6. On the **Test Users** page:
   - Click **Add Users**.
   - Add your own Google email address (the one you want to test connecting).
   - Click **Save and Continue**.

---

## Step 4: Create OAuth 2.0 Client ID Credentials
1. In the left navigation menu, click **APIs & Services > Credentials**.
2. Click **+ Create Credentials** at the top, and select **OAuth client ID**.
3. Choose:
   - **Application type**: `Web application`
   - **Name**: `MailMind AI Web Client`
4. **Authorized JavaScript origins**:
   - Add: `https://your-domain.vercel.app`
   - For local development: `http://localhost:5173`
5. **Authorized redirect URIs**:
   - Add production callback:
     ```
     https://your-domain.vercel.app/api/auth/google/callback
     ```
   - For local development:
     ```
     http://localhost:8000/api/auth/google/callback
     ```
6. Click **Create**.
7. Google will show you your **Client ID** and **Client Secret**. Copy both values immediately.

---

## Step 5: Configure Environment Variables in Vercel
In your Vercel Project Dashboard (**Settings > Environment Variables**), add:

```env
GOOGLE_CLIENT_ID = <your-google-client-id>.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET = <your-google-client-secret>
GOOGLE_REDIRECT_URI = https://your-domain.vercel.app/api/auth/google/callback
```

