import logging
from app.models.database import get_connection
from app.supabase_client import get_supabase_client, is_supabase_configured

logger = logging.getLogger(__name__)


class AuditLog:
    @staticmethod
    def log(user_id, action, resource=None, details=None, ip_address=None):
        if is_supabase_configured():
            try:
                client = get_supabase_client()
                if client:
                    client.table("audit_log").insert({
                        "user_id": user_id,
                        "action": action,
                        "resource": resource,
                        "details": details,
                        "ip_address": ip_address,
                    }).execute()
                    return
            except Exception as e:
                logger.error(f"Supabase AuditLog.log error, falling back to SQLite: {e}")

        conn = get_connection()
        conn.execute(
            "INSERT INTO audit_log (user_id, action, resource, details, ip_address) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, action, resource, details, ip_address)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def get_logs(limit=100, user_id=None):
        if is_supabase_configured():
            try:
                client = get_supabase_client()
                if client:
                    query = client.table("audit_log").select("*").order("timestamp", desc=True).limit(limit)
                    if user_id is not None:
                        query = query.eq("user_id", user_id)
                    res = query.execute()
                    if res.data is not None:
                        return res.data
            except Exception as e:
                logger.error(f"Supabase AuditLog.get_logs error, falling back to SQLite: {e}")

        conn = get_connection()
        if user_id:
            rows = conn.execute(
                "SELECT * FROM audit_log WHERE user_id = ? "
                "ORDER BY timestamp DESC LIMIT ?",
                (user_id, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            ).fetchall()
        conn.close()
        return [dict(row) for row in rows]

    @staticmethod
    def get_file_logs(file_id, limit=100):
        if is_supabase_configured():
            try:
                client = get_supabase_client()
                if client:
                    res = client.table("audit_log").select("*").eq("resource", f"file_id:{file_id}").order("timestamp", desc=True).limit(limit).execute()
                    if res.data is not None:
                        return res.data
            except Exception as e:
                logger.error(f"Supabase AuditLog.get_file_logs error, falling back to SQLite: {e}")

        conn = get_connection()
        rows = conn.execute(
            "SELECT * FROM audit_log WHERE resource = ? ORDER BY timestamp DESC LIMIT ?",
            (f"file_id:{file_id}", limit)
        ).fetchall()
        conn.close()
        return [dict(row) for row in rows]
