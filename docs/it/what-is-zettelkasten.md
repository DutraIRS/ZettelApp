# Che cos'è uno Zettelkasten?

Uno **Zettelkasten** (in tedesco «schedario») è un modo di prendere appunti in modo che continuino a lavorare per te. Non
archivi le note per argomento. Scrivi ogni idea in una nota a sé e la **colleghi** alle note con cui è
in relazione. Col tempo i collegamenti formano una rete, e seguirli è il modo in cui pensi, scrivi e scopri
connessioni che non avevi pianificato.

Non conosci il metodo? Leggi questa pagina, poi prova il [tutorial](tutorial.md).

## Da dove viene

Il metodo è strettamente associato a **Niklas Luhmann (1927–1998)**, sociologo tedesco noto soprattutto per
la sua teoria dei sistemi sociali. Nel corso di circa quattro decenni tenne uno schedario di circa **90.000
schede**. Due caratteristiche lo rendevano più di un semplice archivio di schede:

- **Ogni scheda aveva un indirizzo fisso**, come `21/3d7a`. Una nuova scheda su un pensiero esistente veniva archiviata
  subito dopo, con un indirizzo ramificato (`21/3d7a` → `21/3d7a1`), così le linee di pensiero potevano crescere in
  qualsiasi direzione senza riorganizzare nulla.
- **Le schede rimandavano ad altre schede tramite l'indirizzo.** Questo trasformava lo schedario in una rete di idee anziché in un
  insieme di categorie.

Luhmann attribuì allo schedario gran parte della sua enorme produzione, circa 70 libri e quasi 400
articoli (le cifre variano a seconda del conteggio). Scrisse persino un saggio sul lavorare con esso come con una specie di
interlocutore, *Kommunikation mit Zettelkästen* (1981). Da allora il suo schedario è stato digitalizzato dal
Niklas Luhmann Archive dell'Università di Bielefeld.

Il metodo è diventato noto al di fuori del mondo accademico grazie a ***How to Take Smart Notes* di Sönke Ahrens
(2017)** e a comunità come zettelkasten.de.

## I principi fondamentali

1. **Note atomiche: un'idea per nota.** Una nota dovrebbe contenere una sola idea, abbastanza piccola da essere collegata con precisione
   e riutilizzata in molti contesti. Se non riesci a riassumere una nota nel suo titolo, probabilmente contiene più di una
   idea.
2. **Con parole tue.** Scrivere un'idea con parole proprie è il momento in cui avviene la comprensione. Copiare un
   brano sembra produttivo ma salta il ragionamento.
3. **Collega ogni nota, con un motivo.** Quando aggiungi una nota, chiediti con quali note esistenti è in relazione,
   e *come*. Ne supporta una, ne contraddice un'altra, è un esempio di una terza? Un collegamento con un motivo
   vale molto più di un mucchio di note correlate.
4. **ID unici e permanenti.** I titoli cambiano e gli argomenti si spostano, ma l'indirizzo di una nota non dovrebbe, così i
   collegamenti non si rompono mai.
5. **Lascia emergere la struttura.** Invece di decidere in anticipo le categorie con le cartelle, lascia che i gruppi di
   idee si formino dai collegamenti che crei. La struttura cresce dal basso verso l'alto.
6. **Note di struttura (hub).** Quando un argomento si fa grande, scrivi una nota che lo mappa: una breve panoramica che
   rimanda alle note chiave in un ordine sensato. È un punto di ingresso, non una cartella.
7. **Ripassa e riporta alla luce.** Rivisita le note, segui i loro collegamenti e lascia che le vecchie idee incontrino quelle nuove. Uno
   Zettelkasten è un partner di pensiero solo se continui a dialogare con lui.

## Tre tipi di note

Ahrens descrive tre tipi di note, ciascuno con una diversa durata:

| Tipo | Che cos'è | Cosa farne |
|---|---|---|
| **Note volatili** | Rapidi promemoria di un pensiero, catturati ovunque. | Elaborale entro un giorno o due, poi gettale. |
| **Note bibliografiche** | Brevi note su una fonte, con parole tue, con il riferimento. | Conservale con la fonte (per esempio collegate alla sua voce di Zotero). |
| **Note permanenti** | Note autonome con le tue idee, scritte per il te stesso del futuro e collegate alla rete. | Queste sono lo Zettelkasten. Scrivile con cura e collegale. |

## Errori comuni

- **Collezionare invece di pensare.** Salvare articoli ed evidenziazioni sembra un progresso, ma uno
  Zettelkasten cresce solo con le note che scrivi e colleghi. Questa trappola è spesso chiamata «fallacia del
  collezionista».
- **Copiare citazioni.** Una nota che è per lo più una citazione non è ancora stata compresa. Tieni la citazione in una
  nota bibliografica se ti serve, e scrivi la nota permanente con parole tue.
- **Troppi tag.** Decine di tag per nota ricreano le cartelle sotto un altro nome. Pochi tag generici ti aiutano
  a trovare le note; i collegamenti portano il significato.
- **Note orfane.** Una nota senza collegamenti è difficile da ritrovare e non aggiunge nulla alla rete. Collega
  ogni nuova nota ad almeno una nota esistente.
- **Eccesso di ingegnerizzazione.** Il metodo richiede pochissimo: una nota, un ID e un collegamento. Inizia a scrivere; la
  struttura verrà dopo.

## Come ZettelApp supporta il metodo

| Principio | In ZettelApp |
|---|---|
| ID unici e permanenti | Ogni nota riceve automaticamente un ID basato su data e ora (come `20261027153012`). Collega per titolo o per ID: i [collegamenti wiki](notes-and-links.md#wiki-links) continuano a funzionare quando i titoli cambiano. |
| Note atomiche | Creazione rapida delle note (Ctrl+N), salvataggio automatico e note piccole che si vedono bene in anteprima. |
| Collegamento con un motivo | [Collegamenti tipizzati](notes-and-links.md#typed-links): `supports:: [[…]]`, *contraddice*, *estende*, *esempio di*, *parte di*, *cita*, o tipi tuoi. I tipi orientati si leggono in modo naturale da entrambi i lati (*Supportata da*). |
| Nessuna connessione persa | I [collegamenti suggeriti](link-suggestions.md) confrontano ogni nota con il tuo vault e imparano da ciò che accetti e scarti. I **collegamenti entranti** mostrano chi rimanda a una nota. |
| Lascia emergere la struttura | Il [grafo](graph-and-insights.md): un **grafo locale** attorno a qualsiasi nota e i **cluster** che rivelano argomenti che non hai mai archiviato. *Statistiche* elenca le **note non collegate** da sistemare. |
| Note di struttura | Mappe mentali dentro le note, collegate alle note che organizzano, e collegamenti *parte di*. |
| Note bibliografiche | L'integrazione con [Zotero](zotero.md) crea note bibliografiche collegate all'elemento e al suo PDF. |
| Ripassa e riporta alla luce | [Flashcard, ripetizione dilazionata e quiz](review-and-anki.md) creati dalle tue note, oppure sincronizzati con Anki. |
| Conserva tutto | Le note vanno nel **Cestino**, non vengono eliminate subito, e i backup giornalieri mettono al sicuro la tua cronologia. |

Pronto a provare? Inizia il [tutorial](tutorial.md).
