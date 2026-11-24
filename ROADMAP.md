# Roadmap

Planned work for ZettelApp. What has already shipped is in the [CHANGELOG](CHANGELOG.md).
Suggestions are welcome in [GitHub issues](https://github.com/DutraIRS/ZettelApp/issues).

**Companies can sponsor a specific roadmap item** through [Ko-fi](https://ko-fi.com/dutrairs) or by
getting in touch on [GitHub](https://github.com/DutraIRS/ZettelApp).

## Next

### Ask your notes

- [ ] **Neighbours as context**: send the open note's *k*-hop neighbours (all notes within *k* links,
  *k* configurable) instead of the most related notes.
- [ ] **Review before sending**: a checklist of the notes about to be sent, to untick any first.

### Preview

- [ ] **Text options**: line breaks (a single line break starts a new line, or lines join into one
  paragraph as in standard Markdown), alignment (start or justified), line spacing and paragraph
  spacing. Markdown is parsed by markdown-it-py; the preview's layout is ZettelApp's own.

### Insights

- [ ] **Network metrics**: the degree distribution (and how close it is to a power law), hubs by
  degree, betweenness and PageRank, and the clustering coefficient, to see which notes hold the
  network together.

### Graph

- [ ] **Arrow tips at each end**: a directed link type can have a different tip at each end; an
  undirected one can have tips too, the same at both ends.
- [ ] **Diffusion**: pick a note and a measure (link distance, or links weighted by similarity) and
  watch its influence spread through the network.

### Website

- [ ] **The mobile layout**: the site is hard to use on a phone.
- [ ] **A Google Play link**, ready for when the Android app is listed.

### Linux

- [ ] **Snap Store**: check that `snap info zettelapp` finds 1.4.0 and `sudo snap install zettelapp`
  works, and ask on the Snapcraft forum for `password-manager-service` to connect automatically
  (until then API keys stay in memory unless the user runs
  `sudo snap connect zettelapp:password-manager-service`).
- [ ] **What only a real desktop can confirm** (alarm clicks, KWallet, fractional scaling, input
  methods, Orca) is listed in [PLATFORM_CHECKS.md](PLATFORM_CHECKS.md).

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
