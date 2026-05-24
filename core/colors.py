# core/colors.py

def color_from_roll(value) -> str:
    """Converte valor numérico do Blaze para cor."""
    try:
        v = int(value)
    except (TypeError, ValueError):
        return str(value).strip().lower()
    if v == 0:
        return "branco"
    elif 1 <= v <= 7:
        return "vermelho"
    else:
        return "preto"

def normalize_color(value) -> str:
    """Normaliza qualquer representação para preto/vermelho/branco."""
    if isinstance(value, int):
        return color_from_roll(value)
    v = str(value).strip().lower()
    if v in ("preto", "black", "b", "14", "13", "12", "11", "10", "9", "8"):
        return "preto"
    elif v in ("vermelho", "red", "r", "v", "7", "6", "5", "4", "3", "2", "1"):
        return "vermelho"
    elif v in ("branco", "white", "w", "0"):
        return "branco"
    return v

COLOR_EMOJI = {
    "preto":    "⚫",
    "vermelho": "🔴",
    "branco":   "⚪",
}

COLOR_HEX = {
    "preto":    "#1a1a2e",
    "vermelho": "#e94560",
    "branco":   "#f5f5f5",
}
