# Documentação do ZettelApp

O ZettelApp é um Zettelkasten para Windows: uma rede de notas pequenas, cada uma com uma única ideia, conectadas por
links que dizem *como* as ideias se relacionam. Ele sugere links enquanto você escreve, desenha seu conhecimento como um
grafo 2D ou 3D, transforma notas em flashcards e quizzes e funciona com o Anki, o Zotero e assistentes de IA.

Tudo fica no seu computador, a menos que você peça algo que precise da rede.

## Novo por aqui?

- **[O que é um Zettelkasten?](what-is-zettelkasten.md)**: o método, de onde ele vem e como o
  ZettelApp o apoia.
- **[Tutorial: seus primeiros 30 minutos](tutorial.md)**: um passeio prático, da sua primeira nota ao grafo 3D.

## Conteúdo

- [Primeiros passos](getting-started.md): instalação, seu primeiro cofre e um tour pela janela
- [Notas e links](notes-and-links.md): Markdown, links wiki, links tipados e direcionados, tags, imagens,
  mapas mentais, flashcards, busca e a Lixeira
- [Sugestões de links](link-suggestions.md): como funciona o sugeridor Naive Bayes e como ajustá-lo
- [Grafo e Insights](graph-and-insights.md): grafos 2D e 3D, agrupamento (clustering), grupos e gráficos
- [Revisão, quizzes e Anki](review-and-anki.md): repetição espaçada, modos de quiz, sincronização com o Anki e baralhos
- [Zotero](zotero.md): cite referências e escreva notas de literatura
- [Pergunte às suas notas (IA)](ai-assistant.md): respostas do Claude, OpenAI ou Z.ai, baseadas nas suas notas
- [Servidor MCP](mcp-server.md): deixe o Claude Desktop, o Claude Code e outros clientes MCP lerem seu cofre
- [Referência da API MCP](mcp-reference.md): o protocolo, as ferramentas e os erros, para quem desenvolve clientes MCP
- [Exportar e importar](export-import.md): a coleção inteira ou qualquer subgrafo, em sete formatos
- [Atalhos de teclado](keyboard-shortcuts.md)
- [Privacidade e segurança](privacy-and-security.md): o que sai do seu computador, onde os dados ficam e
  como o ZettelApp os protege
- [Desenvolvimento](development.md): compilar a partir do código-fonte, executar os testes, empacotar uma versão
- [Perguntas frequentes](faq.md)

## As ideias por trás

Um **Zettelkasten** ("caixa de fichas") é um método de anotação tornado famoso pelo sociólogo Niklas Luhmann.
Cada nota é *atômica* (uma ideia, com suas próprias palavras) e tem um ID permanente. O valor vem das
conexões: ao ligar uma nova nota a notas existentes, você é levado a pensar em como as ideias se relacionam,
e depois pode seguir esses links para encontrar combinações inesperadas.

O ZettelApp mantém essa disciplina, mas elimina o atrito:

- **Os IDs são automáticos**: cada nota recebe um ID de data e hora, como `20261027153012`.
- **Os links podem dizer como as notas se relacionam**: *apoia*, *contradiz*, *estende*, *exemplo de*, *parte de*,
  *cita*, ou seus próprios tipos de link.
- **As sugestões revelam conexões que você deixou passar**: um classificador compara uma nota com o resto do seu cofre
  e aprende com os links que você aceita e dispensa.
- **A revisão já vem embutida**: as notas viram flashcards e quizzes, com repetição espaçada ou Anki.
