# Export and import

## Export

*File ▸ Export…* (Ctrl+Shift+E) exports **the whole collection or any part of it**:

| Scope | What is exported |
|---|---|
| **Entire collection** | Every note (not the Trash). |
| **Current note and linked notes** | The open note and the notes within **Depth** links of it, following links in both directions: a *subgraph*. |
| **Notes with tag** | Notes with the tag, including nested tags (`math` includes `math/algebra`). |

The dialog shows how many notes, links and flashcards the scope contains. You can also export from the
note list (right-click ▸ *Export with linked notes…*), from a note's ⋯ menu, from the graph (the export
button exports the notes on screen) and from a graph node's menu.

### Formats

| Format | File | Contents |
|---|---|---|
| **ZettelApp archive** | `.zip` | Everything, including images: notes, typed links, link types, flashcards, mind maps. Re-import it into ZettelApp on any computer. Best for backups and moving vaults. |
| **Markdown files** | `.zip` | One `.md` file per note with YAML front matter (id, title, tags, source link, dates, typed links, mind map) and `[[wiki links]]` between files. Links not written in the text are listed under *Links* as `type:: [[Note]]`, and manual flashcards under *Flashcards* as `Q:`/`A:`. Images are in `assets/`. Opens in Obsidian and other Markdown editors. |
| **Website** | `.zip` | A self-contained static website: an index with a graph overview, a tag index and one page per note, with links, mind maps and flashcards (answers revealed on click). No scripts; it works offline by opening `index.html`. Light and dark themes. |
| **JSON** | `.json` | Structured data for scripts and other tools (images referenced, not included). |
| **GraphML** | `.graphml` | The link graph for Gephi, yEd, Cytoscape or NetworkX, with titles, tags and dates on nodes and link types on edges (directed or not). |
| **Graphviz DOT** | `.dot` | The graph as a Graphviz diagram, with link types coloured and labelled; undirected types have no arrows. |
| **Anki deck** | `.apkg` | The flashcards of the exported notes. See [Anki](review-and-anki.md#anki). |

Exports are written to a temporary file and moved into place only when complete, so an interrupted
export never leaves a half-written file. They run in the background, and **Show in folder** reveals the
result in File Explorer.

Mind maps also have their own export (PNG, SVG or FreeMind `.mm`) in the **Mind map** tab, and the graph
can be saved as a PNG image.

## Import

*File ▸ Import…* accepts:

- **ZettelApp archives** (`.zip`) and **JSON** exports;
- **Markdown files** (`.md`) or a **`.zip` of Markdown files**;
- *File ▸ Import Markdown Folder…* for a folder of Markdown files, such as an **Obsidian vault**.

What is kept:

- **From ZettelApp archives and JSON:** notes keep their IDs, typed links, flashcards, mind maps and
  images. Importing the same archive twice skips notes that haven't changed. If an ID is already used by
  a different note, the import gets a new ID and the links are updated.
- **From Markdown:**
  - the title comes from the front matter `title`, the first `# heading` or the file name;
  - tags come from front matter `tags` and inline `#hashtags`;
  - the source link comes from `url` or `source`, and the creation date from `created`;
  - `[[wiki links]]` (including Obsidian's file-name links) and `type:: [[links]]` become links;
  - images referenced with `![](path)` or Obsidian's `![[image.png]]` are copied into the vault;
  - hidden folders such as `.obsidian` and `.trash` are skipped;
  - ZettelApp's own Markdown export imports back with its typed links, flashcards and mind maps.

### Safety

Imported files are treated as untrusted:

- archive paths are checked, so files can't be written outside the import (no "zip-slip");
- archives with too many files, too much data or suspicious compression ratios (decompression "bombs")
  are refused;
- every field is type-checked and size-limited;
- images are re-verified by content;
- remote images and links to other places on disk are not imported.

A daily backup is made when a vault is opened, and you can make one any time with *File ▸ Back Up Vault
Now*. See [Privacy and security](privacy-and-security.md).
