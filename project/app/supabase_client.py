import logging
from typing import Optional, Tuple
from config import Config

logger = logging.getLogger(__name__)

_supabase_client = None
_client_init_attempted = False


def is_supabase_configured() -> bool:
    """Check if valid Supabase URL and Key are provided in configuration."""
    if Config.USE_SUPABASE_DB in {"false", "0", "no", "off"}:
        return False
    url = (Config.SUPABASE_URL or "").strip()
    key = (Config.SUPABASE_KEY or "").strip()
    return bool(url and key and url.startswith("http"))


def get_supabase_client():
    """
    Get or initialize the Supabase client singleton.
    Returns None if credentials are not configured or client creation fails.
    """
    global _supabase_client, _client_init_attempted

    if _supabase_client is not None:
        return _supabase_client

    if not is_supabase_configured():
        return None

    try:
        from supabase import create_client, Client
        _supabase_client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
        logger.info("Supabase client initialized successfully.")
        return _supabase_client
    except Exception as e:
        logger.warning(f"Failed to initialize Supabase client: {e}")
        return None


def reset_supabase_client():
    """Reset cached client (useful for tests or runtime credential reloads)."""
    global _supabase_client
    _supabase_client = None


def test_supabase_connection() -> Tuple[bool, str]:
    """Test connectivity to the Supabase instance."""
    client = get_supabase_client()
    if client is None:
        return False, "Supabase is not configured. Provide SUPABASE_URL and SUPABASE_KEY in .env."

    try:
        # Perform a lightweight query against users table
        response = client.table("users").select("id").limit(1).execute()
        return True, "Supabase database connection successful."
    except Exception as e:
        return False, f"Supabase connection error: {str(e)}"


# =============================================================================
# Supabase Cloud Storage Helpers
# =============================================================================

def upload_to_supabase_storage(
    destination_path: str,
    file_bytes: bytes,
    bucket_name: Optional[str] = None,
    content_type: str = "application/octet-stream"
) -> Tuple[bool, Optional[str]]:
    """
    Upload file bytes to a Supabase Storage bucket.
    Returns (True, destination_path) on success, (False, error_message) on failure.
    """
    client = get_supabase_client()
    if client is None:
        return False, "Supabase is not configured."

    bucket = bucket_name or Config.SUPABASE_STORAGE_BUCKET
    try:
        # Remove any leading slashes
        clean_path = destination_path.lstrip("/\\")
        
        # storage3 upload
        client.storage.from_(bucket).upload(
            path=clean_path,
            file=file_bytes,
            file_options={"content-type": content_type, "upsert": "true"}
        )
        return True, clean_path
    except Exception as e:
        logger.error(f"Supabase Storage upload error: {e}")
        return False, str(e)


def download_from_supabase_storage(
    file_path: str,
    bucket_name: Optional[str] = None
) -> Tuple[Optional[bytes], Optional[str]]:
    """
    Download file bytes from a Supabase Storage bucket.
    Returns (bytes, None) on success, (None, error_message) on failure.
    """
    client = get_supabase_client()
    if client is None:
        return None, "Supabase is not configured."

    bucket = bucket_name or Config.SUPABASE_STORAGE_BUCKET
    try:
        clean_path = file_path.lstrip("/\\")
        data = client.storage.from_(bucket).download(clean_path)
        return data, None
    except Exception as e:
        logger.error(f"Supabase Storage download error: {e}")
        return None, str(e)


def delete_from_supabase_storage(
    file_path: str,
    bucket_name: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    """
    Delete a file from a Supabase Storage bucket.
    Returns (True, None) on success, (False, error_message) on failure.
    """
    client = get_supabase_client()
    if client is None:
        return False, "Supabase is not configured."

    bucket = bucket_name or Config.SUPABASE_STORAGE_BUCKET
    try:
        clean_path = file_path.lstrip("/\\")
        client.storage.from_(bucket).remove([clean_path])
        return True, None
    except Exception as e:
        logger.error(f"Supabase Storage delete error: {e}")
        return False, str(e)
