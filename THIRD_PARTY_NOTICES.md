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
| ONNX Runtime (semantic search) | MIT | https://github.com/microsoft/onnxruntime |
| Tokenizers (semantic search) | Apache-2.0 | https://github.com/huggingface/tokenizers |
| Anthropic Python SDK | MIT | https://github.com/anthropics/anthropic-sdk-python |
| Fluent UI System Icons (icons where the Segoe icon fonts are missing; see below) | MIT | https://github.com/microsoft/fluentui-system-icons |
| httpx2, httpcore2, h11, anyio, sniffio, idna, jiter, pydantic, pydantic-core, typing-extensions, typing-inspection, annotated-types, docstring-parser, opentelemetry-api (dependencies of the Anthropic SDK) | BSD / MIT / Apache-2.0 | see each project on https://pypi.org/ |

## Semantic search model

Semantic search uses [multilingual-e5-small](https://huggingface.co/intfloat/multilingual-e5-small) (MIT
licence). It isn't part of the download: ZettelApp fetches it from Hugging Face only if you ask for it in
*Tools ▸ Options ▸ Search*.

## Qt and the LGPL

Qt for Python is used under the GNU Lesser General Public License v3. ZettelApp loads the unmodified Qt
and PySide6 libraries dynamically: they ship as separate DLL and `.pyd` files in the app folder. You may
replace them with your own builds of the same version. The source code is available from the Qt Project
at the links above. The LGPL v3 text is at https://www.gnu.org/licenses/lgpl-3.0.html.

## Fonts and icons

ZettelApp does **not** bundle any fonts. On Windows it uses the fonts that come with Windows: Segoe UI
Variable / Segoe UI for text, and Segoe Fluent Icons / Segoe MDL2 Assets for icons. These remain
Microsoft's property and are not redistributed. On Linux it uses the desktop's own fonts, and the
monochrome symbolic icons of the desktop's icon theme where one matches. The ZettelApp icon is original
artwork, drawn by `tools/make_icon.py` and in the public domain like the rest of ZettelApp.

Where the Segoe icon fonts are missing (Linux), ZettelApp draws its icons from a subset of the
[Fluent UI System Icons](https://github.com/microsoft/fluentui-system-icons), version 1.1.345 (npm
package `@fluentui/svg-icons`, plus the language-specific Bold/Italic letters from the repository at
commit `73ec879`), in `zettelapp/resources/icons/fluent/`. `tools/fetch_icons.py` downloads and
checks that release and writes the subset. They are used under the MIT License:

```text
MIT License

Copyright (c) 2020 Microsoft Corporation

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## Installer

The Windows installer is built with [Inno Setup](https://jrsoftware.org/isinfo.php) (Inno Setup
License). Its translations come from the Inno Setup project.
