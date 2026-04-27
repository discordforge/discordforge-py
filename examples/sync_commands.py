"""
Sync your bot's slash commands to the DiscordForge listing panel.

Supports up to 200 commands per request.
Use DiscordCommand for standard Discord API command format,
or CustomCommand if you want to add usage/category metadata.
"""

import asyncio
import os

from discordforge import DiscordCommand, ForgeClient
from discordforge.types import CustomCommand


async def main() -> None:
    async with ForgeClient(
        os.environ["DISCORDFORGE_API_KEY"],
        bot_id=os.environ["BOT_ID"],
    ) as forge:

        # Option A: DiscordCommand (mirrors the Discord API command structure)
        discord_commands = [
            DiscordCommand(name="ping", description="Check bot latency"),
            DiscordCommand(name="help", description="Show all available commands"),
            DiscordCommand(
                name="userinfo",
                description="Get info about a user",
                options=[{"name": "user", "description": "Target user", "type": 6, "required": True}],
            ),
        ]

        # Option B: CustomCommand (adds usage string and category for the listing page)
        custom_commands = [
            CustomCommand(name="ban", description="Ban a member", usage="<user> [reason]", category="Moderation"),
            CustomCommand(name="kick", description="Kick a member", usage="<user> [reason]", category="Moderation"),
            CustomCommand(name="rank", description="Show your XP rank", category="Leveling"),
        ]

        result = await forge.sync_commands(discord_commands + custom_commands)
        print(f"Synced {result.get('synced')} commands successfully.")


asyncio.run(main())
