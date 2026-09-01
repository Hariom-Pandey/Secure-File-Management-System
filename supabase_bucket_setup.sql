-- =============================================================================
-- Supabase Storage Bucket Setup Script for Secure File Management System
-- =============================================================================
-- Copy and run this script in your Supabase SQL Editor:
-- https://supabase.com/dashboard/project/_/sql
-- =============================================================================

-- 1. Create or Update the Private Storage Bucket 'secure-files'
INSERT INTO storage.buckets (
    id,
    name,
    public,
    file_size_limit,
    allowed_mime_types
)
VALUES (
    'secure-files',
    'secure-files',
    false,               -- Private bucket
    52428800,            -- 50 MB limit (50 * 1024 * 1024 bytes)
    NULL                 -- Allows all MIME types (including .enc binary files)
)
ON CONFLICT (id) DO UPDATE SET
    public = EXCLUDED.public,
    file_size_limit = EXCLUDED.file_size_limit,
    allowed_mime_types = EXCLUDED.allowed_mime_types;

-- 2. Remove old policies if they exist (to avoid duplicate policy errors)
DROP POLICY IF EXISTS "Service Role Full Access on secure-files" ON storage.objects;
DROP POLICY IF EXISTS "Authenticated Users Full Access on secure-files" ON storage.objects;

-- 3. Policy: Service Role has full access (for backend server operations)
CREATE POLICY "Service Role Full Access on secure-files"
ON storage.objects
FOR ALL
TO service_role
USING (bucket_id = 'secure-files')
WITH CHECK (bucket_id = 'secure-files');

-- 4. Policy: Authenticated users have full access
CREATE POLICY "Authenticated Users Full Access on secure-files"
ON storage.objects
FOR ALL
TO authenticated
USING (bucket_id = 'secure-files')
WITH CHECK (bucket_id = 'secure-files');
