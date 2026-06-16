"""Token cost estimation for LLM usage.

Prices are USD per 1M tokens (input, output). Update as models/pricing change;
unknown models estimate as $0 rather than guessing.
"""

from __future__ import annotations

# (input $/1M, output $/1M)
PRICING: dict[str, tuple[float, float]] = {
    "claude-opus-4-8": (5.0, 25.0),
    "claude-opus-4-7": (5.0, 25.0),
    "claude-opus-4-6": (5.0, 25.0),
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-haiku-4-5": (1.0, 5.0),
    "claude-fable-5": (10.0, 50.0),
}


def estimate_cost(model: str | None, input_tokens: int, output_tokens: int) -> float:
    """Estimate USD cost for the given token usage; 0.0 for unknown models."""
    rates = PRICING.get(model or "")
    if not rates:
        return 0.0
    in_rate, out_rate = rates
    return input_tokens / 1_000_000 * in_rate + output_tokens / 1_000_000 * out_rate
