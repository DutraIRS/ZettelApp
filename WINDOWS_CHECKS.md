# Checks needed on Windows

For whoever works on the Windows machine. ZettelApp was ported to Linux and gained some features
there; this list is what only Windows can confirm before the next release (1.4.0). This file is
temporary: it is deleted in the release commit.

## Setup and how to report

- Branch **`android-port`** (pull it). The Linux port, the new features and the docs are all there.
  Don't touch the `android/` folder.
- Work from source (`.venv\Scripts\python -m zettelapp`) unless an item says *installed build*
  (`pwsh packaging/build.ps1`, then run the installer from `dist/`).
- Linux-only code must leave Windows exactly as it was; shared code changed for both. A difference
  from 1.3.1 that is not listed here as intended is a bug: report it.
- Tick each item (`[x]`) and write the result under it: "same as before", what you saw, a log
  excerpt, or a screenshot path. Commit screenshots under `WINDOWS_SCREENSHOTS/` (also deleted at
  release). If you fix something, say what in the item and add a CHANGELOG line under *Unreleased*.
- Commit and push to `android-port` when done; the Linux side pulls and continues from there.

## 1. Run everything

- [ ] **Full test suite:** `.venv\Scripts\python -m pytest`, all passing. Report any failure with its
  traceback. (On Linux: 515 passed, 14 skipped.)
- [ ] **Lint and translations:** `ruff check .`, `ruff format --check .`, `python tools/i18n.py check`
  (1022/1022 in every language) and `python tools/build_site.py` leaving no changes in `website/`.
- [ ] **Packaging:** `pwsh packaging/build.ps1` builds; install it; the installed app starts, shows
  its icons (the spec now ships `zettelapp/resources/icons/`) and passes `--self-test`.

## 2. New features: try them on Windows

- [ ] **Black (OLED) theme.** *View ▸ Theme ▸ Black (OLED)* (also in *Options ▸ General ▸ App
  theme*): true black backgrounds, the dark theme's text and accent, and a **dark title bar**.
- [ ] **Your own colours.** *Options ▸ General* has *Primary colour* (buttons, check boxes, tabs,
  accents), *Secondary colour* (links in notes and in the program), *Highlight colour* (selected text
  and find matches) and *Text colour*. Pick each, press Apply: everything follows at once. *Use the
  theme's colour* puts each back. Check in light, dark and black, and with a non-blue Windows accent
  (the primary colour overrides it; without one, Windows' accent is used as before).
- [ ] **Folding panels.** The note list and the links panel each have a small tab near the bottom
  of their edge: click it to fold the panel away and back; drag the edge to resize; double-click the
  edge folds it. *View ▸ Note List* (Ctrl+Shift+L) and *View ▸ Links Panel* (Ctrl+Shift+K) do the
  same; the state survives a restart. Check that no IME or Windows shortcut takes Ctrl+Shift+L/K.
  Check it in Arabic too (right to left: the tabs and chevrons mirror).
- [ ] **Icons follow a live theme switch.** Switch light → dark → black → light while the app runs
  (and with *Use system setting*, switch Windows itself): every icon, Segoe glyphs included, takes
  the new colours at once. Before, they kept the old theme's colour.
- [ ] **Find bar Tab order.** Ctrl+H in a note: Tab from the search goes straight to *Replace with*,
  then *Replace*, *Replace all*, then the search's own buttons.
- [ ] **Alt+Shift+click for extra carets.** Alt+click still adds a caret; Alt+Shift+click does too,
  and again removes it. Note whether the Windows Alt+Shift keyboard-layout hotkey also switches the
  layout when it is enabled.
- [ ] **Help ▸ Donate** now has its own access key (Alt+H, O in English), no longer sharing D with
  *Documentation*.

## 3. Shared code changed for Linux: check Windows is unchanged

- [ ] **Icons still come from Segoe Fluent Icons** (`zettelapp/ui/icons.py` gained native and
  bundled-SVG fallbacks for Linux): nav rail, toolbar and the Bold/Italic letters look as in 1.3.1.
- [ ] **Accent colour.** With a non-blue Windows accent, the app takes it, light and dark
  (`zettelapp/ui/theme.py` was reworked).
- [ ] **Mind map link marker** (now drawn through `icons.paint`): link an idea to a note; the chain
  still shows at the idea's right end, in the text colour, light and dark.
- [ ] **Graph and mind map export to PNG/SVG** (now one shared helper): *Save graph as image* and
  the mind map's PNG and SVG export look as before.
- [ ] **Graphviz export:** the `.dot` file still says `fontname="Segoe UI"`.
- [ ] **API keys** in Windows Credential Manager (`zettelapp/core/secrets.py` changed): save, read
  and delete a key in *Options ▸ AI assistant*; the key hint and "Key … saved on this computer."
  read as before.
- [ ] **MCP switch:** with the status-bar switch on, an MCP client can call tools; switched off or
  with ZettelApp closed, it is refused.
- [ ] **Update notice** (`download_url()` changed): installed copy → *Download* opens the
  `ZettelApp-Setup.exe` link; portable zip → the release page.
- [ ] **Single instance:** a second launch and a `zettelapp://note/<id>` link from Anki bring the
  running window forward.
- [ ] **File dialogs reopen the last folder:** *Insert ▸ Image…*, *Insert ▸ Link to a File…*, the
  mind map export and *Save graph as image* open the folder used last (also after a restart), never
  ZettelApp's install folder.
- [ ] **Alarms:** set an alarm, let it fire with ZettelApp minimised. Describe what the user sees
  and hears (toast, sound, window), and whether clicking the toast opens the note and un-maximises a
  maximised window. Linux now uses the desktop's notifications with an *Open note* button.
- [ ] **Note list snippets** keep underscores inside words: a note starting with
  `supported_by:: [[X]]` shows that, not `supportedby::`.
- [ ] **Checklists:** clicking a box in the preview ticks it, and Ctrl+Z undoes it (the code was
  shared with the core).

## 4. Docs and website

The docs were corrected in all 11 languages (file manager wording, missing passages, English labels
left in translations), and gained the themes and colours. Skim `docs/getting-started.md` and the
rebuilt `website/` in one or two languages you read, and report anything wrong for Windows.

## 5. Numbers and data only Windows can give

- [ ] **Startup and a big vault.** Linux (VM, 2 CPUs, from source): warm start 1.3 s, cold 7.6 s;
  a 10,000-note vault lists and searches in 0.3-1.8 s. Time the same on Windows (installed build and
  from source) so the Linux numbers can be judged.
- [ ] **Fresh reference screenshots:** `python tools/screenshots.py` on this branch, commit the 18
  images in `website/assets/screenshots/` (the current ones predate 1.3.1). Then once more with
  `QT_SCALE_FACTOR=1.5` into `WINDOWS_SCREENSHOTS/150/`, for comparing HiDPI.
- [ ] **A vault made on Windows,** zipped as on disk (`zettel.db` plus `assets`), with pictures,
  attachments, typed links, flashcards with review history and a link to a `C:\...` file. Commit it
  as `WINDOWS_SCREENSHOTS/windows-vault.zip`; Linux checks that it opens and shows the `C:\` link as
  unavailable.

## Not part of this round

GNOME and KDE Wayland sessions are not being tested. Flatpak and Snap are being done separately on
Linux (`FLATPAK_SNAP_WAYLAND_GUIDE.md` on the Linux desktop).

## After everything passes (done on Linux)

Version 1.4.0: `zettelapp/__init__.py`, `packaging/installer.iss`, a `<release>` in
`packaging/io.github.dutrairs.zettelapp.metainfo.xml`, the CHANGELOG heading, `website/version.json`
(by `tools/build_site.py`); delete this file and `WINDOWS_SCREENSHOTS/`; tag and release.
