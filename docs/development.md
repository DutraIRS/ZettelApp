# Development

ZettelApp is written in Python with [Qt for Python (PySide6)](https://doc.qt.io/qtforpython-6/).

## Set up

You need Python 3.12 or later on Windows, and Git.

```powershell
git clone https://github.com/DutraIRS/ZettelApp.git
cd ZettelApp
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python -m zettelapp
```

## Tests

```powershell
pytest
```

The tests cover:

- the core library: storage, similarity measures, the Naive Bayes suggester, clustering, export and
  import, Anki, quizzes, Zotero, the LLM providers (no network) and the MCP server;
- the security checks;
- a smoke test of the main window, run offscreen.

They never touch your real preferences or Credential Manager entries beyond a throwaway test key.

## Useful tools

| Command | What it does |
|---|---|
| `python tools/make_icon.py` | Redraws the app icon (`zettelapp/resources/icon.ico`, PNGs) and the website icons. |
| `python tools/screenshots.py` | Renders screenshots of the real app (light and dark) into `website/assets/screenshots/`, using a demo vault (`tools/demo_vault.py`) and temporary settings. |
| `python tools/build_site.py` | Builds the documentation pages of the website (`website/docs/`, and `website/<language>/` from `docs/<language>/`) from Markdown, the language script and `website/version.json` from the app version. |
| `python tools/i18n.py extract` | Collects every interface string passed to `_()`, `n_()` and `N_()` into `zettelapp/resources/locales/messages.json` (a test fails when it is out of date). |
| `python tools/i18n.py check` | Reports missing, stale and broken entries in each translation catalogue. |

## Build the Windows app

```powershell
pwsh packaging/build.ps1
```

This produces:

- `dist/ZettelApp/`: the app folder (PyInstaller, one-folder mode) with `ZettelApp.exe` and the console
  MCP server `zettelapp-mcp.exe`;
- `dist/ZettelApp-Portable.zip`;
- `dist/ZettelApp-Setup.exe`, when [Inno Setup 6](https://jrsoftware.org/isinfo.php) is installed: a
  per-user installer (no administrator rights) with a language picker, Start menu shortcut, uninstaller
  and `zettelapp://` link registration;
- `dist/SHA256SUMS.txt`.

The executables carry Windows version information and the app icon. One-folder builds start faster and
trigger fewer antivirus false positives than single-file builds.

## Release

1. Update `__version__` in `zettelapp/__init__.py` and `CHANGELOG.md`, run `python tools/build_site.py`
   (it also writes `website/version.json` from `zettelapp.__version__`, which installed copies read to
   learn about new versions) and commit the result.
2. Commit, then tag and push: `git tag v1.0.1; git push origin v1.0.1`.
3. GitHub Actions checks that the tag matches the app version, runs lint, formatting, the tests and the
   dependency audit, builds the app on Windows and publishes a GitHub release with
   `ZettelApp-Setup.exe`, `ZettelApp-Portable.zip` and `SHA256SUMS.txt`. The website's download buttons
   always point to the latest release.

A release needs a **code-signing certificate**, stored in the repository secrets
`WINDOWS_SIGNING_CERT_BASE64` and `WINDOWS_SIGNING_CERT_PASSWORD`. Without it the release job stops,
unless the repository variable `ALLOW_UNSIGNED_RELEASE` is set to `true` to approve an unsigned release
(see `.github/workflows/release.yml`).

The CI workflow (`.github/workflows/ci.yml`) runs each check as its own step: lint, formatting, the
dependency audit and a check that the generated website files are up to date (it fails when
`website/docs` or `website/version.json` differ from what `tools/build_site.py` writes), then the tests
and a build of the packaged app with its self-test.

`packaging/build.ps1` finds Inno Setup on `PATH`, installed for the current user
(`%LOCALAPPDATA%\Programs\Inno Setup 6`) or for everyone.

The vault database has a **schema version** (currently 2: the `tags.source` column tells tags added by
hand from `#tags` written in the text). Older vaults are upgraded automatically when opened.

The website (`website/`) is deployed to GitHub Pages by `.github/workflows/pages.yml` whenever `docs/` or
`website/` change on `main`.

## Project layout

```text
zettelapp/
  core/            Qt-free logic (tested without a GUI)
    storage.py     the vault: SQLite schema, notes, typed links, tags, assets, cards, backups
    similarity.py  Levenshtein, Jaro-Winkler, Jaccard, TF-IDF and LSA
    suggest.py     Naive Bayes link suggester
    cluster.py     k-means, hierarchical clustering, silhouette, cluster keywords
    graph.py       subgraphs and force-directed layout (2D/3D)
    render.py      safe Markdown rendering (notes, exports, Anki)
    export.py      export formats; importer.py: imports
    anki.py        .apkg export and AnkiConnect sync
    quiz.py        SM-2 scheduling and quiz generation
    zotero.py      Zotero local API client
    llm.py         AI providers (registry + adapters) and retrieval
    secrets.py     Windows Credential Manager
    security.py    validation of URLs, file names, images, archives
  ui/              PySide6 widgets: main window, editor, graph views, pages, dialogs, theme
  resources/       icon, adventure illustrations, translation catalogues (locales/)
  i18n.py          interface languages: _(), n_(), plural rules, loading catalogues
  mcp_server.py    MCP server; mcp_main.py: its entry point (zettelapp-mcp.exe)
  app.py           startup, single instance, logging
  settings.py      preferences (QSettings)
  winintegration.py  taskbar identity, dark title bars, zettelapp:// protocol
tests/             pytest suite
tools/             icon, screenshots, demo vault, website builder, translation tools
packaging/         PyInstaller spec, version info, Inno Setup script, build script
docs/              this documentation (also published on the website)
website/           the GitHub Pages site
```

## Adding an AI provider

Add an entry to `PROVIDERS` in `zettelapp/core/llm.py`:

```python
"mistral": ProviderInfo(
    "mistral", "Mistral", OPENAI_COMPATIBLE, "https://api.mistral.ai/v1", "mistral-large-latest",
    ("mistral-large-latest",), "https://console.mistral.ai/api-keys"),
```

Providers that speak the OpenAI chat-completions protocol need nothing else. For a new protocol, write an
adapter class with `stream()` and `list_models()` and register it in `_ADAPTERS`. Keys are stored under
`ZettelApp/llm/<id>` automatically, and the Options page lists the new provider.
