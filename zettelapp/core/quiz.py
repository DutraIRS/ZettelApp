"""Quizzes and spaced repetition (SM-2)."""

from __future__ import annotations

import random
import re
from collections.abc import Sequence
from dataclasses import asdict, dataclass, field
from datetime import date, timedelta

import numpy as np

from zettelapp.core.models import Flashcard, Note, ReviewState
from zettelapp.core.similarity import SemanticIndex, levenshtein_similarity
from zettelapp.core.textutil import (
    CLOZE_RE,
    cloze_back,
    cloze_front,
    cloze_numbers,
    fold,
    normalize,
    strip_markdown,
    tokenize,
)

GRADES = {"again": 1, "hard": 3, "good": 4, "easy": 5}

MODES = {
    "flashcards": "Flashcards (spaced repetition)",
    "choice": "Multiple choice",
    "typed": "Type the answer",
    "notes": "Name that note",
}


def schedule(state: ReviewState, grade: str, today: date | None = None) -> ReviewState:
    """SuperMemo-2 scheduling with Anki-style grade buttons."""
    q = GRADES[grade]
    today = today or date.today()
    s = ReviewState(state.card_id, state.ease, state.interval, state.reps, state.lapses, state.due)
    if q < 3:
        s.reps = 0
        s.interval = 1
        s.lapses += 1
    else:
        if s.reps == 0:
            s.interval = 1
        elif s.reps == 1:
            s.interval = 6
        else:
            s.interval = max(1, round(s.interval * s.ease))
        if grade == "hard":
            s.interval = max(1, round(s.interval * 0.8))
        elif grade == "easy":
            s.interval = max(s.interval + 1, round(s.interval * 1.3))
        s.reps += 1
    s.ease = max(1.3, s.ease + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02)))
    s.due = (today + timedelta(days=s.interval)).isoformat()
    return s


@dataclass
class Question:
    kind: str  # flashcard | choice | typed
    prompt: str  # Markdown
    answer: str  # Markdown
    note_id: str
    note_title: str
    card_id: int | None = None
    choices: list[str] = field(default_factory=list)
    correct: int = -1

    def to_dict(self) -> dict:
        return asdict(self)


def grade_typed(given: str, expected: str) -> tuple[float, str]:
    """Fuzzy-grade a typed answer: returns (similarity, verdict)."""
    a = normalize(strip_markdown(given))
    b = normalize(strip_markdown(expected))
    if not a:
        return 0.0, "wrong"
    score = 1.0 if a == b else levenshtein_similarity(a, b)
    if score >= 0.85:
        return score, "correct"
    if score >= 0.6:
        return score, "close"
    return score, "wrong"


def _card_items(card: Flashcard) -> list[tuple[str, str, str]]:
    """(prompt, answer, short answer) triples; cloze cards yield one per deletion."""
    if card.kind == "cloze":
        items = []
        for number in cloze_numbers(card.front):
            answers = [
                m.group(2) for m in CLOZE_RE.finditer(card.front) if int(m.group(1)) == number
            ]
            short = ", ".join(answers)
            items.append((cloze_front(card.front, number), cloze_back(card.front), short))
        return items
    return [(card.front, card.back, card.back)]


def _distractors(
    correct: str, pool: Sequence[str], rng: random.Random, n: int = 3, by_length: bool = True
) -> list[str]:
    seen = {fold(correct.strip())}
    options = []
    for candidate in pool:
        key = fold(candidate.strip())
        if candidate.strip() and key not in seen:
            seen.add(key)
            options.append(candidate)
    if by_length:
        # Prefer distractors of similar length, which are harder to rule out.
        options.sort(key=lambda o: abs(len(o) - len(correct)) + rng.random() * 20)
    return options[:n]


def build_quiz(
    mode: str,
    notes: dict[str, Note],
    cards: Sequence[Flashcard],
    count: int = 20,
    seed: int | None = None,
) -> list[Question]:
    rng = random.Random(seed)
    questions: list[Question] = []
    if mode == "notes":
        return _note_questions(notes, count, rng)
    items = []
    for card in cards:
        note = notes.get(card.note_id)
        if note is None:
            continue
        for prompt, answer, short in _card_items(card):
            items.append((card, note, prompt, answer, short))
    rng.shuffle(items)
    pool = [short for *_, short in items]
    for card, note, prompt, answer, short in items[:count]:
        if mode == "choice":
            wrong = _distractors(short, pool, rng)
            if len(wrong) < 1:
                continue
            choices = wrong + [short]
            rng.shuffle(choices)
            questions.append(
                Question(
                    "choice",
                    prompt,
                    answer,
                    note.id,
                    note.display_title,
                    card.id,
                    choices,
                    choices.index(short),
                )
            )
        elif mode == "typed":
            questions.append(Question("typed", prompt, short, note.id, note.display_title, card.id))
        else:
            questions.append(
                Question("flashcard", prompt, answer, note.id, note.display_title, card.id)
            )
    return questions


def _mask_title(body: str, title: str) -> str:
    text = strip_markdown(body)
    for word in sorted({w for w in re.findall(r"\w+", title) if len(w) > 3}, key=len, reverse=True):
        text = re.sub(rf"(?i)\b{re.escape(word)}\b", "▁▁▁", text)
    return text[:600] + ("…" if len(text) > 600 else "")


def _note_questions(notes: dict[str, Note], count: int, rng: random.Random) -> list[Question]:
    usable = [n for n in notes.values() if n.title.strip() and len(strip_markdown(n.body)) >= 40]
    if len(usable) < 2:
        return []
    index = SemanticIndex({n.id: tokenize(n.title) + tokenize(n.body) for n in usable}, lsa_dims=32)
    titles = {n.id: n.display_title for n in usable}
    rng.shuffle(usable)
    questions = []
    for note in usable[:count]:
        i = index.position[note.id]
        sims = index.cosine_all(index.vectors[i])
        sims[i] = -1
        # The most similar notes make the hardest (and most instructive) distractors.
        nearest = [index.ids[j] for j in np.argsort(-sims)[:6] if sims[j] >= 0]
        wrong = _distractors(note.display_title, [titles[j] for j in nearest], rng, by_length=False)
        if len(wrong) < 3:
            others = [t for t in titles.values() if t not in wrong]
            wrong += _distractors(note.display_title, rng.sample(others, min(len(others), 8)), rng)[
                : 3 - len(wrong)
            ]
        choices = wrong + [note.display_title]
        rng.shuffle(choices)
        questions.append(
            Question(
                "choice",
                "Which note is this?\n\n> " + _mask_title(note.body, note.title),
                note.display_title,
                note.id,
                note.display_title,
                None,
                choices,
                choices.index(note.display_title),
            )
        )
    return questions
