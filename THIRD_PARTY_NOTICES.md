# Third-party notices

ZettelApp itself is released into the public domain under [The Unlicense](LICENSE). It is built on the
open-source components below, which keep their own licences. The Windows builds include them as
separate files: libraries are dynamically linked, not merged into ZettelApp's code.

| Component | Licence | Source |
|---|---|---|
| Qt 6 / Qt for Python (PySide6, Shiboken6) | GNU LGPL v3 | https://www.qt.io/ · https://code.qt.io/cgit/pyside/pyside-setup.git/ |
| CPython | Python Software Foundation License | https://www.python.org/ |
| NumPy | BSD 3-Clause | https://github.com/numpy/numpy |
| RapidFuzz | MIT | https://github.com/rapidfuzz/RapidFuzz |
| genanki | MIT | https://github.com/kerrickstaley/genanki |
| chevron (used by genanki) | MIT | https://github.com/noahmorrison/chevron |
| frozendict (used by genanki) | LGPL v3 | https://github.com/Marco-Sulla/python-frozendict |
| cached-property (used by genanki) | BSD 3-Clause | https://github.com/pydanny/cached-property |
| markdown-it-py | MIT | https://github.com/executablebooks/markdown-it-py |
| mdurl | MIT | https://github.com/executablebooks/mdurl |
| PyYAML | MIT | https://github.com/yaml/pyyaml |
| Anthropic Python SDK | MIT | https://github.com/anthropics/anthropic-sdk-python |
| httpx2, httpcore2, h11, anyio, sniffio, idna, jiter, pydantic, pydantic-core, typing-extensions, typing-inspection, annotated-types, docstring-parser, opentelemetry-api (dependencies of the Anthropic SDK) | BSD / MIT / Apache-2.0 | see each project on https://pypi.org/ |

## Qt and the LGPL

Qt for Python is used under the GNU Lesser General Public License v3. ZettelApp loads the unmodified Qt
and PySide6 libraries dynamically: they ship as separate DLL and `.pyd` files in the app folder. You may
replace them with your own builds of the same version. The source code is available from the Qt Project
at the links above. The LGPL v3 text is at https://www.gnu.org/licenses/lgpl-3.0.html.

## Fonts and icons

ZettelApp does **not** bundle any fonts. It uses the fonts that come with Windows: Segoe UI Variable /
Segoe UI for text, and Segoe Fluent Icons / Segoe MDL2 Assets for icons. These remain Microsoft's
property and are not redistributed. The ZettelApp icon is original artwork, drawn by
`tools/make_icon.py` and in the public domain like the rest of ZettelApp.

## Installer

The Windows installer is built with [Inno Setup](https://jrsoftware.org/isinfo.php) (Inno Setup
License). Its translations come from the Inno Setup project.
