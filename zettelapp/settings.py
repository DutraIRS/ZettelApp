"""User preferences, stored by QSettings in HKCU\\Software\\ZettelApp\\ZettelApp.

Only QtCore is used here, so the MCP server (which has no GUI) can read the
same preferences as the desktop app. Secrets such as API keys never go here:
they live in Windows Credential Manager (see zettelapp.core.secrets).
"""

from __future__ import annotations

import os
from typing import Any

from PySide6.QtCore import QSettings

from zettelapp import APP_NAME, ORG_NAME

# Keys -----------------------------------------------------------------------
LAST_VAULT = "vault/last"
RECENT_VAULTS = "vault/recent"
THEME = "ui/theme"  # system | light | dark
UI_LANGUAGE = "ui/language"  # system, a code from i18n.LANGUAGES, or the installer's choice
EDITOR_FONT_SIZE = "editor/fontSize"
AUTOSAVE_MS = "editor/autosaveMs"
SUGGEST_ENABLED = "suggest/enabled"
SUGGEST_FEATURES = "suggest/features"
SUGGEST_LIMIT = "suggest/limit"
SUGGEST_MIN_PROB = "suggest/minProbability"
SUGGEST_PRIOR = "suggest/priorStrength"
ANKI_PORT = "anki/port"
ANKI_DECK = "anki/deck"
ZOTERO_PORT = "zotero/port"
BACKUP_ENABLED = "backup/enabled"
BACKUP_KEEP = "backup/keep"
LLM_PROVIDER = "llm/provider"
LLM_MODEL = "llm/model"
LLM_BASE_URL = "llm/baseUrl"
LLM_EFFORT = "llm/effort"
LLM_CONTEXT_NOTES = "llm/contextNotes"
LLM_PRIVACY_ACK = "llm/privacyAcknowledged"
MCP_ALLOW_WRITES = "mcp/allowWrites"
UPDATE_CHECK = "updates/checkAtStart"
UPDATE_NOTIFIED = "updates/notifiedVersion"  # the newest version already announced

DEFAULTS: dict[str, Any] = {
    THEME: "system",
    UI_LANGUAGE: "system",
    EDITOR_FONT_SIZE: 11,
    AUTOSAVE_MS: 800,
    SUGGEST_ENABLED: True,
    SUGGEST_LIMIT: 8,
    SUGGEST_MIN_PROB: 0.10,
    SUGGEST_PRIOR: 10.0,
    ANKI_PORT: 8765,
    ANKI_DECK: "ZettelApp",
    ZOTERO_PORT: 23119,
    BACKUP_ENABLED: True,
    BACKUP_KEEP: 10,
    LLM_PROVIDER: "anthropic",
    LLM_EFFORT: "medium",
    LLM_CONTEXT_NOTES: 8,
    LLM_PRIVACY_ACK: False,
    MCP_ALLOW_WRITES: False,
    UPDATE_CHECK: True,
    UPDATE_NOTIFIED: "",
}


def store() -> QSettings:
    override = os.environ.get("ZETTELAPP_SETTINGS_FILE")  # used by tests and screenshot tooling
    if override:
        return QSettings(override, QSettings.Format.IniFormat)
    return QSettings(QSettings.Format.NativeFormat, QSettings.Scope.UserScope, ORG_NAME, APP_NAME)


def get(key: str, default: Any = None) -> Any:
    fallback = DEFAULTS.get(key) if default is None else default
    value = store().value(key, fallback)
    # The registry returns strings for some types; coerce to the default's type.
    if isinstance(fallback, bool):
        return value in (True, "true", "True", "1", 1)
    if isinstance(fallback, int) and not isinstance(fallback, bool):
        try:
            return int(value)
        except (TypeError, ValueError):
            return fallback
    if isinstance(fallback, float):
        try:
            return float(value)
        except (TypeError, ValueError):
            return fallback
    return value


def put(key: str, value: Any) -> None:
    s = store()
    s.setValue(key, value)
    s.sync()


def get_list(key: str) -> list[str]:
    value = store().value(key, [])
    if isinstance(value, str):
        return [value] if value else []
    return [str(v) for v in (value or [])]
