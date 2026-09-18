"""Token/USD pricing table. Heuristic CI runs are billed as gpt-4o-mini."""

from __future__ import annotations

# USD per 1M tokens
PRICES: dict[str, tuple[float, float]] = {
    "heuristic": (0.15, 0.60),
    "gpt-4o-mini": (0.15, 0.60),
    "gpt-4o": (2.50, 10.00),
    "gpt-4.1-mini": (0.40, 1.60),
}


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, len(text) // 4)


def cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
    inp, out = PRICES.get(model, PRICES["gpt-4o-mini"])
    return (input_tokens * inp + output_tokens * out) / 1_000_000
