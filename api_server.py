# -*- coding: utf-8 -*-
# api_server.py
# Servidor HTTP que fornece APIs para o dashboard

import sys
import os
import json
import io
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Configurar stdout para UTF-8 no Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

sys.path.insert(0, os.path.dirname(__file__))

from config import SIGNALS_LOG_JSON, DB_PATH
from core.db import get_connection, get_last_id, total_results
from core.colors import normalize_color
from strategies.strategy_manager import load_strategies


def fetch_recent_with_rolls(limit=20, db_path=DB_PATH):
    """Retorna lista de {color, roll, id, timestamp} dos resultados mais recentes."""
    conn = get_connection(db_path)
    c = conn.cursor()
    try:
        rows = c.execute(
            "SELECT id, color, roll, created_at FROM results_raw ORDER BY id DESC LIMIT ?",
            (limit,)
        ).fetchall()
    except Exception:
        rows = []
    conn.close()
    results = []
    for row in rows:
        results.append({
            "id":        row[0],
            "color":     normalize_color(row[1]),
            "roll":      row[2],
            "timestamp": row[3],
        })
    results.reverse()  # mais antigo primeiro
    return results


def find_best_bet(recent_colors, db_path=DB_PATH):
    """Verifica se a cauda recente bate com alguma estratégia e retorna a melhor aposta."""
    conn = get_connection(db_path)
    c = conn.cursor()
    try:
        rows = c.execute(
            """SELECT sequence_str, sequence_json, predict_color, confidence, occurrences, distribution_json
               FROM sequence_strategies WHERE confidence >= 70
               ORDER BY confidence DESC, occurrences DESC"""
        ).fetchall()
    except Exception:
        rows = []
    conn.close()

    import json as _json
    best = None
    for row in rows:
        seq = _json.loads(row[1])
        n = len(seq)
        if len(recent_colors) >= n and recent_colors[-n:] == seq:
            best = {
                "sequence_str":  row[0],
                "predict_color": row[2],
                "confidence":    row[3],
                "occurrences":   row[4],
                "distribution":  _json.loads(row[5]),
            }
            break
    return best


class DashboardAPI(BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        """Manipular CORS preflight"""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        try:
            if path == "/api/live":
                self._send_json(self._get_live())
            elif path == "/api/stats":
                self._send_json(self._get_stats())
            elif path == "/api/recent":
                self._send_json(self._get_recent())
            elif path == "/api/dashboard-data":
                self._send_json(self._get_dashboard_data())
            else:
                self._send_json({"error": "Endpoint não encontrado"}, 404)
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8", errors="ignore") if content_length else ""
        try:
            if path == "/api/reset-stats":
                reset_stats()
                self._send_json({"status": "ok", "message": "Stats resetadas com sucesso"})
            elif path == "/api/log-result":
                data = json.loads(body) if body else {}
                result = data.get("result")
                if result in ("win", "loss"):
                    log_win_loss(result)
                    self._send_json({"status": "ok"})
                else:
                    self._send_json({"error": "Resultado inválido. Use 'win' ou 'loss'"}, 400)
            else:
                self._send_json({"error": "Endpoint não encontrado"}, 404)
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    # ── Handlers ──────────────────────────────────────────────

    def _get_live(self):
        """Endpoint principal: dados ao vivo para o dashboard."""
        recent = fetch_recent_with_rolls(20)
        recent_colors = [r["color"] for r in recent]
        bet = find_best_bet(recent_colors)
        stats = _load_stats()
        total = stats.get("wins", 0) + stats.get("losses", 0)
        win_rate = round(stats["wins"] / total * 100, 1) if total > 0 else 0.0

        return {
            "recent":       recent,
            "current":      recent[-1] if recent else None,
            "next_bet":     bet,
            "total_rounds": total_results(),
            "stats": {
                "wins":        stats.get("wins", 0),
                "losses":      stats.get("losses", 0),
                "total":       total,
                "win_rate":    win_rate,
                "win_streak":  stats.get("win_streak", 0),
                "loss_streak": stats.get("loss_streak", 0),
                "history":     stats.get("history", [])[-20:],
            },
            "timestamp": datetime.now().isoformat(),
        }

    def _get_stats(self):
        stats = _load_stats()
        total = stats.get("wins", 0) + stats.get("losses", 0)
        win_rate = round(stats["wins"] / total * 100, 1) if total > 0 else 0.0
        stats["win_rate"]    = win_rate
        stats["total_bets"]  = total
        return stats

    def _get_recent(self):
        return fetch_recent_with_rolls(20)

    def _get_dashboard_data(self):
        recent = fetch_recent_with_rolls(10)
        recent_colors = [r["color"] for r in recent]
        bet = find_best_bet(recent_colors)
        return {
            "recent":       recent,
            "current":      recent[-1] if recent else None,
            "next_bet":     bet,
            "total_results": total_results(),
            "timestamp":    datetime.now().isoformat(),
        }

    def log_message(self, format, *args):
        pass  # silencia logs do servidor HTTP


# ── Stats File ────────────────────────────────────────────────

STATS_FILE = os.path.join(os.path.dirname(__file__), "data", "win_loss_stats.json")


def _load_stats():
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"wins": 0, "losses": 0, "win_streak": 0, "loss_streak": 0, "history": []}


def _save_stats(stats):
    os.makedirs(os.path.dirname(STATS_FILE), exist_ok=True)
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)


def log_win_loss(result: str):
    """Registra win ou loss e atualiza streaks."""
    stats = _load_stats()
    if result == "win":
        stats["wins"]        = stats.get("wins", 0) + 1
        stats["win_streak"]  = stats.get("win_streak", 0) + 1
        stats["loss_streak"] = 0
    else:
        stats["losses"]      = stats.get("losses", 0) + 1
        stats["loss_streak"] = stats.get("loss_streak", 0) + 1
        stats["win_streak"]  = 0

    history = stats.get("history", [])
    history.append({"result": result, "timestamp": datetime.now().isoformat()})
    stats["history"] = history[-100:]
    _save_stats(stats)


def reset_stats():
    """Reseta apenas as stats de win/loss, sem tocar no DB."""
    _save_stats({"wins": 0, "losses": 0, "win_streak": 0, "loss_streak": 0, "history": []})


def start_server(port=8765):
    server = HTTPServer(("localhost", port), DashboardAPI)
    print(f"[API] Servidor rodando em http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("[API] Servidor encerrado")
        server.shutdown()


if __name__ == "__main__":
    start_server()
