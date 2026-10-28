"""A small LaTeX maths renderer drawn with QPainter (no extra libraries needed).

It covers what note-taking needs: fractions, roots, sub- and superscripts, Greek letters,
big operators with limits, stretchy brackets, accents, matrices, cases and aligned
equations, and the usual symbols. Anything it does not know is shown as typed, in red in
the live preview of the formula dialog, so a typo never loses the formula.
"""

from __future__ import annotations

import base64
import re
from dataclasses import dataclass, replace

from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontMetricsF,
    QImage,
    QPainter,
    QPainterPath,
    QPen,
)

MAX_LATEX = 2000
MAX_DEPTH = 24
SCALE = 2  # drawn at twice the size so it stays sharp on high-DPI screens
FAMILIES = ["Cambria Math", "STIX Two Math", "Times New Roman", "Segoe UI Symbol", "Segoe UI"]
AXIS = 0.25  # height of the fraction bar and minus sign above the baseline, in em

GREEK = {
    "alpha": "α", "beta": "β", "gamma": "γ", "delta": "δ", "epsilon": "ϵ", "varepsilon": "ε",
    "zeta": "ζ", "eta": "η", "theta": "θ", "vartheta": "ϑ", "iota": "ι", "kappa": "κ",
    "lambda": "λ", "mu": "μ", "nu": "ν", "xi": "ξ", "pi": "π", "varpi": "ϖ", "rho": "ρ",
    "varrho": "ϱ", "sigma": "σ", "varsigma": "ς", "tau": "τ", "upsilon": "υ", "phi": "ϕ",
    "varphi": "φ", "chi": "χ", "psi": "ψ", "omega": "ω",
    "Gamma": "Γ", "Delta": "Δ", "Theta": "Θ", "Lambda": "Λ", "Xi": "Ξ", "Pi": "Π",
    "Sigma": "Σ", "Upsilon": "Υ", "Phi": "Φ", "Psi": "Ψ", "Omega": "Ω",
}  # fmt: skip
BINARY = {
    "pm": "±", "mp": "∓", "times": "×", "div": "÷", "cdot": "⋅", "ast": "∗", "star": "⋆",
    "circ": "∘", "bullet": "∙", "cup": "∪", "cap": "∩", "wedge": "∧", "land": "∧",
    "vee": "∨", "lor": "∨", "oplus": "⊕", "otimes": "⊗", "setminus": "∖", "dagger": "†",
}  # fmt: skip
RELATION = {
    "leq": "≤", "le": "≤", "geq": "≥", "ge": "≥", "neq": "≠", "ne": "≠", "approx": "≈",
    "equiv": "≡", "sim": "∼", "simeq": "≃", "cong": "≅", "propto": "∝", "ll": "≪", "gg": "≫",
    "in": "∈", "notin": "∉", "ni": "∋", "subset": "⊂", "supset": "⊃", "subseteq": "⊆",
    "supseteq": "⊇", "perp": "⊥", "parallel": "∥", "mid": "∣", "to": "→",
    "rightarrow": "→", "leftarrow": "←", "gets": "←", "leftrightarrow": "↔",
    "Rightarrow": "⇒", "Leftarrow": "⇐", "Leftrightarrow": "⇔", "implies": "⟹",
    "iff": "⟺", "mapsto": "↦", "uparrow": "↑", "downarrow": "↓", "longrightarrow": "⟶",
    "longleftarrow": "⟵", "vdash": "⊢", "models": "⊨", "colon": ":",
}  # fmt: skip
ORDINARY = {
    "infty": "∞", "partial": "∂", "nabla": "∇", "forall": "∀", "exists": "∃", "nexists": "∄",
    "emptyset": "∅", "varnothing": "∅", "neg": "¬", "lnot": "¬", "hbar": "ℏ", "ell": "ℓ",
    "Re": "ℜ", "Im": "ℑ", "aleph": "ℵ", "angle": "∠", "prime": "′", "ldots": "…",
    "dots": "…", "cdots": "⋯", "vdots": "⋮", "ddots": "⋱", "top": "⊤", "bot": "⊥",
    "triangle": "△", "degree": "°", "ldotp": ".", "surd": "√", "backslash": "\\",
    "lbrace": "{", "rbrace": "}", "langle": "⟨", "rangle": "⟩", "lfloor": "⌊", "rfloor": "⌋",
    "lceil": "⌈", "rceil": "⌉", "vert": "|", "Vert": "‖", "|": "‖",
    "%": "%", "$": "$", "&": "&", "#": "#", "_": "_",
}  # fmt: skip
BIG = {"sum": "∑", "prod": "∏", "coprod": "∐", "int": "∫", "iint": "∬", "iiint": "∭",
       "oint": "∮", "bigcup": "⋃", "bigcap": "⋂", "bigoplus": "⨁", "bigotimes": "⨂",
       "bigvee": "⋁", "bigwedge": "⋀"}  # fmt: skip
INTEGRALS = {"int", "iint", "iiint", "oint"}
FUNCTIONS = {
    "sin", "cos", "tan", "cot", "sec", "csc", "arcsin", "arccos", "arctan", "sinh", "cosh",
    "tanh", "coth", "log", "ln", "lg", "exp", "min", "max", "sup", "inf", "lim", "limsup",
    "liminf", "det", "dim", "ker", "deg", "gcd", "arg", "Pr", "mod", "hom",
}  # fmt: skip
LIMITS_ABOVE = {"lim", "limsup", "liminf", "min", "max", "sup", "inf", "det", "gcd", "Pr"}
SPACES = {",": 0.17, ":": 0.22, ";": 0.28, "!": -0.17, "quad": 1.0, "qquad": 2.0, " ": 0.28}
ACCENTS = {"hat": "^", "widehat": "^", "bar": "‾", "tilde": "~", "widetilde": "~",
           "vec": "→", "dot": "˙", "ddot": "¨", "overline": "‾", "check": "ˇ", "acute": "´",
           "grave": "`", "breve": "˘"}  # fmt: skip
DELIMS = {"(", ")", "[", "]", "{", "}", "|", "‖", "⟨", "⟩", "⌊", "⌋", "⌈", "⌉", "/", "\\"}
MATRICES = {
    "matrix": ("", ""), "pmatrix": ("(", ")"), "bmatrix": ("[", "]"), "Bmatrix": ("{", "}"),
    "vmatrix": ("|", "|"), "Vmatrix": ("‖", "‖"), "cases": ("{", ""), "aligned": ("", ""),
    "align": ("", ""), "align*": ("", ""), "array": ("", ""), "gathered": ("", ""),
    "split": ("", ""), "smallmatrix": ("", ""),
}  # fmt: skip
DOUBLE_STRUCK = {"C": "ℂ", "H": "ℍ", "N": "ℕ", "P": "ℙ", "Q": "ℚ", "R": "ℝ", "Z": "ℤ"}
_TOKEN = re.compile(r"\\([A-Za-z]+\*?|.)|(.)", re.S)


def encode(latex: str) -> str:
    """The text that stands for a formula inside an image address."""
    return base64.urlsafe_b64encode(latex.encode("utf-8")).decode("ascii").rstrip("=")


def decode(text: str) -> str | None:
    try:
        raw = base64.urlsafe_b64decode(text.encode("ascii") + b"=" * (-len(text) % 4))
        return raw.decode("utf-8")[:MAX_LATEX]
    except (ValueError, UnicodeError):
        return None


@dataclass(frozen=True)
class Style:
    size: float  # pixels
    kind: str = "it"  # it | rm | bf | bb | cal | tt
    display: bool = False
    level: int = 0  # 0 normal, 1 script, 2 script of a script

    def script(self) -> Style:
        return replace(self, size=max(self.size * 0.7, 6), display=False, level=self.level + 1)

    def font(self, kind: str | None = None, scale: float = 1.0) -> QFont:
        kind = kind or self.kind
        font = QFont()
        font.setFamilies(["Consolas"] + FAMILIES if kind == "tt" else FAMILIES)
        font.setPixelSize(max(1, round(self.size * scale)))
        font.setItalic(kind in ("it", "cal"))
        font.setBold(kind == "bf")
        return font


# --- boxes ------------------------------------------------------------------


class Box:
    """Something with a width, a height above the baseline and a depth below it."""

    w = 0.0
    a = 0.0
    d = 0.0

    def draw(self, p: QPainter, x: float, y: float) -> None:  # y is the baseline
        pass


class Glue(Box):
    def __init__(self, w: float):
        self.w = w


class Text(Box):
    def __init__(self, text: str, style: Style, kind: str | None = None, scale: float = 1.0,
                 error: bool = False):  # fmt: skip
        self.text, self.font, self.error = text, style.font(kind, scale), error
        fm = QFontMetricsF(self.font)
        rect = fm.tightBoundingRect(text)
        self.w = fm.horizontalAdvance(text)
        if self.font.italic():
            self.w += style.size * 0.04
        self.a = max(-rect.top(), 0.0)
        self.d = max(rect.bottom(), 0.0)
        self.size = style.size

    def draw(self, p, x, y):
        p.setFont(self.font)
        if self.error:
            p.save()
            p.setPen(QColor("#c0392b"))
        p.drawText(QPointF(x, y), self.text)
        if self.error:
            p.restore()


class Row(Box):
    def __init__(self, items: list[Box]):
        self.items = items
        self.w = sum(i.w for i in items)
        self.a = max((i.a for i in items), default=0.0)
        self.d = max((i.d for i in items), default=0.0)

    def draw(self, p, x, y):
        for item in self.items:
            item.draw(p, x, y)
            x += item.w


class Fraction(Box):
    def __init__(self, num: Box, den: Box, size: float, bar: bool = True):
        self.num, self.den, self.bar = num, den, bar
        t = max(size * 0.065, 1.0) if bar else 0.0
        gap = size * 0.14
        self.t, self.axis = t, size * AXIS
        pad = size * 0.1
        self.w = max(num.w, den.w) + 2 * pad
        self.num_up = self.axis + t / 2 + gap + num.d
        self.den_down = -(self.axis - t / 2 - gap - den.a)
        self.a = self.num_up + num.a
        self.d = self.den_down + den.d

    def draw(self, p, x, y):
        self.num.draw(p, x + (self.w - self.num.w) / 2, y - self.num_up)
        self.den.draw(p, x + (self.w - self.den.w) / 2, y + self.den_down)
        if self.bar:
            pen = QPen(p.pen())
            pen.setWidthF(self.t)
            pen.setCapStyle(Qt.PenCapStyle.FlatCap)
            p.save()
            p.setPen(pen)
            p.drawLine(QPointF(x + 1, y - self.axis), QPointF(x + self.w - 1, y - self.axis))
            p.restore()


class Scripts(Box):
    def __init__(self, base: Box, sup: Box | None, sub: Box | None, size: float):
        self.base, self.sup, self.sub = base, sup, sub
        self.up = self.down = 0.0
        width = 0.0
        if sup:
            self.up = max(size * 0.38, base.a - size * 0.2)
            width = sup.w
        if sub:
            self.down = max(size * 0.2, base.d + sub.a - size * 0.1)
            width = max(width, sub.w)
        if sup and sub:
            gap = (self.up - sup.d) - (-self.down + sub.a)
            if gap < size * 0.2:
                self.up += (size * 0.2 - gap) / 2
                self.down += (size * 0.2 - gap) / 2
        self.w = base.w + width + size * 0.03
        self.a = max(base.a, self.up + (sup.a if sup else 0))
        self.d = max(base.d, self.down + (sub.d if sub else 0))

    def draw(self, p, x, y):
        self.base.draw(p, x, y)
        x += self.base.w + 1
        if self.sup:
            self.sup.draw(p, x, y - self.up)
        if self.sub:
            self.sub.draw(p, x, y + self.down)


class UnderOver(Box):
    """A big operator or `lim` with its limits above and below."""

    def __init__(self, base: Box, over: Box | None, under: Box | None, size: float):
        self.base, self.over, self.under = base, over, under
        gap = size * 0.12
        self.w = max(base.w, over.w if over else 0, under.w if under else 0)
        self.over_up = base.a + gap + (over.d if over else 0)
        self.under_down = base.d + gap + (under.a if under else 0)
        self.a = self.over_up + over.a if over else base.a
        self.d = self.under_down + under.d if under else base.d

    def draw(self, p, x, y):
        self.base.draw(p, x + (self.w - self.base.w) / 2, y)
        if self.over:
            self.over.draw(p, x + (self.w - self.over.w) / 2, y - self.over_up)
        if self.under:
            self.under.draw(p, x + (self.w - self.under.w) / 2, y + self.under_down)


class Sqrt(Box):
    def __init__(self, body: Box, index: Box | None, size: float):
        self.body, self.index, self.size = body, index, size
        self.t = max(size * 0.06, 1.0)
        self.gap = size * 0.12
        self.surd = size * 0.62
        self.h = body.a + self.gap + self.t
        self.idx_w = max(index.w - self.surd * 0.45, 0) if index else 0.0
        self.w = self.idx_w + self.surd + body.w + size * 0.08
        self.a = self.h + (max(index.a + index.d - self.h * 0.45, 0) if index else 0)
        self.d = max(body.d, size * 0.05)

    def draw(self, p, x, y):
        s = self.surd
        x0 = x + self.idx_w
        top = y - self.h
        bottom = y + self.d
        path = QPainterPath(QPointF(x0, y - self.h * 0.35))
        path.lineTo(x0 + s * 0.22, y - self.h * 0.42)
        path.lineTo(x0 + s * 0.5, bottom)
        path.lineTo(x0 + s, top)
        path.lineTo(x0 + s + self.body.w + self.size * 0.06, top)
        pen = QPen(p.pen())
        pen.setWidthF(self.t)
        pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
        p.save()
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(path)
        p.restore()
        self.body.draw(p, x0 + s, y)
        if self.index:
            self.index.draw(p, x, y - self.h * 0.55)


class Decorated(Box):
    """A box with an accent over it, or a line under it."""

    def __init__(self, body: Box, kind: str, size: float):
        self.body, self.kind, self.size = body, kind, size
        self.w, self.a, self.d = body.w, body.a, body.d
        if kind == "underline":
            self.d = body.d + size * 0.18
        else:
            self.a = max(body.a, size * 0.45) + size * 0.2

    def draw(self, p, x, y):
        self.body.draw(p, x, y)
        s = self.size
        pen = QPen(p.pen())
        pen.setWidthF(max(s * 0.055, 1.0))
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.save()
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        cx = x + self.w / 2
        top = y - max(self.body.a, s * 0.45) - s * 0.1
        if self.kind == "underline":
            u = y + self.body.d + s * 0.1
            p.drawLine(QPointF(x, u), QPointF(x + self.w, u))
        elif self.kind == "overline":
            p.drawLine(QPointF(x, top), QPointF(x + self.w, top))
        elif self.kind == "bar":
            half = min(self.w / 2, s * 0.3)
            p.drawLine(QPointF(cx - half, top), QPointF(cx + half, top))
        elif self.kind == "hat":
            half = min(self.w / 2, s * 0.28)
            path = QPainterPath(QPointF(cx - half, top + s * 0.1))
            path.lineTo(cx, top - s * 0.05)
            path.lineTo(cx + half, top + s * 0.1)
            p.drawPath(path)
        elif self.kind == "tilde":
            half = min(self.w / 2, s * 0.3)
            path = QPainterPath(QPointF(cx - half, top + s * 0.06))
            path.cubicTo(cx - half / 2, top - s * 0.1, cx, top + s * 0.1, cx + half, top - s * 0.04)
            p.drawPath(path)
        elif self.kind == "vec":
            half = min(self.w / 2, s * 0.3)
            p.drawLine(QPointF(cx - half, top), QPointF(cx + half, top))
            p.drawLine(QPointF(cx + half, top), QPointF(cx + half - s * 0.1, top - s * 0.07))
            p.drawLine(QPointF(cx + half, top), QPointF(cx + half - s * 0.1, top + s * 0.07))
        elif self.kind in ("dot", "ddot"):
            ink = p.pen().color()
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(ink)
            r = max(s * 0.045, 1.0)
            xs = [cx] if self.kind == "dot" else [cx - s * 0.1, cx + s * 0.1]
            for dx in xs:
                p.drawEllipse(QPointF(dx, top), r, r)
        p.restore()


class Delimited(Box):
    """Brackets stretched to the height of what they enclose."""

    def __init__(self, left: str, body: Box, right: str, size: float):
        self.left, self.body, self.right, self.size = left, body, right, size
        axis = size * AXIS
        half = max(body.a - axis, body.d + axis, size * 0.5)
        self.top, self.bottom = axis + half, -(half - axis)  # relative to the baseline
        self.lw = self._width(left)
        self.rw = self._width(right)
        self.w = self.lw + body.w + self.rw
        self.a, self.d = self.top + size * 0.05, -self.bottom + size * 0.05

    def _width(self, ch: str) -> float:
        if ch in ("", "."):
            return 0.0
        return self.size * (0.4 if ch in "|‖/\\" else 0.5)

    def draw(self, p, x, y):
        self._glyph(p, self.left, x, y, True)
        self.body.draw(p, x + self.lw, y)
        self._glyph(p, self.right, x + self.lw + self.body.w, y, False)

    def _glyph(self, p, ch, x, y, opening):
        w = self._width(ch)
        if not w:
            return
        s = self.size
        top, bot = y - self.top, y - self.bottom
        mid = (top + bot) / 2
        h = bot - top
        left, right = x + w * 0.18, x + w * 0.82
        near, far = (right, left) if opening else (left, right)  # far = the bulge side
        path = QPainterPath()
        if ch in "()":
            path.moveTo(near, top)
            path.cubicTo(far, top + h * 0.25, far, bot - h * 0.25, near, bot)
        elif ch in "[]":
            path.moveTo(near, top)
            path.lineTo(far, top)
            path.lineTo(far, bot)
            path.lineTo(near, bot)
        elif ch in "⌈⌉":
            path.moveTo(near, top)
            path.lineTo(far, top)
            path.lineTo(far, bot)
        elif ch in "⌊⌋":
            path.moveTo(far, top)
            path.lineTo(far, bot)
            path.lineTo(near, bot)
        elif ch in "{}":
            tip = x + (w * 0.1 if opening else w * 0.9)
            out = x + (w * 0.9 if opening else w * 0.1)
            c = x + w / 2
            path.moveTo(out, top)
            path.cubicTo(c, top, c, top, c, top + h * 0.15)
            path.lineTo(c, mid - h * 0.07)
            path.cubicTo(c, mid, tip + (c - tip) * 0.4, mid, tip, mid)
            path.cubicTo(tip + (c - tip) * 0.4, mid, c, mid, c, mid + h * 0.07)
            path.lineTo(c, bot - h * 0.15)
            path.cubicTo(c, bot, c, bot, out, bot)
        elif ch in "⟨⟩":
            path.moveTo(near, top)
            path.lineTo(far, mid)
            path.lineTo(near, bot)
        elif ch == "‖":
            for dx in (w * 0.3, w * 0.7):
                path.moveTo(x + dx, top)
                path.lineTo(x + dx, bot)
        elif ch == "/":
            path.moveTo(right, top)
            path.lineTo(left, bot)
        elif ch == "\\":
            path.moveTo(left, top)
            path.lineTo(right, bot)
        else:  # | and anything else
            path.moveTo(x + w / 2, top)
            path.lineTo(x + w / 2, bot)
        pen = QPen(p.pen())
        pen.setWidthF(max(s * 0.06, 1.0))
        pen.setCapStyle(Qt.PenCapStyle.FlatCap)
        p.save()
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(path)
        p.restore()


class Grid(Box):
    def __init__(self, rows: list[list[Box]], aligns: list[str], size: float, gap: float = 1.0):
        self.rows, self.aligns = rows, aligns
        cols = max((len(r) for r in rows), default=0)
        self.col_w = [max((r[c].w for r in rows if c < len(r)), default=0.0) for c in range(cols)]
        gap *= size
        self.col_x, x = [], 0.0
        for width in self.col_w:
            self.col_x.append(x)
            x += width + gap
        self.w = max(x - gap, 0.0)
        row_gap = size * 0.3
        self.row_y: list[float] = []  # baseline of each row, from the top
        y = 0.0
        for r in rows:
            a = max((b.a for b in r), default=size * 0.7)
            d = max((b.d for b in r), default=size * 0.2)
            y += a
            self.row_y.append(y)
            y += d + row_gap
        total = max(y - row_gap, 0.0)
        axis = size * AXIS
        self.a = total / 2 + axis
        self.d = total / 2 - axis

    def draw(self, p, x, y):
        top = y - self.a
        for r, ry in zip(self.rows, self.row_y, strict=True):
            for c, box in enumerate(r):
                align = self.aligns[c % len(self.aligns)] if self.aligns else "c"
                space = self.col_w[c] - box.w
                dx = space / 2 if align == "c" else (space if align == "r" else 0.0)
                box.draw(p, x + self.col_x[c] + dx, top + ry)


# --- parser -----------------------------------------------------------------


class MathError(ValueError):
    pass


class Parser:
    def __init__(self, source: str, style: Style):
        self.tokens = [(m.group(1) or m.group(2), m.group(1) is not None) for m in
                       _TOKEN.finditer(source)]  # fmt: skip
        self.pos = 0
        self.root = style
        self.depth = 0

    # token helpers
    def peek(self):
        return self.tokens[self.pos] if self.pos < len(self.tokens) else (None, False)

    def next(self):
        tok = self.peek()
        self.pos += 1
        return tok

    def at(self, text: str, command: bool = False) -> bool:
        tok, is_cmd = self.peek()
        return tok == text and is_cmd == command

    def skip_space(self):
        while self.peek()[0] in (" ", "\n", "\t", "\r") and not self.peek()[1]:
            self.pos += 1

    # grammar
    def parse(self) -> Box:
        box = self.row(self.root, stop=())
        if self.pos < len(self.tokens):
            raise MathError("Unexpected " + str(self.peek()[0]))
        return box

    def row(self, st: Style, stop: tuple[str, ...]) -> Box:
        """Atoms until a stop token (`}`, `&`, `\\\\`, `\\end`, ...). It is not consumed."""
        self.depth += 1
        if self.depth > MAX_DEPTH:
            raise MathError("Too deeply nested")
        items: list[Box] = []
        prev = "open"  # what came before: open | ord | bin | rel | punct | big
        while self.pos < len(self.tokens):
            tok, is_cmd = self.peek()
            if (("\\" + tok) if is_cmd else tok) in stop:
                break
            if tok in (" ", "\n", "\t", "\r") and not is_cmd:
                self.pos += 1
                continue
            atom, kind = self.atom(st, prev)
            atom = self.scripts(atom, st, big=kind == "big")
            if kind == "bin" and prev in ("open", "bin", "rel"):
                kind = "ord"  # a sign, as in -x or a = -b
            spaced = st.level == 0 and kind in ("bin", "rel")
            if spaced and prev != "open":
                items.append(Glue(st.size * (0.22 if kind == "bin" else 0.28)))
            items.append(atom)
            if spaced:
                items.append(Glue(st.size * (0.22 if kind == "bin" else 0.28)))
            elif kind == "punct" and st.level == 0:
                items.append(Glue(st.size * 0.17))
            prev = kind
        self.depth -= 1
        return Row(items)

    def scripts(self, base: Box, st: Style, big: bool = False) -> Box:
        sup = sub = None
        sup_s = st.script()
        while True:
            self.skip_space()
            if self.at("^") and sup is None:
                self.next()
                sup = self.argument(sup_s)
            elif self.at("_") and sub is None:
                self.next()
                sub = self.argument(sup_s)
            else:
                break
        if sup is None and sub is None:
            return base
        if big and getattr(base, "limits", False):
            return UnderOver(base, sup, sub, st.size)
        return Scripts(base, sup, sub, st.size)

    def argument(self, st: Style) -> Box:
        """One group `{...}` or one token, as the argument of a command or script."""
        self.skip_space()
        tok, is_cmd = self.peek()
        if tok is None:
            raise MathError("Missing argument")
        if tok == "{" and not is_cmd:
            self.next()
            box = self.row(st, stop=("}",))
            if not self.at("}"):
                raise MathError("Missing }")
            self.next()
            return box
        atom, _kind = self.atom(st, "open")
        return atom

    def optional(self, st: Style) -> Box | None:
        self.skip_space()
        if self.at("["):
            self.next()
            box = self.row(st, stop=("]",))
            if self.at("]"):
                self.next()
            return box
        return None

    def raw_group(self) -> str:
        """The text of a `{...}` group with no formatting, e.g. an environment name."""
        self.skip_space()
        if not self.at("{"):
            raise MathError("Missing {")
        self.next()
        out = []
        while self.pos < len(self.tokens) and not self.at("}"):
            out.append(self.next()[0])
        self.next()
        return "".join(out).strip()

    def text_group(self, st: Style, kind: str) -> Box:
        """`\\text{...}`: the characters as written, spaces included."""
        self.skip_space()
        if not self.at("{"):
            return self.argument(replace(st, kind=kind))
        self.next()
        out, depth = [], 1
        while self.pos < len(self.tokens):
            tok, is_cmd = self.next()
            if tok == "{" and not is_cmd:
                depth += 1
            elif tok == "}" and not is_cmd:
                depth -= 1
                if depth == 0:
                    break
            out.append(tok if not is_cmd else (" " if tok == " " else ""))
        return Text("".join(out), st, kind="rm" if kind != "tt" else "tt")

    def atom(self, st: Style, prev: str) -> tuple[Box, str]:
        tok, is_cmd = self.next()
        if tok is None:
            raise MathError("Unexpected end")
        if not is_cmd:
            return self.character(tok, st)
        return self.command(tok, st)

    def character(self, ch: str, st: Style) -> tuple[Box, str]:
        if ch == "{":
            box = self.row(st, stop=("}",))
            if not self.at("}"):
                raise MathError("Missing }")
            self.next()
            return box, "ord"
        if ch in "}&^_":
            raise MathError("Unexpected " + ch)
        if ch == "-":
            return Text("−", st, "rm"), "bin"
        if ch in "+*":
            return Text("∗" if ch == "*" else "+", st, "rm"), "bin"
        if ch in "=<>":
            return Text(ch, st, "rm"), "rel"
        if ch == ":":
            return Text(":", st, "rm"), "rel"
        if ch in ",;":
            return Text(ch, st, "rm"), "punct"
        if ch == "!":
            return Text("!", st, "rm"), "ord"
        if ch == "'":
            return Text("′", st, "rm"), "ord"
        if ch in "([|)]/":
            return Text(ch, st, "rm"), "ord"
        if ch.isalpha():
            return self.letter(ch, st), "ord"
        return Text(ch, st, "rm"), "ord"

    def letter(self, ch: str, st: Style) -> Box:
        if st.kind == "bb" and (ch in DOUBLE_STRUCK or ch.isupper()):
            return Text(DOUBLE_STRUCK.get(ch, chr(0x1D538 + ord(ch) - 65)), st, "rm")
        kind = st.kind
        if kind == "it" and not ch.isalpha():
            kind = "rm"
        return Text(ch, st, kind)

    def command(self, name: str, st: Style) -> tuple[Box, str]:
        size = st.size
        if name in GREEK:
            kind = "rm" if name[0].isupper() or st.kind == "rm" else st.kind
            return Text(GREEK[name], st, "it" if kind == "it" else kind), "ord"
        if name in BINARY:
            return Text(BINARY[name], st, "rm"), "bin"
        if name in RELATION:
            return Text(RELATION[name], st, "rm"), "rel"
        if name in ORDINARY:
            return Text(ORDINARY[name], st, "rm"), "ord"
        if name in BIG:
            integral = name in INTEGRALS
            glyph = Text(BIG[name], st, "rm", 1.35 if st.display or integral else 1.0)
            glyph.limits = st.display and not integral  # type: ignore[attr-defined]
            # centre the tall glyph on the axis
            shift = (glyph.a - glyph.d) / 2 - size * AXIS
            glyph.a, glyph.d = glyph.a - shift, glyph.d + shift
            return Raised(glyph, shift), "big"
        if name in FUNCTIONS:
            row = Row([Text(name, st, "rm"), Glue(size * 0.12)])
            row.limits = name in LIMITS_ABOVE and st.display  # type: ignore[attr-defined]
            return row, "big" if name in LIMITS_ABOVE else "ord"
        if name in SPACES:
            return Glue(size * SPACES[name]), "ord"
        if name == "\\":
            raise MathError("Line breaks only work in matrices and aligned equations")
        if name == "frac" or name == "dfrac" or name == "tfrac" or name == "cfrac":
            return self._fraction(st), "ord"
        if name == "binom":
            a = self.argument(st.script())
            b = self.argument(st.script())
            return Delimited("(", Fraction(a, b, size, bar=False), ")", size), "ord"
        if name == "sqrt":
            index = self.optional(st.script().script())
            return Sqrt(self.argument(st), index, size), "ord"
        if name in ("mathrm", "textrm", "operatorname", "mathop"):
            return self.argument(replace(st, kind="rm")), "ord"
        if name in ("mathbf", "boldsymbol", "bm", "textbf", "mathbfit"):
            return self.argument(replace(st, kind="bf")), "ord"
        if name in ("mathit", "textit", "mathnormal"):
            return self.argument(replace(st, kind="it")), "ord"
        if name in ("mathbb", "Bbb"):
            return self.argument(replace(st, kind="bb")), "ord"
        if name in ("mathcal", "mathscr", "mathfrak"):
            return self.argument(replace(st, kind="cal")), "ord"
        if name in ("mathtt", "texttt"):
            return self.text_group(st, "tt"), "ord"
        if name in ("text", "mbox", "hbox"):
            return self.text_group(st, "rm"), "ord"
        if name in ACCENTS or name in ("underline", "overbrace", "underbrace"):
            kind = {"widehat": "hat", "widetilde": "tilde"}.get(name, name)
            if name in ("overbrace", "underbrace"):
                kind = "overline" if name == "overbrace" else "underline"
            return Decorated(self.argument(st), kind, size), "ord"
        if name in ("displaystyle",):
            return Glue(0), "ord"
        if name in ("left",):
            return self.left_right(st), "ord"
        if name in ("right", "big", "Big", "bigg", "Bigg", "bigl", "bigr", "Bigl", "Bigr"):
            tok, is_cmd = self.next()
            return Text(tok if not is_cmd else ORDINARY.get(tok, ""), st, "rm"), "ord"
        if name == "begin":
            return self.environment(st), "ord"
        if name in ("limits", "nolimits", "relax", "ensuremath"):
            return Glue(0), "ord"
        if name in ("lbrack",):
            return Text("[", st, "rm"), "ord"
        if name in ("rbrack",):
            return Text("]", st, "rm"), "ord"
        if name in ("lt", "gt"):
            return Text("<" if name == "lt" else ">", st, "rm"), "rel"
        if name in ("{", "}"):
            return Text(name, st, "rm"), "ord"
        raise MathError(f"Unknown command \\{name}")

    def _fraction(self, st: Style) -> Box:
        # In display style the parts keep the full size; inside text they shrink.
        inner = replace(st, display=False) if st.display else st.script()
        num = self.argument(inner)
        den = self.argument(inner)
        return Fraction(num, den, st.size)

    def left_right(self, st: Style) -> Box:
        left = self._delimiter()
        body = self.row(st, stop=("\\right",))
        if not (self.at("right", True)):
            raise MathError("\\left without \\right")
        self.next()
        right = self._delimiter()
        return Delimited(left, body, right, st.size)

    def _delimiter(self) -> str:
        tok, is_cmd = self.next()
        if tok is None:
            raise MathError("Missing delimiter")
        if is_cmd:
            tok = ORDINARY.get(tok, tok)
            if tok in ("vert", "|"):
                tok = "|"
        return tok if tok in DELIMS or tok == "." else "."

    def environment(self, st: Style) -> Box:
        name = self.raw_group()
        if name not in MATRICES:
            raise MathError(f"Unknown environment {name}")
        left, right = MATRICES[name]
        cell_style = (
            replace(st, display=False)
            if name
            in ("matrix", "pmatrix", "bmatrix", "Bmatrix", "vmatrix", "Vmatrix", "smallmatrix")
            else st
        )
        if name == "array":
            self.skip_space()
            if self.at("{"):
                self.raw_group()
        rows: list[list[Box]] = [[]]
        while True:
            cell = self.row(cell_style, stop=("&", "\\\\", "\\end"))
            rows[-1].append(cell)
            tok, is_cmd = self.peek()
            if tok == "&" and not is_cmd:
                self.next()
            elif tok == "\\":
                self.next()
                rows.append([])
            elif tok == "end" and is_cmd:
                self.next()
                if self.raw_group() != name:
                    raise MathError("Mismatched \\end")
                break
            else:
                raise MathError("Missing \\end{" + name + "}")
        if rows and len(rows[-1]) == 1 and not rows[-1][0].w:
            rows.pop()  # a trailing \\
        if name == "cases":
            aligns = ["l", "l"]
        elif name in ("aligned", "align", "align*", "split"):
            aligns = ["r", "l"]
        else:
            aligns = ["c"]
        tight = name in ("aligned", "align", "align*", "split")
        grid = Grid(rows, aligns, st.size, gap=0.0 if tight else 1.0)
        if left or right:
            return Delimited(left, grid, right, st.size)
        return grid


class Raised(Box):
    """A glyph moved up or down so that it sits on the maths axis."""

    def __init__(self, inner: Text, shift: float):
        self.inner, self.shift = inner, shift
        self.w, self.a, self.d = inner.w, inner.a, inner.d
        self.limits = getattr(inner, "limits", False)

    def draw(self, p, x, y):
        self.inner.draw(p, x, y + self.shift)


# --- public API -------------------------------------------------------------


@dataclass
class Rendered:
    image: QImage
    ok: bool
    message: str = ""


def _fallback(latex: str, style: Style, message: str) -> tuple[Box, str]:
    return Text(latex, replace(style, kind="tt"), "tt", error=True), message


def layout(latex: str, size: float, display: bool) -> tuple[Box, str]:
    style = Style(size=size, display=display)
    latex = latex.strip()[:MAX_LATEX]
    try:
        return Parser(latex, style).parse(), ""
    except (MathError, RecursionError, IndexError) as exc:
        return _fallback(latex, style, str(exc) or "Invalid formula")


def render(
    latex: str,
    size: float = 16.0,
    color: str = "#000000",
    display: bool = False,
    ratio: float = SCALE,
) -> Rendered:
    """Draw *latex* to a transparent image. The image's vertical centre is the maths axis, so
    placing it with `vertical-align: middle` lines the formula up with the surrounding text.
    *ratio* is the screen's device pixel ratio: a mismatch would make Qt resample the image
    and lose the thin strokes of + and =."""
    box, message = layout(latex, size * ratio, display)
    pad = size * ratio * 0.16
    axis = size * ratio * AXIS
    half = max(box.a - axis, box.d + axis, size * ratio * 0.5) + pad
    width, height = box.w + 2 * pad, 2 * half
    image = QImage(
        max(1, int(width + 1)), max(1, int(height + 1)), QImage.Format.Format_ARGB32_Premultiplied
    )
    image.fill(Qt.GlobalColor.transparent)
    p = QPainter(image)
    p.setRenderHints(
        QPainter.RenderHint.Antialiasing
        | QPainter.RenderHint.TextAntialiasing
        | QPainter.RenderHint.SmoothPixmapTransform
    )
    p.setPen(QPen(QColor(color)))
    box.draw(p, pad, half + axis)
    p.end()
    image.setDevicePixelRatio(ratio)
    return Rendered(image, not message, message)


__all__ = ["MathError", "Rendered", "decode", "encode", "layout", "render"]
