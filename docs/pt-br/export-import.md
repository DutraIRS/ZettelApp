# Exportar e importar

## Exportar

*Arquivo ▸ Exportar…* (Ctrl+Shift+E) exporta **a coleção inteira ou qualquer parte dela**:

| Escopo | O que é exportado |
|---|---|
| **Coleção inteira** | Todas as notas (exceto a Lixeira). |
| **Nota atual e notas ligadas** | A nota aberta e as notas a até **Profundidade** links dela, seguindo links nos dois sentidos: um *subgrafo*. |
| **Notas com tag** | Notas com a tag, incluindo tags aninhadas (`math` inclui `math/algebra`). |

A caixa de diálogo mostra quantas notas, links e flashcards o escopo contém. Você também pode exportar pela
lista de notas (clique com o botão direito ▸ *Exportar com notas ligadas…*), pelo menu ⋯ de uma nota, pelo grafo (o botão de exportação
exporta as notas na tela) e pelo menu de um nó do grafo.

### Formatos

| Formato | Arquivo | Conteúdo |
|---|---|---|
| **Arquivo do ZettelApp** | `.zip` | Tudo, incluindo imagens: notas, links tipados, tipos de link (com suas cores, estilos de linha e pontas de seta), flashcards, mapas mentais. Reimporte-o no ZettelApp em qualquer computador. Ideal para backups e para mover cofres. |
| **Arquivos Markdown** | `.zip` | Um arquivo `.md` por nota com front matter YAML (id, título, tags, link de fonte, datas, links tipados, mapa mental) e `[[links wiki]]` entre os arquivos. Os links não escritos no texto são listados em *Links* como `type:: [[Nota]]`, e os flashcards manuais em *Flashcards* como `Q:`/`A:`. As imagens ficam em `assets/`. Abre no Obsidian e em outros editores Markdown. |
| **Website** | `.zip` | Um site estático autocontido: um índice com uma visão geral do grafo, um índice de tags e uma página por nota, com os links desenhados nas cores e estilos de linha de seus tipos de link, mapas mentais e flashcards (respostas reveladas ao clicar). Sem scripts; funciona offline abrindo o `index.html`. Temas claro e escuro. |
| **JSON** | `.json` | Dados estruturados para scripts e outras ferramentas (imagens referenciadas, não incluídas). |
| **GraphML** | `.graphml` | O grafo de links para Gephi, yEd, Cytoscape ou NetworkX, com títulos, tags e datas nos nós e tipos de link nas arestas (direcionadas ou não), com a cor, o estilo de linha e a ponta de seta de cada tipo. |
| **Graphviz DOT** | `.dot` | O grafo como um diagrama Graphviz, com os tipos de link coloridos, rotulados e estilizados: linhas sólidas, tracejadas ou pontilhadas (o Graphviz desenha as linhas traço-ponto e traço longo como tracejadas) e a ponta de seta de cada tipo; os tipos não direcionados não têm setas. |
| **Baralho do Anki** | `.apkg` | Os flashcards das notas exportadas. Veja [Anki](review-and-anki.md#anki). |

As exportações são gravadas em um arquivo temporário e movidas para o lugar somente quando completas, então uma
exportação interrompida nunca deixa um arquivo pela metade. Elas rodam em segundo plano, e **Mostrar na pasta** revela o
resultado no Explorador de Arquivos.

Os mapas mentais também têm sua própria exportação (PNG, SVG ou FreeMind `.mm`) na aba **Mapa mental**, e o grafo
pode ser salvo como uma imagem PNG.

## Importar

*Arquivo ▸ Importar…* aceita:

- **Arquivos do ZettelApp** (`.zip`) e exportações **JSON**;
- **Arquivos Markdown** (`.md`) ou um **`.zip` de arquivos Markdown**;
- *Arquivo ▸ Importar pasta Markdown…* para uma pasta de arquivos Markdown, como um **cofre do Obsidian**.

O que é mantido:

- **De arquivos do ZettelApp e JSON:** as notas mantêm seus IDs, links tipados, flashcards, mapas mentais e
  imagens. Os tipos de link que o cofre ainda não tem são adicionados com suas cores e estilos; os que ele tem
  mantêm os seus. Importar o mesmo arquivo duas vezes ignora as notas que não mudaram. Se um ID já está
  em uso por outra nota, a importação recebe um novo ID e os links são atualizados.
- **De Markdown:**
  - o título vem do `title` do front matter, do primeiro `# título` ou do nome do arquivo;
  - as tags vêm de `tags` do front matter e de `#hashtags` em linha;
  - o link de fonte vem de `url` ou `source`, e a data de criação de `created`;
  - `[[links wiki]]` (incluindo os links por nome de arquivo do Obsidian) e `type:: [[links]]` viram links;
  - as imagens referenciadas com `![](path)` ou `![[image.png]]` do Obsidian são copiadas para o cofre;
  - pastas ocultas como `.obsidian` e `.trash` são ignoradas;
  - a própria exportação Markdown do ZettelApp é importada de volta com seus links tipados, flashcards e mapas mentais.

### Segurança

Os arquivos importados são tratados como não confiáveis:

- os caminhos dentro dos arquivos são verificados, então nada pode ser gravado fora da importação (sem "zip-slip");
- arquivos com arquivos demais, dados demais ou taxas de compressão suspeitas ("bombas" de descompressão)
  são recusados;
- cada campo tem o tipo verificado e o tamanho limitado;
- as imagens são reverificadas pelo conteúdo;
- imagens remotas e links para outros lugares do disco não são importados.

Um backup diário é feito quando um cofre é aberto, e você pode fazer um a qualquer momento com *Arquivo ▸ Fazer backup do cofre
agora*. Veja [Privacidade e segurança](privacy-and-security.md).
