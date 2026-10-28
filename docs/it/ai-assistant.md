# Chiedi alle tue note (IA)

La pagina **Chiedi** (Ctrl+5) risponde alle domande **dalle tue note**, con citazioni su cui puoi cliccare. Usa un
provider di IA a tua scelta con la tua chiave API. È del tutto facoltativa: nulla viene inviato da nessuna parte finché non
fai una domanda.

![Chiedi alle tue note](../website/assets/screenshots/ask-light.png)

## Configurazione

1. Ottieni una chiave API da uno dei provider supportati.
2. Apri *Strumenti ▸ Opzioni ▸ Assistente IA*. Scegli il **provider**, incolla la **chiave API** e scegli un
   **modello** (*Aggiorna elenco* chiede al provider quali modelli la tua chiave può usare).

   Puoi salvare più chiavi per provider (per esempio personale e di lavoro). Usa *Aggiungi chiave…*, *Rinomina…* e
   *Rimuovi* accanto all'elenco delle chiavi; la chiave selezionata è quella usata da Chiedi.
3. Premi **Prova connessione**, poi **OK**.

| Provider | Modello predefinito | Altri modelli suggeriti | Endpoint |
|---|---|---|---|
| **Anthropic Claude** (predefinito) | `claude-opus-5-5` | `claude-sonnet-5-5`, `claude-haiku-5-5` | `https://api.anthropic.com` |
| **OpenAI** | `gpt-6.1-sol` | `gpt-6-astra`, `gpt-6-luna` | `https://api.openai.com/v1` |
| **Z.ai (GLM)** | `glm-5.3` | `glm-5.3-flash`, `glm-4.7-flash` | `https://api.z.ai/api/paas/v4` |

Puoi scrivere qualsiasi ID di modello a cui la tua chiave dà accesso. **Endpoint (facoltativo)** sostituisce l'indirizzo, per
esempio per usare un endpoint del piano coding di Z.ai, un proxy compatibile con OpenAI o un modello in esecuzione sul tuo
computer (`http://localhost:…`). Gli indirizzi devono usare `https://`; `http://` semplice è accettato solo per
`localhost`.

Con Claude puoi anche impostare l'**impegno** (da basso a massimo): un impegno maggiore ragiona di più prima di rispondere e
costa di più. Il valore predefinito è *medio*.

## Porta il tuo LLM

Chiedi usa **il tuo account** presso il provider che scegli, quindi qualsiasi utilizzo viene fatturato a te da quel provider.
ZettelApp non ha un servizio di IA proprio. La tua chiave API è salvata in **Gestione credenziali di Windows**, mai nei
file di impostazioni.

- **Provider**: Anthropic Claude, OpenAI e Z.ai (GLM), in *Strumenti ▸ Opzioni ▸ Assistente IA ▸ Provider*.
  Scegli un **Modello** dall'elenco (*Aggiorna elenco* chiede al provider quali modelli la tua chiave può usare) oppure scrivi
  qualsiasi ID di modello a cui la tua chiave dà accesso.
- **Il tuo server**: funziona qualsiasi servizio che offra un'API **chat completions in stile OpenAI**. Scegli
  **OpenAI** e imposta **Endpoint (facoltativo)** sul suo indirizzo di base, per esempio
  `https://my-proxy.example.com/v1`, `http://localhost:11434/v1` (Ollama) o `http://localhost:1234/v1`
  (LM Studio). `http://` semplice è accettato solo per `localhost`, `127.0.0.1` e `::1`; tutto il resto
  deve usare `https://`. Per questi indirizzi locali la **chiave API** può restare vuota.
- **Verifica**: premi **Prova connessione**. Con un modello locale, la tua domanda e le note non lasciano mai il tuo
  computer.
- **Cosa viene inviato**: solo la tua domanda e le note più pertinenti, trovate sul tuo computer. Il numero di
  note è la casella **quante note** nella pagina Chiedi (8 per impostazione predefinita) e l'elenco *Fonti inviate* mostra
  esattamente quali sono state inviate.

## Fai una domanda

Scrivi una domanda e premi **Chiedi** (Ctrl+Enter). Scegli dove cercare con **Cerca in**: l'intera
raccolta, la nota aperta e le sue note collegate oppure le note con un tag. Scegli **quante note** inviare.

Cosa succede:

1. ZettelApp trova le note più pertinenti **sul tuo computer**, usando la stessa similarità TF-IDF e LSA
   del [suggeritore di collegamenti](link-suggestions.md). Con *Nota corrente e note collegate*, la nota aperta
   viene sempre per prima.
2. La tua domanda e quelle note vengono inviate al provider, per al massimo 120.000 caratteri di note. Una nota
   tagliata per starci termina con un indicatore visibile «[note truncated]». L'elenco **Fonti inviate** mostra esattamente quali
   note sono state inviate.
3. La risposta arriva in streaming mentre viene scritta. Le citazioni come `[[20261027153012]]` compaiono come collegamenti alle
   note. **Ferma** la annulla.

Al modello viene detto di rispondere solo dalle tue note e di dire quando non contengono la risposta. **Copia**
copia la risposta come Markdown. **Salva come nota** la conserva come nuova nota con il tag `ai-answer`, con collegamenti `cites::`
alle sue fonti.

## Privacy e sicurezza

- **Viene inviato solo ciò che chiedi**: la tua domanda e le note elencate sotto *Fonti inviate*. Un avviso
  te lo ricorda prima di chiedere (seleziona *Non mostrare più* per saltarlo).
- **La tua chiave API** è conservata in **Gestione credenziali di Windows** (come `ZettelApp/llm/<provider>`), mai nei
  file di impostazioni o nei log, ed è rimossa da qualsiasi messaggio di errore che ti viene mostrato. *Elimina chiave* la cancella.
- **Il modello non ha strumenti.** Non può cercare sul web, eseguire codice o modificare le tue note, quindi le istruzioni
  nascoste in una nota (o in un file importato) non possono fargli fare nulla. La risposta viene mostrata con lo stesso
  renderer sicuro delle note, senza HTML né script.
- Con Claude, ZettelApp usa l'SDK ufficiale di Anthropic e aderisce al **fallback di rifiuto lato server**: se
  una richiesta viene rifiutata da un classificatore di sicurezza, Anthropic la ritenta sul modello di fallback consigliato.
  Questo vale per Claude Opus 5.5, Opus 5, Sonnet 5.5 e Fable 5.1.
- Si applicano i termini e le politiche sui dati di ciascun provider a ciò che invii.

## Aggiungere un altro provider

I provider risiedono in un piccolo registro (`PROVIDERS` in `zettelapp/core/llm.py`). Un servizio che parla un
protocollo esistente (la Messages API di Anthropic, oppure chat completions in stile OpenAI, che molti provider
offrono) è **una sola voce**: il suo nome, l'endpoint, il modello predefinito e la pagina dove gli utenti ottengono una chiave. Un nuovo
protocollo richiede una piccola classe adattatore. Vedi [Sviluppo](development.md).
