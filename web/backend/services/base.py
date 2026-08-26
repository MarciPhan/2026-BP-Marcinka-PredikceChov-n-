from abc import ABC, abstractmethod
from typing import Dict, Any, List

class BaseAnalyticsService(ABC):
    """
    Abstract base class for the Analytics Service layer.
    Allows swapping complex ML/Math logic (Markov, Kaplan-Meier)
    for simpler heuristic models or Mock services during testing.
    """
    
    @abstractmethod
    async def get_trend_analysis(self, guild_id: int) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def get_engagement_score(self, guild_id: int, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def get_security_score(self, guild_id: int, days: int = 7) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def get_insights(self, guild_id: int) -> List[Dict[str, str]]:
        pass

    @abstractmethod
    async def get_health_research_data(self, guild_id: int) -> dict:
        pass
        
    @abstractmethod
    async def get_action_weights(self) -> dict:
        pass

    @abstractmethod
    async def get_data_quality_score(self, guild_id: int) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def get_channel_activity(self, guild_id: int, start_date: str = None, end_date: str = None, platform: str = "all", channel_id: str = None, topic_id: str = None):
        pass

    @abstractmethod
    async def get_community_health_support(self, guild_id: int, days: int = 30):
        pass
