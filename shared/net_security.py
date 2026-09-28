"""SSRF / DNS-rebinding protection shared by the Discourse connector.

Used both when an administrator adds a Discourse instance (web/backend/routers/api.py)
and on every periodic background synchronization (scripts/discourse_sync.py), so a
domain that starts resolving to a private/internal address *after* it was added is
still rejected on the next sync, not only at add-time.
"""

import ipaddress
import socket
from urllib.parse import urlparse


class UnsafeDiscourseURLError(ValueError):
    """Raised when a Discourse URL resolves to a disallowed network target."""


def _is_disallowed_ip(ip_obj: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    return (
        ip_obj.is_private
        or ip_obj.is_loopback
        or ip_obj.is_multicast
        or ip_obj.is_link_local
        or ip_obj.is_reserved
        or str(ip_obj) == "169.254.169.254"
    )


def validate_hostname_ips(hostname: str) -> bool:
    """Resolve `hostname` and return False if any address is private/loopback/etc."""
    addr_info = socket.getaddrinfo(hostname, None)
    for result in addr_info:
        ip = result[4][0]
        if _is_disallowed_ip(ipaddress.ip_address(ip)):
            return False
    return True


def assert_safe_discourse_url(url: str) -> str:
    """Validate scheme + resolved IPs for a Discourse base URL.

    Returns the normalised URL on success. Raises UnsafeDiscourseURLError with a
    human-readable reason on failure. Callers should re-run this immediately before
    each outbound request (not just once when the instance is first configured),
    since DNS records can change after the fact (DNS rebinding).
    """
    url = (url or "").strip().rstrip("/")
    if not url.startswith("http"):
        raise UnsafeDiscourseURLError("Invalid URL")

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise UnsafeDiscourseURLError("Invalid scheme")
    if not parsed.hostname:
        raise UnsafeDiscourseURLError("Invalid URL hostname")

    try:
        safe = validate_hostname_ips(parsed.hostname)
    except Exception as exc:
        raise UnsafeDiscourseURLError(f"Invalid URL hostname: {exc}") from exc

    if not safe:
        raise UnsafeDiscourseURLError("SSRF Protection: Local or private IPs are not allowed")

    return url
