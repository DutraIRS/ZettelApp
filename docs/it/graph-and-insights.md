# Grafo e Statistiche

## Il grafo

La pagina **Grafo** (Ctrl+2) disegna le tue note come una rete: ogni cerchio è una nota, dimensionato in base a quanti collegamenti
ha, e ogni linea è un collegamento.

![Il grafo, colorato per tag](../website/assets/screenshots/graph-light.png)

### Controlli

| Controllo | Cosa fa |
|---|---|
| **Tutte le note / Locale** | Mostra l'intera raccolta, oppure solo la nota aperta e le note entro **Profondità** collegamenti da essa (seguendo i collegamenti in entrambe le direzioni). *Mostra nel grafo* nel menu ⋯ di una nota apre il grafo locale. |
| **2D / 3D** | Passa da una disposizione piatta e trascinabile a una vista 3D intorno a cui puoi orbitare. |
| **Colora per** | Tag, *Cluster: k-means*, *Cluster: gerarchico*, oppure nulla. |
| **k** | Numero di cluster. *k automatico* lo sceglie per te (vedi sotto). |
| **Raggruppa** | Avvicina le note dello stesso gruppo e ombreggia l'area di ciascun gruppo. |
| **Etichette** | Mostra i titoli delle note. Nei grafi grandi, solo le note meglio collegate sono etichettate finché non ci passi sopra con il mouse. |
| **Tipi di collegamento** | Nascondi o mostra i singoli tipi di collegamento. |
| **Trova nel grafo** | Scrivi parte di un titolo e premi Enter per saltare alla nota. |

In basso a destra ci sono zoom, adatta, **ricalcola disposizione**, **salva come immagine** (PNG) ed **esporta queste
note** (apre la finestra di [esportazione](export-import.md) con le note presenti sullo schermo).

**In 2D**, trascina una nota per spostarla, trascina lo sfondo per la panoramica e usa la rotellina del mouse per lo zoom. Doppio clic
su una nota per aprirla; clic destro per altre opzioni (apri, grafo locale, quiz su questo vicinato, esporta con
le note collegate). L'immagine di una nota è mostrata dentro il suo cerchio.

Più collegamenti tra le stesse due note sono disegnati come **curve separate**, ciascuna con la propria punta di freccia
che segue la curva, così nessuna ne nasconde un'altra. Passare il mouse o selezionare una nota **attenua gli altri collegamenti**, mantiene i collegamenti della nota nei
colori del loro tipo ed etichetta ogni vicina con i tipi di collegamento **letti da quella nota**, per esempio
*Supporta · Esteso da*. Funziona allo stesso modo in 2D e 3D.

**In 3D**, trascina per orbitare, usa la rotellina per lo zoom e fai doppio clic su una nota per aprirla. **Ruota
automaticamente** fa girare la vista. Le note più vicine sono più grandi e luminose, quindi la profondità si legge facilmente, e ogni
gruppo appare come un morbido alone colorato.

La disposizione è guidata da forze (Fruchterman–Reingold): i collegamenti avvicinano le note, tutte le note si respingono
a vicenda e una leggera gravità mantiene sullo schermo i componenti separati. Viene eseguita in background ed è
memorizzata nella cache per vista.

### Colorare per tag

Ogni nota assume il colore del suo **tag più comune**, quello usato dal maggior numero di note nella vista, così i
grandi temi del tuo vault ottengono colori distinti.

### Colorare per cluster

Il clustering raggruppa le note **per significato**, siano collegate o no. Ogni nota diventa un vettore in uno
spazio semantico tramite l'analisi semantica latente (LSA) di titolo, testo e tag. Poi uno di due metodi
raggruppa i vettori:

- **k-means**: l'algoritmo di Lloyd con inizializzazione k-means++, il migliore tra diverse esecuzioni. È veloce e produce
  gruppi tondeggianti e di dimensioni simili.
- **Gerarchico**: clustering agglomerativo con legame medio sulla distanza del coseno, calcolato con l'algoritmo
  della catena dei vicini più prossimi (O(n²)). Funziona meglio per argomenti irregolari e annidati. I vault con più di
  4.000 note ripiegano su k-means.

Con **k automatico**, ZettelApp prova k da 2 fino a circa √(n/2) + 2 (al massimo 12) e mantiene il k con il
miglior **punteggio silhouette**. Il punteggio, mostrato sotto la legenda, misura quanto sono ben separati i cluster:
1 è perfetto, intorno a 0 indica gruppi sovrapposti. Ogni cluster prende il nome dalle sue parole più
distintive, i termini più frequenti al suo interno che nel resto del vault.

### Gruppi e colori

Con **Raggruppa** attivo, le note con lo stesso tag o cluster vengono attratte tra loro e ogni gruppo ottiene un'
area leggermente ombreggiata con il suo nome. La legenda elenca i gruppi con le loro dimensioni. Cliccane uno per
evidenziarne le note.

I colori di gruppi e grafici provengono da una tavolozza **validata per le deficienze della visione dei colori** sia in modalità chiara
sia scura. I colori sono assegnati in un ordine fisso e mai riutilizzati: i gruppi oltre l'ottavo condividono un
grigio neutro «Altro». I **tipi di collegamento** usano un secondo indizio oltre al colore: ciascuno ha la propria linea
(continua, tratteggiata, punteggiata e così via) e i tipi orientati disegnano una punta di freccia come un triangolo o un rombo.
Scegli in *Strumenti ▸ Opzioni ▸ Tipi di collegamento* (vedi [I tuoi tipi di collegamento](notes-and-links.md#your-own-link-types)).
La legenda nomina sempre tutto, quindi nulla dipende dal solo colore.

## Statistiche

La pagina **Statistiche** (Ctrl+3) riassume il tuo vault:

- **Riquadri**: note (e quante sono nel Cestino), collegamenti (e collegamenti per nota), tag, *note non collegate*
  (buoni candidati da collegare), flashcard e schede da ripassare oggi.
- **Note aggiunte per mese** negli ultimi 12 mesi.
- **Tag principali**, **Collegamenti per tipo** e **Note più connesse** (clicca una barra per aprire la nota).
- **Argomenti**: cluster k-means delle tue note con le loro parole chiave e dimensioni.

Ogni grafico ha un pulsante **Mostra come tabella** (l'icona a elenco) con gli stessi numeri in forma di tabella, e le barre
mostrano il loro valore al passaggio del mouse.
