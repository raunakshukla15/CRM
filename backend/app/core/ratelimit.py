"""Tiny in-memory sliding-window rate limiter for auth endpoints.

Per-process memory: correct for single-instance dev; with multiple workers each
worker enforces its own bucket (stricter overall, never looser). For clustered
production use a Redis-backed limiter.
"""

import time
from collections import defaultdict, deque

_buckets: dict[str, deque[float]] = defaultdict(deque)


def is_rate_limited(key: str, max_attempts: int, window_s: int) -> bool:
    now = time.monotonic()
    bucket = _buckets[key]
    while bucket and bucket[0] <= now - window_s:
        bucket.popleft()
    if len(bucket) >= max_attempts:
        return True
    bucket.append(now)
    return False
