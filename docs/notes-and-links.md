# Notes and links

## Writing notes

Notes are written in **Markdown**: `**bold**`, `*italic*`, `# headings`, lists, `> quotes`,
`` `code` ``, fenced code blocks, tables and `~~strikethrough~~`. The toolbar above the editor inserts the
common ones, and Ctrl+B / Ctrl+I work as usual. Lists continue when you press Enter.

The editor has three modes (Ctrl+E cycles through them): **Edit**, **Split** (text and preview side by
side) and **Preview**.

For safety, raw HTML in a note is shown as text and never rendered. Links in the preview open only web
pages (`http`, `https`), e-mail (`mailto`), notes, Zotero items and local files (shown in File Explorer,
see [Links to local files](#links-to-local-files)). See [Privacy and security](privacy-and-security.md).

### Following links

- **In the editor**, **Ctrl+click** follows a `[[note link]]` (creating the note if it doesn't exist yet),
  a web, e-mail or Zotero link, a local file link, or a `#tag` (which lists the notes with that tag).
  Hover over the text and a tooltip says what the click will do. A plain click just places the caret, so
  you can still edit link text.
- **In the preview**, a normal click follows links.

### Links to local files

*Insert ▸ Link to a File…* (or the folder button on the toolbar) lets you pick a file and inserts a link
such as `[report.pdf](file:///C:/Users/me/Documents/report.pdf)`. Dragging a file that isn't an image into
the note text does the same. The file is linked where it is; nothing is copied into the vault.

Clicking the link in the preview, or Ctrl+clicking it in the editor, opens **File Explorer with the file
selected**. The file itself is never opened or run. Only paths on a local drive are allowed: network
(UNC) paths such as `\\server\share\file.pdf` are refused, because looking them up can send your Windows
credentials to that server.

Every note has:

- a **title** (the large field at the top);
- an **ID**, a timestamp such as `20261027153012`, shown under the title (*More ▸ Copy note ID*);
- optional **tags**, a **source link**, a **picture**, a **mind map** and **flashcards**.

## Links between notes

### Wiki links

Type `[[` and start typing a title: ZettelApp completes it from your notes. Inside a note, these all link:

```markdown
See [[Forgetting curve]].
See [[20261027153012]].              (by ID)
See [[Forgetting curve|the curve]].  (custom link text)
```

Ctrl+K (*Insert ▸ Link to Note…*) opens a picker that searches titles and text and lets you choose the
link type. A link to a title that doesn't exist yet is shown in grey in the preview; click it to create
that note. When you later create or rename a note, links that mention its title are updated.

### Typed links

Links can say **how** two notes relate. Put the link type in front of the link, followed by `::`:

```markdown
supports:: [[Forgetting curve]]
contradicts:: [[Rereading notes]]
part_of:: [[Zettelkasten method]]
```

The built-in link types are:

| Type | Name | Reverse name | Directed | Line | Arrow tip |
|---|---|---|---|---|---|
| `related` | Related to | Related to | no | solid, grey | none |
| `supports` | Supports | Supported by | yes | dashed, green | filled triangle |
| `contradicts` | Contradicts | Contradicts | no | dotted, red | none |
| `extends` | Extends | Extended by | yes | dash-dot, blue | filled triangle |
| `example` | Example of | Has example | yes | dash-dot-dot, amber | circle |
| `part_of` | Part of | Contains | yes | long dash, purple | diamond |
| `cites` | Cites | Cited by | yes | solid, teal | open arrow |

These are the looks of a new vault; you can change them (see below). A vault made with an earlier version
keeps the lines it had.

A plain `[[link]]` is *Related to*.

### Directed and undirected links

A **directed** type reads differently from each side. If note A *supports* note B, then B's backlinks
show A as *Supported by*. Directed links get arrow tips in the graph and stay directed in exports.
**Undirected** types such as *Related to* and *Contradicts* read the same both ways.

To flip a directed link created the wrong way round, right-click it in the side panel and choose
**Reverse direction**. Links written in the text are reversed by editing the text.

### Links in the side panel

The side panel lists the note's **Links** (outgoing) and **Backlinks** (incoming), each with its type.

- **Add link…** creates a link without writing it in the text.
- Right-click a link to open the other note, change the link type, reverse its direction, or remove it.
  Links written in the text are removed by editing the text.
- From the note list, right-click another note and choose **Link from the open note as**.

### Your own link types

Add, rename, restyle or remove link types in *Tools ▸ Options ▸ Link types*. Pick a type in the list and
change it beside the list:

- **Name** and **Reverse name**: how the link reads from its source and from its target. The reverse
  name is used only by directed types.
- **Directed**: whether the type reads differently from each side and gets an arrow tip.
- **Colour**: click the colour button to choose any colour.
- **Line**: solid, dashed, dotted, dash-dot, dash-dot-dot or long dash.
- **Arrow tip**: the tip drawn where a directed link arrives: a filled triangle, an open arrow, a
  diamond, a circle or a bar.

The preview shows two notes joined by the link, with its name and how it reads from the other side.
The style is used wherever links appear: the graph, its legend, the side panel, the link picker and
the website, GraphML and Graphviz exports. Give each type its own line as well as its own colour, so
the types stay easy to tell apart for colour-blind readers and on paper. A new type starts with a
colour and a line that few other types use.

In text, use the type's id, shown under the preview (e.g. a type called "Inspired by" becomes
`inspired_by::`). The id is set when the type is created, so renaming a type doesn't break links
written in your notes. Removing one of your own types turns its links into *Related to* links, so
nothing is lost. Built-in types can be renamed and restyled but not removed.

## Tags

Add tags in the tag field under the title (press Enter after each), or write them **in the text** with a
hash sign, like `#welcome` or `#math/algebra`. Tags are lower-case and may be nested with a slash, such as
`math/algebra`. Filtering by `math` also finds notes tagged `math/algebra`.
Use the tag filter above the note list, or type `tag:name` in the search box.

Tags written in the text are real tags, shown as **outlined chips** next to the *Add tag* box. They
disappear when you delete the `#tag` from the text. A `#tag` is ignored inside code, inside link targets
and in `[[#headings]]`. Tags typed in the *Add tag* box are separate: they stay until you remove them with
their ✕. Ctrl+click a `#tag` in the editor to list the notes that have it.

## Source link

The field with the globe icon holds the note's **source**: a web page (`https://…`), an e-mail address,
or a Zotero item (`zotero://select/library/items/…`). The button next to it opens the link. Other kinds of
links are refused. See [Zotero](zotero.md) to create notes straight from your Zotero library.

## Images

Insert images with *Insert ▸ Image…* (Ctrl+Shift+I), by **pasting** from the clipboard, or by
**dragging** image files onto the editor. Supported formats: PNG, JPEG, GIF, WebP and BMP, up to 25 MB.
SVG is refused on purpose, because SVG files can carry scripts.

Images are checked by their content (not their file name), stored once in the vault's `assets` folder
under a name derived from their content, and referenced like this:

```markdown
![Diagram](asset:3f2a9c0b1d4e5f6a7b8c.png)
```

The first image you add to a note becomes its **note picture**. The picture is shown next to the title
and inside the note's circle in the graph. Right-click it to remove it.

## Mind maps

Each note can carry a mind map (the **Mind map** tab, or *Insert ▸ Mind Map*). Branches are coloured
automatically.

| Key | Action |
|---|---|
| Tab | Add a child idea |
| Enter | Add a sibling idea |
| F2 or double-click | Rename |
| Del | Delete the selected idea |
| Arrow keys | Move the selection |
| Mouse wheel / drag | Zoom / pan |

Right-click an idea to **link it to a note**; a linked idea shows a link icon and opens that note.
**From links** builds a mind map from the note's links, grouped by link type, with the linked notes'
own links one level deeper. **Export** saves the map as a PNG or SVG image, or as a FreeMind file
(`.mm`), which FreeMind, Freeplane and XMind can open.

## Flashcards

Flashcards turn notes into review material (see [Review, quizzes and Anki](review-and-anki.md)). There
are two ways to make them:

**In the note text.** These become cards automatically and update as you edit:

```markdown
Q: Who described the forgetting curve?
A: Hermann Ebbinghaus

{{c1::Retrieval practice}} is also called active recall.
```

A question can span several lines until the `A:` line. Any paragraph with `{{c1::…}}` becomes a
**cloze** card, which hides each deletion in turn. `{{c1::text::hint}}` shows a hint instead of `[…]`.

**In the Flashcards tab.** Use *Insert ▸ Flashcard…* (Ctrl+Shift+F) for cards that shouldn't appear in
the note. Cards from the text are marked *from note text* and are edited in the text.

## Search

The search box (Ctrl+F) uses full-text search over titles, text and tags, ignores accents, and matches
word prefixes, so `forget` finds *forgetting*. Add `tag:name` to filter by tag, for example
`memory tag:psychology`. Results are ordered by relevance; without a query, notes follow the chosen sort
order (*Last edited*, *Created*, *Title* or *Most linked*).

## Trash

*Move to Trash* (Ctrl+Delete) hides a note without deleting it. An undo button appears right away, and
the **Trash** button under the note list shows trashed notes: right-click to **Restore** or **Delete
permanently**. **Empty Trash** deletes everything in it after asking. Links to trashed notes are hidden,
and come back when the note is restored.
