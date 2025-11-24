import redis
import hashlib
import json
import uuid
from datetime import datetime, timedelta
from backend.models import Message, Statistics
from typing import List, Dict, Optional


class RedisDatabase:
    def __init__(self, host: str, port: int, db: int, password: Optional[str], salt: str):
        self.redis_client = redis.Redis(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True
        )
        self.salt = salt

        self.MESSAGES_KEY = "messages"
        self.MESSAGE_DATA_PREFIX = "message:"
        self.STATS_KEY = "stats"
        self.USER_ACTIVITY_PREFIX = "user_activity:"

        if not self.redis_client.exists(self.STATS_KEY):
            self._init_stats()

    def _init_stats(self):
        stats = Statistics()
        self.redis_client.hset(self.STATS_KEY, mapping=stats.to_dict())

    def anonymize_user(self, user_id: str) -> str:
        return hashlib.sha256(f"{user_id}{self.salt}".encode()).hexdigest()

    def add_message(
        self,
        source: str,
        source_id: str,
        author_id: str,
        content: str,
        channel: str,
        attachments: int = 0,
        replies: int = 0,
        reactions: int = 0,
        is_historical: bool = False,
        original_timestamp: Optional[datetime] = None
    ) -> Message:

        if original_timestamp:
            timestamp = original_timestamp
        else:
            timestamp = datetime.utcnow()

        message_id = str(uuid.uuid4())
        author_hash = self.anonymize_user(author_id)

        msg_obj = Message(
            id=message_id,
            source=source,
            source_id=source_id,
            author_hash=author_hash,
            content_preview=content[:200] if content else "",
            timestamp=timestamp.isoformat(),
            channel_name=channel,
            has_attachments=bool(attachments),
            reply_count=int(replies),
            reaction_count=int(reactions),
        )

        msg_dict = msg_obj.to_dict()

        safe_dict = {
            k: ("True" if v is True else "False" if v is False else v)
            for k, v in msg_dict.items()
        }

        pipe = self.redis_client.pipeline()

        # Sorted set with actual timestamp
        pipe.zadd(self.MESSAGES_KEY, {message_id: float(timestamp.timestamp())})
        pipe.hset(f"{self.MESSAGE_DATA_PREFIX}{message_id}", mapping=safe_dict)

        # Update statistics - SEPARATE counters for live and historical
        if not is_historical:
            # Live message counters
            pipe.hincrby(self.STATS_KEY, "live_messages", 1)
            pipe.hincrby(self.STATS_KEY, f"{source}_live", 1)
            
            # User activity tracking (only for live messages)
            hour_key = f"{self.USER_ACTIVITY_PREFIX}{datetime.utcnow().strftime('%Y%m%d%H')}"
            pipe.sadd(hour_key, author_hash)
            pipe.expire(hour_key, 3600)
            
            print(f"✅ LIVE message added: {source} - {content[:50]}")
        else:
            # Historical message counters
            pipe.hincrby(self.STATS_KEY, "historical_messages", 1)
            pipe.hincrby(self.STATS_KEY, f"{source}_historical", 1)
            
            print(f"📦 HISTORICAL message added: {source}")

        pipe.execute()

        return msg_obj

    def set_checkpoint(self, collector_name: str, value: str):
        key = f"checkpoint:{collector_name}"
        self.redis_client.set(key, value)
        print(f"✅ Checkpoint saved: {collector_name} = {value}")

    def get_checkpoint(self, collector_name: str) -> Optional[str]:
        key = f"checkpoint:{collector_name}"
        val = self.redis_client.get(key)
        return val if val else None

    def publish_realtime_message(self, channel: str, data: Dict):
        """Publish message to Redis pub/sub channel"""
        try:
            payload = json.dumps(data)
            self.redis_client.publish(channel, payload)
            print(f"📡 Published to {channel}: {data.get('type', 'unknown')}")
        except Exception as e:
            print(f"❌ Failed to publish: {e}")

    def get_pubsub(self):
        return self.redis_client.pubsub()

    def get_statistics(self) -> Dict:
        stats = self.redis_client.hgetall(self.STATS_KEY)

        now = datetime.utcnow()
        hour_ago = now - timedelta(hours=1)

        # Count messages in last hour
        messages_last_hour = self.redis_client.zcount(
            self.MESSAGES_KEY,
            hour_ago.timestamp(),
            now.timestamp()
        )

        # Active users in last hour
        current_hour_key = f"{self.USER_ACTIVITY_PREFIX}{now.strftime('%Y%m%d%H')}"
        prev_hour_key = f"{self.USER_ACTIVITY_PREFIX}{(now - timedelta(hours=1)).strftime('%Y%m%d%H')}"
        active_users = len(self.redis_client.sunion(current_hour_key, prev_hour_key))

        # SEPARATE live and historical counts
        live_messages = int(stats.get("live_messages", 0))
        historical_messages = int(stats.get("historical_messages", 0))
        total_messages = live_messages + historical_messages

        discord_live = int(stats.get("discord_live", 0))
        discord_historical = int(stats.get("discord_historical", 0))
        discord_total = discord_live + discord_historical

        discourse_live = int(stats.get("discourse_live", 0))
        discourse_historical = int(stats.get("discourse_historical", 0))
        discourse_total = discourse_live + discourse_historical

        result = {
            # Total counts
            "total_messages": total_messages,
            "discord_messages": discord_total,
            "discourse_messages": discourse_total,
            
            # Live counts (for realtime stats)
            "live_messages": live_messages,
            "discord_live": discord_live,
            "discourse_live": discourse_live,
            
            # Historical counts
            "historical_messages": historical_messages,
            "discord_historical": discord_historical,
            "discourse_historical": discourse_historical,
            
            # Time-based metrics
            "messages_last_hour": messages_last_hour,
            "active_users_last_hour": active_users,
        }

        print(f"📊 Stats: Live={live_messages}, Historical={historical_messages}, LastHour={messages_last_hour}")
        
        return result

    def get_recent_messages(self, limit: int = 100) -> List[Dict]:
        """Get recent messages for API"""
        try:
            # Get most recent message IDs
            message_ids = self.redis_client.zrevrange(self.MESSAGES_KEY, 0, limit - 1)
            
            messages = []
            for msg_id in message_ids:
                msg_data = self.redis_client.hgetall(f"{self.MESSAGE_DATA_PREFIX}{msg_id}")
                if msg_data:
                    messages.append(msg_data)
            
            return messages
        except Exception as e:
            print(f"❌ Error getting recent messages: {e}")
            return []