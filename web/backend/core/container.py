from ..repositories.base import BaseRepository
from ..repositories.redis_repo import RedisRepository
from ..services.base import BaseAnalyticsService
from ..services.analytics_service import DefaultAnalyticsService

class AppContainer:
    """
    Global Dependency Injection Container.
    Holds the active implementations for all architectural layers.
    Allows for entire layers to be swapped out easily.
    """
    repo: BaseRepository = None
    analytics: BaseAnalyticsService = None

    @classmethod
    def init(cls, repo_override: BaseRepository = None, analytics_override: BaseAnalyticsService = None):
        cls.repo = repo_override or RedisRepository()
        cls.analytics = analytics_override or DefaultAnalyticsService(repo=cls.repo)

# Initialize the default production dependencies immediately
AppContainer.init()
