# 🚀 Supabase Integration Guide
### Secure File Management System

This guide outlines how to connect your **Supabase** cloud database and storage with this project in just a few simple steps.

---

## 1. Get Your Supabase Credentials

1. Go to [https://supabase.com](https://supabase.com) and log into your dashboard.
2. Create a new project (or select an existing one).
3. Navigate to **Project Settings** (gear icon) ➔ **API**.
4. Copy the following values:
   - **Project URL**: `https://<your-project-ref>.supabase.co`
   - **API Keys**: Copy the `service_role` secret key (recommended for backend server) or the `anon` public key.

---

## 2. Execute the Database Schema in Supabase

1. In your Supabase dashboard, click on **SQL Editor** (the `>_` icon on the left sidebar).
2. Click **New Query**.
3. Open the file [`supabase_schema.sql`](supabase_schema.sql) in this repository and copy all its contents.
4. Paste the SQL script into the Supabase SQL editor and click **Run**.
5. This creates:
   - `public.users` (user accounts, roles, 2FA/PIN state)
   - `public.files` (metadata, encryption flags, file paths)
   - `public.file_permissions` (read/write access control list)
   - `public.audit_log` (security and compliance logs)
   - `public.share_history` (history of shared files)
   - High-performance indexes and automatic `updated_at` triggers.
   - Storage bucket `secure-files` for optional cloud file storage.

---

## 3. Add Credentials to `.env`

Open your `.env` file (located in the `project/` directory or root) and paste your credentials:

```env
# ========================================================
# Supabase Configuration
# ========================================================
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_STORAGE_BUCKET=secure-files
USE_SUPABASE_STORAGE=false
```

> **Note on Storage**:
> - If `USE_SUPABASE_STORAGE=true`, encrypted file payloads (`.enc` files) will also be uploaded to your Supabase Storage bucket `secure-files`.
> - If `USE_SUPABASE_STORAGE=false`, database records are stored in Supabase PostgreSQL while encrypted files remain on your local disk storage.

---

## 4. Run the Project

Start the application as usual:

```powershell
.venv\Scripts\python project\main.py
```

You will see:
```text
=== Secure File Management System ===
Server running at http://127.0.0.1:5000
Database Backend: Supabase (Cloud PostgreSQL)
```

You can also check the health endpoint at:
`http://127.0.0.1:5000/api/health`

It will return:
```json
{
  "database": "supabase",
  "service": "Secure File Management System",
  "status": "ok",
  "supabase_configured": true
}
```

---

## 5. Offline / Local Fallback

If `SUPABASE_URL` or `SUPABASE_KEY` are empty or omitted, the application will **automatically and safely fall back** to the local SQLite database (`project/data/secure_files.db`) without throwing errors.
