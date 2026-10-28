"""The generated website: language redirect script, flag switcher, and link integrity."""

import re
from pathlib import Path
from urllib.parse import urlparse

from tools import build_site


def test_csp_allows_the_language_script_but_nothing_else():
    assert "script-src 'self'" in build_site.CSP
    assert "'unsafe-inline'" not in build_site.CSP and "'unsafe-eval'" not in build_site.CSP


def test_language_links_switch_the_same_page_and_fall_back_for_untranslated_pages():
    links = dict(
        (folder, href) for folder, _n, _c, _f, href in build_site._language_links("", "docs", "faq")
    )
    assert links[""] == "faq.html"
    assert links["fr"] == "../fr/docs/faq.html"

    # mcp-reference.md has no translation: non-English links fall back to that language's docs index.
    links = dict(
        (folder, href)
        for folder, _n, _c, _f, href in build_site._language_links("", "docs", "mcp-reference")
    )
    assert links["fr"] == "../fr/docs/"

    # From inside a translated page, switching to another translated page stays on the same stem.
    links = dict(
        (folder, href)
        for folder, _n, _c, _f, href in build_site._language_links("fr", "docs", "faq")
    )
    assert links[""] == "../../docs/faq.html"
    assert links["de"] == "../../de/docs/faq.html"


def test_language_switch_is_a_dropdown_with_every_language_and_marks_the_current_one():
    markup = build_site.language_switch("ar", "home")
    assert markup.startswith('<details class="lang-switch">')
    assert markup.count("<li>") == len(build_site.LANGS) + 1  # every language plus English
    assert 'href="../ar/" lang="ar" hreflang="ar" aria-current="true"' in markup


def test_lang_script_detects_browser_language_and_redirects_once(tmp_path, monkeypatch):
    monkeypatch.setattr(build_site, "ROOT", tmp_path)
    (tmp_path / "website" / "assets").mkdir(parents=True)
    target = build_site.write_lang_script()
    script = target.read_text(encoding="utf-8")
    assert "zettelapp-lang" in script
    for folder in build_site.LANGS:
        assert f'"{folder}"' in script
    # Every translated page stem is embedded so untranslated pages can fall back sensibly.
    for stem in build_site.TRANSLATED:
        assert f'"{stem}"' in script


def test_build_writes_every_page_with_no_broken_local_links():
    written = build_site.build()
    assert written, "build() should write at least the English pages"
    assert (build_site.ROOT / "website" / "assets" / "lang.js").exists()

    website = build_site.ROOT / "website"
    html_files = list(website.rglob("*.html"))
    expected_docs = len(build_site.PAGES) + len(build_site.LANGS) * len(build_site.TRANSLATED)
    expected_landing = 1 + len(build_site.LANGS)
    assert len(html_files) == expected_docs + expected_landing
    for html_file in html_files:
        text = html_file.read_text(encoding="utf-8")
        for m in re.finditer(r'(?:href|src)="([^"]*)"', text):
            href = m.group(1)
            if not href or href.startswith("#"):
                continue
            parsed = urlparse(href)
            if parsed.scheme or href.startswith("mailto:"):
                continue
            if not parsed.path:
                continue
            target = (html_file.parent / parsed.path).resolve()
            if target.is_dir():
                target = target / "index.html"
            assert target.exists(), f"{html_file.relative_to(website)} -> {href}"


def test_every_landing_page_has_the_relaxed_csp_and_both_language_widgets():
    for folder in ["", *build_site.LANGS]:
        path = (
            Path(build_site.ROOT) / "website" / folder / "index.html"
            if folder
            else (Path(build_site.ROOT) / "website" / "index.html")
        )
        text = path.read_text(encoding="utf-8")
        assert "script-src 'self'" in text
        assert "assets/lang.js" in text
        assert "<!--langswitch-->" in text and "<!--/langswitch-->" in text
        assert "<!--langs-->" in text and "<!--/langs-->" in text
