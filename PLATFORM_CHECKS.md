# Checks to do on Windows, GNOME, KDE and Xfce

Everything in ZettelApp that only a person at a real desktop can confirm, in one place, so each
platform session can be done start to finish without asking what to look at. It is kept up to date
with every change that touches the interface, theming, files, notifications or packaging. Items
belong to the next release; once it ships, the checked items are removed.

Last updated: 25 November 2026, at the 1.5.0 release: what's left is what the Windows, GNOME, KDE
and Xfce passes could not reach (real hardware, a person at the screen, the sandboxed packages).

## How to work through it

- Branch **`desktop-aesthetics`** (pull it first). Don't touch the `android/` folder.
- Run from source unless an item says otherwise: `.venv\Scripts\python -m zettelapp` on Windows,
  `.venv/bin/python -m zettelapp` on Linux. Use a throwaway vault (*File ▸ New Vault…*), not your
  own notes.
- GNOME and KDE mean a **Wayland** session on Debian 13 (Ubuntu 24.04 where an item says so);
  Xfce means an **X11** session on Debian 13.
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

## 3. GNOME only

- [ ] **Alarm notification**: set an alarm a minute ahead. The banner appears with ZettelApp's
  name and icon (the GNOME pass saw "No notifications" and never confirmed it). Click **Open
  note**: the note opens and the window **comes to the front** (activation token, unit-tested,
  never seen on screen).
  *GNOME, 25 November: the notification is sent through the desktop's notification service
  (it answers, so no tray fallback) and the in-app strip says "Alarm: …"; the banner and the
  click weren't seen (no screen capture or clicks on this Wayland VM without permissions). Since
  the KDE pass the notification also carries an **Open note** button on GNOME (section 4):
  look for it.*
- [ ] **Second launch from the overview** (Super, type ZettelApp, Enter) with ZettelApp already
  open: the running window comes to the front; no second window.
  *GNOME: a second launch from a terminal hands over and exits, one window. The overview launch
  needs a person at the keyboard.*
- [ ] **Input methods**: with IBus and a Japanese or Chinese input method (*Settings ▸ Keyboard ▸
  Input Sources*), type in a note title, the note text and the search box; the candidate window
  sits at the caret. Also a dead key or Compose (é, ñ).
  *Not tried: needs typing on a real keyboard.*
- [ ] **Orca** (Super+Alt+S): it reads the nav rail buttons, the toolbar buttons' names, the fold
  tabs ("Hide the note list…", "Hide the text and read the note…"), the note list and the
  editor text.
  *Not tried: needs a person listening.*
- [ ] **Ubuntu 24.04**: the `.deb` (`packaging/build-linux.sh`, then `sudo apt install ./…deb`)
  installs and starts from the app grid with its icon; API keys go to GNOME Keyring.
  *Not tried: no Ubuntu 24.04 machine. The `.deb` built on Debian 13 needs libc6 ≥ 2.39, which
  24.04 has.*

## 4. KDE Plasma only

- [ ] **KWallet as the Secret Service**: on a Plasma session where `kwalletd6` provides
  `org.freedesktop.secrets` (not GNOME Keyring, as on the test VM): save, read and delete an API
  key in *Options ▸ AI assistant*; KWallet's first-run dialog appears once.
  *Not on this VM: GNOME Keyring still owns `org.freedesktop.secrets` here. Save, read and
  delete through it work on Plasma.*
- [ ] **Alarm notification click**: the notification appears (seen before); click **Open note**:
  the note opens and the window comes to the front.
  *KDE: Plasma showed the banner with ZettelApp's icon, name, title and text, but **no Open note
  button**: the app sent its only action under the key `default`, which Plasma (and GNOME) make
  the click on the notification. Fixed with a test: Open note is now also sent under its own
  key, except to Xfce's service, which already drew `default` as a button. After the fix the
  banner shows **Open note** (desktop screenshot). The click itself wasn't made: no way to click
  from a script on this Wayland VM. GNOME and Xfce: look at the banner once more.*
- [ ] **Second launch from KRunner or the launcher** with ZettelApp open: the window comes to the
  front (a terminal launch only marks it "demands attention", which is correct).
  *Not tried: the installed `zettelapp` is 1.3.1, and the launcher needs a person. A second
  launch from a terminal hands over and exits, one window.*
- [ ] **Drag and drop from Dolphin** into a note: a picture is stored and inserted; another file
  becomes a file link.
  *Not tried: needs a person to drag.*
- [ ] **Fractional scaling** (*System Settings ▸ Display ▸ Scale* 125 %, 150 %, 200 %), **input
  methods** (Fcitx 5 with a Japanese or Chinese engine) and **Orca**: as for GNOME above.
  *KDE fractional scaling (`kscreen-doctor`, 1.25, 1.5 and 2): the app gets exactly those device
  pixel ratios, text and icons are sharp, the three tabs share one height, no sideways
  scrolling, nothing cut in Options. The VM's screen is 922 px high, so KWin maximised the window
  below its 640 px minimum at 1.5 (543 px; everything still usable) and at 2 (960 × 389, where
  the adventure card no longer fits); a 1080p screen at 150 % leaves about 680 px. Scale 1
  restored. Input methods and Orca not tried (they need a person).*

## 6. Flatpak and Snap (when built)

The same app in a sandbox reaches the desktop through portals. On GNOME and KDE, in the Flatpak
and the Snap:

- [ ] Starts with its icon; dark/light and the accent at start and live.
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
Windows, GNOME, KDE and Xfce (24–25 November 2026, for 1.5.0): the Reading view and the fold
tabs, preview spacing and options, the adventure card, the accent and dark/light followed live,
Windows' own top row, arrow tips, network measures, Ask's review, the rail and sort menu,
Diffusion, Obsidian folders, and the Xfce session as a whole (the results are in this file's
history).

## At a release

The version in `zettelapp/__init__.py`, `packaging/installer.iss`, a `<release>` in
`packaging/io.github.dutrairs.zettelapp.metainfo.xml`, the CHANGELOG heading, `website/version.json`
(by `tools/build_site.py`); delete `WINDOWS_SCREENSHOTS/` (a Windows pass's evidence, if any)
and the checked items here, summarised above; tag and release.
