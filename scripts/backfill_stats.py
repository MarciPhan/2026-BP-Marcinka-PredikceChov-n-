import discord
import argparse
import asyncio
import os
import sys
import json
import time
from datetime import datetime, timedelta, timezone
from collections import defaultdict

# Setup paths
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from shared.redis_client import get_redis_client
from shared.community_health import is_probable_question
import config.config as config_module

async def run_backfill(guild_id: int, token: str, days: int = 30):
    r = await get_redis_client()
    await r.hset(f"backfill:status:{guild_id}", mapping={
        "status": "processing",
        "total_messages": 0,
        "current_channel": "připojování"
    })
    
    intents = discord.Intents.default()
    intents.message_content = True
    intents.guilds = True
    intents.members = True
    
    client = discord.Client(intents=intents)
    
    @client.event
    async def on_ready():
        print(f"Backfill script logged in as {client.user}")
        guild = client.get_guild(guild_id)
        
        if not guild:
            await r.hset(f"backfill:status:{guild_id}", mapping={
                "status": "error",
                "message": "Guild not found"
            })
            await client.close()
            return
            
        discord_epoch = datetime(2015, 1, 1)
        limit_date = datetime.now() - timedelta(days=days)
        if limit_date < discord_epoch: 
            limit_date = discord_epoch
            
        msg_count = 0
        
        raw_cfg = await r.hgetall(f"cfg:health:{guild_id}")
        support_ids = await r.smembers(f"cfg:health:support_channels:{guild_id}")
        help_enabled = raw_cfg.get("help_requests_enabled") == "true"
        question_mode = raw_cfg.get("question_mode", "heuristic")
        
        for channel in guild.text_channels:
            try:
                await r.hset(f"backfill:status:{guild_id}", "current_channel", channel.name)
                
                async for msg in channel.history(limit=None, after=limit_date, oldest_first=True):
                    if not msg.author.bot:
                        ts = msg.created_at.timestamp()
                        uid = msg.author.id
                        
                        # 1. LEGACY ACTIVITY DATA
                        key_legacy = f"events:msg:{guild_id}:{uid}"
                        event_data = json.dumps({
                            "mid": msg.id, 
                            "channel_id": channel.id,
                            "len": len(msg.content), 
                            "reply": msg.reference is not None, 
                            "reply_to_mid": msg.reference.message_id if msg.reference and hasattr(msg.reference, 'message_id') else None,
                            "reaction_count": len(msg.reactions),
                            "is_question": msg.content.strip().endswith('?') if msg.content else False
                        })
                        await r.zadd(key_legacy, {event_data: ts})
                        
                        # 2. NEW COMMUNITY HEALTH DATA
                        reply_to = msg.reference.message_id if msg.reference and hasattr(msg.reference, 'message_id') else ""
                        reply_author_id = "" # Simplified
                        
                        mapping = {
                            "message_id": str(msg.id),
                            "author_id": str(uid),
                            "channel_id": str(channel.id),
                            "created_at": str(ts),
                            "reply_to": str(reply_to),
                            "reply_author_id": str(reply_author_id),
                            "is_question": "1" if is_probable_question(msg.content) else "0",
                            "reaction_count": str(sum(reaction.count for reaction in msg.reactions)),
                        }
                        
                        health_key = f"health:message:{guild_id}:{msg.id}"
                        async with r.pipeline() as pipe:
                            pipe.hset(health_key, mapping=mapping)
                            pipe.hset(f"channel:info:{channel.id}", mapping={"name": getattr(channel, "name", str(channel.id)), "guild_id": str(guild_id)})
                            pipe.zadd(f"health:messages:{guild_id}", {str(msg.id): ts})
                            pipe.zadd(f"health:user_messages:{guild_id}:{uid}", {str(msg.id): ts})
                            
                            if help_enabled and str(channel.id) in support_ids:
                                is_q = is_probable_question(msg.content)
                                if question_mode == "all" or is_q:
                                    help_key = f"health:help:{guild_id}:{msg.id}"
                                    pipe.hset(help_key, mapping={
                                        "message_id": str(msg.id), "author_id": str(msg.author.id),
                                        "channel_id": str(channel.id), "created_at": str(ts),
                                        "status": "open", "answered_at": "", "responder_id": "",
                                        "response_id": "", "response_seconds": "", "acknowledged_by_reaction": "0"
                                    })
                                    pipe.zadd(f"health:help:all:{guild_id}", {str(msg.id): ts})
                                    pipe.zadd(f"health:help:open:{guild_id}", {str(msg.id): ts})
                                    pipe.zadd(f"health:help:user:{guild_id}:{uid}", {str(msg.id): ts})
                            
                            # Cache user info
                            pipe.hset(f"user:info:{uid}", mapping={"name": msg.author.display_name, "avatar": msg.author.display_avatar.url})
                            
                            # 3. DASHBOARD MAIN STATS (from stats_hll.py)
                            msg_dt = datetime.fromtimestamp(ts, tz=timezone.utc)
                            d_str = msg_dt.strftime("%Y%m%d")
                            hour = msg_dt.hour
                            weekday = msg_dt.weekday()
                            msg_len = len(msg.content)
                            
                            if msg_len == 0: bucket = 0
                            elif msg_len <= 10: bucket = 5
                            elif msg_len <= 50: bucket = 30
                            elif msg_len <= 100: bucket = 75
                            elif msg_len <= 200: bucket = 150
                            else: bucket = 250
                            
                            pipe.pfadd(f"hll:dau:{guild_id}:{d_str}", str(uid))
                            pipe.hincrby(f"stats:hourly:{guild_id}:{d_str}", hour, 1)
                            pipe.hincrby(f"stats:heatmap:{guild_id}", f"{weekday}_{hour}", 1)
                            pipe.zincrby(f"stats:msglen:{guild_id}", 1, bucket)
                            pipe.incr(f"stats:total_msgs:{guild_id}")
                            pipe.incr(f"stats:channel:{guild_id}:{channel.id}:{d_str}")
                            pipe.zincrby(f"stats:channel_total:{guild_id}", 1, str(channel.id))
                            pipe.zincrby(f"leaderboard:messages:{guild_id}", 1, str(uid))
                            pipe.zincrby(f"stats:user_daily:{guild_id}:{d_str}", 1, str(uid))
                            pipe.lpush(f"leaderboard:msg_lengths:{guild_id}:{uid}", msg_len)
                            pipe.ltrim(f"leaderboard:msg_lengths:{guild_id}:{uid}", 0, 99)
                            pipe.hincrby(f"stats:channel_hourly:{guild_id}:{channel.id}", hour, 1)
                            
                            await pipe.execute()
                            
                        # Mark help answered
                        if msg.reference and msg.reference.message_id:
                            parent_id = msg.reference.message_id
                            hkey = f"health:help:{guild_id}:{parent_id}"
                            if await r.exists(hkey) and await r.hget(hkey, "status") != "answered":
                                created = float(await r.hget(hkey, "created_at") or ts)
                                async with r.pipeline() as ppipe:
                                    ppipe.hset(hkey, mapping={
                                        "status": "answered", "answered_at": str(ts),
                                        "responder_id": str(uid), "response_id": str(msg.id),
                                        "response_seconds": str(max(0, int(ts - created)))
                                    })
                                    ppipe.zrem(f"health:help:open:{guild_id}", str(parent_id))
                                    ppipe.zadd(f"health:help:answered:{guild_id}", {str(parent_id): ts})
                                    await ppipe.execute()
                            
                        msg_count += 1
                        
                        if msg_count % 500 == 0:
                            await r.hset(f"backfill:status:{guild_id}", "total_messages", msg_count)
                            
            except discord.Forbidden:
                pass
            except Exception as e:
                print(f"Error in {channel.name}: {e}")
                
        # Audit logs
        audit_ops = 0
        try:
            await r.hset(f"backfill:status:{guild_id}", "current_channel", "audit logs")
            async for entry in guild.audit_logs(limit=None, after=limit_date, oldest_first=True):
                if entry.user and not entry.user.bot:
                    action_type = None
                    if entry.action == discord.AuditLogAction.ban: action_type = "ban"
                    elif entry.action == discord.AuditLogAction.kick: action_type = "kick"
                    elif entry.action == discord.AuditLogAction.unban: action_type = "unban"
                    elif entry.action == discord.AuditLogAction.message_delete: action_type = "msg_delete"
                    elif entry.action == discord.AuditLogAction.member_update:
                        if getattr(entry.after, "timed_out_until", None):
                            action_type = "timeout"
                    elif entry.action == discord.AuditLogAction.member_role_update:
                        action_type = "role_update"
                        
                    if action_type:
                        ts = entry.created_at.timestamp()
                        
                        # 1. LEGACY ACTIVITY DATA
                        key_legacy_action = f"events:action:{guild_id}:{entry.user.id}"
                        event_data = json.dumps({"type": action_type})
                        await r.zadd(key_legacy_action, {event_data: ts})
                        
                        # 2. NEW COMMUNITY HEALTH DATA
                        target_id = getattr(entry.target, "id", None)
                        channel_id = getattr(getattr(entry, "extra", None), "channel", None)
                        channel_id = getattr(channel_id, "id", None)
                        
                        event_key = f"health:mod_event:{guild_id}:{entry.id}"
                        mapping = {
                            "event_id": str(entry.id),
                            "moderator_id": str(entry.user.id),
                            "target_user_id": str(target_id or ""),
                            "action_type": action_type,
                            "channel_id": str(channel_id or ""),
                            "created_at": str(ts),
                            "resolved_at": str(ts) if action_type == "unban" else "",
                        }
                        
                        async with r.pipeline() as pipe:
                            pipe.hset(event_key, mapping=mapping)
                            pipe.zadd(f"health:mod_events:{guild_id}", {str(entry.id): ts})
                            pipe.zadd(f"health:mod_events:moderator:{guild_id}:{entry.user.id}", {str(entry.id): ts})
                            if target_id:
                                pipe.zadd(f"health:mod_events:target:{guild_id}:{target_id}", {str(entry.id): ts})
                                pipe.zadd(f"health:mod_pair:{guild_id}:{target_id}:{entry.user.id}", {str(entry.id): ts})
                            
                            # Cache user info
                            pipe.hset(f"user:info:{entry.user.id}", mapping={"name": entry.user.display_name, "avatar": entry.user.display_avatar.url})
                            if target_id and hasattr(entry.target, "display_name"):
                                pipe.hset(f"user:info:{target_id}", mapping={"name": entry.target.display_name, "avatar": entry.target.display_avatar.url})
                                
                            await pipe.execute()
                            
                        audit_ops += 1
        except Exception:
            pass
            
        # Store events
        for event in guild.scheduled_events:
            ch_id = getattr(getattr(event, "channel", None), "id", None)
            emapping = {
                "event_id": str(event.id), "name": event.name[:200], "channel_id": str(ch_id or ""),
                "scheduled_start": str(event.start_time.timestamp() if event.start_time else ""),
                "scheduled_end": str(event.end_time.timestamp() if event.end_time else ""),
                "status": str(event.status)
            }
            await r.hset(f"health:event:{guild_id}:{event.id}", mapping=emapping)
            await r.sadd(f"health:events:{guild_id}", str(event.id))
            
        await r.hset(f"backfill:status:{guild_id}", mapping={
            "status": "completed",
            "total_messages": msg_count,
            "current_channel": "hotovo"
        })
        print(f"Backfill finished. {msg_count} messages, {audit_ops} audit actions.")
        await client.close()

    await client.start(token)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--guild_id", type=int, required=True)
    parser.add_argument("--token", type=str, required=True)
    parser.add_argument("--days", type=int, default=30)
    args = parser.parse_args()
    
    asyncio.run(run_backfill(args.guild_id, args.token, args.days))
