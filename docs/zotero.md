# Zotero

ZettelApp connects to [Zotero](https://www.zotero.org/), the free reference manager, so you can cite
references in your notes and write **literature notes** linked to the item, and its PDF, in your library.

## Set up

1. Use **Zotero 7 or later** and keep it running.
2. In Zotero, open *Settings ▸ Advanced* and turn on **"Allow other applications on this computer to
   communicate with Zotero"**.
3. In ZettelApp, *Tools ▸ Options ▸ Zotero ▸ Test connection* should say *Connected to Zotero*.

ZettelApp reads your library through Zotero's **local API** on this computer (`127.0.0.1`, port 23119 by
default). It only reads: it never changes your Zotero library, and nothing goes over the internet.
Your personal library (*My Library*) is searched; group libraries are not, yet.

## Cite a reference

*Insert ▸ Zotero Reference…*, or the books button in the editor toolbar, opens a search box. Type part of
a title, an author or a year. With an empty search, your most recently modified items are listed. Select
an item to see its details, then:

- **Insert citation** (or double-click) adds an author–year citation that opens the item in Zotero:

  ```markdown
  [Ebbinghaus (1885)](zotero://select/library/items/ABCD2345)
  ```

- **New literature note** creates a note for the item, with:
  - the item's title;
  - a reference line (authors, year, title, publication, DOI);
  - links to *Open in Zotero*, *Open PDF* (when the item has a PDF attachment) and the DOI;
  - the abstract;
  - *Key ideas* and *My thoughts* sections to fill in;
  - the tag `literature` plus the item's Zotero tags;
  - the Zotero item as the note's **source link**.

Literature notes are the classic Zettelkasten bridge between reading and your own permanent notes: write
the key ideas in your own words, then link them to the notes they support, extend or contradict.

## Zotero links

Clicking a Zotero link in a note opens Zotero at the item, or opens the PDF in Zotero's reader. For safety,
ZettelApp only follows two kinds of Zotero link and refuses any other `zotero://` address:

```text
zotero://select/library/items/<KEY>
zotero://open-pdf/library/items/<KEY>?page=<N>
```

Group-library links (`zotero://select/groups/<ID>/items/<KEY>`) are accepted too. You can also paste a
Zotero link into a note's **source link** field. In Zotero, right-click an item and copy its link (or use
an add-on such as Zutilo), then paste it.

## Troubleshooting

| Message | What to do |
|---|---|
| *Could not reach Zotero* | Start Zotero 7 or later. Check the port in *Options ▸ Zotero* (default 23119). |
| *Zotero refused the request* | Turn on the *Allow other applications…* setting (step 2 above). |
| *This Zotero version has no local API* | Update Zotero to version 7 or later. |
