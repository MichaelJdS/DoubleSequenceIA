#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# start.py — Inicia todo o sistema DoubleSequenceIA de uma vez
# Abre: Coletor + Analisador + Monitor + Dashboard no navegador

import subprocess
import sys
import os
import time
import threading
import json
import http.server
import socketserver
import webbrowser
import io
from datetime import datetime

# Forcar UTF-8 no stdout/stderr do Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(ROOT, "data")
DB_PATH  = os.path.join(DATA_DIR, "blaze_double.db")
STRATS   = os.path.join(DATA_DIR, "strategies.json")
DASH_DIR  = os.path.join(ROOT, "dashboard")
DASH_PORT = 8766   # servidor de arquivos estaticos
API_PORT  = 8765   # API JSON

os.makedirs(DATA_DIR, exist_ok=True)

PURPLE = "\033[95m"
CYAN   = "\033[96m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

def banner():
    print(f"""
{PURPLE}{BOLD}
  ____  ____  _   _ ____  _     _____
 | __ )|  _ \| | | |  _ \| |   | ____|
 |  _ \| | | | | | | |_) | |   |  _|
 | |_) | |_| | |_| |  _ <| |___| |___
 |____/|____/ \___/|_|_\_|_____|_____|
  SequenceIA  — Double Pattern Engine
{RESET}{CYAN}  Pattern Recognition Engine v2.0{RESET}
{PURPLE}{'='*54}{RESET}
""")

def log(tag, msg, color=CYAN):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"  {color}{BOLD}[{tag}]{RESET} {color}{msg}{RESET}  {YELLOW}[{ts}]{RESET}")

def step(n, total, msg):
    bar_len = 20
    filled  = round(n / total * bar_len)
    bar     = "#" * filled + "-" * (bar_len - filled)
    print(f"\r  {PURPLE}[{bar}]{RESET} {CYAN}{msg:<40}{RESET}", end="", flush=True)
    if n == total:
        print()

# ── Verifica dependências ─────────────────────────────────
def check_deps():
    log("DEPS", "Verificando dependências...")
    missing = []
    for pkg in ["websockets", "requests"]:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        log("DEPS", f"Instalando: {', '.join(missing)}", YELLOW)
        subprocess.run([sys.executable, "-m", "pip", "install"] + missing,
                       capture_output=True)
        log("DEPS", "Dependências instaladas!", GREEN)
    else:
        log("DEPS", "Todas as dependências OK", GREEN)

# ── Análise inicial ───────────────────────────────────────
def run_analysis():
    if not os.path.exists(DB_PATH):
        log("ANALYZE", "DB não encontrado — aguardando coletor...", YELLOW)
        return False

    log("ANALYZE", "Analisando banco de dados...")
    try:
        result = subprocess.run(
            [sys.executable, "main.py", "analyze"],
            cwd=ROOT, capture_output=True, text=True, timeout=120
        )
        if result.returncode == 0:
            # Conta estratégias geradas
            count = 0
            if os.path.exists(STRATS):
                with open(STRATS, "r") as f:
                    data = json.load(f)
                    count = len(data)
            log("ANALYZE", f"{count} estratégias geradas com sucesso!", GREEN)
            return True
        else:
            log("ANALYZE", f"Aviso: {result.stderr[:100]}", YELLOW)
            return False
    except subprocess.TimeoutExpired:
        log("ANALYZE", "Timeout na análise — banco muito grande?", YELLOW)
        return False
    except Exception as e:
        log("ANALYZE", f"Erro: {e}", RED)
        return False

# ── Servidor do Dashboard ─────────────────────────────────
def start_dashboard_server():
    class Handler(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=ROOT, **kwargs)
        def log_message(self, format, *args):
            pass  # silencia logs do servidor

    try:
        socketserver.TCPServer.allow_reuse_address = True
        with socketserver.TCPServer(("", DASH_PORT), Handler) as httpd:
            httpd.serve_forever()
    except OSError as e:
        log("DASH", f"Porta {DASH_PORT} em uso ou erro: {e}", YELLOW)

# -- Servidor de API -----------------------------------------------
def _start_api_server():
    try:
        from api_server import start_server
        start_server(port=API_PORT)
    except Exception as e:
        log("API", f"Erro ao iniciar API: {e}", RED)

# ── Subprocessos ──────────────────────────────────────────
processes = []

def start_process(name, args, color=CYAN):
    log(name, f"Iniciando: {' '.join(args[-2:])}", color)
    p = subprocess.Popen(
        args, cwd=ROOT,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, bufsize=1
    )
    processes.append((name, p))

    def stream(proc, tag, c):
        for line in proc.stdout:
            line = line.rstrip()
            if line:
                ts = datetime.now().strftime("%H:%M:%S")
                print(f"  {c}[{tag}]{RESET} {line}  {YELLOW}[{ts}]{RESET}")
    threading.Thread(target=stream, args=(p, name, color), daemon=True).start()
    return p

# -- Abre Dashboard -----------------------------------------------
def open_dashboard():
    url = f"http://localhost:{DASH_PORT}/index.html"
    log("DASH", f"Abrindo dashboard -> {url}", GREEN)
    time.sleep(1.5)
    webbrowser.open(url)

# -- Shutdown -----------------------------------------------
def shutdown():
    print(f"\n  Encerrando todos os processos...")
    for name, p in processes:
        try:
            p.terminate()
            log(name, "Encerrado", YELLOW)
        except Exception:
            pass
    print(f"  Sistema encerrado.\n")

# ═════════════════════════════════════════════════════════
def main():
    banner()

    print(f"  {PURPLE}{'─'*54}{RESET}")
    print(f"  {BOLD}INICIANDO SISTEMA — {datetime.now().strftime('%d/%m/%Y %H:%M')}{RESET}")
    print(f"  {PURPLE}{'─'*54}{RESET}\n")

    # 1. Dependências
    step(0, 5, "Verificando dependências...")
    check_deps()
    step(1, 5, "Dependências OK")
    print()

    # 2. Análise do DB (se existir)
    step(1, 5, "Analisando banco de dados...")
    has_strats = run_analysis()
    step(2, 5, "Análise concluída")
    print()

    # 3. Servidor do dashboard (arquivos estaticos)
    step(2, 5, "Iniciando servidor do dashboard...")
    dash_thread = threading.Thread(target=start_dashboard_server, daemon=True)
    dash_thread.start()
    time.sleep(0.8)
    log("DASH", f"Servidor rodando em http://localhost:{DASH_PORT}", GREEN)
    step(3, 5, "Dashboard pronto")
    print()

    # 4. API Server (JSON endpoints)
    step(3, 5, "Iniciando servidor de API...")
    api_thread = threading.Thread(target=_start_api_server, daemon=True)
    api_thread.start()
    time.sleep(0.5)
    log("API", f"API rodando em http://localhost:{API_PORT}", GREEN)
    step(4, 5, "API pronta")
    print()

    # 5. Coletor WebSocket
    step(4, 5, "Iniciando coletor Blaze...")
    start_process("COLETOR", [sys.executable, "main.py", "collect"], CYAN)
    time.sleep(2)
    step(5, 5, "Coletor ativo")
    print()

    # 6. Monitor em tempo real
    step(5, 5, "Iniciando monitor...")
    start_process("MONITOR", [sys.executable, "main.py", "monitor"], GREEN)
    print()

    # Abrir dashboard
    open_dashboard()

    print(f"\n  {'='*54}")
    print(f"  [OK] SISTEMA ONLINE!")
    print(f"  {'='*54}")
    print(f"  Dashboard  -> http://localhost:{DASH_PORT}/index.html")
    print(f"  API JSON   -> http://localhost:{API_PORT}")
    print(f"  Coletor    -> WebSocket Blaze ativo")
    print(f"  Monitor    -> Detectando padroes em tempo real")
    if has_strats and os.path.exists(STRATS):
        with open(STRATS) as f:
            n = len(json.load(f))
        print(f"  Estrategias-> {n} carregadas")
    print(f"\n  Pressione Ctrl+C para encerrar tudo.\n")
    print(f"  {'-'*54}")
    print(f"  LOGS EM TEMPO REAL:")
    print(f"  {'-'*54}\n")

    # Fica vivo monitorando
    try:
        while True:
            time.sleep(1)
            # Reagenda re-análise a cada 30 min
            if int(time.time()) % 1800 == 0:
                log("ANALYZE", "Re-analisando DB (ciclo 30min)...", YELLOW)
                threading.Thread(target=run_analysis, daemon=True).start()
    except KeyboardInterrupt:
        shutdown()

if __name__ == "__main__":
    main()
