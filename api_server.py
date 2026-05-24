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

from config import SIGNALS_LOG_JSON
from core.db import fetch_recent_colors, get_all_results
from strategies.strategy_manager import load_strategies


class DashboardAPI(BaseHTTPRequestHandler):
    def do_GET(self):
        """Manipular requisições GET"""
        parsed = urlparse(self.path)
        path = parsed.path
        
        # CORS
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        
        try:
            if path == "/api/dashboard-data":
                self.get_dashboard_data()
            elif path == "/api/stats":
                self.get_stats()
            elif path == "/api/recent":
                self.get_recent_results()
            else:
                self.wfile.write(json.dumps({"error": "Endpoint não encontrado"}).encode())
        except Exception as e:
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def do_POST(self):
        """Manipular requisições POST"""
        parsed = urlparse(self.path)
        path = parsed.path
        
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode()
        
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        
        try:
            if path == "/api/reset-stats":
                self.reset_stats()
            elif path == "/api/log-result":
                data = json.loads(body) if body else {}
                self.log_result(data)
            else:
                self.wfile.write(json.dumps({"error": "Endpoint não encontrado"}).encode())
        except Exception as e:
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def do_OPTIONS(self):
        """Manipular CORS preflight"""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def get_dashboard_data(self):
        """Retornar dados do dashboard"""
        try:
            # Pegar últimos 10 resultados
            recent = fetch_recent_colors(10)
            
            # Pegar estratégias
            strategies = load_strategies()
            
            # Identificar próxima estratégia
            next_bet = None
            if len(recent) >= 4:
                recent_seq = tuple([c[0] for c in recent[-6:]])
                for strat in strategies:
                    seq = tuple(strat.get("sequence", []))
                    if recent_seq[-len(seq):] == seq:
                        next_bet = {
                            "color": strat.get("prediction"),
                            "confidence": strat.get("confidence", 0),
                            "occurrences": strat.get("total_occurrences", 0)
                        }
                        break
            
            data = {
                "recent": [{"color": c[0], "id": c[1]} for c in recent],
                "current": recent[0][0] if recent else None,
                "next_bet": next_bet,
                "total_results": len(get_all_results()),
                "timestamp": datetime.now().isoformat()
            }
            
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
        except Exception as e:
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def get_stats(self):
        """Retornar estatísticas de win/loss"""
        try:
            stats = load_stats()
            total = stats.get("wins", 0) + stats.get("losses", 0)
            win_rate = (stats.get("wins", 0) / total * 100) if total > 0 else 0
            
            stats["win_rate"] = round(win_rate, 2)
            stats["total_bets"] = total
            
            self.wfile.write(json.dumps(stats, ensure_ascii=False).encode("utf-8"))
        except Exception as e:
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def get_recent_results(self):
        """Retornar últimos 20 resultados"""
        try:
            results = get_all_results()[-20:]
            data = [
                {
                    "id": r[0],
                    "color": r[1],
                    "timestamp": r[2]
                }
                for r in reversed(results)
            ]
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
        except Exception as e:
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def reset_stats(self):
        """Resetar estatísticas de win/loss"""
        try:
            reset_stats()
            self.wfile.write(json.dumps({"status": "ok", "message": "Stats resetadas"}).encode())
        except Exception as e:
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def log_result(self, data):
        """Registrar resultado de aposta"""
        try:
            result = data.get("result")  # "win" ou "loss"
            if result in ["win", "loss"]:
                log_win_loss(result)
                self.wfile.write(json.dumps({"status": "ok"}).encode())
            else:
                self.wfile.write(json.dumps({"error": "Invalid result"}).encode())
        except Exception as e:
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def log_message(self, format, *args):
        """Suprimir logs padrão do servidor"""
        pass


def load_stats():
    """Carregar estatísticas de win/loss"""
    stats_file = os.path.join("data", "win_loss_stats.json")
    if os.path.exists(stats_file):
        try:
            with open(stats_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"wins": 0, "losses": 0, "streak": 0, "history": []}


def save_stats(stats):
    """Salvar estatísticas de win/loss"""
    os.makedirs("data", exist_ok=True)
    stats_file = os.path.join("data", "win_loss_stats.json")
    with open(stats_file, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)


def log_win_loss(result):
    """Registrar win ou loss"""
    stats = load_stats()
    
    if result == "win":
        stats["wins"] = stats.get("wins", 0) + 1
        stats["streak"] = stats.get("streak", 0) + 1
    else:
        stats["losses"] = stats.get("losses", 0) + 1
        stats["streak"] = 0
    
    # Manter histórico dos últimos 100
    history = stats.get("history", [])
    history.append({
        "result": result,
        "timestamp": datetime.now().isoformat()
    })
    stats["history"] = history[-100:]
    
    save_stats(stats)


def reset_stats():
    """Resetar estatísticas sem afetar o DB"""
    save_stats({"wins": 0, "losses": 0, "streak": 0, "history": []})


def start_server(port=8765):
    """Iniciar servidor HTTP"""
    server = HTTPServer(("localhost", port), DashboardAPI)
    print(f"[API] Servidor rodando em http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("[API] Servidor encerrado")
        server.shutdown()


if __name__ == "__main__":
    start_server()
