# Checks to do on Windows, GNOME and KDE

Everything in ZettelApp that only a person at a real desktop can confirm, in one place, so each
platform session can be done start to finish without asking what to look at. It is kept up to date
with every change that touches the interface, theming, files, notifications or packaging. Items
belong to the next release, **1.4.0**; once it ships, the checked items are removed.

Last updated: 24 November 2026 (the window's top row on Windows; earlier: Reading view, preview spacing, the adventure card, live accent,
Dolphin, plus everything the earlier Windows, GNOME and KDE passes could not reach).

## How to work through it

- Branch **`desktop-aesthetics`** (pull it first). Don't touch the `android/` folder.
- Run from source unless an item says otherwise: `.venv\Scripts\python -m zettelapp` on Windows,
  `.venv/bin/python -m zettelapp` on Linux. Use a throwaway vault (*File ▸ New Vault…*), not your
  own notes.
- GNOME and KDE mean a **Wayland** session on Debian 13 (Ubuntu 24.04 where an item says so).
- Under each platform box, write the result: "as described", what you saw instead, or a screenshot
  path. Tick the box (`[x]`) once it is checked, even if it failed: the result says how it went.
- A bug found: fix it with a test and a CHANGELOG line, or describe it under the item.

A note for the spacing and reading checks (paste it into a new note):

```markdown
# The missing prince

Zettelkasten is a method of note-taking in which each note holds one idea and links to others. The
links matter more than the folders: they let ideas meet that were written months apart.

A second paragraph, long enough to wrap onto a second line so the line height shows.

## What to write

- One idea per note, in your own words.
- A reason for every link, like supports or contradicts.

1. Read the source.
2. Write the note.

> A quotation stands apart from the text around it.

| Column | Other |
| --- | --- |
| a | b |

    some code

### Checklist

- [ ] Find the prince
- [x] Meet Quill

$$e^{i\pi} + 1 = 0$$
```

Then add a picture (*Insert ▸ Image…*) between the two first paragraphs.

## 1. On all three desktops

### 1.1 Reading view and the text's fold tab (new)

The editor's three modes are now **Edit**, **Split view** and **Reading view** (the third button,
the page icon; Ctrl+E cycles). Check, with the note above:

- Reading view shows the preview alone as a **centred column** (about 70 letters wide) at the
  **same text size as the editor**; on a narrow window the column fills the width with a margin.
- The **title and the source link can't be edited** (click and type: nothing changes); an empty
  source link is **hidden**; the formatting buttons are greyed.
- A **tab between the text and the preview** (accent colour, chevron, grip dots) folds the text away
  and brings it back. It sits at **exactly the same height as the note list's and the links
  panel's tabs**; in Reading view it sits just right of the note list's tab. Dragging it resizes
  the text; double-clicking the thin strip under it folds too. In Edit mode it is gone.
- The mode survives a **restart**. A **new note** (Ctrl+N) opens in Split view to be written, and
  the next start is still in Reading view if that was chosen.
- In **Arabic** (*Options ▸ General ▸ Language*) everything mirrors: the text pane is on the
  right, the tab's chevron points the other way.
- At **150 % scaling**, nothing is cut and the three tabs still line up.

- [x] Windows: as described, driven on the Windows platform in English, Arabic, Japanese and
  Chinese, light and dark, 100 % and 150 %. The three tabs share one height (y = 773 at 100 %,
  569 at 150 %); in Reading view the text's tab sits 32 px right of the note list's (mirrored in
  Arabic); the column is centred (120 px a side at 1440 px wide, 24 px when narrow); typing in
  the locked title changes nothing; no tab in Edit mode. Two fixes: *Editor text size* wasn't
  applied at start (the text was always 11 pt, the preview smaller), and after writing a new note
  the next note stayed in Split view instead of going back to Reading view. Both fixed with tests.
- [ ] GNOME
- [ ] KDE

### 1.2 Preview spacing (fixed)

With the note above in Split view and in Reading view: every block (paragraph, list, quote, code,
table, checklist, formula) leaves the **same space below it**; a heading has more space above than
below, so it sits with the text it introduces; list items are evenly spaced; **no large gap under
the picture**. Change *Options ▸ General ▸ Editor text size* (try 9 and 16): the preview follows.
Also look at a flashcard in *Review* and an answer in *Ask*: same spacing, nothing broken.

- [x] Windows: as described at 9, 11 and 16 pt; no gap under the picture. Lines were 150 % of
  Qt's line spacing (about twice the font size, which read as double-spaced); now 125 %. The
  website's screenshots were refreshed with it.
- [ ] GNOME
- [ ] KDE

### 1.3 The adventure card (changed)

*Help ▸ Start the Adventure* (or the offer on a fresh settings file). The story above each task is
in **justified paragraphs with a gap between them**: the prologue's three paragraphs, a chapter's
story, a clue, the finale. Check in English, Arabic (justified right to left) and Japanese or
Chinese (no odd stretching), at 100 % and 150 %, light and dark. Nothing cut at the card's bottom.

- [x] Windows: as described in English and Arabic. Chinese showed odd stretching: Qt justifies
  at spaces only, so the gaps around Latin words ("Ask", "AI") went wide. Chinese and Japanese
  are now aligned to the start (fixed with a test).
- [ ] GNOME
- [ ] KDE

### 1.4 Accent colour followed live (new)

With *View ▸ Theme ▸ Use System Setting* (and once with *Dark*): change the desktop's accent colour
while ZettelApp runs. Within a second the app takes it: the **New** button, the fold tabs, the
selected note, the tabs' underline, check boxes; shaded lighter in dark. Change it back: it
follows again. With a primary colour of your own set in *Options ▸ General*, a desktop change does
**not** override it.

- Windows: *Settings ▸ Personalisation ▸ Colours ▸ Accent colour* (try both "Manual" and
  "Automatic" from the wallpaper).
- GNOME 47 or later: *Settings ▸ Appearance ▸ Accent colour*.
- KDE Plasma 6: *System Settings ▸ Colours & Themes ▸ Colours ▸ Accent colour* (a custom colour,
  then "From wallpaper").

- [x] Windows: as described with *Use System Setting* and *Dark*. The accent was switched the
  way Settings does it (the `Explorer\Accent` palette and the `ImmersiveColorSet` broadcast):
  red → green → purple followed within a second; with an own primary colour (#ff8800) a desktop
  change left it alone. The desktop's values were restored afterwards.
- [ ] GNOME
- [ ] KDE

### 1.5 Dark and light followed live, both ways

With *Use System Setting*, switch the desktop from **dark to light** and back while ZettelApp runs.
Fixed on every OS by the KDE pass (the switch to light was missed): the whole window changes,
icons included, in both directions, also with a message strip showing (export a mind map just
before switching). The earlier Windows pass never switched Windows itself.

- [x] Windows (*Settings ▸ Personalisation ▸ Colours ▸ Choose your mode*): as described, dark →
  light → dark with a message strip showing; window, icons and strip all switched each way.
- [ ] GNOME (re-check after this round's changes)
- [ ] KDE (re-check after this round's changes)

### 1.6 The window's top row (new)

On **Windows**, the app's icon, the menus, the window's title (muted, centred) and the minimise,
maximise and close buttons share one row in the theme's sidebar colour, instead of Windows'
title bar above the menu bar. With the rail at the left it forms one L around the page. The window
still drags by the empty row (double-click maximises), snaps (drag to an edge, Win+arrows),
resizes from every edge and corner, keeps its shadow and rounded corners, and maximises to the
screen's free area. Close turns red on hover. In Arabic the row is mirrored: buttons at the left,
all six menus at the right.

On **GNOME and KDE** nothing changes: the desktop's own title bar, Qt's menu bar under it.

- [x] Windows (11, 125 % scaling, from source): as described in light, dark and black. Windows'
  own `WM_NCHITTEST` answers: caption over the empty row, the title and the icon; client over the
  menus and the three buttons; the matching edge or corner at each side. Maximised, the client area
  equals the work area exactly (1920 × 1020) and the button reads "Restore Down". Win+Left snapped
  it to the left at full height. Close's red hover and the Arabic row were checked on screen; the
  row's menus had shrunk to the » button right to left (a Qt quirk), fixed with a test.
- [ ] GNOME: the desktop's own title bar and Qt's menu bar, as before.
- [ ] KDE: the desktop's own title bar and Qt's menu bar, as before.

## 2. Windows only

- [x] **Tests and lint**: `.venv\Scripts\python -m pytest` all passing (Linux: 545 passed,
  14 skipped; Windows skips the Linux-only ones), `ruff check .`, `ruff format --check .`,
  `python tools/i18n.py check` (1030/1030 in every language). *Windows: 490 passed, 70 skipped;
  ruff clean; 1027/1027 in all ten languages.*
- [x] **Microsoft Store package** (`dist/ZettelApp.msix`, built with a test signature (since removed) to
  install it locally): installs and starts from the Start menu with its logo; *Options ▸ Desktop
  integration* offers no link registration (the manifest registers `zettelapp://`), and a
  `zettelapp://note/<id>` link opens the note; no update notice at start; *Options ▸ MCP* points
  Claude Desktop at the `zettelapp-mcp.exe` alias and a client can call tools with the switch on;
  this round's items in section 1 also work in the package. Uninstall leaves the vault.
  *Windows, 23 November (package built from b445927, test-signed): starts from the Start menu
  with its logo in the taskbar; inside the package `is_packaged()` is true, Desktop integration
  says "Registered by the ZettelApp package.", no update request is made, Claude Desktop is
  pointed at the alias; `zettelapp://note/<id>` opened the note in the running package with no
  app chooser; through the alias an MCP client initialised, listed the six tools and searched
  with the switch on, and was refused with the switch off; the editor text size applied at start;
  uninstalling removed the package and alias and left the vault untouched.*
- [x] **Alarm toast click** with the window maximised and then minimised: the note opens and
  the window comes back maximised (the toast's look was confirmed; the click after the fix was
  not watched). **Fails on Windows 11**: with the built `ZettelApp.exe`, clicking the toast
  shows the desktop (every window minimised) instead of the note; seen by the user and twice in
  the scripted run. The toast itself appears ("ZettelApp", title, note text). To investigate
  before 1.4.0: the app shows the alarm through `QSystemTrayIcon.showMessage` (a legacy balloon
  Windows turns into a toast). **Fixed**: Windows never handed that click to the app. Alarms
  are now a Windows reminder toast (icon, title, text, "ZettelApp · Alarm", Open note and
  Dismiss) that opens the note's `zettelapp://` link. Checked from source: a click on the toast
  with the window maximised and behind another window, and Open note with it minimised, both
  opened the note with the window maximised and in front.
- [x] **Options ▸ AI assistant** wording, by eye: save a key, read the hint ("Key … saved on this
  computer."), delete it. *Windows: "Key “Platform check” saved on this computer.", read back
  from Credential Manager, then "… deleted from this computer." and gone from `cmdkey /list`.*
- [x] **Show in folder** (*Export* result, a `file:///` link in a note): Explorer opens with the
  file selected, as before (Linux-only code changed; Windows should be unchanged). *Windows: both
  routes opened Explorer on the folder with the file selected (read back from the Shell).*

## 3. GNOME only

- [ ] **Alarm notification**: set an alarm a minute ahead. The banner appears with ZettelApp's
  name and icon (the GNOME pass saw "No notifications" and never confirmed it). Click **Open
  note**: the note opens and the window **comes to the front** (activation token, unit-tested,
  never seen on screen).
- [ ] **Second launch from the overview** (Super, type ZettelApp, Enter) with ZettelApp already
  open: the running window comes to the front; no second window.
- [ ] **Fractional scaling**: *Settings ▸ Displays ▸ Scale* 125 %, 150 %, 200 % (turn on
  fractional scaling first if offered): text sharp, icons sharp, the three fold tabs aligned,
  nothing cut in Options, the adventure card or the Ask page.
- [ ] **Input methods**: with IBus and a Japanese or Chinese input method (*Settings ▸ Keyboard ▸
  Input Sources*), type in a note title, the note text and the search box; the candidate window
  sits at the caret. Also a dead key or Compose (é, ñ).
- [ ] **Orca** (Super+Alt+S): it reads the nav rail buttons, the toolbar buttons' names, the fold
  tabs ("Hide the note list…", "Hide the text and read the note…"), the note list and the
  editor text.
- [ ] **A stock GNOME look**: the test VM had Xfce leftovers in gsettings (Tango icons, "Sans 10").
  On a clean GNOME (Adwaita, Cantarell) or Ubuntu's Yaru: icons, font and spacing look right.
- [ ] **Ubuntu 24.04**: the `.deb` (`packaging/build-linux.sh`, then `sudo apt install ./…deb`)
  installs and starts from the app grid with its icon; API keys go to GNOME Keyring.

## 4. KDE Plasma only

- [ ] **Show in folder prefers Dolphin (new)**: with Dolphin as the default file manager and
  Nautilus (or Thunar) also installed, **no file manager running**: *Show in folder* after an
  export, and a `file:///` link in a note, open **Dolphin with the file selected** (before, D-Bus
  could start Nautilus). Make Nautilus the default (*System Settings ▸ Default Applications ▸ File
  manager*): then it goes to Nautilus.
- [ ] **KWallet as the Secret Service**: on a Plasma session where `kwalletd6` provides
  `org.freedesktop.secrets` (not GNOME Keyring, as on the test VM): save, read and delete an API
  key in *Options ▸ AI assistant*; KWallet's first-run dialog appears once.
- [ ] **Alarm notification click**: the notification appears (seen before); click **Open note**:
  the note opens and the window comes to the front.
- [ ] **Second launch from KRunner or the launcher** with ZettelApp open: the window comes to the
  front (a terminal launch only marks it "demands attention", which is correct).
- [ ] **Drag and drop from Dolphin** into a note: a picture is stored and inserted; another file
  becomes a file link.
- [ ] **Paste a picture on real Plasma hardware**: Spectacle (Print), copy, Ctrl+V in a note. On the
  VM, Klipper served every image empty; on real hardware it should paste. If it fails, the app
  says "The image on the clipboard could not be read…".
- [ ] **Fractional scaling** (*System Settings ▸ Display ▸ Scale* 125 %, 150 %, 200 %), **input
  methods** (Fcitx 5 with a Japanese or Chinese engine) and **Orca**: as for GNOME above.

## 5. Flatpak and Snap (when built)

The same app in a sandbox reaches the desktop through portals. On GNOME and KDE, in the Flatpak
and the Snap:

- [ ] Starts with its icon; dark/light and the accent at start and live (1.4, 1.5).
- [ ] *Show in folder* selects the file (Dolphin isn't visible inside the sandbox, so KDE uses
  D-Bus there).
- [ ] An API key is kept between starts (Secret portal or keyring).
- [ ] An alarm notification shows and its click opens the note.
- [ ] File dialogs are the desktop's own and can reach `~/Documents`.

## Already confirmed (no need to repeat)

Windows (23 November 2026): the OLED theme, own colours, folding side panels, icons on theme
switch, find bar order, extra carets, access keys, icons and fonts as in 1.3.1, the Windows accent
at start, mind map and graph exports, Credential Manager, MCP switch, update link, single instance,
file dialogs' folder, snippets, checklists, packaging, start-up times, `zettelapp://` links
clicked in Anki, the alarm toast's look ("ZettelApp", the title, "Time for this note."), a
Windows vault (opens on
Linux: pictures, typed links, flashcards; the `C:\` links show greyed out as unavailable).
GNOME and KDE (23 November 2026): native Wayland, app id and icon, dark at start, Show in folder
(Nautilus; Dolphin when it owns the name), drag and drop and screenshot paste on GNOME, menus and
the desktops' own file dialogs, KDE's notification, a second launch from a terminal.

## At the 1.4.0 release (done on Linux)

Version 1.4.0 in `zettelapp/__init__.py`, `packaging/installer.iss`, a `<release>` in
`packaging/io.github.dutrairs.zettelapp.metainfo.xml`, the CHANGELOG heading, `website/version.json`
(by `tools/build_site.py`); delete `WINDOWS_SCREENSHOTS/` (the Windows pass's evidence; its
results are summarised above) and the checked items here; tag and release.
