"""
Post your bot's server/shard/user statistics to DiscordForge.

Rate limit: 1 request per 5 minutes.
Use AutoPoster (see autoposter.py) to handle this automatically.
"""

import asyncio
import os

from discordforge import BotStats, ForgeClient


async def main() -> None:
    async with ForgeClient(
        os.environ["DISCORDFORGE_API_KEY"],
        bot_id=os.environ["BOT_ID"],
    ) as forge:
        result = await forge.post_stats(
            BotStats(
                server_count=1500,
                shard_count=4,
                user_count=80000,
                voice_connections=12,
            )
        )
        print("Stats posted:", result)


asyncio.run(main())
