from __future__ import annotations

import httpx
import pytest
import respx

from discordforge import BotStats, ClientOptions, ForgeClient
from discordforge.errors import (
    ForgeAPIError,
    ForgeAuthError,
    ForgeNotFoundError,
)

BASE = "https://discordforge.org"


def make_client(**kwargs) -> ForgeClient:
    opts = kwargs.pop("options", ClientOptions(seed_known_limits=False))
    return ForgeClient("test-api-key", bot_id="123456789", options=opts, **kwargs)


@pytest.mark.asyncio
@respx.mock
async def test_post_stats_success():
    respx.post(f"{BASE}/api/bots/stats").mock(
        return_value=httpx.Response(200, json={"success": True})
    )
    async with make_client() as client:
        result = await client.post_stats(BotStats(server_count=100, shard_count=2, user_count=5000))
    assert result["success"] is True


@pytest.mark.asyncio
@respx.mock
async def test_post_stats_rejects_negative_server_count():
    async with make_client() as client:
        with pytest.raises(ValueError, match="server_count"):
            await client.post_stats(BotStats(server_count=-1))


@pytest.mark.asyncio
@respx.mock
async def test_check_vote_has_voted():
    respx.get(f"{BASE}/api/bots/123456789/votes/check").mock(
        return_value=httpx.Response(
            200, json={"hasVoted": True, "votedAt": "2026-04-27T10:00:00Z", "nextVoteAt": None}
        )
    )
    async with make_client() as client:
        meta = await client.check_vote("987654321")
    assert meta.has_voted is True
    assert meta.voted_at == "2026-04-27T10:00:00Z"


@pytest.mark.asyncio
@respx.mock
async def test_check_vote_not_voted():
    respx.get(f"{BASE}/api/bots/123456789/votes/check").mock(
        return_value=httpx.Response(
            200, json={"hasVoted": False, "votedAt": None, "nextVoteAt": None}
        )
    )
    async with make_client() as client:
        meta = await client.check_vote("111")
    assert meta.has_voted is False


@pytest.mark.asyncio
async def test_check_vote_requires_bot_id():
    async with ForgeClient("test-api-key") as client:
        with pytest.raises(ValueError, match="bot_id"):
            await client.check_vote("111")


@pytest.mark.asyncio
@respx.mock
async def test_get_bot():
    respx.get(f"{BASE}/api/bots/123456789").mock(
        return_value=httpx.Response(
            200, json={"id": "123456789", "name": "TestBot", "voteCount": 42, "serverCount": 500}
        )
    )
    async with make_client() as client:
        info = await client.get_bot()
    assert info.name == "TestBot"
    assert info.vote_count == 42


@pytest.mark.asyncio
@respx.mock
async def test_sync_commands_success():
    from discordforge import DiscordCommand

    respx.post(f"{BASE}/api/external/bots/commands").mock(
        return_value=httpx.Response(200, json={"success": True, "synced": 2})
    )
    cmds = [
        DiscordCommand(name="ping", description="Ping the bot"),
        DiscordCommand(name="help", description="Get help"),
    ]
    async with make_client() as client:
        result = await client.sync_commands(cmds)
    assert result["synced"] == 2


@pytest.mark.asyncio
async def test_sync_commands_rejects_empty():
    async with make_client() as client:
        with pytest.raises(ValueError, match="empty"):
            await client.sync_commands([])


@pytest.mark.asyncio
async def test_sync_commands_rejects_over_200():
    from discordforge import DiscordCommand

    cmds = [DiscordCommand(name=f"cmd{i}", description="desc") for i in range(201)]
    async with make_client() as client:
        with pytest.raises(ValueError, match="200"):
            await client.sync_commands(cmds)


@pytest.mark.asyncio
@respx.mock
async def test_401_raises_forge_auth_error():
    respx.post(f"{BASE}/api/bots/stats").mock(
        return_value=httpx.Response(401, json={"message": "Unauthorized"})
    )
    async with make_client() as client:
        with pytest.raises(ForgeAuthError):
            await client.post_stats(BotStats(server_count=1))


@pytest.mark.asyncio
@respx.mock
async def test_404_raises_forge_not_found():
    respx.get(f"{BASE}/api/bots/123456789").mock(
        return_value=httpx.Response(404, json={"message": "Not found"})
    )
    async with make_client() as client:
        with pytest.raises(ForgeNotFoundError):
            await client.get_bot()


@pytest.mark.asyncio
@respx.mock
async def test_500_raises_forge_api_error():
    respx.post(f"{BASE}/api/bots/stats").mock(
        return_value=httpx.Response(500, json={"message": "Internal Server Error"})
    )
    opts = ClientOptions(retries=0)
    async with make_client(options=opts) as client:
        with pytest.raises(ForgeAPIError) as exc_info:
            await client.post_stats(BotStats(server_count=1))
    assert exc_info.value.status == 500


@pytest.mark.asyncio
@respx.mock
async def test_rate_limit_retries():
    call_count = 0

    def handler(request):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return httpx.Response(
                429, headers={"retry-after": "0"}, json={"message": "rate limited"}
            )
        return httpx.Response(200, json={"success": True})

    respx.post(f"{BASE}/api/bots/stats").mock(side_effect=handler)
    async with make_client() as client:
        result = await client.post_stats(BotStats(server_count=10))
    assert result["success"] is True
    assert call_count == 2


@pytest.mark.asyncio
@respx.mock
async def test_context_manager_closes():
    respx.post(f"{BASE}/api/bots/stats").mock(
        return_value=httpx.Response(200, json={"success": True})
    )
    client = make_client()
    async with client:
        await client.post_stats(BotStats(server_count=1))
