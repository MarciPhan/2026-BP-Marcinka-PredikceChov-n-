import os

import discord
import pytest
from discord.ext import commands

COMMANDS_DIR = os.path.join(os.path.dirname(__file__), "..", "bot", "commands")


def discovered_command_modules():
    """Mirror bot/main.py's module discovery: every .py file in bot/commands/
    except private (_-prefixed) modules and __init__.py, in the same
    (unsorted) filesystem order main.py iterates them in."""
    return [
        f[:-3]
        for f in os.listdir(COMMANDS_DIR)
        if f.endswith(".py") and not f.startswith("_") and f != "__init__.py"
    ]


@pytest.mark.asyncio
async def test_all_command_cogs_load_without_name_collisions():
    """Regression test for a real bug: bot/commands/health.py registers a
    top-level slash command named "health", while bot/commands/community_health.py
    used to register an app_commands.Group also named "health". Discord's
    command tree does not allow a command and a group to share a top-level
    name, so loading both raised CommandAlreadyRegistered and the entire
    CommunityHealthTracker cog (all its listeners included) silently failed
    to load in bot/main.py, which only logs load failures and continues.

    This test loads every bot/commands/*.py extension into a fresh Bot, in
    the same filesystem order bot/main.py discovers them in, and fails loudly
    if any extension raises -- instead of only logging a warning that's easy
    to miss in a live deployment.
    """
    intents = discord.Intents.default()
    bot = commands.Bot(command_prefix="!", intents=intents)
    # bot/main.py only loads extensions from inside on_ready(), i.e. after
    # bot.start()/login() has run and bound the client to the running loop.
    # A bare Bot() has not done that yet, so cogs that touch bot.loop or
    # start a @tasks.loop at __init__ time (e.g. stats_hll.py) would raise
    # here even though they work fine in the real, fully-started bot.
    # _async_setup_hook() reproduces just that binding step, without a real
    # network login.
    await bot._async_setup_hook()

    failures = {}
    try:
        for module in discovered_command_modules():
            try:
                await bot.load_extension(f"bot.commands.{module}")
            except Exception as exc:  # noqa: BLE001 - we want to report every failure
                failures[module] = f"{type(exc).__name__}: {exc}"
    finally:
        # Some cogs start background @tasks.loop()/asyncio tasks as soon as
        # they load; close() cancels them so pytest doesn't warn about
        # dangling tasks after the test ends.
        await bot.close()

    assert not failures, f"Command modules failed to load: {failures}"
