# Changelog

All notable changes to ZettelApp are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- **Tags in the text**: `#tags` written anywhere in a note are real tags (ignored in code, link targets and
  `[[#headings]]`). They appear as outlined chips and disappear when the `#tag` is deleted. Tags typed in
  the *Add tag* box stay separate.
- **Ctrl+click in the editor** follows `[[note links]]` (creating the note if needed), web, e-mail and
  Zotero links, and `#tags`, with a tooltip saying what will happen. In the preview a normal click follows
  links.
- **Links to local files** (*Insert ▸ Link to a File…*, or drag a file into the text): clicking one shows the
  file in File Explorer without opening or running it. Network (UNC) paths are refused.
- **Graph**: links between the same two notes are separate curves with arrowheads. Hovering or selecting a
  note dims other links and labels each neighbour with the link types as read from that note.
- **MCP switch** in the status bar: MCP clients can use the vault only while ZettelApp is open and the
  switch, which is off at every start, is on. `zettelapp-mcp` stops by itself when it goes off.
- **Update check** at start-up (one request, optional) with a small notice in the lower-right corner.
- **Uninstaller option** to delete settings, saved API keys, logs, cache and backups. Notes are never
  deleted.
- **Documentation**: an MCP API reference, a *Bring your own LLM* section, and updated Anki, Zotero,
  privacy, graph and FAQ pages.

### Changed

- The welcome note in new vaults explains links, tags, images, mind maps and flashcards.
- The vault schema is now version 2 (`tags.source`) and upgrades automatically.

### Fixed

- Options sections overlapping on hover.
- CI checks that could not fail.
- Markdown imports are atomic: a failed import leaves the vault unchanged.

## [1.0.0] - 2026-10-27

First release.

### Added

- **Notes**
  - Atomic Markdown notes with timestamp IDs and autosave.
  - Edit, Split and Preview modes.
  - Tags (nested `a/b`), source links (web, e-mail or Zotero) and images (paste, drop or insert).
  - Note pictures.
  - Full-text search with `tag:` filters.
  - A Trash with restore.
- **Links**
  - `[[Wiki links]]` by title or ID, with completion.
  - **Typed links** (`supports:: [[…]]`): seven built-in types and custom ones, directed or undirected,
    with reverse names.
  - Reverse direction, and backlinks.
- **Link suggestions**: a Naive Bayes classifier over eight similarity features (LSA, TF-IDF,
  Levenshtein and Jaro-Winkler on titles, Levenshtein on text, tag and link overlap, title mentions).
  It learns from accepted and dismissed suggestions and explains each suggestion.
- **Mind maps** per note, with keyboard editing and links to notes. "From links" generation. PNG, SVG and
  FreeMind export.
- **Graph**
  - 2D and 3D views, local graphs with depth, and link-type filters.
  - Colouring by tag or by **k-means / hierarchical clusters** (auto k by silhouette, named by keywords).
  - **Grouping** with shaded regions.
  - Colour-vision-safe palette and dash patterns.
- **Insights**: stat tiles and charts (notes per month, top tags, links by type, hubs, topics), each with a
  table view.
- **Review**
  - SM-2 spaced repetition.
  - Quizzes: flashcards, multiple choice, typed answers graded by edit distance, and "Name that note".
  - Flashcards from `Q:`/`A:` and `{{c1::cloze}}` text, or added by hand.
- **Anki**: sync through AnkiConnect, and `.apkg` export with stable IDs. `zettelapp://` links on cards
  open the note.
- **Zotero**: search the local library, insert citations, create literature notes with PDF links.
- **Ask your notes**: retrieval-augmented answers with citations from Anthropic Claude (default
  `claude-opus-5-5`), OpenAI or Z.ai, through an extensible provider registry. Keys are kept in Windows
  Credential Manager.
- **MCP server** (`zettelapp-mcp.exe`) for Claude Desktop, Claude Code and other MCP clients. It is
  read-only by default.
- **Export**
  - Scopes: the whole collection, a note's subgraph, or a tag.
  - Formats: ZettelApp archive, Markdown (Obsidian-compatible), static website, JSON, GraphML, Graphviz
    DOT and Anki deck.
- **Import**: ZettelApp archives and JSON, Markdown files, zips and folders (including Obsidian vaults).
- **Windows**
  - Light/dark theme and accent colour that follow Windows.
  - Standard menus and shortcuts.
  - Per-user installer with a language picker.
  - Portable zip.
  - Daily backups.
  - Single instance with `zettelapp://` link handling.
- **Documentation** and a website.
