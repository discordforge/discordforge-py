from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import TYPE_CHECKING, Any

from .types import BotStats

if TYPE_CHECKING:
    from .client import ForgeClient

log = logging.getLogger(__name__)

_MIN_INTERVAL = 300.0  # 5 minutes, this matches the API rate limit

PostCallback = Callable[[BotStats], Awaitable[None] | None]
ErrorCallback = Callable[[Exception], Awaitable[None] | None]


def _collect_stats(discord_client: Any) -> BotStats:
    server_count: int = getattr(
        getattr(discord_client, "guilds", None), "__len__", lambda: 0
    )() or len(getattr(discord_client, "guilds", []))

    shard_count: int | None = getattr(discord_client, "shard_count", None)
    if shard_count is None:
        ws = getattr(discord_client, "ws", None)
        shards = getattr(ws, "shards", None) or getattr(discord_client, "shards", None)
        if shards is not None:
            shard_count = len(shards)

    user_count: int | None = None
    users = getattr(discord_client, "users", None)
    if users is not None:
        cache = getattr(users, "cache", None)
        user_count = len(cache) if cache is not None else len(users)

    return BotStats(
        server_count=server_count,
        shard_count=shard_count,
        user_count=user_count,
    )


async def _invoke(cb: PostCallback | ErrorCallback, *args: Any) -> None:
    result = cb(*args)  # type: ignore[call-arg]
    if asyncio.isfuture(result) or asyncio.iscoroutine(result):
        await result  # type: ignore[misc]


class AutoPoster:
    def __init__(
        self,
        client: ForgeClient,
        discord_client: Any,
        *,
        interval: float = _MIN_INTERVAL,
        start_immediately: bool = True,
    ) -> None:
        if interval < _MIN_INTERVAL:
            raise ValueError(
                f"interval must be >= {_MIN_INTERVAL}s (5 minutes) to respect the API rate limit."
            )
        self._forge = client
        self._discord = discord_client
        self._interval = interval
        self._start_immediately = start_immediately
        self._task: asyncio.Task[None] | None = None
        self._on_post: list[PostCallback] = []
        self._on_error: list[ErrorCallback] = []

    def on(self, event: str, callback: PostCallback | ErrorCallback) -> AutoPoster:
        if event == "post":
            self._on_post.append(callback)  # type: ignore[arg-type]
        elif event == "error":
            self._on_error.append(callback)  # type: ignore[arg-type]
        else:
            raise ValueError(f"Unknown event '{event}'. Use 'post' or 'error'.")
        return self

    def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._task = asyncio.get_event_loop().create_task(self._run())

    def stop(self) -> None:
        if self._task:
            self._task.cancel()
            self._task = None

    def destroy(self) -> None:
        self.stop()
        self._on_post.clear()
        self._on_error.clear()

    @property
    def is_running(self) -> bool:
        return self._task is not None and not self._task.done()

    async def _run(self) -> None:
        await self._wait_for_ready()

        if self._start_immediately:
            await self._post()

        while True:
            await asyncio.sleep(self._interval)
            await self._post()

    async def _post(self) -> None:
        try:
            stats = _collect_stats(self._discord)
            await self._forge.post_stats(stats)
            for cb in self._on_post:
                await _invoke(cb, stats)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            log.warning("AutoPoster failed to post stats: %s", exc)
            if self._on_error:
                for cb in self._on_error:
                    await _invoke(cb, exc)

    async def _wait_for_ready(self) -> None:
        is_ready = getattr(self._discord, "is_ready", None)
        if callable(is_ready) and is_ready():
            return

        ready_flag = getattr(self._discord, "ready", None)
        if ready_flag is True:
            return

        wait_for = getattr(self._discord, "wait_for", None)
        if callable(wait_for):
            try:
                await wait_for("ready", timeout=300.0)  # type: ignore[misc]
                return
            except TimeoutError:
                log.warning("AutoPoster: timed out waiting for ready event, posting anyway.")
                return

        once = getattr(self._discord, "once", None)
        if callable(once):
            ready_event: asyncio.Event = asyncio.Event()
            once("ready", lambda *_: ready_event.set())
            try:
                await asyncio.wait_for(ready_event.wait(), timeout=300.0)
            except TimeoutError:
                log.warning("AutoPoster: timed out waiting for ready event, posting anyway.")
