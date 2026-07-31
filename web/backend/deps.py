from .repositories.redis_repo import RedisRepository
from .repositories.base import BaseRepository

# Globální instance pro produkci
_redis_repo = RedisRepository()

async def get_repository() -> BaseRepository:
    """
    FastAPI Dependency pro získání datového repozitáře.
    Umožňuje snadné nahrazení za MockRepository v testech nebo PostgresRepository v budoucnu.
    """
    return _redis_repo
