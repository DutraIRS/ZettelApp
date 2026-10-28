# Erste Schritte

## Installieren

ZettelApp läuft unter **Windows 10 (21H2 oder höher) und Windows 11, 64-Bit**. Laden Sie die App von der
[neuesten Version](https://github.com/DutraIRS/ZettelApp/releases/latest) herunter:

| Download | Verwenden Sie diese Version, wenn … |
|---|---|
| `ZettelApp-Setup.exe` | Sie eine normale Installation mit Eintrag im Startmenü, Deinstallationsprogramm unter *Einstellungen ▸ Apps* und `zettelapp://`-Links wünschen, die Notizen aus Anki öffnen. Administratorrechte sind nicht erforderlich: Die Installation gilt nur für Ihr Konto. |
| `ZettelApp-Portable.zip` | Sie keine Software installieren können oder die App von einem USB-Laufwerk ausführen möchten. Entpacken Sie das Archiv an einem beliebigen Ort und starten Sie `ZettelApp.exe`. |

Das Installationsprogramm fragt nach der Sprache und schlägt die Anzeigesprache von Windows vor. Das
Installationsprogramm und die App sind in 11 Sprachen übersetzt; die Sprache der App ändern Sie unter
*Optionen*.

Für jede Version sind SHA-256-Prüfsummen aufgeführt (`SHA256SUMS.txt`). So prüfen Sie einen Download in PowerShell:

```powershell
Get-FileHash .\ZettelApp-Setup.exe -Algorithm SHA256
```

### „Windows hat Ihren PC geschützt“

Die Builds sind noch nicht signiert. Daher kann Microsoft Defender SmartScreen beim ersten Start des
Installationsprogramms eine Warnung anzeigen. Wenn Sie das Programm von der offiziellen Release-Seite
heruntergeladen haben und die Prüfsumme stimmt, wählen Sie **Weitere Informationen ▸ Trotzdem ausführen**.
Die Codesignierung steht auf der [Roadmap](https://github.com/DutraIRS/ZettelApp/blob/main/ROADMAP.md).

## Ihr erster Tresor

Ein **Tresor** ist ein Ordner mit Ihren Notizen: einer Datenbankdatei (`zettel.db`) und einem Ordner
`assets` für Bilder. Beim ersten Start erstellt ZettelApp einen Tresor in **Documents\ZettelApp** mit elf
verknüpften Startnotizen. Die Notiz *Welcome to ZettelApp* führt Sie durch Links, Tags, Bilder, Mindmaps,
Lernkarten und die übrigen Funktionen der App. Optional bietet ein zehnminütiges Abenteuer dieselbe
Einführung anhand echter Aktionen. Neue Tresore, die Sie über *Datei ▸ Neuen Tresor…* oder *Datei ▸ Tresor
öffnen…* erstellen, erhalten dieselben Startinhalte. So können Sie an einem anderen Ort arbeiten, zum
Beispiel in einem OneDrive-Ordner. Unter *Datei ▸ Zuletzt geöffnet* finden Sie die zuletzt verwendeten Tresore.

Notizen werden beim Tippen automatisch gespeichert. Es gibt keine Schaltfläche zum Speichern.

## Rundgang durch das Fenster

![Die Seite „Notizen“](../website/assets/screenshots/notes-light.png)

Mit der **Navigationsleiste** links wechseln Sie zwischen den Seiten (Ctrl+1 bis Ctrl+5):

- **Notizen**: Notizliste, Editor und Seitenleiste.
  - Die *Liste* enthält Suche (auch Filter wie `tag:name`), Tagfilter, Sortierung und den Papierkorb.
  - Der *Editor* enthält Titel, Tags, einen optionalen Quellenlink und Registerkarten für die **Notiz** (Markdown mit den Modi Bearbeiten, Geteilte Ansicht und Vorschau), ihre **Mindmap** und ihre **Lernkarten**.
  - Die *Seitenleiste* zeigt **Linkvorschläge**, die **Links** der Notiz und ihre **Backlinks**.
- **Graph**: Ihre Notizen als Netzwerk in 2D oder 3D, nach Tag oder Themencluster eingefärbt.
- **Einblicke**: Statistiken und Diagramme zu Ihrem Tresor.
- **Wiederholen**: Wiederholungen mit verteiltem Wiederholen, Quizfragen und Anki.
- **Fragen**: Stellen Sie Fragen zu Ihren Notizen mit einem KI-Anbieter Ihrer Wahl (optional).

Unter **Optionen** (unten in der Navigationsleiste oder über *Werkzeuge ▸ Optionen…*, Ctrl+,) finden Sie
Einstellungen für Design, Editor-Schriftgröße, Linkvorschläge, Linktypen, KI, MCP-Server, Anki, Zotero,
Windows-Integration und Sicherungen.

Die App übernimmt die **helle/dunkle** Darstellung und **Akzentfarbe** von Windows. Unter *Ansicht ▸ Design*
können Sie ein Design festlegen.

## Aktualisierungen

Etwa vier Sekunden nach dem Start sendet ZettelApp eine HTTPS-Anfrage an
`https://dutrairs.github.io/ZettelApp/version.json`, um die neueste Version zu ermitteln. Es werden keine
weiteren Informationen gesendet (nur ein User-Agent `ZettelApp/<version>`). Wenn die Anfrage fehlschlägt,
sehen Sie nichts. Ist eine neuere Version verfügbar, erscheint höchstens einmal pro Version ein kleiner
Hinweis unten rechts. Er stiehlt nie den Fokus. **Herunterladen** öffnet die Releases-Seite im Browser,
**✕** schließt den Hinweis und **Nicht nach Aktualisierungen suchen** schaltet die Suche aus. Sie können sie
unter *Werkzeuge ▸ Optionen ▸ Allgemein ▸ Beim Start von ZettelApp nach Aktualisierungen suchen* wieder
aktivieren. ZettelApp installiert niemals selbst etwas.

## Deinstallieren

Verwenden Sie *Windows-Einstellungen ▸ Apps ▸ Installierte Apps ▸ ZettelApp ▸ Deinstallieren*. Nach Ihrer
Bestätigung bietet ein Dialog die nicht aktivierte Option **Auch meine ZettelApp-Einstellungen und -Daten
löschen** an. Sie entfernt Ihre Einstellungen, gespeicherten API-Schlüssel, Protokolle, den Cache und
automatische Sicherungen (`%LOCALAPPDATA%\ZettelApp`) **sowie alle Ihre Notizen** (die Datenbank und
Anhänge Ihrer Tresore). Lassen Sie die Option deaktiviert, um Ihre Notizen zu behalten. Bei der portablen
Version löschen Sie deren Ordner.

## Nächste Schritte

- Lernen Sie die Notizsyntax unter [Notizen und Links](notes-and-links.md) kennen.
- Lesen Sie, wie [Linkvorschläge](link-suggestions.md) funktionieren.
- Drücken Sie jederzeit **F1**, um diese Dokumentation zu öffnen, oder lesen Sie die
  [Tastenkombinationen](keyboard-shortcuts.md).
