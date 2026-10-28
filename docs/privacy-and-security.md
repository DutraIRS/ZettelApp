# Privacy and security

## What leaves your computer

**Nothing, unless you ask for it.** ZettelApp has no accounts, telemetry, ads or automatic updates, and it
doesn't load anything from the internet while you work. Network use happens only when you trigger
it:

| When you… | ZettelApp contacts | What is sent |
|---|---|---|
| Ask a question on the **Ask** page | The AI provider you configured (Anthropic, OpenAI, Z.ai or your own endpoint) | Your question and the notes listed under *Sources sent* |
| Test the AI connection or refresh the model list | The same provider | Your API key, to authenticate |
| **Sync to Anki** | AnkiConnect on **this computer** (`127.0.0.1`) | The flashcards in the chosen scope |
| Use **Insert ▸ Zotero Reference** | Zotero on **this computer** (`127.0.0.1`) | Your search words (read-only) |
| Click a web link, or use *Help ▸ Website / Documentation / Check for Updates* | Your web browser opens the page | Nothing from ZettelApp |

Local connections to Anki and Zotero never use a proxy, so they can't be redirected off your computer.

## Where your data lives

| What | Where |
|---|---|
| Notes, links, flashcards, review history | Your vault folder: `zettel.db` (SQLite). By default **Documents\ZettelApp**. |
| Images | The vault's `assets` folder. |
| Preferences | The registry, under `HKEY_CURRENT_USER\Software\ZettelApp\ZettelApp`. |
| API keys | **Windows Credential Manager** (`ZettelApp/llm/…`), never in files or the registry. |
| Logs | `%LOCALAPPDATA%\ZettelApp\Logs` (rotated, at most a few MB). They record errors, not your notes, and never include API keys. |
| Automatic backups | `%LOCALAPPDATA%\ZettelApp\Backups` |
| Small UI cache | `%LOCALAPPDATA%\ZettelApp\Cache` |

The vault is an ordinary folder: you can copy it, back it up or keep it in OneDrive. ZettelApp writes the
database with full synchronisation, a setting chosen to suit synced folders. Avoid opening the same vault on two
computers at the same time.

## Backups and undo

- **Daily backups:** the first time a vault is opened each day, a consistent copy of its database is
  saved. The newest 10 are kept (*Options ▸ Backups*). *File ▸ Back Up Vault Now* makes one any time.
  Images are stored by content and never deleted automatically.
- **Trash:** deleted notes go to the Trash first, and can be restored until you empty it.
- **Autosave:** notes save as you type. A crash dialog reports unexpected errors and writes details to the
  log.

## How ZettelApp protects you

Notes can come from imports, the web or AI answers, so ZettelApp treats their contents as untrusted:

- **No active content.** Raw HTML in notes is shown as text, never rendered; nothing in a note can run
  scripts. The note preview loads images **only from the vault's own `assets` folder**, never from the
  web or elsewhere on disk.
- **Link allowlist.** Clicking a link opens only web pages (`http`/`https`), e-mail (`mailto`), notes, and
  Zotero *select item* / *open PDF* links. `javascript:`, `file:` and other schemes are refused.
- **Images are verified by content**, not by file name. Only PNG, JPEG, GIF, WebP and BMP up to 25 MB are
  accepted; SVG is refused because it can carry scripts. Verification covers the file signature and
  compressed size; pixel dimensions are checked when the image is first displayed.
- **Safe imports.** Archives are checked for path tricks ("zip-slip") and decompression bombs. Every field
  is validated and size-limited, Markdown imports can't reach outside the imported folder, and a failed
  import leaves the vault unchanged: imports run in a single database transaction that is rolled back on
  any error.
- **Safe exports.** Exported websites contain no scripts and carry a strict Content-Security-Policy. Files
  are written atomically.
- **Database safety.** All database queries use bound parameters, and search text is never interpreted as
  query syntax.
- **`zettelapp://` links** (used by Anki cards) can only *open a note by its ID*. Any other request is
  ignored.
- **Single instance per user.** A second launch hands its request to the running app through a Windows
  named pipe that only your user account can access.
- **AI safety.** The AI model gets no tools, so instructions hidden in a note can't make it act, and its
  answer is rendered with the same safe renderer. API keys stay in Credential Manager and are removed from
  error messages.
- **MCP server.** It is read-only by default and runs only when your MCP client starts it, over standard
  input/output with no network port. See [MCP server](mcp-server.md).

Found a security problem? Please report it privately; see
[SECURITY.md](https://github.com/DutraIRS/ZettelApp/blob/main/SECURITY.md).
