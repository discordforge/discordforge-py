class DiscordForgeError(Exception):
    """Base exception for all DiscordForge client errors."""


class DiscordForgeAPIError(DiscordForgeError):
    """Raised when the DiscordForge API returns an error response."""

    def __init__(self, status_code: int, message: str, payload: object = None) -> None:
        self.status_code = status_code
        self.payload = payload
        super().__init__(f"DiscordForge API error {status_code}: {message}")


class DiscordForgeValidationError(DiscordForgeError):
    """Raised when input values are invalid before request execution."""
