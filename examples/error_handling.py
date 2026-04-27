import asyncio
import os
import time

from discordforge import ForgeClient
from discordforge.errors import ForgeAPIError, ForgeAuthError, ForgeNotFoundError


def _ms(start: float) -> str:
    return f"{(time.perf_counter() - start) * 1000:.1f}ms"


async def main() -> None:
    async with ForgeClient(
        os.environ["DISCORDFORGE_API_KEY"],
        bot_id=os.environ["BOT_ID"],
    ) as forge:

        # Valid vote check
        t = time.perf_counter()
        try:
            vote = await forge.check_vote("000000000000000001")
            print(f"Voted: {vote.has_voted} ({_ms(t)})")
        except ForgeNotFoundError:
            print(f"Bot not found on DiscordForge. ({_ms(t)})")
        except ForgeAPIError as e:
            print(f"API error {e.status}: {e} ({_ms(t)})")

        # Bot not found
        t = time.perf_counter()
        try:
            await forge.get_bot(bot_id="000000000000000000")
        except ForgeNotFoundError:
            print(f"Caught ForgeNotFoundError — bot ID does not exist. ({_ms(t)})")
        except ForgeAPIError as e:
            print(f"API error {e.status}: {e} ({_ms(t)})")

        # Bad API key — use an authenticated endpoint to trigger 401
        t = time.perf_counter()
        try:
            async with ForgeClient("invalid-key", bot_id=os.environ["BOT_ID"]) as bad:
                await bad.check_vote("123456789012345678")
        except ForgeAuthError:
            print(f"Caught ForgeAuthError — invalid API key. ({_ms(t)})")
        except ForgeAPIError as e:
            print(f"API error {e.status}: {e} ({_ms(t)})")


asyncio.run(main())
