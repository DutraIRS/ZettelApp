"""The ZettelApp website as a Rational Web app (https://github.com/DutraIRS/Rational-Web).

Pages are built from components: the head, the header with its language menu, the footer and
the documentation layout. Content is data: documentation pages come from docs/**/*.md (see
build_site.py), and each landing page's strings and main section from
tools/site_content/landing/<language>.json and .html.

The app is only ever exported (tools/build_site.py): every page is static, links are relative,
and there is no Rational theme, runtime or inline style, so the site keeps its own stylesheet
and its strict Content-Security-Policy.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from rational import App, Page, h, unsafe_html

CONTENT = Path(__file__).resolve().parent / "site_content"
GITHUB = "https://github.com/DutraIRS/ZettelApp"
KOFI = "https://ko-fi.com/dutrairs"
RATIONAL_WEB = "https://github.com/DutraIRS/Rational-Web"


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

# Translated sites: folder -> (native name, HTML language, right-to-left, browser language
# prefixes that should redirect to it). English is the root ("").
LANGS = {
    "es": ("Español", "es", False, ["es"]),
    "pt-br": ("Português (Brasil)", "pt-BR", False, ["pt"]),
    "fr": ("Français", "fr", False, ["fr"]),
    "de": ("Deutsch", "de", False, ["de"]),
    "it": ("Italiano", "it", False, ["it"]),
    "ru": ("Русский", "ru", False, ["ru"]),
    "zh-cn": ("简体中文", "zh-CN", False, ["zh"]),
    "ja": ("日本語", "ja", False, ["ja"]),
    "ko": ("한국어", "ko", False, ["ko"]),
    "ar": ("العربية", "ar", True, ["ar"]),
}
GLOBE_ICON = (
    '<svg class="globe" viewBox="0 0 24 24" width="20" height="20" aria-hidden="true" '
    'focusable="false"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.4 2.5 3.6 5.5 '
    '3.6 9s-1.2 6.5-3.6 9c-2.4-2.5-3.6-5.5-3.6-9s1.2-6.5 3.6-9z"/></svg>'
)
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


def language_links(current: str, target: str, stem: str = "") -> list[tuple[str, str, str, str]]:
    """(folder, name, code, href) for every language, for *current* page's language/kind.

    *target* is "docs" for a documentation page (linking to the same page) or "home".
    """
    entries = [("", "English", "en")] + [(d, n, h) for d, (n, h, _r, _p) in LANGS.items()]
    links = []
    for folder, name, code in entries:
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
        links.append((folder, name, code, href))
    return links


# --- head -----------------------------------------------------------------------------------


def head_start() -> str:
    return f'<meta http-equiv="Content-Security-Policy" content="{CSP}">'


def head_end(up: str, landing: bool) -> str:
    referrer = '<meta name="referrer" content="strict-origin-when-cross-origin">' if landing else ""
    return (
        f'{referrer}<meta name="color-scheme" content="light dark">'
        f'<link rel="icon" type="image/png" href="{up}assets/favicon.png">'
        f'<link rel="stylesheet" href="{up}style.css">'
        f'<script src="{up}assets/lang.js" defer></script>'
    )


# --- chrome ---------------------------------------------------------------------------------


@dataclass(frozen=True)
class Chrome:
    """What the header and footer say and where their links go, on one page."""

    up: str  # from the page to the site root: "", "../" or "../../"
    home: str  # the landing page of this language
    here: str  # "#features" and "#download" live on the landing page
    tutorial: str
    docs: str
    skip: str
    skip_target: str
    nav_label: str
    features: str
    tutorial_label: str
    docs_label: str
    donate: str
    download: str
    menu: str
    languages: str


def language_items(current: str, target: str, stem: str) -> list:
    return [
        h(
            "li",
            h(
                "a",
                name,
                href=href,
                lang=code,
                hreflang=code,
                aria_current="true" if folder == current else None,
            ),
        )
        for folder, name, code, href in language_links(current, target, stem)
    ]


def language_switch(current: str, target: str, label: str, stem: str = ""):
    """The globe button and its CSS-only list of every language (native names, no flags)."""
    return h(
        "details",
        h("summary", unsafe_html(GLOBE_ICON), h("span", label, class_="sr-only")),
        h(
            "ul",
            language_items(current, target, stem),
            class_="lang-switch-panel",
            aria_label=label,
        ),
        class_="lang-switch",
    )


def language_row(current: str, target: str, label: str, stem: str = ""):
    return h("ul", language_items(current, target, stem), class_="nav lang-row", aria_label=label)


def header(c: Chrome, switch):
    def nav_links():
        return [
            h("li", h("a", c.features, href=f"{c.here}#features")),
            h("li", h("a", c.tutorial_label, href=c.tutorial)),
            h("li", h("a", c.docs_label, href=c.docs)),
            h("li", h("a", "GitHub", href=GITHUB)),
        ]

    heart = h("span", "♥", aria_hidden="true")
    return h(
        "header",
        h(
            "div",
            h(
                "a",
                h("img", src=f"{c.up}assets/favicon.png", alt="", width="28", height="28"),
                " ",
                h("span", "ZettelApp", class_="brand-name"),
                class_="brand",
                href=c.home,
            ),
            h(
                "nav",
                h(
                    "ul",
                    nav_links(),
                    h(
                        "li",
                        h(
                            "a",
                            heart,
                            f" {c.donate}",
                            class_="nav-donate",
                            href=KOFI,
                            rel="noopener",
                        ),
                    ),
                    h("li", h("a", c.download, class_="nav-cta", href=f"{c.here}#download")),
                    class_="nav",
                ),
                class_="nav-wide",
                aria_label=c.nav_label,
            ),
            switch,
            h(
                "div",
                h(
                    "a",
                    heart,
                    h("span", c.donate, class_="hbtn-text", aria_hidden="true"),
                    class_="hbtn donate",
                    href=KOFI,
                    rel="noopener",
                    aria_label=c.donate,
                ),
                h("a", c.download, class_="hbtn cta", href=f"{c.here}#download"),
                h(
                    "details",
                    h(
                        "summary",
                        h("span", class_="menu-icon", aria_hidden="true"),
                        h("span", c.menu, class_="sr-only"),
                    ),
                    h("ul", nav_links(), class_="menu-panel"),
                    class_="menu",
                ),
                class_="header-actions",
            ),
            class_="wrap header-row",
        ),
        class_="site-header",
    )


def footer(up: str, license_html: str, links: list, languages):
    return h(
        "footer",
        h(
            "div",
            h(
                "p",
                h("img", src=f"{up}assets/favicon.png", alt="", width="20", height="20"),
                " ",
                h("span", unsafe_html(license_html)),
            ),
            h("ul", [h("li", link) for link in links], class_="nav"),
            class_="wrap footer-row",
        ),
        languages,
        h(
            "p",
            "Proudly developed with ",
            h("a", "RationalWeb", href=RATIONAL_WEB),
            class_="made-with",
        ),
        class_="site-footer",
    )


def link(text: str, href: str, rel: str | None = None):
    return h("a", text, href=href, rel=rel or None)


# --- landing pages --------------------------------------------------------------------------


def landing(folder: str) -> tuple[dict, str]:
    code = folder or "en"
    data = json.loads((CONTENT / "landing" / f"{code}.json").read_text(encoding="utf-8"))
    main = (CONTENT / "landing" / f"{code}.html").read_text(encoding="utf-8")
    return data, main


def landing_body(folder: str):
    data, main = landing(folder)
    up = "../" if folder else ""
    label = CHROME[folder or "en"][13]
    c = Chrome(
        up=up,
        home="./",
        here="",
        tutorial="docs/tutorial.html",
        docs="docs/",
        skip=data["skip"],
        skip_target="#main",
        nav_label=data["nav_label"],
        features=data["features"],
        tutorial_label=data["tutorial"],
        docs_label=data["docs"],
        donate=data["donate"],
        download=data["download"],
        menu=data["menu"],
        languages=label,
    )
    links = [link(text, href, rel) for href, text, rel in data["footer_links"]]
    return [
        h("a", c.skip, class_="skip", href=c.skip_target),
        header(c, language_switch(folder, "home", label)),
        h("main", unsafe_html(main), id="main"),
        footer(up, data["license_html"], links, language_row(folder, "home", label)),
    ]


# --- documentation pages --------------------------------------------------------------------


@dataclass(frozen=True)
class Doc:
    folder: str  # "" for English
    stem: str
    title: str  # the page's own heading
    label: str  # its name in the documentation menu
    description: str
    body: str  # rendered Markdown
    source_url: str
    menu: tuple[tuple[str, str], ...]  # (stem, label) of every page in this language


def doc_body(doc: Doc):
    folder = doc.folder
    t = CHROME[folder or "en"]
    up = "../../" if folder else "../"
    c = Chrome(
        up=up,
        home="../",
        here="../",
        tutorial="tutorial.html",
        docs="./",
        skip=t[0],
        skip_target="#content",
        nav_label="Main",
        features=t[1],
        tutorial_label=t[2],
        docs_label=t[3],
        donate=t[4],
        download=t[5],
        menu=t[6],
        languages=t[13],
    )

    def menu_items():
        return [
            h(
                "li",
                h(
                    "a",
                    label,
                    href=f"{stem}.html",
                    aria_current="page" if stem == doc.stem else None,
                ),
            )
            for stem, label in doc.menu
        ]

    edit = h("a", t[9], href=doc.source_url)
    before, _sep, after = t[8].partition("{link}")
    links = [link(t[10], "../"), link(t[11], f"{GITHUB}/issues"), link(t[4], KOFI, "noopener")]
    return [
        h("a", c.skip, class_="skip", href=c.skip_target),
        header(c, language_switch(folder, "docs", t[13], doc.stem)),
        h(
            "div",
            h(
                "nav",
                h(
                    "details",
                    h(
                        "summary",
                        h(
                            "span",
                            h("span", t[7], class_="docs-menu-label"),
                            h("span", doc.label, class_="docs-menu-current"),
                            class_="docs-menu-text",
                        ),
                    ),
                    h("ul", menu_items()),
                    class_="docs-menu",
                ),
                h("div", h("h2", t[7]), h("ul", menu_items()), class_="docs-list"),
                class_="docs-nav",
                aria_label=t[7],
            ),
            h(
                "main",
                unsafe_html(doc.body),
                h("p", before, edit, after, class_="doc-footer"),
                id="content",
                class_="doc",
            ),
            class_="wrap docs-layout",
        ),
        footer(
            up,
            f'ZettelApp · public domain (<a href="{GITHUB}/blob/main/LICENSE">The Unlicense</a>)',
            links,
            language_row(folder, "docs", t[13], doc.stem),
        ),
    ]


# --- the app ----------------------------------------------------------------------------------


def make_app(docs: dict[tuple[str, str], Doc]) -> App:
    """Every page of the site: the landing pages and *docs*, keyed by (folder, stem)."""
    app = App(title="ZettelApp", theme=None, favicon=False)
    folders = list(LANGS)

    @app.page("/")
    class Home(Page):
        def mount(self):
            data, _main = landing("")
            self.title, self.description, self.lang = data["title"], data["description"], "en"
            self.head_start, self.head_end = head_start(), head_end("", landing=True)

        def render(self):
            return landing_body("")

    @app.page("/{folder}/", paths=[{"folder": f} for f in folders])
    class TranslatedHome(Page):
        folder: str

        def mount(self):
            data, _main = landing(self.folder)
            self.title, self.description = data["title"], data["description"]
            _name, self.lang, rtl, _prefixes = LANGS[self.folder]
            self.dir = "rtl" if rtl else None
            self.head_start, self.head_end = head_start(), head_end("../", landing=True)

        def render(self):
            return landing_body(self.folder)

    def setup(page: Page, doc: Doc) -> None:
        page.title = CHROME[doc.folder or "en"][12].format(t=doc.title)
        page.description = doc.description
        if doc.folder:
            _name, page.lang, rtl, _prefixes = LANGS[doc.folder]
            page.dir = "rtl" if rtl else None
        else:
            page.lang = "en"
        page.head_start = head_start()
        page.head_end = head_end("../../" if doc.folder else "../", landing=False)

    @app.page("/docs/{stem}.html", paths=[{"stem": s} for (f, s) in docs if not f])
    class EnglishDoc(Page):
        stem: str

        def mount(self):
            self.doc = docs[("", self.stem)]
            setup(self, self.doc)

        def render(self):
            return doc_body(self.doc)

    @app.page(
        "/{folder}/docs/{stem}.html",
        paths=[{"folder": f, "stem": s} for (f, s) in docs if f],
    )
    class TranslatedDoc(Page):
        folder: str
        stem: str

        def mount(self):
            self.doc = docs[(self.folder, self.stem)]
            setup(self, self.doc)

        def render(self):
            return doc_body(self.doc)

    return app
