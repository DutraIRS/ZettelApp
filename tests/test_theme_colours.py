"""The black (OLED) theme and the colours a user may choose over any theme."""

import pytest

pytest.importorskip("PySide6")

from PySide6.QtGui import QColor  # noqa: E402

from zettelapp import settings  # noqa: E402
from zettelapp.ui import theme  # noqa: E402


@pytest.fixture(autouse=True)
def no_desktop_accent(monkeypatch):
    monkeypatch.setattr(theme, "_desktop_accent", lambda dark: None)


def test_black_is_the_dark_theme_on_true_black():
    dark, black = theme.build_theme("dark"), theme.build_theme("black")
    assert black.dark
    assert black.window == black.surface == black.sidebar == "#000000"
    assert black.text == dark.text and black.accent == dark.accent


def test_without_choices_links_and_highlights_use_the_accent():
    for mode in ("light", "dark", "black"):
        t = theme.build_theme(mode)
        assert t.link == t.highlight == t.accent


def test_chosen_colours_go_where_their_names_say():
    t = theme.build_theme(
        "light",
        {"primary": "#7a1fa2", "secondary": "#00897b", "highlight": "#ffd54f", "text": "#102030"},
    )
    assert t.accent == "#7a1fa2" and t.on_accent == "#ffffff"  # white reads on purple
    assert t.link == "#00897b"
    assert t.highlight == "#ffd54f" and t.on_highlight == "#000000"  # black reads on yellow
    assert t.text == "#102030"
    # The softer text shades follow the chosen text, between it and the window.
    assert QColor(t.text_secondary).lightness() > QColor(t.text).lightness()
    assert QColor(t.text_muted).lightness() > QColor(t.text_secondary).lightness()


def test_unknown_names_and_invalid_colours_are_ignored():
    plain = theme.build_theme("dark")
    assert theme.build_theme("dark", {"primary": "not a colour", "border": "#ff0000"}) == plain


def test_the_settings_keep_only_the_colours_that_were_chosen(tmp_path, monkeypatch):
    monkeypatch.setenv("ZETTELAPP_SETTINGS_FILE", str(tmp_path / "settings.ini"))
    assert settings.theme_colours() == {}
    settings.put(settings.THEME_COLOUR + "highlight", "#ffd54f")
    settings.put(settings.THEME_COLOUR + "primary", "")
    assert settings.theme_colours() == {"highlight": "#ffd54f"}
