# Zotero

ZettelApp verbindet sich mit [Zotero](https://www.zotero.org/), dem kostenlosen Literaturverwaltungsprogramm.
So können Sie Referenzen in Ihren Notizen zitieren und **Literatur-Notizen** schreiben, die mit dem Eintrag
und seinem PDF in Ihrer Bibliothek verknüpft sind.

## Einrichten

1. Verwenden Sie **Zotero 7 oder neuer** und lassen Sie Zotero geöffnet.
2. Öffnen Sie in Zotero *Einstellungen ▸ Erweitert* und aktivieren Sie **„Anderen Anwendungen auf diesem Computer die Kommunikation mit Zotero erlauben“**.
3. Unter *Werkzeuge ▸ Optionen ▸ Zotero ▸ Verbindung testen* sollte ZettelApp *Mit Zotero verbunden* melden.

ZettelApp liest Ihre Bibliothek über die **lokale API** von Zotero auf diesem Computer (standardmäßig
`127.0.0.1`, Port 23119). Die App liest ausschließlich Daten: Sie ändert Ihre Zotero-Bibliothek nie, und
es wird nichts über das Internet übertragen. Durchsucht wird Ihre persönliche Bibliothek (*Meine
Bibliothek*); Gruppenbibliotheken werden bislang nicht durchsucht.

## Eine Referenz zitieren

*Einfügen ▸ Zotero-Referenz…* oder die Buchschaltfläche in der Editor-Symbolleiste öffnet ein Suchfeld.
Geben Sie einen Teil des Titels, einen Autor oder ein Jahr ein. Bei leerem Suchfeld werden die zuletzt
geänderten Einträge aufgelistet. Wählen Sie einen Eintrag, um seine Details zu sehen. Danach können Sie:

- Mit **Zitat einfügen** (oder per Doppelklick) ein Autor-Jahr-Zitat einfügen, das den Eintrag in Zotero öffnet:

  ```markdown
  [Ebbinghaus (1885)](zotero://select/library/items/ABCD2345)
  ```

- Mit **Neue Literatur-Notiz** eine Notiz für den Eintrag erstellen, die Folgendes enthält:
  - den Titel des Eintrags;
  - eine Referenzzeile (Autoren, Jahr, Titel, Veröffentlichung, DOI);
  - Links zu *In Zotero öffnen*, *PDF öffnen* (wenn der Eintrag einen PDF-Anhang hat) und dem DOI;
  - den Abstract;
  - Abschnitte *Kernideen* und *Meine Gedanken* zum Ausfüllen;
  - den Tag `literature` sowie die Zotero-Tags des Eintrags;
  - den Zotero-Eintrag als **Quellenlink** der Notiz.

Literatur-Notizen bilden die klassische Brücke vom Zettelkasten zur Lektüre: Schreiben Sie die Kernideen
in eigenen Worten auf und verknüpfen Sie sie anschließend mit Notizen, die sie unterstützen, erweitern oder
ihnen widersprechen.

## Zotero-Links

Wenn Sie in einer Notiz auf einen Zotero-Link klicken, wird Zotero beim entsprechenden Eintrag geöffnet
oder das PDF im Zotero-Reader angezeigt. Aus Sicherheitsgründen folgt ZettelApp nur zwei Arten von
Zotero-Links und lehnt alle anderen `zotero://`-Adressen ab:

```text
zotero://select/library/items/<KEY>
zotero://open-pdf/library/items/<KEY>?page=<N>
```

Links zu Gruppenbibliotheken (`zotero://select/groups/<ID>/items/<KEY>`) werden ebenfalls akzeptiert. Sie
können auch einen Zotero-Link in das Feld **Quellenlink** einer Notiz einfügen. Klicken Sie in Zotero mit
der rechten Maustaste auf einen Eintrag und kopieren Sie den Link (oder verwenden Sie ein Add-on wie
Zutilo); fügen Sie ihn anschließend ein.

## Fehlerbehebung

| Meldung | Vorgehen |
|---|---|
| *Zotero konnte nicht erreicht werden* | Starten Sie Zotero 7 oder neuer. Prüfen Sie den Port unter *Optionen ▸ Zotero* (Standard 23119). |
| *Zotero hat die Anfrage abgelehnt* | Aktivieren Sie die Einstellung *Anderen Anwendungen… erlauben* (Schritt 2 oben). |
| *Diese Zotero-Version verfügt über keine lokale API* | Aktualisieren Sie Zotero auf Version 7 oder neuer. |
