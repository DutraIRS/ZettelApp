"""Interface translations: plural rules, safe loading and complete, valid catalogs."""

import json

import pytest

from tools import i18n as tool
from zettelapp import i18n


@pytest.fixture(autouse=True)
def english():
    yield
    i18n.load("en")


def test_resolves_settings_installer_names_and_windows_languages():
    assert i18n.resolve("de") == "de"
    assert i18n.resolve("brazilianportuguese") == "pt_BR"
    assert i18n.resolve("system", "fr_CA") == "fr"
    assert i18n.resolve("system", "pt_PT") == "pt_BR"
    assert i18n.resolve("system", "zh_TW") == "zh_CN"
    assert i18n.resolve("system", "hi_IN") == "en"
    assert i18n.resolve("klingon", "en_US") == "en"


@pytest.mark.parametrize(
    ("language", "counts", "forms"),
    [
        ("en", (0, 1, 2), (1, 0, 1)),
        ("fr", (0, 1, 2), (0, 0, 1)),
        ("ru", (1, 2, 5, 11, 21, 22, 112), (0, 1, 2, 2, 0, 1, 2)),
        ("ar", (0, 1, 2, 3, 11, 100, 102), (0, 1, 2, 3, 4, 5, 5)),
        ("ja", (1, 2), (0, 0)),
    ],
)
def test_plural_rules(language, counts, forms):
    assert tuple(i18n.plural_index(language, n) for n in counts) == forms


def test_broken_translations_fall_back_to_english(tmp_path, monkeypatch):
    locales = tmp_path / "locales"
    locales.mkdir()
    (locales / "messages.json").write_text(
        json.dumps({"{n} note": {"plural": "{n} notes", "where": []}}), encoding="utf-8"
    )
    (locales / "de.json").write_text(
        json.dumps(
            {
                "Close": "Schließen",
                "Hello {name}": "Hallo {nmae}",  # a typo in the placeholder would crash
                "Broken {": "Kaputt {",
                "{n} note": ["{n} Notiz", "{n} Notizen"],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr("zettelapp.paths.resource_path", lambda *parts: tmp_path.joinpath(*parts))
    assert i18n.load("de") == "de"
    assert i18n._("Close") == "Schließen"
    assert i18n._("Hello {name}").format(name="Ana") == "Hello Ana"
    assert i18n._("Broken {") == "Broken {"
    assert i18n.n_("{n} note", "{n} notes", 3).format(n=3) == "3 Notizen"
    assert i18n.load("xx") == "en" and i18n._("Close") == "Close"


def test_messages_file_is_up_to_date():
    """Run `python tools/i18n.py extract` after changing user-visible text."""
    stored = json.loads(tool.TEMPLATE.read_text(encoding="utf-8"))
    assert stored == tool.extract()


def test_catalogs_are_complete_and_valid():
    """Run `python tools/i18n.py check` to see what is missing or broken."""
    messages = tool.extract()
    for language, catalog in tool.catalogs().items():
        assert language in i18n.LANGUAGES
        found = tool.problems(language, catalog, messages)
        assert found == {"missing": [], "stale": [], "broken": []}, language
