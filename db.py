import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "upload_log.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE NOT NULL,
            video_id TEXT,
            title TEXT,
            uploaded_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def already_uploaded(filename: str) -> bool:
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute(
        "SELECT 1 FROM uploads WHERE filename = ?", (filename,)
    ).fetchone()
    conn.close()
    return row is not None

def log_upload(filename: str, title: str, video_id: str = None):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT OR IGNORE INTO uploads (filename, video_id, title, uploaded_at) VALUES (?, ?, ?, ?)",
        (filename, video_id, title, datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()

def list_uploads():
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT filename, title, uploaded_at FROM uploads ORDER BY uploaded_at DESC"
    ).fetchall()
    conn.close()
    return rows
