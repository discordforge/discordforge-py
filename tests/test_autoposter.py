from __future__ import annotations

import asyncio

import httpx
import pytest
import respx

from discordforge import AutoPoster, BotStats, ForgeClient
from discordforge.autoposter import _collect_stats
from discordforge.types import ClientOptions

BASE = "https://discordforge.org"


class FakeGuild:
    pass


class FakeDiscordClient:
    def __init__(self, guild_count: int = 10, shard_count: int | None = 2):
        self.guilds = [FakeGuild() for _ in range(guild_count)]
        self.shard_count = shard_count
        self._ready = True

    def is_ready(self) -> bool:
        return self._ready


class NotReadyClient(FakeDiscordClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._ready = False
        self._listeners: list = []

    def is_ready(self) -> bool:
        return False

    async def wait_for(self, event: str, *, timeout: float = 300.0) -> None:
        await asyncio.sleep(0)


def test_collect_stats_basic():
    client = FakeDiscordClient(guild_count=50, shard_count=4)
    stats = _collect_stats(client)
    assert stats.server_count == 50
    assert stats.shard_count == 4


def test_collect_stats_no_shards():
    client = FakeDiscordClient(guild_count=5, shard_count=None)
    stats = _collect_stats(client)
    assert stats.server_count == 5
    assert stats.shard_count is None


def test_autoposter_rejects_short_interval():
    forge = ForgeClient("key", bot_id="123", options=ClientOptions(seed_known_limits=False))
    discord = FakeDiscordClient()
    with pytest.raises(ValueError, match="interval"):
        AutoPoster(forge, discord, interval=60.0)


@pytest.mark.asyncio
@respx.mock
async def test_autoposter_posts_on_start():
    posted: list[BotStats] = []
    done = asyncio.Event()

    respx.post(f"{BASE}/api/bots/stats").mock(
        return_value=httpx.Response(200, json={"success": True})
    )

    forge = ForgeClient("key", bot_id="123", options=ClientOptions(seed_known_limits=False))
    discord = FakeDiscordClient(guild_count=25)
    poster = AutoPoster(forge, discord, interval=300.0, start_immediately=True)

    async def on_post(stats: BotStats) -> None:
        posted.append(stats)
        done.set()

    poster.on("post", on_post)
    poster.start()

    await asyncio.wait_for(done.wait(), timeout=5.0)
    poster.stop()
    await forge.close()

    assert len(posted) == 1
    assert posted[0].server_count == 25


@pytest.mark.asyncio
@respx.mock
async def test_autoposter_calls_error_callback_on_failure():
    errors: list[Exception] = []

    respx.post(f"{BASE}/api/bots/stats").mock(
        return_value=httpx.Response(500, json={"message": "fail"})
    )

    forge = ForgeClient(
        "key", bot_id="123", options=ClientOptions(retries=0, seed_known_limits=False)
    )
    discord = FakeDiscordClient()
    poster = AutoPoster(forge, discord, interval=300.0, start_immediately=True)

    async def on_error(exc: Exception) -> None:
        errors.append(exc)
        poster.stop()

    poster.on("error", on_error)
    poster.start()

    import contextlib

    with contextlib.suppress(TimeoutError, asyncio.CancelledError):
        await asyncio.wait_for(asyncio.shield(poster._task), timeout=5.0)  # type: ignore[arg-type]
    await forge.close()

    assert len(errors) >= 1


@pytest.mark.asyncio
@respx.mock
async def test_autoposter_waits_for_ready():
    posted: list[BotStats] = []
    done = asyncio.Event()

    respx.post(f"{BASE}/api/bots/stats").mock(
        return_value=httpx.Response(200, json={"success": True})
    )

    forge = ForgeClient("key", bot_id="123", options=ClientOptions(seed_known_limits=False))
    discord = NotReadyClient(guild_count=10)
    poster = AutoPoster(forge, discord, interval=300.0, start_immediately=True)

    async def on_post(stats: BotStats) -> None:
        posted.append(stats)
        done.set()

    poster.on("post", on_post)
    poster.start()

    await asyncio.wait_for(done.wait(), timeout=5.0)
    poster.stop()
    await forge.close()

    assert len(posted) == 1


def test_autoposter_is_running():
    forge = ForgeClient("key", bot_id="123", options=ClientOptions(seed_known_limits=False))
    discord = FakeDiscordClient()
    poster = AutoPoster(forge, discord, interval=300.0)
    assert not poster.is_running
    poster.start()
    assert poster.is_running
    poster.stop()
    assert not poster.is_running


def test_autoposter_destroy_clears_listeners():
    forge = ForgeClient("key", bot_id="123", options=ClientOptions(seed_known_limits=False))
    discord = FakeDiscordClient()
    poster = AutoPoster(forge, discord, interval=300.0)
    poster.on("post", lambda s: None)
    poster.on("error", lambda e: None)
    poster.destroy()
    assert not poster._on_post
    assert not poster._on_error
    assert not poster.is_running
