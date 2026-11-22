#!/usr/bin/env bash
# Builds ZettelApp for Linux.
#
# Produces, in dist/:
#   ZettelApp/                     the app folder (zettelapp + zettelapp-mcp)
#   ZettelApp-Linux-x86_64.tar.gz  the same folder, portable archive
#   ZettelApp-Linux-amd64.deb      the .deb package (needs dpkg-deb; skipped otherwise)
#   SHA256SUMS-linux.txt           checksums for the downloads
#
# The names carry no version, like the Windows downloads, so the website can link to
# /releases/latest/download/<name>; the version is inside the package.
#
# Needs Python 3.12+ with requirements-dev.txt installed. The PyInstaller binaries bundle
# Python, Qt and the wheels; the .deb additionally Depends on the system libraries Qt talks
# to (X11/Wayland/GL) and on libsecret for the keyring. Validate afterwards with:
#   dpkg-deb -I dist/ZettelApp-Linux-amd64.deb
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

python="python3"
if [ -x ".venv/bin/python" ]; then python=".venv/bin/python"; fi
version="$("$python" -c 'import zettelapp; print(zettelapp.__version__)')"
echo "Building ZettelApp $version"

rm -rf dist build
"$python" -m PyInstaller --noconfirm --clean --distpath dist --workpath build/pyinstaller \
    packaging/zettelapp-linux.spec

# The packaged app must import every module and build its window (offscreen, no UI shown).
QT_QPA_PLATFORM=offscreen dist/ZettelApp/zettelapp --self-test
mcp_version="$(dist/ZettelApp/zettelapp-mcp --version)"
echo "Self-tests passed ($mcp_version)"

# Portable archive: unpack anywhere and run ZettelApp/zettelapp.
tar -C dist -czf "dist/ZettelApp-Linux-x86_64.tar.gz" ZettelApp

# .deb package. A version such as 1.4.0-rc1 becomes 1.4.0~rc1 (Debian's pre-release order).
deb_version="${version%%-*}"
if [ "$deb_version" != "$version" ]; then deb_version="${deb_version}~${version#*-}"; fi
staging=build/deb
install -d "$staging/DEBIAN" \
    "$staging/usr/lib" "$staging/usr/bin" \
    "$staging/usr/share/applications" "$staging/usr/share/metainfo" \
    "$staging/usr/share/icons/hicolor/256x256/apps" "$staging/usr/share/icons/hicolor/512x512/apps" \
    "$staging/usr/share/icons/hicolor/scalable/apps" "$staging/usr/share/doc/zettelapp"
cp -r dist/ZettelApp "$staging/usr/lib/ZettelApp"

for tool in zettelapp zettelapp-mcp; do
    cat > "$staging/usr/bin/$tool" <<WRAPPER
#!/bin/sh
exec /usr/lib/ZettelApp/$tool "\$@"
WRAPPER
    chmod 755 "$staging/usr/bin/$tool"
done

install -m 644 packaging/io.github.dutairs.zettelapp.desktop "$staging/usr/share/applications/"
install -m 644 packaging/io.github.dutairs.zettelapp.metainfo.xml "$staging/usr/share/metainfo/"
install -m 644 zettelapp/resources/icon-256.png \
    "$staging/usr/share/icons/hicolor/256x256/apps/io.github.dutairs.zettelapp.png"
install -m 644 website/assets/icon-512.png \
    "$staging/usr/share/icons/hicolor/512x512/apps/io.github.dutairs.zettelapp.png"
install -m 644 zettelapp/resources/icon.svg \
    "$staging/usr/share/icons/hicolor/scalable/apps/io.github.dutairs.zettelapp.svg"
install -m 644 packaging/debian-copyright "$staging/usr/share/doc/zettelapp/copyright"
gzip -9n < CHANGELOG.md > "$staging/usr/share/doc/zettelapp/changelog.gz"
chmod 644 "$staging/usr/share/doc/zettelapp/changelog.gz"

# Debian permissions whatever the build umask: folders 755, files 644, programs 755
# (shared libraries are not programs).
find "$staging/usr" -type d -exec chmod 755 {} +
find "$staging/usr" -type f -exec chmod u+rw,go+r,go-w {} +
find "$staging/usr" -type f -name "*.so*" -exec chmod 644 {} +

# The newest glibc symbol any bundled binary needs (system libraries PyInstaller copied from the
# build machine raise it): the oldest distribution the package runs on.
glibc="$(find dist/ZettelApp -type f \( -name '*.so*' -o -perm -u+x \) -exec objdump -T {} + 2>/dev/null \
    | grep -oE 'GLIBC_[0-9]+\.[0-9]+' | sed 's/GLIBC_//' | sort -uV | tail -1 || true)"
echo "Needs glibc ${glibc:-2.31} or newer"

cat > "$staging/DEBIAN/control" <<CONTROL
Package: zettelapp
Version: $deb_version
Architecture: amd64
Maintainer: ZettelApp contributors <https://github.com/DutraIRS/ZettelApp>
Installed-Size: $(du -sk --exclude=DEBIAN "$staging/usr" | cut -f1)
Depends: libc6 (>= ${glibc:-2.31}), libdbus-1-3, libegl1, libfontconfig1, libgl1, libsecret-1-0, libwayland-client0, libx11-6, libxkbcommon0, libxkbcommon-x11-0, libxcb-cursor0, libxcb-icccm4, libxcb-keysyms1, libxcb-shape0, libxcb-xinerama0, libxcb-xkb1, desktop-file-utils, xdg-utils
Recommends: gnome-keyring | kwalletd6 | kwalletd5, libglib2.0-bin, fonts-noto-cjk
Suggests: anki, zotero
Section: editors
Priority: optional
Homepage: https://dutrairs.github.io/ZettelApp/
Description: Zettelkasten note-taking app with typed links, a graph and link suggestions
 Atomic notes in Markdown with typed, optionally directed links, mind maps,
 flashcards and quizzes, a 2D/3D knowledge graph with topic clusters,
 typo-tolerant and semantic search, Zotero and Anki integration, and an MCP
 server for Claude Desktop and Claude Code. API keys are stored in the Secret
 Service (GNOME Keyring / KWallet); notes stay on your computer. The
 zettelapp:// scheme handler lets links on Anki cards open the matching note.
CONTROL

cat > "$staging/DEBIAN/postinst" <<'POSTINST'
#!/bin/sh
set -e
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database -q /usr/share/applications || true
fi
exit 0
POSTINST
chmod 755 "$staging/DEBIAN/postinst"

dpkg-deb --build --root-owner-group "$staging" "dist/ZettelApp-Linux-amd64.deb"

# Checksums for the release page (the Windows workflow merges these into SHA256SUMS.txt).
{
    sha256sum "dist/ZettelApp-Linux-x86_64.tar.gz" "dist/ZettelApp-Linux-amd64.deb"
} | sed "s#  dist/#  #" > dist/SHA256SUMS-linux.txt

echo "Done: $(pwd)/dist"
ls -lh dist