from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseRepository(ABC):
    """
    Abstract base class for data access.
    Allows swapping Redis with PostgreSQL or Mock databases for testing.
    """
    
    @abstractmethod
    async def get_client(self):
        pass

    @abstractmethod
    async def load_member_stats(self, guild_id: int, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def get_activity_stats(self, guild_id: int, start_date: str = None, end_date: str = None, days: int = 30) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def get_deep_stats_redis(self, guild_id: int, start_date: str = None, end_date: str = None, role_id: str = "all") -> Dict[str, Any]:
        pass

    @abstractmethod
    async def get_redis_dashboard_stats(self, guild_id: int, start_date: str = None, end_date: str = None, role_id: str = None) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def get_realtime_online_count(self, guild_id: int = None) -> int:
        pass

    @abstractmethod
    async def get_user_guilds(self, user_id: str) -> List[Dict[str, Any]]:
        pass
        
    @abstractmethod
    async def save_user_guilds(self, user_id: str, guilds_data: List[Dict[str, Any]], expiry_seconds: int = 86400):
        pass
        
    @abstractmethod
    async def get_bot_guilds(self) -> List[str]:
        pass
        
    @abstractmethod
    async def get_cached_roles(self, guild_id: int) -> List[Dict[str, str]]:
        pass
        
    # the rest of the functions from redis_repo...
