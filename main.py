#!/usr/bin/env python3
# main.py — Entry point DoubleSequenceIA
import sys, os

HELP = """
╔══════════════════════════════════════════╗
║        DoubleSequenceIA — Comandos       ║
╠══════════════════════════════════════════╣
║  python main.py analyze   — Analisa DB  ║
║  python main.py monitor   — Tempo real  ║
║  python main.py collect   — Coleta WS   ║
║  python main.py report    — Relatório   ║
╚══════════════════════════════════════════╝
"""

def cmd_analyze():
    from core.db import load_all_colors, create_tables
    from core.sequence_analyzer import analyze_sequences
    from strategies.strategy_manager import save_strategies, export_json, print_report
    from notifier.telegram_notifier import alert_analysis_done
    from collections import defaultdict

    create_tables()
    colors = load_all_colors()
    if not colors:
        print("[ERRO] Sem dados no banco. Rode: python main.py collect")
        return

    strategies = analyze_sequences(colors)
    if not strategies:
        print("[AVISO] Nenhuma estratégia atingiu os critérios. Ajuste config.py")
        return

    print_report(strategies)
    save_strategies(strategies)
    export_json(strategies)

    by_size = defaultdict(int)
    for s in strategies:
        by_size[s["sequence_size"]] += 1
    alert_analysis_done(len(strategies), dict(by_size))


def cmd_monitor():
    from monitor.realtime_monitor import run
    run()


def cmd_collect():
    from coletor.blaze_collector import run
    run()


def cmd_report():
    from strategies.strategy_manager import load_strategies, print_report
    strategies, _ = load_strategies()
    if strategies:
        print_report(strategies, top_n=50)
    else:
        print("[ERRO] Nenhuma estratégia. Rode: python main.py analyze")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(HELP)
        sys.exit(0)

    cmd = sys.argv[1].lower()
    if cmd == "analyze":
        cmd_analyze()
    elif cmd == "monitor":
        cmd_monitor()
    elif cmd == "collect":
        cmd_collect()
    elif cmd == "report":
        cmd_report()
    else:
        print(f"[ERRO] Comando desconhecido: {cmd}")
        print(HELP)
