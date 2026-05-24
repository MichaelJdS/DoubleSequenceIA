# coletor/blaze_collector.py
# Coleta resultados do Blaze Double via WebSocket em tempo real
# e insere no banco de dados local.

import asyncio
import json
import re
import sys, os
from datetime import datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    import websockets  # type: ignore
except ImportError:
    print("[COLETOR] Instale: pip install websockets")
    sys.exit(1)

from config import BLAZE_WS_URL, BLAZE_ROOM_ID
from core.db import insert_result, create_tables, total_results
from core.colors import color_from_roll
from notifier.telegram_notifier import send_message

PING_INTERVAL = 25  # segundos entre pings para manter conexão


def _parse_message(raw: str):
    """
    Tenta extrair dados de resultado do Blaze do payload WebSocket.
    O Blaze usa Socket.IO sobre WebSocket (formato: NUMBER["event", data]).
    """
    try:
        # Remove prefixo numérico do Socket.IO: ex "42[..." -> '["...'
        match = re.match(r"\d+(.+)", raw)
        if not match:
            return None
        payload = json.loads(match.group(1))

        if not isinstance(payload, list) or len(payload) < 2:
            return None

        event = payload[0]
        data  = payload[1]

        # Evento de resultado de rodada finalizada
        if event in ("double.tick", "double.complete", "result"):
            if isinstance(data, dict):
                roll  = data.get("roll") or data.get("color") or data.get("result")
                color = data.get("color_name") or data.get("color") or None
                if roll is not None:
                    return {"roll": int(roll), "color": color_from_roll(int(roll))}
                if color is not None:
                    return {"roll": None, "color": str(color).lower()}
    except Exception:
        pass
    return None


async def collect():
    create_tables()
    print(f"\n📡 BLAZE COLLECTOR — Conectando ao WebSocket...")
    print(f"   URL: {BLAZE_WS_URL}\n")

    retry_delay = 5
    while True:
        try:
            async with websockets.connect(
                BLAZE_WS_URL,
                ping_interval=PING_INTERVAL
            ) as ws:
                print(f"[COLETOR] ✅ Conectado! Total no DB: {total_results():,} resultados")
                retry_delay = 5

                # Solicita entrada na sala Double (Socket.IO handshake)
                await ws.send(f'42["cmd", {{"id": "subscribe", "payload": {{"room": "{BLAZE_ROOM_ID}"}}}}]')

                async for message in ws:
                    if isinstance(message, bytes):
                        message = message.decode("utf-8", errors="ignore")

                    result = _parse_message(message)
                    if result:
                        color = result["color"]
                        roll  = result.get("roll")
                        insert_result(color, roll)
                        ts = datetime.now().strftime("%H:%M:%S")
                        emoji = {"preto": "⚫", "vermelho": "🔴", "branco": "⚪"}.get(color, "❓")
                        print(f"  [{ts}] {emoji} {color.upper()}" + (f" (roll={roll})" if roll is not None else ""))

        except websockets.exceptions.ConnectionClosed as e:
            print(f"[COLETOR] Conexão fechada: {e}. Reconectando em {retry_delay}s...")
        except Exception as e:
            print(f"[COLETOR] Erro: {e}. Reconectando em {retry_delay}s...")

        await asyncio.sleep(retry_delay)
        retry_delay = min(retry_delay * 2, 60)


def run():
    try:
        asyncio.run(collect())
    except KeyboardInterrupt:
        print("\n[COLETOR] Encerrado pelo usuário.")
