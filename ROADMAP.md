# Roadmap

Ideas and planned work for ZettelApp. Suggestions are welcome in
[GitHub issues](https://github.com/DutraIRS/ZettelApp/issues).

**Companies can sponsor a specific roadmap item** through [Ko-fi](https://ko-fi.com/dutrairs) or by getting in
touch on [GitHub](https://github.com/DutraIRS/ZettelApp).

Linux support was requested for 1.0, evaluated, and **deferred because it is not quick**: it needed
careful work across the whole app rather than a small addition. It has since shipped — see item 2.

## 1. App localisation (many languages)

**Status: done in 1.1.** The app, its documentation and the website are available in English, Spanish,
Portuguese (Brazil), French, German, Italian, Russian, Simplified Chinese, Japanese, Korean and Arabic
(right to left). The language follows your system or the installer's choice, and can be changed in
*Tools ▸ Options ▸ General*.

Still to do:

- A review of every catalogue by a native speaker. Corrections are welcome as GitHub issues or pull
  requests against `zettelapp/resources/locales/<language>.json` and `docs/<language>/`.
- More languages: `python tools/i18n.py extract` lists every string in
  `zettelapp/resources/locales/messages.json`, and `python tools/i18n.py check` reports what a catalogue is
  missing.

## 2. Linux (.deb, portable archive, Flatpak, Snap)

**Status: done in 1.4** (from the original evaluation and checklist):

- [x] **Icons**: every icon is painted with QPainter through a bundled shape library (`ui/iconshapes.py`),
  so the app looks right without Windows' *Segoe Fluent Icons* font and without any icon theme.
- [x] **Paths**: XDG locations — notes default to `~/Documents/ZettelApp` via `xdg-user-dir`, settings in
  `~/.config/ZettelApp`, caches in `~/.cache/ZettelApp`.
- [x] **API keys**: stored with the Secret Service through libsecret (GNOME Keyring / KWallet); the
  Windows Credential Manager path is untouched and the memory-only fallback remains.
- [x] **Links**: the `.deb` ships a `.desktop` file with `MimeType=x-scheme-handler/zettelapp;`; other
  installs register a user-local desktop entry from *Options ▸ Desktop integration*.
- [x] **Theme**: follows the desktop's light/dark preference and accent colour (GNOME via `gsettings`,
  KDE via `kdeglobals`), with per-platform font stacks.
- [x] **Packaging**: a PyInstaller build on Linux packed into a portable `.tar.gz` and a `.deb`
  (`packaging/build-linux.sh`), a Flatpak manifest (`packaging/flatpak/`, freedesktop 24.08) and a Snap
  recipe (`packaging/snap/`, core24 + GNOME). AppImage was dropped in favour of the portable archive:
  it covers the same "run anywhere" need without bundling a runtime. Store listings (Flathub, Snap
  Store) are planned — the release workflow can already publish the Snap when credentials exist.
- [x] **CI**: Ubuntu jobs run the tests and build the packages on every pull request; releases carry
  the `.deb` and `.tar.gz` alongside the Windows installer.

Still open: reviews of the Linux builds on more real desktops (GNOME and KDE Wayland sessions in
particular), and the Flathub submission.

## 3. Signed Windows builds

Sign `ZettelApp.exe`, `zettelapp-mcp.exe` and the installer with a code-signing certificate, so Microsoft
Defender SmartScreen stops warning on first run. The release workflow already has a place for a signing
step.

## 4. macOS

A universal `.app` bundle and `.dmg`, after the Linux work: icon fallback, Keychain for API keys and
platform paths.

## 5. Android (mobile app)

**Status: in progress.** The core (storage, models, Markdown rendering, Anki
export, security) is plain Python and runs on Android through
[Chaquopy](https://chaquo.com/chaquopy/); a native Kotlin/Compose screen calls
it through the small, Qt-free `zettelapp.mobile` facade (`android/` holds the
Gradle project).

What works:

- Notes list with search and a tag filter, editing and creating notes, links,
  backlinks and flashcards under each note, a graph, Insights and flashcard
  review. The vault lives in the app's private storage (scoped storage won't
  let SQLite open a database in the shared `Documents` folder).
- `zettelapp://note/<id>` deep links open the matching note.
- API keys stay in memory for the session (Android has no shared secret store
  the app could use yet).
- AnkiDroid availability checks and `zotero://` links through Android intents.

Still to do:

- Semantic search and *Ask your notes* on device (needs onnxruntime/tokenizers
  Android wheels), on-device flashcard export to AnkiDroid, a release pipeline
  with signing, and store listings.
- The Markdown renderer in the preview, a force-directed graph, translated
  phone screens, and opening a vault in shared storage through the Storage
  Access Framework.

## 6. Sync between devices

Optional sync of a vault between computers. Options include a change log in the database merged through
a folder you already sync, or a self-hosted service. The goal is to avoid conflicts when the same vault
is open on two machines.

## 7. More ideas

- **More uses for the local language model** that semantic search can download: link suggestions and
  *Ask your notes*, fully offline. They would be optional additions alongside LSA.
- **Import PDF annotations** from Zotero into literature notes.
- **Zotero group libraries** in the reference search.
- **Plugins**: a small extension API for custom link-suggestion features, exporters and importers.
- **Daily notes and templates.**
- **Mind map ↔ notes**: turn a mind map's ideas into linked notes in one step.
- **Accessibility audit** with Windows Narrator, and a high-contrast theme.
- **Bulk editing**: tag, retype links or export a hand-picked selection of notes.
