from .autoposter import AutoPoster
from .client import ForgeClient
from .errors import ForgeAPIError, ForgeAuthError, ForgeNotFoundError, ForgeRateLimitError
from .types import BotInfo, BotStats, ClientOptions, CustomCommand, DiscordCommand, VoteMetadata

__version__ = "1.0.0"
__all__ = [
    "ForgeClient",
    "AutoPoster",
    "ClientOptions",
    "BotStats",
    "VoteMetadata",
    "BotInfo",
    "CustomCommand",
    "DiscordCommand",
    "ForgeAPIError",
    "ForgeRateLimitError",
    "ForgeAuthError",
    "ForgeNotFoundError",
]
