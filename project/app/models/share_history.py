import logging
from app.models.database import get_connection
from app.supabase_client import get_supabase_client, is_supabase_configured

logger = logging.getLogger(__name__)


class ShareHistory:
    @staticmethod
    def create_event(file_id, sender_user_id, target_user_id, action,
                     permission=None, previous_permission=None):
        if is_supabase_configured():
            try:
                client = get_supabase_client()
                if client:
                    client.table("share_history").insert({
                        "file_id": file_id,
                        "sender_user_id": sender_user_id,
                        "target_user_id": target_user_id,
                        "action": action,
                        "permission": permission,
                        "previous_permission": previous_permission,
                    }).execute()
                    return
            except Exception as e:
                logger.error(f"Supabase ShareHistory.create_event error, falling back to SQLite: {e}")

        conn = get_connection()
        conn.execute(
            "INSERT INTO share_history "
            "(file_id, sender_user_id, target_user_id, action, permission, previous_permission) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (file_id, sender_user_id, target_user_id, action, permission, previous_permission)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def get_sent_by_user(sender_user_id, limit=200):
        if is_supabase_configured():
            try:
                client = get_supabase_client()
                if client:
                    sh_res = client.table("share_history").select("*").eq("sender_user_id", sender_user_id).order("created_at", desc=True).limit(limit).execute()
                    rows = sh_res.data or []
                    result = []
                    for r in rows:
                        item = dict(r)
                        # Fetch file name
                        f_res = client.table("files").select("original_name").eq("id", r.get("file_id")).limit(1).execute()
                        item["filename"] = f_res.data[0]["original_name"] if f_res.data else None

                        # Fetch target username
                        t_res = client.table("users").select("username").eq("id", r.get("target_user_id")).limit(1).execute()
                        item["target_username"] = t_res.data[0]["username"] if t_res.data else None

                        result.append(item)
                    return result
            except Exception as e:
                logger.error(f"Supabase ShareHistory.get_sent_by_user error, falling back to SQLite: {e}")

        conn = get_connection()
        rows = conn.execute(
            "SELECT sh.id, sh.file_id, sh.sender_user_id, sh.target_user_id, "
            "sh.action, sh.permission, sh.previous_permission, sh.created_at, "
            "f.original_name AS filename, target.username AS target_username "
            "FROM share_history sh "
            "JOIN files f ON f.id = sh.file_id "
            "JOIN users target ON target.id = sh.target_user_id "
            "WHERE sh.sender_user_id = ? "
            "ORDER BY sh.created_at DESC, sh.id DESC "
            "LIMIT ?",
            (sender_user_id, limit)
        ).fetchall()
        conn.close()
        return [dict(row) for row in rows]
