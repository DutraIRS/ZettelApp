"""Build the website's pages with Rational Web (see tools/website.py).

Run with:  python tools/build_site.py
Exports every page into website/ (the landing pages, website/docs/<page>.html from
docs/<page>.md and website/<language>/docs/ from docs/<language>/), and writes
website/assets/lang.js and website/version.json, which installed copies read to learn about
new versions. Markdown is rendered with markdown-it-py with raw HTML disabled, like the app.
"""

from __future__ import annotations

import asyncio
import html
import json
import re
import sys
import tempfile
import unicodedata
from pathlib import Path

from markdown_it import MarkdownIt
from rational.export import export_site

sys.path.insert(0, str(Path(__file__).resolve().parent))
from website import (  # noqa: E402  (the site itself: data, components and the Rational app)
    LANGS,
    PAGES,
    TRANSLATED,
    Doc,
    make_app,
)

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
OUT = ROOT / "website" / "docs"
REPO = "https://github.com/DutraIRS/ZettelApp/blob/main/"


def slugify(text: str) -> str:
    """GitHub-style heading anchors, so #links work on GitHub and on the site."""
    text = unicodedata.normalize("NFKD", html.unescape(re.sub(r"<[^>]+>", "", text))).lower()
    text = re.sub(r"[^\w\- ]", "", text)
    return re.sub(r" ", "-", text.strip())


def renderer() -> MarkdownIt:
    md = MarkdownIt("commonmark", {"html": False, "typographer": False})
    md.enable(["table", "strikethrough"])
    return md


def rewrite_href(href: str, lang: str = "") -> str:
    """Map a link in a Markdown page to its place on the site (*lang* is a folder or "")."""
    if re.match(r"^[a-z][a-z0-9+.-]*:", href, re.I) or href.startswith("#"):
        return href
    up = "../../" if lang else "../"
    path, _, fragment = href.partition("#")
    if path.endswith(".md"):
        stem = Path(path).stem
        local = set(TRANSLATED if lang else [p for p, _ in PAGES])
        if "/" not in path and stem in local:
            path = f"{stem}.html"
        elif "/" not in path and stem in {p for p, _ in PAGES}:  # not translated: the English page
            path = f"{up}docs/{stem}.html"
        else:  # a Markdown file outside docs/ (ROADMAP.md, …): link to it on GitHub
            path = REPO + path.lstrip("./").replace("../", "")
    elif path.startswith("../website/"):
        path = up + path[len("../website/") :]
    elif path.startswith("../"):
        path = REPO + path[3:]
    return path + (f"#{fragment}" if fragment else "")


def postprocess(body: str, lang: str = "") -> str:
    used: dict[str, int] = {}

    def heading(m: re.Match) -> str:
        level, content = m.group(1), m.group(2)
        slug = slugify(content) or "section"
        n = used.get(slug, 0)
        used[slug] = n + 1
        if n:
            slug = f"{slug}-{n}"
        return f'<h{level} id="{slug}">{content}</h{level}>'

    body = re.sub(r"<h([1-6])>(.*?)</h\1>", heading, body, flags=re.S)
    body = re.sub(
        r'(href|src)="([^"]*)"',
        lambda m: (
            f'{m.group(1)}="{html.escape(rewrite_href(html.unescape(m.group(2)), lang), quote=True)}"'
        ),
        body,
    )
    body = body.replace("<table>", '<div class="table-wrap"><table>').replace(
        "</table>", "</table></div>"
    )
    body = re.sub(r"<img ", '<img loading="lazy" ', body)
    return body


def description(markdown: str) -> str:
    """The first paragraph, as plain text (Rational escapes it in the page)."""
    for block in markdown.split("\n\n"):
        block = block.strip()
        if block and not block.startswith(("#", "!", "|", "```", "-")):
            return re.sub(r"[*_`\[\]]|\(([^)]*)\)", "", " ".join(block.split()))[:180]
    return "ZettelApp documentation"


def write_lang_script() -> Path:
    """website/assets/lang.js: redirect a first-time visitor to their browser language once.

    Nothing is sent anywhere; the only persisted value is the chosen language folder, kept in
    localStorage so the redirect happens at most once and never overrides a language the visitor
    already reached by browsing (including picking one from the dropdown).
    """
    folder_alt = "|".join(re.escape(f) for f in LANGS)
    prefixes = {"": ["en"], **{f: p for f, (_n, _h, _r, p) in LANGS.items()}}
    script = (
        TEMPLATE_JS.replace("__PREFIXES__", json.dumps(prefixes))
        .replace("__TRANSLATED__", json.dumps(TRANSLATED))
        .replace("__FOLDERS__", folder_alt)
    )
    target = ROOT / "website" / "assets" / "lang.js"
    target.write_text(script, encoding="utf-8", newline="\n")
    return target


TEMPLATE_JS = """(function () {
  "use strict";
  var KEY = "zettelapp-lang";
  var PREFIXES = __PREFIXES__;
  var TRANSLATED = __TRANSLATED__;
  var FOLDERS = "__FOLDERS__";

  function currentFolder(path) {
    var m = path.match(new RegExp("/(" + FOLDERS + ")(?:/|$)"));
    return m ? m[1] : "";
  }

  function targetPath(path, folder) {
    var docsRe = new RegExp("^(.*?)(?:/(" + FOLDERS + "))?/docs/(?:([a-z0-9-]+)\\\\.html)?$", "i");
    var m = path.match(docsRe);
    if (m) {
      var stem = m[3] || "index"; // m[2] is the language folder, if any
      if (folder && TRANSLATED.indexOf(stem) === -1) {
        return m[1] + "/" + folder + "/docs/";
      }
      return m[1] + (folder ? "/" + folder : "") + "/docs/" + stem + ".html";
    }
    var homeRe = new RegExp("^(.*?)(?:/(" + FOLDERS + "))?/(?:index\\\\.html)?$", "i");
    var hm = path.match(homeRe);
    if (hm) {
      return hm[1] + (folder ? "/" + folder + "/" : "/");
    }
    return null;
  }

  function detect() {
    var prefs = navigator.languages && navigator.languages.length
      ? navigator.languages
      : [navigator.language || "en"];
    for (var i = 0; i < prefs.length; i++) {
      var primary = String(prefs[i]).split("-")[0].toLowerCase();
      for (var folder in PREFIXES) {
        if (PREFIXES[folder].indexOf(primary) !== -1) return folder;
      }
    }
    return "";
  }

  try {
    // One slash at a time: "//host/docs/" must never become a protocol-relative redirect.
    var path = location.pathname.replace(/\\/{2,}/g, "/");
    var here = currentFolder(path);
    var stored = localStorage.getItem(KEY);
    if (stored === null) {
      var want = detect();
      if (want !== here) {
        var dest = targetPath(path, want);
        if (dest && dest !== path) {
          localStorage.setItem(KEY, want);
          location.replace(dest + location.search + location.hash);
          return;
        }
      }
      localStorage.setItem(KEY, here);
    } else if (stored !== here) {
      localStorage.setItem(KEY, here);
    }
  } catch (e) {
    /* Storage blocked (e.g. private browsing): skip silently, no redirect. */
  }
})();
"""


def load_docs(md: MarkdownIt) -> dict[tuple[str, str], Doc]:
    """Every documentation page, keyed by (language folder, stem); English is folder ""."""
    docs: dict[tuple[str, str], Doc] = {}
    sets = [("", PAGES)] + [(f, None) for f in LANGS if (DOCS / f).is_dir()]
    for folder, pages in sets:
        texts, titles = {}, {}
        stems = [p for p, _ in PAGES] if not folder else TRANSLATED
        for stem in stems:
            source = DOCS / folder / f"{stem}.md"
            if not source.exists():
                raise SystemExit(f"Missing documentation page: {source}")
            texts[stem] = source.read_text(encoding="utf-8")
            match = re.search(r"^#\s+(.+)$", texts[stem], re.M)
            titles[stem] = match.group(1).strip() if match else stem
        labels = dict(pages) if pages else titles  # English uses the sidebar names above
        menu = tuple((stem, labels[stem]) for stem in stems)
        for stem in stems:
            docs[(folder, stem)] = Doc(
                folder=folder,
                stem=stem,
                title=titles[stem],
                label=labels[stem],
                description=description(texts[stem]),
                body=postprocess(md.render(texts[stem]), folder),
                source_url=f"{REPO}docs/{folder + '/' if folder else ''}{stem}.md",
                menu=menu,
            )
    return docs


def build() -> list[Path]:
    """Export every page with Rational Web and write lang.js. Returns the files written."""
    app = make_app(load_docs(renderer()))
    website = ROOT / "website"
    written = []
    with tempfile.TemporaryDirectory() as tmp:
        report = asyncio.run(export_site(app, tmp, not_found=False))
        if report.skipped:
            raise SystemExit(f"Pages not exported: {report.skipped}")
        for page in sorted(Path(tmp).rglob("*.html")):
            target = website / page.relative_to(tmp)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(page.read_bytes())
            written.append(target)
    written.append(write_lang_script())
    return written


def app_version() -> str:
    text = (ROOT / "zettelapp" / "__init__.py").read_text(encoding="utf-8")
    match = re.search(r'^__version__\s*=\s*"([^"]+)"', text, re.M)
    if not match:
        raise SystemExit("No __version__ in zettelapp/__init__.py")
    return match.group(1)


def write_version_file() -> Path:
    """website/version.json, read by the app's update check (only "version" is used)."""
    target = ROOT / "website" / "version.json"
    data = {"name": "ZettelApp", "version": app_version()}
    target.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8", newline="\n")
    return target


if __name__ == "__main__":
    files = build()
    version_file = write_version_file()
    print(f"Wrote {len(files)} pages to {OUT} and {version_file.name}")
    sys.exit(0)
