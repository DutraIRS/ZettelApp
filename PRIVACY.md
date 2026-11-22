# Privacy

**ZettelApp makes one network request on its own: a check for a new version. Everything else stays
on your computer unless you use a feature that needs the internet.**

There are no accounts, no telemetry, no analytics, no ads and no crash reports. Notes are never
uploaded anywhere by the app.

## The one automatic request

About 4 seconds after ZettelApp starts, it downloads
`https://dutrairs.github.io/ZettelApp/version.json` to see whether a newer version exists. The
request carries only the header `User-Agent: ZettelApp/<version>`: no notes, settings, identifiers or
usage data. Failures are silent.

Turn it off in *Tools ▸ Options ▸ General ▸ Check for updates when ZettelApp starts*. Then the app
makes no request at all unless you use one of the features below.

## Requests only when you ask for them

| You… | ZettelApp contacts | What is sent |
|---|---|---|
| ask a question on the **Ask** page, or test the AI connection | the AI provider you configured yourself (Anthropic, OpenAI, Z.ai or your own endpoint) | your question and the notes listed under *Sources sent*, or just your API key for a test |
| click **Download model** for semantic search | `huggingface.co` | requests for the model files; nothing about your notes |
| **Sync to Anki** or search **Zotero** | Anki and Zotero on **this computer** (`127.0.0.1`), never the internet | the flashcards, or your search words |
| click a web link or a *Help* menu item | your web browser opens the page | nothing from ZettelApp |

The AI assistant is off until you add an API key and confirm what it sends. The MCP server, for AI
apps on your own computer, makes no network requests.

## Where your data lives

Your notes are a SQLite file in your vault folder (by default *Documents/ZettelApp*). API keys are
kept in the system keyring (Windows Credential Manager, or GNOME Keyring / KWallet on Linux), never
in files. On Android, the vault lives in the app's private storage.

The full details, including every folder the app writes to and how untrusted content is handled,
are in [Privacy and security](docs/privacy-and-security.md).
