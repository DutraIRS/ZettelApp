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
    ("mcp-reference", "MCP API reference"),
    ("export-import", "Export and import"),
    ("keyboard-shortcuts", "Keyboard shortcuts"),
    ("privacy-and-security", "Privacy and security"),
    ("development", "Development"),
    ("faq", "FAQ"),
]

CSP = (
    "default-src 'self'; img-src 'self'; style-src 'self'; script-src 'self'; "
    "base-uri 'none'; form-action 'none'"
)

# Translated sites: folder -> (native name, HTML language, right-to-left, flag emoji, browser
# language prefixes that should redirect to it). English is the root ("").
LANGS = {
    "es": ("Español", "es", False, "🇪🇸", ["es"]),
    "pt-br": ("Português (Brasil)", "pt-BR", False, "🇧🇷", ["pt"]),
    "fr": ("Français", "fr", False, "🇫🇷", ["fr"]),
    "de": ("Deutsch", "de", False, "🇩🇪", ["de"]),
    "it": ("Italiano", "it", False, "🇮🇹", ["it"]),
    "ru": ("Русский", "ru", False, "🇷🇺", ["ru"]),
    "zh-cn": ("简体中文", "zh-CN", False, "🇨🇳", ["zh"]),
    "ja": ("日本語", "ja", False, "🇯🇵", ["ja"]),
    "ko": ("한국어", "ko", False, "🇰🇷", ["ko"]),
    "ar": ("العربية", "ar", True, "🇸🇦", ["ar"]),
}
EN_FLAG = "🇺🇸"
# Translated pages: the user documentation (development and the MCP reference stay English).
TRANSLATED = [p for p, _ in PAGES if p not in ("mcp-reference", "development")]

# Page chrome per language: skip, features, tutorial, docs, donate, download, menu,
# documentation, mistake ({link} wraps "edit"), home, issues, title ("{t}" suffix), languages.
CHROME = {
    "en": (
        "Skip to content",
        "Features",
        "Tutorial",
        "Docs",
        "Donate",
        "Download",
        "Menu",
        "Documentation",
        "Found a mistake? {link}.",
        "Edit this page on GitHub",
        "Home",
        "Issues",
        "{t} – ZettelApp documentation",
        "Languages",
    ),
    "es": (
        "Saltar al contenido",
        "Funciones",
        "Tutorial",
        "Documentación",
        "Donar",
        "Descargar",
        "Menú",
        "Documentación",
        "¿Encontraste un error? {link}.",
        "Edita esta página en GitHub",
        "Inicio",
        "Incidencias",
        "{t} – documentación de ZettelApp",
        "Idiomas",
    ),
    "pt-br": (
        "Ir para o conteúdo",
        "Recursos",
        "Tutorial",
        "Documentação",
        "Doar",
        "Baixar",
        "Menu",
        "Documentação",
        "Encontrou um erro? {link}.",
        "Edite esta página no GitHub",
        "Início",
        "Problemas",
        "{t} – documentação do ZettelApp",
        "Idiomas",
    ),
    "fr": (
        "Aller au contenu",
        "Fonctionnalités",
        "Tutoriel",
        "Documentation",
        "Faire un don",
        "Télécharger",
        "Menu",
        "Documentation",
        "Une erreur ? {link}.",
        "Modifier cette page sur GitHub",
        "Accueil",
        "Tickets",
        "{t} – documentation de ZettelApp",
        "Langues",
    ),
    "de": (
        "Zum Inhalt springen",
        "Funktionen",
        "Tutorial",
        "Doku",
        "Spenden",
        "Herunterladen",
        "Menü",
        "Dokumentation",
        "Fehler gefunden? {link}.",
        "Diese Seite auf GitHub bearbeiten",
        "Start",
        "Issues",
        "{t} – ZettelApp-Dokumentation",
        "Sprachen",
    ),
    "it": (
        "Vai al contenuto",
        "Funzionalità",
        "Tutorial",
        "Documentazione",
        "Dona",
        "Scarica",
        "Menu",
        "Documentazione",
        "Hai trovato un errore? {link}.",
        "Modifica questa pagina su GitHub",
        "Home",
        "Segnalazioni",
        "{t} – documentazione di ZettelApp",
        "Lingue",
    ),
    "ru": (
        "К содержимому",
        "Возможности",
        "Руководство",
        "Документация",
        "Поддержать",
        "Скачать",
        "Меню",
        "Документация",
        "Нашли ошибку? {link}.",
        "Править страницу на GitHub",
        "Главная",
        "Проблемы",
        "{t} – документация ZettelApp",
        "Языки",
    ),
    "zh-cn": (
        "跳到内容",
        "功能",
        "教程",
        "文档",
        "捐赠",
        "下载",
        "菜单",
        "文档",
        "发现错误？{link}。",
        "在 GitHub 上编辑此页",
        "首页",
        "问题",
        "{t} – ZettelApp 文档",
        "语言",
    ),
    "ja": (
        "本文へスキップ",
        "機能",
        "チュートリアル",
        "ドキュメント",
        "寄付",
        "ダウンロード",
        "メニュー",
        "ドキュメント",
        "誤りを見つけたら：{link}。",
        "GitHub でこのページを編集",
        "ホーム",
        "Issues",
        "{t} – ZettelApp ドキュメント",
        "言語",
    ),
    "ko": (
        "본문으로 건너뛰기",
        "기능",
        "튜토리얼",
        "문서",
        "후원",
        "다운로드",
        "메뉴",
        "문서",
        "오류를 발견하셨나요? {link}.",
        "GitHub에서 이 페이지 편집",
        "홈",
        "이슈",
        "{t} – ZettelApp 문서",
        "언어",
    ),
    "ar": (
        "انتقل إلى المحتوى",
        "الميزات",
        "الدرس",
        "التوثيق",
        "تبرّع",
        "تنزيل",
        "القائمة",
        "التوثيق",
        "وجدت خطأ؟ {link}.",
        "حرّر هذه الصفحة على GitHub",
        "الرئيسية",
        "المشكلات",
        "{t} – توثيق ZettelApp",
        "اللغات",
    ),
}

TEMPLATE = """<!doctype html>
<html lang="{lang}"{dir}>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="{csp}">
<meta name="color-scheme" content="light dark">
<meta name="description" content="{description}">
<title>{title}</title>
<link rel="icon" type="image/png" href="{up}assets/favicon.png">
<link rel="stylesheet" href="{up}style.css">
<script src="{up}assets/lang.js" defer></script>
</head>
<body>
<a class="skip" href="#content">{c_skip}</a>
<header class="site-header">
  <div class="wrap header-row">
    <a class="brand" href="../"><img src="{up}assets/favicon.png" alt="" width="28" height="28"> <span class="brand-name">ZettelApp</span></a>
    <nav class="nav-wide" aria-label="Main">
      <ul class="nav">
        <li><a href="../#features">{c_features}</a></li>
        <li><a href="tutorial.html">{c_tutorial}</a></li>
        <li><a href="./">{c_docs}</a></li>
        <li><a href="https://github.com/DutraIRS/ZettelApp">GitHub</a></li>
        <li><a class="nav-donate" href="https://ko-fi.com/dutrairs" rel="noopener"><span aria-hidden="true">♥</span> {c_donate}</a></li>
        <li><a class="nav-cta" href="../#download">{c_download}</a></li>
      </ul>
    </nav>
    {langswitch}
    <div class="header-actions">
      <a class="hbtn donate" href="https://ko-fi.com/dutrairs" rel="noopener" aria-label="{c_donate}"><span aria-hidden="true">♥</span><span class="hbtn-text" aria-hidden="true">{c_donate}</span></a>
      <a class="hbtn cta" href="../#download">{c_download}</a>
      <details class="menu">
        <summary><span class="menu-icon" aria-hidden="true"></span><span class="sr-only">{c_menu}</span></summary>
        <ul class="menu-panel">
          <li><a href="../#features">{c_features}</a></li>
          <li><a href="tutorial.html">{c_tutorial}</a></li>
          <li><a href="./">{c_docs}</a></li>
          <li><a href="https://github.com/DutraIRS/ZettelApp">GitHub</a></li>
        </ul>
      </details>
    </div>
  </div>
</header>
<div class="wrap docs-layout">
  <nav class="docs-nav" aria-label="{c_documentation}">
    <details class="docs-menu">
      <summary><span class="docs-menu-text"><span class="docs-menu-label">{c_documentation}</span><span class="docs-menu-current">{current}</span></span></summary>
      <ul>
{nav}
      </ul>
    </details>
    <div class="docs-list">
      <h2>{c_documentation}</h2>
      <ul>
{nav}
      </ul>
    </div>
  </nav>
  <main id="content" class="doc">
{body}
    <p class="doc-footer">{mistake}</p>
  </main>
</div>
<footer class="site-footer">
  <div class="wrap footer-row">
    <p><img src="{up}assets/favicon.png" alt="" width="20" height="20">
      <span>ZettelApp · public domain (<a href="https://github.com/DutraIRS/ZettelApp/blob/main/LICENSE">The Unlicense</a>)</span></p>
    <ul class="nav">
      <li><a href="../">{c_home}</a></li>
      <li><a href="https://github.com/DutraIRS/ZettelApp/issues">{c_issues}</a></li>
      <li><a href="https://ko-fi.com/dutrairs" rel="noopener">{c_donate}</a></li>
    </ul>
  </div>
  {langs}
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
    for block in markdown.split("\n\n"):
        block = block.strip()
        if block and not block.startswith(("#", "!", "|", "```", "-")):
            text = re.sub(r"[*_`\[\]]|\(([^)]*)\)", "", " ".join(block.split()))
            return html.escape(text[:180], quote=True)
    return "ZettelApp documentation"


def _language_links(
    current: str, target: str, stem: str = ""
) -> list[tuple[str, str, str, str, str]]:
    """(folder, name, code, flag, href) for every language, for *current* page's language/kind.

    *target* is "docs" for a documentation page (linking to the same page) or "home".
    """
    entries = [("", "English", "en", EN_FLAG)] + [
        (d, n, h, f) for d, (n, h, _, f, _p) in LANGS.items()
    ]
    links = []
    for folder, name, code, flag in entries:
        if target == "home":
            if current:
                href = f"../{folder}/" if folder else "../"
            else:
                href = f"{folder}/" if folder else "./"
        else:
            page = f"{stem}.html" if folder == "" or stem in TRANSLATED else "./"
            if folder:
                href = ("../" if current == "" else "../../") + f"{folder}/docs/{page}"
                if page == "./":
                    href = ("../" if current == "" else "../../") + f"{folder}/docs/"
            else:
                href = ("" if current == "" else "../../docs/") + f"{stem}.html"
        links.append((folder, name, code, flag, href))
    return links


def language_row(current: str, target: str, stem: str = "") -> str:
    """The footer list of language links (full native names, one per language)."""
    label = CHROME[current or "en"][13]
    items = []
    for folder, name, code, _flag, href in _language_links(current, target, stem):
        marker = ' aria-current="true"' if folder == current else ""
        items.append(
            f'<li><a href="{href}" lang="{code}" hreflang="{code}"{marker}>{html.escape(name)}</a></li>'
        )
    return f'<ul class="nav lang-row" aria-label="{html.escape(label)}">{"".join(items)}</ul>'


def language_switch(current: str, target: str, stem: str = "") -> str:
    """A CSS-only flag dropdown in the header to switch the current page's language."""
    label = CHROME[current or "en"][13]
    links = _language_links(current, target, stem)
    current_flag = next(flag for folder, _n, _c, flag, _h in links if folder == current)
    items = []
    for folder, name, code, flag, href in links:
        marker = ' aria-current="true"' if folder == current else ""
        items.append(
            f'<li><a href="{href}" lang="{code}" hreflang="{code}"{marker}>'
            f'<span aria-hidden="true">{flag}</span> {html.escape(name)}</a></li>'
        )
    summary = f'<span aria-hidden="true">{current_flag}</span><span class="sr-only">{html.escape(label)}</span>'
    return (
        f'<details class="lang-switch"><summary>{summary}</summary>'
        f'<ul class="lang-switch-panel" aria-label="{html.escape(label)}">{"".join(items)}</ul></details>'
    )


def build_language(folder: str, md: MarkdownIt) -> list[Path]:
    """Build website/<folder>/docs/*.html from docs/<folder>/*.md."""
    _, lang, rtl, _flag, _prefixes = LANGS[folder]
    chrome = CHROME[folder]
    out = ROOT / "website" / folder / "docs"
    out.mkdir(parents=True, exist_ok=True)
    titles: dict[str, str] = {}
    texts: dict[str, str] = {}
    for stem in TRANSLATED:
        source = DOCS / folder / f"{stem}.md"
        if not source.exists():
            raise SystemExit(f"Missing translated page: {source}")
        texts[stem] = source.read_text(encoding="utf-8")
        match = re.search(r"^#\s+(.+)$", texts[stem], re.M)
        titles[stem] = match.group(1).strip() if match else stem
    nav = "\n".join(
        f'      <li><a href="{p}.html"@@{p}@@>{html.escape(titles[p])}</a></li>' for p in TRANSLATED
    )
    written = []
    for stem in TRANSLATED:
        page = render_page(
            md,
            texts[stem],
            stem,
            titles[stem],
            nav,
            chrome,
            lang,
            rtl,
            folder,
            f"{REPO}docs/{folder}/{stem}.md",
        )
        target = out / f"{stem}.html"
        target.write_text(page, encoding="utf-8", newline="\n")
        written.append(target)
    return written


def render_page(md, text, stem, label, nav, chrome, lang, rtl, folder, source_url) -> str:
    c = chrome
    title_match = re.search(r"^#\s+(.+)$", text, re.M)
    title = title_match.group(1).strip() if title_match else label
    link = f'<a href="{source_url}">{html.escape(c[9])}</a>'
    return TEMPLATE.format(
        csp=CSP,
        lang=lang,
        dir=' dir="rtl"' if rtl else "",
        up="../../" if folder else "../",
        title=html.escape(c[12].format(t=title)),
        current=html.escape(label),
        description=description(text),
        nav=re.sub(
            r"@@(.+?)@@", lambda m: ' aria-current="page"' if m.group(1) == stem else "", nav
        ),
        body=postprocess(md.render(text), folder),
        mistake=c[8].format(link=link),
        langs=language_row(folder, "docs", stem),
        langswitch=language_switch(folder, "docs", stem),
        c_skip=c[0],
        c_features=c[1],
        c_tutorial=c[2],
        c_docs=c[3],
        c_donate=c[4],
        c_download=c[5],
        c_menu=c[6],
        c_documentation=c[7],
        c_home=c[10],
        c_issues=c[11],
    )


def build_landing_pages() -> list[Path]:
    """Refresh the language links in the landing pages, between the <!--langs--> (footer list)
    and <!--langswitch--> (header flag dropdown) markers."""
    written = []
    for folder in ["", *LANGS]:
        path = (
            ROOT / "website" / folder / "index.html" if folder else ROOT / "website" / "index.html"
        )
        if not path.exists():
            continue
        page = path.read_text(encoding="utf-8")
        row = language_row(folder, "home")
        switch = language_switch(folder, "home")
        page, n1 = re.subn(
            r"<!--langs-->.*?<!--/langs-->",
            lambda _: f"<!--langs-->{row}<!--/langs-->",
            page,
            flags=re.S,
        )
        page, n2 = re.subn(
            r"<!--langswitch-->.*?<!--/langswitch-->",
            lambda _: f"<!--langswitch-->{switch}<!--/langswitch-->",
            page,
            flags=re.S,
        )
        if n1 or n2:
            path.write_text(page, encoding="utf-8", newline="\n")
            written.append(path)
    return written


def write_lang_script() -> Path:
    """website/assets/lang.js: redirect a first-time visitor to their browser language once.

    Nothing is sent anywhere; the only persisted value is the chosen language folder, kept in
    localStorage so the redirect happens at most once and never overrides a language the visitor
    already reached by browsing (including picking one from the dropdown).
    """
    folder_alt = "|".join(re.escape(f) for f in LANGS)
    prefixes = {"": ["en"], **{f: p for f, (_n, _h, _r, _fl, p) in LANGS.items()}}
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
      var stem = m[2] || "index";
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
    var path = location.pathname;
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


def build() -> list[Path]:
    md = renderer()
    OUT.mkdir(parents=True, exist_ok=True)
    written = []
    english = dict(PAGES)
    nav = "\n".join(
        f'      <li><a href="{p}.html"@@{p}@@>{html.escape(l)}</a></li>' for p, l in PAGES
    )
    for stem, label in PAGES:
        source = DOCS / f"{stem}.md"
        if not source.exists():
            raise SystemExit(f"Missing documentation page: {source}")
        text = source.read_text(encoding="utf-8")
        page = render_page(
            md,
            text,
            stem,
            english[stem],
            nav,
            CHROME["en"],
            "en",
            False,
            "",
            f"{REPO}docs/{stem}.md",
        )
        target = OUT / f"{stem}.html"
        target.write_text(page, encoding="utf-8", newline="\n")
        written.append(target)
    for folder in LANGS:
        if (DOCS / folder).is_dir():
            written += build_language(folder, md)
    build_landing_pages()
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
