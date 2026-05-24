# core/db.py
import sqlite3
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import DB_PATH
from core.colors import normalize_color


def get_connection(db_path=DB_PATH):
    return sqlite3.connect(db_path, check_same_thread=False)


def _detect_columns(c):
    c.execute("PRAGMA table_info(results_raw)")
    columns = {row[1]: row[0] for row in c.fetchall()}

    color_col = next(
        (x for x in ["color", "colour", "cor", "roll", "value", "resultado", "result"]
         if x in columns), None
    )
    time_col = next(
        (x for x in ["created_at", "timestamp", "time", "data", "dt", "id"]
         if x in columns), None
    )
    return color_col, time_col, columns


def create_tables(db_path=DB_PATH):
    conn = get_connection(db_path)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS results_raw (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            color      TEXT NOT NULL,
            roll       INTEGER,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS sequence_strategies (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            sequence_str      TEXT NOT NULL UNIQUE,
            sequence_size     INTEGER NOT NULL,
            sequence_json     TEXT NOT NULL,
            occurrences       INTEGER NOT NULL,
            predict_color     TEXT NOT NULL,
            predict_count     INTEGER NOT NULL,
            confidence        REAL NOT NULL,
            distribution_json TEXT NOT NULL,
            created_at        TEXT NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS signals_log (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            sequence_str  TEXT NOT NULL,
            predict_color TEXT NOT NULL,
            confidence    REAL NOT NULL,
            result_color  TEXT,
            hit           INTEGER,
            logged_at     TEXT DEFAULT (datetime('now'))
        )
    """)

    conn.commit()
    conn.close()


def load_all_colors(db_path=DB_PATH) -> list:
    conn = get_connection(db_path)
    c = conn.cursor()
    color_col, time_col, _ = _detect_columns(c)

    if not color_col:
        print("[DB] ERRO: coluna de cor não encontrada.")
        conn.close()
        return []

    order = f"ORDER BY {time_col} ASC" if time_col else ""
    c.execute(f"SELECT {color_col} FROM results_raw {order}")
    rows = c.fetchall()
    conn.close()

    return [normalize_color(r[0]) for r in rows]


def get_last_id(db_path=DB_PATH):
    conn = get_connection(db_path)
    c = conn.cursor()
    try:
        result = c.execute("SELECT MAX(id) FROM results_raw").fetchone()[0]
    except Exception:
        result = None
    conn.close()
    return result


def fetch_recent_colors(limit=10, db_path=DB_PATH) -> list:
    conn = get_connection(db_path)
    c = conn.cursor()
    color_col, time_col, _ = _detect_columns(c)

    if not color_col:
        conn.close()
        return []

    order = f"ORDER BY {time_col} DESC" if time_col else ""
    c.execute(f"SELECT {color_col} FROM results_raw {order} LIMIT {limit}")
    rows = c.fetchall()
    conn.close()

    colors = [normalize_color(r[0]) for r in rows]
    colors.reverse()
    return colors


def insert_result(color: str, roll: int = None, db_path=DB_PATH):
    conn = get_connection(db_path)
    c = conn.cursor()
    c.execute(
        "INSERT INTO results_raw (color, roll) VALUES (?, ?)",
        (color, roll)
    )
    conn.commit()
    conn.close()


def log_signal(sequence_str, predict_color, confidence, db_path=DB_PATH):
    conn = get_connection(db_path)
    c = conn.cursor()
    c.execute("""
        INSERT INTO signals_log (sequence_str, predict_color, confidence)
        VALUES (?, ?, ?)
    """, (sequence_str, predict_color, confidence))
    conn.commit()
    conn.close()


def total_results(db_path=DB_PATH) -> int:
    conn = get_connection(db_path)
    c = conn.cursor()
    try:
        n = c.execute("SELECT COUNT(*) FROM results_raw").fetchone()[0]
    except Exception:
        n = 0
    conn.close()
    return n
