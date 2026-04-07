from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class BotStatsUpdate:
    server_count: int
    shard_count: Optional[int] = None
    user_count: Optional[int] = None
    voice_connections: Optional[int] = None

    def to_payload(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {"server_count": self.server_count}
        if self.shard_count is not None:
            payload["shard_count"] = self.shard_count
        if self.user_count is not None:
            payload["user_count"] = self.user_count
        if self.voice_connections is not None:
            payload["voice_connections"] = self.voice_connections
        return payload


@dataclass(frozen=True)
class VoteCheckResult:
    has_voted: bool
    voted_at: Optional[datetime]
    next_vote_at: Optional[datetime]
    raw: Dict[str, Any]


@dataclass(frozen=True)
class CommandSyncResult:
    success: bool
    synced: int
    raw: Dict[str, Any]


@dataclass(frozen=True)
class BotInfo:
    data: Dict[str, Any]

    @property
    def id(self) -> Optional[str]:
        value = self.data.get("id")
        return str(value) if value is not None else None

    @property
    def name(self) -> Optional[str]:
        value = self.data.get("name")
        return str(value) if value is not None else None

    @property
    def vote_count(self) -> Optional[int]:
        return _as_int(self.data.get("voteCount"))

    @property
    def server_count(self) -> Optional[int]:
        return _as_int(self.data.get("serverCount"))


def parse_iso_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    normalized = value.replace("Z", "+00:00")
    return datetime.fromisoformat(normalized)


def _as_int(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, int):
        return value
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


CommandObject = Dict[str, Any]
CommandsList = List[CommandObject]
