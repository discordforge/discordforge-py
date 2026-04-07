from typing import Any, Dict, Iterable, List, Optional

import requests

from .exceptions import DiscordForgeAPIError, DiscordForgeValidationError
from .models import (
    BotInfo,
    BotStatsUpdate,
    CommandSyncResult,
    CommandsList,
    VoteCheckResult,
    parse_iso_datetime,
)


class DiscordForgeClient:
    """Simple, typed client for DiscordForge REST API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: str = "https://discordforge.org",
        timeout: float = 10.0,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session = session or requests.Session()

    def post_bot_stats(
        self,
        *,
        server_count: int,
        shard_count: Optional[int] = None,
        user_count: Optional[int] = None,
        voice_connections: Optional[int] = None,
    ) -> Dict[str, Any]:
        self._require_api_key()
        _ensure_non_negative("server_count", server_count)
        _ensure_optional_non_negative("shard_count", shard_count)
        _ensure_optional_non_negative("user_count", user_count)
        _ensure_optional_non_negative("voice_connections", voice_connections)

        stats = BotStatsUpdate(
            server_count=server_count,
            shard_count=shard_count,
            user_count=user_count,
            voice_connections=voice_connections,
        )
        return self._request(
            "POST",
            "/api/bots/stats",
            json=stats.to_payload(),
            auth_required=True,
        )

    def check_vote(self, *, bot_id: str, user_id: str) -> VoteCheckResult:
        self._require_api_key()
        _ensure_not_blank("bot_id", bot_id)
        _ensure_not_blank("user_id", user_id)
        data = self._request(
            "GET",
            f"/api/bots/{bot_id}/votes/check",
            params={"userId": user_id},
            auth_required=True,
        )
        return VoteCheckResult(
            has_voted=bool(data.get("hasVoted", False)),
            voted_at=parse_iso_datetime(data.get("votedAt")),
            next_vote_at=parse_iso_datetime(data.get("nextVoteAt")),
            raw=data,
        )

    def get_bot(self, *, bot_id: str) -> BotInfo:
        _ensure_not_blank("bot_id", bot_id)
        data = self._request("GET", f"/api/bots/{bot_id}", auth_required=False)
        return BotInfo(data=data)

    def sync_commands(self, *, commands: CommandsList) -> CommandSyncResult:
        self._require_api_key()
        if not isinstance(commands, list):
            raise DiscordForgeValidationError("commands must be a list")
        if not commands:
            raise DiscordForgeValidationError("commands must not be empty")
        if len(commands) > 200:
            raise DiscordForgeValidationError("commands may contain at most 200 items")

        for index, command in enumerate(commands):
            if not isinstance(command, dict):
                raise DiscordForgeValidationError(f"commands[{index}] must be an object")
            if not command.get("name") or not command.get("description"):
                raise DiscordForgeValidationError(
                    f"commands[{index}] requires both 'name' and 'description'"
                )

        data = self._request(
            "POST",
            "/api/external/bots/commands",
            json={"commands": commands},
            auth_required=True,
        )
        return CommandSyncResult(
            success=bool(data.get("success", False)),
            synced=int(data.get("synced", 0)),
            raw=data,
        )

    def sync_from_discordpy(
        self,
        *,
        command_source: Any,
        category: Optional[str] = None,
        limit: int = 200,
        strict_limit: bool = False,
    ) -> CommandSyncResult:
        """
        Sync commands directly from discord.py command objects.

        `command_source` can be:
        - `bot.tree` or any object with `get_commands()`
        - an iterable of command objects
        """
        _ensure_positive("limit", limit)
        commands = self._map_discordpy_commands(command_source=command_source, category=category)
        if len(commands) > limit:
            if strict_limit:
                raise DiscordForgeValidationError(
                    f"mapped commands exceed limit {limit}: {len(commands)}"
                )
            commands = commands[:limit]
        return self.sync_commands(commands=commands)

    def _map_discordpy_commands(
        self,
        *,
        command_source: Any,
        category: Optional[str],
    ) -> List[Dict[str, Any]]:
        raw_commands: Iterable[Any]
        get_commands = getattr(command_source, "get_commands", None)
        if callable(get_commands):
            raw_commands = get_commands()
        elif isinstance(command_source, Iterable):
            raw_commands = command_source
        else:
            raise DiscordForgeValidationError(
                "command_source must be an iterable or expose get_commands()"
            )

        mapped: List[Dict[str, Any]] = []
        for index, command in enumerate(raw_commands):
            name = str(getattr(command, "name", "") or "").strip()
            description = str(getattr(command, "description", "") or "").strip()
            if not name or not description:
                raise DiscordForgeValidationError(
                    f"discord.py command at index {index} is missing name/description"
                )

            usage = _build_usage_from_options(getattr(command, "options", None))
            mapped_command: Dict[str, Any] = {
                "name": name,
                "description": description,
            }
            if usage:
                mapped_command["usage"] = usage
            if category:
                mapped_command["category"] = category
            mapped.append(mapped_command)
        return mapped

    def _request(
        self,
        method: str,
        path: str,
        *,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        auth_required: bool = False,
    ) -> Dict[str, Any]:
        headers: Dict[str, str] = {"Content-Type": "application/json"}
        if auth_required:
            headers.update(self._auth_headers())

        response = self._session.request(
            method=method.upper(),
            url=f"{self.base_url}{path}",
            headers=headers,
            json=json,
            params=params,
            timeout=self.timeout,
        )

        try:
            payload = response.json()
        except ValueError:
            payload = {"message": response.text or "Non-JSON response from API"}

        if not response.ok:
            message = str(payload.get("message") or payload.get("error") or response.reason)
            raise DiscordForgeAPIError(response.status_code, message, payload)

        if isinstance(payload, dict):
            return payload
        return {"data": payload}

    def _require_api_key(self) -> None:
        if not self.api_key:
            raise DiscordForgeValidationError("api_key is required for this endpoint")

    def _auth_headers(self) -> Dict[str, str]:
        if not self.api_key:
            return {}
        return {
            "Authorization": self.api_key,
            "x-api-key": self.api_key,
        }


def _ensure_not_blank(name: str, value: str) -> None:
    if not value or not value.strip():
        raise DiscordForgeValidationError(f"{name} is required")


def _ensure_non_negative(name: str, value: int) -> None:
    if not isinstance(value, int):
        raise DiscordForgeValidationError(f"{name} must be an integer")
    if value < 0:
        raise DiscordForgeValidationError(f"{name} must be >= 0")


def _ensure_optional_non_negative(name: str, value: Optional[int]) -> None:
    if value is None:
        return
    _ensure_non_negative(name, value)


def _build_usage_from_options(options: Optional[Any]) -> Optional[str]:
    if not options:
        return None
    usage_parts: List[str] = []
    for option in options:
        option_name = _option_get(option, "name")
        if not option_name:
            continue
        required = bool(_option_get(option, "required"))
        usage_parts.append(f"<{option_name}>" if required else f"[{option_name}]")
    return " ".join(usage_parts) if usage_parts else None


def _option_get(option: Any, key: str) -> Any:
    if isinstance(option, dict):
        return option.get(key)
    return getattr(option, key, None)


def _ensure_positive(name: str, value: int) -> None:
    if not isinstance(value, int):
        raise DiscordForgeValidationError(f"{name} must be an integer")
    if value <= 0:
        raise DiscordForgeValidationError(f"{name} must be > 0")
