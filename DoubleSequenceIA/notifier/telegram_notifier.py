# notifier/telegram_notifier.py
import requests
import json
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
from core.colors import COLOR_EMOJI


def send_message(text: str, parse_mode="HTML") -> bool:
    if not TELEGRAM_TOKEN or "SEU_BOT" in TELEGRAM_TOKEN:
        print(f"[TELEGRAM] (não configurado) {text[:80]}")
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": parse_mode}
    try:
        r = requests.post(url, json=payload, timeout=5)
        return r.status_code == 200
    except Exception as e:
        print(f"[TELEGRAM] Erro ao enviar: {e}")
        return False


def alert_signal(signal: dict) -> bool:
    emoji = COLOR_EMOJI.get(signal["predict_color"], "❓")
    dist = "\n".join(
        f"  {COLOR_EMOJI.get(c, c)} {c.upper()}: <b>{p}%</b>"
        for c, p in signal["distribution"].items()
    )

    bar_total = 20
    filled = round(signal["confidence"] / 100 * bar_total)
    bar = "█" * filled + "░" * (bar_total - filled)

    text = (
        f"🚨 <b>SINAL DETECTADO — BLAZE DOUBLE</b>\n"
        f"{'─'*32}\n"
        f"📋 <b>Sequência:</b>\n"
        f"   <code>{signal['sequence_str']}</code>\n\n"
        f"🎯 <b>Apostar em:</b> {emoji} <b>{signal['predict_color'].upper()}</b>\n\n"
        f"📊 <b>Confiança:</b> {signal['confidence']}%\n"
        f"   <code>[{bar}]</code>\n\n"
        f"📈 <b>Distribuição histórica:</b>\n{dist}\n\n"
        f"🔁 <b>Ocorrências:</b> {signal['occurrences']}x no histórico\n"
        f"{'─'*32}\n"
        f"⚡ <i>DoubleSequenceIA</i>"
    )
    return send_message(text)


def alert_analysis_done(total_strategies: int, by_size: dict) -> bool:
    lines = "\n".join(
        f"  • {size} cores: <b>{count}</b> estratégias"
        for size, count in sorted(by_size.items())
    )
    text = (
        f"✅ <b>ANÁLISE CONCLUÍDA</b>\n"
        f"{'─'*32}\n"
        f"📦 Total de estratégias geradas: <b>{total_strategies}</b>\n\n"
        f"{lines}\n"
        f"{'─'*32}\n"
        f"⚡ <i>DoubleSequenceIA</i>"
    )
    return send_message(text)
