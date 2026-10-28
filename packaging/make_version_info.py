"""Write the Windows version resource (Properties ▸ Details) for the executables.

Usage: python packaging/make_version_info.py <version> <output file>
"""

import sys
from pathlib import Path

TEMPLATE = """VSVersionInfo(
  ffi=FixedFileInfo(filevers={tuple}, prodvers={tuple}, mask=0x3f, flags=0x0, OS=0x40004,
                    fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[
    StringFileInfo([StringTable('040904B0', [
      StringStruct('CompanyName', 'ZettelApp contributors'),
      StringStruct('FileDescription', 'ZettelApp'),
      StringStruct('FileVersion', '{version}'),
      StringStruct('InternalName', 'ZettelApp'),
      StringStruct('LegalCopyright', 'Public domain (The Unlicense)'),
      StringStruct('OriginalFilename', 'ZettelApp.exe'),
      StringStruct('ProductName', 'ZettelApp'),
      StringStruct('ProductVersion', '{version}')])]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""


def main() -> None:
    version, output = sys.argv[1], Path(sys.argv[2])
    numbers = [int(part) for part in version.split("-")[0].split(".")][:4]
    numbers += [0] * (4 - len(numbers))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(TEMPLATE.format(tuple=tuple(numbers), version=version), encoding="utf-8")


if __name__ == "__main__":
    main()
