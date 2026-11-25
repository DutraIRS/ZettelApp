# Roadmap

Planned work for ZettelApp. What has already shipped is in the [CHANGELOG](CHANGELOG.md).
Suggestions are welcome in [GitHub issues](https://github.com/DutraIRS/ZettelApp/issues).

**Companies can sponsor a specific roadmap item** through [Ko-fi](https://ko-fi.com/dutrairs) or by
getting in touch on [GitHub](https://github.com/DutraIRS/ZettelApp).

## Next

### Android

**In progress** (`android/`): a native Kotlin/Compose app runs ZettelApp's Python core on the
device through [Chaquopy](https://chaquo.com/chaquopy/). It has the note list with search and tag
filter, editing, links, backlinks, flashcards, a graph, Insights, review and `zettelapp://` links.

- [ ] **Open notes in a reading view** first, as the desktop's Reading view.
- [ ] **The Markdown preview**, a force-directed graph and translated screens.
- [ ] **A vault in shared storage**, through the Storage Access Framework.
- [ ] **Semantic search and *Ask your notes*** on the device (they need Android builds of
  onnxruntime and tokenizers), and flashcard export to AnkiDroid.
- [ ] **A signed release** and the Google Play listing.

## Later

- **Sync between devices**: a vault shared between computers without conflicts when it is open on
  two of them, through a change log merged via a folder you already sync, or a self-hosted service.
- **The local language model** (the one semantic search downloads) for link suggestions and *Ask
  your notes*, fully offline, alongside LSA.
- **Zotero**: PDF annotations into literature notes, and group libraries in the reference search.
- **Plugins**: a small extension API for link-suggestion features, exporters and importers.
- **Daily notes and templates.**
- **Mind map to notes**: turn a mind map's ideas into linked notes in one step.
- **Bulk editing**: tag, retype links or export a hand-picked selection of notes.
- **Accessibility**: an audit with Narrator and Orca, and a high-contrast theme.
