"""
Regression tests: user-facing texts must stay consistent with
the actual EVENT_RETENTION_DAYS retention setting.
"""
import ast
import re
import os
import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ---------------------------------------------------------------------------
# 1. /privacy embed must reference settings.event_retention_days dynamically
# ---------------------------------------------------------------------------

def _read_gdpr_source() -> str:
    path = os.path.join(PROJECT_ROOT, "bot", "commands", "gdpr.py")
    with open(path, encoding="utf-8") as f:
        return f.read()


def test_privacy_embed_contains_retention_days_reference():
    """The 'Jak dlouho ukládáme' field must use settings.event_retention_days
    so the displayed value cannot silently drift from the real config."""
    source = _read_gdpr_source()
    assert "settings.event_retention_days" in source, (
        "gdpr.py must reference settings.event_retention_days "
        "in the /privacy embed, not a hardcoded value."
    )


def test_privacy_embed_imports_settings():
    """gdpr.py must import settings from shared.config."""
    source = _read_gdpr_source()
    assert "from shared.config import settings" in source, (
        "gdpr.py must import settings from shared.config."
    )


def test_privacy_embed_no_unlimited_claims():
    """The /privacy embed must not contain 'Neomezené' or 'indefinitely'."""
    source = _read_gdpr_source()
    assert "Neomezené" not in source, (
        "gdpr.py still contains 'Neomezené' — must use actual retention."
    )
    assert "indefinitely" not in source.lower(), (
        "gdpr.py still contains 'indefinitely' — must use actual retention."
    )


# ---------------------------------------------------------------------------
# 2. README and docs must not claim unlimited event retention
# ---------------------------------------------------------------------------

_UNLIMITED_PATTERNS = re.compile(
    r"neomezeně|indefinitely|forever|no expiration|nikdy nemažeme",
    re.IGNORECASE,
)

_DOC_PATHS = [
    "README.md",
    os.path.join("docs", "data-schema.md"),
    os.path.join("docs", "security-technical.md"),
]


@pytest.mark.parametrize("rel_path", _DOC_PATHS)
def test_no_unlimited_retention_claims_in_docs(rel_path):
    """No user-facing documentation should claim events are stored
    indefinitely, which contradicts EVENT_RETENTION_DAYS."""
    full = os.path.join(PROJECT_ROOT, rel_path)
    if not os.path.exists(full):
        pytest.skip(f"{rel_path} not found")
    with open(full, encoding="utf-8") as f:
        content = f.read()
    matches = _UNLIMITED_PATTERNS.findall(content)
    assert not matches, (
        f"{rel_path} still contains unlimited retention claims: {matches}"
    )


# ---------------------------------------------------------------------------
# 3. Dead duplicate Discourse connector must not exist
# ---------------------------------------------------------------------------

def test_no_duplicate_discourse_connector():
    """The old web/backend/scripts/discourse_sync.py must be deleted."""
    dead_path = os.path.join(
        PROJECT_ROOT, "web", "backend", "scripts", "discourse_sync.py"
    )
    assert not os.path.exists(dead_path), (
        f"Duplicate Discourse connector still exists: {dead_path}"
    )
