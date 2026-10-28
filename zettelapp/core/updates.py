"""Checking the website for a newer version of ZettelApp.

One small HTTPS request for version.json on the app's website. Nothing about the user
or their notes is sent; failures of any kind are silent. The result is only a version
number: the download link the app shows is always the fixed releases page.
"""

from __future__ import annotations

import json
import logging
import re
import urllib.request

from zettelapp import HOMEPAGE_URL, __version__

log = logging.getLogger(__name__)

VERSION_URL = HOMEPAGE_URL + "version.json"
MAX_RESPONSE_BYTES = 16 * 1024
TIMEOUT_SECONDS = 8.0
_VERSION_RE = re.compile(r"^\d{1,4}(?:\.\d{1,4}){1,3}$")


def parse_version(text: object) -> tuple[int, ...] | None:
    """(1, 2, 0) for "1.2.0"; None for anything that isn't a plain release number."""
    if not isinstance(text, str) or not _VERSION_RE.match(text.strip()):
        return None
    parts = [int(p) for p in text.strip().split(".")]
    while len(parts) > 1 and parts[-1] == 0:  # 1.2 == 1.2.0
        parts.pop()
    return tuple(parts)


def is_newer(candidate: str, current: str = __version__) -> bool:
    new, old = parse_version(candidate), parse_version(current)
    return new is not None and old is not None and new > old


def latest_version(timeout: float = TIMEOUT_SECONDS) -> str | None:
    """The newest released version listed on the website, or None if it can't be read."""
    request = urllib.request.Request(
        VERSION_URL,
        headers={"User-Agent": f"ZettelApp/{__version__}", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = response.read(MAX_RESPONSE_BYTES + 1)
        if len(data) > MAX_RESPONSE_BYTES:
            return None
        payload = json.loads(data.decode("utf-8"))
    except Exception as exc:  # noqa: BLE001 - offline, blocked, malformed: never an error
        log.info("Update check skipped: %s", exc.__class__.__name__)
        return None
    version = payload.get("version") if isinstance(payload, dict) else None
    if isinstance(version, str) and parse_version(version):
        return version.strip()
    return None


def available_update() -> str | None:
    """A newer version than this one, or None (also when the check fails)."""
    version = latest_version()
    return version if version is not None and is_newer(version) else None
