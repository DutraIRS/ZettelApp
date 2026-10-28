# Ripasso, quiz e Anki

Le note servono per pensare, e ricordarle aiuta. ZettelApp trasforma le note in
[flashcard](notes-and-links.md#flashcards) e ti permette di ripassarle nell'app o in Anki.

## Ripetizione dilazionata

La pagina **Ripasso** (Ctrl+4) mostra quante schede sono **da ripassare oggi**. **Inizia ripasso** le percorre:

1. Leggi la domanda e prova a ricordare la risposta.
2. Premi **Space** (oppure *Mostra risposta*).
3. Valutati: **Ancora (1)**, **Difficile (2)**, **Bene (3)** o **Facile (4)**. Passa il mouse su un pulsante per vedere quando
   la scheda tornerebbe.

La pianificazione usa l'algoritmo **SM-2** (l'algoritmo di SuperMemo da cui è nato Anki):

- Le schede nuove tornano dopo 1 giorno, poi dopo 6 giorni, poi a intervalli che crescono in base al *fattore di facilità* della scheda
  (inizialmente 2,5).
- *Ancora* riporta la scheda a 1 giorno e ne abbassa la facilità. *Difficile* accorcia l'intervallo successivo e *Facile*
  lo allunga.

Le schede cloze producono un ripasso per ogni cancellazione (`{{c1::…}}`, `{{c2::…}}`, …). Ogni domanda mostra un
collegamento **Da:** alla sua nota.

## Quiz

**Quiz di esercitazione** crea un quiz a partire da un ambito: l'intera raccolta, la nota aperta e le sue note collegate
(con una profondità) oppure le note con un tag. Scegli uno stile e il numero di domande:

| Stile | Come funziona |
|---|---|
| **Flashcard (ripetizione dilazionata)** | Come un ripasso, e le tue valutazioni aggiornano la pianificazione. |
| **Scelta multipla** | Scegli la risposta giusta tra quattro. Le risposte sbagliate sono risposte di altre schede di lunghezza simile, quindi sono plausibili. I tasti 1–4 scelgono. |
| **Scrivi la risposta** | Scrivi la risposta e premi Enter. Viene valutata per somiglianza di modifica (Levenshtein), ignorando maiuscole, accenti e formattazione: l'85% o più conta come corretta e il 60% o più come *quasi*, così i piccoli errori di battitura non ti penalizzano. |
| **Dai un nome a quella nota** | Mostra il testo di una nota con le parole del titolo oscurate; scegli il titolo giusto. Le opzioni sbagliate sono le **note più simili** (per TF-IDF), così impari a distinguere idee affini. Non servono flashcard. |

*Strumenti ▸ Quiz sulle note collegate a questa* avvia un quiz sulla nota aperta e sulle note entro due collegamenti
da essa. Fai clic destro su una nota nel grafo per lo stesso risultato.

## Anki

ZettelApp funziona con [Anki](https://apps.ankiweb.net/) in due modi. Entrambi usano due tipi di nota, **ZettelApp
Basic** e **ZettelApp Cloze**, con questi campi:

- *Front* e *Back* (oppure *Text* ed *Extra* per le schede cloze), generati dal Markdown;
- *Source*, un collegamento alla nota;
- *ZettelID* e *CardKey*.

I tag delle tue note diventano tag di Anki (i tag annidati diventano `parent::child`), più `zettelapp`. Le immagini nelle schede
sono incluse come media.

### Sincronizzazione con AnkiConnect

1. In Anki, installa il componente aggiuntivo **AnkiConnect** (*Strumenti ▸ Componenti aggiuntivi ▸ Scarica componenti aggiuntivi…*, codice **2055492159**)
   e riavvia Anki.
2. Con Anki in esecuzione, apri **Ripasso** in ZettelApp, scegli il nome del mazzo (**Mazzo predefinito** in
   *Opzioni ▸ Anki*, inizialmente `ZettelApp`) e l'ambito, e premi
   **Sincronizza con Anki** (oppure *Strumenti ▸ Sincronizza con Anki*). *Verifica connessione* mette alla prova il collegamento.

ZettelApp ricorda quale nota di Anki appartiene a ciascuna scheda. Sincronizzare di nuovo **aggiorna** le schede invece di
aggiungere duplicati, e una scheda può essere ritrovata tramite la sua *CardKey* anche se quella memoria è andata persa. Le schede
che elimini in ZettelApp non vengono eliminate da Anki.

ZettelApp parla solo con AnkiConnect su questo computer (`127.0.0.1`, porta 8765 per impostazione predefinita, modificabile in
*Opzioni ▸ Anki*).

### Esporta un mazzo (.apkg)

**Esporta mazzo (.apkg)…** (oppure *File ▸ Esporta…* con il formato *Mazzo Anki*) scrive un pacchetto che
importi con *File ▸ Importa* in Anki. Non serve alcun componente aggiuntivo. I tipi di nota, il mazzo e l'identità di ogni scheda sono
stabili, quindi importare un'esportazione più recente **aggiorna** le schede importate in precedenza.

### Da Anki alle tue note

La **Source** di ogni scheda è un collegamento `zettelapp://note/<id>`. Cliccalo in Anki e la nota si apre in
ZettelApp. Il programma di installazione lo configura. Con la versione portatile, usa *Opzioni ▸ Integrazione con Windows ▸
Registra collegamenti*. Il gestore dei collegamenti accetta solo collegamenti *apri nota*; vedi
[Privacy e sicurezza](privacy-and-security.md).
