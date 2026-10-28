# Notas e links

## Escrevendo notas

As notas são escritas em **Markdown**: `**negrito**`, `*itálico*`, `# títulos`, listas, `> citações`,
`` `código` ``, blocos de código delimitados, tabelas e `~~tachado~~`. A barra de ferramentas acima do editor insere as
mais comuns, e Ctrl+B / Ctrl+I funcionam como de costume. As listas continuam quando você pressiona Enter.

O editor tem três modos (Ctrl+E alterna entre eles): **Editar**, **Dividir** (texto e pré-visualização lado a
lado) e **Pré-visualizar**.

Por segurança, HTML bruto em uma nota é exibido como texto e nunca renderizado. Os links na pré-visualização abrem apenas páginas
web (`http`, `https`), e-mail (`mailto`), notas, itens do Zotero e arquivos locais (mostrados no Explorador de Arquivos,
veja [Links para arquivos locais](#links-to-local-files)). Veja [Privacidade e segurança](privacy-and-security.md).

### Seguindo links

- **No editor**, **Ctrl+clique** segue um `[[link de nota]]` (criando a nota se ela ainda não existir),
  um link web, de e-mail ou do Zotero, um link de arquivo local ou uma `#tag` (que lista as notas com essa tag).
  Passe o mouse sobre o texto e uma dica diz o que o clique fará. Um clique simples apenas posiciona o cursor, então
  você ainda pode editar o texto do link.
- **Na pré-visualização**, um clique normal segue os links.

### Links para arquivos locais

*Inserir ▸ Link para um arquivo…* (ou o botão de pasta na barra de ferramentas) permite escolher um arquivo e insere um link
como `[report.pdf](file:///C:/Users/me/Documents/report.pdf)`. Arrastar um arquivo que não seja imagem para
o texto da nota faz o mesmo. O arquivo é ligado onde está; nada é copiado para o cofre.

Clicar no link na pré-visualização, ou Ctrl+clicar nele no editor, abre o **Explorador de Arquivos com o arquivo
selecionado**. O arquivo em si nunca é aberto nem executado. Somente caminhos em uma unidade local são permitidos: caminhos de rede
(UNC), como `\\server\share\file.pdf`, são recusados, porque consultá-los pode enviar suas credenciais do Windows
a esse servidor.

Toda nota tem:

- um **título** (o campo grande no topo);
- um **ID**, um carimbo de data e hora como `20261027153012`, exibido abaixo do título (*Mais ▸ Copiar ID da nota*);
- opcionalmente **tags**, um **link de fonte**, uma **imagem**, um **mapa mental** e **flashcards**.

## Links entre notas

### Links wiki

Digite `[[` e comece a digitar um título: o ZettelApp o completa a partir das suas notas. Dentro de uma nota, todos estes são links:

```markdown
See [[Forgetting curve]].
See [[20261027153012]].              (by ID)
See [[Forgetting curve|the curve]].  (custom link text)
```

Ctrl+K (*Inserir ▸ Link para nota…*) abre um seletor que busca em títulos e textos e permite escolher o
tipo de link. Um link para um título que ainda não existe aparece em cinza na pré-visualização; clique nele para criar
essa nota. Quando você criar ou renomear uma nota depois, os links que mencionam o título dela são atualizados.

### Links tipados

Os links podem dizer **como** duas notas se relacionam. Coloque o tipo de link antes do link, seguido de `::`:

```markdown
supports:: [[Forgetting curve]]
contradicts:: [[Rereading notes]]
part_of:: [[Zettelkasten method]]
```

Os tipos de link embutidos são:

| Tipo | Nome | Nome inverso | Direcionado | Linha | Ponta da seta |
|---|---|---|---|---|---|
| `related` | Relacionada a | Relacionada a | não | sólida, cinza | nenhuma |
| `supports` | Apoia | Apoiada por | sim | tracejada, verde | triângulo preenchido |
| `contradicts` | Contradiz | Contradiz | não | pontilhada, vermelha | nenhuma |
| `extends` | Estende | Estendida por | sim | traço-ponto, azul | triângulo preenchido |
| `example` | Exemplo de | Tem exemplo | sim | traço-ponto-ponto, âmbar | círculo |
| `part_of` | Parte de | Contém | sim | traço longo, roxo | losango |
| `cites` | Cita | Citada por | sim | sólida, verde-azulada | seta aberta |

Este é o visual de um cofre novo; você pode alterá-lo (veja abaixo). Um cofre criado com uma versão anterior
mantém as linhas que tinha.

Um `[[link]]` simples é *Relacionada a*.

### Links direcionados e não direcionados

Um tipo **direcionado** se lê de forma diferente de cada lado. Se a nota A *apoia* a nota B, os backlinks de B
mostram A como *Apoiada por*. Os links direcionados ganham pontas de seta no grafo e continuam direcionados nas exportações.
Os tipos **não direcionados**, como *Relacionada a* e *Contradiz*, se leem igual nos dois sentidos.

Para inverter um link direcionado criado ao contrário, clique com o botão direito nele no painel lateral e escolha
**Inverter direção**. Os links escritos no texto são invertidos editando-se o texto.

### Links no painel lateral

O painel lateral lista os **Links** da nota (saída) e os **Backlinks** (entrada), cada um com seu tipo.

- **Adicionar link…** cria um link sem escrevê-lo no texto.
- Clique com o botão direito em um link para abrir a outra nota, alterar o tipo de link, inverter sua direção ou removê-lo.
  Os links escritos no texto são removidos editando-se o texto.
- Na lista de notas, clique com o botão direito em outra nota e escolha **Ligar a partir da nota aberta como**.

### Seus próprios tipos de link

Adicione, renomeie, altere o estilo ou remova tipos de link em *Ferramentas ▸ Opções ▸ Tipos de link*. Escolha um tipo na lista e
altere-o ao lado dela:

- **Nome** e **Nome inverso**: como o link se lê a partir da origem e a partir do destino. O nome
  inverso é usado apenas por tipos direcionados.
- **Direcionado**: se o tipo se lê de forma diferente de cada lado e ganha uma ponta de seta.
- **Cor**: clique no botão de cor para escolher qualquer cor.
- **Linha**: sólida, tracejada, pontilhada, traço-ponto, traço-ponto-ponto ou traço longo.
- **Ponta da seta**: a ponta desenhada onde um link direcionado chega: um triângulo preenchido, uma seta aberta, um
  losango, um círculo ou uma barra.

A pré-visualização mostra duas notas unidas pelo link, com seu nome e como ele se lê do outro lado.
O estilo é usado onde quer que os links apareçam: o grafo, sua legenda, o painel lateral, o seletor de links e
as exportações de site, GraphML e Graphviz. Dê a cada tipo sua própria linha, além de sua própria cor, para que
os tipos continuem fáceis de distinguir para leitores daltônicos e no papel. Um novo tipo começa com uma
cor e uma linha que poucos outros tipos usam.

No texto, use o id do tipo, mostrado abaixo da pré-visualização (por exemplo, um tipo chamado "Inspirada por" vira
`inspired_by::`). O id é definido quando o tipo é criado, então renomear um tipo não quebra os links
escritos nas suas notas. Remover um dos seus próprios tipos transforma seus links em links *Relacionada a*, de modo que
nada se perde. Os tipos embutidos podem ser renomeados e ter o estilo alterado, mas não removidos.

## Tags

Adicione tags no campo de tags abaixo do título (pressione Enter após cada uma) ou escreva-as **no texto** com um
sinal de cerquilha, como `#welcome` ou `#math/algebra`. As tags são em minúsculas e podem ser aninhadas com uma barra, como
`math/algebra`. Filtrar por `math` também encontra as notas com a tag `math/algebra`.
Use o filtro de tags acima da lista de notas ou digite `tag:nome` na caixa de busca.

As tags escritas no texto são tags de verdade, exibidas como **chips com contorno** ao lado da caixa *Adicionar tag*. Elas
desaparecem quando você apaga a `#tag` do texto. Uma `#tag` é ignorada dentro de código, dentro de destinos de link
e em `[[#headings]]`. As tags digitadas na caixa *Adicionar tag* são independentes: permanecem até você removê-las com
o ✕ delas. Ctrl+clique em uma `#tag` no editor para listar as notas que a têm.

## Link da fonte

O campo com o ícone de globo guarda a **fonte** da nota: uma página web (`https://…`), um endereço de e-mail
ou um item do Zotero (`zotero://select/library/items/…`). O botão ao lado dele abre o link. Outros tipos de
link são recusados. Veja [Zotero](zotero.md) para criar notas diretamente da sua biblioteca do Zotero.

## Imagens

Insira imagens com *Inserir ▸ Imagem…* (Ctrl+Shift+I), **colando** da área de transferência ou
**arrastando** arquivos de imagem para o editor. Formatos aceitos: PNG, JPEG, GIF, WebP e BMP, até 25 MB.
O SVG é recusado de propósito, porque arquivos SVG podem conter scripts.

As imagens são verificadas pelo conteúdo (não pelo nome do arquivo), armazenadas uma única vez na pasta `assets` do cofre
com um nome derivado do conteúdo, e referenciadas assim:

```markdown
![Diagram](asset:3f2a9c0b1d4e5f6a7b8c.png)
```

A primeira imagem que você adiciona a uma nota vira a sua **imagem do título**. Ela é exibida como uma pequena miniatura arredondada na
lista de notas e dentro do círculo da nota no grafo. Clique com o botão direito em qualquer imagem no editor ou na pré-visualização
e escolha *Usar como imagem do título* para escolher outra, ou *Remover imagem do título* para ficar sem nenhuma.
Apagar a imagem do título do texto da nota também a remove como imagem do título.

## Checklists

Comece uma linha com `- [ ]` (ou pressione o botão de checklist na barra de ferramentas) para criar uma tarefa. `- [x]` é uma
tarefa concluída. Na pré-visualização, clique na caixa para marcá-la; pressionar Enter no fim de uma tarefa inicia a
próxima, e Enter em uma tarefa vazia encerra a lista.

## Alarmes

Pressione o botão de alarme (ou *Inserir ▸ Alarme…*) para definir uma data e, opcionalmente, um horário para uma nota. Quando chegar
a hora, o ZettelApp mostra uma notificação; clique nela para abrir a nota. O ZettelApp precisa estar em execução para avisar você,
e os alarmes que venceram enquanto ele estava fechado disparam logo depois que você abre o cofre. As notas com alarme mostram um
sino na lista de notas. Use *Remover alarme* na mesma caixa de diálogo para limpá-lo.

## Fórmulas

Escreva LaTeX entre cifrões: `$E = mc^2$` é em linha e `$$\int_0^1 x^2\,dx$$` é uma fórmula em destaque.
O botão de fórmula (*Inserir ▸ Fórmula…*) abre uma caixa de diálogo com pré-visualização ao vivo. As fórmulas são desenhadas na
pré-visualização; as exportações mantêm o código-fonte LaTeX.

## Mapas mentais

Cada nota pode ter um mapa mental (a aba **Mapa mental**, ou *Inserir ▸ Mapa mental*). Os ramos são coloridos
automaticamente.

| Tecla | Ação |
|---|---|
| Tab | Adicionar uma ideia filha |
| Enter | Adicionar uma ideia irmã |
| F2 ou clique duplo | Renomear |
| Del | Excluir a ideia selecionada |
| Setas do teclado | Mover a seleção |
| Roda do mouse / arrastar | Zoom / deslocar |

Clique com o botão direito em uma ideia para **ligá-la a uma nota**; uma ideia ligada mostra um ícone de link e abre essa nota.
**A partir dos links** constrói um mapa mental a partir dos links da nota, agrupados por tipo de link, com os
próprios links das notas ligadas um nível abaixo. **Exportar** salva o mapa como uma imagem PNG ou SVG, ou como um arquivo FreeMind
(`.mm`), que o FreeMind, o Freeplane e o XMind conseguem abrir.

## Flashcards

Os flashcards transformam notas em material de revisão (veja [Revisão, quizzes e Anki](review-and-anki.md)). Há
duas maneiras de criá-los:

**No texto da nota.** Eles viram cartões automaticamente e são atualizados conforme você edita:

```markdown
Q: Who described the forgetting curve?
A: Hermann Ebbinghaus

{{c1::Retrieval practice}} is also called active recall.
```

Uma pergunta pode ocupar várias linhas até a linha `A:`. Qualquer parágrafo com `{{c1::…}}` vira um cartão de
**lacuna (cloze)**, que oculta cada omissão em sequência. `{{c1::texto::dica}}` mostra uma dica em vez de `[…]`.

**Na aba Flashcards.** Use *Inserir ▸ Flashcard…* (Ctrl+Shift+F) para cartões que não devem aparecer na
nota. Os cartões do texto são marcados como *do texto da nota* e são editados no texto.

## Busca

A caixa de busca (Ctrl+F) usa busca de texto completo em títulos, textos e tags, ignora acentos e corresponde a
prefixos de palavras, então `esquec` encontra *esquecimento*. Adicione `tag:nome` para filtrar por tag, por exemplo
`memory tag:psychology`. Os resultados são ordenados por relevância; sem uma consulta, as notas seguem a ordenação
escolhida (*Última edição*, *Criada*, *Título* ou *Mais ligadas*).

## Lixeira

*Mover para a lixeira* (Ctrl+Delete) oculta uma nota sem excluí-la. Um botão de desfazer aparece imediatamente, e
o botão **Lixeira** abaixo da lista de notas mostra as notas na lixeira: clique com o botão direito para **Restaurar** ou **Excluir
permanentemente**. **Esvaziar lixeira** exclui tudo o que há nela após pedir confirmação. Os links para notas na lixeira ficam ocultos
e voltam quando a nota é restaurada.
