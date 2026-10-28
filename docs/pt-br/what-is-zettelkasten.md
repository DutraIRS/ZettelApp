# O que é um Zettelkasten?

Um **Zettelkasten** (do alemão, "caixa de fichas") é uma forma de tomar notas para que elas continuem trabalhando
por você. Você não arquiva as notas por assunto. Escreve cada ideia em uma nota própria e **a liga** às notas com
as quais ela se relaciona. Com o tempo, os links formam uma rede, e segui-los é como você pensa, escreve e descobre
conexões que não havia planejado.

Novo no método? Leia esta página e depois experimente o [tutorial](tutorial.md).

## De onde vem

O método está intimamente associado a **Niklas Luhmann (1927–1998)**, sociólogo alemão mais conhecido por
sua teoria dos sistemas sociais. Ao longo de cerca de quatro décadas, ele manteve uma caixa de fichas com aproximadamente **90.000
fichas de índice**. Duas características a tornavam mais do que um simples fichário:

- **Toda ficha tinha um endereço fixo**, como `21/3d7a`. Uma nova ficha sobre um pensamento existente era arquivada
  logo depois dele, com um endereço ramificado (`21/3d7a` → `21/3d7a1`), de modo que linhas de pensamento podiam crescer em
  qualquer direção sem reorganizar nada.
- **As fichas faziam referência a outras fichas pelo endereço.** Isso transformava a caixa em uma teia de ideias, e não em um
  conjunto de categorias.

Luhmann atribuía à caixa de fichas grande parte de sua enorme produção, cerca de 70 livros e quase 400
artigos (os números variam conforme a contagem). Ele chegou a escrever um ensaio sobre trabalhar com ela como uma espécie de
parceira de conversa, *Kommunikation mit Zettelkästen* (1981). Desde então, sua caixa de fichas foi digitalizada pelo
Arquivo Niklas Luhmann da Universidade de Bielefeld.

O método se tornou amplamente conhecido fora da academia graças a ***How to Take Smart Notes* (2017), de Sönke Ahrens**,
e a comunidades como a zettelkasten.de.

## Os princípios fundamentais

1. **Notas atômicas: uma ideia por nota.** Uma nota deve conter uma única ideia, pequena o bastante para ser ligada com precisão
   e reutilizada em muitos contextos. Se você não consegue resumir uma nota em seu título, ela provavelmente contém mais de uma
   ideia.
2. **Com suas próprias palavras.** Escrever uma ideia com suas próprias palavras é onde a compreensão acontece. Copiar uma
   passagem dá a sensação de produtividade, mas pula o pensar.
3. **Ligue cada nota, com um motivo.** Ao adicionar uma nota, pergunte-se com quais notas existentes ela se relaciona,
   e *como*. Ela apoia uma, contradiz outra, dá um exemplo de uma terceira? Um link com um motivo
   vale muito mais do que uma pilha de notas relacionadas.
4. **IDs únicos e permanentes.** Títulos mudam e assuntos se deslocam, mas o endereço de uma nota não deve mudar, para que os links
   nunca quebrem.
5. **Deixe a estrutura emergir.** Em vez de decidir categorias de antemão com pastas, deixe que grupos de
   ideias se formem a partir dos links que você cria. A estrutura cresce de baixo para cima.
6. **Notas de estrutura (hubs).** Quando um assunto fica grande, escreva uma nota que o mapeie: uma visão geral curta que
   liga às notas principais em uma ordem sensata. É um ponto de entrada, não uma pasta.
7. **Revise e traga de volta.** Revisite as notas, siga seus links e deixe ideias antigas encontrarem as novas. Um
   Zettelkasten só é um parceiro de pensamento se você continuar conversando com ele.

## Três tipos de notas

Ahrens descreve três tipos de notas, cada um com uma vida útil diferente:

| Tipo | O que é | O que fazer com ela |
|---|---|---|
| **Notas passageiras** | Lembretes rápidos de um pensamento, capturados em qualquer lugar. | Processe-as em um ou dois dias e depois descarte-as. |
| **Notas de literatura** | Notas curtas sobre uma fonte, com suas próprias palavras, junto com a referência. | Guarde-as com a fonte (por exemplo, ligadas à entrada dela no Zotero). |
| **Notas permanentes** | Notas autossuficientes com ideias suas, escritas para o seu eu do futuro e ligadas à rede. | Elas são o Zettelkasten. Escreva-as com cuidado e ligue-as. |

## Armadilhas comuns

- **Coletar em vez de pensar.** Salvar artigos e destaques dá a sensação de progresso, mas um
  Zettelkasten só cresce com notas que você escreve e conecta. Essa armadilha costuma ser chamada de "falácia do
  colecionador".
- **Copiar citações.** Uma nota que é principalmente uma citação ainda não foi compreendida. Guarde a citação em uma
  nota de literatura, se precisar, e escreva a nota permanente com suas palavras.
- **Excesso de tags.** Dezenas de tags por nota recriam pastas com outro nome. Poucas tags amplas ajudam
  a encontrar notas; os links carregam o significado.
- **Notas órfãs.** Uma nota sem links é difícil de reencontrar e não acrescenta nada à rede. Ligue
  cada nova nota a pelo menos uma nota existente.
- **Excesso de engenharia.** O método precisa de muito pouco: uma nota, um ID e um link. Comece a escrever; a
  estrutura vem depois.

## Como o ZettelApp apoia o método

| Princípio | No ZettelApp |
|---|---|
| IDs únicos e permanentes | Cada nota recebe automaticamente um ID de data e hora (como `20261027153012`). Ligue por título ou por ID: os [links wiki](notes-and-links.md#wiki-links) continuam funcionando quando os títulos mudam. |
| Notas atômicas | Criação rápida de notas (Ctrl+N), salvamento automático e notas pequenas que ficam bem na pré-visualização. |
| Link com um motivo | [Links tipados](notes-and-links.md#typed-links): `supports:: [[…]]`, *contradiz*, *estende*, *exemplo de*, *parte de*, *cita*, ou os seus. Tipos direcionados se leem naturalmente dos dois lados (*Apoiada por*). |
| Nunca perca uma conexão | Os [links sugeridos](link-suggestions.md) comparam cada nota com seu cofre e aprendem com o que você aceita e dispensa. Os **backlinks** mostram quem liga a uma nota. |
| Deixe a estrutura emergir | O [grafo](graph-and-insights.md): um **grafo local** ao redor de qualquer nota e **clusters** que revelam assuntos que você nunca arquivou. O *Insights* lista as **notas sem links** a corrigir. |
| Notas de estrutura | Mapas mentais dentro das notas, ligados às notas que organizam, e links *parte de*. |
| Notas de literatura | A integração com o [Zotero](zotero.md) cria notas de literatura ligadas ao item e ao seu PDF. |
| Revise e traga de volta | [Flashcards, repetição espaçada e quizzes](review-and-anki.md) criados a partir das suas notas, ou sincronizados com o Anki. |
| Guarde tudo | As notas vão para a **Lixeira**, e não direto para a exclusão, e backups diários mantêm seu histórico seguro. |

Pronto para experimentar? Comece o [tutorial](tutorial.md).
