# Tutorial: Ihre ersten 30 Minuten

Ein Rundgang zum Ausprobieren. Jeder Schritt beschreibt, was Sie tun und sehen sollten. Für Schritte mit
*optional* benötigen Sie Zotero, einen KI-Schlüssel oder Anki; überspringen Sie diese, wenn Sie sie nicht
verwenden.

Neu bei der Methode selbst? Lesen Sie zuerst [Was ist ein Zettelkasten?](what-is-zettelkasten.md). Das dauert fünf Minuten.

## 1. Installieren und den Willkommens-Tresor öffnen

1. Laden Sie **ZettelApp-Setup.exe** aus der [neuesten Version](https://github.com/DutraIRS/ZettelApp/releases/latest)
   herunter und führen Sie es aus, oder entpacken Sie **ZettelApp-Portable.zip** und starten Sie `ZettelApp.exe`.
2. Starten Sie ZettelApp.

**Das sollten Sie sehen:** Die Seite „Notizen“ mit elf verknüpften Startnotizen in einem neuen Tresor unter
*Documents\ZettelApp*. Im Editor ist „Welcome to ZettelApp“ geöffnet. Nach einem Moment bietet ZettelApp
Ihnen außerdem das optionale Abenteuer *Lost Prince of the Archive* an. Wählen Sie **Nicht jetzt**, wenn Sie
diese schriftliche Anleitung bevorzugen.

## 2. Eine Notiz erstellen

1. Drücken Sie **Ctrl+N**.
2. Geben Sie einen Titel ein, zum Beispiel *Verteiltes Wiederholen*, und drücken Sie **Enter**, um zum Text zu wechseln.
3. Schreiben Sie eine Idee in eigenen Worten in zwei oder drei Sätzen:
   *Material in zunehmenden Abständen zu wiederholen, hilft dem Langzeitgedächtnis, weil jede Wiederholung kurz vor dem Vergessen stattfindet.*

**Das sollten Sie sehen:** Die Notiz erscheint oben in der Liste. Es gibt keine Schaltfläche zum Speichern:
Notizen werden beim Tippen gespeichert. Die ID unter dem Titel (zum Beispiel `20261027153012`) ist die
Daueradresse der Notiz.

## 3. Tags hinzufügen

Klicken Sie unter dem Titel auf **Tag hinzufügen**, geben Sie `learning` ein und drücken Sie **Enter**.
Fügen Sie auch `memory` hinzu.

**Das sollten Sie sehen:** Zwei Chips, *#learning* und *#memory*. Der Tagfilter über der Liste bietet diese
Tags jetzt an. Wenn Sie im Suchfeld `tag:memory` eingeben, finden Sie die Notiz.

## 4. Eine andere Notiz verknüpfen

1. Erstellen Sie eine zweite Notiz (**Ctrl+N**) mit dem Titel *Vergessenskurve* und dem Satz: *Ohne Wiederholung verblasst die Erinnerung schnell.*
2. Kehren Sie zu *Verteiltes Wiederholen* zurück (klicken Sie in der Liste darauf). Geben Sie im Text `[[` und dann `Verg` ein.
3. Wählen Sie **Vergessenskurve** aus der Vervollständigungsliste und drücken Sie **Enter**.

**Das sollten Sie sehen:** `[[Vergessenskurve]]` ist im Text unterstrichen. In der Seitenleiste erscheint
*Vergessenskurve* unter **Links**. Klicken Sie in der Symbolleiste auf die Augenschaltfläche (**Geteilte
Ansicht**): Die Vorschau zeigt einen anklickbaren Link.

## 5. Beschreiben, *wie* die Notizen zusammenhängen

Machen Sie den Link zu einem typisierten Link, indem Sie `supports::` davor setzen:

```markdown
supports:: [[Forgetting curve]]
```

**Das sollten Sie sehen:** Der Link wird in der Seitenleiste als *Unterstützt* aufgeführt. Öffnen Sie
*Vergessenskurve*: Die **Backlinks** zeigen *Verteiltes Wiederholen: **Wird unterstützt von***, denn
*supports* ist ein gerichteter Linktyp. Einfache `[[links]]` bedeuten *Steht in Beziehung zu*.

## 6. Einen Linkvorschlag verwenden

Schreiben Sie einige weitere Notizen zu verwandten Ideen, zum Beispiel *Aktives Abrufen* und *Interleaving*,
jeweils mit ein oder zwei Sätzen und dem Tag `learning`. Öffnen Sie dann eine davon und sehen Sie sich die
**Linkvorschläge** in der Seitenleiste an.

- Klicken Sie auf **Verknüpfen**, um einen Vorschlag anzunehmen. Mit dem kleinen Pfeil daneben wählen Sie einen Linktyp.
- Klicken Sie auf **✕**, um einen unpassenden Vorschlag zu verwerfen.
- Bewegen Sie den Mauszeiger über einen Vorschlag, um zu erfahren, **warum** er vorgeschlagen wurde: Jede Kennzahl zeigt Belege dafür oder dagegen.

**Was das Modell lernt:** Angenommene Vorschläge werden zu Links und trainieren den Klassifikator als
positive Beispiele. Abgelehnte Vorschläge werden als negative Beispiele gespeichert und für dieses Paar
nie wieder vorgeschlagen. Je häufiger Sie die Vorschläge nutzen, desto besser werden sie. Siehe
[Linkvorschläge](link-suggestions.md).

![Notizen mit Linkvorschlägen](../website/assets/screenshots/notes-light.png)

## 7. Ein Bild hinzufügen

Kopieren Sie ein beliebiges Bild (zum Beispiel mit *Win+Shift+S*), klicken Sie in den Notiztext und drücken
Sie **Ctrl+V**. Sie können auch eine Bilddatei hineinziehen oder *Einfügen ▸ Bild…* verwenden.

**Das sollten Sie sehen:** `![…](asset:…)` im Text und das Bild in der Vorschau. Da es das erste Bild der
Notiz ist, wird es auch zum **Notizbild** und erscheint neben dem Titel sowie im Kreis der Notiz im Graphen.

## 8. Eine Mindmap skizzieren

1. Öffnen Sie die Registerkarte **Mindmap** und klicken Sie auf **Idee hinzufügen**.
2. Drücken Sie **Tab**, um eine untergeordnete Idee hinzuzufügen, **Enter** für ein gleichrangiges Element,
   **F2** zum Umbenennen und **Del** zum Löschen. Mit den Pfeiltasten wechseln Sie zwischen den Ideen.
3. Klicken Sie nun auf **Aus Links erstellen** und bestätigen Sie, dass die gerade erstellte Map ersetzt werden darf.

**Das sollten Sie sehen:** Eine Mindmap aus den Links der Notiz, nach Linktyp gruppiert, mit den Links jeder
verknüpften Notiz eine Ebene tiefer. Klicken Sie mit der rechten Maustaste auf eine Idee, um sie mit einer
Notiz zu verknüpfen. Die Export-Schaltfläche speichert die Map als PNG, SVG oder FreeMind-Datei.

![Eine Mindmap](../website/assets/screenshots/mindmap-light.png)

## 9. Lernkarten erstellen und wiederholen

Fügen Sie dem Text von *Verteiltes Wiederholen* folgende Zeilen hinzu:

```markdown
Q: Why space reviews out?
A: Each effortful retrieval just before forgetting strengthens the memory.

{{c1::Hermann Ebbinghaus}} described the forgetting curve.
```

**Das sollten Sie sehen:** Die Registerkarte zeigt **Lernkarten (2)**: eine Fragekarte und eine Lückentextkarte.
Öffnen Sie nun **Wiederholen** (**Ctrl+4**) und klicken Sie auf **Wiederholung starten**.

- Drücken Sie **Space**, um die Antwort anzuzeigen.
- Bewerten Sie sich mit **1–4** (*Nochmal, Schwer, Gut, Einfach*).

Der SM-2-Zeitplan entscheidet, wann die jeweilige Karte wieder erscheint. Probieren Sie auch **Quiz üben ▸
Multiple Choice** oder **Notiz erraten** aus.

![Ein Multiple-Choice-Quiz](../website/assets/screenshots/quiz-light.png)

## 10. Den Graph erkunden

Öffnen Sie **Graph** (**Ctrl+2**).

1. Ziehen Sie Notizen an eine andere Stelle, zoomen Sie mit dem Mausrad und zeigen Sie auf eine Notiz, um ihre Nachbarn hervorzuheben.
2. Wählen Sie auf der Seite „Notizen“ eine Notiz aus, wechseln Sie zurück und klicken Sie auf **Lokal**. Stellen Sie **Tiefe** auf 1, 2 oder 3.
3. Setzen Sie **Färben nach** auf **Cluster: k-means**. Notizen werden nach Bedeutung gruppiert und die Legende benennt jedes Cluster anhand seiner Stichwörter.
4. Aktivieren Sie **Gruppieren**, um die Gruppen auf einem schattierten Hintergrund zusammenzuführen.
5. Klicken Sie auf **3D**, ziehen Sie zum Umlaufen und probieren Sie **Automatisch drehen** aus.

![Der nach Tags eingefärbte und gruppierte Graph](../website/assets/screenshots/graph-light.png)

## 11. Einblicke prüfen

Öffnen Sie **Einblicke** (**Ctrl+3**), um Anzahlen, Notizen pro Monat, häufigste Tags, Links nach Typ und
die am stärksten verknüpften Notizen zu sehen. **Unverknüpfte Notizen** ist Ihre Aufgabenliste: Verknüpfen
Sie sie mit anderen Notizen. Für jedes Diagramm gibt es eine Tabellenansicht.

## 12. Einen Zotero-Eintrag zitieren und eine Literatur-Notiz schreiben (optional)

Wenn Zotero 7 oder neuer läuft und unter *Einstellungen ▸ Erweitert* die Option *Anderen Anwendungen auf
diesem Computer die Kommunikation mit Zotero erlauben* aktiviert ist:

1. Wählen Sie *Einfügen ▸ Zotero-Referenz…*, suchen Sie einen Eintrag und klicken Sie auf **Zitat einfügen**: Der Link, etwa *Ebbinghaus (1885)*, öffnet den Eintrag in Zotero.
2. Wiederholen Sie den Vorgang und klicken Sie auf **Neue Literatur-Notiz**.

**Das sollten Sie sehen:** Eine neue Notiz mit Referenz, Links *In Zotero öffnen* und *PDF öffnen*, Abstract
sowie den Abschnitten *Kernideen* und *Meine Gedanken*, versehen mit dem Tag `literature`. Siehe [Zotero](zotero.md).

## 13. Ihre Notizen befragen (optional)

1. Wählen Sie unter *Werkzeuge ▸ Optionen ▸ KI-Assistent* einen Anbieter (Anthropic, OpenAI oder Z.ai), geben Sie Ihren API-Schlüssel ein und klicken Sie auf **Verbindung testen**.
2. Öffnen Sie **Fragen** (**Ctrl+5**) und fragen Sie: *Wie hängen zeitliche Abstände und Abruf zusammen?*

**Das sollten Sie sehen:** Eine Antwort mit Links zu den zitierten Notizen und einer genauen Liste der
**gesendeten Quellen**. Nur diese Notizen und Ihre Frage verlassen Ihren Computer. Siehe
[Fragen Sie Ihre Notizen](ai-assistant.md).

## 14. Einen Teilgraphen exportieren und mit Anki synchronisieren (optional)

1. Öffnen Sie eine Notiz, wählen Sie *Datei ▸ Exportieren…* (**Ctrl+Shift+E**), legen Sie **Aktuelle Notiz und verknüpfte Notizen**, Tiefe 2 und das Format **Website** fest.
2. Öffnen Sie `index.html` aus dem ZIP-Archiv in Ihrem Browser: eine kleine Website zu diesem Teil Ihres Zettelkastens.
3. Wenn Anki läuft und das AnkiConnect-Add-on (Code `2055492159`) installiert ist, öffnen Sie **Wiederholen** und klicken Sie auf **Mit Anki synchronisieren**. Der Quellenlink jeder Karte öffnet die Notiz in ZettelApp.

Siehe [Export und Import](export-import.md) und [Anki](review-and-anki.md#anki).

## 15. Wissen, wo Ihre Daten liegen

- Ihre Notizen liegen im Tresorordner (*Datei ▸ Tresor im Datei-Explorer anzeigen*): `zettel.db` und `assets`.
- Einmal täglich wird automatisch eine Sicherung erstellt. Mit *Datei ▸ Tresor jetzt sichern* können Sie jederzeit eine erstellen.
- Gelöschte Notizen landen im **Papierkorb** unter der Notizliste und können dort wiederhergestellt werden.

Weitere Informationen finden Sie unter [Datenschutz und Sicherheit](privacy-and-security.md).

**Das war's.** Schreiben Sie weiterhin eine Idee pro Notiz, begründen Sie jeden neuen Link und lassen Sie
sich von Vorschlägen und Graph zeigen, was Sie gesammelt haben. Die Tastenkombinationen stehen unter
[Tastenkombinationen](keyboard-shortcuts.md).
