# Suggerimenti di collegamento

Mentre scrivi, il pannello **Collegamenti suggeriti** elenca le note che probabilmente stanno insieme a quella che stai
modificando. Clicca **Collega** per collegarle (la freccia accanto sceglie il tipo di collegamento), oppure **✕** per scartare un
suggerimento. Entrambe le azioni istruiscono il modello. Passa il mouse su un suggerimento per vedere *perché* è stato proposto.

I suggerimenti si aggiornano circa un secondo dopo che smetti di digitare, in background, così l'editor non resta mai in attesa.
Usano anche il tuo testo non ancora salvato.

## Come funziona

ZettelApp tratta «queste due note dovrebbero essere collegate?» come un problema di classificazione e lo risolve con un
classificatore **Naive Bayes**. Per una nota *q* e ogni nota candidata *c*, calcola otto
caratteristiche di similarità e combina le prove in una probabilità.

### Le caratteristiche

| Caratteristica | Cosa misura |
|---|---|
| **Similarità semantica (LSA)** | Similarità del coseno in uno spazio semantico latente: una SVD troncata della matrice TF-IDF (SVD randomizzata, fino a 64 dimensioni). Le note che usano un vocabolario affine finiscono vicine anche se condividono poche parole esatte. |
| **Parole chiave condivise (coseno TF-IDF)** | Similarità del coseno dei vettori TF-IDF (frequenza dei termini sublineare, frequenza inversa dei documenti smussata). I titoli contano il doppio; i tag sono inclusi. |
| **Similarità dei titoli (Levenshtein)** | 1 − distanza di modifica ÷ lunghezza del titolo più lungo. |
| **Similarità dei titoli (Jaro-Winkler)** | Similarità di Jaro-Winkler dei titoli, che premia un inizio in comune. |
| **Similarità dei testi (Levenshtein)** | Distanza di modifica normalizzata tra i primi 400 caratteri dei due testi. |
| **Tag condivisi (Jaccard)** | Tag in comune ÷ tag totali. |
| **Titolo citato nel testo** | 1 se il titolo di una delle due note compare come parole intere nel testo dell'altra, altrimenti 0. |
| **Collegamenti condivisi (Jaccard)** | Sovrapposizione tra le note collegate alle due note (chiusura di triangoli nel grafo). |

Il testo viene convertito in minuscolo, gli accenti vengono eliminati (così *informação* corrisponde a *informacao*), la sintassi Markdown viene
rimossa e le comuni stop word inglesi, portoghesi e spagnole vengono ignorate. Le distanze di modifica usano
[RapidFuzz](https://github.com/rapidfuzz/RapidFuzz); un algoritmo bit-parallelo in puro Python dà
risultati identici quando non è disponibile.

### Dalle caratteristiche a una probabilità

Il valore di ogni caratteristica (tra 0 e 1) viene collocato in uno di **8 intervalli**. Per ogni caratteristica, il modello tiene traccia di
quanto spesso le coppie collegate e non collegate cadono in ciascun intervallo, e stima

```text
P(link | f1 … f8)  ∝  P(link) × Π P(fi | link)
```

L'**evidenza** di una caratteristica è il suo rapporto di log-verosimiglianza, log P(intervallo | link) − log P(intervallo | no link).
La probabilità mostrata è la funzione logistica dei log-odds a priori più la somma (ponderata)
delle evidenze.

**Da dove vengono i conteggi.** Il modello si addestra sul tuo vault ogni volta che cambia in modo apprezzabile:

- **esempi positivi**: ogni coppia di note collegate, più i suggerimenti che hai accettato (nei vault molto grandi vengono
  campionate fino a 600 coppie);
- **esempi negativi**: coppie casuali di note non collegate, tre per ogni esempio positivo, più ogni
  suggerimento che hai **scartato**, che conta il doppio.

**Un prior perché funzioni dal primo giorno.** Prima di qualsiasi dato, ogni intervallo parte con *pseudo-conteggi* di Dirichlet
(10 per caratteristica e classe, per impostazione predefinita). Codificano una convinzione debole: per le coppie collegate i conteggi aumentano
con la similarità, mentre per le coppie non collegate calano bruscamente. Basta per ordinare i suggerimenti in un nuovo
vault. Man mano che colleghi note, i conteggi reali prevalgono sul prior e il modello si adatta al *tuo* modo di collegare.
Poiché positivi e negativi sono campionati in rapporto da uno a tre, il prior di classe P(link) è circa uno su quattro
(con pseudo-conteggi corrispondenti).

**Due correzioni mantengono oneste le stime:**

1. **Nessuna fuga di etichette.** I `[[collegamenti wiki]]` vengono rimossi dal testo prima di calcolare le caratteristiche.
   Altrimenti un collegamento nel testo inserirebbe il titolo della destinazione nel testo e il modello imparerebbe a
   riconoscere i collegamenti esistenti anziché le idee correlate. Per lo stesso motivo, quando si addestra su una coppia
   collegata, la caratteristica «collegamenti condivisi» ignora il collegamento tra le due note.
2. **Le evidenze correlate sono ponderate.** Naive Bayes presume che le caratteristiche siano indipendenti, ma alcune
   non lo sono: TF-IDF e LSA si sovrappongono, così come le tre distanze tra stringhe. Contare evidenze correlate come
   indipendenti rende il Naive Bayes semplice troppo sicuro di sé. ZettelApp quindi moltiplica l'evidenza di ogni caratteristica
   per **0,6** (Naive Bayes con caratteristiche ponderate), il che mantiene realistiche le probabilità.

**Le caratteristiche mancanti o disattivate non contano come evidenza.** Se disattivi una caratteristica, o non può essere
calcolata, non aggiunge nulla: è il modo in cui Naive Bayes gestisce naturalmente i valori mancanti.

### Ordinamento rapido

Confrontare testi lunghi con la distanza di Levenshtein è il passaggio più lento, quindi l'ordinamento avviene in due fasi.
Tutti i candidati vengono prima valutati senza la caratteristica di similarità del testo e solo i migliori 150 ottengono il
punteggio completo. Le note a cui sei già collegato e le coppie che hai scartato non vengono mai suggerite.

## Leggere il suggerimento «perché»

Passa il mouse su un suggerimento per vedere la stima del modello e l'evidenza di ogni caratteristica. I numeri positivi sono a favore di un
collegamento e quelli negativi contro. L'etichetta accanto alla barra riassume la probabilità: **forte**
(50% o più), **probabile** (25% o più) o **possibile**.

Le probabilità sono stime oneste e, in un vault poco denso, la maggior parte delle coppie in effetti non è collegata, quindi il 15–30% può
essere un buon suggerimento. Ciò che conta di più è l'ordine.

## Regolazione

*Strumenti ▸ Opzioni ▸ Suggerimenti di collegamento*:

| Opzione | Predefinito | Effetto |
|---|---|---|
| Suggerisci collegamenti mentre scrivo | attivo | Disattiva del tutto i suggerimenti del pannello. |
| Caratteristiche | tutte e otto | Deseleziona le caratteristiche che non vuoi considerare. |
| Mostra al massimo | 8 | Numero di suggerimenti elencati. |
| Corrispondenza minima | 10% | Nasconde i suggerimenti sotto questa probabilità. |
| Forza del prior | 10 | Quante pseudo-osservazioni sostengono il prior. Valori più alti si fidano più a lungo del prior; valori più bassi si adattano più in fretta ai tuoi collegamenti. |

- **Dettagli del modello…** mostra su quante coppie collegate e non collegate il modello si è addestrato e quanto è informativa
  ogni caratteristica (la divergenza di Kullback–Leibler simmetrica tra le sue distribuzioni per le coppie collegate e
  non collegate).
- **Dimentica i suggerimenti scartati** cancella i tuoi scarti, così quelle coppie possono essere suggerite di nuovo e
  smettono di contare come esempi negativi.
