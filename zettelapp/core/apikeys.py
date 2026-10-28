"""Several saved API keys per AI provider (say a work key and a personal one).

The secret values live in Windows Credential Manager (see ``secrets``); only the key
names and which one is in use are kept in the settings, as JSON. A key saved before
profiles existed is the "default" profile and keeps its original secret name.
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import dataclass

from zettelapp import settings
from zettelapp.core.llm import PROVIDERS
from zettelapp.core.secrets import delete_secret, get_secret, set_secret

PROFILES_KEY = "llm/keyProfiles"
LEGACY_ID = "default"
MAX_LABEL = 60
_ID_RE = re.compile(r"^[a-z0-9]{1,32}$")


@dataclass(frozen=True)
class KeyProfile:
    id: str
    label: str


def secret_name(provider: str, key_id: str) -> str:
    base = PROVIDERS[provider].secret_name
    return base if key_id == LEGACY_ID else f"{base}/{key_id}"


def _load() -> dict[str, dict]:
    try:
        data = json.loads(settings.get(PROFILES_KEY, "") or "{}")
    except (TypeError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def _save(data: dict[str, dict]) -> None:
    settings.put(PROFILES_KEY, json.dumps(data, ensure_ascii=False))


def _clean_label(label: str, fallback: str) -> str:
    return " ".join((label or "").split())[:MAX_LABEL] or fallback


def list_keys(provider: str) -> list[KeyProfile]:
    """The saved keys for *provider*, oldest first. A pre-profile key shows up as "Default"."""
    entry = _load().get(provider) or {}
    keys = [
        KeyProfile(k["id"], _clean_label(k.get("label", ""), k["id"]))
        for k in entry.get("keys", [])
        if isinstance(k, dict) and isinstance(k.get("id"), str) and _ID_RE.match(k["id"])
    ]
    known = {k.id for k in keys}
    if provider in PROVIDERS and LEGACY_ID not in known and entry.get("legacy") is not False:
        if get_secret(PROVIDERS[provider].secret_name):
            keys.insert(0, KeyProfile(LEGACY_ID, "Default"))
    return keys


def active_id(provider: str) -> str | None:
    keys = list_keys(provider)
    wanted = (_load().get(provider) or {}).get("active")
    if any(k.id == wanted for k in keys):
        return wanted
    return keys[0].id if keys else None


def active_secret(provider: str) -> str | None:
    """The key to use for *provider*, or None when none is saved."""
    key_id = active_id(provider)
    return get_secret(secret_name(provider, key_id)) if key_id else None


def get_key(provider: str, key_id: str) -> str | None:
    return get_secret(secret_name(provider, key_id))


def _store(provider: str, keys: list[KeyProfile], active: str | None, legacy: bool) -> None:
    data = _load()
    data[provider] = {
        "keys": [{"id": k.id, "label": k.label} for k in keys if k.id != LEGACY_ID or legacy],
        "active": active,
        "legacy": legacy,
    }
    if legacy and not any(k.id == LEGACY_ID for k in keys):
        data[provider]["keys"].insert(0, {"id": LEGACY_ID, "label": "Default"})
    _save(data)


def add_key(provider: str, label: str, value: str, make_active: bool = True) -> KeyProfile:
    value = (value or "").strip()
    if not value:
        raise ValueError("The key is empty.")
    keys = list_keys(provider)
    profile = KeyProfile(uuid.uuid4().hex[:12], _clean_label(label, f"Key {len(keys) + 1}"))
    set_secret(secret_name(provider, profile.id), value)
    keys.append(profile)
    active = profile.id if make_active else active_id(provider) or profile.id
    _store(provider, keys, active, legacy=any(k.id == LEGACY_ID for k in keys))
    return profile


def rename_key(provider: str, key_id: str, label: str) -> None:
    keys = [
        KeyProfile(k.id, _clean_label(label, k.label) if k.id == key_id else k.label)
        for k in list_keys(provider)
    ]
    _store(provider, keys, active_id(provider), legacy=any(k.id == LEGACY_ID for k in keys))


def replace_key(provider: str, key_id: str, value: str) -> None:
    if key_id not in {k.id for k in list_keys(provider)}:
        raise KeyError(key_id)
    set_secret(secret_name(provider, key_id), value.strip())


def set_active(provider: str, key_id: str) -> None:
    keys = list_keys(provider)
    if key_id in {k.id for k in keys}:
        _store(provider, keys, key_id, legacy=any(k.id == LEGACY_ID for k in keys))


def delete_key(provider: str, key_id: str) -> None:
    keys = list_keys(provider)
    delete_secret(secret_name(provider, key_id))
    keys = [k for k in keys if k.id != key_id]
    active = active_id(provider)
    if active == key_id or active not in {k.id for k in keys}:
        active = keys[0].id if keys else None
    _store(provider, keys, active, legacy=any(k.id == LEGACY_ID for k in keys))


def has_key(provider: str) -> bool:
    return active_id(provider) is not None
