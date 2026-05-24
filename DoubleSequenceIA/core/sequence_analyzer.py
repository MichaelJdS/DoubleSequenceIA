# core/sequence_analyzer.py
import json
from collections import defaultdict
from datetime import datetime
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import SEQ_SIZES, MIN_OCCURRENCES, MIN_CONFIDENCE


def analyze_sequences(colors: list, seq_sizes=None, min_occurrences=None,
                      min_confidence=None) -> list:
    if seq_sizes is None:       seq_sizes = SEQ_SIZES
    if min_occurrences is None: min_occurrences = MIN_OCCURRENCES
    if min_confidence is None:  min_confidence = MIN_CONFIDENCE

    seq_stats = defaultdict(lambda: defaultdict(int))
    total = len(colors)
    max_size = max(seq_sizes)

    print(f"[ANALYZER] Varrendo {total:,} resultados...")

    for i in range(total - max_size - 1):
        for size in seq_sizes:
            if i + size >= total:
                continue
            seq = tuple(colors[i: i + size])
            next_color = colors[i + size]
            seq_stats[seq][next_color] += 1
            seq_stats[seq]["__total__"] += 1

    print(f"[ANALYZER] {len(seq_stats):,} sequências únicas encontradas. Filtrando...")

    strategies = []
    for seq, outcomes in seq_stats.items():
        total_seq = outcomes["__total__"]
        if total_seq < min_occurrences:
            continue

        best_color = max(
            (c for c in outcomes if c != "__total__"),
            key=lambda c: outcomes[c],
            default=None
        )
        if not best_color:
            continue

        confidence = outcomes[best_color] / total_seq
        if confidence < min_confidence:
            continue

        distribution = {
            c: round(outcomes[c] / total_seq * 100, 1)
            for c in ["preto", "vermelho", "branco"]
            if c in outcomes
        }

        strategies.append({
            "sequence":       list(seq),
            "sequence_size":  len(seq),
            "sequence_str":   " → ".join(seq).upper(),
            "occurrences":    total_seq,
            "predict_color":  best_color,
            "predict_count":  outcomes[best_color],
            "confidence":     round(confidence * 100, 2),
            "distribution":   distribution,
            "created_at":     datetime.now().isoformat(),
        })

    strategies.sort(key=lambda x: (-x["confidence"], -x["occurrences"]))
    print(f"[ANALYZER] {len(strategies)} estratégias válidas geradas.")
    return strategies
