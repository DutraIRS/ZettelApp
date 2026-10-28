"""Collect translatable strings and check the translation catalogs.

    python tools/i18n.py extract   write zettelapp/resources/locales/messages.json
    python tools/i18n.py check     report missing, stale and broken translations

messages.json lists every string passed to _(), N_() and n_() (with its plural form and
where it is used); it is what translators work from. Each <code>.json catalog maps the
English text to its translation, or to a list of plural forms for n_() strings (one form
for zh_CN/ja/ko, two for most languages, three for Russian, six for Arabic).
"""

from __future__ import annotations

import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from zettelapp.i18n import placeholders  # noqa: E402

LOCALES = ROOT / "zettelapp" / "resources" / "locales"
TEMPLATE = LOCALES / "messages.json"
PLURAL_FORMS = {"zh_CN": 1, "ja": 1, "ko": 1, "ru": 3, "ar": 6}


def extract() -> dict[str, dict]:
    """English text -> {"plural": str | None, "where": [file:line, ...]}."""
    messages: dict[str, dict] = {}
    for path in sorted((ROOT / "zettelapp").rglob("*.py")):
        rel = path.relative_to(ROOT).as_posix()
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Name):
                continue
            name, args = node.func.id, node.args
            literal = [
                a.value if isinstance(a, ast.Constant) and isinstance(a.value, str) else None
                for a in args
            ]
            if name in ("_", "N_") and literal and literal[0]:
                entry = messages.setdefault(literal[0], {"plural": None, "where": []})
            elif name == "n_" and len(literal) >= 2 and literal[0] and literal[1]:
                entry = messages.setdefault(literal[0], {"plural": None, "where": []})
                entry["plural"] = literal[1]
            else:
                continue
            entry["where"].append(f"{rel}:{node.lineno}")
    return dict(sorted(messages.items(), key=lambda kv: kv[0].casefold()))


def problems(language: str, catalog: dict, messages: dict[str, dict]) -> dict[str, list[str]]:
    """Missing, stale and broken entries of one catalog."""
    out: dict[str, list[str]] = {"missing": [], "stale": [], "broken": []}
    for key, value in catalog.items():
        if key not in messages:
            out["stale"].append(key)
            continue
        allowed = placeholders(key) | placeholders(messages[key]["plural"] or "")
        forms = value if isinstance(value, list) else [value]
        wanted = PLURAL_FORMS.get(language, 2) if messages[key]["plural"] else None
        if (wanted is None) != (not isinstance(value, list)) or (wanted and len(forms) != wanted):
            out["broken"].append(f"{key!r}: expected {wanted or 'a single'} form(s)")
            continue
        for form in forms:
            if not isinstance(form, str) or not form.strip():
                out["broken"].append(f"{key!r}: empty translation")
            elif not placeholders(form) <= allowed:
                out["broken"].append(f"{key!r}: unknown placeholder in {form!r}")
            else:
                try:
                    form.format(**{name: "x" for name in placeholders(form)})
                except (IndexError, KeyError, ValueError) as exc:
                    out["broken"].append(f"{key!r}: {exc}")
    out["missing"] = [k for k in messages if k not in catalog]
    return out


def catalogs() -> dict[str, dict]:
    return {
        p.stem: json.loads(p.read_text(encoding="utf-8"))
        for p in sorted(LOCALES.glob("*.json"))
        if p.name != TEMPLATE.name
    }


def main(argv: list[str]) -> int:
    command = argv[1] if len(argv) > 1 else "check"
    messages = extract()
    if command == "extract":
        LOCALES.mkdir(parents=True, exist_ok=True)
        TEMPLATE.write_text(
            json.dumps(messages, ensure_ascii=False, indent=1) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        print(f"{len(messages)} strings written to {TEMPLATE.relative_to(ROOT)}")
        return 0
    status = 0
    for language, catalog in catalogs().items():
        found = problems(language, catalog, messages)
        print(
            f"{language}: {len(catalog) - len(found['stale'])}/{len(messages)} translated, "
            f"{len(found['missing'])} missing, {len(found['stale'])} stale, {len(found['broken'])} broken"
        )
        for issue in found["broken"][:10]:
            print("   broken:", issue)
        status |= bool(found["broken"] or found["missing"] or found["stale"])
    return status


if __name__ == "__main__":
    sys.exit(main(sys.argv))
