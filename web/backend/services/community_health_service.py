from __future__ import annotations

import json
import time
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from shared.community_health import conflict_severity, factual_role_evidence, normalise_config


class CommunityHealthService:
    def __init__(self, redis_client):
        self.r = redis_client

    @staticmethod
    def _range(days: int = 30, start_date: str | None = None, end_date: str | None = None) -> tuple[float, float]:
        if end_date:
            end = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1) - timedelta(seconds=1)
        else:
            end = datetime.now()
        if start_date:
            start = datetime.strptime(start_date, "%Y-%m-%d")
        else:
            start = end - timedelta(days=max(1, days))
        return start.timestamp(), end.timestamp()

    async def config(self, guild_id: int | str) -> Dict[str, Any]:
        raw = await self.r.hgetall(f"cfg:health:{guild_id}")
        cfg = normalise_config(raw)
        cfg["support_channel_ids"] = sorted(await self.r.smembers(f"cfg:health:support_channels:{guild_id}"))
        return cfg

    async def _user(self, uid: str | int | None) -> Dict[str, Any]:
        if not uid:
            return {"id": None, "name": "Neznámý uživatel", "avatar": None}
        info = await self.r.hgetall(f"user:info:{uid}")
        return {
            "id": str(uid),
            "name": info.get("name") or info.get("username") or f"User {uid}",
            "avatar": info.get("avatar") or None,
        }

    async def _channel_name(self, channel_id: str | int | None) -> str:
        if not channel_id:
            return "Neznámý kanál"
        name = await self.r.hget(f"channel:info:{channel_id}", "name")
        return name or f"Channel {channel_id}"

    async def conflict_summary(self, guild_id: int | str, days: int = 30, start_date: str = None, end_date: str = None, limit: int = 25) -> Dict[str, Any]:
        start_ts, end_ts = self._range(days, start_date, end_date)
        rows: List[Dict[str, Any]] = []
        action_totals = Counter()

        async for key in self.r.scan_iter(f"health:mod_pair:{guild_id}:*"):
            parts = key.split(":")
            if len(parts) < 5:
                continue
            target_id, moderator_id = parts[-2], parts[-1]
            event_ids = await self.r.zrangebyscore(key, start_ts, end_ts)
            if not event_ids:
                continue
            actions = []
            last_at = 0.0
            for event_id in event_ids:
                event = await self.r.hgetall(f"health:mod_event:{guild_id}:{event_id}")
                if not event:
                    continue
                action = event.get("action_type", "unknown")
                actions.append(action)
                action_totals[action] += 1
                last_at = max(last_at, float(event.get("created_at") or 0))
            if not actions:
                continue
            target, moderator = await self._user(target_id), await self._user(moderator_id)
            rows.append({
                "target": target,
                "moderator": moderator,
                "event_count": len(actions),
                "actions": dict(Counter(actions)),
                "severity": conflict_severity(actions),
                "last_event_at": last_at,
                "is_repeated": len(actions) >= 2,
                "notice": "Opakování je časová souvislost, nikoli automatický důkaz pochybení.",
            })
        rows.sort(key=lambda row: (row["event_count"], row["last_event_at"]), reverse=True)
        repeated = sum(1 for row in rows if row["is_repeated"])
        return {
            "period": {"start": start_ts, "end": end_ts},
            "pairs": rows[:limit],
            "repeated_pairs": repeated,
            "total_pairs": len(rows),
            "action_totals": dict(action_totals),
        }

    async def help_requests(self, guild_id: int | str, days: int = 30, start_date: str = None, end_date: str = None, limit: int = 50) -> Dict[str, Any]:
        start_ts, end_ts = self._range(days, start_date, end_date)
        ids = await self.r.zrevrangebyscore(f"health:help:all:{guild_id}", end_ts, start_ts, start=0, num=max(limit * 4, 100))
        rows = []
        response_times = []
        ignored_by_user = Counter()
        now = time.time()
        cfg = await self.config(guild_id)
        timeout_seconds = int(cfg["help_timeout_hours"]) * 3600

        for mid in ids:
            item = await self.r.hgetall(f"health:help:{guild_id}:{mid}")
            if not item:
                continue
            created = float(item.get("created_at") or 0)
            status = item.get("status", "open")
            response_seconds = int(float(item.get("response_seconds") or 0))
            overdue = status == "open" and now - created >= timeout_seconds
            if response_seconds:
                response_times.append(response_seconds)
            if overdue:
                ignored_by_user[item.get("author_id", "unknown")] += 1
            author = await self._user(item.get("author_id"))
            rows.append({
                "message_id": mid,
                "author": author,
                "channel_id": item.get("channel_id"),
                "channel_name": await self._channel_name(item.get("channel_id")),
                "created_at": created,
                "status": status,
                "overdue": overdue,
                "acknowledged_by_reaction": item.get("acknowledged_by_reaction") == "1",
                "response_seconds": response_seconds or None,
            })
        open_count = sum(1 for row in rows if row["status"] == "open")
        overdue_count = sum(1 for row in rows if row["overdue"])
        repeat_users = []
        for uid, count in ignored_by_user.most_common(10):
            repeat_users.append({"user": await self._user(uid), "overdue_requests": count})
        return {
            "items": rows[:limit],
            "total": len(rows),
            "open": open_count,
            "overdue": overdue_count,
            "answered": len(rows) - open_count,
            "median_response_seconds": sorted(response_times)[len(response_times) // 2] if response_times else None,
            "repeat_unanswered_users": repeat_users,
        }

    async def departures(self, guild_id: int | str, days: int = 30, start_date: str = None, end_date: str = None, limit: int = 50) -> Dict[str, Any]:
        start_ts, end_ts = self._range(days, start_date, end_date)
        ids = await self.r.zrevrangebyscore(f"health:departures:{guild_id}", end_ts, start_ts, start=0, num=limit)
        rows = []
        for departure_id in ids:
            item = await self.r.hgetall(f"health:departure:{guild_id}:{departure_id}")
            if not item:
                continue
            user = await self._user(item.get("user_id"))
            mod_events = int(item.get("recent_moderation_events") or 0)
            help_requests = int(item.get("recent_help_requests") or 0)
            rows.append({
                "departure_id": departure_id,
                "user": user,
                "left_at": float(item.get("left_at") or 0),
                "last_message_at": float(item.get("last_message_at") or 0) or None,
                "recent_moderation_events": mod_events,
                "recent_help_requests": help_requests,
                "has_preceding_negative_signal": bool(mod_events or help_requests),
                "notice": "Systém zobrazuje pouze časovou posloupnost a neurčuje příčinu odchodu.",
            })
        return {
            "items": rows,
            "total": len(rows),
            "with_preceding_signal": sum(1 for row in rows if row["has_preceding_negative_signal"]),
        }

    async def moderator_workload(self, guild_id: int | str, days: int = 30, start_date: str = None, end_date: str = None, limit: int = 30) -> Dict[str, Any]:
        start_ts, end_ts = self._range(days, start_date, end_date)
        rows = []
        counts = []
        async for key in self.r.scan_iter(f"health:mod_events:moderator:{guild_id}:*"):
            uid = key.split(":")[-1]
            count = int(await self.r.zcount(key, start_ts, end_ts))
            if count:
                counts.append(count)
                rows.append({"moderator": await self._user(uid), "actions": count})
        avg = sum(counts) / len(counts) if counts else 0
        # Descriptive flag, not a performance judgement.
        threshold = max(5, avg * 1.75) if counts else 5
        for row in rows:
            row["above_team_distribution"] = row["actions"] > threshold
            row["notice"] = "Vyšší počet může být způsoben více službami nebo aktivnějším kanálem."
        rows.sort(key=lambda x: x["actions"], reverse=True)
        return {"items": rows[:limit], "team_average": round(avg, 2), "descriptive_threshold": round(threshold, 2)}

    async def role_evidence(self, guild_id: int | str, user_id: int | str, days: int = 90) -> Dict[str, Any]:
        start_ts, end_ts = self._range(days)
        mids = await self.r.zrangebyscore(f"health:user_messages:{guild_id}:{user_id}", start_ts, end_ts)
        replies = 0
        reactions = 0
        channels = set()
        for mid in mids:
            item = await self.r.hgetall(f"health:message:{guild_id}:{mid}")
            if not item:
                continue
            if item.get("reply_to"):
                replies += 1
            reactions += int(item.get("reaction_count") or 0)
            if item.get("channel_id"):
                channels.add(item["channel_id"])
        incidents = int(await self.r.zcount(f"health:mod_events:target:{guild_id}:{user_id}", start_ts, end_ts))
        review = await self.r.hgetall(f"health:role_review:{guild_id}:{user_id}") or None
        evidence = factual_role_evidence(
            messages=len(mids), replies=replies, channels=len(channels), received_reactions=reactions,
            moderation_incidents=incidents, manual_review=review,
        )
        evidence["user"] = await self._user(user_id)
        evidence["period_days"] = days
        return evidence

    async def event_conversion(self, guild_id: int | str, limit: int = 50) -> Dict[str, Any]:
        event_ids = list(await self.r.smembers(f"health:events:{guild_id}"))
        rows = []
        for event_id in event_ids:
            item = await self.r.hgetall(f"health:event:{guild_id}:{event_id}")
            if not item:
                continue
            interested = int(await self.r.scard(f"health:event:interested:{guild_id}:{event_id}"))
            attended = int(await self.r.scard(f"health:event:attended:{guild_id}:{event_id}"))
            rows.append({
                "event_id": event_id,
                "name": item.get("name") or f"Event {event_id}",
                "scheduled_start": float(item.get("scheduled_start") or 0) or None,
                "status": item.get("status"),
                "interested": interested,
                "attended": attended,
                "conversion_percent": round(attended / interested * 100, 1) if interested else None,
            })
        rows.sort(key=lambda x: x["scheduled_start"] or 0, reverse=True)
        return {"items": rows[:limit]}

    async def overview(self, guild_id: int | str, days: int = 30) -> Dict[str, Any]:
        conflicts = await self.conflict_summary(guild_id, days=days, limit=5)
        help_data = await self.help_requests(guild_id, days=days, limit=5)
        departures = await self.departures(guild_id, days=days, limit=5)
        workload = await self.moderator_workload(guild_id, days=days, limit=5)
        events = await self.event_conversion(guild_id, limit=5)
        return {
            "config": await self.config(guild_id),
            "conflicts": conflicts,
            "help_requests": help_data,
            "departures": departures,
            "moderator_workload": workload,
            "events": events,
            "principles": {
                "human_decision_required": True,
                "causality_not_inferred": True,
                "message_content_stored": False,
            },
        }
