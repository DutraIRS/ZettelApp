# FAQ

### Ist ZettelApp kostenlos?

Ja. Die App ist kostenlos und quelloffen und wurde unter der [Unlicense](https://github.com/DutraIRS/ZettelApp/blob/main/LICENSE)
in die Gemeinfreiheit überführt. Die optionale KI-Funktion verwendet Ihren eigenen API-Schlüssel, daher
rechnet der Anbieter direkt mit Ihnen ab.

### Wie kann ich ZettelApp unterstützen?

Vielen Dank für Ihr Interesse! Sie können die Entwicklung auf [Ko-fi](https://ko-fi.com/dutrairs)
unterstützen. Unternehmen können einen bestimmten Punkt der [Roadmap](https://github.com/DutraIRS/ZettelApp/blob/main/ROADMAP.md)
sponsern; wenden Sie sich über [GitHub](https://github.com/DutraIRS/ZettelApp) an uns. Sponsoren werden
in den Versionshinweisen erwähnt. Auch Fehlermeldungen, Verbesserungen an der Dokumentation und das
Weiterempfehlen von ZettelApp helfen.

### Benötigt die App eine Internetverbindung?

Nein. Alles funktioniert offline. Das Internet wird nur für eine kleine Aktualisierungsprüfung beim Start
(die Sie deaktivieren können), beim Stellen einer Frage auf der Seite **Fragen** und beim Öffnen eines
Links verwendet. Siehe [Datenschutz und Sicherheit](privacy-and-security.md).

### Sucht ZettelApp nach Aktualisierungen?

Ja, einmal beim Start: Die App fragt eine kleine Datei auf der Projektwebsite ab und übermittelt keine
Informationen über Sie oder Ihre Notizen. Wenn eine neuere Version verfügbar ist, erscheint unten rechts
ein Hinweis. Sie können die Suche unter *Werkzeuge ▸ Optionen ▸ Allgemein ▸ Beim Start von ZettelApp nach
Aktualisierungen suchen* oder über **Nicht nach Aktualisierungen suchen** im Hinweis ausschalten. Siehe
[Erste Schritte](getting-started.md#updates).

### Was bedeutet der MCP-Schalter in der Statusleiste?

Damit können KI-Assistenten wie Claude Desktop oder Claude Code über [MCP](mcp-server.md) Ihre Notizen
verwenden. Der Schalter ist **bei jedem Start von ZettelApp ausgeschaltet**. Solange er aus ist oder
ZettelApp geschlossen wurde, können Assistenten nicht auf Ihre Notizen zugreifen. Nachdem Sie ihn
aktiviert haben, verbinden Sie ZettelApp in Ihrem MCP-Client erneut (oder starten den Client neu).

### Kann ich ein Modell auf meinem eigenen Computer verwenden?

Ja. Wählen Sie unter *Werkzeuge ▸ Optionen ▸ KI-Assistent* **OpenAI** und geben Sie unter **Endpunkt**
Ihren lokalen Server an, zum Beispiel `http://localhost:11434/v1` (Ollama) oder
`http://localhost:1234/v1` (LM Studio). Für `localhost` ist kein API-Schlüssel erforderlich. Siehe
[Eigenes LLM verwenden](ai-assistant.md#bring-your-own-llm).

### Wo sind meine Notizen gespeichert?

Im Tresorordner, standardmäßig **Documents\ZettelApp**: in einer Datenbank `zettel.db` und einem Ordner
`assets`. Mit *Datei ▸ Tresor im Datei-Explorer anzeigen* öffnen Sie den Ordner.

### Kann ich ZettelApp mit OneDrive, Dropbox oder Google Drive verwenden?

Ja. Legen Sie den Tresor in einem synchronisierten Ordner ab (*Datei ▸ Neuen Tresor…*). Schließen Sie
ZettelApp auf einem Computer, bevor Sie denselben Tresor auf einem anderen Computer öffnen, da gleichzeitige
Änderungen zu Konflikten führen können.

### Wie übertrage ich meine Daten auf einen anderen Computer?

Kopieren Sie den Tresorordner oder verwenden Sie *Datei ▸ Exportieren…* ▸ **ZettelApp-Archiv** und
importieren Sie das Archiv auf dem anderen Computer.

### Kann ich meinen Obsidian-Tresor verwenden?

Ja. *Datei ▸ Markdown-Ordner importieren…* importiert Markdown-Dateien mit Frontmatter, `#tags`, `[[links]]`
und Bildern. Ihre Obsidian-Dateien werden nicht geändert. Umgekehrt können Sie Notizen als
**Markdown-Dateien** exportieren und den Ordner in Obsidian öffnen.

### Warum haben die Zettel-IDs das Format 20261027153012?

Jede Notiz erhält bei ihrer Erstellung eine dauerhafte ID aus dem Zeitstempel (Jahr, Monat, Tag, Stunde,
Minute, Sekunde). Titel können sich ändern, IDs nicht; Links anhand der ID gehen daher nie kaputt. Sie
müssen die IDs selten sehen.

### Was unterscheidet einen Link im Text von einem Link in der Seitenleiste?

Beides sind echte Links. `[[Links]]` im Text gehören zum Geschriebenen und werden entfernt, wenn Sie sie
aus dem Text löschen. Über **Link hinzufügen…** oder durch Annahme eines Vorschlags erstellte Links stehen
nicht im Text. Sie können deren Typ und Richtung in der Seitenleiste ändern oder sie dort entfernen.

### Warum steht bei einem Vorschlag nur „18 % · möglich“?

Die Zahl ist die ehrliche Schätzung des Modells, wie wahrscheinlich Sie die beiden Notizen verknüpfen
würden. In einem neuen oder dünn gefüllten Tresor sind die meisten Notizpaare nicht miteinander verwandt,
daher fallen auch gute Vorschläge zunächst niedrig aus. Am wichtigsten ist die Reihenfolge der Vorschläge;
die Schätzungen werden besser, wenn Sie Links annehmen und Vorschläge ablehnen. Siehe
[Linkvorschläge](link-suggestions.md).

### Funktioniert die App unter macOS oder Linux?

Noch nicht. Linux-Pakete (.deb, AppImage) und macOS stehen auf der
[Roadmap](https://github.com/DutraIRS/ZettelApp/blob/main/ROADMAP.md).

### Ist die App in weiteren Sprachen verfügbar?

Ja. Das Installationsprogramm und die App sind auf Spanisch, brasilianischem Portugiesisch, Französisch,
Deutsch, Italienisch, Russisch, vereinfachtem Chinesisch, Japanisch, Koreanisch und Arabisch verfügbar.
Die App verwendet standardmäßig die Sprache von Windows; ändern Sie sie unter *Optionen*. Fehlende Texte
werden auf Englisch angezeigt.

### Wie deinstalliere ich die App und was geschieht mit meinen Daten?

*Einstellungen ▸ Apps ▸ Installierte Apps ▸ ZettelApp ▸ Deinstallieren*. Das Deinstallationsprogramm
bietet die standardmäßig deaktivierte Option **Auch meine ZettelApp-Einstellungen und -Daten löschen** an.
Wenn Sie sie aktivieren, werden Einstellungen, gespeicherte API-Schlüssel, Protokolle, Cache und
automatische Sicherungen **sowie alle Ihre Notizen** (Datenbanken und Anhänge Ihrer Tresore) entfernt.
Wenn Sie die Option nicht aktivieren, bleiben Ihre Notizen erhalten. Bei der portablen Version löschen Sie
deren Ordner; ihre Einstellungen liegen in der Registrierung unter `HKEY_CURRENT_USER\Software\ZettelApp`,
Protokolle und Sicherungen unter `%LOCALAPPDATA%\ZettelApp`.

### Es ist ein Fehler aufgetreten. Wo finde ich die Protokolle?

Unter `%LOCALAPPDATA%\ZettelApp\Logs`. Fügen Sie dem
[Fehlerbericht](https://github.com/DutraIRS/ZettelApp/issues) bitte den relevanten Abschnitt bei. Prüfen
Sie vorher, dass er keine privaten Informationen enthält.
