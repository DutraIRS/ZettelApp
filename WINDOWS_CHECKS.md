# Checks needed on Windows

Requests from the Linux review (`LINUX_REVIEW_PLAN.md` on the Linux machine's desktop) for whoever works
on the Windows machine. The Linux work is on branch `linux-port`. Linux-only changes must leave
Windows untouched, but some code is shared, and some answers only Windows can give. Tick an item when
it's done and write the result under it (a screenshot path, a log excerpt, or "same as before").

## Screenshots

- [ ] **Fresh reference screenshots.** `website/assets/screenshots/*.png` were taken before 1.3.1, so
  they predate the sort-order icon and the "LSA" wording. Run `python tools/screenshots.py` on
  Windows (current `linux-port` code) and commit the 18 images, so Linux can be compared with today's
  Windows look.
- [ ] **The same screenshots at 150% scaling.** Run `python tools/screenshots.py <folder>` with
  `QT_SCALE_FACTOR=1.5`; Linux compares its HiDPI rendering against these.

## Behaviour only Windows can show

- [ ] **How alarms and reminders notify.** Set an alarm on a note, let it fire with ZettelApp in the
  background and minimised, and describe exactly what the user sees and hears: a tray balloon, a
  Windows toast, a sound, a window coming forward. Linux must offer the same.
- [ ] **The accent colour.** With the Windows accent set to something other than blue, confirm the
  app still takes it (light and dark). `zettelapp/ui/theme.py` was reworked for Linux.

## Regression checks after the Linux changes

- [ ] **Full test suite on Windows:** `pytest` on `linux-port`, all passing. Report any failure.
- [ ] **Icons still come from Segoe Fluent Icons** (`zettelapp/ui/icons.py` now has native and
  bundled-SVG fallbacks for Linux): the nav rail, toolbar and Bold/Italic letters look as before.
- [ ] **Mind map link marker** (`zettelapp/ui/mindmap.py` now draws it through `icons.paint`): in a
  note's *Mind map* tab, right-click an idea ▸ link it to a note; the chain glyph still shows at the
  idea's right end, in the text colour, light and dark, as before.
- [ ] **Graphviz export** (`File ▸ Export ▸ Graphviz`): the `.dot` file still says
  `fontname="Segoe UI"` on Windows.
- [ ] **API keys** in Windows Credential Manager: save, read and delete a key (Options ▸ AI);
  `zettelapp/core/secrets.py` changed for Linux.
- [ ] **MCP switch** (`zettelapp/mcp_switch.py`): with the status-bar switch on, an MCP client can
  call tools; switched off or with ZettelApp closed, it is refused.
- [ ] **Packaging:** `pwsh packaging/build.ps1` still builds; the installed app shows its icons
  (the spec now ships `zettelapp/resources/icons/`).
- [ ] **Update notice** (`zettelapp/ui/update_notice.py`, `download_url()` now takes the version):
  with an installed copy, *Download* still opens the `ZettelApp-Setup.exe` link; with the portable
  zip, the release page. `pytest tests/test_updates.py` runs the Windows test there.
- [ ] **Single instance** (`zettelapp/app.py`, the socket name changed on Linux only): a second
  launch and a `zettelapp://note/<id>` link from Anki still bring the running window forward.
- [ ] **Options ▸ AI wording:** the key hint and "Key … saved on this computer." read as before
  (the new "No system keyring was found…" text is for Linux without a Secret Service only).

- [ ] **Which folder file dialogs open in.** *Insert ▸ Image…*, *Insert ▸ Link to a File…*, the mind
  map export and *Save graph as image* pass no folder. Confirm that Windows reopens the folder used
  last (also after a restart), and that the save dialogs propose that folder, not ZettelApp's
  install folder. Linux now does the same itself (it opened the working folder before).
- [ ] **Alarm toast click.** Confirm that clicking the alarm toast opens the alarmed note and
  whether it also un-maximises a maximised window (`showNormal()` in `_open_alarm_note`); Linux now
  sends the same alarm to the desktop's notification service and opens the note on *Open note*.

## Data only Windows can provide

- [ ] **A vault made on Windows,** zipped as it is on disk (`zettel.db` plus its assets folder),
  with a few notes holding pictures, attachments, typed links, flashcards with review history and a
  link to a `C:\...` file. Linux checks that it opens and that the `C:\` link shows as unavailable.
