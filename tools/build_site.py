"""Build the documentation pages of the website from docs/*.md.

Run with:  python tools/build_site.py
Writes website/docs/<page>.html (docs/index.md becomes website/docs/index.html) and
website/version.json, which installed copies read to learn about new versions.
Uses markdown-it-py with raw HTML disabled, like the app itself.
"""

from __future__ import annotations

import html
import json
import re
import sys
import unicodedata
from pathlib import Path

from markdown_it import MarkdownIt

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
OUT = ROOT / "website" / "docs"
REPO = "https://github.com/DutraIRS/ZettelApp/blob/main/"

# Sidebar order (file stem, label).
PAGES = [
    ("index", "Overview"),
    ("what-is-zettelkasten", "What is a Zettelkasten?"),
    ("tutorial", "Tutorial: first 30 minutes"),
    ("getting-started", "Getting started"),
    ("notes-and-links", "Notes and links"),
    ("link-suggestions", "Link suggestions"),
    ("graph-and-insights", "Graph and Insights"),
    ("review-and-anki", "Review, quizzes and Anki"),
    ("zotero", "Zotero"),
    ("ai-assistant", "Ask your notes (AI)"),
    ("mcp-server", "MCP server"),
    ("export-import", "Export and import"),
    ("keyboard-shortcuts", "Keyboard shortcuts"),
    ("privacy-and-security", "Privacy and security"),
    ("development", "Development"),
    ("faq", "FAQ"),
]

CSP = (
    "default-src 'self'; img-src 'self'; style-src 'self'; script-src 'none'; "
    "base-uri 'none'; form-action 'none'"
)

TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="{csp}">
<meta name="color-scheme" content="light dark">
<meta name="description" content="{description}">
<title>{title} – ZettelApp documentation</title>
<link rel="icon" type="image/png" href="../assets/favicon.png">
<link rel="stylesheet" href="../style.css">
</head>
<body>
<a class="skip" href="#content">Skip to content</a>
<header class="site-header">
  <div class="wrap header-row">
    <a class="brand" href="../"><img src="../assets/favicon.png" alt="" width="28" height="28"> ZettelApp</a>
    <nav aria-label="Main">
      <ul class="nav">
        <li><a href="../#features">Features</a></li>
        <li><a href="tutorial.html">Tutorial</a></li>
        <li><a href="./">Docs</a></li>
        <li><a href="https://github.com/DutraIRS/ZettelApp">GitHub</a></li>
        <li><a class="nav-donate" href="https://ko-fi.com/dutrairs" rel="noopener"><span aria-hidden="true">♥</span> Donate</a></li>
        <li><a class="nav-cta" href="../#download">Download</a></li>
      </ul>
    </nav>
  </div>
</header>
<div class="wrap docs-layout">
  <nav class="docs-nav" aria-label="Documentation">
    <h2>Documentation</h2>
    <ul>
{nav}
    </ul>
  </nav>
  <main id="content" class="doc">
{body}
    <p class="doc-footer">Found a mistake? <a href="{source}">Edit this page on GitHub</a>.</p>
  </main>
</div>
<footer class="site-footer">
  <div class="wrap footer-row">
    <p><img src="../assets/favicon.png" alt="" width="20" height="20"> ZettelApp · public domain
      (<a href="https://github.com/DutraIRS/ZettelApp/blob/main/LICENSE">The Unlicense</a>)</p>
    <ul class="nav">
      <li><a href="../">Home</a></li>
      <li><a href="https://github.com/DutraIRS/ZettelApp/issues">Issues</a></li>
      <li><a href="https://ko-fi.com/dutrairs" rel="noopener">Donate</a></li>
    </ul>
  </div>
</footer>
</body>
</html>
"""


def slugify(text: str) -> str:
    """GitHub-style heading anchors, so #links work on GitHub and on the site."""
    text = unicodedata.normalize("NFKD", html.unescape(re.sub(r"<[^>]+>", "", text))).lower()
    text = re.sub(r"[^\w\- ]", "", text)
    return re.sub(r" ", "-", text.strip())


def renderer() -> MarkdownIt:
    md = MarkdownIt("commonmark", {"html": False, "typographer": False})
    md.enable(["table", "strikethrough"])
    return md


def rewrite_href(href: str) -> str:
    if re.match(r"^[a-z][a-z0-9+.-]*:", href, re.I) or href.startswith("#"):
        return href
    path, _, fragment = href.partition("#")
    if path.endswith(".md"):
        stem = Path(path).stem
        known = {p for p, _ in PAGES}
        if stem in known and "/" not in path:
            path = f"{stem}.html"
        else:  # a Markdown file outside docs/ (ROADMAP.md, …): link to it on GitHub
            path = REPO + path.lstrip("./").replace("../", "")
    elif path.startswith("../website/"):
        path = "../" + path[len("../website/") :]
    elif path.startswith("../"):
        path = REPO + path[3:]
    return path + (f"#{fragment}" if fragment else "")


def postprocess(body: str) -> str:
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
            f'{m.group(1)}="{html.escape(rewrite_href(html.unescape(m.group(2))), quote=True)}"'
        ),
        body,
    )
    body = body.replace("<table>", '<div class="table-wrap"><table>').replace(
        "</table>", "</table></div>"
    )
    body = re.sub(r"<img ", '<img loading="lazy" ', body)
    return body


def description(markdown: str) -> str:
    for block in markdown.split("\n\n"):
        block = block.strip()
        if block and not block.startswith(("#", "!", "|", "```", "-")):
            text = re.sub(r"[*_`\[\]]|\(([^)]*)\)", "", " ".join(block.split()))
            return html.escape(text[:180], quote=True)
    return "ZettelApp documentation"


def build() -> list[Path]:
    md = renderer()
    OUT.mkdir(parents=True, exist_ok=True)
    written = []
    for stem, label in PAGES:
        source = DOCS / f"{stem}.md"
        if not source.exists():
            raise SystemExit(f"Missing documentation page: {source}")
        text = source.read_text(encoding="utf-8")
        body = postprocess(md.render(text))
        title_match = re.search(r"^#\s+(.+)$", text, re.M)
        title = title_match.group(1).strip() if title_match else label
        nav = "\n".join(
            f'      <li><a href="{p}.html"{' aria-current="page"' if p == stem else ""}>{html.escape(l)}</a></li>'
            for p, l in PAGES
        )
        page = TEMPLATE.format(
            csp=CSP,
            title=html.escape(title),
            description=description(text),
            nav=nav,
            body=body,
            source=f"{REPO}docs/{stem}.md",
        )
        target = OUT / f"{stem}.html"
        target.write_text(page, encoding="utf-8", newline="\n")
        written.append(target)
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
