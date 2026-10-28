"""A small, realistic demo Zettelkasten used for screenshots, demos and UI tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from zettelapp.core.models import Flashcard
from zettelapp.core.storage import Vault

NOTES = [
    # (title, tags, body)
    ("Spaced repetition", ["learning", "memory"],
     "Reviewing material at **increasing intervals** moves it into long-term memory with far less effort than "
     "massed practice. It works because each retrieval happens just before forgetting.\n\n"
     "supports:: [[Forgetting curve]]\n\nQ: Why space reviews out?\nA: Each effortful retrieval just before "
     "forgetting strengthens the memory more than an easy one."),
    ("Forgetting curve", ["memory", "psychology"],
     "Ebbinghaus showed that retention decays roughly exponentially unless information is reviewed. The curve "
     "flattens after every successful review.\n\n{{c1::Hermann Ebbinghaus}} measured it with nonsense syllables."),
    ("Active recall", ["learning", "memory"],
     "Testing yourself (retrieval practice) produces stronger memories than rereading. Closing the book and "
     "explaining an idea is a test.\n\nextends:: [[Spaced repetition]]"),
    ("Interleaving", ["learning"],
     "Mixing different kinds of problems during practice feels harder but improves transfer, because the learner "
     "must choose a strategy each time.\n\nsupports:: [[Desirable difficulties]]"),
    ("Desirable difficulties", ["learning", "psychology"],
     "Bjork's term for conditions that slow apparent progress but improve long-term retention: spacing, "
     "interleaving, testing and varying conditions."),
    ("Illusion of competence", ["learning", "psychology"],
     "Rereading and highlighting create fluency that we mistake for mastery. contradicts:: [[Rereading notes]]"),
    ("Rereading notes", ["learning"],
     "Rereading feels productive but mostly builds recognition, not recall."),
    ("Elaborative interrogation", ["learning"],
     "Asking *why* a fact is true connects it to prior knowledge and improves retention. example:: [[Feynman technique]]"),
    ("Feynman technique", ["learning", "writing"],
     "Explain the idea in plain words as if teaching a beginner; gaps in the explanation reveal gaps in understanding."),
    ("Atomic notes", ["zettelkasten", "writing"],
     "One idea per note. Atomic notes can be linked and reused in many contexts, which is what makes a "
     "Zettelkasten generative.\n\npart_of:: [[Zettelkasten method]]"),
    ("Zettelkasten method", ["zettelkasten"],
     "Niklas Luhmann's slip-box: a network of small notes with unique IDs and explicit links. Thinking happens "
     "by following and creating links."),
    ("Linking notes", ["zettelkasten", "writing"],
     "A link should say *why* two ideas belong together. Typed links (supports, contradicts, extends) make that "
     "explicit.\n\npart_of:: [[Zettelkasten method]]"),
    ("Literature notes", ["zettelkasten", "reading"],
     "Short notes in your own words about a source, written while reading. They feed permanent notes.\n\n"
     "part_of:: [[Zettelkasten method]]"),
    ("Permanent notes", ["zettelkasten", "writing"],
     "Self-contained notes written for your future self, linked into the network.\n\nextends:: [[Literature notes]]"),
    ("Writing is thinking", ["writing"],
     "Writing externalises thought, which lets us examine and improve it. supports:: [[Feynman technique]]"),
    ("Progressive summarization", ["writing", "reading"],
     "Highlight in layers: bold the key passages, then highlight the best of those, so notes stay skimmable."),
    ("Deep work", ["productivity"],
     "Long stretches of distraction-free concentration produce more valuable output than fragmented time."),
    ("Attention residue", ["productivity", "psychology"],
     "Switching tasks leaves part of attention on the previous task, which lowers performance. supports:: [[Deep work]]"),
    ("Timeboxing", ["productivity"],
     "Assign a fixed block of time to a task; the boundary limits perfectionism and protects focus."),
    ("Pomodoro technique", ["productivity"],
     "Work for 25 minutes, then take a short break. example:: [[Timeboxing]]"),
    ("Flow state", ["productivity", "psychology"],
     "Full immersion in a challenging task matched to one's skill. related:: [[Deep work]]"),
    ("Falsifiability", ["science", "philosophy"],
     "Popper: a theory is scientific if some observation could prove it wrong."),
    ("Confirmation bias", ["psychology", "science"],
     "We favour evidence that confirms what we already believe. contradicts:: [[Falsifiability]]"),
    ("Occam's razor", ["science", "philosophy"],
     "Prefer the simplest explanation that accounts for the evidence."),
    ("Bayesian reasoning", ["science", "statistics"],
     "Update beliefs in proportion to the evidence: posterior ∝ likelihood × prior. Naive Bayes classifiers "
     "assume features are independent given the class."),
    ("Base rate fallacy", ["statistics", "psychology"],
     "Ignoring how common something is when judging probabilities. extends:: [[Bayesian reasoning]]"),
    ("Levenshtein distance", ["statistics", "computing"],
     "The minimum number of insertions, deletions and substitutions that turn one string into another."),
    ("Latent semantic analysis", ["computing", "statistics"],
     "Truncated SVD of a term-document matrix: documents that use related words end up close together."),
]

MINDMAP = {
    "text": "Learning that lasts", "children": [
        {"text": "Spacing", "children": [{"text": "Forgetting curve", "children": []},
                                         {"text": "Review schedules", "children": []}]},
        {"text": "Retrieval", "children": [{"text": "Active recall", "children": []},
                                           {"text": "Flashcards", "children": []}]},
        {"text": "Difficulty", "children": [{"text": "Interleaving", "children": []},
                                            {"text": "Varied practice", "children": []}]},
        {"text": "Meaning", "children": [{"text": "Elaboration", "children": []},
                                         {"text": "Explain it simply", "children": []}]},
    ]}


def build_demo(vault: Vault) -> dict[str, str]:
    """Fill *vault* with the demo notes; returns {title: id}."""
    now = datetime.now()
    ids: dict[str, str] = {}
    for i, (title, tags, _) in enumerate(NOTES):
        when = now - timedelta(days=(len(NOTES) - i) * 11, hours=i)
        note = vault.create_note(title=title, tags=tags, note_id=vault.new_note_id(when),
                                 created=when.astimezone(timezone.utc).isoformat(timespec="seconds"))
        ids[title] = note.id
    for title, tags, body in NOTES:
        note = vault.get_note(ids[title])
        note.body = body
        if title == "Spaced repetition":
            note.mindmap = MINDMAP
            note.url = "https://en.wikipedia.org/wiki/Spaced_repetition"
        vault.save_note(note)
    extra = [("Spaced repetition", "Active recall", "related"), ("Deep work", "Flow state", "related"),
             ("Atomic notes", "Linking notes", "supports"), ("Interleaving", "Active recall", "related"),
             ("Bayesian reasoning", "Confirmation bias", "related"), ("Falsifiability", "Occam's razor", "related"),
             ("Latent semantic analysis", "Levenshtein distance", "related"),
             ("Illusion of competence", "Active recall", "supports"), ("Timeboxing", "Deep work", "supports")]
    for a, b, t in extra:
        vault.add_link(ids[a], ids[b], t)
    vault.save_card(Flashcard(None, ids["Active recall"], "What is retrieval practice?",
                              "Recalling information from memory, e.g. by self-testing."))
    vault.save_card(Flashcard(None, ids["Bayesian reasoning"], "Bayes' rule in words",
                              "Posterior is proportional to likelihood times prior."))
    return ids
