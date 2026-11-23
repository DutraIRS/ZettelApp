# Checks needed on Windows

For whoever works on the Windows machine. ZettelApp was ported to Linux and gained some features
there; this list is what only Windows can confirm before the next release (1.4.0). This file is
temporary: it is deleted in the release commit.

**Windows pass done on 2026-11-23** (Windows 11, display at 125 %, Windows accent red #E81123,
"show accent colour on title bars" on, Portuguese (Brazil) UI and keyboard plus en-US). Results
are under each item. Five bugs were found and fixed on Windows (commits on `android-port`, each
with a test and a CHANGELOG line); nothing else differs from 1.3.1 except what is listed as
intended. Two items need a person at the machine (marked **needs a person**).

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

How the checks were run: the real app on the real Windows platform (visible window, throwaway
settings and vault), with real key presses and clicks sent through Windows (`keybd_event`,
`mouse_event`) where an item is about system hotkeys, and Windows' own APIs to read back the
title bar mode, the keyboard layout and the native file dialog's folder.

## 1. Run everything

- [x] **Full test suite:** `.venv\Scripts\python -m pytest`, all passing. Report any failure with its
  traceback. (On Linux: 515 passed, 14 skipped.)
  - Windows: **471 passed, 61 skipped, 0 failed** (15 min). The extra skips are Linux-only tests
    (Secret Service, XDG, D-Bus, `.desktop`); the count difference is that. After the fixes below,
    the affected suites were run again: all pass. (Not counted: the uncommitted Android work in the
    working tree.)
- [x] **Lint and translations:** `ruff check .`, `ruff format --check .`, `python tools/i18n.py check`
  (1022/1022 in every language) and `python tools/build_site.py` leaving no changes in `website/`.
  - All clean on the committed code; i18n complete in every language (1022/1022 before, still
    complete after the fixes); `build_site.py` left `website/` unchanged. Lint does flag
    `zettelapp/mobile.py`, `zettelapp/settings.py` and `tests/test_mobile.py`, but only in the
    **uncommitted Android work** in the working tree (`Any` undefined, unused imports, formatting),
    not in what was pushed.
- [x] **Packaging:** `pwsh packaging/build.ps1` builds; install it; the installed app starts, shows
  its icons (the spec now ships `zettelapp/resources/icons/`) and passes `--self-test`.
  - Builds (Setup.exe and the portable zip); the build's self-tests pass; silent per-user install
    (`/VERYSILENT /CURRENTUSER`) works; the installed `ZettelApp.exe --self-test` exits 0;
    `_internal\zettelapp\resources\icons` is shipped; `zettelapp-mcp.exe --version` answers.
    Installed start-up: 2.3 s, then 1.75 s warm.

## 2. New features: try them on Windows

- [x] **Black (OLED) theme.** *View ▸ Theme ▸ Black (OLED)* (also in *Options ▸ General ▸ App
  theme*): true black backgrounds, the dark theme's text and accent, and a **dark title bar**.
  - Window #000000, dark text and accent. DWM reports `DWMWA_USE_IMMERSIVE_DARK_MODE` = 1 for dark
    and black, 0 for light. On this machine the title bar shows the red accent anyway, because
    *Settings ▸ Personalisation ▸ Colours ▸ Show accent colour on title bars* is on: Windows'
    choice, same as other apps. Screenshots: `WINDOWS_SCREENSHOTS/theme-*.png`.
- [x] **Your own colours.** *Options ▸ General* has *Primary colour* (buttons, check boxes, tabs,
  accents), *Secondary colour* (links in notes and in the program), *Highlight colour* (selected text
  and find matches) and *Text colour*. Pick each, press Apply: everything follows at once. *Use the
  theme's colour* puts each back. Check in light, dark and black, and with a non-blue Windows accent
  (the primary colour overrides it; without one, Windows' accent is used as before).
  - Green primary, purple secondary, amber highlight, blue text: all follow at once in light, dark
    and black (buttons, tabs, fold tabs, links, find matches, all text). Reset: back to Windows'
    red accent (#d20e1e light, #f46762 dark/black). `WINDOWS_SCREENSHOTS/colours-*.png`.
- [x] **Folding panels.** The note list and the links panel each have a small tab near the bottom
  of their edge: click it to fold the panel away and back; drag the edge to resize; double-click the
  edge folds it. *View ▸ Note List* (Ctrl+Shift+L) and *View ▸ Links Panel* (Ctrl+Shift+K) do the
  same; the state survives a restart. Check that no IME or Windows shortcut takes Ctrl+Shift+L/K.
  Check it in Arabic too (right to left: the tabs and chevrons mirror).
  - Fold and unfold work; state survives a restart. Ctrl+Shift+L and Ctrl+Shift+K sent as **real
    key presses through Windows** reached the app and folded each panel (no system or IME hotkey
    took them, with the pt-BR keyboard). Arabic: layout and tabs mirror.
    `WINDOWS_SCREENSHOTS/folds-*.png`.
- [x] **Icons follow a live theme switch.** Switch light → dark → black → light while the app runs
  (and with *Use system setting*, switch Windows itself): every icon, Segoe glyphs included, takes
  the new colours at once. Before, they kept the old theme's colour.
  - Nav-rail icon colour read from the pixels after each switch: #1b1b1b → #f3f3f3 → #f3f3f3 →
    #1b1b1b, always the theme's text colour. (Switching Windows itself was not tried.)
  - **Bug found and fixed:** the message strip ("Mind map exported", "Graph image saved"…) kept
    the old theme's colours when the theme changed while it was showing (a white strip in a dark
    window). It is now restyled with the rest. (`0a64616`)
- [x] **Find bar Tab order.** Ctrl+H in a note: Tab from the search goes straight to *Replace with*,
  then *Replace*, *Replace all*, then the search's own buttons.
  - Exactly that: Replace with › Replace › Replace all › Match case › Previous › Next › Replace.
- [x] **Alt+Shift+click for extra carets.** Alt+click still adds a caret; Alt+Shift+click does too,
  and again removes it. Note whether the Windows Alt+Shift keyboard-layout hotkey also switches the
  layout when it is enabled.
  - Both add a caret. With **real** Left Alt+Shift and a real click sent through Windows, on this
    machine with two input languages (pt-BR, en-US, so Alt+Shift is the live language hotkey): the
    caret was added and the **keyboard layout did not change** (f0100416 before and after).
  - **Bug found and fixed:** "again removes it" failed right after adding, because the click spot
    is then the main caret, which wasn't removable. Alt(+Shift)+click on the main caret now
    removes it and the last added caret leads. (`43e2b7f`)
- [x] **Help ▸ Donate** now has its own access key (Alt+H, O in English), no longer sharing D with
  *Documentation*.
  - Yes in English. **Bug found and fixed:** checking every menu in every language found letters
    used twice in a menu: 2 in English (*Cu&t* / *Move Note to &Trash*, *Link to a &File* /
    *&Flashcard*), 3 to 12 in each translation, and the Arabic strings carried two access keys
    each (an Arabic one and a Latin "(&X)" that Qt ignores). The window now moves a clashing key to
    a free letter, the catalogs were fixed the same way, English uses *&Move Note to Trash* and
    *Link to a Fil&e*, Arabic keeps one key per item. 0 clashes left in all 11 languages; a test
    keeps it so. (`5466c9d`)

## 3. Shared code changed for Linux: check Windows is unchanged

- [x] **Icons still come from Segoe Fluent Icons** (`zettelapp/ui/icons.py` gained native and
  bundled-SVG fallbacks for Linux): nav rail, toolbar and the Bold/Italic letters look as in 1.3.1.
  - Same as 1.3.1: `tools/screenshots.py` was run on tag v1.3.1 and on this branch and compared;
    the icons are identical. Intended differences only: the note list ordered by closeness to the
    open note, and the fold tabs on the panel edges.
- [x] **Accent colour.** With a non-blue Windows accent, the app takes it, light and dark
  (`zettelapp/ui/theme.py` was reworked).
  - Red accent taken: #d20e1e light, #f46762 dark and black.
- [x] **Mind map link marker** (now drawn through `icons.paint`): link an idea to a note; the chain
  still shows at the idea's right end, in the text colour, light and dark.
  - Yes, light and dark, in the app and in the PNG/SVG exports. `WINDOWS_SCREENSHOTS/mindmap-link-*.png`.
- [x] **Graph and mind map export to PNG/SVG** (now one shared helper): *Save graph as image* and
  the mind map's PNG and SVG export look as before.
  - All three export and look right.
- [x] **Graphviz export:** the `.dot` file still says `fontname="Segoe UI"`.
  - Yes (graph, node and edge).
- [x] **API keys** in Windows Credential Manager (`zettelapp/core/secrets.py` changed): save, read
  and delete a key in *Options ▸ AI assistant*; the key hint and "Key … saved on this computer."
  read as before.
  - Saved, read back and deleted through `core.secrets` with a throwaway name; `cmdkey /list` no
    longer shows it after the delete. The Options page wording was not looked at by eye.
- [x] **MCP switch:** with the status-bar switch on, an MCP client can call tools; switched off or
  with ZettelApp closed, it is refused.
  - With the **packaged** `zettelapp-mcp.exe`: switch on → `tools/list` answers; switch off → the
    server refuses ("ZettelApp is closed or its MCP switch is off…") and exits 1. Another process
    sees the switch state.
- [x] **Update notice** (`download_url()` changed): installed copy → *Download* opens the
  `ZettelApp-Setup.exe` link; portable zip → the release page.
  - Installed (an `unins000.exe` beside the exe) → `…/releases/latest/download/ZettelApp-Setup.exe`;
    portable → `…/releases/latest`.
- [x] **Single instance:** a second launch and a `zettelapp://note/<id>` link from Anki bring the
  running window forward.
  - From source and installed: the second launch with a link hands it over and quits in ~0.55 s;
    the first window comes back from minimised. From source it also came to the front; installed,
    Windows kept it behind because the test launcher was itself in the background (Windows only
    lets a foreground app pass the foreground on; Anki is in the foreground when you click a
    link). **Needs a person:** click a `zettelapp://` link in Anki once.
  - **Bug found and fixed:** a maximised window came back un-maximised (the restore used
    `showNormal()`); it now keeps its state, for links and for alarms. (`78025ba`)
- [x] **File dialogs reopen the last folder:** *Insert ▸ Image…*, *Insert ▸ Link to a File…*, the
  mind map export and *Save graph as image* open the folder used last (also after a restart), never
  ZettelApp's install folder.
  - **Bug found and fixed.** On Windows the helper left the folder to the system, and the native
    dialog (folder read from its address bar) opened the **working folder** — for the Start-menu
    shortcut, the install folder. Real evidence on this machine: a `Verbos Latinos.png` had been
    saved into `%LOCALAPPDATA%\Programs\ZettelApp\`. Windows now remembers the folder like Linux
    (Documents the first time), the Linux test runs on Windows too, plus a new one. (`43e2b7f`)
- [x] **Alarms:** set an alarm, let it fire with ZettelApp minimised. Describe what the user sees
  and hears (toast, sound, window), and whether clicking the toast opens the note and un-maximises a
  maximised window. Linux now uses the desktop's notifications with an *Open note* button.
  - With the window minimised, the alarm fires through `QSystemTrayIcon.showMessage` (tray
    available) and the in-app strip shows "Alarm: …". What a click does (`_open_alarm_note`):
    opens the note and brings the window back — **un-maximised before the fix above, maximised
    now**. **Needs a person:** what the toast looks and sounds like (Focus Assist and notification
    settings decide); the screen grab missed it.
- [x] **Note list snippets** keep underscores inside words: a note starting with
  `supported_by:: [[X]]` shows that, not `supportedby::`.
  - Shows `supported_by:: X …`.
- [x] **Checklists:** clicking a box in the preview ticks it, and Ctrl+Z undoes it (the code was
  shared with the core).
  - Ticks; Ctrl+Z undoes one box at a time. The existing test now also checks the undo.

## 4. Docs and website

The docs were corrected in all 11 languages (file manager wording, missing passages, English labels
left in translations), and gained the themes and colours. Skim `docs/getting-started.md` and the
rebuilt `website/` in one or two languages you read, and report anything wrong for Windows.

- [x] Rebuilt site unchanged. Portuguese and English *Getting started* are right for Windows.
  One thing for the **Linux** side, in every language: the `.deb` row says the software centre
  "then offers updates". A `.deb` installed from a file has no repository, so nothing offers
  updates (the app's own update notice does). Suggest dropping that clause.

## 5. Numbers and data only Windows can give

- [x] **Startup and a big vault.** Linux (VM, 2 CPUs, from source): warm start 1.3 s, cold 7.6 s;
  a 10,000-note vault lists and searches in 0.3-1.8 s. Time the same on Windows (installed build and
  from source) so the Linux numbers can be judged.
  - Start-up to window: from source 2.9 s, warm 1.9 s; installed 2.3 s, warm 1.75 s. (A truly
    cold start, after a reboot, was not measured.)
  - 10,000 notes (40-160 words each, from source): open the vault and list it 8.0 s (includes
    building the meaning index for the default order); list again 1.3-1.7 s; search 0.3-2.1 s
    (`zzznothing` 0.26 s, `tag:latin declension` 0.50 s, `memory` 1.35 s, `latin grammar` 2.12 s);
    open a note with link suggestions 3.1 s.
- [x] **Fresh reference screenshots:** `python tools/screenshots.py` on this branch, commit the 18
  images in `website/assets/screenshots/` (the current ones predate 1.3.1). Then once more with
  `QT_SCALE_FACTOR=1.5` into `WINDOWS_SCREENSHOTS/150/`, for comparing HiDPI.
  - Done, both. **Bug found and fixed:** the tool crashed on Windows: forcing the default blue
    replaced every `*_accent` function in `theme`, including `_with_accent`, which builds the theme.
- [x] **A vault made on Windows,** zipped as on disk (`zettel.db` plus `assets`), with pictures,
  attachments, typed links, flashcards with review history and a link to a `C:\...` file. Commit it
  as `WINDOWS_SCREENSHOTS/windows-vault.zip`; Linux checks that it opens and shows the `C:\` link as
  unavailable.
  - `WINDOWS_SCREENSHOTS/windows-vault.zip`: two pictures (one the title image), a table cloze, a
    checklist, a mind map with linked ideas, a custom *Discusses* type written as `discussed_by::`,
    `supports::`, a flashcard with three reviews, and links to `C:\Windows\win.ini` (as a Markdown
    link and as `file:///C:/…`).

## Not part of this round

GNOME and KDE Wayland sessions are not being tested. Flatpak and Snap are being done separately on
Linux (`FLATPAK_SNAP_WAYLAND_GUIDE.md` on the Linux desktop).

## After everything passes (done on Linux)

Version 1.4.0: `zettelapp/__init__.py`, `packaging/installer.iss`, a `<release>` in
`packaging/io.github.dutrairs.zettelapp.metainfo.xml`, the CHANGELOG heading, `website/version.json`
(by `tools/build_site.py`); delete this file and `WINDOWS_SCREENSHOTS/`; tag and release.
