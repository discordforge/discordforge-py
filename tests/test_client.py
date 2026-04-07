from datetime import datetime, timezone

import pytest

from discordforge import AsyncDiscordForgeClient, DiscordForgeClient
from discordforge.exceptions import DiscordForgeAPIError, DiscordForgeValidationError


class DummyResponse:
    def __init__(self, *, status_code=200, payload=None, text="", reason=""):
        self.status_code = status_code
        self._payload = payload if payload is not None else {}
        self.text = text
        self.reason = reason

    @property
    def ok(self):
        return 200 <= self.status_code < 300

    def json(self):
        return self._payload


class DummySession:
    def __init__(self, response):
        self.response = response
        self.last_request = None

    def request(self, **kwargs):
        self.last_request = kwargs
        return self.response


class DummyOption:
    def __init__(self, name, required):
        self.name = name
        self.required = required


class DummyCommand:
    def __init__(self, name, description, options=None):
        self.name = name
        self.description = description
        self.options = options or []


class DummyTree:
    def __init__(self, commands):
        self._commands = commands

    def get_commands(self):
        return self._commands


def test_check_vote_parses_dates():
    session = DummySession(
        DummyResponse(
            payload={
                "hasVoted": True,
                "votedAt": "2023-10-27T10:00:00.000Z",
                "nextVoteAt": "2023-10-27T22:00:00.000Z",
            }
        )
    )
    client = DiscordForgeClient(api_key="abc", session=session)

    result = client.check_vote(bot_id="123", user_id="456")

    assert result.has_voted is True
    assert result.voted_at == datetime(2023, 10, 27, 10, 0, tzinfo=timezone.utc)
    assert result.next_vote_at == datetime(2023, 10, 27, 22, 0, tzinfo=timezone.utc)


def test_sync_commands_enforces_limit():
    client = DiscordForgeClient(api_key="abc")
    commands = [{"name": "x", "description": "x"}] * 201
    with pytest.raises(DiscordForgeValidationError):
        client.sync_commands(commands=commands)


def test_get_bot_no_auth():
    session = DummySession(DummyResponse(payload={"id": "1", "name": "MyBot"}))
    client = DiscordForgeClient(session=session)

    bot = client.get_bot(bot_id="1")

    assert bot.id == "1"
    assert "Authorization" not in session.last_request["headers"]


def test_api_error_raises():
    session = DummySession(
        DummyResponse(status_code=401, payload={"message": "Unauthorized"})
    )
    client = DiscordForgeClient(api_key="bad", session=session)

    with pytest.raises(DiscordForgeAPIError):
        client.post_bot_stats(server_count=1)


@pytest.mark.asyncio
async def test_async_wrapper_works():
    session = DummySession(DummyResponse(payload={"id": "1", "name": "MyBot"}))
    sync_client = DiscordForgeClient(session=session)
    async_client = AsyncDiscordForgeClient()
    async_client._client = sync_client

    bot = await async_client.get_bot(bot_id="1")

    assert bot.name == "MyBot"


def test_sync_from_discordpy_maps_usage_and_category():
    session = DummySession(DummyResponse(payload={"success": True, "synced": 1}))
    client = DiscordForgeClient(api_key="abc", session=session)
    tree = DummyTree(
        [
            DummyCommand(
                "ban",
                "Ban a user",
                options=[DummyOption("user", True), DummyOption("reason", False)],
            )
        ]
    )

    result = client.sync_from_discordpy(command_source=tree, category="Moderation")

    assert result.success is True
    sent = session.last_request["json"]["commands"][0]
    assert sent["name"] == "ban"
    assert sent["usage"] == "<user> [reason]"
    assert sent["category"] == "Moderation"


def test_sync_from_discordpy_limit_truncates():
    session = DummySession(DummyResponse(payload={"success": True, "synced": 1}))
    client = DiscordForgeClient(api_key="abc", session=session)
    commands = [
        DummyCommand("one", "First"),
        DummyCommand("two", "Second"),
    ]

    client.sync_from_discordpy(command_source=commands, limit=1)

    sent_commands = session.last_request["json"]["commands"]
    assert len(sent_commands) == 1
    assert sent_commands[0]["name"] == "one"
