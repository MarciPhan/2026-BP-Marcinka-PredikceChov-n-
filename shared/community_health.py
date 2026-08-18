"""Shared helpers for context-aware community health analytics.

The module deliberately separates observable facts from human judgements.  It
must never output a verdict such as "suitable moderator" based only on metrics.
"""
from __future__ import annotations

import hashlib
import json
import re
import secrets
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

DEFAULT_HEALTH_CONFIG: Dict[str, Any] = {
    "community_type": "general",
    "help_requests_enabled": False,
    "moderation_context_enabled": True,
    "departure_context_enabled": True,
    "event_conversion_enabled": False,
    "question_mode": "heuristic",
    "help_timeout_hours": 24,
    "conflict_window_days": 30,
}

QUESTION_PREFIXES = (
    "jak", "proč", "proc", "kde", "kdy", "kdo", "co", "můžu", "muzu",
    "máte", "mate", "poradí", "poradi", "help", "how", "why", "where",
    "when", "who", "what", "can", "could", "does", "do", "is", "are",
)


def utc_now_ts() -> float:
    return datetime.now(timezone.utc).timestamp()


def json_loads(value: Any, default: Any = None) -> Any:
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(value)
    except (TypeError, ValueError, json.JSONDecodeError):
        return default


def is_probable_question(content: str) -> bool:
    """Conservative heuristic used only in explicitly configured help channels."""
    text = re.sub(r"\s+", " ", (content or "").strip().lower())
    if not text:
        return False
    if "?" in text:
        return True
    first = re.sub(r"^[^\wá-ž]+", "", text).split(" ", 1)[0]
    return first in QUESTION_PREFIXES


def api_key_digest(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


def generate_api_key() -> str:
    return "mtr_" + secrets.token_urlsafe(32)


def normalise_config(raw: Dict[str, Any] | None) -> Dict[str, Any]:
    cfg = dict(DEFAULT_HEALTH_CONFIG)
    for key, value in (raw or {}).items():
        if key not in cfg:
            continue
        if isinstance(cfg[key], bool):
            cfg[key] = str(value).lower() in {"1", "true", "yes", "on"}
        elif isinstance(cfg[key], int):
            try:
                cfg[key] = max(1, int(value))
            except (TypeError, ValueError):
                pass
        else:
            cfg[key] = str(value)
    return cfg


def conflict_severity(action_types: Iterable[str]) -> str:
    actions = set(action_types)
    if actions & {"ban", "kick"}:
        return "high"
    if actions & {"timeout", "message_delete"}:
        return "medium"
    return "low"


def factual_role_evidence(
    *,
    messages: int,
    replies: int,
    channels: int,
    received_reactions: int,
    moderation_incidents: int,
    manual_review: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Return explainable evidence without deriving a suitability score."""
    return {
        "observable": {
            "messages": int(messages),
            "replies": int(replies),
            "active_channels": int(channels),
            "received_reactions": int(received_reactions),
            "moderation_incidents": int(moderation_incidents),
        },
        "human_review": manual_review,
        "decision": None,
        "notice": (
            "Metriky jsou pouze podklady. Vhodnost pro roli musí posoudit člověk "
            "s ohledem na důvěru, komunikaci a kontext komunity."
        ),
    }
