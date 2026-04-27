from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .http import HTTPClient
from .types import BotInfo, BotStats, ClientOptions, DiscordCommand, SyncCommand, VoteMetadata

if TYPE_CHECKING:
    from collections.abc import Iterable


class ForgeClient:
    def __init__(
        self,
        api_key: str,
        bot_id: str | None = None,
        *,
        options: ClientOptions | None = None,
    ) -> None:
        if not api_key or not api_key.strip():
            raise ValueError("api_key is required.")
        opts = options or ClientOptions()
        self.bot_id = bot_id
        self._http = HTTPClient(
            api_key=api_key,
            base_url=opts.base_url,
            timeout=opts.timeout,
            retries=opts.retries,
            max_connections=opts.max_connections,
            max_keepalive_connections=opts.max_keepalive_connections,
            seed_known_limits=opts.seed_known_limits,
        )

    async def post_stats(self, stats: BotStats) -> dict[str, Any]:
        if stats.server_count < 0:
            raise ValueError("server_count must be >= 0")
        return await self._http.request("POST", "/api/bots/stats", json=stats.to_dict())

    async def check_vote(self, user_id: str, bot_id: str | None = None) -> VoteMetadata:
        bid = bot_id or self.bot_id
        if not bid:
            raise ValueError("bot_id required — pass it to ForgeClient() or check_vote().")
        if not user_id or not user_id.strip():
            raise ValueError("user_id is required.")
        data = await self._http.request(
            "GET",
            f"/api/bots/{bid}/votes/check",
            params={"userId": user_id},
        )
        return VoteMetadata.from_dict(data)

    async def get_bot(self, bot_id: str | None = None) -> BotInfo:
        bid = bot_id or self.bot_id
        if not bid:
            raise ValueError("bot_id required — pass it to ForgeClient() or get_bot().")
        data = await self._http.request("GET", f"/api/bots/{bid}")
        return BotInfo.from_dict(data)

    async def sync_commands(self, commands: list[SyncCommand]) -> dict[str, Any]:
        if not commands:
            raise ValueError("commands must not be empty.")
        if len(commands) > 200:
            raise ValueError("commands may contain at most 200 items.")
        payload = [
            c.to_dict() if hasattr(c, "to_dict") else c  # type: ignore[union-attr]
            for c in commands
        ]
        return await self._http.request(
            "POST",
            "/api/external/bots/commands",
            json={"commands": payload},
        )

    async def sync_from_discordpy(
        self,
        command_source: Any,
        *,
        category: str | None = None,
        limit: int = 200,
    ) -> dict[str, Any]:
        raw: Iterable[Any]
        get_commands = getattr(command_source, "get_commands", None)
        if callable(get_commands):
            raw = get_commands()  # type: ignore[assignment]
        elif hasattr(command_source, "__iter__"):
            raw = command_source
        else:
            raise ValueError("command_source must be iterable or expose get_commands().")

        commands: list[SyncCommand] = []
        for cmd in raw:
            name = str(getattr(cmd, "name", "") or "").strip()
            description = str(getattr(cmd, "description", "") or "").strip()
            if not name or not description:
                continue
            options = getattr(cmd, "options", None) or []
            commands.append(
                DiscordCommand(name=name, description=description, options=list(options))
            )
            if len(commands) >= limit:
                break

        return await self.sync_commands(commands)

    async def close(self) -> None:
        await self._http.close()

    async def __aenter__(self) -> ForgeClient:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.close()
