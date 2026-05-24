# -*- coding: utf-8 -*-
# monitor/realtime_monitor.py
import sys
import os
import time
import json
import io
from datetime import datetime

# Configurar stdout para UTF-8 no Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import MONITOR_INTERVAL, HISTORY_SIZE, SIGNALS_LOG_JSON
from core.db import get_last_id, fetch_recent_colors, log_signal
from strategies.strategy_manager import load_strategies
from notifier.telegram_notifier import alert_signal
from datetime import datetime


def check_signals(recent: list, by_size: dict) -> list:
    signals = []
    for size, strats in by_size.items():
        if len(recent) < size:
            continue
        tail = recent[-size:]
        for s in strats:
            if tail == s["sequence"]:
                signals.append(s)
    signals.sort(key=lambda x: -x["confidence"])
    return signals


def _log_signal_json(signal: dict, path=SIGNALS_LOG_JSON):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    log = []
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                log = json.load(f)
        except Exception:
            log = []
    log.insert(0, {
        "sequence_str":  signal["sequence_str"],
        "predict_color": signal["predict_color"],
        "confidence":    signal["confidence"],
        "occurrences":   signal["occurrences"],
        "distribution":  signal["distribution"],
        "logged_at":     datetime.now().isoformat(),
    })
    log = log[:200]  # mantém últimos 200 sinais
    with open(path, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)


def print_alert(signal: dict):
    ts = datetime.now().strftime("%H:%M:%S")
    emoji = {"preto": "⚫", "vermelho": "🔴", "branco": "⚪"}.get(signal["predict_color"], "❓")
    print(f"\n{'█'*62}")
    print(f"  🚨 SINAL DETECTADO  [{ts}]")
    print(f"  Sequência  : {signal['sequence_str']}")
    print(f"  Apostar em : {emoji} {signal['predict_color'].upper()}")
    print(f"  Confiança  : {signal['confidence']}%  |  Histórico: {signal['occurrences']}x")
    dist = " | ".join(f"{c.upper()}: {p}%" for c, p in signal["distribution"].items())
    print(f"  Distribuição: {dist}")
    print(f"{'█'*62}\n")


def run(min_confidence=70.0):
    print("\n👁️  SEQUENCE MONITOR — Iniciando monitoramento em tempo real...")
    strategies, by_size = load_strategies(min_confidence=min_confidence)
    if not strategies:
        print("[MONITOR] Nenhuma estratégia. Execute: python main.py analyze")
        return

    print(f"[MONITOR] {len(strategies)} estratégias carregadas.")
    last_id = get_last_id()
    signaled = set()

    while True:
        try:
            current_id = get_last_id()
            if current_id != last_id and current_id not in signaled:
                recent = fetch_recent_colors(limit=HISTORY_SIZE)
                signals = check_signals(recent, by_size)

                if signals:
                    for sig in signals:
                        print_alert(sig)
                        log_signal(sig["sequence_str"], sig["predict_color"], sig["confidence"])
                        _log_signal_json(sig)
                        alert_signal(sig)   # Telegram
                    signaled.add(current_id)
                else:
                    ts = datetime.now().strftime("%H:%M:%S")
                    tail = " → ".join(recent[-6:]).upper() if recent else "—"
                    print(f"  [{ts}] Cauda: {tail} | Sem sinal")

                last_id = current_id
            time.sleep(MONITOR_INTERVAL)

        except KeyboardInterrupt:
            print("\n[MONITOR] Encerrado pelo usuário.")
            break
        except Exception as e:
            print(f"[ERRO] {e}")
            time.sleep(MONITOR_INTERVAL)
