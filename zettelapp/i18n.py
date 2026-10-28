"""Interface languages.

Text shown to users goes through ``_()`` when it is displayed. Module-level
constants are marked with ``N_()`` (which returns the text unchanged) and translated
with ``_()`` where they are shown, because the language is chosen after import.
Counted text uses ``n_(singular, plural, n)``, which applies each language's plural
rules. Placeholders use ``str.format`` names (``_("{n} notes").format(n=3)``) so
translators can move them.

Catalogs live in zettelapp/resources/locales/<code>.json and map the English text to
the translation (a list of plural forms for ``n_`` entries); tools/i18n.py extracts
the strings and checks the catalogs. Missing entries fall back to English.
"""

from __future__ import annotations

import json
import logging

log = logging.getLogger(__name__)

# Native names, shown in Options. Each has Qt's own translations for standard dialogs.
LANGUAGES: dict[str, str] = {
    "en": "English",
    "es": "Español",
    "pt_BR": "Português (Brasil)",
    "fr": "Français",
    "de": "Deutsch",
    "it": "Italiano",
    "ru": "Русский",
    "zh_CN": "简体中文",
    "ja": "日本語",
    "ko": "한국어",
    "ar": "العربية",
}
RIGHT_TO_LEFT = frozenset({"ar"})

# Language names written by the installer (Inno Setup) into the same setting.
_INSTALLER_NAMES = {
    "english": "en",
    "spanish": "es",
    "brazilianportuguese": "pt_BR",
    "portuguese": "pt_BR",
    "french": "fr",
    "german": "de",
    "italian": "it",
    "russian": "ru",
    "japanese": "ja",
    "korean": "ko",
    "arabic": "ar",
}

_catalog: dict[str, str | list[str]] = {}
_language = "en"


def N_(text: str) -> str:  # noqa: N802 - gettext convention
    """Mark *text* for translation without translating it yet."""
    return text


def _(text: str) -> str:
    """*text* in the interface language."""
    value = _catalog.get(text)
    return value if isinstance(value, str) and value else text


def plural_index(language: str, n: int) -> int:
    """Which plural form *n* takes (CLDR rules for the supported languages)."""
    n = abs(int(n))
    if language in ("zh_CN", "ja", "ko"):
        return 0
    if language == "ru":
        if n % 10 == 1 and n % 100 != 11:
            return 0
        if 2 <= n % 10 <= 4 and not 12 <= n % 100 <= 14:
            return 1
        return 2
    if language == "ar":
        if n in (0, 1, 2):
            return n
        if 3 <= n % 100 <= 10:
            return 3
        if 11 <= n % 100 <= 99:
            return 4
        return 5
    if language in ("fr", "pt_BR"):
        return 0 if n in (0, 1) else 1
    return 0 if n == 1 else 1


def n_(singular: str, plural: str, n: int) -> str:
    """The form of a counted text that fits *n*; format it with ``n`` afterwards."""
    forms = _catalog.get(singular)
    if isinstance(forms, list) and forms:
        return forms[min(plural_index(_language, n), len(forms) - 1)] or singular
    return singular if n == 1 else plural


def current_language() -> str:
    return _language


def is_right_to_left() -> bool:
    return _language in RIGHT_TO_LEFT


def resolve(setting: str | None, system_name: str = "en") -> str:
    """The language code for a setting: a code, an installer name, or "system"."""
    value = (setting or "system").strip()
    if value in LANGUAGES:
        return value
    if value.lower() in _INSTALLER_NAMES:
        return _INSTALLER_NAMES[value.lower()]
    for candidate in (system_name, system_name.split("_")[0]):
        if candidate in LANGUAGES:
            return candidate
    if system_name.startswith("pt"):
        return "pt_BR"
    if system_name.startswith("zh"):
        return "zh_CN"
    return "en"


def load(language: str) -> str:
    """Make *language* the interface language for ``_()``; returns the code used."""
    global _catalog, _language
    from zettelapp.paths import resource_path

    _catalog, _language = {}, "en"
    if language not in LANGUAGES or language == "en":
        return _language
    path = resource_path("locales", f"{language}.json")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        log.warning("No usable translation for %s; using English", language)
        return _language
    _catalog = (
        {k: v for k, v in data.items() if isinstance(k, str) and v}
        if isinstance(data, dict)
        else {}
    )
    _language = language
    return _language


def install(app, setting: str | None) -> str:
    """Load the chosen language into the running app, including Qt's own dialogs."""
    from PySide6.QtCore import QLibraryInfo, QLocale, Qt, QTranslator

    language = load(resolve(setting, QLocale.system().name()))
    if language != "en":
        translator = QTranslator(app)
        folder = QLibraryInfo.path(QLibraryInfo.LibraryPath.TranslationsPath)
        if translator.load(f"qtbase_{language}", folder):
            app.installTranslator(translator)
        QLocale.setDefault(QLocale(language))
    app.setLayoutDirection(
        Qt.LayoutDirection.RightToLeft if is_right_to_left() else Qt.LayoutDirection.LeftToRight
    )
    return language
