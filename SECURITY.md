# Security policy

What ZettelApp sends over the network (only a version check, unless you use the AI assistant or
download the search model) is described in [PRIVACY.md](PRIVACY.md).

## Reporting a vulnerability

Please **do not open a public issue** for security problems. Instead, report them privately with
GitHub's private vulnerability reporting:
[**Report a vulnerability**](https://github.com/DutraIRS/ZettelApp/security/advisories/new).

Please include:

- the ZettelApp version (*Help ▸ About*) and your Windows version or Linux distribution;
- what an attacker could do, and what they would need (for example a crafted note, archive, link or
  image);
- steps or a file to reproduce it.

You can expect an acknowledgement within a week. Fixes are released as soon as practical, and credited
in the changelog unless you prefer otherwise.

## Supported versions

| Version | Supported |
|---|---|
| 1.3.x | ✅ |
| older | ❌ |

Security fixes go into the latest release. Please update through *Help ▸ Check for Updates*.

## Security model in brief

ZettelApp is a local desktop app. It treats note contents, imported files, `zettelapp://` links and
responses from local or remote services as **untrusted**:

- Notes are rendered without raw HTML or scripts, and images load only from the vault's own folder.
- Links are limited to web, e-mail, note and specific Zotero links. On Linux, links to local files are
  restricted to absolute paths on the same machine: network shares, `file://` URLs with a host and
  control characters are refused before any lookup.
- Images are verified by content, and SVG is refused.
- Archives are checked for path traversal and decompression bombs. Imported fields are validated and
  size-limited.
- Database access uses bound parameters only.
- The `zettelapp://` handler can only open a note by its ID, and the single-instance channel is
  restricted to the current user.
- Connections to Anki and Zotero are restricted to `127.0.0.1` and never use a proxy.
- AI models get no tools.
- API keys are stored in the system keyring (Windows Credential Manager, or the Linux Secret Service
  through GNOME Keyring / KWallet) and scrubbed from error messages.
- The MCP server is read-only unless the user enables writes in two places.

Details: [docs/privacy-and-security.md](docs/privacy-and-security.md).
