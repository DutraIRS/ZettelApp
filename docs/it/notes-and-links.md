# Note e collegamenti

## Scrivere note

Le note si scrivono in **Markdown**: `**grassetto**`, `*corsivo*`, `# titoli`, elenchi, `> citazioni`,
`` `codice` ``, blocchi di codice delimitati, tabelle e `~~testo barrato~~`. La barra degli strumenti sopra l'editor inserisce
i più comuni, e Ctrl+B / Ctrl+I funzionano come al solito. Gli elenchi continuano quando premi Enter.

L'editor ha tre modalità (Ctrl+E le alterna): **Modifica**, **Divisa** (testo e anteprima affiancati)
e **Anteprima**.

Per sicurezza, l'HTML grezzo in una nota viene mostrato come testo e non viene mai interpretato. I collegamenti nell'anteprima aprono solo pagine
web (`http`, `https`), e-mail (`mailto`), note, elementi di Zotero e file locali (mostrati in Esplora file,
vedi [Collegamenti a file locali](#links-to-local-files)). Vedi [Privacy e sicurezza](privacy-and-security.md).

### Seguire i collegamenti

- **Nell'editor**, **Ctrl+clic** segue un `[[collegamento a nota]]` (creando la nota se non esiste ancora),
  un collegamento web, e-mail o Zotero, un collegamento a un file locale o un `#tag` (che elenca le note con quel tag).
  Passa il mouse sul testo e un suggerimento dice cosa farà il clic. Un semplice clic posiziona solo il cursore, così
  puoi comunque modificare il testo del collegamento.
- **Nell'anteprima**, un normale clic segue i collegamenti.

### Collegamenti a file locali

*Inserisci ▸ Collega a un file…* (o il pulsante cartella nella barra degli strumenti) ti permette di scegliere un file e inserisce un collegamento
come `[report.pdf](file:///C:/Users/me/Documents/report.pdf)`. Trascinare nel testo della nota un file che non è un'immagine
ottiene lo stesso risultato. Il file resta collegato dov'è; nulla viene copiato nel vault.

Cliccando il collegamento nell'anteprima, o con Ctrl+clic nell'editor, si apre **Esplora file con il file
selezionato**. Il file in sé non viene mai aperto né eseguito. Sono consentiti solo percorsi su un'unità locale: i percorsi
di rete (UNC) come `\\server\share\file.pdf` vengono rifiutati, perché cercarli può inviare le tue credenziali
Windows a quel server.

Ogni nota ha:

- un **titolo** (il campo grande in alto);
- un **ID**, una data e ora come `20261027153012`, mostrato sotto il titolo (*Altro ▸ Copia ID nota*);
- facoltativamente **tag**, un **collegamento alla fonte**, un'**immagine**, una **mappa mentale** e delle **flashcard**.

## Collegamenti tra note

### Collegamenti wiki

Scrivi `[[` e inizia a digitare un titolo: ZettelApp lo completa dalle tue note. All'interno di una nota, tutti questi sono collegamenti:

```markdown
See [[Forgetting curve]].
See [[20261027153012]].              (per ID)
See [[Forgetting curve|the curve]].  (testo del collegamento personalizzato)
```

Ctrl+K (*Inserisci ▸ Collega a nota…*) apre un selettore che cerca nei titoli e nei testi e ti permette di scegliere il
tipo di collegamento. Un collegamento a un titolo che non esiste ancora è mostrato in grigio nell'anteprima; cliccalo per creare
quella nota. Quando in seguito crei o rinomini una nota, i collegamenti che ne citano il titolo vengono aggiornati.

### Collegamenti tipizzati

I collegamenti possono dire **come** due note sono in relazione. Metti il tipo di collegamento davanti al collegamento, seguito da `::`:

```markdown
supports:: [[Forgetting curve]]
contradicts:: [[Rereading notes]]
part_of:: [[Zettelkasten method]]
```

I tipi di collegamento predefiniti sono:

| Tipo | Nome | Nome inverso | Orientato | Linea | Punta della freccia |
|---|---|---|---|---|---|
| `related` | Correlata a | Correlata a | no | continua, grigia | nessuna |
| `supports` | Supporta | Supportata da | sì | tratteggiata, verde | triangolo pieno |
| `contradicts` | Contraddice | Contraddice | no | punteggiata, rossa | nessuna |
| `extends` | Estende | Esteso da | sì | tratto-punto, blu | triangolo pieno |
| `example` | Esempio di | Ha esempio | sì | tratto-punto-punto, ambra | cerchio |
| `part_of` | Parte di | Contiene | sì | tratto lungo, viola | rombo |
| `cites` | Cita | Citata da | sì | continua, verde acqua | freccia aperta |

Questo è l'aspetto di un nuovo vault; puoi modificarlo (vedi sotto). Un vault creato con una versione precedente
mantiene le linee che aveva.

Un semplice `[[collegamento]]` è *Correlata a*.

### Collegamenti orientati e non orientati

Un tipo **orientato** si legge in modo diverso da ciascun lato. Se la nota A *supporta* la nota B, allora i collegamenti entranti
di B mostrano A come *Supportata da*. I collegamenti orientati hanno punte di freccia nel grafo e restano orientati nelle esportazioni.
I tipi **non orientati** come *Correlata a* e *Contraddice* si leggono allo stesso modo in entrambe le direzioni.

Per invertire un collegamento orientato creato nel verso sbagliato, fai clic destro su di esso nel pannello laterale e scegli
**Inverti direzione**. I collegamenti scritti nel testo si invertono modificando il testo.

### Collegamenti nel pannello laterale

Il pannello laterale elenca i **Collegamenti** (uscenti) e i **Collegamenti entranti** della nota, ciascuno con il suo tipo.

- **Aggiungi collegamento…** crea un collegamento senza scriverlo nel testo.
- Clic destro su un collegamento per aprire l'altra nota, cambiare il tipo di collegamento, invertirne la direzione o rimuoverlo.
  I collegamenti scritti nel testo si rimuovono modificando il testo.
- Dall'elenco delle note, fai clic destro su un'altra nota e scegli **Collega dalla nota aperta come**.

### I tuoi tipi di collegamento

Aggiungi, rinomina, cambia lo stile o rimuovi i tipi di collegamento in *Strumenti ▸ Opzioni ▸ Tipi di collegamento*. Scegli un tipo nell'elenco e
modificalo accanto all'elenco:

- **Nome** e **Nome inverso**: come il collegamento si legge dall'origine e dalla destinazione. Il nome
  inverso è usato solo dai tipi orientati.
- **Orientato**: se il tipo si legge in modo diverso da ciascun lato e ottiene una punta di freccia.
- **Colore**: clicca il pulsante del colore per sceglierne uno qualsiasi.
- **Linea**: continua, tratteggiata, punteggiata, tratto-punto, tratto-punto-punto o tratto lungo.
- **Punta della freccia**: la punta disegnata dove arriva un collegamento orientato: un triangolo pieno, una freccia aperta, un
  rombo, un cerchio o una barra.

L'anteprima mostra due note unite dal collegamento, con il suo nome e come si legge dall'altro lato.
Lo stile viene usato ovunque compaiano i collegamenti: il grafo, la sua legenda, il pannello laterale, il selettore dei collegamenti e
le esportazioni in sito web, GraphML e Graphviz. Dai a ogni tipo una linea propria oltre a un colore proprio, così
i tipi restano facili da distinguere per chi ha difficoltà con i colori e su carta. Un nuovo tipo parte con un
colore e una linea che pochi altri tipi usano.

Nel testo, usa l'id del tipo, mostrato sotto l'anteprima (per esempio un tipo chiamato «Ispirato da» diventa
`ispirato_da::`). L'id viene impostato quando il tipo è creato, quindi rinominare un tipo non rompe i collegamenti
scritti nelle tue note. Rimuovere uno dei tuoi tipi trasforma i suoi collegamenti in collegamenti *Correlata a*, così
nulla va perso. I tipi predefiniti possono essere rinominati e cambiati di stile ma non rimossi.

## Tag

Aggiungi i tag nel campo tag sotto il titolo (premi Enter dopo ciascuno), oppure scrivili **nel testo** con il
cancelletto, come `#welcome` o `#math/algebra`. I tag sono in minuscolo e possono essere annidati con una barra, come
`math/algebra`. Filtrare per `math` trova anche le note con tag `math/algebra`.
Usa il filtro tag sopra l'elenco delle note, oppure scrivi `tag:nome` nella casella di ricerca.

I tag scritti nel testo sono tag veri e propri, mostrati come **chip con il bordo** accanto alla casella *Aggiungi tag*. Spariscono
quando elimini il `#tag` dal testo. Un `#tag` viene ignorato nel codice, nelle destinazioni dei collegamenti
e in `[[#headings]]`. I tag scritti nella casella *Aggiungi tag* sono separati: restano finché non li rimuovi con
la loro ✕. Ctrl+clic su un `#tag` nell'editor per elencare le note che lo hanno.

## Collegamento alla fonte

Il campo con l'icona del globo contiene la **fonte** della nota: una pagina web (`https://…`), un indirizzo e-mail
o un elemento Zotero (`zotero://select/library/items/…`). Il pulsante accanto apre il collegamento. Altri tipi di
collegamenti vengono rifiutati. Vedi [Zotero](zotero.md) per creare note direttamente dalla tua libreria Zotero.

## Immagini

Inserisci le immagini con *Inserisci ▸ Immagine…* (Ctrl+Shift+I), **incollandole** dagli appunti o
**trascinando** file immagine sull'editor. Formati supportati: PNG, JPEG, GIF, WebP e BMP, fino a 25 MB.
SVG è rifiutato di proposito, perché i file SVG possono contenere script.

Le immagini vengono verificate dal loro contenuto (non dal nome del file), salvate una sola volta nella cartella `assets` del vault
con un nome derivato dal loro contenuto e referenziate così:

```markdown
![Diagram](asset:3f2a9c0b1d4e5f6a7b8c.png)
```

La prima immagine che aggiungi a una nota diventa la sua **immagine del titolo**. È mostrata come una piccola miniatura arrotondata nell'
elenco delle note e dentro il cerchio della nota nel grafo. Fai clic destro su qualsiasi immagine nell'editor o nell'anteprima
e scegli *Usa come immagine del titolo* per sceglierne un'altra, oppure *Rimuovi immagine del titolo* per non averne nessuna.
Eliminare l'immagine del titolo dal testo della nota la rimuove anche come immagine del titolo.

## Liste di controllo

Inizia una riga con `- [ ]` (oppure premi il pulsante della lista di controllo nella barra degli strumenti) per creare un'attività. `- [x]` è un'
attività completata. Nell'anteprima, clicca la casella per spuntarla; premere Enter alla fine di un'attività avvia
la successiva, ed Enter su un'attività vuota termina l'elenco.

## Allarmi

Premi il pulsante dell'allarme (oppure *Inserisci ▸ Allarme…*) per impostare una data e, facoltativamente, un'ora per una nota. Quando
scade, ZettelApp mostra una notifica; cliccala per aprire la nota. ZettelApp deve essere in esecuzione per avvisarti,
e gli allarmi scaduti mentre era chiuso scattano poco dopo l'apertura del vault. Le note con un allarme mostrano una
campanella nell'elenco delle note. Usa *Rimuovi allarme* nella stessa finestra per cancellarlo.

## Formule

Scrivi LaTeX tra segni di dollaro: `$E = mc^2$` è in linea e `$$\int_0^1 x^2\,dx$$` è una formula in evidenza.
Il pulsante della formula (*Inserisci ▸ Formula…*) apre una finestra con anteprima in tempo reale. Le formule vengono disegnate
nell'anteprima; le esportazioni mantengono il sorgente LaTeX.

## Mappe mentali

Ogni nota può contenere una mappa mentale (la scheda **Mappa mentale**, oppure *Inserisci ▸ Mappa mentale*). I rami sono colorati
automaticamente.

| Tasto | Azione |
|---|---|
| Tab | Aggiungi un'idea figlia |
| Enter | Aggiungi un'idea sorella |
| F2 o doppio clic | Rinomina |
| Del | Elimina l'idea selezionata |
| Tasti freccia | Sposta la selezione |
| Rotellina / trascinamento | Zoom / panoramica |

Fai clic destro su un'idea per **collegarla a una nota**; un'idea collegata mostra un'icona di collegamento e apre quella nota.
**Dai collegamenti** crea una mappa mentale dai collegamenti della nota, raggruppati per tipo di collegamento, con i collegamenti
delle note collegate un livello più in profondità. **Esporta** salva la mappa come immagine PNG o SVG, oppure come file FreeMind
(`.mm`), che FreeMind, Freeplane e XMind possono aprire.

## Flashcard

Le flashcard trasformano le note in materiale di ripasso (vedi [Ripasso, quiz e Anki](review-and-anki.md)). Ci sono
due modi per crearle:

**Nel testo della nota.** Diventano schede automaticamente e si aggiornano mentre modifichi:

```markdown
Q: Who described the forgetting curve?
A: Hermann Ebbinghaus

{{c1::Retrieval practice}} is also called active recall.
```

Una domanda può estendersi su più righe fino alla riga `A:`. Qualsiasi paragrafo con `{{c1::…}}` diventa una
scheda **cloze**, che nasconde a turno ogni cancellazione. `{{c1::testo::suggerimento}}` mostra un suggerimento al posto di `[…]`.

**Nella scheda Flashcard.** Usa *Inserisci ▸ Flashcard…* (Ctrl+Shift+F) per le schede che non devono comparire nel
testo della nota. Le schede dal testo sono contrassegnate come *dal testo della nota* e si modificano nel testo.

## Ricerca

La casella di ricerca (Ctrl+F) usa la ricerca full-text su titoli, testi e tag, ignora gli accenti e trova
i prefissi delle parole, quindi `forget` trova *forgetting*. Aggiungi `tag:nome` per filtrare per tag, per esempio
`memory tag:psychology`. I risultati sono ordinati per pertinenza; senza una query, le note seguono l'ordinamento
scelto (*Ultima modifica*, *Creata*, *Titolo* o *Più collegate*).

## Cestino

*Sposta nel cestino* (Ctrl+Delete) nasconde una nota senza eliminarla. Compare subito un pulsante di annullamento e il pulsante
**Cestino** sotto l'elenco delle note mostra le note cestinate: clic destro per **Ripristina** o **Elimina
definitivamente**. **Svuota cestino** elimina tutto il contenuto dopo una richiesta di conferma. I collegamenti alle note nel cestino sono nascosti
e tornano quando la nota viene ripristinata.
