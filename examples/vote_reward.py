"""
Full vote reward flow — check if a user voted and grant them a role.

Typical pattern: user runs /claim, bot checks DiscordForge, grants reward.
"""

import os

import discord
from discord import app_commands

from discordforge import ForgeClient
from discordforge.errors import ForgeAPIError

bot = discord.Client(intents=discord.Intents.default())
tree = app_commands.CommandTree(bot)
forge = ForgeClient(os.environ["DISCORDFORGE_API_KEY"], bot_id=os.environ["BOT_ID"])

VOTER_ROLE_ID = int(os.environ["VOTER_ROLE_ID"])


@tree.command(name="claim", description="Claim your vote reward")
async def claim(interaction: discord.Interaction) -> None:
    await interaction.response.defer(ephemeral=True)

    try:
        vote = await forge.check_vote(str(interaction.user.id))
    except ForgeAPIError as e:
        await interaction.followup.send(f"Could not verify your vote: {e}", ephemeral=True)
        return

    if not vote.has_voted:
        await interaction.followup.send(
            f"You haven't voted yet. Vote here: https://discordforge.org/bots/{os.environ['BOT_ID']}",
            ephemeral=True,
        )
        return

    guild = interaction.guild
    member = interaction.user

    role = guild.get_role(VOTER_ROLE_ID)
    if role and isinstance(member, discord.Member) and role not in member.roles:
        await member.add_roles(role, reason="DiscordForge vote reward")
        await interaction.followup.send("Thanks for voting! Your reward role has been granted.", ephemeral=True)
    else:
        await interaction.followup.send("Thanks for voting! You already have your reward role.", ephemeral=True)


async def setup_hook() -> None:
    await tree.sync()


bot.setup_hook = setup_hook
bot.run(os.environ["BOT_TOKEN"])
