"""Fetch the Fluent UI System Icons that ZettelApp draws where the Windows icon fonts are missing.

Run with:  python tools/fetch_icons.py

Downloads the pinned release of Microsoft's Fluent UI System Icons (MIT licence) from the npm
registry, checked against its published sha512, and writes the icons that
zettelapp.ui.icons.FLUENT names, minified, to zettelapp/resources/icons/fluent/, together with
the licence. The language-specific Bold/Italic letters exist only in the GitHub repository; they
come from the commit that the same release was built from. Files no longer listed are removed,
so running it again after changing FLUENT or the version gives exactly the subset in use.
"""

from __future__ import annotations

import ast
import base64
import hashlib
import io
import re
import sys
import tarfile
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

VERSION = "1.1.345"
INTEGRITY = "sha512-Mz5e5BFKtvRN5Yiwrs5JqZRKgd8Rt8S3YiCAuwOWudmm7NA14Y8Ijr8QzMrE6gtNdoUP6/om7ue0lBQJLL57Mw=="
COMMIT = "73ec879377b1f412f33aca4a128aa967e6c238f0"  # the release's gitHead on npm
TARBALL = f"https://registry.npmjs.org/@fluentui/svg-icons/-/svg-icons-{VERSION}.tgz"
REPO = f"https://raw.githubusercontent.com/microsoft/fluentui-system-icons/{COMMIT}/"

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "zettelapp" / "resources" / "icons" / "fluent"
SVG_NS = "http://www.w3.org/2000/svg"
PATH_ATTRIBUTES = ("d", "fill-rule", "clip-rule")


def wanted() -> dict[str, str]:
    """FLUENT from zettelapp/ui/icons.py, read without importing Qt."""
    tree = ast.parse((ROOT / "zettelapp" / "ui" / "icons.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "FLUENT" for t in node.targets
        ):
            return ast.literal_eval(node.value)
    raise SystemExit("FLUENT not found in zettelapp/ui/icons.py")


def download(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "zettelapp-fetch-icons"})
    with urllib.request.urlopen(request, timeout=60) as response:  # noqa: S310 - fixed https URLs
        return response.read()


def minify(svg: bytes, name: str) -> str:
    """The icon as one line: its view box and paths, with no colour (the app tints it)."""
    root = ET.fromstring(svg)  # noqa: S314 - a pinned upstream file, checked below
    if root.tag != f"{{{SVG_NS}}}svg":
        raise SystemExit(f"{name}: not an SVG document")
    view_box = root.get("viewBox") or f"0 0 {root.get('width')} {root.get('height')}"
    if not re.fullmatch(r"0 0 \d+ \d+", view_box):
        raise SystemExit(f"{name}: unexpected view box {view_box!r}")
    paths = []
    for element in root.iter():
        if element is root:
            continue
        if element.tag != f"{{{SVG_NS}}}path":
            raise SystemExit(f"{name}: unexpected <{element.tag}> element")
        attributes = "".join(
            f' {key}="{element.get(key)}"' for key in PATH_ATTRIBUTES if element.get(key)
        )
        if not re.fullmatch(r'( [a-z-]+="[-0-9A-Za-z .,]+")+', attributes):
            raise SystemExit(f"{name}: unexpected path data")
        paths.append(f"<path{attributes}/>")
    width, height = view_box.split()[2:]
    return (
        f'<svg xmlns="{SVG_NS}" width="{width}" height="{height}" viewBox="{view_box}">'
        + "".join(paths)
        + "</svg>\n"
    )


def localized_url(stem: str, locale: str) -> str:
    """Where the GitHub repository keeps a language variant, e.g. Text Bold/pt/SVG/…"""
    base = re.sub(r"_\d+_(regular|filled)$", "", stem)
    folder = " ".join(word.capitalize() for word in base.split("_"))
    path = f"assets/{folder}/{locale}/SVG/ic_fluent_{stem}.svg"
    return REPO + urllib.parse.quote(path)


def small(name: str) -> str:
    """The 16 px design of a 20 px icon: drawn for small icons, its 1 px strokes stay sharp."""
    return name.replace("_20_", "_16_", 1)


def main() -> None:
    files = sorted(set(wanted().values()))
    print(f"Fluent UI System Icons {VERSION}: {len(files)} icons, in 20 and 16 px designs")
    tarball = download(TARBALL)
    digest = "sha512-" + base64.b64encode(hashlib.sha512(tarball).digest()).decode()
    if digest != INTEGRITY:
        raise SystemExit(f"{TARBALL} does not match the pinned sha512")
    icons: dict[str, str] = {}
    with tarfile.open(fileobj=io.BytesIO(tarball), mode="r:gz") as archive:
        names = set(archive.getnames())
        for name in files:
            if "." in name:
                continue
            for variant in (name, small(name)):
                path = f"package/icons/{variant}.svg"
                if path not in names:
                    if variant == name:
                        raise SystemExit(f"{name} is not in @fluentui/svg-icons {VERSION}")
                    print(f"  no 16 px design of {name}: the 20 px one is scaled")
                    continue
                member = archive.extractfile(path)  # read, never unpacked
                assert member is not None
                icons[variant] = minify(member.read(), variant)
    for name in files:
        if "." in name:
            stem, locale = name.split(".", 1)
            for variant in (stem, small(stem)):
                icons[f"{variant}.{locale}"] = minify(
                    download(localized_url(variant, locale)), f"{variant}.{locale}"
                )
    licence = download(REPO + "LICENSE").decode("utf-8").replace("\r\n", "\n").strip()
    if "MIT License" not in licence:
        raise SystemExit("unexpected licence text")

    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("*.svg"):
        if old.stem not in icons:
            old.unlink()
    for name, svg in icons.items():
        (OUT / f"{name}.svg").write_text(svg, encoding="utf-8", newline="\n")
    (OUT / "LICENSE.txt").write_text(
        f"Fluent UI System Icons {VERSION} (subset)\n"
        "https://github.com/microsoft/fluentui-system-icons\n"
        "Written by tools/fetch_icons.py; do not edit by hand.\n\n" + licence + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(f"Wrote {len(icons)} icons to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    sys.exit(main())
