# ============================================================
#  config.py — Configurações Centralizadas
#  DoubleSequenceIA
# ============================================================

import os

# ── Banco de Dados ──────────────────────────────────────────
DB_PATH = os.path.join("data", "blaze_double.db")

# ── Coleta (Blaze WebSocket) ────────────────────────────────
BLAZE_WS_URL = "wss://api-v2.blaze.com/replication/?EIO=3&transport=websocket"
BLAZE_ROOM_ID = "ae978cff-4e7e-4d0e-803e-d21cf0c69ee1"   # Double room

# ── Análise de Sequências ───────────────────────────────────
SEQ_SIZES         = [4, 5, 6]
MIN_OCCURRENCES   = 5       # mínimo de vezes que a sequência deve aparecer
MIN_CONFIDENCE    = 0.70    # 70% de confiança mínima

# ── Monitor em Tempo Real ───────────────────────────────────
MONITOR_INTERVAL  = 5       # segundos entre verificações
HISTORY_SIZE      = 10      # quantidade de resultados recentes a manter

# ── Telegram ────────────────────────────────────────────────
TELEGRAM_TOKEN    = "6674179143:AAEUv9Yzu0LCqAsg05tUEcptDm8bRXBih50"
TELEGRAM_CHAT_ID  = "5662495395"

# ── Dashboard ───────────────────────────────────────────────
STRATEGIES_JSON   = os.path.join("data", "strategies.json")
SIGNALS_LOG_JSON  = os.path.join("data", "signals_log.json")
