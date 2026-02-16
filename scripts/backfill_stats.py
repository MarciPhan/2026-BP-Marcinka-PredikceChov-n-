#!/usr/bin/env python3
"""
Backfill Stats Script - Compatible with discord.py 1.7.3 & 2.x
Fetches historical messages and audit logs, populates Redis with activity stats.
"""

import discord
import asyncio
import argparse
import os
import json
import time
from datetime import datetime, timedelta, timezone
from collections import defaultdict, Counter
import redis.asyncio as aioredis

# Parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("--guild_id", type=int, required=True)
parser.add_argument("--token", type=str, required=True)
parser.add_argument("--days", type=int, default=30)
args = parser.parse_args()

# Redis Configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Key Helpers
def day_key(dt: datetime) -> str: return dt.strftime("%Y%m%d")
def K_DAU(gid: int, d: str) -> str: return f"hll:dau:{gid}:{d}"
def K_HOURLY(gid: int, d: str) -> str: return f"stats:hourly:{gid}:{d}"
def K_MSGLEN(gid: int) -> str: return f"stats:msglen:{gid}"
def K_HEATMAP(gid: int) -> str: return f"stats:heatmap:{gid}"
def K_TOTAL_MSGS(gid: int) -> str: return f"stats:total_msgs:{gid}"

class BackfillClient(discord.Client):
    def __init__(self, guild_id, days):
        # discord.py 2.0+ intents (using 1.7.3 compat mode if needed, but this codebase seems mixed)
        intents = discord.Intents.default()
        intents.members = True
        intents.guilds = True
        intents.message_content = True
        super().__init__(intents=intents)
        self.target_guild_id = guild_id
        self.days = days
        self.redis = None

    async def setup_redis(self):
        self.redis = await aioredis.from_url(REDIS_URL, decode_responses=True)

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print(f"Starting backfill for guild {self.target_guild_id} with {self.days} days history...")
        
        try:
            await self.setup_redis()
            
            guild = self.get_guild(self.target_guild_id)
            if not guild:
                # Try to fetch guild if not in cache
                try:
                    guild = await self.fetch_guild(self.target_guild_id)
                except:
                    pass

            if not guild:
                print(f"Guild {self.target_guild_id} not found!")
                progress_key = f"backfill:progress:{self.target_guild_id}"
                await self.redis.set(progress_key, json.dumps({"status": "error", "message": "Guild not found. Is the bot added?"}))
                await self.close()
                return

            await self.run_backfill(guild)
        except Exception as e:
            import traceback
            print(f"Error during backfill: {e}")
            traceback.print_exc()
        finally:
            if self.redis:
                await self.redis.aclose()
            await self.close()

    async def _update_user_info(self, user):
        """Cache user info in Redis."""
        if user.bot: return
        key = f"user:info:{user.id}"
        name = getattr(user, 'display_name', user.name)
        avatar = str(user.display_avatar.url) if hasattr(user, 'display_avatar') else ""
        roles = ""
        if isinstance(user, discord.Member):
             roles = ",".join(str(r.id) for r in user.roles)
        
        await self.redis.hset(key, mapping={"name": name, "avatar": avatar, "roles": roles})
        await self.redis.expire(key, 604800)

    async def run_backfill(self, guild):
        gid = guild.id
        # Update progress key
        progress_key = f"backfill:progress:{gid}"
        await self.redis.set(progress_key, json.dumps({"status": "starting", "progress": 0}))

        limit_date = datetime.now() - timedelta(days=self.days)
        discord_epoch = datetime(2015, 1, 1)
        if limit_date < discord_epoch: limit_date = discord_epoch
        
        print(f"Processing messages since {limit_date.date()}...")

        # 1. Process Messages
        msg_count = 0
        user_messages = defaultdict(list)
        
        # Aggregation containers
        hourly_stats = defaultdict(lambda: defaultdict(int)) # local cache for hourly: key -> hour -> count
        heatmap_stats = defaultdict(int) 
        msglen_bucket_stats = defaultdict(int)
        channel_total_stats = defaultdict(int)
        user_daily_stats = defaultdict(lambda: defaultdict(int)) # date -> user -> count
        leaderboard_stats = defaultdict(int)
        
        channels = guild.text_channels
        total_channels = len(channels)
        
        for idx, channel in enumerate(channels):
            try:
                permissions = channel.permissions_for(guild.me)
                if not permissions.read_message_history:
                    print(f"  Skipping #{channel.name} (no permission)")
                    continue

                print(f"  Processing #{channel.name}...")
                async for msg in channel.history(limit=None, after=limit_date):
                    if not msg.author.bot:
                        ts = msg.created_at.timestamp()
                        msg_dt = msg.created_at.replace(tzinfo=None) # naive for aggregation simplicity or convert to utc
                        
                        length = len(msg.content)
                        is_reply = (msg.reference is not None)
                        
                        user_messages[msg.author.id].append((ts, length, is_reply))
                        msg_count += 1
                        
                        # Aggregation Logic
                        today_str = msg_dt.strftime("%Y%m%d")
                        hour = msg_dt.hour
                        weekday = msg_dt.weekday()
                        
                        # Hourly
                        hourly_stats[f"{gid}:{today_str}"][hour] += 1
                        
                        # Msg Len
                        bucket = 0
                        if length == 0: bucket = 0
                        elif length <= 10: bucket = 5
                        elif length <= 50: bucket = 30
                        elif length <= 100: bucket = 75
                        elif length <= 200: bucket = 150
                        else: bucket = 250
                        
                        msglen_bucket_stats[bucket] += 1
                        
                        # Heatmap
                        heatmap_key = f"{weekday}_{hour}"
                        heatmap_stats[heatmap_key] += 1
                        
                        # Channel totals
                        channel_total_stats[channel.id] += 1
                        
                        # User Daily
                        user_daily_stats[today_str][msg.author.id] += 1
                        
                        # Leaderboard
                        leaderboard_stats[msg.author.id] += 1
                        
                        await self._update_user_info(msg.author)
                        
                        if msg_count % 1000 == 0:
                            print(f"    {msg_count} messages processed...")

            except discord.Forbidden:
                print(f"  Skipping #{channel.name} (Forbidden)")
            except Exception as e:
                print(f"  Error reading channel {channel.name}: {e}")
            
            # Update progress
            progress = int((idx / max(total_channels, 1)) * 50)
            await self.redis.set(progress_key, json.dumps({
                "status": "processing_messages", 
                "progress": progress, 
                "messages": msg_count,
                "current_channel": channel.name
            }))

        # Write messages to Redis
        print(f"Writing {msg_count} messages to Redis...")
        async with self.redis.pipeline() as pipe:
            # Raw events
            for uid, messages in user_messages.items():
                key = f"events:msg:{gid}:{uid}"
                mapping = {}
                for ts, length, is_reply in messages:
                    event_data = json.dumps({"len": length, "reply": is_reply})
                    mapping[event_data] = ts
                if mapping:
                    pipe.zadd(key, mapping)
            
            # Aggregated Stats
            # Hourly
            for key_suffix, hour_map in hourly_stats.items():
                real_key = f"stats:hourly:{key_suffix}"
                for hour, count in hour_map.items():
                    pipe.hincrby(real_key, str(hour), count)
                pipe.expire(real_key, 60 * 86400)
            
            # Msg Len
            for bucket, count in msglen_bucket_stats.items():
                pipe.zincrby(K_MSGLEN(gid), count, bucket)
            
            # Heatmap
            for hm_key, count in heatmap_stats.items():
                pipe.hincrby(K_HEATMAP(gid), hm_key, count)
            pipe.expire(K_HEATMAP(gid), 60 * 86400)
            
            # Total Msgs
            pipe.incrby(K_TOTAL_MSGS(gid), msg_count)
            
            # Channel Totals
            for cid, count in channel_total_stats.items():
                pipe.zincrby(f"stats:channel_total:{gid}", count, str(cid))
                
            # Leaderboard
            for uid, count in leaderboard_stats.items():
                pipe.zincrby(f"leaderboard:messages:{gid}", count, str(uid))

            await pipe.execute()

        await self.redis.set(progress_key, json.dumps({"status": "processing_messages_done", "progress": 55, "messages": msg_count}))

        # 2. Process Audit Logs
        print("Processing audit logs...")
        await self.redis.set(progress_key, json.dumps({"status": "processing_audit_logs", "progress": 60, "messages": msg_count}))
        
        audit_ops = 0
        user_actions = defaultdict(list)
        
        try:
            # We attempt to fetch audit logs. If the bot has no permission, it will fail gracefully.
            async for entry in guild.audit_logs(limit=None, after=limit_date):
                if entry.user and not entry.user.bot:
                    action_type = None
                    if entry.action == discord.AuditLogAction.ban: action_type = "ban"
                    elif entry.action == discord.AuditLogAction.kick: action_type = "kick"
                    elif entry.action == discord.AuditLogAction.unban: action_type = "unban"
                    elif entry.action == discord.AuditLogAction.message_delete: action_type = "msg_delete"
                    elif entry.action == discord.AuditLogAction.member_role_update: action_type = "role_update"
                    elif entry.action == discord.AuditLogAction.member_update:
                        if hasattr(entry, 'after') and hasattr(entry.after, 'timed_out_until'):
                            if entry.after.timed_out_until:
                                action_type = "timeout"
                    
                    if action_type:
                        ts = entry.created_at.timestamp()
                        user_actions[entry.user.id].append((ts, action_type))
                        audit_ops += 1
                        if isinstance(entry.user, discord.Member):
                            await self._update_user_info(entry.user)
        except discord.Forbidden:
             print("  No permission to read audit logs")
        except Exception as e:
             print(f"  Error reading audit logs: {e}")

        # Write actions to Redis
        print(f"Writing {audit_ops} audit actions to Redis...")
        async with self.redis.pipeline() as pipe:
            for uid, actions in user_actions.items():
                key = f"events:action:{gid}:{uid}"
                mapping = {}
                for ts, action_type in actions:
                    event_data = json.dumps({"type": action_type})
                    mapping[event_data] = ts
                if mapping:
                     pipe.zadd(key, mapping)
            await pipe.execute()

        await self.redis.set(progress_key, json.dumps({"status": "completed", "progress": 100, "messages": msg_count, "actions": audit_ops}))
        await self.redis.expire(progress_key, 3600)  # Keep for 1 hour
        print(f"Backfill completed: {msg_count} messages, {audit_ops} actions.")

if __name__ == "__main__":
    client = BackfillClient(args.guild_id, args.days)
    client.run(args.token)
