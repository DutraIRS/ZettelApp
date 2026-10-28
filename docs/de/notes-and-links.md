# Notizen und Links

## Notizen schreiben

Notizen werden in **Markdown** geschrieben: `**fett**`, `*kursiv*`, `# Überschriften`, Listen, `> Zitate`,
`` `Code` ``, Codeblöcke, Tabellen und `~~durchgestrichen~~`. Die Symbolleiste über dem Editor fügt häufig
verwendete Elemente ein; Ctrl+B und Ctrl+I funktionieren wie gewohnt. Listen werden bei Enter fortgesetzt.

Der Editor hat drei Modi (Ctrl+E wechselt zwischen ihnen): **Bearbeiten**, **Geteilte Ansicht** (Text und
Vorschau nebeneinander) und **Vorschau**.

Aus Sicherheitsgründen wird rohes HTML in einer Notiz als Text angezeigt und nie dargestellt. Links in der
Vorschau öffnen nur Webseiten (`http`, `https`), E-Mail-Adressen (`mailto`), Notizen, Zotero-Einträge und
lokale Dateien (werden im Datei-Explorer angezeigt, siehe [Links zu lokalen Dateien](#links-to-local-files)).
Siehe [Datenschutz und Sicherheit](privacy-and-security.md).

### Links folgen

- **Im Editor** folgt **Ctrl+Klick** einem `[[Notizlink]]` (und erstellt die Notiz, falls sie noch nicht existiert), einem Web-, E-Mail- oder Zotero-Link, einem Link zu einer lokalen Datei oder einem `#tag` (und listet Notizen mit diesem Tag auf). Wenn Sie auf den Text zeigen, erklärt ein Tooltip, was beim Klicken geschieht. Ein normaler Klick setzt nur den Cursor, sodass Sie den Linktext weiterhin bearbeiten können.
- **In der Vorschau** folgen Sie Links mit einem normalen Klick.

### Links zu lokalen Dateien

Mit *Einfügen ▸ Link zu einer Datei…* (oder der Ordnerschaltfläche in der Symbolleiste) wählen Sie eine
Datei aus und fügen einen Link wie `[report.pdf](file:///C:/Users/me/Documents/report.pdf)` ein. Wenn Sie
eine Datei, die kein Bild ist, in den Notiztext ziehen, passiert dasselbe. Die Datei bleibt an ihrem
Speicherort; in den Tresor wird keine Kopie eingefügt.

Wenn Sie in der Vorschau auf den Link oder im Editor bei gedrückter Ctrl-Taste darauf klicken, wird **der
Datei-Explorer mit ausgewählter Datei geöffnet**. Die Datei selbst wird weder geöffnet noch ausgeführt.
Erlaubt sind nur Pfade auf einem lokalen Laufwerk: Netzwerkpfade (UNC) wie `\\server\share\file.pdf` werden
abgelehnt, denn deren Abfrage könnte Ihre Windows-Anmeldedaten an den Server senden.

Jede Notiz hat:

- einen **Titel** (das große Feld oben);
- eine **ID**, einen Zeitstempel wie `20261027153012`, der unter dem Titel angezeigt wird (*Mehr ▸ Notiz-ID kopieren*);
- optional **Tags**, einen **Quellenlink**, ein **Titelbild**, eine **Mindmap** und **Lernkarten**.

## Links zwischen Notizen

### Wiki-Links

Tippen Sie `[[` und beginnen Sie mit der Eingabe eines Titels: ZettelApp vervollständigt ihn anhand Ihrer
Notizen. Innerhalb einer Notiz funktionieren alle diese Links:

```markdown
See [[Forgetting curve]].
See [[20261027153012]].              (by ID)
See [[Forgetting curve|the curve]].  (custom link text)
```

Ctrl+K (*Einfügen ▸ Link zu Notiz…*) öffnet eine Auswahlliste, die Titel und Text durchsucht und Sie den
Linktyp auswählen lässt. Ein Link zu einem Titel, der noch nicht existiert, wird in der Vorschau grau
angezeigt; klicken Sie darauf, um die Notiz zu erstellen. Wenn Sie später eine Notiz erstellen oder
umbenennen, werden Links, die ihren Titel enthalten, aktualisiert.

### Typisierte Links

Links können beschreiben, **wie** zwei Notizen zusammenhängen. Setzen Sie den Linktyp mit `::` vor den Link:

```markdown
supports:: [[Forgetting curve]]
contradicts:: [[Rereading notes]]
part_of:: [[Zettelkasten method]]
```

Die integrierten Linktypen sind:

| Typ | Name | Gegenrichtung | Gerichteter Link | Linie | Pfeilspitze |
|---|---|---|---|---|---|
| `related` | Steht in Beziehung zu | Steht in Beziehung zu | nein | durchgezogen, grau | keine |
| `supports` | Unterstützt | Wird unterstützt von | ja | gestrichelt, grün | ausgefülltes Dreieck |
| `contradicts` | Widerspricht | Widerspricht | nein | gepunktet, rot | keine |
| `extends` | Erweitert | Wird erweitert von | ja | Strich-Punkt, blau | ausgefülltes Dreieck |
| `example` | Beispiel für | Hat als Beispiel | ja | Strich-Punkt-Punkt, bernsteinfarben | Kreis |
| `part_of` | Teil von | Enthält | ja | langer Strich, violett | Raute |
| `cites` | Zitiert | Wird zitiert von | ja | durchgezogen, türkis | offener Pfeil |

Dies sind die Voreinstellungen eines neuen Tresors; Sie können sie ändern (siehe unten). Ein Tresor aus
einer älteren Version behält seine bisherigen Linien bei.

Ein einfacher `[[Link]]` bedeutet *Steht in Beziehung zu*.

### Gerichtete und ungerichtete Links

Ein **gerichteter** Linktyp wird von jeder Seite anders gelesen. Wenn Notiz A Notiz B *unterstützt*, zeigen
B's Backlinks A als *Wird unterstützt von* an. Gerichtete Links erhalten Pfeilspitzen im Graph und bleiben
beim Export gerichtet. **Ungerichtete** Typen wie *Steht in Beziehung zu* und *Widerspricht* lesen sich in
beide Richtungen gleich.

Um die Richtung eines falsch herum angelegten gerichteten Links umzukehren, klicken Sie in der Seitenleiste
mit der rechten Maustaste darauf und wählen **Richtung umkehren**. Links im Text kehren Sie um, indem Sie
den Text bearbeiten.

### Links in der Seitenleiste

Die Seitenleiste listet die **Links** (ausgehend) und **Backlinks** (eingehend) der Notiz jeweils mit ihrem Typ auf.

- **Link hinzufügen…** erstellt einen Link, ohne ihn in den Text zu schreiben.
- Mit der rechten Maustaste auf einen Link können Sie die andere Notiz öffnen, den Linktyp ändern, seine Richtung umkehren oder ihn entfernen. Links im Text entfernen Sie durch Bearbeiten des Textes.
- Klicken Sie in der Notizliste mit der rechten Maustaste auf eine andere Notiz und wählen Sie **Link von der geöffneten Notiz als**.

### Eigene Linktypen

Unter *Werkzeuge ▸ Optionen ▸ Linktypen* können Sie Linktypen hinzufügen, umbenennen, neu gestalten oder
entfernen. Wählen Sie einen Typ in der Liste aus und ändern Sie die Einstellungen daneben:

- **Name** und **Gegenrichtung**: So wird der Link von der Quelle bzw. vom Ziel aus gelesen. Der Name der Gegenrichtung wird nur bei gerichteten Typen verwendet.
- **Gerichtet**: Legt fest, ob der Typ von jeder Seite aus anders gelesen wird und eine Pfeilspitze erhält.
- **Farbe**: Klicken Sie auf die Farbschaltfläche, um eine beliebige Farbe zu wählen.
- **Linie**: durchgezogen, gestrichelt, gepunktet, Strich-Punkt, Strich-Punkt-Punkt oder langer Strich.
- **Pfeilspitze**: Die Spitze am Ziel eines gerichteten Links: ausgefülltes Dreieck, offener Pfeil, Raute, Kreis oder Balken.

Die Vorschau zeigt zwei Notizen, die durch einen Link verbunden sind, mit seinem Namen und der Bezeichnung
von der anderen Seite. Der Stil wird überall verwendet, wo Links angezeigt werden: im Graph, seiner Legende,
der Seitenleiste, der Linkauswahl sowie in den Exporten Website, GraphML und Graphviz. Geben Sie jedem Typ
eine eigene Linie und Farbe, damit die Typen für farbenblinde Leser und auf Papier unterscheidbar bleiben.
Ein neuer Typ erhält zunächst eine Farbe und Linie, die nur wenige andere Typen verwenden.

Verwenden Sie im Text die ID des Typs, die unter der Vorschau angezeigt wird (zum Beispiel wird aus einem
Typ namens „Inspiriert von“ `inspired_by::`). Die ID wird beim Anlegen festgelegt; durch Umbenennen eines
Typs werden Links im Text also nicht ungültig. Wenn Sie einen eigenen Typ entfernen, werden seine Links zu
Links vom Typ *Steht in Beziehung zu*; es geht nichts verloren. Integrierte Typen können umbenannt und neu
gestaltet, aber nicht entfernt werden.

## Tags

Fügen Sie Tags in das Tagfeld unter dem Titel ein (drücken Sie nach jedem Tag Enter) oder schreiben Sie sie
**im Text** mit einem Rautezeichen, etwa `#welcome` oder `#math/algebra`. Tags werden kleingeschrieben und
können mit einem Schrägstrich verschachtelt werden, zum Beispiel `math/algebra`. Eine Suche nach `math`
findet auch Notizen mit dem Tag `math/algebra`.
Verwenden Sie den Tagfilter über der Notizliste oder geben Sie `tag:name` in das Suchfeld ein.

Im Text geschriebene Tags sind echte Tags und erscheinen als **umrandete Chips** neben dem Feld *Tag
hinzufügen*. Wenn Sie `#tag` aus dem Text löschen, verschwinden sie. Ein `#tag` wird innerhalb von Code,
in Linkzielen und in `[[#headings]]` ignoriert. Tags aus dem Feld *Tag hinzufügen* sind davon unabhängig:
Sie bleiben erhalten, bis Sie sie mit ✕ entfernen. Mit Ctrl+Klick auf ein `#tag` im Editor listen Sie die
Notizen mit diesem Tag auf.

## Quellenlink

Das Feld mit dem Globussymbol enthält die **Quelle** der Notiz: eine Webseite (`https://…`), eine
E-Mail-Adresse oder einen Zotero-Eintrag (`zotero://select/library/items/…`). Die Schaltfläche daneben
öffnet den Link. Andere Linktypen werden abgelehnt. Unter [Zotero](zotero.md) erfahren Sie, wie Sie Notizen
direkt aus Ihrer Zotero-Bibliothek erstellen.

## Bilder

Fügen Sie Bilder über *Einfügen ▸ Bild…* (Ctrl+Shift+I), durch **Einfügen** aus der Zwischenablage oder
indem Sie Bilddateien auf den Editor **ziehen** ein. Unterstützte Formate: PNG, JPEG, GIF, WebP und BMP,
bis zu 25 MB. SVG wird absichtlich abgelehnt, da SVG-Dateien Skripte enthalten können.

Bilder werden anhand ihres Inhalts (nicht des Dateinamens) geprüft, einmalig im Ordner `assets` des Tresors
unter einem aus ihrem Inhalt abgeleiteten Namen gespeichert und wie folgt referenziert:

```markdown
![Diagram](asset:3f2a9c0b1d4e5f6a7b8c.png)
```

Das erste Bild, das Sie zu einer Notiz hinzufügen, wird zum **Titelbild**. Es wird als kleines abgerundetes
Vorschaubild in der Notizliste und im Kreis der Notiz im Graph angezeigt. Klicken Sie im Editor oder in
der Vorschau mit der rechten Maustaste auf ein beliebiges Bild und wählen Sie *Als Titelbild verwenden*,
um ein anderes auszuwählen, oder *Titelbild entfernen*, um keins festzulegen.

## Checklisten

Beginnen Sie eine Zeile mit `- [ ]` (oder klicken Sie in der Symbolleiste auf die Schaltfläche **Checkliste**),
um eine Aufgabe zu erstellen. `- [x]` kennzeichnet eine erledigte Aufgabe. Klicken Sie in der Vorschau auf
das Kästchen, um es anzukreuzen. Wenn Sie am Ende einer Aufgabe Enter drücken, wird die nächste begonnen;
Enter bei einer leeren Aufgabe beendet die Liste.

## Alarme

Klicken Sie auf die Alarm-Schaltfläche (oder wählen Sie *Einfügen ▸ Alarm…*), um für eine Notiz ein Datum
und optional eine Uhrzeit festzulegen. Wenn der Alarm fällig ist, zeigt ZettelApp eine Benachrichtigung;
klicken Sie darauf, um die Notiz zu öffnen. ZettelApp muss laufen, damit Sie benachrichtigt werden. Alarme,
die während der Schließzeit fällig wurden, werden kurz nach dem Öffnen des Tresors ausgelöst. Notizen mit
Alarm sind in der Notizliste mit einer Glocke markiert. Wählen Sie im selben Dialog *Alarm entfernen*, um
den Alarm zu löschen.

## Formeln

Schreiben Sie LaTeX zwischen Dollarzeichen: `$E = mc^2$` ist eine Inline-Formel und
`$$\int_0^1 x^2\,dx$$` eine abgesetzte Formel. Die Formelschaltfläche (*Einfügen ▸ Formel…*) öffnet einen
Dialog mit einer Live-Vorschau. Formeln werden in der Vorschau dargestellt; Exporte behalten den
LaTeX-Quelltext.

## Mindmaps

Jede Notiz kann eine Mindmap enthalten (Registerkarte **Mindmap** oder *Einfügen ▸ Mindmap*). Die Zweige
werden automatisch eingefärbt.

| Taste | Aktion |
|---|---|
| Tab | Untergeordnete Idee hinzufügen |
| Enter | Gleichrangige Idee hinzufügen |
| F2 oder Doppelklick | Umbenennen |
| Del | Ausgewählte Idee löschen |
| Pfeiltasten | Auswahl verschieben |
| Mausrad / Ziehen | Zoomen / verschieben |

Klicken Sie mit der rechten Maustaste auf eine Idee, um sie **mit einer Notiz zu verknüpfen**; ein
verknüpfter Gedanke zeigt ein Linksymbol und öffnet die Notiz. **Aus Links erstellen** erstellt eine
Mindmap aus den Links der Notiz, nach Linktyp gruppiert, mit den eigenen Links der verknüpften Notizen eine
Ebene tiefer. **Exportieren** speichert die Map als PNG- oder SVG-Bild oder als FreeMind-Datei (`.mm`), die
FreeMind, Freeplane und XMind öffnen können.

## Lernkarten

Lernkarten machen aus Notizen Wiederholungsmaterial (siehe [Wiederholung, Quizfragen und Anki](review-and-anki.md)).
Es gibt zwei Möglichkeiten, sie zu erstellen:

**Im Notiztext.** Diese Karten werden automatisch erstellt und beim Bearbeiten aktualisiert:

```markdown
Q: Who described the forgetting curve?
A: Hermann Ebbinghaus

{{c1::Retrieval practice}} is also called active recall.
```

Eine Frage kann sich über mehrere Zeilen erstrecken, bis die Zeile `A:` beginnt. Jeder Absatz mit
`{{c1::…}}` wird zu einer **Lückentextkarte**, die jede Lücke nacheinander ausblendet. `{{c1::text::hint}}`
zeigt einen Hinweis statt `[…]`.

**Auf der Registerkarte „Lernkarten“.** Verwenden Sie *Einfügen ▸ Lernkarte…* (Ctrl+Shift+F) für Karten,
die nicht in der Notiz erscheinen sollen. Karten aus dem Text sind mit *aus Notiztext* gekennzeichnet und
werden im Text bearbeitet.

## Suche

Das Suchfeld (Ctrl+F) durchsucht Titel, Text und Tags im Volltext, ignoriert Akzente und findet
Wortanfänge: `forget` findet also *forgetting*. Mit `tag:name` filtern Sie nach Tags, zum Beispiel
`memory tag:psychology`. Ergebnisse werden nach Relevanz sortiert; ohne Suchbegriff folgen die Notizen der
ausgewählten Sortierung (*Zuletzt bearbeitet*, *Erstellt*, *Titel* oder *Am stärksten verknüpft*).

## Papierkorb

*In den Papierkorb verschieben* (Ctrl+Delete) blendet eine Notiz aus, ohne sie zu löschen. Sofort erscheint
eine Schaltfläche zum Rückgängigmachen. Über die Schaltfläche **Papierkorb** unter der Notizliste sehen Sie
gelöschte Notizen: Klicken Sie mit der rechten Maustaste auf eine Notiz, um sie **wiederherzustellen** oder
**endgültig zu löschen**. **Papierkorb leeren** löscht alle darin enthaltenen Notizen nach einer
Bestätigung. Links zu Notizen im Papierkorb werden ausgeblendet und sind nach dem Wiederherstellen wieder
sichtbar.
