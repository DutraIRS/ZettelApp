# Wiederholung, Quizfragen und Anki

Notizen sollen zum Denken anregen, und es hilft, sich an sie zu erinnern. ZettelApp macht aus Notizen
[Lernkarten](notes-and-links.md#flashcards), die Sie in der App oder mit Anki wiederholen können.

## Verteiltes Wiederholen

Die Seite **Wiederholen** (Ctrl+4) zeigt, wie viele Karten **heute fällig** sind. Mit **Wiederholung
starten** gehen Sie sie durch:

1. Lesen Sie die Frage und versuchen Sie, sich an die Antwort zu erinnern.
2. Drücken Sie **Space** (oder wählen Sie *Antwort zeigen*).
3. Bewerten Sie sich selbst: **Nochmal (1)**, **Schwer (2)**, **Gut (3)** oder **Einfach (4)**. Wenn Sie auf eine Schaltfläche zeigen, sehen Sie, wann die Karte erneut erscheint.

Die Planung verwendet den **SM-2**-Algorithmus (den SuperMemo-Algorithmus, aus dem Anki hervorgegangen
ist):

- Neue Karten erscheinen nach 1 Tag erneut, dann nach 6 Tagen und anschließend in Abständen, die mit ihrem *Leichtigkeitsfaktor* wachsen (anfangs 2.5).
- *Nochmal* setzt die Karte auf einen Tag zurück und verringert ihre Leichtigkeit. *Schwer* verkürzt den nächsten Abstand, *Einfach* verlängert ihn.

Für jeden Lückentext (`{{c1::…}}`, `{{c2::…}}`, …) wird eine eigene Wiederholung erstellt. Bei jeder Frage
wird ein Link **Aus:** zugehörigen Notiz angezeigt.

## Quizfragen

**Quiz üben** erstellt ein Quiz für einen Bereich: die gesamte Sammlung, die geöffnete Notiz und ihre
verknüpften Notizen (mit einer festlegbaren Tiefe) oder Notizen mit einem Tag. Wählen Sie einen Stil und
die Anzahl der Fragen aus:

| Stil | Funktionsweise |
|---|---|
| **Lernkarten (verteiltes Wiederholen)** | Wie eine Wiederholung; Ihre Bewertungen aktualisieren den Zeitplan. |
| **Multiple Choice** | Wählen Sie unter vier Antworten die richtige aus. Falsche Antworten stammen von anderen Karten mit Antworten ähnlicher Länge und wirken daher plausibel. Mit den Tasten 1–4 treffen Sie Ihre Auswahl. |
| **Antwort eingeben** | Geben Sie die Antwort ein und drücken Sie Enter. Sie wird anhand der Bearbeitungsähnlichkeit (Levenshtein) bewertet; Groß-/Kleinschreibung, Akzente und Formatierung werden ignoriert. Ab 85 % gilt die Antwort als richtig, ab 60 % als *fast richtig* – kleine Tippfehler werden Ihnen also verziehen. |
| **Notiz erraten** | Zeigt den Text einer Notiz, wobei die Wörter ihres Titels ausgeblendet sind; wählen Sie den richtigen Titel. Die falschen Optionen sind die **ähnlichsten Notizen** (nach TF-IDF), damit Sie verwandte Ideen voneinander unterscheiden lernen. Lernkarten sind nicht erforderlich. |

*Werkzeuge ▸ Quiz über die Nachbarschaft dieser Notiz* startet ein Quiz über die geöffnete Notiz und die
Notizen innerhalb von zwei Links. Dasselbe erreichen Sie über das Kontextmenü einer Notiz im Graph.

## Anki

ZettelApp funktioniert auf zwei Arten mit [Anki](https://apps.ankiweb.net/). Beide verwenden die zwei
Notiztypen **ZettelApp Basic** und **ZettelApp Cloze** mit folgenden Feldern:

- *Vorderseite* und *Rückseite* (bei Lückentextkarten *Text* und *Zusatz*), aus Markdown dargestellt;
- *Quelle*, ein Link zurück zur Notiz;
- *ZettelID* und *CardKey*.

Die Tags Ihrer Notiz werden zu Anki-Tags (verschachtelte Tags werden zu `parent::child`), zusätzlich kommt
`zettelapp` hinzu. Bilder in Karten werden als Medien übernommen.

### Mit AnkiConnect synchronisieren

1. Installieren Sie in Anki das Add-on **AnkiConnect** (*Werkzeuge ▸ Add-ons ▸ Add-ons herunterladen…*, Code **2055492159**) und starten Sie Anki neu.
2. Wenn Anki läuft, öffnen Sie in ZettelApp **Wiederholen**, wählen Sie den Decknamen (**Standard-Deck** unter *Optionen ▸ Anki*, anfangs `ZettelApp`) und den Bereich aus und klicken Sie auf **Mit Anki synchronisieren** (oder *Werkzeuge ▸ Mit Anki synchronisieren*). Mit *Verbindung prüfen* testen Sie die Verbindung.

ZettelApp merkt sich, welche Anki-Notiz zu welcher Karte gehört. Bei erneuter Synchronisierung werden
Karten **aktualisiert**, statt Duplikate hinzuzufügen. Selbst wenn diese Zuordnung verloren geht, kann eine
Karte anhand ihres *CardKey* wiedergefunden werden. In ZettelApp gelöschte Karten werden nicht aus Anki
gelöscht.

ZettelApp kommuniziert ausschließlich mit AnkiConnect auf diesem Computer (`127.0.0.1`, standardmäßig
Port 8765, unter *Optionen ▸ Anki* änderbar).

### Ein Deck exportieren (.apkg)

**Deck exportieren (.apkg)…** (oder *Datei ▸ Exportieren…* mit dem Format *Anki-Deck*) erstellt ein Paket,
das Sie in Anki über *Datei ▸ Importieren* importieren. Ein Add-on ist nicht erforderlich. Notiztypen, Deck
und Identität jeder Karte bleiben stabil; ein neuerer Export **aktualisiert** daher die zuvor importierten
Karten.

### Von Anki zurück zu Ihren Notizen

Die **Quelle** jeder Karte ist ein Link `zettelapp://note/<id>`. Klicken Sie in Anki darauf, um die Notiz
in ZettelApp zu öffnen. Das Installationsprogramm richtet dies ein. Bei der portablen Version verwenden
Sie *Optionen ▸ Windows-Integration ▸ Links registrieren*. Der Linkhandler akzeptiert nur Links zum
*Öffnen einer Notiz*; siehe [Datenschutz und Sicherheit](privacy-and-security.md).
