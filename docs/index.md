# ZettelApp documentation

ZettelApp is a Zettelkasten for Windows: a network of small notes, each holding one idea, connected by
links that say *how* ideas relate. It suggests links while you write, draws your knowledge as a 2D or 3D
graph, turns notes into flashcards and quizzes, and works with Anki, Zotero and AI assistants.

Everything stays on your computer unless you ask for something that needs the network.

## New here?

- **[What is a Zettelkasten?](what-is-zettelkasten.md)**: the method, where it comes from, and how
  ZettelApp supports it.
- **[Tutorial: your first 30 minutes](tutorial.md)**: a hands-on tour from your first note to the 3D graph.

## Contents

- [Getting started](getting-started.md): install, your first vault and a tour of the window
- [Notes and links](notes-and-links.md): Markdown, wiki links, typed and directed links, tags, images,
  mind maps, flashcards, search and the Trash
- [Link suggestions](link-suggestions.md): how the Naive Bayes suggester works and how to tune it
- [Graph and Insights](graph-and-insights.md): 2D and 3D graphs, clustering, grouping and charts
- [Review, quizzes and Anki](review-and-anki.md): spaced repetition, quiz modes, Anki sync and decks
- [Zotero](zotero.md): cite references and write literature notes
- [Ask your notes (AI)](ai-assistant.md): answers from Claude, OpenAI or Z.ai, grounded in your notes
- [MCP server](mcp-server.md): let Claude Desktop, Claude Code and other MCP clients read your vault
- [MCP API reference](mcp-reference.md): the protocol, tools and errors, for people building MCP clients
- [Export and import](export-import.md): the whole collection or any subgraph, in seven formats
- [Keyboard shortcuts](keyboard-shortcuts.md)
- [Privacy and security](privacy-and-security.md): what leaves your computer, where data lives and
  how ZettelApp protects it
- [Development](development.md): build from source, run the tests, package a release
- [FAQ](faq.md)

## The ideas behind it

A **Zettelkasten** ("slip box") is a note-taking method made famous by the sociologist Niklas Luhmann.
Each note is *atomic* (one idea, in your own words) and has a permanent ID. Value comes from the
connections: when you link a new note to existing ones, you are forced to think about how ideas relate,
and later you can follow those links to find unexpected combinations.

ZettelApp keeps that discipline but removes the friction:

- **IDs are automatic**: every note gets a timestamp ID such as `20261027153012`.
- **Links can say how notes relate**: *supports*, *contradicts*, *extends*, *example of*, *part of*,
  *cites*, or your own link types.
- **Suggestions surface connections you missed**: a classifier compares a note with the rest of your vault
  and learns from the links you accept and dismiss.
- **Review is built in**: notes become flashcards and quizzes, with spaced repetition or Anki.
