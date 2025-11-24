from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional
import json

@dataclass
class Message:
    id: str
    source: str  # 'discord' or 'discourse'
    source_id: str
    author_hash: str
    content_preview: str
    timestamp: str
    channel_name: str
    has_attachments: bool = False
    reply_count: int = 0
    reaction_count: int = 0
    
    def to_dict(self):
        return asdict(self)
    
    def to_json(self):
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str):
        data = json.loads(json_str)
        return cls(**data)

@dataclass
class Statistics:
    total_messages: int = 0
    messages_last_hour: int = 0
    active_users_last_hour: int = 0
    discord_messages: int = 0
    discourse_messages: int = 0
    
    def to_dict(self):
        return asdict(self)
