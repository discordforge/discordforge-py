"""
AutoPoster — automatically post bot stats every 5 minutes.

Waits for the bot's ready event before the first post so stats
are always accurate. Callbacks can be sync or async.
"""

import os

import discord

from discordforge import AutoPoster, ForgeClient

bot = discord.Client(intents=discord.Intents.default())
forge = ForgeClient(os.environ["DISCORDFORGE_API_KEY"], bot_id=os.environ["BOT_ID"])


async def setup_hook() -> None:
    poster = AutoPoster(forge, bot, interval=300.0, start_immediately=True)

    async def on_post(stats):
        print(f"Posted: {stats.server_count} servers, {stats.shard_count} shards")

    def on_error(err):
        print(f"AutoPoster error: {err}")

    poster.on("post", on_post)
    poster.on("error", on_error)
    poster.start()


bot.setup_hook = setup_hook
bot.run(os.environ["BOT_TOKEN"])
