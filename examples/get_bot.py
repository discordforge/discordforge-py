"""
Fetch your bot's public listing info from DiscordForge.
No rate limit documented — treat as a low-frequency read.
"""

import asyncio
import os
import time

from discordforge import ForgeClient


async def main() -> None:
    async with ForgeClient(
        os.environ["DISCORDFORGE_API_KEY"],
        bot_id=os.environ["BOT_ID"],
    ) as forge:
        t = time.perf_counter()
        info = await forge.get_bot()
        ms = (time.perf_counter() - t) * 1000

        print(f"Name:         {info.name}")
        print(f"ID:           {info.id}")
        print(f"Vote count:   {info.vote_count}")
        print(f"Server count: {info.server_count}")
        print(f"Latency:      {ms:.1f}ms")


asyncio.run(main())
