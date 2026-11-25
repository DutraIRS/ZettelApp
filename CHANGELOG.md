# Changelog

All notable changes to ZettelApp are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Changed

- **One top row on Windows** (roadmap item 10): the app's icon, the menus, the window's title and
  the minimise, maximise and close buttons share one row in the theme's colours, instead of
  Windows' title bar above the menu bar. The window still snaps, resizes from every edge, keeps its
  shadow and rounded corners, and maximises on a double click. Linux keeps the desktop's own title
  bar.
- **Notes in the rail (or Ctrl+1) brings a folded note list back**: there is nothing else to see
  on that page. Opening a note from the graph or elsewhere still leaves the list as it was.

### Added

- **Diffusion in the graph** (*Graph ▸ Diffusion*): select a note and watch its influence spread
  through the network in a five-step loop, by link distance (one link further at each step) or by
  links weighted by similarity (a random walk with restart that favours links between notes alike
  in meaning). Notes run from deep red to yellow as their share falls, unreached notes turn grey,
  and the legend explains the colours; in 2D and 3D.
- **Preview and Reading view options** (*Options ▸ General*): whether a single line break starts a
  new line or lines join into one paragraph (standard Markdown), alignment at the start or
  justified, line spacing and the space between paragraphs. They apply wherever notes are shown
  read-only: the preview, the Reading view, Review and Ask.
- **Ask your notes: send the open note's neighbours** (*Send ▸ Every note in the scope, nearest
  first*): with *Current note and linked notes*, every note within the depth chosen goes, nearest
  first, instead of only the most relevant. **Review before sending** shows the notes about to be
  sent, to untick any first.
- **Network measures in Insights**: connected parts, the clustering coefficient and transitivity,
  the degree distribution with a power-law exponent (fitted by maximum likelihood when the vault
  is big enough), and the notes that bridge the network (betweenness) or sit at its centre
  (PageRank).
- **Arrow tips at each end** (*Options ▸ Link types ▸ Tip at the start*): a directed link type can
  start with a different tip from the one it ends with, and an undirected type can have tips, the
  same at both ends. Graph, samples and the SVG, GraphML and DOT exports draw them. The vault's
  schema goes to version 6; older ZettelApp versions won't open a vault after this one has.

### Fixed

- **The first window fits the screen**: on its first start the window took 1440 × 900 whatever the
  screen, so on a small one (a 1366 × 768 laptop) it ran off the edge, and Xfce leaves it there.
  It now shrinks to the screen's free area.
- **Pictures fit the Reading view's column**: a picture was scaled to the whole preview's width, so
  in Reading view a wide one stuck out of the centred column and the preview scrolled sideways (a
  little in Split view too). It now fits the text's width, and follows it: a picture kept the
  size it was loaded at, so after switching to Reading view or resizing the window it was sized
  for the old layout.
- **Diffusion's legend title wraps**: *Diffusion from “…”* was cut off at the legend's edge when
  the note's title was long ("Welcome to ZettelAp"); it now goes onto a second line.
- **An alarm's notification has an Open note button on KDE Plasma and GNOME**: they made the
  notification's only action the click on it and showed no button. The button is now sent too,
  except to Xfce's notification service, which already showed it.
- **The website on phones**: links to a section (*Download*, *Features*) no longer hide its heading
  under the header; the menus close once a link in them is followed (and on Escape); the Linux
  install commands stay on one line and scroll sideways instead of breaking mid-word, and read
  left to right on the Arabic page; in Arabic the menu
  opens under its button. A screenshot opens full size when tapped (the dark one in dark mode).
- **Imports from Obsidian**: links by path (`[[Folder/Note]]`) and to a block (`[[Note^id]]`)
  now link to the note; where two notes share a name, a bare link goes to the one nearest the
  vault's root, and links to a title that two notes share name the note by its id, so they
  can't land on the wrong one (also a note of that name already in the vault).
- **Imports from Evernote**: list items from Evernote 10 keep their text on the bullet's line,
  checklist items in a list become checklist lines, tables become Markdown tables, and code
  blocks are fenced.

## [1.4.0] - 2026-11-23

### Added

- **Black (OLED) theme** (*View ▸ Theme*, or Options): the dark theme on true black.
- **Your own colours** in *Options ▸ General*: a primary colour (buttons and other accents), a
  secondary colour (links), a highlight colour (selected text and find matches) and a text colour,
  over any theme; each can go back to the theme's own.
- **Folding side panels**: the note list and the links panel each have a small tab near the bottom
  of their edge that folds them away to give the note more room, and brings them back; dragging the edge resizes them
  and a double-click on it folds them too. *View ▸ Note List* (Ctrl+Shift+L) and *View ▸ Links
  Panel* (Ctrl+Shift+K) do the same, and ZettelApp remembers each panel's state.
- **Reading view** (roadmap item 9): the third editor mode shows the note alone, as a centred
  column of comfortable width at the editor's text size, with the title and source link locked
  (an empty source link is left out). A tab between the text and the preview folds the text away
  and brings it back, like the side panels' tabs and in line with them. The mode chosen is kept
  for the next start; a new note still opens with its text, and the next note opens in Reading
  view again.
- **The adventure card's story** is set in justified paragraphs with space between them (aligned
  to the start in Chinese and Japanese, where justifying stretched the gaps around Latin words).
- **Android (alpha)** (roadmap item 5): a native Kotlin/Compose app in `android/` runs the Qt-free
  Python core on device through Chaquopy, with a notes list, title search, editing and creating
  notes, a tag filter, links and backlinks, a graph, Insights, flashcard review, the trash and
  `zettelapp://note/<id>` deep links. A new vault starts with the starter notes. The vault lives in
  the app's private storage (scoped storage denies SQLite the shared `Documents` folder), API keys
  stay in memory for the session, and
  AnkiDroid detection plus `zotero://` links go through Android intents. The desktop apps are
  unchanged; `paths` and `core.secrets` gained explicit Android branches so the platform dispatch
  stays correct (`sys.platform` is `linux` on Android).
- **Linux support** (roadmap item 2): ZettelApp now runs on 64-bit Linux desktops, on X11 and Wayland.
  - New install options: a `.deb` for Debian-based distributions and a portable `.tar.gz`, built by
    `packaging/build-linux.sh`. A Flatpak manifest (`packaging/flatpak/`, freedesktop 24.08) and a Snap
    recipe (`packaging/snap/`, core24 with the GNOME extension) live in the repository; store listings
    are planned, and releases can already publish the Snap when store credentials are configured.
  - API keys are stored in the Secret Service (GNOME Keyring / KWallet) instead of Windows Credential
    Manager. Without a keyring they are kept in memory only, as before, and *Options ▸ AI* and the
    *Ask* page say so; a keyring that refuses (a dismissed prompt, a locked collection) gets an error
    message. Nothing changes on Windows.
  - Alarms show a desktop notification through the desktop's notification service, also on desktops
    without a tray such as GNOME; clicking it (*Open note*) opens the note, as the toast does on
    Windows.
  - Notes default to `~/Documents/ZettelApp` (the desktop's own Documents folder, through
    `xdg-user-dir DOCUMENTS`, so `~/Documentos` on a Portuguese desktop), settings live in
    `~/.config/ZettelApp`, caches and generated images in `~/.cache/ZettelApp`: the XDG base
    directories, instead of `%LOCALAPPDATA%`.
  - Where the Windows icon fonts are missing, icons come from the desktop's icon theme when it has a
    monochrome symbolic icon of the same meaning (Adwaita, for instance), and otherwise from the
    Fluent UI System Icons, the open-source set the Windows glyphs belong to (MIT licence, a small
    subset bundled by `tools/fetch_icons.py`): the same pictures as on Windows, including the Graph,
    Insights, Review and Mind map icons and the language-specific Bold and Italic letters, drawn
    sharp at any scaling and in the theme's colour. Mind map nodes linked to a note show their link
    icon again.
  - The theme follows the desktop's light/dark setting as Qt's platform theme reports it (on Xfce,
    the GTK theme) and switches when it changes. The accent colour is GNOME's on GNOME, KDE's on
    KDE and the settings portal's where it offers one, in a lighter or darker shade per theme as
    Windows does; desktops without an accent setting, such as Xfce, keep the Windows blue.
  - Text uses the desktop's own font (whatever GNOME, KDE, Xfce… are set to) at the app's usual
    sizes, so layouts match Windows; code in the preview uses the desktop's monospace font, and
    formulas use the serif and maths fonts Linux distributions ship. Graphviz exports made on Linux
    name `sans-serif` after Segoe UI, so diagrams drawn from them don't fall back to a serif font.
  - `zettelapp://` links from Anki cards open the matching note: the `.deb` ships a desktop entry
    advertising the scheme, and other installs register a user-local one from
    *Options ▸ Desktop integration* (also from a folder whose name has spaces).
  - Revealing a file in the file manager selects it through `org.freedesktop.FileManager1`, also when
    the file manager isn't running yet (Thunar, Nautilus, Dolphin and Nemo start on demand); a folder
    opens as on Windows, and without that service the file's folder opens.
  - The MCP switch holds a lock that the system releases when ZettelApp exits in any way, so MCP
    clients are refused as soon as ZettelApp closes, even after a crash.
  - The update notice's *Download* button offers the `.deb` to the `.deb` install, the `.tar.gz` to
    the portable folder and the software centre to Flatpak and Snap.
  - On Linux, links to local files in notes accept only absolute paths on the same machine: network
    shares, `file://` URLs with a host and control characters are refused before any lookup.
- CI now runs the tests on Ubuntu as well as Windows, builds and self-tests the Linux packages on every
  pull request, and releases carry the `.deb` and `.tar.gz` alongside the Windows installer.
- **Reverse names in the text**: with a directed type such as *Discusses* / *Discussed by*, a note can
  write `discussed_by::[[A]]` for the link A → this note. Types are also written by their name
  (`apoia::`), and built-in types answer to their English names in any language. A directed type
  whose reverse isn't named yet reads "Reverse Nameon", and `reverse_nameon::` always works.
- **Write links in both notes** (*Options ▸ Link types*, off by default): a `[[link]]` added in a
  note's text is also written in the linked note's text as seen from its side (`discussed_by::[[A]]`
  for `discusses::[[B]]`), at its end or start, and taken out again when the link is deleted.
- **Note list ordered by closeness to the open note**, by meaning (LSA, the new default) or by the
  fewest links away. The open note comes first and the order follows it as you move between notes.
- **Graph filters with checkboxes**: *Link types* is now a list of checkboxes that stays open, and a new
  *Tags* list has *Show* (hide the notes with a tag) and *Group* (a tag that forms no group and doesn't
  count for clusters, for tags like `#todo`) for each tag. The choices are kept between sessions.
- **Microsoft Store package**: `packaging/build.ps1` also builds `dist/ZettelApp.msix` (with the
  Windows SDK). In the package the app leaves updates to the Store, links come from its manifest, and
  the MCP server is reached through a `zettelapp-mcp.exe` alias.
- **Find and replace in a note**: Ctrl+F in the note text (Ctrl+F again searches all notes), Ctrl+H to
  replace one or all matches.
- **Several carets**: Alt+Shift+click (or Alt+click) adds a caret; typing, deleting and moving happen
  at every one. Alt+Shift+click works on Linux desktops that keep Alt+click for moving windows (Xfce,
  KDE before Plasma 6).
- `PRIVACY.md`: the one automatic network request (the update check) and what else is sent, and when.
- The local graph says which note it is centred on (*Around "…"*), or that no note is open.

### Changed

- *Options*: the *Windows integration* page is now *Desktop integration*, and on Linux it configures a
  `zettelapp` (not `zettelapp.exe`) MCP binary and a Claude Desktop config under `XDG_CONFIG_HOME`.

### Fixed

- **Clicking an alarm notification on Windows 11 showed the desktop** instead of the note:
  Windows never passed the click on Qt's tray balloon to the app. Alarms are now a Windows
  reminder toast with the app's icon, the note's title and text, and **Open note** and
  **Dismiss** buttons; it stays until you choose, and opening it brings the window back as it
  was (maximised stays maximised). It opens the note through its `zettelapp://` link, so the
  installed app and the Store app use it; a portable copy does once links are registered in
  *Options ▸ Desktop integration*, and shows the old balloon otherwise.
- *Options ▸ General ▸ Editor text size* now applies from the start: the note text was always
  11 pt and the preview the interface's size until Options was saved again.
- Closing a vault (or switching to another) while the note list was being reordered by closeness
  raised an error in the background.
- The preview spaced paragraphs, headings and lists unevenly and used a smaller text than the
  editor. Every block now leaves the same space below it, a heading more above it, and the
  preview follows the editor's text size (also in Review and Ask).
- A change of the desktop's accent colour was followed only after a restart. The app now
  follows it at once: on Windows, on GNOME 47+ and on KDE Plasma 6.
- KDE Plasma: *Show in folder* and local file links opened whichever file manager owned the
  `org.freedesktop.FileManager1` D-Bus name (Nautilus, when installed). When Dolphin is the
  default file manager, Dolphin now shows the file.
- Windows: file dialogs (insert image, link to a file, mind map export, save graph image) opened
  the working folder, which from the Start-menu shortcut is the install folder. They now open the
  folder used last, or Documents.
- A maximised window came back un-maximised after clicking an alarm or a `zettelapp://` link.
- Menu access keys were used twice in some menus (in English, and more in translations); every
  item now has its own, in every language.
- A message strip on screen kept the old theme's colours after a theme switch.
- Alt+click on the caret just added takes it away again.
- Icons follow a theme switch made while ZettelApp runs (*View ▸ Theme*, or the system turning dark);
  they kept the old theme's colour, nearly invisible on dark.
- In the find bar, Tab goes from the search straight to *Replace with*.
- A system keyring that answers with an error (locked, refused or timed out) no longer crashes the
  *Ask* page: it shows no key, and *Ask* reports the keyring's error.
- Replaced link suggestions no longer stay drawn under the new ones while a dialog is open.
- Note list snippets keep underscores inside words, so `supported_by:: [[…]]` no longer shows as
  `supportedby:: …`.
- *Help ▸ Donate* has its own access key (Alt+H, O in English) instead of sharing D with
  *Documentation*; the same clash is fixed in Arabic, Chinese, French, Japanese, Korean, Portuguese
  and Spanish.
- On Linux, *Insert ▸ Image…*, *Link to a File…*, the mind map export and *Save graph as image*
  open the folder used last (Documents the first time), as on Windows, instead of the folder
  ZettelApp was started from.
- Markdown files saved with a byte-order mark (as Notepad and other Windows editors do) keep their
  front matter (title, tags, aliases) when imported; JSON exports with one import too.
- Importing a Markdown folder no longer follows symbolic links to notes or images outside that
  folder.
- On Linux, the settings, data (logs, backups, search index) and cache folders are made readable by
  your account only (0700), and so is the log file (0600), whatever the umask; folders made by an
  earlier version are tightened at the next start.
- `---` under a line of text drew a heading in the preview (a Markdown "setext" heading) while the same
  `---` elsewhere drew a rule, and the editor showed neither as a heading. It is now always a rule, and
  indented lines are no longer code blocks (fence code with ```), so the preview reads like the editor.
- Cloze cards in a table: the prompt was capped in height, so the blank could sit out of sight and the
  card looked like the whole table with nothing hidden; revealing printed the table again. The prompt
  now fills the card, the blank is bold and scrolled into view, and the answer fills it in place.
- Bold or Italic on part of a bold or italic stretch nested a second one (no visible change); it now
  takes the formatting off that part (`*homo nov*os`).
- The Linux app ID is `io.github.dutrairs.zettelapp` (it was missing an r).
- An undirected link written in both notes is drawn once in the graph and listed once in the side panel.
- A click on empty space in the graph unselects the note.
- The link types list in *Options* (and the note picker and Zotero results) no longer starts with
  overlapping rows.
- Wording no longer assumes Windows on Linux: the *App theme* and *Language* options and the
  *View ▸ Theme* menu say "use system setting", privacy notes about API keys say "the system
  keyring", the About dialog says "for Windows and Linux", and *File ▸ Show Vault in File Manager*,
  the hints on file links and the welcome notes say "file manager" instead of "File Explorer".
  Translations updated in all 11 languages.
- A link to a local file whose address contains a tab or a line break is refused, instead of
  silently pointing at the file named without those characters.
- Links to local files whose names contain spaces or accented letters open again: the renderer now
  decodes the link destination before looking the file up (markdown-it writes destinations
  percent-encoded).

## [1.3.1] - 2026-11-05

### Changed

- Bold and Italic (buttons, Ctrl+B and Ctrl+I) work like a word processor's: pressing again removes them,
  spaces and list, heading or quote marks at the edges of the selection stay outside the markers, each
  selected line is formatted on its own, and the text stays selected so both can be combined.
- The Bold and Italic buttons show the letters Windows uses in each language: N in Portuguese and
  Spanish, G in French and Italian, F in German, Ж in Russian, and so on.
- After `[[`, the best match is highlighted, so Enter or Tab takes it. Titles that start with what
  you typed come first, and accents don't matter.
- Search results that only semantic search found say *≈ similar meaning*, and *Options ▸ Search*
  says that semantic search works in the search box. The link suggestions name their own semantic
  similarity (LSA), which doesn't use the language model.
- The note list's sort order is a menu behind an icon, next to the tag options, so *All tags* fits in
  every language. A tag too long for its box ends in "…" and shows in full on hover.

### Fixed

- Bold inside italics, and bold italics, show as bold in the editor and the preview.
- An autosave while the `[[` list is open no longer clears the highlighted note.
- The match strength of suggested links ("possible", "likely", "strong") and the "3 of 8" note
  count are translated.
- Tests and the screenshot tool no longer write backups, search indexes or caches into the real
  ZettelApp data folder.

## [1.3.0] - 2026-11-03

### Added

- Import Evernote exports (`.enex`): text, tags, pictures, checklists, source links and dates.
- Markdown imports turn links to other Markdown files (as Notion and some Obsidian vaults write them),
  `aliases` in the front matter and embedded notes (`![[Note]]`) into note links, and leave Notion's
  long IDs out of titles.
- An unticked installer option, *Set up semantic search*: ZettelApp then downloads the language
  model the first time it starts and turns semantic search on.
- In the 3D graph, Ctrl+drag a note to move it.
- A **Graph** tab in *Tools ▸ Tag Ontology…* draws the ontology.

### Changed

- Notes in the 3D graph are shaded like spheres instead of flat discs.
- The website's screenshots show the current version, with English dates on any computer.

### Fixed

- Group names in the 3D graph no longer overlap.

## [1.2.1] - 2026-11-03

### Fixed

- Opening a note whose stored time has no time zone no longer crashes the app.

## [1.2.0] - 2026-11-02

### Added

- **Tag ontology** (*Tools ▸ Tag Ontology…*): say that a tag is the parent, a synonym or a related concept
  of another, and tag filters and searches follow. ZettelApp archives carry it, and MCP's `list_tags`
  returns it.
- **Hybrid search** in the note list: full text, typo-tolerant titles and tags, and the tag ontology, fused
  into one ranking whose weights can be set in *Tools ▸ Options ▸ Search*. Results show the part of the
  note around your word.
- **Semantic search** (optional, off by default): after a one-time 135 MB download you ask for, a language
  model on your computer finds notes by meaning, across languages. Your notes never leave your computer.
- An unticked installer option, *Set up semantic search*, downloads the model on the first start.
- **Adaptive ranking** (optional, off by default): right-click a search result to mark it as relevant or
  not, and the kinds of match you prefer count for more.
- Vaults move to schema 5 when opened; older versions of ZettelApp can't open them afterwards.

### Changed

- The update notice's **Download** button fetches the installer directly on installed copies; portable
  copies still open the release page.
- The MCP server is stricter about malformed requests, and `tag:name` also follows the tag ontology.
- The 3D graph stops rotating while it isn't visible.

### Fixed

- Searching Chinese, Japanese or Korean text now finds words inside longer runs of characters.
- A search combining a tag filter and a very common word could miss tagged notes.
- API keys are never sent to another site when a provider redirects a request.
- A timestamp without a time zone in an imported file is read as local time.
- Dialogs are freed when closed; each one used to stay in memory until the app closed.
- *Computing layout…* and *Analysing…* no longer stay on screen when another program changes the vault.

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
