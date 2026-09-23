"""
dependencies.py — Server configuration, rolling token telemetry counters, and helper state.
"""

import time
from typing import Dict, Any

# Rolling token usage tracking
_TOKEN_USAGE_LOGS: list[dict[str, Any]] = []


def record_token_usage(prompt_tokens: int, completion_tokens: int):
    """Records token consumption event with timestamp."""
    _TOKEN_USAGE_LOGS.append({
        "timestamp": time.time(),
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens
    })


def get_token_telemetry() -> Dict[str, int]:
    """Computes rolling 5-hour and 24-hour token totals."""
    now = time.time()
    five_hours_ago = now - (5 * 3600)
    twenty_four_hours_ago = now - (24 * 3600)

    tokens_5h = sum(item["total_tokens"] for item in _TOKEN_USAGE_LOGS if item["timestamp"] >= five_hours_ago)
    tokens_24h = sum(item["total_tokens"] for item in _TOKEN_USAGE_LOGS if item["timestamp"] >= twenty_four_hours_ago)

    return {
        "tokens_5h": tokens_5h,
        "tokens_24h": tokens_24h
    }
