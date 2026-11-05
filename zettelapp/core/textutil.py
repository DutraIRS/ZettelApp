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


def _cut(plain: str, length: int) -> str:
    return plain if len(plain) <= length else plain[: length - 1].rsplit(" ", 1)[0] + "…"


def snippet(body: str, length: int = 140) -> str:
    return _cut(strip_markdown(body), length)


def snippet_around(body: str, words: str, length: int = 140) -> str:
    """Like snippet(), but moved along the text to show the first of the words if it would
    otherwise be cut off."""
    plain = strip_markdown(body)
    found = re.findall(r"\w+", words)
    match = re.search("|".join(map(re.escape, found)), plain, re.IGNORECASE) if found else None
    if match is None or match.end() < length:
        return _cut(plain, length)
    around = max(0, match.start() - length // 3)
    start = plain.rfind(" ", max(0, around - 20), around) + 1 or around  # at a word if possible
    return "…" + _cut(plain[start:], length)


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


# --- bold and italics -------------------------------------------------------

# Where * and _ mean nothing: a link's address and an <autolink>.
_LINK_ADDRESS_RE = re.compile(r"\]\([^)\n]*\)|<[A-Za-z][\w+.-]{1,31}:[^\s<>]*>")


def code_spans(line: str) -> list[tuple[int, int]]:
    """Where the `code` in one line is, backticks included: a run of backticks up to the
    next run of the same length, as CommonMark reads them."""
    runs = [(m.start(), m.end()) for m in re.finditer(r"`+", line)]
    spans, i = [], 0
    while i < len(runs):
        start, end = runs[i]
        i += 1
        for j in range(i, len(runs)):
            if runs[j][1] - runs[j][0] == end - start:
                spans.append((start, runs[j][1]))
                i = j + 1
                break
    return spans


@dataclass
class _Markers:
    char: str
    pos: int  # where the markers not paired yet start
    count: int  # how many are not paired yet
    size: int  # how many the run had
    can_open: bool
    can_close: bool


def _punctuation(ch: str) -> bool:
    return unicodedata.category(ch)[0] in "PS"


def _pairs(opener: _Markers, closer: _Markers) -> bool:
    if opener.char != closer.char:
        return False
    # CommonMark's rule of three: in *a**b* the ** neither opens nor closes.
    if (opener.can_close or closer.can_open) and (opener.size + closer.size) % 3 == 0:
        return opener.size % 3 == 0 and closer.size % 3 == 0
    return True


def emphasis_spans(line: str) -> list[tuple[int, int, bool]]:
    """Each *italic* or **bold** stretch of one line of Markdown, as (start, end, bold) with its
    markers included. The markers pair up the way CommonMark (and so the preview) pairs them:
    *a **b** c* nests, ***both*** is both, and snake_case_names or 2 * 3 stay plain. Code,
    formulas, [[links]] and link addresses are left alone."""
    if "*" not in line and "_" not in line:
        return []
    blocked = bytearray(len(line))
    covered = [*code_spans(line)]
    for pattern in (MATH_RE, WIKILINK_RE, _LINK_ADDRESS_RE):
        covered += [m.span() for m in pattern.finditer(line)]
    for start, end in covered:
        blocked[start:end] = b"\x01" * (end - start)
    runs: list[_Markers] = []
    i, n = 0, len(line)
    while i < n:
        ch = line[i]
        if blocked[i]:
            i += 1
        elif ch == "\\":  # \* is a plain asterisk
            i += 2
        elif ch in "*_":
            j = i
            while j < n and line[j] == ch and not blocked[j]:
                j += 1
            before = line[i - 1] if i else " "
            after = line[j] if j < n else " "
            left = not after.isspace() and (
                not _punctuation(after) or before.isspace() or _punctuation(before)
            )
            right = not before.isspace() and (
                not _punctuation(before) or after.isspace() or _punctuation(after)
            )
            if ch == "*":
                can_open, can_close = left, right
            else:  # _ inside a word is just an underscore
                can_open = left and (not right or _punctuation(before))
                can_close = right and (not left or _punctuation(after))
            if can_open or can_close:
                runs.append(_Markers(ch, i, j - i, j - i, can_open, can_close))
            i = j
        else:
            i += 1
    spans: list[tuple[int, int, bool]] = []
    openers: list[_Markers] = []
    for run in runs:
        while run.can_close and run.count:
            k = len(openers) - 1
            while k >= 0 and not _pairs(openers[k], run):
                k -= 1
            if k < 0:
                break
            opener = openers[k]
            used = 2 if opener.count >= 2 and run.count >= 2 else 1
            opener.count -= used
            spans.append((opener.pos + opener.count, run.pos + used, used == 2))
            run.pos += used
            run.count -= used
            del openers[k + 1 :]  # markers between the pair stay plain text
            if not opener.count:
                del openers[k]
        if run.can_open and run.count:
            openers.append(run)
    return spans


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
