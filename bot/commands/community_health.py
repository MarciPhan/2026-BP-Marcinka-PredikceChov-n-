from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Optional

import discord
from discord.ext import commands
from discord import app_commands
import redis.asyncio as redis

from shared.community_health import is_probable_question, keys as health_keys, normalise_config
from shared.config import settings

REDIS_URL = __import__("os").getenv("REDIS_URL", "redis://localhost:6379/0")


class CommunityHealthTracker(commands.Cog):
    """Collects context required by the survey-prioritised analytics.

    No message content is persisted.  Only identifiers, timestamps and compact
    metadata needed for explainable aggregate analytics are stored.
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.pool = redis.ConnectionPool.from_url(REDIS_URL, decode_responses=True)
        self.r = redis.Redis(connection_pool=self.pool)

    async def cog_unload(self):
        await self.pool.disconnect()

    async def _config(self, guild_id: int) -> dict:
        raw = await self.r.hgetall(f"cfg:health:{guild_id}")
        return normalise_config(raw)

    async def _is_support_channel(self, guild_id: int, channel_id: int) -> bool:
        return bool(await self.r.sismember(f"cfg:health:support_channels:{guild_id}", str(channel_id)))

    async def _store_message_metadata(self, message: discord.Message) -> None:
        gid = message.guild.id
        mid = message.id
        reply_to = None
        reply_author_id = None
        if message.reference and message.reference.message_id:
            reply_to = message.reference.message_id
            resolved = message.reference.resolved
            if isinstance(resolved, discord.Message):
                reply_author_id = resolved.author.id

        mapping = {
            "message_id": str(mid),
            "author_id": str(message.author.id),
            "channel_id": str(message.channel.id),
            "created_at": str(message.created_at.timestamp()),
            "reply_to": str(reply_to or ""),
            "reply_author_id": str(reply_author_id or ""),
            "is_question": "1" if is_probable_question(message.content) else "0",
            "reaction_count": str(sum(reaction.count for reaction in message.reactions)),
        }
        key = health_keys.message(gid, mid)
        cutoff = time.time() - (settings.event_retention_days * 86400)
        async with self.r.pipeline() as pipe:
            pipe.hset(key, mapping=mapping)
            pipe.expire(key, settings.event_retention_days * 86400)
            pipe.hset(f"channel:info:{message.channel.id}", mapping={"name": getattr(message.channel, "name", str(message.channel.id)), "guild_id": str(gid)})
            pipe.zadd(health_keys.messages_index(gid), {str(mid): message.created_at.timestamp()})
            pipe.zremrangebyscore(health_keys.messages_index(gid), "-inf", cutoff)
            pipe.zadd(health_keys.user_messages(gid, message.author.id), {str(mid): message.created_at.timestamp()})
            pipe.zremrangebyscore(health_keys.user_messages(gid, message.author.id), "-inf", cutoff)
            await pipe.execute()

    async def _mark_help_answered(
        self,
        guild_id: int,
        parent_id: int,
        responder_id: int,
        response_id: int,
        answered_at: float | None = None,
    ) -> None:
        key = health_keys.help_item(guild_id, parent_id)
        if not await self.r.exists(key):
            return
        author_id = await self.r.hget(key, "author_id")
        if author_id and str(author_id) == str(responder_id):
            return
        now = answered_at if answered_at is not None else time.time()
        created = float(await self.r.hget(key, "created_at") or now)
        if await self.r.hget(key, "status") == "answered":
            return
        cutoff = time.time() - (settings.event_retention_days * 86400)
        async with self.r.pipeline() as pipe:
            pipe.hset(key, mapping={
                "status": "answered",
                "answered_at": str(now),
                "responder_id": str(responder_id),
                "response_id": str(response_id),
                "response_seconds": str(max(0, int(now - created))),
            })
            pipe.zrem(health_keys.help_open(guild_id), str(parent_id))
            pipe.zadd(health_keys.help_answered(guild_id), {str(parent_id): now})
            pipe.zremrangebyscore(health_keys.help_answered(guild_id), "-inf", cutoff)
            await pipe.execute()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        await self._store_message_metadata(message)

        gid = message.guild.id
        cfg = await self._config(gid)

        # A direct reply closes an existing help request, regardless of whether
        # question detection is enabled for the current channel.
        if message.reference and message.reference.message_id:
            await self._mark_help_answered(
                gid,
                message.reference.message_id,
                message.author.id,
                message.id,
                message.created_at.timestamp(),
            )

        if not cfg["help_requests_enabled"]:
            return
        if not await self._is_support_channel(gid, message.channel.id):
            return
        if cfg["question_mode"] == "heuristic" and not is_probable_question(message.content):
            return

        key = health_keys.help_item(gid, message.id)
        mapping = {
            "message_id": str(message.id),
            "author_id": str(message.author.id),
            "channel_id": str(message.channel.id),
            "created_at": str(message.created_at.timestamp()),
            "status": "open",
            "answered_at": "",
            "responder_id": "",
            "response_id": "",
            "response_seconds": "",
            "acknowledged_by_reaction": "0",
        }
        cutoff = time.time() - (settings.event_retention_days * 86400)
        async with self.r.pipeline() as pipe:
            pipe.hset(key, mapping=mapping)
            pipe.expire(key, settings.event_retention_days * 86400)
            pipe.zadd(health_keys.help_all(gid), {str(message.id): message.created_at.timestamp()})
            pipe.zremrangebyscore(health_keys.help_all(gid), "-inf", cutoff)
            pipe.zadd(health_keys.help_open(gid), {str(message.id): message.created_at.timestamp()})
            pipe.zremrangebyscore(health_keys.help_open(gid), "-inf", cutoff)
            pipe.zadd(health_keys.help_user(gid, message.author.id), {str(message.id): message.created_at.timestamp()})
            pipe.zremrangebyscore(health_keys.help_user(gid, message.author.id), "-inf", cutoff)
            await pipe.execute()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if not payload.guild_id or not payload.user_id or payload.user_id == getattr(self.bot.user, "id", None):
            return
        message_key = health_keys.message(payload.guild_id, payload.message_id)
        if await self.r.exists(message_key):
            await self.r.hincrby(message_key, "reaction_count", 1)
        help_key = health_keys.help_item(payload.guild_id, payload.message_id)
        if await self.r.exists(help_key):
            author_id = await self.r.hget(help_key, "author_id")
            if str(payload.user_id) != str(author_id):
                await self.r.hset(help_key, mapping={
                    "acknowledged_by_reaction": "1",
                    "acknowledged_at": str(time.time()),
                })

    @commands.Cog.listener()
    async def on_audit_log_entry_create(self, entry: discord.AuditLogEntry):
        if not entry.guild or not entry.user or entry.user.bot:
            return
        action_map = {
            discord.AuditLogAction.ban: "ban",
            discord.AuditLogAction.kick: "kick",
            discord.AuditLogAction.unban: "unban",
            discord.AuditLogAction.member_role_update: "role_update",
            discord.AuditLogAction.message_delete: "message_delete",
        }
        action_type = action_map.get(entry.action)
        if entry.action == discord.AuditLogAction.member_update:
            if getattr(entry.after, "timed_out_until", None):
                action_type = "timeout"
        if not action_type:
            return
        cfg = await self._config(entry.guild.id)
        if not cfg["moderation_context_enabled"]:
            return

        target_id = getattr(entry.target, "id", None)
        channel_id = getattr(getattr(entry, "extra", None), "channel", None)
        channel_id = getattr(channel_id, "id", None)
        ts = entry.created_at.timestamp()
        gid = entry.guild.id
        event_key = health_keys.mod_event(gid, entry.id)
        mapping = {
            "event_id": str(entry.id),
            "moderator_id": str(entry.user.id),
            "target_user_id": str(target_id or ""),
            "action_type": action_type,
            "channel_id": str(channel_id or ""),
            "created_at": str(ts),
            "resolved_at": str(ts) if action_type == "unban" else "",
        }
        cutoff = time.time() - (settings.event_retention_days * 86400)
        async with self.r.pipeline() as pipe:
            pipe.hset(event_key, mapping=mapping)
            pipe.expire(event_key, settings.event_retention_days * 86400)
            pipe.zadd(health_keys.mod_events(gid), {str(entry.id): ts})
            pipe.zremrangebyscore(health_keys.mod_events(gid), "-inf", cutoff)
            pipe.zadd(health_keys.mod_events_moderator(gid, entry.user.id), {str(entry.id): ts})
            pipe.zremrangebyscore(health_keys.mod_events_moderator(gid, entry.user.id), "-inf", cutoff)
            if target_id:
                pipe.zadd(health_keys.mod_events_target(gid, target_id), {str(entry.id): ts})
                pipe.zremrangebyscore(health_keys.mod_events_target(gid, target_id), "-inf", cutoff)
                pipe.zadd(health_keys.mod_pair(gid, target_id, entry.user.id), {str(entry.id): ts})
                pipe.zremrangebyscore(health_keys.mod_pair(gid, target_id, entry.user.id), "-inf", cutoff)
            await pipe.execute()

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        if member.bot:
            return
        gid, uid = member.guild.id, member.id
        cfg = await self._config(gid)
        if not cfg["departure_context_enabled"]:
            return
        now = time.time()
        lookback = now - 30 * 86400
        mod_count = await self.r.zcount(health_keys.mod_events_target(gid, uid), lookback, now)
        recent_help_ids = await self.r.zrangebyscore(health_keys.help_user(gid, uid), lookback, now)
        open_help = 0
        for help_id in recent_help_ids:
            if await self.r.hget(health_keys.help_item(gid, help_id), "status") == "open":
                open_help += 1
        last_messages = await self.r.zrevrangebyscore(health_keys.user_messages(gid, uid), now, 0, start=0, num=1, withscores=True)
        last_message_at = last_messages[0][1] if last_messages else ""
        departure_id = f"{uid}:{int(now)}"
        key = health_keys.departure(gid, departure_id)
        mapping = {
            "departure_id": departure_id,
            "user_id": str(uid),
            "left_at": str(now),
            "last_message_at": str(last_message_at),
            "recent_moderation_events": str(mod_count),
            "recent_help_requests": str(open_help),
            "interpretation": "temporal_context_only",
        }
        cutoff = now - (settings.event_retention_days * 86400)
        async with self.r.pipeline() as pipe:
            pipe.hset(key, mapping=mapping)
            pipe.expire(key, settings.event_retention_days * 86400)
            pipe.zadd(health_keys.departures(gid), {departure_id: now})
            pipe.zremrangebyscore(health_keys.departures(gid), "-inf", cutoff)
            await pipe.execute()


    @commands.Cog.listener()
    async def on_scheduled_event_create(self, event: discord.ScheduledEvent):
        await self._store_event(event)

    @commands.Cog.listener()
    async def on_scheduled_event_delete(self, event: discord.ScheduledEvent):
        await self._store_event(event)

    @commands.Cog.listener()
    async def on_scheduled_event_user_add(self, event: discord.ScheduledEvent, user: discord.User):
        key = health_keys.event_interested(event.guild_id, event.id)
        await self.r.sadd(key, str(user.id))
        await self.r.expire(key, settings.event_retention_days * 86400)
        await self._store_event(event)

    @commands.Cog.listener()
    async def on_scheduled_event_user_remove(self, event: discord.ScheduledEvent, user: discord.User):
        await self.r.srem(health_keys.event_interested(event.guild_id, event.id), str(user.id))

    @commands.Cog.listener()
    async def on_scheduled_event_update(self, before: discord.ScheduledEvent, after: discord.ScheduledEvent):
        await self._store_event(after)

    async def _store_event(self, event: discord.ScheduledEvent) -> None:
        channel_id = getattr(getattr(event, "channel", None), "id", None)
        mapping = {
            "event_id": str(event.id),
            "name": event.name[:200],
            "channel_id": str(channel_id or ""),
            "scheduled_start": str(event.start_time.timestamp() if event.start_time else ""),
            "scheduled_end": str(event.end_time.timestamp() if event.end_time else ""),
            "status": str(event.status),
        }
        event_key = health_keys.event(event.guild_id, event.id)
        await self.r.hset(event_key, mapping=mapping)
        await self.r.expire(event_key, settings.event_retention_days * 86400)
        index_key = health_keys.events_index(event.guild_id)
        await self.r.sadd(index_key, str(event.id))
        await self.r.expire(index_key, settings.event_retention_days * 86400)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.bot or not after.channel or before.channel == after.channel:
            return
        gid = member.guild.id
        cfg = await self._config(gid)
        if not cfg["event_conversion_enabled"]:
            return
        event_ids = await self.r.smembers(health_keys.events_index(gid))
        now = time.time()
        for event_id in event_ids:
            data = await self.r.hgetall(health_keys.event(gid, event_id))
            if not data or data.get("channel_id") != str(after.channel.id):
                continue
            start = float(data.get("scheduled_start") or 0)
            end = float(data.get("scheduled_end") or (start + 6 * 3600))
            if start - 30 * 60 <= now <= end + 30 * 60:
                attended_key = health_keys.event_attended(gid, event_id)
                await self.r.sadd(attended_key, str(member.id))
                await self.r.expire(attended_key, settings.event_retention_days * 86400)


    # Named "chealth", not "health": bot/commands/health.py already registers a
    # top-level slash command literally called "health" (Engagement Score/MII
    # summary). Discord's command tree does not allow a command and a group to
    # share a top-level name, so this cog failed to load at all when it also
    # tried to claim "health" (see tests/test_bot_cog_loading.py).
    health_group = app_commands.Group(name="chealth", description="Kontextová analytika Community Health")

    @health_group.command(name="status", description="Zobrazí stav modulů Engagement Score.")
    @app_commands.checks.has_permissions(administrator=True)
    async def health_status(self, interaction: discord.Interaction):
        cfg = await self._config(interaction.guild_id)
        support_count = await self.r.scard(f"cfg:health:support_channels:{interaction.guild_id}")
        await interaction.response.send_message(
            "**Engagement Score**\n"
            f"Typ: `{cfg['community_type']}`\n"
            f"Žádosti o pomoc: `{'zapnuto' if cfg['help_requests_enabled'] else 'vypnuto'}` ({support_count} kanálů)\n"
            f"Kontext moderace: `{'zapnuto' if cfg['moderation_context_enabled'] else 'vypnuto'}`\n"
            f"Kontext odchodů: `{'zapnuto' if cfg['departure_context_enabled'] else 'vypnuto'}`\n"
            f"Akce: `{'zapnuto' if cfg['event_conversion_enabled'] else 'vypnuto'}`",
            ephemeral=True,
        )

    @health_group.command(name="backfill", description="Doplní historický kontext zpráv a moderace.")
    @app_commands.describe(days="Počet dní zpětně, maximálně 180")
    @app_commands.checks.has_permissions(administrator=True)
    async def health_backfill(self, interaction: discord.Interaction, days: app_commands.Range[int, 1, 180] = 30):
        await interaction.response.defer(ephemeral=True, thinking=True)
        guild = interaction.guild
        if not guild:
            await interaction.followup.send("Příkaz je dostupný pouze na serveru.", ephemeral=True)
            return
        after = datetime.now(timezone.utc) - __import__("datetime").timedelta(days=int(days))
        cfg = await self._config(guild.id)
        support_ids = await self.r.smembers(f"cfg:health:support_channels:{guild.id}")
        messages = questions = replies = audits = 0

        for channel in guild.text_channels:
            try:
                async for message in channel.history(limit=None, after=after, oldest_first=True):
                    if message.author.bot:
                        continue
                    await self._store_message_metadata(message)
                    messages += 1
                    if message.reference and message.reference.message_id:
                        await self._mark_help_answered(
                            guild.id,
                            message.reference.message_id,
                            message.author.id,
                            message.id,
                            message.created_at.timestamp(),
                        )
                        replies += 1
                    if cfg["help_requests_enabled"] and str(channel.id) in support_ids:
                        if cfg["question_mode"] == "all" or is_probable_question(message.content):
                            key = health_keys.help_item(guild.id, message.id)
                            if not await self.r.exists(key):
                                backfill_cutoff = time.time() - (settings.event_retention_days * 86400)
                                await self.r.hset(key, mapping={
                                    "message_id": str(message.id), "author_id": str(message.author.id),
                                    "channel_id": str(channel.id), "created_at": str(message.created_at.timestamp()),
                                    "status": "open", "answered_at": "", "responder_id": "",
                                    "response_id": "", "response_seconds": "", "acknowledged_by_reaction": "0",
                                })
                                await self.r.expire(key, settings.event_retention_days * 86400)
                                await self.r.zadd(health_keys.help_all(guild.id), {str(message.id): message.created_at.timestamp()})
                                await self.r.zremrangebyscore(health_keys.help_all(guild.id), "-inf", backfill_cutoff)
                                await self.r.zadd(health_keys.help_open(guild.id), {str(message.id): message.created_at.timestamp()})
                                await self.r.zremrangebyscore(health_keys.help_open(guild.id), "-inf", backfill_cutoff)
                                await self.r.zadd(health_keys.help_user(guild.id, message.author.id), {str(message.id): message.created_at.timestamp()})
                                await self.r.zremrangebyscore(health_keys.help_user(guild.id, message.author.id), "-inf", backfill_cutoff)
                                questions += 1
            except (discord.Forbidden, discord.HTTPException):
                continue

        if cfg["moderation_context_enabled"]:
            try:
                async for entry in guild.audit_logs(limit=None, after=after, oldest_first=True):
                    before = await self.r.exists(health_keys.mod_event(guild.id, entry.id))
                    await self.on_audit_log_entry_create(entry)
                    after_exists = await self.r.exists(health_keys.mod_event(guild.id, entry.id))
                    if after_exists and not before:
                        audits += 1
            except (discord.Forbidden, discord.HTTPException):
                pass

        for event in guild.scheduled_events:
            await self._store_event(event)

        await interaction.followup.send(
            f"Hotovo: {messages} zpráv, {questions} žádostí o pomoc, {replies} odpovědí a {audits} moderačních událostí.",
            ephemeral=True,
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(CommunityHealthTracker(bot))
