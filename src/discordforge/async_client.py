import asyncio
from typing import Any, Dict, Optional

from .client import DiscordForgeClient
from .models import BotInfo, CommandSyncResult, CommandsList, VoteCheckResult


class AsyncDiscordForgeClient:
    """Async wrapper around DiscordForgeClient for event-loop safe usage."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: str = "https://discordforge.org",
        timeout: float = 10.0,
    ) -> None:
        self._client = DiscordForgeClient(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
        )

    async def post_bot_stats(
        self,
        *,
        server_count: int,
        shard_count: Optional[int] = None,
        user_count: Optional[int] = None,
        voice_connections: Optional[int] = None,
    ) -> Dict[str, Any]:
        return await asyncio.to_thread(
            self._client.post_bot_stats,
            server_count=server_count,
            shard_count=shard_count,
            user_count=user_count,
            voice_connections=voice_connections,
        )

    async def check_vote(self, *, bot_id: str, user_id: str) -> VoteCheckResult:
        return await asyncio.to_thread(
            self._client.check_vote,
            bot_id=bot_id,
            user_id=user_id,
        )

    async def get_bot(self, *, bot_id: str) -> BotInfo:
        return await asyncio.to_thread(self._client.get_bot, bot_id=bot_id)

    async def sync_commands(self, *, commands: CommandsList) -> CommandSyncResult:
        return await asyncio.to_thread(self._client.sync_commands, commands=commands)

    async def sync_from_discordpy(
        self,
        *,
        command_source: Any,
        category: Optional[str] = None,
        limit: int = 200,
        strict_limit: bool = False,
    ) -> CommandSyncResult:
        return await asyncio.to_thread(
            self._client.sync_from_discordpy,
            command_source=command_source,
            category=category,
            limit=limit,
            strict_limit=strict_limit,
        )
