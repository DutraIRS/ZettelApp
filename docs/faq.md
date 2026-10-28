# FAQ

### Is ZettelApp free?

Yes. It is free and open source, released into the public domain under
[The Unlicense](https://github.com/DutraIRS/ZettelApp/blob/main/LICENSE). The optional AI feature uses
your own API key, so the provider bills you directly.

### How can I support ZettelApp?

Thank you for asking! You can support development on [Ko-fi](https://ko-fi.com/dutrairs). Companies can
sponsor a specific [roadmap](https://github.com/DutraIRS/ZettelApp/blob/main/ROADMAP.md) item; get in
touch through [GitHub](https://github.com/DutraIRS/ZettelApp). Sponsors are thanked in the release notes.
Reporting bugs, improving the docs and sharing ZettelApp help too.

### Does it need the internet?

No. Everything works offline. The internet is used only for a small update check at start-up (which you
can turn off), when you ask a question on the **Ask** page, and when you open a link. See
[Privacy and security](privacy-and-security.md).

### Does ZettelApp check for updates?

Yes, once at start-up: one request for a small file on the project's website, with nothing about you or
your notes. If a newer version exists, a notice appears in the lower-right corner. Turn it off with
*Tools ▸ Options ▸ General ▸ Check for updates when ZettelApp starts*, or with **Don't check for updates**
on the notice. See [Getting started](getting-started.md#updates).

### What is the MCP switch in the status bar?

It lets AI assistants such as Claude Desktop or Claude Code use your notes through
[MCP](mcp-server.md). It is **off every time ZettelApp starts**. While it is off, or ZettelApp is closed,
assistants can't reach your notes. After you switch it on, reconnect ZettelApp in your MCP client (or
restart the client).

### Can I use a model on my own computer?

Yes. In *Tools ▸ Options ▸ AI assistant*, choose **OpenAI** and set **Endpoint** to your local server, for
example `http://localhost:11434/v1` (Ollama) or `http://localhost:1234/v1` (LM Studio). No API key is
needed for `localhost`. See [Bring your own LLM](ai-assistant.md#bring-your-own-llm).

### Where are my notes?

In your vault folder, by default **Documents\ZettelApp**: a `zettel.db` database and an `assets` folder.
*File ▸ Show Vault in File Explorer* opens it.

### Can I use it with OneDrive, Dropbox or Google Drive?

Yes. Put the vault in a synced folder (*File ▸ New Vault…*). Close ZettelApp on one computer before
opening the same vault on another, because two computers writing at once can conflict.

### How do I move to another computer?

Copy the vault folder, or use *File ▸ Export…* ▸ **ZettelApp archive** and import it on the other
computer.

### Can I use my Obsidian vault?

Yes. *File ▸ Import Markdown Folder…* imports Markdown files with their front matter, `#tags`,
`[[links]]` and images. Your Obsidian files are not changed. Going the other way, export to **Markdown
files** and open the folder in Obsidian.

### Why "Zettel" IDs like 20261027153012?

Each note gets a permanent ID from the time it was created (year, month, day, hour, minute, second).
Titles can change; IDs don't, so links by ID never break. You rarely need to see them.

### What's the difference between a link in the text and a link in the side panel?

Both are real links. `[[Links]]` in the text are part of your writing and are removed by deleting them
from the text. Links added with **Add link…** or by accepting a suggestion aren't in the text. You can
change their type, reverse their direction or remove them in the side panel.

### Why does a suggestion say only "18% · possible"?

The number is the model's honest estimate that you would link the two notes. In a young or sparse vault,
most pairs of notes are unrelated, so even good suggestions start modest. The order of suggestions
matters most, and the estimates improve as you link and dismiss. See
[Link suggestions](link-suggestions.md).

### Does it work on macOS or Linux?

Not yet. Linux packages (.deb, AppImage) and macOS are on the
[roadmap](https://github.com/DutraIRS/ZettelApp/blob/main/ROADMAP.md).

### Is the app available in other languages?

Yes. The installer and the app are translated into Spanish, Portuguese (Brazil), French, German, Italian,
Russian, Simplified Chinese, Japanese, Korean and Arabic. The app follows your Windows language by default;
change it in *Options*. Missing text falls back to English.

### How do I uninstall, and what happens to my data?

*Settings ▸ Apps ▸ Installed apps ▸ ZettelApp ▸ Uninstall*. The uninstaller offers an unticked **Also
delete my ZettelApp settings and data** option that removes preferences, saved API keys, logs, cache and
automatic backups, **and all your notes** (vault databases and attachments). Unticked, your notes are kept. For the
portable version, delete its folder; its preferences live in the registry under
`HKEY_CURRENT_USER\Software\ZettelApp`, and logs and backups in `%LOCALAPPDATA%\ZettelApp`.

### Something went wrong. Where are the logs?

In `%LOCALAPPDATA%\ZettelApp\Logs`. Please include the relevant part when you
[report an issue](https://github.com/DutraIRS/ZettelApp/issues). Check that it contains nothing private
first.
