# Datenschutz und Sicherheit

## Was Ihren Computer verlässt

**Nichts – außer wenn Sie es anfordern; ausgenommen ist eine kleine Aktualisierungsprüfung.** ZettelApp
hat keine Konten, Telemetrie oder Werbung und lädt während Ihrer Arbeit nichts aus dem Internet. Folgende
Netzwerkanfragen kann die App stellen:

| Wann… | ZettelApp kontaktiert | Gesendete Daten |
|---|---|---|
| Etwa 4 Sekunden nach dem Start von ZettelApp (kann deaktiviert werden) | `https://dutrairs.github.io/ZettelApp/version.json` | Eine HTTPS-Anfrage für diese Datei mit dem Header `User-Agent: ZettelApp/<version>`. Sonst nichts: keine Notizen, Einstellungen oder Kennungen. Fehler bleiben unsichtbar. Siehe [Aktualisierungen](getting-started.md#updates). |
| Sie eine Frage auf der Seite **Fragen** stellen | Den von Ihnen eingerichteten KI-Anbieter (Anthropic, OpenAI, Z.ai oder Ihren eigenen Endpunkt) | Ihre Frage und die Notizen in der Liste *Gesendete Quellen* |
| Sie die KI-Verbindung testen oder die Modellliste aktualisieren | Denselben Anbieter | Ihren API-Schlüssel zur Authentifizierung |
| Sie **Mit Anki synchronisieren** verwenden | AnkiConnect auf **diesem Computer** (`127.0.0.1`) | Die Lernkarten im ausgewählten Bereich |
| Sie **Einfügen ▸ Zotero-Referenz** oder *Verbindung testen* in den Zotero-Optionen verwenden | Zotero auf **diesem Computer** (`127.0.0.1`) | Ihre Suchbegriffe (nur lesender Zugriff) |
| Sie auf einen Weblink klicken oder *Hilfe ▸ Website / Dokumentation / Nach Aktualisierungen suchen* oder auf **Herunterladen** im Aktualisierungshinweis klicken | Ihr Webbrowser öffnet die Seite | Nichts von ZettelApp |

Um die Aktualisierungsprüfung zu beenden, deaktivieren Sie *Werkzeuge ▸ Optionen ▸ Allgemein ▸ Beim Start
von ZettelApp nach Aktualisierungen suchen*. ZettelApp stellt danach keine Anfrage, bis Sie eine Frage
stellen oder eine der anderen oben genannten Funktionen nutzen.

Lokale Verbindungen zu Anki und Zotero verwenden nie einen Proxy und können daher nicht von Ihrem Computer
weggeleitet werden. Der MCP-Server stellt überhaupt keine Netzwerkanfragen.

## Wo Ihre Daten liegen

| Daten | Speicherort |
|---|---|
| Notizen, Links, Lernkarten, Wiederholungsverlauf | Ihr Tresorordner: `zettel.db` (SQLite). Standardmäßig **Documents\ZettelApp**. |
| Bilder | Der Ordner `assets` im Tresor. |
| Einstellungen | Die Registrierung unter `HKEY_CURRENT_USER\Software\ZettelApp\ZettelApp`. |
| API-Schlüssel | **Windows-Anmeldeinformations-Manager** (`ZettelApp/llm/…`), nie in Dateien oder der Registrierung. |
| Protokolle | `%LOCALAPPDATA%\ZettelApp\Logs` (rotierte Protokolle, höchstens einige MB). Sie enthalten Fehler, aber keine Notizen und niemals API-Schlüssel. |
| Automatische Sicherungen | `%LOCALAPPDATA%\ZettelApp\Backups` |
| Kleiner UI-Cache | `%LOCALAPPDATA%\ZettelApp\Cache` |

Der Tresor ist ein gewöhnlicher Ordner: Sie können ihn kopieren, sichern oder in OneDrive aufbewahren.
ZettelApp schreibt die Datenbank mit vollständiger Synchronisierung, einer Einstellung für synchronisierte
Ordner. Vermeiden Sie es, denselben Tresor gleichzeitig auf zwei Computern zu öffnen.

## Sicherungen und Rückgängig machen

- **Tägliche Sicherungen:** Beim ersten Öffnen eines Tresors pro Tag wird eine konsistente Kopie der Datenbank gespeichert. Die 10 neuesten Sicherungen bleiben erhalten (*Optionen ▸ Sicherungen*). Über *Datei ▸ Tresor jetzt sichern* erstellen Sie jederzeit eine Sicherung. Bilder werden nach ihrem Inhalt gespeichert und nie automatisch gelöscht.
- **Papierkorb:** Gelöschte Notizen landen zunächst im Papierkorb und können bis zu dessen Leerung wiederhergestellt werden.
- **Automatisches Speichern:** Notizen werden während des Tippens gespeichert. Ein Absturzdialog meldet unerwartete Fehler und schreibt Details in das Protokoll.

## Wie ZettelApp Sie schützt

Notizen können aus Importen, dem Web oder KI-Antworten stammen. ZettelApp behandelt ihren Inhalt daher als
nicht vertrauenswürdig:

- **Keine aktiven Inhalte.** Rohes HTML in Notizen wird als Text angezeigt und nie dargestellt; in einer Notiz können keine Skripte ausgeführt werden. Die Notizvorschau lädt Bilder **nur aus dem Ordner `assets` des Tresors**, niemals aus dem Web oder anderen Orten auf der Festplatte.
- **Zulässige Links.** Beim Anklicken werden nur Webseiten (`http`/`https`), E-Mail (`mailto`), Notizen, Zotero-Links zum *Auswählen eines Eintrags* oder *Öffnen eines PDFs* sowie Links zu lokalen Dateien (siehe unten) geöffnet. `javascript:` und andere Schemas werden abgelehnt.
- **Links zu lokalen Dateien zeigen die Datei nur an.** Ein Link `file:///` öffnet **den Datei-Explorer mit ausgewählter Datei**; die Datei selbst wird weder geöffnet noch ausgeführt. Erlaubt sind nur Pfade auf lokalen Laufwerken. Netzwerkpfade (UNC) wie `\\server\share` werden abgelehnt, weil eine Abfrage Ihre Windows-Anmeldedaten an den Server senden könnte.
- **Bilder werden anhand ihres Inhalts geprüft**, nicht anhand des Dateinamens. Erlaubt sind PNG, JPEG, GIF, WebP und BMP bis 25 MB; SVG wird abgelehnt, da es Skripte enthalten kann. Die Prüfung umfasst die Dateisignatur und komprimierte Größe; beim ersten Anzeigen werden außerdem die Pixelabmessungen überprüft.
- **Sichere Importe.** Archive werden auf Pfadmanipulationen („Zip Slip“) und Dekompressionsbomben geprüft. Jedes Feld wird validiert und in der Größe begrenzt; Markdown-Importe können nicht aus dem Importordner herausgreifen. Bei einem fehlgeschlagenen Import bleibt der Tresor unverändert: Der Import läuft in einer einzelnen Datenbanktransaktion, die bei jedem Fehler zurückgerollt wird.
- **Sichere Exporte.** Exportierte Websites enthalten keine Skripte und verwenden eine strikte Content-Security-Policy. Dateien werden atomar geschrieben.
- **Sicherheit der Datenbank.** Alle Datenbankabfragen verwenden gebundene Parameter; Suchtext wird nie als Abfragesyntax interpretiert.
- **`zettelapp://`-Links** (für Anki-Karten) können ausschließlich *eine Notiz anhand ihrer ID öffnen*. Alle anderen Anfragen werden ignoriert.
- **Nur eine Instanz pro Benutzer.** Ein zweiter Start übergibt seine Anfrage über eine Windows-Named-Pipe an die bereits laufende App, auf die nur Ihr Benutzerkonto zugreifen kann.
- **KI-Sicherheit.** Das KI-Modell erhält keine Tools. Versteckte Anweisungen in einer Notiz können es daher nicht zu Aktionen veranlassen; seine Antwort wird mit demselben sicheren Renderer angezeigt. API-Schlüssel bleiben im Anmeldeinformations-Manager und werden aus Fehlermeldungen entfernt.
- **MCP-Server und Schalter.** MCP-Clients können nur dann auf Ihre Notizen zugreifen, wenn ZettelApp geöffnet **und** der MCP-Schalter in der Statusleiste eingeschaltet ist. Bei jedem Start ist der Schalter aus und wird nie gespeichert. Standardmäßig ist der Server schreibgeschützt. Er läuft nur, wenn Ihr MCP-Client ihn startet, und verwendet Standardein- und -ausgabe ohne Netzwerkport. Siehe [MCP-Server](mcp-server.md).

## Deinstallieren

Deinstallieren Sie ZettelApp unter *Windows-Einstellungen ▸ Apps ▸ Installierte Apps ▸ ZettelApp ▸
Deinstallieren*. Das Deinstallationsprogramm bietet die standardmäßig deaktivierte Option **Auch meine
ZettelApp-Einstellungen und -Daten löschen**. Wenn Sie sie aktivieren, werden Ihre Einstellungen, die im
Anmeldeinformations-Manager gespeicherten API-Schlüssel, Protokolle, der Cache und automatische Sicherungen
(`%LOCALAPPDATA%\ZettelApp`) **sowie alle Ihre Notizen** (die Datenbank und Anhänge Ihrer Tresore) entfernt.
Wenn Sie die Option nicht aktivieren, bleiben Ihre Notizen an ihrem Speicherort.

Haben Sie ein Sicherheitsproblem gefunden? Melden Sie es bitte vertraulich; siehe
[SECURITY.md](https://github.com/DutraIRS/ZettelApp/blob/main/SECURITY.md).
