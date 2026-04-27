import os

import discord
from discord import app_commands

from discordforge import AutoPoster, BotStats, ForgeClient
from discordforge.errors import ForgeAPIError, ForgeAuthError, ForgeNotFoundError

bot = discord.AutoShardedClient(intents=discord.Intents.default())
tree = app_commands.CommandTree(bot)
forge = ForgeClient(os.environ["DISCORDFORGE_API_KEY"], bot_id=os.environ["BOT_ID"])


@tree.command(name="vote", description="Get the link to vote for this bot")
async def vote(interaction: discord.Interaction) -> None:
    await interaction.response.send_message(
        f"Vote for us here: https://discordforge.org/bots/{os.environ['BOT_ID']}",
        ephemeral=True,
    )


@tree.command(name="claim", description="Claim your vote reward")
async def claim(interaction: discord.Interaction) -> None:
    await interaction.response.defer(ephemeral=True)

    try:
        result = await forge.check_vote(str(interaction.user.id))
    except ForgeAuthError:
        await interaction.followup.send("Bot configuration error. Contact an admin.", ephemeral=True)
        return
    except ForgeAPIError as e:
        await interaction.followup.send(f"Could not verify your vote ({e.status}). Try again later.", ephemeral=True)
        return

    if not result.has_voted:
        await interaction.followup.send(
            f"You haven't voted yet.\nVote here: https://discordforge.org/bots/{os.environ['BOT_ID']}",
            ephemeral=True,
        )
        return

    role_id = os.environ.get("VOTER_ROLE_ID")
    if role_id and isinstance(interaction.user, discord.Member):
        role = interaction.guild.get_role(int(role_id))
        if role and role not in interaction.user.roles:
            await interaction.user.add_roles(role, reason="DiscordForge vote reward")

    await interaction.followup.send(
        f"Thanks for voting! Next vote available: {result.next_vote_at or 'in 12 hours'}",
        ephemeral=True,
    )


@tree.command(name="stats", description="Show this bot's DiscordForge listing stats")
async def stats(interaction: discord.Interaction) -> None:
    await interaction.response.defer()

    try:
        info = await forge.get_bot()
    except ForgeNotFoundError:
        await interaction.followup.send("Bot not found on DiscordForge.")
        return
    except ForgeAPIError as e:
        await interaction.followup.send(f"API error ({e.status}). Try again later.")
        return

    embed = discord.Embed(title=info.name, color=0x5865F2)
    embed.add_field(name="Votes", value=str(info.vote_count), inline=True)
    embed.add_field(name="Servers", value=str(info.server_count), inline=True)
    embed.set_footer(text="discordforge.org")
    await interaction.followup.send(embed=embed)


@tree.command(name="poststats", description="Manually post bot stats to DiscordForge (owner only)")
@app_commands.checks.has_permissions(administrator=True)
async def poststats(interaction: discord.Interaction) -> None:
    await interaction.response.defer(ephemeral=True)

    try:
        await forge.post_stats(
            BotStats(
                server_count=len(bot.guilds),
                shard_count=bot.shard_count,
                user_count=sum(g.member_count or 0 for g in bot.guilds),
            )
        )
        await interaction.followup.send("Stats posted successfully.", ephemeral=True)
    except ForgeAPIError as e:
        await interaction.followup.send(f"Failed to post stats: {e}", ephemeral=True)


async def setup_hook() -> None:
    await tree.sync()
    await forge.sync_from_discordpy(tree, category="General")

    poster = AutoPoster(forge, bot, interval=300.0)
    poster.on("post", lambda s: print(f"[DiscordForge] {s.server_count} servers posted"))
    poster.on("error", lambda e: print(f"[DiscordForge] AutoPoster error: {e}"))
    poster.start()


bot.setup_hook = setup_hook
bot.run(os.environ["BOT_TOKEN"])
