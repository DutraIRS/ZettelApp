# Revisão, quizzes e Anki

As notas existem para pensar com elas, e lembrar delas ajuda. O ZettelApp transforma notas em
[flashcards](notes-and-links.md#flashcards) e permite que você os revise dentro do aplicativo ou no Anki.

## Repetição espaçada

A página **Revisão** (Ctrl+4) mostra quantos cartões estão **para hoje**. **Iniciar revisão** passa por eles:

1. Leia a pergunta e tente lembrar a resposta.
2. Pressione **Espaço** (ou *Mostrar resposta*).
3. Avalie-se: **De novo (1)**, **Difícil (2)**, **Bom (3)** ou **Fácil (4)**. Passe o mouse sobre um botão para ver quando
   o cartão voltaria.

O agendamento usa o algoritmo **SM-2** (o algoritmo do SuperMemo, do qual o Anki se originou):

- Os cartões novos voltam após 1 dia, depois 6 dias, e então em intervalos que crescem pelo *fator de facilidade* do cartão
  (2,5 no início).
- *De novo* reinicia o cartão para 1 dia e reduz sua facilidade. *Difícil* encurta o próximo intervalo, e *Fácil*
  o alonga.

Os cartões de lacuna (cloze) geram uma revisão por omissão (`{{c1::…}}`, `{{c2::…}}`, …). Cada pergunta mostra um
link **De:** para sua nota.

## Quizzes

O **Quiz de prática** monta um quiz a partir de um escopo: a coleção inteira, a nota aberta e suas notas ligadas
(com uma profundidade) ou as notas com uma tag. Escolha um estilo e o número de perguntas:

| Estilo | Como funciona |
|---|---|
| **Flashcards (repetição espaçada)** | Como uma revisão, e suas avaliações atualizam o agendamento. |
| **Múltipla escolha** | Escolha a resposta certa entre quatro. As respostas erradas são respostas de outros cartões, de tamanho parecido, então são plausíveis. As teclas 1–4 escolhem. |
| **Digite a resposta** | Digite a resposta e pressione Enter. Ela é avaliada pela similaridade de edição (Levenshtein), ignorando maiúsculas, acentos e formatação: 85% ou mais conta como correta e 60% ou mais como *quase*, então pequenos erros de digitação não te prejudicam. |
| **Dê um nome a essa nota** | Mostra o texto de uma nota com as palavras do título apagadas; escolha o título certo. As opções erradas são as **notas mais parecidas** (por TF-IDF), para que você aprenda a distinguir ideias relacionadas. Não precisa de flashcards. |

*Ferramentas ▸ Quiz sobre a vizinhança desta nota* inicia um quiz sobre a nota aberta e as notas a até dois links
de distância dela. Clique com o botão direito em uma nota no grafo para o mesmo.

## Anki

O ZettelApp funciona com o [Anki](https://apps.ankiweb.net/) de duas maneiras. Ambas usam dois tipos de nota, **ZettelApp
Basic** e **ZettelApp Cloze**, com estes campos:

- *Front* e *Back* (ou *Text* e *Extra* para cartões de lacuna), renderizados a partir de Markdown;
- *Source*, um link de volta para a nota;
- *ZettelID* e *CardKey*.

As tags da sua nota viram tags do Anki (tags aninhadas viram `parent::child`), mais `zettelapp`. As imagens dos cartões
são incluídas como mídia.

### Sincronização com o AnkiConnect

1. No Anki, instale o complemento **AnkiConnect** (*Ferramentas ▸ Complementos ▸ Obter complementos…*, código **2055492159**)
   e reinicie o Anki.
2. Com o Anki em execução, abra a **Revisão** no ZettelApp, escolha o nome do baralho (**Baralho padrão** em
   *Opções ▸ Anki*, `ZettelApp` no início) e o escopo, e pressione
   **Sincronizar com o Anki** (ou *Ferramentas ▸ Sincronizar com o Anki*). *Testar conexão* verifica a ligação.

O ZettelApp lembra qual nota do Anki pertence a cada cartão. Sincronizar de novo **atualiza** os cartões em vez de
adicionar duplicatas, e um cartão pode ser reencontrado pelo seu *CardKey* mesmo que essa memória tenha se perdido. Os cartões
que você exclui no ZettelApp não são excluídos do Anki.

O ZettelApp só conversa com o AnkiConnect neste computador (`127.0.0.1`, porta 8765 por padrão, alterável em
*Opções ▸ Anki*).

### Exportar um baralho (.apkg)

**Exportar baralho (.apkg)…** (ou *Arquivo ▸ Exportar…* com o formato *Baralho do Anki*) grava um pacote que você
importa com *Arquivo ▸ Importar* no Anki. Não é necessário nenhum complemento. Os tipos de nota, o baralho e a identidade de cada cartão são
estáveis, então importar uma exportação mais recente **atualiza** os cartões que você importou antes.

### Do Anki de volta às suas notas

A **Source** de cada cartão é um link `zettelapp://note/<id>`. Clique nele no Anki e a nota abre no
ZettelApp. O instalador configura isso. Na versão portátil, use *Opções ▸ Integração com o Windows ▸
Registrar links*. O manipulador de links só aceita links de *abrir nota*; veja
[Privacidade e segurança](privacy-and-security.md).
