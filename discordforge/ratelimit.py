from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field

# added known rate limits per route this is seeded before the first request so we never
# have to hit a 429 to discover the limit.
# Format: "METHOD:/path" -> (limit, window_seconds)
_KNOWN_LIMITS: dict[str, tuple[int, float]] = {
    "POST:/api/bots/stats": (1, 300.0),  # 1 req / 5 min
    "GET:/api/bots/{bot_id}/votes/check": (60, 60.0),  # 60 req / min
}


@dataclass
class _Bucket:
    limit: int
    remaining: int
    window: float
    reset_at: float = field(default_factory=time.monotonic)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


class RateLimitManager:
    def __init__(self, *, seed_known_limits: bool = True) -> None:
        self._buckets: dict[str, _Bucket] = {}
        if seed_known_limits:
            self._seed_known_limits()

    def _seed_known_limits(self) -> None:
        now = time.monotonic()
        for route, (limit, window) in _KNOWN_LIMITS.items():
            self._buckets[route] = _Bucket(
                limit=limit,
                remaining=limit,
                window=window,
                reset_at=now + window,
            )

    def _resolve_route(self, route: str) -> str:
        # Normalise parameterised routes like GET:/api/bots/123/votes/check
        # back to the known-limit key with a placeholder.
        for known in _KNOWN_LIMITS:
            parts_known = known.split("/")
            parts_route = route.split("/")
            if len(parts_known) != len(parts_route):
                continue
            if all(
                k == r or k.startswith("{") for k, r in zip(parts_known, parts_route, strict=False)
            ):
                return known
        return route

    def update(self, route: str, limit: int, remaining: int, reset_at: float) -> None:
        key = self._resolve_route(route)
        window = _KNOWN_LIMITS.get(key, (limit, 60.0))[1]
        if key not in self._buckets:
            self._buckets[key] = _Bucket(
                limit=limit, remaining=remaining, window=window, reset_at=reset_at
            )
        else:
            b = self._buckets[key]
            b.limit = limit
            b.remaining = remaining
            b.reset_at = reset_at

    async def acquire(self, route: str) -> None:
        key = self._resolve_route(route)
        bucket = self._buckets.get(key)
        if bucket is None:
            return

        async with bucket.lock:
            now = time.monotonic()
            # Reset window if it has expired
            if now >= bucket.reset_at:
                bucket.remaining = bucket.limit
                bucket.reset_at = now + bucket.window

            if bucket.remaining <= 0:
                wait = bucket.reset_at - now
                await asyncio.sleep(wait)
                bucket.remaining = bucket.limit
                bucket.reset_at = time.monotonic() + bucket.window

            bucket.remaining -= 1
