# Review, quizzes and Anki

Notes are meant to be thought with, and remembering them helps. ZettelApp turns notes into
[flashcards](notes-and-links.md#flashcards) and lets you review them inside the app or in Anki.

## Spaced repetition

The **Review** page (Ctrl+4) shows how many cards are **due today**. **Start review** goes through them:

1. Read the question and try to recall the answer.
2. Press **Space** (or *Show answer*).
3. Grade yourself: **Again (1)**, **Hard (2)**, **Good (3)** or **Easy (4)**. Hover a button to see when
   the card would come back.

Scheduling uses the **SM-2** algorithm (the SuperMemo algorithm Anki grew from):

- New cards come back after 1 day, then 6 days, then at intervals that grow by the card's *ease factor*
  (2.5 at first).
- *Again* resets the card to 1 day and lowers its ease. *Hard* shortens the next interval, and *Easy*
  lengthens it.

Cloze cards produce one review per deletion (`{{c1::…}}`, `{{c2::…}}`, …). Each question shows a
**From:** link to its note.

## Quizzes

**Practice quiz** builds a quiz from a scope: the entire collection, the open note and its linked notes
(with a depth), or the notes with a tag. Choose a style and the number of questions:

| Style | How it works |
|---|---|
| **Flashcards (spaced repetition)** | Like a review, and your grades update the schedule. |
| **Multiple choice** | Pick the right answer among four. The wrong answers are other cards' answers of similar length, so they're plausible. Keys 1–4 choose. |
| **Type the answer** | Type the answer and press Enter. It is graded by edit (Levenshtein) similarity, ignoring case, accents and formatting: 85% or more counts as correct, and 60% or more as *almost*, so small typos don't cost you. |
| **Name that note** | Shows a note's text with the words of its title blanked out; pick the right title. The wrong options are the **most similar notes** (by TF-IDF), so you learn to tell related ideas apart. No flashcards needed. |

*Tools ▸ Quiz on This Note's Neighbourhood* starts a quiz on the open note and the notes within two links
of it. Right-click a note in the graph for the same.

## Anki

ZettelApp works with [Anki](https://apps.ankiweb.net/) in two ways. Both use two note types, **ZettelApp
Basic** and **ZettelApp Cloze**, with these fields:

- *Front* and *Back* (or *Text* and *Extra* for cloze cards), rendered from Markdown;
- *Source*, a link back to the note;
- *ZettelID* and *CardKey*.

Your note's tags become Anki tags (nested tags become `parent::child`), plus `zettelapp`. Images in cards
are included as media.

### Sync with AnkiConnect

1. In Anki, install the **AnkiConnect** add-on (*Tools ▸ Add-ons ▸ Get Add-ons…*, code **2055492159**)
   and restart Anki.
2. With Anki running, open **Review** in ZettelApp, choose the deck name and scope, and press
   **Sync to Anki** (or *Tools ▸ Sync with Anki*). *Check connection* tests the link.

ZettelApp remembers which Anki note belongs to each card. Syncing again **updates** cards instead of
adding duplicates, and a card can be found again by its *CardKey* even if that memory was lost. Cards
you delete in ZettelApp are not deleted from Anki.

ZettelApp only ever talks to AnkiConnect on this computer (`127.0.0.1`, port 8765 by default, changeable in
*Options ▸ Anki*).

### Export a deck (.apkg)

**Export deck (.apkg)…** (or *File ▸ Export…* with the *Anki deck* format) writes a package that you
import with *File ▸ Import* in Anki. No add-on is needed. Note types, the deck and each card's identity are
stable, so importing a newer export **updates** the cards you imported before.

### From Anki back to your notes

Every card's **Source** is a `zettelapp://note/<id>` link. Click it in Anki and the note opens in
ZettelApp. The installer sets this up. With the portable version, use *Options ▸ Windows integration ▸
Register links*. The link handler only accepts *open note* links; see
[Privacy and security](privacy-and-security.md).
