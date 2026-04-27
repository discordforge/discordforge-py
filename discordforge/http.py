from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx

from .errors import ForgeAPIError, ForgeAuthError, ForgeNotFoundError, ForgeRateLimitError
from .ratelimit import RateLimitManager

_SDK_VERSION = "1.0.0"
_USER_AGENT = f"discordforge-python/{_SDK_VERSION} (httpx/{httpx.__version__})"


class HTTPClient:
    def __init__(
        self,
        api_key: str,
        *,
        base_url: str = "https://discordforge.org",
        timeout: float = 10.0,
        retries: int = 3,
        max_connections: int = 10,
        max_keepalive_connections: int = 5,
        seed_known_limits: bool = True,
    ) -> None:
        self._api_key = api_key
        self._retries = retries
        self._rl = RateLimitManager(seed_known_limits=seed_known_limits)
        self._client = httpx.AsyncClient(
            base_url=base_url,
            timeout=httpx.Timeout(timeout),
            limits=httpx.Limits(
                max_connections=max_connections,
                max_keepalive_connections=max_keepalive_connections,
            ),
            headers={
                "Authorization": api_key,
                "x-api-key": api_key,
                "User-Agent": _USER_AGENT,
                "Accept": "application/json",
            },
            http2=False,
        )

    async def request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        route = f"{method}:{path}"
        last_error: Exception | None = None

        for attempt in range(self._retries + 1):
            await self._rl.acquire(route)

            try:
                response = await self._client.request(
                    method,
                    path,
                    json=json,
                    params=params,
                )
            except httpx.TimeoutException as exc:
                last_error = exc
                await self._backoff(attempt)
                continue
            except httpx.NetworkError as exc:
                last_error = exc
                await self._backoff(attempt)
                continue

            self._sync_ratelimit_headers(route, response.headers)

            if response.status_code == 429:
                retry_after = self._parse_retry_after(response.headers)
                await asyncio.sleep(retry_after)
                try:
                    body = response.json()
                except Exception:
                    body = {}
                last_error = ForgeRateLimitError(retry_after, body)
                continue

            try:
                payload: Any = response.json()
            except Exception:
                payload = {"message": response.text or "non-json response"}

            if response.status_code == 401:
                raise ForgeAuthError(payload)
            if response.status_code == 404:
                raise ForgeNotFoundError(payload)
            if not response.is_success:
                message = str(
                    (payload.get("message") or payload.get("error") or response.reason_phrase)
                    if isinstance(payload, dict)
                    else payload
                )
                raise ForgeAPIError(message, response.status_code, payload)

            if isinstance(payload, dict):
                return payload
            return {"data": payload}

        raise last_error or ForgeAPIError("Request failed after retries.", 0, {})

    async def close(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> HTTPClient:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()

    def _sync_ratelimit_headers(self, route: str, headers: httpx.Headers) -> None:
        limit = headers.get("x-ratelimit-limit")
        remaining = headers.get("x-ratelimit-remaining")
        reset = headers.get("x-ratelimit-reset")
        if limit and remaining and reset:
            try:
                reset_at = float(reset) - time.time() + time.monotonic()
                self._rl.update(route, int(limit), int(remaining), reset_at)
            except ValueError:
                pass

    @staticmethod
    def _parse_retry_after(headers: httpx.Headers) -> int:
        val = headers.get("retry-after") or headers.get("x-ratelimit-reset-after")
        try:
            return max(1, int(val)) if val else 5
        except ValueError:
            return 5

    @staticmethod
    async def _backoff(attempt: int) -> None:
        await asyncio.sleep(min(2**attempt, 30))
