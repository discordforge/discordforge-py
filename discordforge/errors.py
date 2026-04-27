from __future__ import annotations


class ForgeAPIError(Exception):
    def __init__(
        self,
        message: str,
        status: int,
        body: object,
        *,
        retry_after: int | None = None,
        reset_after: int | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.body = body
        self.retry_after = retry_after
        self.reset_after = reset_after

    def __repr__(self) -> str:
        return f"ForgeAPIError(status={self.status}, message={self.args[0]!r})"


class ForgeRateLimitError(ForgeAPIError):
    def __init__(self, retry_after: int, body: object) -> None:
        super().__init__(
            f"Rate limited. Retry after {retry_after}s.",
            429,
            body,
            retry_after=retry_after,
        )


class ForgeAuthError(ForgeAPIError):
    def __init__(self, body: object) -> None:
        super().__init__("Invalid or missing API key.", 401, body)


class ForgeNotFoundError(ForgeAPIError):
    def __init__(self, body: object) -> None:
        super().__init__("Resource not found.", 404, body)
