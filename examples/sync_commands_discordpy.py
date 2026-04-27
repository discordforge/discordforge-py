"""
Sync commands directly from a discord.py app_commands.CommandTree.

ForgeClient reads the tree automatically — no manual mapping needed.
Run this once after bot.tree.sync() to keep your listing page up to date.
"""

import os

import discord
from discord import app_commands

from discordforge import ForgeClient

bot = discord.Client(intents=discord.Intents.default())
tree = app_commands.CommandTree(bot)
forge = ForgeClient(os.environ["DISCORDFORGE_API_KEY"], bot_id=os.environ["BOT_ID"])


@tree.command(name="ping", description="Check bot latency")
async def ping(interaction: discord.Interaction) -> None:
    await interaction.response.send_message("Pong!")


@tree.command(name="help", description="Show all available commands")
async def help_cmd(interaction: discord.Interaction) -> None:
    await interaction.response.send_message("Here are my commands...")


async def setup_hook() -> None:
    await tree.sync()
    result = await forge.sync_from_discordpy(tree, category="General")
    print(f"Synced {result.get('synced')} commands to DiscordForge.")


bot.setup_hook = setup_hook
bot.run(os.environ["BOT_TOKEN"])
