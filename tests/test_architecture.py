import asyncio
import sys
import pytest
from pathlib import Path
from typing import Dict, Any, List

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from web.backend.core.container import AppContainer
from web.backend.repositories.base import BaseRepository
from web.backend.services.analytics_service import DefaultAnalyticsService

class MockRepository(BaseRepository):
    """
    Simulovaná databáze pro testování. Neukládá se na disk, nepotřebuje Redis.
    Perfektní pro Unit Testy, kde chceme testovat pouze matematiku v AnalyticsService.
    """
    
    async def get_client(self):
        return None

    async def load_member_stats(self, guild_id: int, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        # Simulujeme postupný růst serveru (100 -> 105 -> 110)
        return {
            "labels": ["2026-07-01", "2026-07-02", "2026-07-03"],
            "total": [100, 105, 110],
            "joins": [5, 5, 5],
            "leaves": [0, 0, 0]
        }

    async def get_activity_stats(self, guild_id: int, start_date: str = None, end_date: str = None, days: int = 30) -> Dict[str, Any]:
        return {
            "dau_data": [10, 10, 10, 10, 10, 15, 20],
            "mau_data": [50, 50, 50, 50, 50, 55, 60],
            "dau_labels": ["d1", "d2", "d3", "d4", "d5", "d6", "d7"],
            "avg_dau": 12
        }

    async def get_deep_stats_redis(self, *args, **kwargs) -> Dict[str, Any]:
        return {}
    
    async def get_redis_dashboard_stats(self, *args, **kwargs) -> Dict[str, Any]:
        return {}

    async def get_realtime_online_count(self, guild_id: int = None) -> int:
        return 42

    async def get_user_guilds(self, user_id: str) -> List[Dict[str, Any]]:
        return []
        
    async def save_user_guilds(self, *args, **kwargs):
        pass
        
    async def get_bot_guilds(self) -> List[str]:
        return []
        
    async def get_cached_roles(self, guild_id: int) -> List[Dict[str, str]]:
        return []

@pytest.mark.asyncio
async def test_swappable_architecture():
    print("="*50)
    print("1. Spouštím test s originálním Redis repozitářem (může selhat, pokud Redis neběží)")
    
    # Original (Redis)
    AppContainer.init()
    try:
        online = await AppContainer.repo.get_realtime_online_count()
        print(f"✅ Původní repo vrátil online count: {online}")
    except Exception as e:
        print(f"❌ Redis není dostupný: {e}")

    print("\n" + "="*50)
    print("2. Měním repozitář za MockRepository...")
    
    # DI in action
    mock_repo = MockRepository()
    AppContainer.init(repo_override=mock_repo)
    
    # Měli bychom dostat 42 nezávisle na Redis databázi
    online = await AppContainer.repo.get_realtime_online_count()
    print(f"✅ Mock repo vrátil online count: {online}")
    
    print("\n" + "="*50)
    print("3. Testování výpočtů v AnalyticsService s Mock daty")
    
    # get_trend_analysis volá load_member_stats() pod kapotou, 
    # spočítá "změnu" a % růst nad poli 100 -> 110.
    trend = await AppContainer.analytics.get_trend_analysis(guild_id=123)
    
    print("Výsledek predikce DAU:")
    print(f"Průměr: {trend.get('avg_dau')}")
    print(f"Růst: {trend.get('growth_30d')}%")
    print(f"Predikce: {trend.get('prediction')}")
    
    assert trend.get('growth_30d') == 100.0  # (20 - 10) / 10 = 100%
    assert trend.get('avg_dau') == 12        # (85 / 7) = 12
    assert trend.get('prediction') == 24     # 12 * 2.0 = 24
    
    print("\n✅ Všechny matematické výpočty fungují správně nad Mock databází!")
    print("="*50)


if __name__ == "__main__":
    asyncio.run(test_swappable_architecture())
