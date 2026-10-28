# MCP server

The [Model Context Protocol](https://modelcontextprotocol.io/) (MCP) is an open standard that lets AI
assistants use tools and data from other programs. ZettelApp includes an MCP server, so assistants such
as **Claude Desktop** and **Claude Code** can search your Zettelkasten, read notes, follow typed links
and ask for link suggestions while they help you.

## How it runs

The server is a separate small program, **`zettelapp-mcp.exe`**, installed next to `ZettelApp.exe`.
From source, the same server runs with `python -m zettelapp.mcp_main`. Your MCP client starts it when
needed and talks to it over standard input/output. **No network port is opened.**

```text
zettelapp-mcp --vault "C:\Users\me\Documents\ZettelApp" [--allow-writes]
```

Without `--vault`, it serves the vault you last opened in ZettelApp. Changes made through MCP appear in
the app within a few seconds.

## The MCP switch

MCP clients can reach your notes only while **ZettelApp is open and the MCP switch in its status bar is
on**. The switch is **off every time ZettelApp starts**, so you decide, each session, whether assistants
may read your notes. Turn it off, or close ZettelApp, and the server stops within about a second.
Without the switch the server refuses to start and says why. For the exact behaviour, see the
[MCP API reference](mcp-reference.md).

## Connect Claude Desktop

Open *Tools ▸ Options ▸ MCP server* and click **Add to Claude Desktop…**. ZettelApp adds itself to
`%APPDATA%\Claude\claude_desktop_config.json` (keeping a backup of the old file). Then restart Claude
Desktop. Turn on the **MCP switch** in ZettelApp's status bar before you start Claude Desktop; if you turn
it on later, reconnect ZettelApp in Claude Desktop or restart it. To do it by hand, copy the snippet shown
on that page into the file. It looks like this:

```json
{
  "mcpServers": {
    "zettelapp": {
      "command": "C:\\Users\\me\\AppData\\Local\\Programs\\ZettelApp\\zettelapp-mcp.exe",
      "args": ["--vault", "C:\\Users\\me\\Documents\\ZettelApp"]
    }
  }
}
```

## Connect Claude Code

The same Options page shows the command to copy:

```powershell
claude mcp add zettelapp -- "C:\Users\me\AppData\Local\Programs\ZettelApp\zettelapp-mcp.exe" --vault "C:\Users\me\Documents\ZettelApp"
```

Other MCP clients need the same command and arguments. As with Claude Desktop, switch MCP on in ZettelApp
first, and reconnect the server (in Claude Code, `/mcp`) if you switch it on afterwards.

## Tools

| Tool | What it does |
|---|---|
| `search_notes` | Full-text search over titles, text and tags (`tag:name` filters work). An empty query lists recently edited notes. |
| `get_note` | A note's full text, tags, source link, dates, typed links in both directions, flashcards and mind map outline. |
| `list_tags` | All tags, with the number of notes using each. |
| `get_subgraph` | The notes within 1–4 links of a note, and the typed links between them (optionally only some link types). |
| `suggest_links` | Notes likely related to a note but not yet linked, ranked by the [Naive Bayes suggester](link-suggestions.md). |
| `list_link_types` | The link types in the vault, such as *supports*, *contradicts* and *part of*. |
| `create_note` | *(write)* Create a note. `[[Title]]` in the body links to existing notes. |
| `add_link` | *(write)* Add a typed link from one note to another. |

## Read-only by default

The server opens your vault **read-only**. The two write tools are offered only when **both** of these
are true:

1. **Allow MCP clients to create notes and links** is ticked in *Options ▸ MCP server*;
2. the server was started with `--allow-writes`. The snippet on the Options page includes this flag once
   you tick the option.

The setting is checked again on every write, so unticking it takes effect immediately. Turning it on
needs the MCP client to restart the server.

Note contents are passed to the assistant as data, and the server tells the assistant not to treat them
as instructions. Inputs are validated (IDs, sizes and limits), and the server never touches files
outside the vault.

## Troubleshooting

- **The client says the server failed to start, or tool calls say the switch is off.** Open ZettelApp
  and turn on MCP in its status bar, then reconnect the server in your client.
- **The server still fails to start.** Check that the path to `zettelapp-mcp.exe` is right.
  Run the command yourself in a terminal: it reports what's wrong (for example "No ZettelApp vault
  found") on standard error.
- **Write tools are missing.** Tick the option *and* add `--allow-writes`, then restart the client.
