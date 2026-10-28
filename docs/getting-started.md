# Getting started

## Install

ZettelApp runs on **Windows 10 (21H2 or later) and Windows 11, 64-bit**. Download it from the
[latest release](https://github.com/DutraIRS/ZettelApp/releases/latest):

| Download | Use it when |
|---|---|
| `ZettelApp-Setup.exe` | You want a normal installation with a Start menu entry, an uninstaller in *Settings ▸ Apps*, and `zettelapp://` links that open notes from Anki. No administrator rights are needed: it installs for your account only. |
| `ZettelApp-Portable.zip` | You can't install software, or you want to run it from a USB drive. Unzip it anywhere and run `ZettelApp.exe`. |

The installer asks which language to use and suggests your Windows display language. The installer
itself is translated; the app is in English for now (see the [roadmap](https://github.com/DutraIRS/ZettelApp/blob/main/ROADMAP.md)).

Each release lists SHA-256 checksums (`SHA256SUMS.txt`). To check a download in PowerShell:

```powershell
Get-FileHash .\ZettelApp-Setup.exe -Algorithm SHA256
```

### "Windows protected your PC"

Builds are not code-signed yet, so Microsoft Defender SmartScreen may warn the first time you run the
installer. If you downloaded it from the official release page and the checksum matches, choose
**More info ▸ Run anyway**. Code signing is on the [roadmap](https://github.com/DutraIRS/ZettelApp/blob/main/ROADMAP.md).

## Your first vault

A **vault** is a folder holding your notes: a database file (`zettel.db`) and an `assets` folder for images.
On first start ZettelApp creates one in **Documents\ZettelApp** with eleven linked starter notes. The
*Welcome to ZettelApp* note leads through links, tags, images, mind maps, flashcards and the rest of the app. An
optional ten-minute adventure offers the same tour through real actions. New vaults created with
*File ▸ New Vault…* or *File ▸ Open Vault…* receive the same starter material, so you can work elsewhere,
for example in a OneDrive folder.
*File ▸ Open Recent* lists the vaults you used last.

Notes save automatically as you type. There is no Save button.

## A tour of the window

![The Notes page](../website/assets/screenshots/notes-light.png)

The **navigation rail** on the left switches between pages (Ctrl+1 to Ctrl+5):

- **Notes**: the note list, the editor and a side panel.
  - The *list* has search (`tag:name` filters work too), a tag filter, sorting and the Trash.
  - The *editor* has the title, tags, an optional source link, and tabs for the **Note** (Markdown, with
    Edit, Split and Preview modes), its **Mind map** and its **Flashcards**.
  - The *side panel* shows **Suggested links**, the note's **Links** and its **Backlinks**.
- **Graph**: your notes as a network in 2D or 3D, coloured by tag or by topic cluster.
- **Insights**: statistics and charts about your vault.
- **Review**: spaced-repetition reviews, quizzes and Anki.
- **Ask**: ask questions about your notes using an AI provider of your choice (optional).

**Options** (bottom of the rail, or *Tools ▸ Options…*, Ctrl+,) holds the preferences: theme, editor text
size, link suggestions, link types, AI, MCP server, Anki, Zotero, Windows integration and backups.

The app follows your Windows **light/dark** setting and **accent colour**. You can force a theme in
*View ▸ Theme*.

## Updates

About four seconds after it starts, ZettelApp makes one HTTPS request to
`https://dutrairs.github.io/ZettelApp/version.json` to learn the newest version. It sends nothing else
(only a `ZettelApp/<version>` user-agent), and if the request fails you won't see anything. When a newer
version exists, a small notice appears in the lower-right corner, at most once per version. It never
takes focus. **Download** opens the releases page in your browser, **✕** closes the notice, and
**Don't check for updates** turns checking off. You can turn it back on in
*Tools ▸ Options ▸ General ▸ Check for updates when ZettelApp starts*. ZettelApp never installs
anything by itself.

## Uninstalling

Use *Windows Settings ▸ Apps ▸ Installed apps ▸ ZettelApp ▸ Uninstall*. After you confirm, a dialog offers
an unticked **Also delete my ZettelApp settings and data** option. It removes your settings, saved API
keys, logs, cache and automatic backups (`%LOCALAPPDATA%\ZettelApp`). Your notes are never deleted:
vault folders such as `Documents\ZettelApp` stay. For the portable version, delete its folder.

## Next steps

- Learn the note syntax in [Notes and links](notes-and-links.md).
- Read how [link suggestions](link-suggestions.md) work.
- Press **F1** at any time to open this documentation, or see the [keyboard shortcuts](keyboard-shortcuts.md).
