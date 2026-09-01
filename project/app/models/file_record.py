import logging
from app.models.database import get_connection
from app.supabase_client import get_supabase_client, is_supabase_configured

logger = logging.getLogger(__name__)


class FileRecord:
    def __init__(self, id=None, filename=None, original_name=None,
                 owner_id=None, file_size=0, file_type=None,
                 is_encrypted=True, created_at=None, updated_at=None,
                 owner_username=None, shared_permission=None,
                 shared_by_username=None, shared_at=None,
                 permission_updated_at=None, storage_path=None):
        self.id = id
        self.filename = filename
        self.original_name = original_name
        self.owner_id = owner_id
        self.file_size = file_size
        self.file_type = file_type
        self.is_encrypted = bool(is_encrypted)
        self.created_at = created_at
        self.updated_at = updated_at
        self.owner_username = owner_username
        self.shared_permission = shared_permission
        self.shared_by_username = shared_by_username
        self.shared_at = shared_at
        self.permission_updated_at = permission_updated_at
        self.storage_path = storage_path

    @staticmethod
    def create(filename, original_name, owner_id, file_size, file_type, storage_path=None):
        if is_supabase_configured():
            try:
                client = get_supabase_client()
                if client:
                    data = {
                        "filename": filename,
                        "original_name": original_name,
                        "owner_id": owner_id,
                        "file_size": file_size,
                        "file_type": file_type,
                        "is_encrypted": True,
                    }
                    if storage_path:
                        data["storage_path"] = storage_path
                    res = client.table("files").insert(data).execute()
                    if res.data and len(res.data) > 0:
                        return FileRecord(**res.data[0])
            except Exception as e:
                logger.error(f"Supabase FileRecord.create error, falling back to SQLite: {e}")

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO files (filename, original_name, owner_id, file_size, file_type) "
            "VALUES (?, ?, ?, ?, ?)",
            (filename, original_name, owner_id, file_size, file_type)
        )
        conn.commit()
        file_id = cursor.lastrowid
        conn.close()
        return FileRecord.get_by_id(file_id)

    @staticmethod
    def get_by_id(file_id):
        if file_id is None:
            return None

        if is_supabase_configured():
            try:
                client = get_supabase_client()
                if client:
                    res = client.table("files").select("*").eq("id", file_id).limit(1).execute()
                    if res.data and len(res.data) > 0:
                        return FileRecord(**res.data[0])
                    return None
            except Exception as e:
                logger.error(f"Supabase FileRecord.get_by_id error, falling back to SQLite: {e}")

        conn = get_connection()
        row = conn.execute("SELECT * FROM files WHERE id = ?", (file_id,)).fetchone()
        conn.close()
        if row:
            return FileRecord(**dict(row))
        return None

    @staticmethod
    def get_by_owner(owner_id):
        if is_supabase_configured():
            try:
                client = get_supabase_client()
                if client:
                    res = client.table("files").select("*").eq("owner_id", owner_id).order("created_at", desc=True).execute()
                    if res.data is not None:
                        return [FileRecord(**row) for row in res.data]
            except Exception as e:
                logger.error(f"Supabase FileRecord.get_by_owner error, falling back to SQLite: {e}")

        conn = get_connection()
        rows = conn.execute(
            "SELECT * FROM files WHERE owner_id = ? ORDER BY created_at DESC",
            (owner_id,)
        ).fetchall()
        conn.close()
        return [FileRecord(**dict(row)) for row in rows]

    @staticmethod
    def get_shared_with_user(user_id):
        if is_supabase_configured():
            try:
                client = get_supabase_client()
                if client:
                    perm_res = client.table("file_permissions").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
                    permissions = perm_res.data or []
                    if not permissions:
                        return []

                    records = []
                    for p in permissions:
                        file_res = client.table("files").select("*").eq("id", p.get("file_id")).limit(1).execute()
                        if not file_res.data:
                            continue
                        f_data = file_res.data[0]

                        # Get owner username
                        owner_name = None
                        if f_data.get("owner_id"):
                            u_res = client.table("users").select("username").eq("id", f_data.get("owner_id")).limit(1).execute()
                            if u_res.data:
                                owner_name = u_res.data[0].get("username")

                        # Get granter username
                        granter_name = None
                        if p.get("granted_by"):
                            g_res = client.table("users").select("username").eq("id", p.get("granted_by")).limit(1).execute()
                            if g_res.data:
                                granter_name = g_res.data[0].get("username")

                        rec = FileRecord(
                            id=f_data.get("id"),
                            filename=f_data.get("filename"),
                            original_name=f_data.get("original_name"),
                            owner_id=f_data.get("owner_id"),
                            file_size=f_data.get("file_size", 0),
                            file_type=f_data.get("file_type"),
                            is_encrypted=f_data.get("is_encrypted", True),
                            created_at=f_data.get("created_at"),
                            updated_at=f_data.get("updated_at"),
                            owner_username=owner_name,
                            shared_permission=p.get("permission"),
                            shared_by_username=granter_name,
                            shared_at=p.get("created_at"),
                            permission_updated_at=p.get("updated_at"),
                        )
                        records.append(rec)
                    return records
            except Exception as e:
                logger.error(f"Supabase FileRecord.get_shared_with_user error, falling back to SQLite: {e}")

        conn = get_connection()
        rows = conn.execute(
            "SELECT f.*, owner.username AS owner_username, "
            "fp.permission AS shared_permission, "
            "fp.created_at AS shared_at, "
            "fp.updated_at AS permission_updated_at, "
            "granter.username AS shared_by_username "
            "FROM files f "
            "JOIN file_permissions fp ON f.id = fp.file_id "
            "JOIN users owner ON owner.id = f.owner_id "
            "LEFT JOIN users granter ON granter.id = fp.granted_by "
            "WHERE fp.user_id = ? "
            "ORDER BY fp.created_at DESC, f.created_at DESC",
            (user_id,)
        ).fetchall()
        conn.close()
        return [FileRecord(**dict(row)) for row in rows]

    def delete(self):
        if is_supabase_configured():
            try:
                client = get_supabase_client()
                if client:
                    client.table("files").delete().eq("id", self.id).execute()
                    return
            except Exception as e:
                logger.error(f"Supabase FileRecord.delete error, falling back to SQLite: {e}")

        conn = get_connection()
        conn.execute("DELETE FROM files WHERE id = ?", (self.id,))
        conn.commit()
        conn.close()

    def to_dict(self):
        return {
            "id": self.id,
            "filename": self.original_name,
            "owner_id": self.owner_id,
            "owner_username": self.owner_username,
            "file_size": self.file_size,
            "file_type": self.file_type,
            "is_encrypted": bool(self.is_encrypted),
            "created_at": str(self.created_at) if self.created_at else None,
            "updated_at": str(self.updated_at) if self.updated_at else None,
            "shared_permission": self.shared_permission,
            "shared_by_username": self.shared_by_username,
            "shared_at": str(self.shared_at) if self.shared_at else None,
            "permission_updated_at": str(self.permission_updated_at) if self.permission_updated_at else None,
        }


class FilePermission:
    @staticmethod
    def grant(file_id, user_id, permission, granted_by):
        if is_supabase_configured():
            try:
                client = get_supabase_client()
                if client:
                    client.table("file_permissions").upsert({
                        "file_id": file_id,
                        "user_id": user_id,
                        "permission": permission,
                        "granted_by": granted_by,
                    }, on_conflict="file_id,user_id").execute()
                    return
            except Exception as e:
                logger.error(f"Supabase FilePermission.grant error, falling back to SQLite: {e}")

        conn = get_connection()
        conn.execute(
            "INSERT INTO file_permissions (file_id, user_id, permission, granted_by) "
            "VALUES (?, ?, ?, ?) "
            "ON CONFLICT(file_id, user_id) DO UPDATE SET "
            "permission = excluded.permission, "
            "granted_by = excluded.granted_by, "
            "updated_at = CURRENT_TIMESTAMP",
            (file_id, user_id, permission, granted_by)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def revoke(file_id, user_id):
        if is_supabase_configured():
            try:
                client = get_supabase_client()
                if client:
                    client.table("file_permissions").delete().eq("file_id", file_id).eq("user_id", user_id).execute()
                    return
            except Exception as e:
                logger.error(f"Supabase FilePermission.revoke error, falling back to SQLite: {e}")

        conn = get_connection()
        conn.execute(
            "DELETE FROM file_permissions WHERE file_id = ? AND user_id = ?",
            (file_id, user_id)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def get_permission(file_id, user_id):
        if is_supabase_configured():
            try:
                client = get_supabase_client()
                if client:
                    res = client.table("file_permissions").select("permission").eq("file_id", file_id).eq("user_id", user_id).limit(1).execute()
                    if res.data and len(res.data) > 0:
                        return res.data[0].get("permission")
                    return None
            except Exception as e:
                logger.error(f"Supabase FilePermission.get_permission error, falling back to SQLite: {e}")

        conn = get_connection()
        row = conn.execute(
            "SELECT permission FROM file_permissions "
            "WHERE file_id = ? AND user_id = ?",
            (file_id, user_id)
        ).fetchone()
        conn.close()
        if row:
            return row["permission"]
        return None

    @staticmethod
    def get_file_permissions(file_id):
        if is_supabase_configured():
            try:
                client = get_supabase_client()
                if client:
                    res = client.table("file_permissions").select("*").eq("file_id", file_id).order("created_at", desc=True).execute()
                    permissions = res.data or []
                    result = []
                    for p in permissions:
                        # fetch user username
                        u_res = client.table("users").select("username").eq("id", p.get("user_id")).limit(1).execute()
                        u_name = u_res.data[0]["username"] if u_res.data else None

                        g_res = client.table("users").select("username").eq("id", p.get("granted_by")).limit(1).execute() if p.get("granted_by") else None
                        g_name = g_res.data[0]["username"] if g_res and g_res.data else None

                        item = dict(p)
                        item["username"] = u_name
                        item["granted_by_username"] = g_name
                        result.append(item)
                    return result
            except Exception as e:
                logger.error(f"Supabase FilePermission.get_file_permissions error, falling back to SQLite: {e}")

        conn = get_connection()
        rows = conn.execute(
            "SELECT fp.id, fp.file_id, fp.user_id, fp.permission, fp.granted_by, "
            "fp.created_at, fp.updated_at, "
            "u.username AS username, gu.username AS granted_by_username "
            "FROM file_permissions fp "
            "JOIN users u ON fp.user_id = u.id "
            "LEFT JOIN users gu ON fp.granted_by = gu.id "
            "WHERE fp.file_id = ? "
            "ORDER BY fp.updated_at DESC, fp.created_at DESC",
            (file_id,)
        ).fetchall()
        conn.close()
        return [dict(row) for row in rows]
