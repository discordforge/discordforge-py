# discordforge

Python package for interacting with the DiscordForge REST API.

## discord.py Compatibility

This package does not conflict with `discord.py` imports:

- `discord.py` uses `import discord`
- this package uses `import discordforge`

Use `AsyncDiscordForgeClient` in `discord.py` bots to avoid blocking the event loop.

## Install

```bash
pip install -e .
```

For development tools:

```bash
pip install -e ".[dev]"
```

## Quick Start

```python
from discordforge import DiscordForgeClient

client = DiscordForgeClient(api_key="YOUR_API_KEY")

# POST /api/bots/stats
client.post_bot_stats(server_count=1500, shard_count=5, user_count=50000)

# GET /api/bots/:id/votes/check?userId=...
vote = client.check_vote(bot_id="YOUR_BOT_ID", user_id="USER_ID")
print(vote.has_voted, vote.voted_at, vote.next_vote_at)

# GET /api/bots/:id (public endpoint, no API key required)
public_client = DiscordForgeClient()
bot = public_client.get_bot(bot_id="YOUR_BOT_ID")
print(bot.id, bot.name, bot.vote_count, bot.server_count)

# POST /api/external/bots/commands
result = client.sync_commands(
    commands=[
        {
            "name": "ban",
            "description": "Ban a user from the server",
            "usage": "/ban <user> [reason]",
            "category": "Moderation",
        },
        {
            "name": "play",
            "description": "Play a song in your voice channel",
            "type": 1,
            "options": [
                {"name": "query", "type": 3, "required": True},
            ],
        },
    ]
)
print(result.success, result.synced)
```

## Easy Command Sync (discord.py)

Use one call to map and sync your slash commands:

```python
import os
from discordforge import DiscordForgeClient

forge = DiscordForgeClient(api_key=os.environ["DISCORDFORGE_API_KEY"])

# command_source can be bot.tree or an iterable of command objects.
result = forge.sync_from_discordpy(
    command_source=bot.tree,
    category="General",
    limit=200,        # auto-truncate to API max by default
    strict_limit=False,
)
print(result.success, result.synced)
```

## discord.py Async Example

```python
import os
import discord
from discord.ext import tasks
from discordforge import AsyncDiscordForgeClient

bot = discord.Client(intents=discord.Intents.default())
forge = AsyncDiscordForgeClient(api_key=os.environ["DISCORDFORGE_API_KEY"])

@bot.event
async def on_ready():
    post_stats.start()

@tasks.loop(minutes=5)
async def post_stats():
    # Keep this endpoint at 1 request per 5 minutes.
    await forge.post_bot_stats(
        server_count=len(bot.guilds),
        shard_count=getattr(bot, "shard_count", None),
    )

@bot.event
async def setup_hook():
    # Easy one-call command sync from discord.py command tree.
    await forge.sync_from_discordpy(command_source=bot.tree, category="General")
```

## Environment Variable Example

```python
import os
from discordforge import DiscordForgeClient

client = DiscordForgeClient(api_key=os.environ["DISCORDFORGE_API_KEY"])
```

## Error Handling

```python
from discordforge import DiscordForgeClient, DiscordForgeAPIError, DiscordForgeValidationError

client = DiscordForgeClient(api_key="YOUR_API_KEY")

try:
    client.post_bot_stats(server_count=1500)
except DiscordForgeValidationError as exc:
    print("Invalid input:", exc)
except DiscordForgeAPIError as exc:
    print("DiscordForge request failed:", exc.status_code, exc)
```

## Notes

- `sync_commands` accepts both DiscordForge custom command format and raw Discord API slash command format.
- `sync_from_discordpy` maps command objects (`name`, `description`, `options`) and syncs in one call.
- The client sends both `Authorization` and `x-api-key` headers when authentication is required.
- `sync_commands` enforces DiscordForge limits (`1..200` commands).
- For `discord.py`, prefer `AsyncDiscordForgeClient` to keep the bot loop responsive.
