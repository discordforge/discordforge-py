"""
Check whether a user has voted for your bot in the last 12 hours.

Rate limit: 60 requests per minute.
Use case: reward users with a role or bonus after voting.
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
        user_id = "1180554986686525506"

        t = time.perf_counter()
        vote = await forge.check_vote(user_id)
        ms = (time.perf_counter() - t) * 1000

        if vote.has_voted:
            print(f"User {user_id} has voted.")
            print(f"  Voted at:        {vote.voted_at}")
            print(f"  Next vote after: {vote.next_vote_at}")
        else:
            print(f"User {user_id} has not voted yet.")
            print("  Send them: https://discordforge.org/bots/" + os.environ["BOT_ID"])

        print(f"Latency: {ms:.1f}ms")


asyncio.run(main())
