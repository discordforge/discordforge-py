# discordforge-sdk-python

<p align="center">
  <img src="https://camo.githubusercontent.com/17fab4e9878bf65d24c59ecd561f38b4a8dc1f860ba087451e98413b91922b80/68747470733a2f2f646973636f7264666f7267652e6f72672f696d616765732f6c6f676f2e706e67" alt="Banner" />
</p>

A fully async Python SDK for the [DiscordForge](https://discordforge.org) bot listing platform. Works with small bots and large sharded/auto-sharded bots equally.

## Requirements

- Python 3.11+
- `httpx >= 0.27`

## Installation

```bash
pip install discordforge-sdk-python
```

## Quickstart

```python
import os
import discord
from discordforge import ForgeClient, AutoPoster

bot = discord.Client(intents=discord.Intents.default())
forge = ForgeClient(os.environ["DISCORDFORGE_API_KEY"], bot_id=os.environ["BOT_ID"])

async def setup_hook():
    await forge.sync_from_discordpy(bot.tree, category="General")
    AutoPoster(forge, bot).start()

bot.setup_hook = setup_hook
bot.run(os.environ["BOT_TOKEN"])
```

`AutoPoster` posts your stats every 5 minutes automatically. It waits until all shards are ready before the first post, so counts are always accurate.

Want to post every 30 minutes instead? Pass `interval=1800.0`. Minimum is 300s (API limit).

```python
AutoPoster(forge, bot, interval=1800.0).start()
```

## Usage with discord.py

### AutoPoster

```python
poster = AutoPoster(forge, bot, interval=300.0)  # minimum 300s
poster.on("post", lambda stats: print(f"Posted {stats.server_count} servers"))
poster.on("error", lambda err: print(f"Error: {err}"))
poster.start()
```

Callbacks can be sync or async. The poster keeps running even if a post fails.

### Manual stat posting

```python
from discordforge import ForgeClient, BotStats

forge = ForgeClient("YOUR_API_KEY", bot_id="YOUR_BOT_ID")

@bot.event
async def on_ready():
    await forge.post_stats(BotStats(
        server_count=len(bot.guilds),
        shard_count=bot.shard_count,
        user_count=len(bot.users),
    ))
```

### Check if a user voted

```python
vote = await forge.check_vote("USER_DISCORD_ID")

if vote.has_voted:
    print(f"Voted at {vote.voted_at}, next vote available at {vote.next_vote_at}")
else:
    await ctx.send("You haven't voted yet! https://discordforge.org/bots/YOUR_BOT_ID")
```

### Get your bot's public listing info

```python
info = await forge.get_bot()
print(f"{info.name} has {info.vote_count} votes across {info.server_count} servers")
```

### Sync slash commands

Pass your discord.py command tree and it maps commands automatically:

```python
async def setup_hook():
    await bot.tree.sync()
    await forge.sync_from_discordpy(bot.tree, category="General")
```

Or pass a raw list if you want full control:

```python
from discordforge import DiscordCommand

await forge.sync_commands([
    DiscordCommand(name="ping", description="Check bot latency"),
    DiscordCommand(name="help", description="Show help menu"),
])
```

## Configuration

```python
from discordforge import ForgeClient, ClientOptions

forge = ForgeClient(
    "YOUR_API_KEY",
    bot_id="YOUR_BOT_ID",
    options=ClientOptions(
        timeout=10.0,               # seconds per request
        retries=3,                  # retries on 5xx / network errors
        max_connections=10,         # httpx connection pool size
        max_keepalive_connections=5,
    ),
)
```

## Error handling

```python
from discordforge.errors import ForgeAPIError, ForgeRateLimitError, ForgeAuthError, ForgeNotFoundError

try:
    await forge.post_stats(BotStats(server_count=100))
except ForgeRateLimitError as e:
    print(f"Rate limited, retry in {e.retry_after}s")
except ForgeAuthError:
    print("Invalid API key")
except ForgeAPIError as e:
    print(f"API error {e.status}: {e}")
```

| Exception | When raised |
|---|---|
| `ForgeRateLimitError` | 429 — backs off and retries automatically, only raises after all retries exhausted |
| `ForgeAuthError` | 401 — invalid or missing API key |
| `ForgeNotFoundError` | 404 — bot ID not found on DiscordForge |
| `ForgeAPIError` | any other non-2xx response |

## AutoPoster reference

```python
poster = AutoPoster(
    forge,                      # ForgeClient instance
    bot,                        # any discord client (discord.py, nextcord, py-cord, eris-style)
    interval=300.0,             # seconds between posts (minimum 300 — API rate limit)
    start_immediately=True,     # post as soon as ready fires
)

poster.on("post", callback)     # called after each successful post with BotStats
poster.on("error", callback)    # called on failure — poster keeps running

poster.start()                  # start the background task
poster.stop()                   # cancel the task (can restart with start())
poster.destroy()                # stop + clear all listeners
poster.is_running               # bool
```

Callbacks can be sync or async — both work:

```python
async def on_post(stats):
    await log_channel.send(f"Posted {stats.server_count} servers")

def on_error(err):
    print(f"Error: {err}")

poster.on("post", on_post)
poster.on("error", on_error)
```

## Types reference

| Type | Fields |
|---|---|
| `BotStats` | `server_count`, `shard_count`, `user_count`, `voice_connections` |
| `VoteMetadata` | `has_voted`, `voted_at`, `next_vote_at` |
| `BotInfo` | `id`, `name`, `vote_count`, `server_count` |
| `DiscordCommand` | `name`, `description`, `type`, `options` |
| `CustomCommand` | `name`, `description`, `usage`, `category` |

## Examples

The [`examples/`](examples/) folder has ready-to-run scripts covering every API feature:

| File | What it shows |
|---|---|
| [`post_stats.py`](examples/post_stats.py) | Post server/shard/user counts |
| [`check_vote.py`](examples/check_vote.py) | Check if a user voted in the last 12h |
| [`get_bot.py`](examples/get_bot.py) | Fetch your bot's public listing info |
| [`sync_commands.py`](examples/sync_commands.py) | Sync commands using `DiscordCommand` or `CustomCommand` |
| [`sync_commands_discordpy.py`](examples/sync_commands_discordpy.py) | Auto-sync directly from `bot.tree` |
| [`autoposter.py`](examples/autoposter.py) | AutoPoster with post/error callbacks |
| [`vote_reward.py`](examples/vote_reward.py) | Full vote reward flow with role assignment |
| [`error_handling.py`](examples/error_handling.py) | Catching all error types |
| [`bot.py`](examples/bot.py) | Complete bot with all slash commands and AutoPoster |

All examples use environment variables for credentials — copy and set these before running:

```bash
export DISCORDFORGE_API_KEY="your_api_key"
export BOT_ID="your_bot_discord_id"
export BOT_TOKEN="your_bot_token"       # discord.py examples only
export VOTER_ROLE_ID="role_id"          # vote_reward.py only
```

## Running tests

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

## License

MIT
