# Roadmap

Ideas and planned work for ZettelApp. Suggestions are welcome in
[GitHub issues](https://github.com/DutraIRS/ZettelApp/issues).

**Companies can sponsor a specific roadmap item** through [Ko-fi](https://ko-fi.com/dutrairs) or by getting in
touch on [GitHub](https://github.com/DutraIRS/ZettelApp).

The first two items were requested for 1.0, evaluated, and **deferred because they are not quick**.
Each would need careful work across the whole app rather than a small addition.

## 1. App localisation (many languages)

**Status: translation infrastructure is ready; the app remains in English until translated catalogues
are written and reviewed.**

Already done:

- The Windows installer lets you pick a language, suggests your Windows display language, and is fully
  translated (using Inno Setup's bundled translations).
- The installer stores its language choice in
  `HKEY_CURRENT_USER\Software\ZettelApp\ZettelApp\ui\language`, ready for the app catalogues.
- User-visible interface strings are marked for translation and extracted into a source catalogue.
- The app has safe catalogue loading, plural rules, right-to-left layout support and English fallback.

Plan:

1. Translate. Start with **Portuguese (Brazil), Spanish, French and German**, then accept community
   translations and expose complete catalogues in *Tools ▸ Options ▸ General*.
2. Review every catalogue with a native speaker and test layouts with longer strings.
3. Translate the documentation.

The remaining work needs native-speaker review and layout checks because longer strings can break the
design.

## 2. Linux (.deb, AppImage, Flatpak)

**Status: planned.** *(Evaluated for 1.0 and deferred.)*

What already works: the core is plain Python and Qt, which run on Linux. That covers storage, search, link
suggestions, clustering, export and import, Anki, Zotero, the AI providers and the MCP server, and the
whole test suite should pass there.

Checklist:

- [ ] **Icons**: the app draws icons from Windows' *Segoe Fluent Icons* font, which Linux doesn't have.
  Add a fallback: an open icon set bundled as SVG, or freedesktop theme icons via `QIcon.fromTheme`.
- [ ] **Paths**: XDG locations (`~/.local/share/ZettelApp`, `~/.cache/ZettelApp`, `~/Documents`
  via `xdg-user-dir`) instead of `%LOCALAPPDATA%`.
- [ ] **API keys**: store them with the Secret Service (libsecret / GNOME Keyring / KWallet) instead of
  Windows Credential Manager. Today, Linux keeps them in memory only.
- [ ] **Links**: a `.desktop` file with `MimeType=x-scheme-handler/zettelapp;`, so `zettelapp://` links
  from Anki open notes.
- [ ] **Theme**: follow the desktop's light/dark preference and accent colour where available.
- [ ] **Packaging**: a PyInstaller build on Linux, packed into a `.deb` (`dpkg-deb` or fpm) and an
  AppImage, then possibly a Flatpak on Flathub.
- [ ] **CI**: an Ubuntu job that runs the tests and builds the packages on each release.

Why deferred: each item is small, but together they need testing on real Linux desktops (GNOME, KDE)
and a second release pipeline.

## 3. Signed Windows builds

Sign `ZettelApp.exe`, `zettelapp-mcp.exe` and the installer with a code-signing certificate, so Microsoft
Defender SmartScreen stops warning on first run. The release workflow already has a place for a signing
step.

## 4. macOS

A universal `.app` bundle and `.dmg`, after the Linux work: icon fallback, Keychain for API keys and
platform paths.

## 5. Sync between devices

Optional sync of a vault between computers. Options include a change log in the database merged through
a folder you already sync, or a self-hosted service. The goal is to avoid conflicts when the same vault
is open on two machines.

## 6. More ideas

- **Local embedding models** for semantic similarity and *Ask your notes*, fully offline (for example
  through Ollama or ONNX Runtime). They would be optional additions alongside LSA.
- **Import PDF annotations** from Zotero into literature notes.
- **Zotero group libraries** in the reference search.
- **Plugins**: a small extension API for custom link-suggestion features, exporters and importers.
- **Daily notes and templates.**
- **Mind map ↔ notes**: turn a mind map's ideas into linked notes in one step.
- **Accessibility audit** with Windows Narrator, and a high-contrast theme.
- **Bulk editing**: tag, retype links or export a hand-picked selection of notes.
