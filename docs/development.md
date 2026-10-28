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
| `python tools/build_site.py` | Builds the documentation pages of the website (`website/docs/`) from `docs/*.md`. |

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

1. Update `__version__` in `zettelapp/__init__.py` and `CHANGELOG.md`.
2. Commit, then tag and push: `git tag v1.0.1; git push origin v1.0.1`.
3. GitHub Actions builds the app on Windows, runs the tests and publishes a GitHub release with
   `ZettelApp-Setup.exe`, `ZettelApp-Portable.zip` and `SHA256SUMS.txt`. The website's download buttons
   always point to the latest release.

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
  mcp_server.py    MCP server; mcp_main.py: its entry point (zettelapp-mcp.exe)
  app.py           startup, single instance, logging
  settings.py      preferences (QSettings)
  winintegration.py  taskbar identity, dark title bars, zettelapp:// protocol
tests/             pytest suite
tools/             icon, screenshots, demo vault, website builder
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
