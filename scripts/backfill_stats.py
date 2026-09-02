import discord
import argparse
import asyncio
import os
import sys
import json
import time
from datetime import datetime, timedelta
from collections import defaultdict

# Setup paths
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from shared.redis_client import get_redis_client
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
        BATCH_SIZE = 10000
        
        for channel in guild.text_channels:
            try:
                await r.hset(f"backfill:status:{guild_id}", "current_channel", channel.name)
                
                async for msg in channel.history(limit=None, after=limit_date):
                    if not msg.author.bot:
                        ts = msg.created_at.timestamp()
                        uid = msg.author.id
                        
                        key = f"events:msg:{guild_id}:{uid}"
                        event_data = json.dumps({
                            "mid": msg.id, 
                            "channel_id": channel.id,
                            "len": len(msg.content), 
                            "reply": msg.reference is not None, 
                            "reply_to_mid": msg.reference.message_id if msg.reference and hasattr(msg.reference, 'message_id') else None,
                            "reaction_count": len(msg.reactions),
                            "is_question": msg.content.strip().endswith('?') if msg.content else False
                        })
                        
                        await r.zadd(key, {event_data: ts})
                        msg_count += 1
                        
                        if msg_count % 100 == 0:
                            await r.hset(f"backfill:status:{guild_id}", "total_messages", msg_count)
                            
            except discord.Forbidden:
                pass
            except Exception as e:
                print(f"Error in {channel.name}: {e}")
                
        # Audit logs (simplified)
        audit_ops = 0
        try:
            await r.hset(f"backfill:status:{guild_id}", "current_channel", "audit logs")
            async for entry in guild.audit_logs(limit=None, after=limit_date):
                if entry.user and not entry.user.bot:
                    action_type = None
                    if entry.action == discord.AuditLogAction.ban: action_type = "ban"
                    elif entry.action == discord.AuditLogAction.kick: action_type = "kick"
                    elif entry.action == discord.AuditLogAction.unban: action_type = "unban"
                    elif entry.action == discord.AuditLogAction.message_delete: action_type = "msg_delete"
                    
                    if action_type:
                        ts = entry.created_at.timestamp()
                        key = f"events:action:{guild_id}:{entry.user.id}"
                        event_data = json.dumps({"type": action_type})
                        await r.zadd(key, {event_data: ts})
                        audit_ops += 1
        except Exception:
            pass
            
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
