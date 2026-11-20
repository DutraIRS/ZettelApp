# PyInstaller build for Linux: one folder containing two executables that share the same libraries.
#   zettelapp       - the desktop app (windowed)
#   zettelapp-mcp   - the MCP server (console: MCP clients talk to it over stdin/stdout)
# Run through packaging/build-linux.sh, which packs the folder into a portable .tar.gz and a .deb.
# The Windows spec (zettelapp.spec) stays separate: Linux has no version resource or .ico to embed.

from pathlib import Path

ROOT = Path(SPECPATH).parent

datas = [(str(ROOT / "zettelapp" / "resources"), "zettelapp/resources")]
# Qt modules the app never uses; leaving them out keeps the download small.
excludes = ["tkinter", "PySide6.QtQml", "PySide6.QtQuick", "PySide6.QtPdf", "PySide6.QtOpenGL",
            "PySide6.QtMultimedia", "PySide6.QtSql", "PySide6.QtTest", "PySide6.QtDesigner"]
# The app only uses the system local timezone (datetime.astimezone()), never ZoneInfo. pydantic imports
# zoneinfo, which makes PyInstaller's zoneinfo hook request tzdata; it is not installed, so skip it.
excludes.append("tzdata")


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
    name="zettelapp",
    console=False,
    upx=False,
)
mcp_exe = EXE(
    PYZ(mcp.pure),
    mcp.scripts,
    [],
    exclude_binaries=True,
    name="zettelapp-mcp",
    console=True,
    upx=False,
)
COLLECT(
    app_exe, app.binaries, app.datas,
    mcp_exe, mcp.binaries, mcp.datas,
    name="ZettelApp",
    upx=False,
)