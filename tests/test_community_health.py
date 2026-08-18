import time

import fakeredis.aioredis
import pytest

from shared.community_health import (
    api_key_digest,
    factual_role_evidence,
    is_probable_question,
    normalise_config,
)
from web.backend.services.community_health_service import CommunityHealthService


def test_question_heuristic_is_conservative():
    assert is_probable_question("Jak to nastavím")
    assert is_probable_question("Can someone help?")
    assert not is_probable_question("Dnes bude pravidelná schůzka")
    assert not is_probable_question("")


def test_config_and_human_decision_principle():
    cfg = normalise_config({"help_requests_enabled": "true", "help_timeout_hours": "48"})
    assert cfg["help_requests_enabled"] is True
    assert cfg["help_timeout_hours"] == 48
    evidence = factual_role_evidence(
        messages=10, replies=4, channels=3, received_reactions=8,
        moderation_incidents=0, manual_review=None,
    )
    assert evidence["decision"] is None
    assert "člověk" in evidence["notice"]
    assert api_key_digest("secret") != "secret"


@pytest.mark.asyncio
async def test_conflicts_help_and_departure_context():
    r = fakeredis.aioredis.FakeRedis(decode_responses=True)
    service = CommunityHealthService(r)
    gid = 123
    now = time.time()

    await r.hset("user:info:10", mapping={"name": "Člen"})
    await r.hset("user:info:20", mapping={"name": "Moderátor"})
    for i, action in enumerate(("timeout", "kick"), 1):
        event_id = str(100 + i)
        await r.hset(f"health:mod_event:{gid}:{event_id}", mapping={
            "event_id": event_id, "target_user_id": "10", "moderator_id": "20",
            "action_type": action, "created_at": str(now - i * 60),
        })
        await r.zadd(f"health:mod_pair:{gid}:10:20", {event_id: now - i * 60})
        await r.zadd(f"health:mod_events:target:{gid}:10", {event_id: now - i * 60})

    await r.hset(f"cfg:health:{gid}", mapping={"help_timeout_hours": "1"})
    await r.hset(f"health:help:{gid}:500", mapping={
        "message_id": "500", "author_id": "10", "channel_id": "99",
        "created_at": str(now - 7200), "status": "open", "acknowledged_by_reaction": "0",
    })
    await r.zadd(f"health:help:all:{gid}", {"500": now - 7200})

    departure_id = f"10:{int(now)}"
    await r.hset(f"health:departure:{gid}:{departure_id}", mapping={
        "departure_id": departure_id, "user_id": "10", "left_at": str(now),
        "last_message_at": str(now - 300), "recent_moderation_events": "2",
        "recent_help_requests": "1", "interpretation": "temporal_context_only",
    })
    await r.zadd(f"health:departures:{gid}", {departure_id: now})

    conflicts = await service.conflict_summary(gid)
    assert conflicts["repeated_pairs"] == 1
    assert conflicts["pairs"][0]["severity"] == "high"

    help_data = await service.help_requests(gid)
    assert help_data["open"] == 1
    assert help_data["overdue"] == 1

    departures = await service.departures(gid)
    assert departures["with_preceding_signal"] == 1
    assert "neurčuje příčinu" in departures["items"][0]["notice"]
    await r.aclose()
