# Notes and links

## Writing notes

Notes are written in **Markdown**: `**bold**`, `*italic*`, `# headings`, lists, `> quotes`,
`` `code` ``, fenced code blocks, tables and `~~strikethrough~~`. The toolbar above the editor inserts the
common ones, and Ctrl+B / Ctrl+I work as usual. Lists continue when you press Enter.

The editor has three modes (Ctrl+E cycles through them): **Edit**, **Split** (text and preview side by
side) and **Preview**.

For safety, raw HTML in a note is shown as text and never rendered. Links in the preview open only web
pages (`http`, `https`), e-mail (`mailto`) and Zotero items. See [Privacy and security](privacy-and-security.md).

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

| Type | Name | Reverse name | Directed |
|---|---|---|---|
| `related` | Related to | Related to | no |
| `supports` | Supports | Supported by | yes |
| `contradicts` | Contradicts | Contradicts | no |
| `extends` | Extends | Extended by | yes |
| `example` | Example of | Has example | yes |
| `part_of` | Part of | Contains | yes |
| `cites` | Cites | Cited by | yes |

A plain `[[link]]` is *Related to*.

### Directed and undirected links

A **directed** type reads differently from each side. If note A *supports* note B, then B's backlinks
show A as *Supported by*. Directed links get arrowheads in the graph and stay directed in exports.
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

Add, rename, recolour or remove link types in *Tools ▸ Options ▸ Link types*. Each type has a name, a
reverse name, a colour and a *Directed* switch. In text, use the type's id (shown in the `type:: [[…]]`
form, e.g. a type called "Inspired by" becomes `inspired_by::`). Removing a type turns its links into
*Related to* links, so nothing is lost. *Related to* itself can't be removed.

## Tags

Add tags in the tag field under the title (press Enter after each). Tags are lower-case and may be
nested with a slash, such as `math/algebra`. Filtering by `math` also finds notes tagged `math/algebra`.
Use the tag filter above the note list, or type `tag:name` in the search box.

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
