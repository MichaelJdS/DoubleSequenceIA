# strategies/strategy_manager.py
import sqlite3
import json
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import DB_PATH, STRATEGIES_JSON
from core.db import get_connection


def save_strategies(strategies: list, db_path=DB_PATH):
    conn = get_connection(db_path)
    c = conn.cursor()
    inserted = updated = 0

    for s in strategies:
        exists = c.execute(
            "SELECT id FROM sequence_strategies WHERE sequence_str = ?",
            (s["sequence_str"],)
        ).fetchone()

        if exists:
            c.execute("""
                UPDATE sequence_strategies
                SET occurrences=?, predict_color=?, predict_count=?,
                    confidence=?, distribution_json=?, created_at=?, sequence_size=?
                WHERE sequence_str=?
            """, (s["occurrences"], s["predict_color"], s["predict_count"],
                  s["confidence"], json.dumps(s["distribution"]),
                  s["created_at"], s["sequence_size"], s["sequence_str"]))
            updated += 1
        else:
            c.execute("""
                INSERT INTO sequence_strategies
                (sequence_str, sequence_size, sequence_json, occurrences,
                 predict_color, predict_count, confidence, distribution_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (s["sequence_str"], s["sequence_size"],
                  json.dumps(s["sequence"]), s["occurrences"],
                  s["predict_color"], s["predict_count"],
                  s["confidence"], json.dumps(s["distribution"]),
                  s["created_at"]))
            inserted += 1

    conn.commit()
    conn.close()
    print(f"[STRATEGIES] {inserted} novas | {updated} atualizadas")


def load_strategies(min_confidence=70.0, db_path=DB_PATH) -> tuple:
    conn = get_connection(db_path)
    c = conn.cursor()
    try:
        c.execute("""
            SELECT sequence_str, sequence_json, predict_color,
                   confidence, occurrences, distribution_json, sequence_size
            FROM sequence_strategies
            WHERE confidence >= ?
            ORDER BY confidence DESC, occurrences DESC
        """, (min_confidence,))
        rows = c.fetchall()
    except Exception as e:
        print(f"[STRATEGIES] Tabela não encontrada: {e}")
        conn.close()
        return [], {}
    conn.close()

    strategies = [
        {
            "sequence_str":  r[0],
            "sequence":      json.loads(r[1]),
            "predict_color": r[2],
            "confidence":    r[3],
            "occurrences":   r[4],
            "distribution":  json.loads(r[5]),
            "sequence_size": r[6],
        }
        for r in rows
    ]

    by_size = {}
    for s in strategies:
        by_size.setdefault(s["sequence_size"], []).append(s)

    return strategies, by_size


def export_json(strategies: list, path=None):
    if path is None:
        path = STRATEGIES_JSON
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(strategies, f, ensure_ascii=False, indent=2)
    print(f"[STRATEGIES] {len(strategies)} estratégias exportadas → {path}")


def print_report(strategies: list, top_n=20):
    from collections import defaultdict
    from datetime import datetime

    print("\n" + "="*72)
    print(f"  RELATÓRIO DE PADRÕES — {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    print("="*72)
    print(f"  Total: {len(strategies)} estratégias válidas\n")

    by_size = defaultdict(list)
    for s in strategies:
        by_size[s["sequence_size"]].append(s)

    per_group = max(1, top_n // len(by_size)) if by_size else top_n
    for size in sorted(by_size.keys()):
        group = by_size[size]
        print(f"  {'─'*68}")
        print(f"  SEQUÊNCIAS DE {size} CORES — {len(group)} estratégias")
        print(f"  {'─'*68}")
        for i, s in enumerate(group[:per_group], 1):
            emoji = {"preto": "⚫", "vermelho": "🔴", "branco": "⚪"}.get(s["predict_color"], "?")
            dist = " | ".join(f"{c.upper()}: {p}%" for c, p in s["distribution"].items())
            print(f"  [{i:02d}] {s['sequence_str']}")
            print(f"       ➜ {emoji} {s['predict_color'].upper():<10} | {s['confidence']}% confiança | {s['occurrences']}x histórico")
            print(f"       📊 {dist}\n")
    print("="*72)
