import logging
from app.models.database import get_connection
from app.supabase_client import get_supabase_client, is_supabase_configured

logger = logging.getLogger(__name__)


class User:
    def __init__(self, id=None, username=None, password_hash=None, role="user",
                 totp_secret=None, two_factor_enabled=False,
                 created_at=None, updated_at=None):
        self.id = id
        self.username = username
        self.password_hash = password_hash
        self.role = role
        self.totp_secret = totp_secret
        self.two_factor_enabled = bool(two_factor_enabled)
        self.created_at = created_at
        self.updated_at = updated_at

    @staticmethod
    def create(username, password_hash, role="user"):
        if is_supabase_configured():
            try:
                client = get_supabase_client()
                if client:
                    res = client.table("users").insert({
                        "username": username,
                        "password_hash": password_hash,
                        "role": role,
                    }).execute()
                    if res.data and len(res.data) > 0:
                        return User(**res.data[0])
            except Exception as e:
                logger.error(f"Supabase User.create error, falling back to SQLite: {e}")

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            (username, password_hash, role)
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return User.get_by_id(user_id)

    @staticmethod
    def get_by_id(user_id):
        if user_id is None:
            return None

        if is_supabase_configured():
            try:
                client = get_supabase_client()
                if client:
                    res = client.table("users").select("*").eq("id", user_id).limit(1).execute()
                    if res.data and len(res.data) > 0:
                        return User(**res.data[0])
                    return None
            except Exception as e:
                logger.error(f"Supabase User.get_by_id error, falling back to SQLite: {e}")

        conn = get_connection()
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        conn.close()
        if row:
            return User(**dict(row))
        return None

    @staticmethod
    def get_by_username(username):
        if username is None:
            return None

        normalized = username.strip()
        if not normalized:
            return None

        if is_supabase_configured():
            try:
                client = get_supabase_client()
                if client:
                    res = client.table("users").select("*").ilike("username", normalized).limit(1).execute()
                    if res.data and len(res.data) > 0:
                        return User(**res.data[0])
                    return None
            except Exception as e:
                logger.error(f"Supabase User.get_by_username error, falling back to SQLite: {e}")

        conn = get_connection()
        row = conn.execute(
            "SELECT * FROM users WHERE username = ? COLLATE NOCASE", (normalized,)
        ).fetchone()
        conn.close()
        if row:
            return User(**dict(row))
        return None

    def update_totp_secret(self, secret):
        if is_supabase_configured():
            try:
                client = get_supabase_client()
                if client:
                    client.table("users").update({
                        "totp_secret": secret,
                        "two_factor_enabled": True
                    }).eq("id", self.id).execute()
                    self.totp_secret = secret
                    self.two_factor_enabled = True
                    return
            except Exception as e:
                logger.error(f"Supabase User.update_totp_secret error, falling back to SQLite: {e}")

        conn = get_connection()
        conn.execute(
            "UPDATE users SET totp_secret = ?, two_factor_enabled = 1, "
            "updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (secret, self.id)
        )
        conn.commit()
        conn.close()
        self.totp_secret = secret
        self.two_factor_enabled = True

    def disable_2fa(self):
        if is_supabase_configured():
            try:
                client = get_supabase_client()
                if client:
                    client.table("users").update({
                        "totp_secret": None,
                        "two_factor_enabled": False
                    }).eq("id", self.id).execute()
                    self.totp_secret = None
                    self.two_factor_enabled = False
                    return
            except Exception as e:
                logger.error(f"Supabase User.disable_2fa error, falling back to SQLite: {e}")

        conn = get_connection()
        conn.execute(
            "UPDATE users SET totp_secret = NULL, two_factor_enabled = 0, "
            "updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (self.id,)
        )
        conn.commit()
        conn.close()
        self.totp_secret = None
        self.two_factor_enabled = False

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role,
            "two_factor_enabled": bool(self.two_factor_enabled),
            "created_at": str(self.created_at) if self.created_at else None,
            "updated_at": str(self.updated_at) if self.updated_at else None,
        }
