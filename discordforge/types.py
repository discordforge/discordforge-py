from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True, frozen=True)
class BotStats:
    server_count: int
    shard_count: int | None = None
    user_count: int | None = None
    voice_connections: int | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"serverCount": self.server_count}
        if self.shard_count is not None:
            d["shardCount"] = self.shard_count
        if self.user_count is not None:
            d["userCount"] = self.user_count
        if self.voice_connections is not None:
            d["voiceConnections"] = self.voice_connections
        return d


@dataclass(slots=True, frozen=True)
class VoteMetadata:
    has_voted: bool
    voted_at: str | None
    next_vote_at: str | None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> VoteMetadata:
        return cls(
            has_voted=data["hasVoted"],
            voted_at=data.get("votedAt"),
            next_vote_at=data.get("nextVoteAt"),
        )


@dataclass(slots=True, frozen=True)
class BotInfo:
    id: str
    name: str
    vote_count: int
    server_count: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BotInfo:
        return cls(
            id=data["id"],
            name=data["name"],
            vote_count=data["voteCount"],
            server_count=data["serverCount"],
        )


@dataclass(slots=True)
class CustomCommand:
    name: str
    description: str
    usage: str | None = None
    category: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d: dict[str, Any] = {"name": self.name, "description": self.description}
        if self.usage is not None:
            d["usage"] = self.usage
        if self.category is not None:
            d["category"] = self.category
        return d


@dataclass(slots=True)
class DiscordCommand:
    name: str
    description: str
    type: int = 1
    options: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "type": self.type,
            "options": self.options,
        }


SyncCommand = CustomCommand | DiscordCommand


@dataclass(slots=True, frozen=True)
class ClientOptions:
    timeout: float = 10.0
    retries: int = 3
    base_url: str = "https://discordforge.org"
    max_connections: int = 10
    max_keepalive_connections: int = 5
    seed_known_limits: bool = True
