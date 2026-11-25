<p align="center">
  <img src="website/assets/icon-512.png" alt="ZettelApp icon" width="96" height="96">
</p>

<h1 align="center">ZettelApp</h1>

<p align="center"><b>A Zettelkasten for Windows and Linux that helps you connect ideas.</b><br>
Atomic notes, typed links, mind maps, flashcards, a 2D/3D knowledge graph, and link suggestions that learn from you.</p>

<p align="center">
  <a href="https://apps.microsoft.com/detail/9PB0HCDXF63D"><b>Microsoft Store</b></a> ·
  <a href="https://github.com/DutraIRS/ZettelApp/releases/latest/download/ZettelApp-Setup.exe">Windows installer</a> ·
  <a href="https://snapcraft.io/zettelapp"><b>Snap Store</b></a> ·
  <a href="https://github.com/DutraIRS/ZettelApp/releases/latest">Linux (.deb, .tar.gz, .flatpak)</a> ·
  <a href="https://dutrairs.github.io/ZettelApp/">Website</a> ·
  <a href="https://dutrairs.github.io/ZettelApp/docs/">Documentation</a>
</p>

![ZettelApp: notes, preview and suggested links](website/assets/screenshots/notes-light.png)

## Features

- **Atomic notes in Markdown**, saved automatically. Each note has a timestamp ID, and can have tags
  (also written as `#tags` in the text), a source link, images (paste or drop), links to local files and a
  picture. Ctrl+click follows links and tags in the editor.
- **Typed, optionally directed links**: `supports:: [[Claim]]`, *contradicts*, *extends*, *example of*,
  *part of*, *cites*, or your own types. Backlinks read naturally (*Supported by*), and every type can
  have its own line style and arrow tip.
- **Search that forgives typos**, with an optional **tag ontology** (parents, synonyms, related concepts)
  and optional **semantic search** by a language model that runs on your computer, in any language. It
  can learn from your feedback.
- **Link suggestions that learn**: a Naive Bayes classifier combines semantic (LSA), keyword (TF-IDF),
  Levenshtein and Jaro-Winkler string similarity, shared tags and shared links. Accept or dismiss a
  suggestion and the model learns; hover to see *why* it was suggested.
- **Knowledge graph in 2D and 3D**, coloured by tag or by **k-means / hierarchical clusters** of meaning,
  with groups pulled together on shaded backgrounds, and local graphs around any note.
- **Mind maps** inside notes, with links to notes and PNG/SVG/FreeMind export.
- **Flashcards and quizzes**: `Q:`/`A:` and `{{c1::cloze}}` cards from your text, SM-2 spaced repetition,
  multiple choice, typed answers and *Name that note*.
- **Anki**: sync through AnkiConnect or export `.apkg` decks; links on cards open the note.
- **Zotero**: cite references and create literature notes linked to the item and its PDF.
- **Ask your notes**: answers with citations from Anthropic Claude, OpenAI or Z.ai, using your own key,
  stored in the system keyring (Windows Credential Manager, or GNOME Keyring / KWallet through the
  Secret Service on Linux).
- **MCP server**: let Claude Desktop, Claude Code and other MCP clients search and read your vault, only
  while ZettelApp is open with its status-bar MCP switch on (read-only by default).
- **Learn by doing** with *The Lost Prince of the Archive*, an optional first-run adventure that guides
  you through ZettelApp's main features.
- **Export the whole collection or any subgraph**: ZettelApp archive, Markdown (Obsidian), static website,
  JSON, GraphML, Graphviz and Anki. Imports Markdown folders and Obsidian vaults.
- **At home on your desktop**: follows your light/dark theme and accent colour (Windows, GNOME and
  KDE), or a black theme for OLED screens and colours of your own, with standard menus and shortcuts,
  per-user installers and daily backups.
- **Private and safe by design**: works offline; nothing leaves your computer unless you ask for it, apart
  from one small, optional update check at start-up. Notes can't run scripts, imports are sandboxed, and
  API keys never touch disk in plain text.

## Install

### Windows

Get it from the **[Microsoft Store](https://apps.microsoft.com/detail/9PB0HCDXF63D)** (it updates
itself and shows no SmartScreen warning), or download
**[ZettelApp-Setup.exe](https://github.com/DutraIRS/ZettelApp/releases/latest/download/ZettelApp-Setup.exe)**
(per-user, no admin rights needed) or the
**[portable zip](https://github.com/DutraIRS/ZettelApp/releases/latest/download/ZettelApp-Portable.zip)**.
Requires Windows 10 (21H2+) or 11, 64-bit.

### Linux

<a href="https://snapcraft.io/zettelapp"><picture>
    <source srcset="website/assets/badges/snap-store-en-white.svg" media="(prefers-color-scheme: dark)">
    <img src="website/assets/badges/snap-store-en-black.svg" alt="Get it from the Snap Store" height="48">
  </picture></a>

From the **[Snap Store](https://snapcraft.io/zettelapp)**: `sudo snap install zettelapp` (it updates
itself, on any distribution with snapd). To keep API keys in the system keyring, also run
`sudo snap connect zettelapp:password-manager-service`.

Or from the [latest release](https://github.com/DutraIRS/ZettelApp/releases/latest):

| Download | Use it when |
|---|---|
| `ZettelApp-Linux-amd64.deb` | You use Debian, Ubuntu, Mint or another `.deb`-based distribution: install it with `sudo apt install ./ZettelApp-Linux-amd64.deb` (or open it in your software centre). |
| `ZettelApp-Linux-x86_64.tar.gz` | You want a portable build, or use another distribution: unpack it anywhere and run `ZettelApp/zettelapp`. |
| `ZettelApp-Linux-x86_64.flatpak` | You prefer Flatpak: `flatpak install --user ./ZettelApp-Linux-x86_64.flatpak` (a bundle, not on Flathub). |

Officially supported: **Debian 13 and Ubuntu 24.04 LTS or newer** (and distributions built on them,
such as Linux Mint 22). The portable archive also runs on other 64-bit distributions with glibc 2.39 or
newer (Fedora 40+, Arch, openSUSE Tumbleweed…), without official testing.

Both bundle Python and Qt; they need a 64-bit desktop (X11 or Wayland, GNOME, KDE and others) with the
standard graphics libraries, listed in the `.deb`'s dependencies. API keys are stored in the Secret
Service (GNOME Keyring or KWallet); without a keyring ZettelApp keeps them in memory only. The Flatpak
manifest and the Snap recipe live in the repository (`packaging/`).

Checksums are listed on the [release page](https://github.com/DutraIRS/ZettelApp/releases/latest). See
[Getting started](docs/getting-started.md).

## Build from source

Windows:

```powershell
git clone https://github.com/DutraIRS/ZettelApp.git
cd ZettelApp
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
python -m zettelapp          # run
pytest                       # test
pwsh packaging/build.ps1     # build dist/ (app folder, portable zip, installer)
```

Linux (Python 3.12+, Qt offscreen for the tests):

```bash
git clone https://github.com/DutraIRS/ZettelApp.git
cd ZettelApp
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
python -m zettelapp                          # run
QT_QPA_PLATFORM=offscreen pytest             # test
bash packaging/build-linux.sh                # build dist/ (app folder, portable tar.gz, .deb)
```

More in [docs/development.md](docs/development.md).

## Documentation

Read it on the [website](https://dutrairs.github.io/ZettelApp/docs/) or in [`docs/`](docs/index.md).
New to the method? Start with **[What is a Zettelkasten?](docs/what-is-zettelkasten.md)** and the
**[tutorial: your first 30 minutes](docs/tutorial.md)**.

- [Getting started](docs/getting-started.md)
- [Notes and links](docs/notes-and-links.md)
- [Link suggestions](docs/link-suggestions.md)
- [Graph and Insights](docs/graph-and-insights.md)
- [Review, quizzes and Anki](docs/review-and-anki.md)
- [Zotero](docs/zotero.md)
- [Ask your notes (AI)](docs/ai-assistant.md)
- [MCP server](docs/mcp-server.md)
- [MCP API reference](docs/mcp-reference.md)
- [Export and import](docs/export-import.md)
- [Keyboard shortcuts](docs/keyboard-shortcuts.md)
- [Privacy and security](docs/privacy-and-security.md)
- [FAQ](docs/faq.md)

What's next: see the [roadmap](ROADMAP.md), including signed Windows builds and macOS.

## Sponsor

ZettelApp is free, public-domain software built in the open. If it saves you time, or you want to see the
roadmap happen sooner, please consider sponsoring:

- **Ko-fi:** https://ko-fi.com/dutrairs
- **Companies:** sponsorship can fund a specific roadmap item. Get in touch through GitHub.

Sponsors are thanked in the release notes. Thank you! ❤️

## Licence

ZettelApp is free and unencumbered software released into the public domain. See [LICENSE](LICENSE)
(The Unlicense). It builds on open-source components listed in
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Privacy: [PRIVACY.md](PRIVACY.md) (one update check, nothing else unless you ask). Security reports: [SECURITY.md](SECURITY.md).
Contributions: [CONTRIBUTING.md](CONTRIBUTING.md).
