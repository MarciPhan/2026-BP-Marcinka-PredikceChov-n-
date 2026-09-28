"""Regression tests for Community Health data retention (NFR-04).

Before this fix, the *index* structures (health:messages_index, health:user_messages,
health:mod_events, health:mod_pair, health:departures, health:help_*, event
interest/attendance sets) never pruned old entries at all, even though the individual
detail hashes they point to already expired via TTL. That meant e.g. a specific
moderation-conflict pair between two users kept accumulating forever.

These indexes are continuously active/growing (mirroring the same
`zremrangebyscore`-based retention already used for the main `events:msg:*` sorted
sets in bot/commands/activity.py and scripts/discourse_sync.py), so the fix is
score-based pruning of stale members on every write, not a blanket TTL on the whole
key -- a whole-key TTL would incorrectly wipe out recent entries too. A narrow index
like `health:mod_pair:{guild}:{a}:{b}` naturally disappears once its last (stale)
member is pruned, since Redis deletes a sorted set once it becomes empty.
"""
import time

import fakeredis.aioredis
import pytest

from shared.community_health import keys as health_keys
from shared.config import settings


def _make_tracker():
    from bot.commands.community_health import CommunityHealthTracker

    tracker = CommunityHealthTracker.__new__(CommunityHealthTracker)
    tracker.bot = None
    tracker.r = fakeredis.aioredis.FakeRedis(decode_responses=True)
    return tracker


def _make_message(guild_id, author_id, message_id, content="ahoj", reference=None):
    import discord

    message = type("FakeMessage", (), {})()
    message.guild = type("FakeGuild", (), {"id": guild_id})()
    message.author = type("FakeAuthor", (), {"id": author_id, "bot": False})()
    message.channel = type("FakeChannel", (), {"id": 555, "name": "obecne"})()
    message.id = message_id
    message.content = content
    message.created_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
    message.reference = reference
    message.reactions = []
    return message


@pytest.mark.asyncio
async def test_message_indexes_get_ttl_and_prune_old_entries():
    tracker = _make_tracker()
    gid, uid = 1, 2

    # Simulate a stale entry that predates the retention window, inserted directly
    # (as if it had been written a long time ago under the old, TTL-less code).
    stale_score = time.time() - (settings.event_retention_days + 5) * 86400
    await tracker.r.zadd(health_keys.messages_index(gid), {"stale-1": stale_score})
    await tracker.r.zadd(health_keys.user_messages(gid, uid), {"stale-1": stale_score})

    await tracker._store_message_metadata(_make_message(gid, uid, 42))

    for key in (health_keys.messages_index(gid), health_keys.user_messages(gid, uid)):
        members = await tracker.r.zrange(key, 0, -1)
        assert "stale-1" not in members, f"{key} must prune entries older than retention"
        assert "42" in members


@pytest.mark.asyncio
async def test_moderation_indexes_get_ttl_and_prune_old_entries():
    tracker = _make_tracker()
    gid, moderator_id, target_id = 1, 20, 10

    entry = type("FakeAuditEntry", (), {})()
    entry.guild = type("FakeGuild", (), {"id": gid})()
    entry.user = type("FakeUser", (), {"id": moderator_id, "bot": False})()
    entry.target = type("FakeTarget", (), {"id": target_id})()
    entry.id = 999
    entry.created_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
    import discord
    entry.action = discord.AuditLogAction.kick
    entry.extra = None

    stale_score = time.time() - (settings.event_retention_days + 5) * 86400
    keys_to_check = [
        health_keys.mod_events(gid),
        health_keys.mod_events_moderator(gid, moderator_id),
        health_keys.mod_events_target(gid, target_id),
        health_keys.mod_pair(gid, target_id, moderator_id),
    ]
    for key in keys_to_check:
        await tracker.r.zadd(key, {"stale-event": stale_score})

    await tracker.on_audit_log_entry_create(entry)

    for key in keys_to_check:
        members = await tracker.r.zrange(key, 0, -1)
        assert "stale-event" not in members, f"{key} must prune entries older than retention"
        assert "999" in members
