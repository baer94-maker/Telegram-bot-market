import sqlite3
import json
from datetime import datetime
from config import DATABASE_PATH


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    cur = conn.cursor()
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY,
            username    TEXT,
            first_name  TEXT,
            created_at  TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS sessions (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id         INTEGER NOT NULL,
            description     TEXT,
            photo_file_id   TEXT,
            clarify_qa      TEXT DEFAULT '[]',
            clarify_count   INTEGER DEFAULT 0,
            card_result     TEXT,
            created_at      TEXT DEFAULT (datetime('now')),
            updated_at      TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """)
    conn.commit()
    conn.close()


def upsert_user(user_id: int, username: str | None, first_name: str | None) -> None:
    conn = get_connection()
    conn.execute(
        """INSERT INTO users (id, username, first_name)
           VALUES (?, ?, ?)
           ON CONFLICT(id) DO UPDATE SET username=excluded.username, first_name=excluded.first_name""",
        (user_id, username, first_name),
    )
    conn.commit()
    conn.close()


def create_session(user_id: int, description: str = "", photo_file_id: str = "") -> int:
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO sessions (user_id, description, photo_file_id) VALUES (?, ?, ?)",
        (user_id, description, photo_file_id),
    )
    session_id = cur.lastrowid
    conn.commit()
    conn.close()
    return session_id


def get_session(session_id: int) -> dict | None:
    conn = get_connection()
    row = conn.execute("SELECT * FROM sessions WHERE id=?", (session_id,)).fetchone()
    conn.close()
    if row is None:
        return None
    d = dict(row)
    d["clarify_qa"] = json.loads(d["clarify_qa"])
    return d


def update_session(session_id: int, **kwargs) -> None:
    if not kwargs:
        return
    if "clarify_qa" in kwargs:
        kwargs["clarify_qa"] = json.dumps(kwargs["clarify_qa"], ensure_ascii=False)
    kwargs["updated_at"] = datetime.utcnow().isoformat()
    fields = ", ".join(f"{k}=?" for k in kwargs)
    values = list(kwargs.values()) + [session_id]
    conn = get_connection()
    conn.execute(f"UPDATE sessions SET {fields} WHERE id=?", values)
    conn.commit()
    conn.close()


def get_latest_session(user_id: int) -> dict | None:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM sessions WHERE user_id=? ORDER BY id DESC LIMIT 1",
        (user_id,),
    ).fetchone()
    conn.close()
    if row is None:
        return None
    d = dict(row)
    d["clarify_qa"] = json.loads(d["clarify_qa"])
    return d