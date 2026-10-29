"""The website, built with Rational Web: pages, language menu, redirect script and links."""

import json
import re
import shutil
import subprocess
from pathlib import Path
from urllib.parse import urlparse

import pytest
from rational.rendering import to_html

from tools import build_site, website


def test_csp_allows_the_language_script_but_nothing_else():
    assert "script-src 'self'" in website.CSP
    assert "'unsafe-inline'" not in website.CSP and "'unsafe-eval'" not in website.CSP


def test_language_links_switch_the_same_page_and_fall_back_for_untranslated_pages():
    links = dict(
        (folder, href) for folder, _n, _c, href in website.language_links("", "docs", "faq")
    )
    assert links[""] == "faq.html"
    assert links["fr"] == "../fr/docs/faq.html"

    # mcp-reference.md has no translation: non-English links fall back to that language's docs index.
    links = dict(
        (folder, href)
        for folder, _n, _c, href in website.language_links("", "docs", "mcp-reference")
    )
    assert links["fr"] == "../fr/docs/"

    # From inside a translated page, switching to another translated page stays on the same stem.
    links = dict(
        (folder, href) for folder, _n, _c, href in website.language_links("fr", "docs", "faq")
    )
    assert links[""] == "../../docs/faq.html"
    assert links["de"] == "../../de/docs/faq.html"


def test_language_switch_is_a_dropdown_with_every_language_and_marks_the_current_one():
    markup = to_html(website.language_switch("ar", "home", "Languages"))
    assert markup.startswith('<details class="lang-switch">')
    assert markup.count("<li>") == len(website.LANGS) + 1  # every language plus English
    assert 'href="../ar/" lang="ar" hreflang="ar" aria-current="true"' in markup


def test_lang_script_detects_browser_language_and_redirects_once(tmp_path, monkeypatch):
    monkeypatch.setattr(build_site, "ROOT", tmp_path)
    (tmp_path / "website" / "assets").mkdir(parents=True)
    target = build_site.write_lang_script()
    script = target.read_text(encoding="utf-8")
    assert "zettelapp-lang" in script
    for folder in website.LANGS:
        assert f'"{folder}"' in script
    # Every translated page stem is embedded so untranslated pages can fall back sensibly.
    for stem in website.TRANSLATED:
        assert f'"{stem}"' in script


def _first_visit(script: str, path: str, browser_languages: list[str]) -> list[str]:
    """The addresses lang.js sends a first-time visitor of *path* to (run with Node.js)."""
    harness = (
        "var calls = [];\n"
        # Node 21+ has a read-only navigator of its own (with the machine's languages).
        "Object.defineProperty(globalThis, 'navigator', { configurable: true, value:"
        f" {{ languages: {json.dumps(browser_languages)} }} }});\n"
        "globalThis.localStorage = { data: {}, getItem(k) { return k in this.data ? this.data[k] : null; },"
        " setItem(k, v) { this.data[k] = String(v); } };\n"
        f"globalThis.location = {{ pathname: {json.dumps(path)}, search: '', hash: '',"
        " replace(u) { calls.push(u); } };\n" + script + "\nconsole.log(JSON.stringify(calls));\n"
    )
    done = subprocess.run(
        ["node", "-"], input=harness, capture_output=True, text=True, timeout=30, check=True
    )
    return json.loads(done.stdout)


@pytest.mark.skipif(shutil.which("node") is None, reason="needs Node.js to run the script")
def test_lang_script_sends_a_first_visit_to_the_same_page_in_the_browser_language(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(build_site, "ROOT", tmp_path)
    (tmp_path / "website" / "assets").mkdir(parents=True)
    script = build_site.write_lang_script().read_text(encoding="utf-8")
    site = "/ZettelApp"
    assert _first_visit(script, f"{site}/docs/faq.html", ["pt-BR", "en"]) == [
        f"{site}/pt-br/docs/faq.html"
    ]
    assert _first_visit(script, f"{site}/docs/mcp-reference.html", ["de"]) == [f"{site}/de/docs/"]
    assert _first_visit(script, f"{site}/", ["ja"]) == [f"{site}/ja/"]
    assert _first_visit(script, f"{site}/fr/docs/zotero.html", ["en-US"]) == [
        f"{site}/docs/zotero.html"
    ]
    assert _first_visit(script, f"{site}/docs/faq.html", ["en-GB"]) == []  # already English
    # A path starting with two slashes must not turn into a redirect to another site.
    hostile = _first_visit(script, "//evil.example/docs/faq.html", ["de"])
    assert hostile and not any(url.startswith("//") for url in hostile)


def test_build_writes_every_page_with_no_broken_local_links():
    written = build_site.build()
    assert written, "build() should write at least the English pages"
    assert (build_site.ROOT / "website" / "assets" / "lang.js").exists()

    site_dir = build_site.ROOT / "website"
    html_files = list(site_dir.rglob("*.html"))
    expected_docs = len(website.PAGES) + len(website.LANGS) * len(website.TRANSLATED)
    expected_landing = 1 + len(website.LANGS)
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
            assert target.exists(), f"{html_file.relative_to(site_dir)} -> {href}"


def test_every_landing_page_has_the_csp_both_language_widgets_and_no_rational_extras():
    for folder in ["", *website.LANGS]:
        path = (
            Path(build_site.ROOT) / "website" / folder / "index.html"
            if folder
            else (Path(build_site.ROOT) / "website" / "index.html")
        )
        text = path.read_text(encoding="utf-8")
        assert "script-src 'self'" in text
        assert "assets/lang.js" in text
        assert '<details class="lang-switch">' in text and 'class="nav lang-row"' in text
        assert "Proudly developed with" in text
        # Static and self-styled: no theme stylesheet, inline style, runtime or 404 page.
        assert "_rational" not in text and "<style" not in text and "data-rw" not in text
