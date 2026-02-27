import sqlite3
import threading
from datetime import datetime
from typing import Iterable


def _now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")


class Database:
    def __init__(self, path: str) -> None:
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY,
                    username TEXT,
                    full_name TEXT,
                    is_banned INTEGER DEFAULT 0,
                    joined_at TEXT,
                    updated_at TEXT
                )
                """
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS links (
                    admin_msg_id INTEGER PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    created_at TEXT
                )
                """
            )

    def add_or_update_user(self, user_id: int, username: str | None, full_name: str) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                """
                INSERT INTO users (id, username, full_name, is_banned, joined_at, updated_at)
                VALUES (?, ?, ?, 0, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    username=excluded.username,
                    full_name=excluded.full_name,
                    updated_at=excluded.updated_at
                """,
                (user_id, username, full_name, _now(), _now()),
            )

    def set_ban(self, user_id: int, is_banned: bool) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                "UPDATE users SET is_banned=?, updated_at=? WHERE id=?",
                (1 if is_banned else 0, _now(), user_id),
            )

    def is_banned(self, user_id: int) -> bool:
        with self._lock:
            cur = self._conn.execute("SELECT is_banned FROM users WHERE id=?", (user_id,))
            row = cur.fetchone()
            return bool(row["is_banned"]) if row else False

    def add_link(self, admin_msg_id: int, user_id: int) -> None:
        with self._lock, self._conn:
            self._conn.execute(
                "INSERT OR IGNORE INTO links (admin_msg_id, user_id, created_at) VALUES (?, ?, ?)",
                (admin_msg_id, user_id, _now()),
            )

    def get_user_id_by_admin_msg(self, admin_msg_id: int) -> int | None:
        with self._lock:
            cur = self._conn.execute("SELECT user_id FROM links WHERE admin_msg_id=?", (admin_msg_id,))
            row = cur.fetchone()
            return int(row["user_id"]) if row else None

    def count_users(self) -> int:
        with self._lock:
            cur = self._conn.execute("SELECT COUNT(*) AS cnt FROM users")
            return int(cur.fetchone()["cnt"])

    def count_banned(self) -> int:
        with self._lock:
            cur = self._conn.execute("SELECT COUNT(*) AS cnt FROM users WHERE is_banned=1")
            return int(cur.fetchone()["cnt"])

    def count_messages(self) -> int:
        with self._lock:
            cur = self._conn.execute("SELECT COUNT(*) AS cnt FROM links")
            return int(cur.fetchone()["cnt"])

    def get_users_page(self, offset: int, limit: int) -> list[sqlite3.Row]:
        with self._lock:
            cur = self._conn.execute(
                "SELECT id, username, full_name, is_banned FROM users ORDER BY joined_at ASC LIMIT ? OFFSET ?",
                (limit, offset),
            )
            return list(cur.fetchall())

    def iter_user_ids(self, only_active: bool = True) -> Iterable[int]:
        with self._lock:
            if only_active:
                cur = self._conn.execute("SELECT id FROM users WHERE is_banned=0 ORDER BY joined_at ASC")
            else:
                cur = self._conn.execute("SELECT id FROM users ORDER BY joined_at ASC")
            rows = cur.fetchall()
        for row in rows:
            yield int(row["id"])
