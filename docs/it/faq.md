# FAQ

### ZettelApp è gratuito?

Sì. È gratuito e open source, rilasciato nel pubblico dominio sotto
[The Unlicense](https://github.com/DutraIRS/ZettelApp/blob/main/LICENSE). La funzione di IA facoltativa usa
la tua chiave API, quindi è il provider a fatturarti direttamente.

### Come posso sostenere ZettelApp?

Grazie per averlo chiesto! Puoi sostenere lo sviluppo su [Ko-fi](https://ko-fi.com/dutrairs). Le aziende possono
sponsorizzare una specifica voce della [roadmap](https://github.com/DutraIRS/ZettelApp/blob/main/ROADMAP.md); mettiti in
contatto tramite [GitHub](https://github.com/DutraIRS/ZettelApp). Gli sponsor vengono ringraziati nelle note di rilascio.
Anche segnalare bug, migliorare la documentazione e far conoscere ZettelApp sono un aiuto.

### Serve Internet?

No. Tutto funziona offline. Internet viene usato solo per un piccolo controllo degli aggiornamenti all'avvio (che puoi
disattivare), quando fai una domanda nella pagina **Chiedi** e quando apri un collegamento. Vedi
[Privacy e sicurezza](privacy-and-security.md).

### ZettelApp cerca gli aggiornamenti?

Sì, una volta all'avvio: una richiesta per un piccolo file sul sito web del progetto, senza nulla su di te o sulle
tue note. Se esiste una versione più recente, compare un avviso nell'angolo in basso a destra. Disattivalo con
*Strumenti ▸ Opzioni ▸ Generale ▸ Cerca aggiornamenti all'avvio di ZettelApp*, oppure con **Non cercare aggiornamenti**
nell'avviso. Vedi [Per iniziare](getting-started.md#updates).

### Cos'è l'interruttore MCP nella barra di stato?

Permette ad assistenti IA come Claude Desktop o Claude Code di usare le tue note tramite
[MCP](mcp-server.md). È **disattivato a ogni avvio di ZettelApp**. Finché è disattivato, o ZettelApp è chiuso,
gli assistenti non possono raggiungere le tue note. Dopo averlo attivato, ricollega ZettelApp nel tuo client MCP (oppure
riavvia il client).

### Posso usare un modello sul mio computer?

Sì. In *Strumenti ▸ Opzioni ▸ Assistente IA*, scegli **OpenAI** e imposta **Endpoint** sul tuo server locale, per
esempio `http://localhost:11434/v1` (Ollama) o `http://localhost:1234/v1` (LM Studio). Per `localhost` non serve
alcuna chiave API. Vedi [Porta il tuo LLM](ai-assistant.md#bring-your-own-llm).

### Dove sono le mie note?

Nella cartella del tuo vault, per impostazione predefinita **Documenti\ZettelApp**: un database `zettel.db` e una cartella `assets`.
*File ▸ Mostra vault in Esplora file* la apre.

### Posso usarlo con OneDrive, Dropbox o Google Drive?

Sì. Metti il vault in una cartella sincronizzata (*File ▸ Nuovo vault…*). Chiudi ZettelApp su un computer prima di
aprire lo stesso vault su un altro, perché due computer che scrivono contemporaneamente possono causare conflitti.

### Come mi sposto su un altro computer?

Copia la cartella del vault, oppure usa *File ▸ Esporta…* ▸ **Archivio ZettelApp** e importalo sull'altro
computer.

### Posso usare il mio vault di Obsidian?

Sì. *File ▸ Importa cartella Markdown…* importa i file Markdown con il loro front matter, `#tag`,
`[[collegamenti]]` e immagini. I tuoi file di Obsidian non vengono modificati. Nell'altra direzione, esporta in **file
Markdown** e apri la cartella in Obsidian.

### Perché ID «Zettel» come 20261027153012?

Ogni nota riceve un ID permanente dall'ora in cui è stata creata (anno, mese, giorno, ora, minuto, secondo).
I titoli possono cambiare; gli ID no, quindi i collegamenti per ID non si rompono mai. Raramente hai bisogno di vederli.

### Qual è la differenza tra un collegamento nel testo e uno nel pannello laterale?

Entrambi sono collegamenti veri. I `[[collegamenti]]` nel testo fanno parte di ciò che scrivi e si rimuovono eliminandoli
dal testo. I collegamenti aggiunti con **Aggiungi collegamento…** o accettando un suggerimento non sono nel testo. Puoi
cambiarne il tipo, invertirne la direzione o rimuoverli nel pannello laterale.

### Perché un suggerimento dice solo «18% · possibile»?

Il numero è la stima onesta del modello che tu colleghi le due note. In un vault giovane o poco denso,
la maggior parte delle coppie di note non è correlata, quindi anche i buoni suggerimenti partono modesti. L'ordine dei suggerimenti
conta di più e le stime migliorano man mano che colleghi e scarti. Vedi
[Suggerimenti di collegamento](link-suggestions.md).

### Funziona su macOS o Linux?

Non ancora. I pacchetti Linux (.deb, AppImage) e macOS sono nella
[roadmap](https://github.com/DutraIRS/ZettelApp/blob/main/ROADMAP.md).

### L'app è disponibile in altre lingue?

Sì. Il programma di installazione e l'app sono tradotti in spagnolo, portoghese (Brasile), francese, tedesco, italiano,
russo, cinese semplificato, giapponese, coreano e arabo. L'app segue per impostazione predefinita la lingua di Windows;
cambiala in *Opzioni*. Il testo mancante ricade sull'inglese.

### Come disinstallo e cosa succede ai miei dati?

*Impostazioni ▸ App ▸ App installate ▸ ZettelApp ▸ Disinstalla*. Il programma di disinstallazione offre un'opzione non selezionata **Elimina anche
le impostazioni e i dati di ZettelApp** che rimuove preferenze, chiavi API salvate, log, cache e
backup automatici, **e tutte le tue note** (database e allegati dei vault). Se non la selezioni, le note vengono conservate. Per la
versione portatile, elimina la sua cartella; le sue preferenze risiedono nel registro sotto
`HKEY_CURRENT_USER\Software\ZettelApp`, mentre log e backup in `%LOCALAPPDATA%\ZettelApp`.

### Qualcosa è andato storto. Dove sono i log?

In `%LOCALAPPDATA%\ZettelApp\Logs`. Includi la parte rilevante quando
[segnali un problema](https://github.com/DutraIRS/ZettelApp/issues). Verifica prima che non contenga nulla di privato.
