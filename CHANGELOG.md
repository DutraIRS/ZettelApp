# Changelog

All notable changes to ZettelApp are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/).

## [1.1.1] - 2026-10-29

### Added

- Select several notes in the list (Ctrl+click, Shift+click, Shift+arrows) to duplicate, trash,
  restore or delete them together; Delete moves the selection to the Trash.
- Duplicate a note (*Edit ▸ Duplicate Note*, Ctrl+D): its text, tags, picture, mind map, the links
  it makes and its hand-written flashcards.
- In the 2D graph, click a group's area to select it and drag it to move all its notes.

### Changed

- The website is built with [Rational Web](https://github.com/DutraIRS/Rational-Web). It looks and
  works exactly as before, with a "Proudly developed with RationalWeb" line in the footer.

## [1.1.0] - 2026-10-28

### Added

- **The Lost Prince of the Archive**, an optional first-run adventure that teaches notes, links, tags,
  suggestions, the graph, mind maps, attachments, review and Insights through real actions.
- Line styles and arrow-tip choices for built-in and custom link types, including a live preview.
- Checklists (`- [ ]`) in note bodies, toggled from the preview.
- Alarm notes: set a date and optional time and get a notification (ZettelApp must be running).
- LaTeX formulas (`$…$` and `$$…$$`) with a formula dialog and live preview.
- A title image per note (right-click an image), shown as a rounded thumbnail in the note list.
- Insert file links, and manage several saved AI API keys.
- Interface, documentation and website translations: Spanish, Portuguese (Brazil), French, German,
  Italian, Russian, Simplified Chinese, Japanese, Korean and Arabic. Change the app's language in
  *Options ▸ General*; the website suggests your browser's language once and has a language menu
  (the globe) on every page. The installer is also offered in Korean and Arabic.

### Changed

- Split view is the default; the delete button moved to the editor toolbar.
- Menu and option check marks now show a tick.
- The 3D graph labels are clearer, its group areas are bounded hulls that follow depth, and 2D
  arrows follow nodes while dragging.
- Link styles now travel through archive and JSON export, import and MCP responses.
- New vaults start with a small linked tour of ZettelApp.
- The website, documentation navigation and footer now adapt to narrow phone screens.
- Installing an update keeps the interface language picked in *Options*.
- The main window can be made much narrower (about 1,000 px in every language): the editor and
  graph toolbars wrap onto a second line instead of setting the window's minimum width.
- Deleting a note's title image from its text also clears it as the title image.

### Fixed

- Dragging and dropping images into a note now works.
- Ticking "delete my data" when uninstalling now also removes your notes, and only the files
  ZettelApp created: other files in a vault's folders (even in its `assets` folder) are kept.
- Close the database connection when opening or upgrading a vault fails.
- *Options* showed "Use Windows setting" when the language had been chosen in the installer.
- Options, the graph page, the link panel and many messages were still in English in the other
  languages, and counts used English plurals.
- An alarm time edited by hand into the database no longer breaks the alarm check.
- Background tasks (link suggestions, the graph layout, Insights) were never freed, so memory grew
  with every note opened (about 85 MB per 60 notes in a 2,000-note vault). Graph layouts kept for
  quick switching are now also limited to the latest few.
- Website: the first-visit language redirect opened the documentation index instead of the same
  page, Arabic pages scrolled sideways, and between 720 and 900 px the header wrapped so the
  language list opened off-screen.

## [1.0.0] - 2026-10-28

First release.

### Added

- **Notes**
  - Atomic Markdown notes with timestamp IDs and autosave.
  - Edit, Split and Preview modes.
  - Tags (nested `a/b`), source links (web, e-mail or Zotero) and images (paste, drop or insert).
  - `#tags` written anywhere in the text are real tags (ignored in code, link targets and
    `[[#headings]]`), shown as outlined chips that disappear when the `#tag` is deleted.
  - Ctrl+click in the editor follows `[[note links]]` (creating the note if needed), web, e-mail, Zotero
    and file links, and `#tags`, with a tooltip saying what will happen. In the preview a normal click
    follows links.
  - Links to local files (*Insert ▸ Link to a File…*, or drag a file into the text) show the file in File
    Explorer without opening or running it. Network (UNC) paths are refused.
  - A welcome note in new vaults that explains links, tags, images, mind maps and flashcards.
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
  - Links between the same two notes are separate curves with arrowheads. Hovering or selecting a note
    dims other links and labels each neighbour with the link types as read from that note.
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
  read-only by default. It works only while ZettelApp is open and the MCP switch in its status bar, which
  is off at every start, is on.
- **Update check** at start-up (one optional HTTPS request) with a small notice in the lower-right corner.
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
  - An uninstaller option to delete settings, saved API keys, logs, cache and backups. Notes are never
    deleted.
- **Documentation** (including an MCP API reference and a *Bring your own LLM* guide) and a website.
