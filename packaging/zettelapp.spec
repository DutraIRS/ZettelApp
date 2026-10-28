# PyInstaller build: one folder containing two executables that share the same libraries.
#   ZettelApp.exe      - the desktop app (windowed)
#   zettelapp-mcp.exe  - the MCP server (console: MCP clients talk to it over stdin/stdout)
# Run through packaging/build.ps1, which also writes build/version_info.txt.
# A one-folder build starts faster than one-file and triggers fewer antivirus false positives.

from pathlib import Path

ROOT = Path(SPECPATH).parent
VERSION_FILE = str(ROOT / "build" / "version_info.txt")
ICON = str(ROOT / "zettelapp" / "resources" / "icon.ico")

datas = [(str(ROOT / "zettelapp" / "resources"), "zettelapp/resources")]
# Qt modules the app never uses; leaving them out keeps the download small.
excludes = ["tkinter", "PySide6.QtQml", "PySide6.QtQuick", "PySide6.QtPdf", "PySide6.QtOpenGL",
            "PySide6.QtMultimedia", "PySide6.QtSql", "PySide6.QtTest", "PySide6.QtDesigner"]


def analysis(script):
    return Analysis(
        [str(ROOT / script)],
        pathex=[str(ROOT)],
        datas=datas,
        hiddenimports=["zettelapp.mcp_main"],
        excludes=excludes,
        noarchive=False,
    )


app = analysis("packaging/launcher.py")
mcp = analysis("packaging/mcp_launcher.py")

app_exe = EXE(
    PYZ(app.pure),
    app.scripts,
    [],
    exclude_binaries=True,
    name="ZettelApp",
    icon=ICON,
    version=VERSION_FILE,
    console=False,
    upx=False,
)
mcp_exe = EXE(
    PYZ(mcp.pure),
    mcp.scripts,
    [],
    exclude_binaries=True,
    name="zettelapp-mcp",
    icon=ICON,
    version=VERSION_FILE,
    console=True,
    upx=False,
)
COLLECT(
    app_exe, app.binaries, app.datas,
    mcp_exe, mcp.binaries, mcp.datas,
    name="ZettelApp",
    upx=False,
)
