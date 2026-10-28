# Tutorial: seus primeiros 30 minutos

Um passeio prático. Cada passo diz o que fazer e o que você deve ver. Os passos marcados como *opcional* precisam do Zotero,
de uma chave de IA ou do Anki; pule-os se você não usa essas ferramentas.

Novo no próprio método? Leia primeiro [O que é um Zettelkasten?](what-is-zettelkasten.md). Leva cinco
minutos.

## 1. Instale e abra o cofre de boas-vindas

1. Baixe o **ZettelApp-Setup.exe** da [versão mais recente](https://github.com/DutraIRS/ZettelApp/releases/latest)
   e execute-o, ou descompacte o **ZettelApp-Portable.zip** e execute `ZettelApp.exe`.
2. Inicie o ZettelApp.

**Você deve ver** a página Notas com onze notas iniciais ligadas entre si, em um novo cofre em
*Documentos\ZettelApp*. "Bem-vindo ao ZettelApp" está aberta no editor. Depois de um instante, o ZettelApp também oferece a
aventura opcional *O Príncipe Perdido do Arquivo*; escolha **Agora não** se preferir este tour escrito.

## 2. Crie uma nota

1. Pressione **Ctrl+N**.
2. Digite um título, por exemplo *Repetição espaçada*, e pressione **Enter** para ir ao texto.
3. Escreva uma ideia com suas próprias palavras, em duas ou três frases:
   *Revisar o conteúdo em intervalos crescentes ajuda a memória de longo prazo, porque cada revisão acontece logo
   antes do esquecimento.*

**Você deve ver** a nota aparecer no topo da lista. Não há botão Salvar: as notas são salvas enquanto você
digita. O ID abaixo do título (por exemplo `20261027153012`) é o endereço permanente da nota.

## 3. Adicione tags

Clique em **Adicionar tag** abaixo do título, digite `learning` e pressione **Enter**. Adicione `memory` também.

**Você deve ver** dois chips, *#learning* e *#memory*. O filtro de tags acima da lista agora os oferece,
e digitar `tag:memory` na caixa de busca encontra a nota.

## 4. Ligue a outra nota

1. Crie uma segunda nota (**Ctrl+N**) com o título *Curva do esquecimento* e uma frase: *A memória se esvai
   rapidamente, a menos que a informação seja revisada.*
2. Volte para *Repetição espaçada* (clique nela na lista). No texto, digite `[[` e depois `Curv`.
3. Escolha **Curva do esquecimento** na lista de preenchimento e pressione **Enter**.

**Você deve ver** `[[Curva do esquecimento]]` sublinhado no texto. No painel lateral, *Curva do esquecimento*
aparece em **Links**. Clique no botão de olho (**Visão dividida**) na barra de ferramentas: a pré-visualização mostra um link
clicável.

## 5. Diga *como* as notas se relacionam

Transforme o link em um link tipado colocando `supports::` na frente:

```markdown
supports:: [[Curva do esquecimento]]
```

**Você deve ver** o link listado como *Apoia* no painel lateral. Abra *Curva do esquecimento*: seus
**Backlinks** dizem *Repetição espaçada: **Apoiada por***, porque *supports* é um tipo de link direcionado.
Os `[[links]]` simples significam *Relacionada a*.

## 6. Use um link sugerido

Escreva mais algumas notas sobre ideias relacionadas, por exemplo *Recordação ativa* e *Intercalação*, cada uma com uma
ou duas frases e a tag `learning`. Depois abra uma delas e olhe os **Links sugeridos** no
painel lateral.

- Clique em **Link** para aceitar uma sugestão. A pequena seta ao lado dele escolhe um tipo de link.
- Clique em **✕** para dispensar uma que não serve.
- Passe o mouse sobre uma sugestão para ver **por que** ela foi sugerida: a evidência de cada medida a favor ou contra.

**O que o modelo aprende:** as sugestões aceitas viram links, que treinam o classificador como exemplos
positivos. As dispensadas são lembradas como exemplos negativos e nunca mais são sugeridas para aquele par.
As sugestões melhoram quanto mais você as usa. Veja [Sugestões de links](link-suggestions.md).

![Notas com links sugeridos](../website/assets/screenshots/notes-light.png)

## 7. Adicione uma imagem

Copie qualquer imagem (por exemplo com *Win+Shift+S*), clique no texto da nota e pressione **Ctrl+V**. Você também pode
arrastar um arquivo de imagem para dentro ou usar *Inserir ▸ Imagem…*.

**Você deve ver** `![…](asset:…)` no texto e a imagem na pré-visualização. Como é a primeira imagem da nota,
ela também vira a **imagem da nota**, exibida ao lado do título e dentro do círculo da nota
no grafo.

## 8. Esboce um mapa mental

1. Abra a aba **Mapa mental** e clique em **Adicionar ideia**.
2. Pressione **Tab** para adicionar uma ideia filha, **Enter** para uma irmã, **F2** para renomear e **Del** para excluir.
   As setas do teclado movem entre as ideias.
3. Agora clique em **A partir dos links** e confirme que ele pode substituir o mapa que você acabou de desenhar.

**Você deve ver** um mapa mental construído a partir dos links da nota, agrupado por tipo de link, com os próprios
links de cada nota ligada um nível abaixo. Clique com o botão direito em qualquer ideia para ligá-la a uma nota. O botão de exportação salva PNG, SVG
ou FreeMind.

![Um mapa mental](../website/assets/screenshots/mindmap-light.png)

## 9. Crie flashcards e revise-os

Adicione estas linhas ao texto de *Repetição espaçada*:

```markdown
Q: Why space reviews out?
A: Each effortful retrieval just before forgetting strengthens the memory.

{{c1::Hermann Ebbinghaus}} described the forgetting curve.
```

**Você deve ver** **Flashcards (2)** na aba: um cartão de pergunta e um cartão de lacuna (cloze). Agora abra **Revisão**
(**Ctrl+4**) e clique em **Iniciar revisão**.

- Pressione **Espaço** para mostrar a resposta.
- Avalie-se com **1–4** (*De novo, Difícil, Bom, Fácil*).

O cronograma SM-2 decide quando cada cartão volta. Experimente também **Quiz de prática ▸ Múltipla escolha** ou **Dê um nome a
essa nota**.

![Um quiz de múltipla escolha](../website/assets/screenshots/quiz-light.png)

## 10. Explore o grafo

Abra o **Grafo** (**Ctrl+2**).

1. Arraste as notas, use a roda para dar zoom e passe o mouse sobre uma nota para destacar suas vizinhas.
2. Selecione uma nota na página Notas, volte e clique em **Local**, depois mude a **Profundidade** para 1, 2 ou 3.
3. Defina **Cor por** como **Clusters: k-means**. As notas são agrupadas por significado, e a legenda nomeia cada
   cluster por suas palavras-chave.
4. Ative **Grupo** para juntar cada grupo sobre um fundo sombreado.
5. Clique em **3D**, arraste para orbitar e experimente **Girar automaticamente**.

![O grafo, colorido por tag e agrupado](../website/assets/screenshots/graph-light.png)

## 11. Confira seus Insights

Abra o **Insights** (**Ctrl+3**) para ver contagens, notas por mês, principais tags, links por tipo e as notas mais
conectadas. **Notas sem links** é a sua lista de tarefas: ligue-as a alguma coisa. Todo gráfico tem uma visualização
em tabela.

## 12. Cite um item do Zotero e escreva uma nota de literatura (opcional)

Com o Zotero 7+ em execução e a opção *Permitir que outros aplicativos neste computador se comuniquem com o Zotero* ativada
em *Configurações ▸ Avançado*:

1. Escolha *Inserir ▸ Referência do Zotero…*, busque um item e clique em **Inserir citação**: um link como
   *Ebbinghaus (1885)* que abre o item no Zotero.
2. Faça de novo e clique em **Nova nota de literatura**.

**Você deve ver** uma nova nota com a referência, os links *Abrir no Zotero* e *Abrir PDF*, o resumo e as
seções *Ideias-chave* / *Meus pensamentos*, com a tag `literature`. Veja [Zotero](zotero.md).

## 13. Pergunte às suas notas (opcional)

1. Em *Ferramentas ▸ Opções ▸ Assistente de IA*, escolha um provedor (Anthropic, OpenAI ou Z.ai), cole sua chave de API
   e clique em **Testar conexão**.
2. Abra **Perguntar** (**Ctrl+5**) e pergunte: *Como o espaçamento e a recordação funcionam juntos?*

**Você deve ver** uma resposta que cita suas notas como links e a lista exata de **fontes enviadas**. Somente
essas notas e sua pergunta saem do seu computador. Veja [Pergunte às suas notas](ai-assistant.md).

## 14. Exporte um subgrafo e sincronize com o Anki (opcional)

1. Abra uma nota, escolha *Arquivo ▸ Exportar…* (**Ctrl+Shift+E**), selecione **Nota atual e notas ligadas**,
   profundidade 2 e o formato **Website**.
2. Abra o `index.html` do zip no navegador: um pequeno site dessa parte do seu Zettelkasten.
3. Com o Anki em execução e o complemento AnkiConnect (código `2055492159`) instalado, abra **Revisão** e clique em
   **Sincronizar com o Anki**. O link da fonte de cada cartão abre a nota no ZettelApp.

Veja [Exportar e importar](export-import.md) e [Anki](review-and-anki.md#anki).

## 15. Saiba onde ficam seus dados

- Suas notas ficam na pasta do cofre (*Arquivo ▸ Mostrar cofre no Explorador de Arquivos*): `zettel.db` mais `assets`.
- Um backup é feito automaticamente uma vez por dia, e *Arquivo ▸ Fazer backup do cofre agora* faz um a qualquer momento.
- As notas excluídas vão para a **Lixeira**, abaixo da lista de notas, onde você pode restaurá-las.

Detalhes em [Privacidade e segurança](privacy-and-security.md).

**É isso.** Continue escrevendo uma ideia por nota, ligue cada nova nota com um motivo e deixe as sugestões e
o grafo mostrarem o que você tem. Os atalhos estão em [Atalhos de teclado](keyboard-shortcuts.md).
