# 🚀 Deploying SecureFile to Vercel

This guide walks you through deploying the **Secure File Management System** to **Vercel** with Supabase and Groq AI.

---

## 📋 Prerequisites
1. A **[Vercel Account](https://vercel.com/)**
2. A **[Supabase Project](https://supabase.com/)** (for Cloud Database & Storage)
3. A **[Groq API Key](https://console.groq.com/)** (for AI Insights & Assistant)

---

## ⚙️ Step 1: Import Project into Vercel
1. Go to [Vercel Dashboard](https://vercel.com/new).
2. Select your GitHub repository: `Hariom-Pandey/Secure-File-Management-System`.
3. In **Project Settings**:
   - **Framework Preset**: `Other` (or leave default)
   - **Root Directory**: `./` (leave as repository root)
   - **Build & Output Settings**: Leave defaults (Vercel automatically detects `vercel.json` and `@vercel/python`)

---

## 🔑 Step 2: Configure Environment Variables in Vercel
In the Vercel project configuration page (under **Environment Variables**), add the following:

| Variable Name | Description | Example / Recommended Value |
| :--- | :--- | :--- |
| `SECRET_KEY` | Flask session secret | *(Generate a 32-char hex key or random string)* |
| `JWT_SECRET_KEY` | JWT token secret | *(Generate a 32-char hex key or random string)* |
| `MASTER_KEY` | 32-byte Fernet key for file encryption | *(Generate via `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`)* |
| `SUPABASE_URL` | Your Supabase Project URL | `https://your-project.supabase.co` |
| `SUPABASE_KEY` | Your Supabase Service Role Key or Anon Key | `sb_secret_...` or `eyJ...` |
| `SUPABASE_STORAGE_BUCKET` | Storage bucket name | `secure-files` |
| `USE_SUPABASE_STORAGE` | Store encrypted files in cloud bucket | `true` |
| `USE_SUPABASE_DB` | Store records in Supabase PostgreSQL | `true` |
| `GROQ_API_KEY` | Your Groq API key | `gsk_...` |
| `GROQ_MODEL` | Active Groq LLM model | `qwen/qwen3.8-27b` |
| `GROQ_FALLBACK_MODEL` | Fallback Groq LLM model | `groq/compound` |
| `GROQ_REQUIRE_SUCCESS` | AI Insight requirement flag | `true` |

> 💡 **Tip for Generating `MASTER_KEY`**:
> Run in terminal:
> ```bash
> python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
> ```
> Paste this key into Vercel as `MASTER_KEY`. This ensures all serverless function instances share the exact same encryption key!

---

## 📦 Step 3: Deploy & Verify
1. Click **Deploy**.
2. Once deployment completes, visit your assigned `.vercel.app` URL.
3. Check the health status at `/api/health` to confirm Supabase and Groq connectivity:
   ```json
   {
     "database": "supabase",
     "service": "Secure File Management System",
     "status": "ok",
     "storage": "supabase (secure-files)",
     "storage_bucket": "secure-files",
     "supabase_configured": true
   }
   ```

---

## ⚠️ Important Vercel Notes & Limitations
- **Serverless File Size Limit**: Vercel free tier limits request bodies to **4.5 MB**. Uploading files larger than 4.5 MB directly through serverless functions may trigger a 413 error.
- **Persistence**: Because Vercel functions are stateless and read-only, ensure `USE_SUPABASE_STORAGE=true` and `USE_SUPABASE_DB=true` so all user accounts, audit logs, and files persist in Supabase.
