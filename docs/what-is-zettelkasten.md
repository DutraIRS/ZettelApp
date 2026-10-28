# What is a Zettelkasten?

A **Zettelkasten** (German for "slip box") is a way of taking notes so that they keep working for you. You
don't file notes away by topic. You write each idea on its own note and **link it** to the notes it
relates to. Over time the links form a network, and following them is how you think, write and discover
connections you didn't plan.

New to the method? Read this page, then try the [tutorial](tutorial.md).

## Where it comes from

The method is closely associated with **Niklas Luhmann (1927–1998)**, a German sociologist best known for
his theory of social systems. Over about four decades he kept a slip box of roughly **90,000 index
cards**. Two features made it more than a card file:

- **Every card had a fixed address**, such as `21/3d7a`. A new card about an existing thought was filed
  right after it, with a branching address (`21/3d7a` → `21/3d7a1`), so lines of thought could grow in
  any direction without reorganising anything.
- **Cards referred to other cards by address.** That turned the box into a web of ideas rather than a
  set of categories.

Luhmann credited the slip box for much of his very large output, about 70 books and close to 400
articles (figures vary by count). He even wrote an essay about working with it as a kind of
conversation partner, *Kommunikation mit Zettelkästen* (1981). His slip box has since been digitised by
the Niklas Luhmann Archive at Bielefeld University.

The method became widely known outside academia through **Sönke Ahrens' *How to Take Smart Notes*
(2017)**, and through communities such as zettelkasten.de.

## The core principles

1. **Atomic notes: one idea per note.** A note should hold a single idea, small enough to link precisely
   and reuse in many contexts. If you can't sum up a note in its title, it probably holds more than one
   idea.
2. **In your own words.** Writing an idea in your own words is where understanding happens. Copying a
   passage feels productive but skips the thinking.
3. **Link every note, with a reason.** When you add a note, ask which existing notes it relates to,
   and *how*. Does it support one, contradict another, give an example of a third? A link with a reason
   is worth far more than a pile of related notes.
4. **Unique, permanent IDs.** Titles change and topics shift, but a note's address shouldn't, so links
   never break.
5. **Let structure emerge.** Instead of deciding categories up front with folders, let clusters of
   ideas form from the links you make. Structure grows from the bottom up.
6. **Structure (hub) notes.** When a topic gets big, write a note that maps it: a short overview that
   links to the key notes in a sensible order. It is an entry point, not a folder.
7. **Review and resurface.** Revisit notes, follow their links, and let old ideas meet new ones. A
   Zettelkasten is a thinking partner only if you keep talking to it.

## Three kinds of notes

Ahrens describes three kinds of notes, each with a different lifespan:

| Kind | What it is | What to do with it |
|---|---|---|
| **Fleeting notes** | Quick reminders of a thought, captured anywhere. | Process them within a day or two, then throw them away. |
| **Literature notes** | Short notes on a source, in your own words, with the reference. | Keep them with the source (for example linked to its Zotero entry). |
| **Permanent notes** | Self-contained notes of your own ideas, written for your future self and linked into the network. | These are the Zettelkasten. Write them carefully and link them. |

## Common pitfalls

- **Collecting instead of thinking.** Saving articles and highlights feels like progress, but a
  Zettelkasten grows only from notes you write and connect. This trap is often called the "collector's
  fallacy".
- **Copying quotes.** A note that is mostly a quotation hasn't been understood yet. Keep the quote in a
  literature note if you need it, and write the permanent note in your words.
- **Over-tagging.** Dozens of tags per note recreate folders under another name. A few broad tags help
  you find notes; links carry the meaning.
- **Orphan notes.** A note with no links is hard to find again and adds nothing to the network. Link
  every new note to at least one existing note.
- **Over-engineering.** The method needs very little: a note, an ID and a link. Start writing; the
  structure comes later.

## How ZettelApp supports the method

| Principle | In ZettelApp |
|---|---|
| Unique, permanent IDs | Every note gets a timestamp ID (such as `20261027153012`) automatically. Link by title or by ID: [wiki links](notes-and-links.md#wiki-links) keep working when titles change. |
| Atomic notes | Fast note creation (Ctrl+N), autosave, and small notes that preview well. |
| Link with a reason | [Typed links](notes-and-links.md#typed-links): `supports:: [[…]]`, *contradicts*, *extends*, *example of*, *part of*, *cites*, or your own. Directed types read naturally from both sides (*Supported by*). |
| Never miss a connection | [Suggested links](link-suggestions.md) compare each note with your vault and learn from what you accept and dismiss. **Backlinks** show who links to a note. |
| Let structure emerge | The [graph](graph-and-insights.md): a **local graph** around any note, and **clusters** that reveal topics you never filed. *Insights* lists **unlinked notes** to fix. |
| Structure notes | Mind maps inside notes, linked to the notes they organise, and *part of* links. |
| Literature notes | [Zotero](zotero.md) integration creates literature notes linked to the item and its PDF. |
| Review and resurface | [Flashcards, spaced repetition and quizzes](review-and-anki.md) built from your notes, or synced to Anki. |
| Keep everything | Notes go to the **Trash**, not straight to deletion, and daily backups keep your history safe. |

Ready to try it? Start the [tutorial](tutorial.md).
