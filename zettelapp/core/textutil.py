"""Text processing: normalisation, tokens, wiki links and inline flashcards."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

_STOPWORDS_EN = """
a about above after again against all am an and any are as at be because been
before being below between both but by can could did do does doing down during
each few for from further had has have having he her here hers herself him
himself his how i if in into is it its itself just me more most my myself no nor
not now of off on once only or other our ours ourselves out over own same she
should so some such than that the their theirs them themselves then there these
they this those through to too under until up very was we were what when where
which while who whom why will with would you your yours yourself yourselves also
may might must shall via per etc vs
"""
_STOPWORDS_PT = """
de da do das dos a o as os um uma uns umas e em no na nos nas por para com sem
que se ao aos pela pelo pelas pelos como mais mas ou ja nao sim ser estar foi sao
era isso isto esse essa este esta ele ela eles elas eu tu voce voces nos me te
lhe seu sua seus suas meu minha muito pouco entre sobre ate quando onde qual
quais tambem tem ter
"""
_STOPWORDS_ES = """
el la los las un una unos unas y en del al por para con sin que se lo le les
como mas pero o ya no si es son fue ser estar esto eso este esta ese esa su sus
mi mis muy entre sobre hasta cuando donde cual tambien hay
"""
STOPWORDS = frozenset((_STOPWORDS_EN + _STOPWORDS_PT + _STOPWORDS_ES).split())

WORD_RE = re.compile(r"[^\W_]+", re.UNICODE)


def fold(text: str) -> str:
    """Case-fold and strip accents so "Informação" matches "informacao"."""
    decomposed = unicodedata.normalize("NFKD", text or "")
    return "".join(c for c in decomposed if not unicodedata.combining(c)).casefold()


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", fold(text)).strip()


def tokenize(text: str) -> list[str]:
    return [
        t
        for t in WORD_RE.findall(fold(text))
        if len(t) > 1 and not t.isdigit() and t not in STOPWORDS
    ]


# --- markdown helpers -------------------------------------------------------

_MD_NOISE = [
    (re.compile(r"```.*?```", re.S), " "),
    (re.compile(r"!\[[^\]]*\]\([^)]*\)"), " "),
    (re.compile(r"\[([^\]]*)\]\([^)]*\)"), r"\1"),
    (re.compile(r"\[\[([^\]|]*)(?:\|([^\]]*))?\]\]"), lambda m: m.group(2) or m.group(1)),
    (re.compile(r"\{\{c\d+::(.*?)(?:::[^}]*)?\}\}"), r"\1"),
    (re.compile(r"^(\s{0,3}(?:[-*+]|\d+[.)])\s+)\[[ xX]\]\s*", re.M), r"\1"),
    (re.compile(r"^\s{0,3}(?:#{1,6}|>|[-*+]|\d+[.)])\s+", re.M), ""),
    (re.compile(r"[*_`~]+"), ""),
]


def strip_markdown(text: str) -> str:
    for pattern, repl in _MD_NOISE:
        text = pattern.sub(repl, text or "")
    return re.sub(r"\s+", " ", text).strip()


def snippet(body: str, length: int = 140) -> str:
    plain = strip_markdown(body)
    if len(plain) <= length:
        return plain
    return plain[: length - 1].rsplit(" ", 1)[0] + "…"


# --- checklists -------------------------------------------------------------

TASK_RE = re.compile(r"^[ \t]*(?:[-*+]|\d+[.)])[ \t]+(\[([ xX])\])(?=[ \t]|$)")


def find_tasks(text: str) -> list[tuple[int, int, bool]]:
    """Checklist items ("- [ ] item", "- [x] item") outside code blocks, in order, as
    (start, end, checked) where start:end spans the "[ ]" or "[x]" itself."""
    found: list[tuple[int, int, bool]] = []
    in_fence = False
    offset = 0
    for line in (text or "").split("\n"):
        stripped = line.lstrip()
        if stripped.startswith(("```", "~~~")):
            in_fence = not in_fence
        elif not in_fence:
            m = TASK_RE.match(line)
            if m:
                found.append((offset + m.start(1), offset + m.end(1), m.group(2) != " "))
        offset += len(line) + 1
    return found


def toggle_task(text: str, index: int) -> str:
    """*text* with the checklist item number *index* (see find_tasks) ticked or unticked."""
    tasks = find_tasks(text)
    if not 0 <= index < len(tasks):
        return text
    start, end, checked = tasks[index]
    return text[:start] + ("[ ]" if checked else "[x]") + text[end:]


# --- LaTeX ------------------------------------------------------------------

MATH_RE = re.compile(
    r"\$\$(?P<display>[^$]+?)\$\$"
    r"|(?<![\\$\w])\$(?P<inline>[^\s$](?:[^$\n]*?[^\s$\\])?)\$(?!\d)"
)


# --- wiki links -------------------------------------------------------------

WIKILINK_RE = re.compile(
    r"(?:(?P<type>[A-Za-z][\w-]{0,30})::[ \t]*)?"
    r"\[\[(?P<target>[^\[\]|#\n]{1,200})(?:#[^\[\]|\n]*)?(?:\|(?P<alias>[^\[\]\n]{0,200}))?\]\]"
)


@dataclass(frozen=True)
class WikiLink:
    target: str
    alias: str | None
    link_type: str | None
    start: int
    end: int


def slugify_type(name: str) -> str:
    return re.sub(r"[^a-z0-9_]+", "_", fold(name).replace("-", "_")).strip("_")


def find_wikilinks(text: str) -> list[WikiLink]:
    links = []
    for m in WIKILINK_RE.finditer(text or ""):
        link_type = slugify_type(m.group("type")) if m.group("type") else None
        links.append(
            WikiLink(m.group("target").strip(), m.group("alias"), link_type, m.start(), m.end())
        )
    return links


# --- inline flashcards ------------------------------------------------------

CLOZE_RE = re.compile(r"\{\{c(\d+)::(.+?)(?:::([^}]*))?\}\}", re.S)
_Q_RE = re.compile(r"^\s*(?:Q|Question)\s*:\s*(.*)$", re.I)
_A_RE = re.compile(r"^\s*(?:A|Answer)\s*:\s*(.*)$", re.I)


@dataclass(frozen=True)
class InlineCard:
    front: str
    back: str
    kind: str  # "basic" or "cloze"


def extract_inline_cards(body: str) -> list[InlineCard]:
    """Find `Q:`/`A:` pairs and paragraphs containing {{c1::cloze}} deletions."""
    cards: list[InlineCard] = []
    lines = (body or "").splitlines()
    in_fence = False
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("```"):
            in_fence = not in_fence
            i += 1
            continue
        q = None if in_fence else _Q_RE.match(line)
        if not q:
            i += 1
            continue
        question = [q.group(1)]
        i += 1
        while (
            i < len(lines)
            and lines[i].strip()
            and not _A_RE.match(lines[i])
            and not _Q_RE.match(lines[i])
        ):
            question.append(lines[i])
            i += 1
        a_match = _A_RE.match(lines[i]) if i < len(lines) else None
        if a_match:
            answer = [a_match.group(1)]
            i += 1
            while i < len(lines) and lines[i].strip() and not _Q_RE.match(lines[i]):
                answer.append(lines[i])
                i += 1
            front, back = "\n".join(question).strip(), "\n".join(answer).strip()
            if front and back:
                cards.append(InlineCard(front, back, "basic"))

    for paragraph in re.split(r"\n\s*\n", body or ""):
        if CLOZE_RE.search(paragraph) and not paragraph.lstrip().startswith("```"):
            cards.append(InlineCard(paragraph.strip(), "", "cloze"))
    return cards


def cloze_front(text: str, number: int | None = None) -> str:
    """Hide cloze deletions ("[...]" or the hint) for quizzing."""

    def repl(m: re.Match) -> str:
        if number is not None and int(m.group(1)) != number:
            return m.group(2)
        return f"[{m.group(3)}]" if m.group(3) else "[…]"

    return CLOZE_RE.sub(repl, text)


def cloze_back(text: str) -> str:
    return CLOZE_RE.sub(lambda m: m.group(2), text)


def cloze_numbers(text: str) -> list[int]:
    return sorted({int(m.group(1)) for m in CLOZE_RE.finditer(text)})


HASHTAG_RE = re.compile(r"(?<![\w#&/])#([^\W\d_][\w/-]{0,60})", re.UNICODE)
_CODE_RE = re.compile(r"```.*?```|~~~.*?~~~|`[^`\n]*`", re.S)
_WIKI_SPAN_RE = re.compile(r"\[\[[^\]\n]*\]\]")
_LINK_TARGET_RE = re.compile(r"\]\([^)\n]*\)")


def normalize_tag(tag: str) -> str:
    tag = re.sub(r"\s+", "-", (tag or "").strip().lstrip("#"))
    return re.sub(r"[^\w/-]", "", tag)[:60].lower()


def extract_hashtags(text: str) -> list[str]:
    """Tags written as #tag in the text, ignoring code, link targets and [[#headings]]."""
    text = _CODE_RE.sub(" ", text or "")
    text = _WIKI_SPAN_RE.sub(" ", text)
    text = _LINK_TARGET_RE.sub("]", text)
    tags = {normalize_tag(m).strip("/-") for m in HASHTAG_RE.findall(text)}
    return sorted(t for t in tags if t)
