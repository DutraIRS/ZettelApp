# Documentación de ZettelApp

ZettelApp es un Zettelkasten para Windows: una red de notas pequeñas, cada una con una sola idea, conectadas por
enlaces que dicen *cómo* se relacionan las ideas. Sugiere enlaces mientras escribes, dibuja tu conocimiento como un
grafo en 2D o 3D, convierte las notas en tarjetas de estudio y cuestionarios, y funciona con Anki, Zotero y asistentes de IA.

Todo permanece en tu equipo, salvo que pidas algo que necesite la red.

## ¿Eres nuevo?

- **[¿Qué es un Zettelkasten?](what-is-zettelkasten.md)**: el método, de dónde viene y cómo lo
  apoya ZettelApp.
- **[Tutorial: tus primeros 30 minutos](tutorial.md)**: un recorrido práctico desde tu primera nota hasta el grafo 3D.

## Contenido

- [Primeros pasos](getting-started.md): instalación, tu primera bóveda y un recorrido por la ventana
- [Notas y enlaces](notes-and-links.md): Markdown, enlaces wiki, enlaces con tipo y dirigidos, etiquetas, imágenes,
  mapas mentales, tarjetas, búsqueda y la papelera
- [Sugerencias de enlaces](link-suggestions.md): cómo funciona el sugeridor Naive Bayes y cómo ajustarlo
- [Grafo y Estadísticas](graph-and-insights.md): grafos 2D y 3D, agrupamiento, agrupación y gráficos
- [Repaso, cuestionarios y Anki](review-and-anki.md): repetición espaciada, modos de cuestionario, sincronización con Anki y mazos
- [Zotero](zotero.md): cita referencias y escribe notas bibliográficas
- [Pregunta a tus notas (IA)](ai-assistant.md): respuestas de Claude, OpenAI o Z.ai, basadas en tus notas
- [Servidor MCP](mcp-server.md): deja que Claude Desktop, Claude Code y otros clientes MCP lean tu bóveda
- [Referencia de la API de MCP](mcp-reference.md): el protocolo, las herramientas y los errores, para quienes desarrollan clientes MCP
- [Exportar e importar](export-import.md): toda la colección o cualquier subgrafo, en siete formatos
- [Atajos de teclado](keyboard-shortcuts.md)
- [Privacidad y seguridad](privacy-and-security.md): qué sale de tu equipo, dónde viven los datos y
  cómo los protege ZettelApp
- [Desarrollo](development.md): compilar desde el código fuente, ejecutar las pruebas, empaquetar una versión
- [Preguntas frecuentes](faq.md)

## Las ideas detrás

Un **Zettelkasten** («caja de fichas») es un método de toma de notas que hizo famoso el sociólogo Niklas Luhmann.
Cada nota es *atómica* (una idea, con tus propias palabras) y tiene un ID permanente. El valor viene de las
conexiones: al enlazar una nota nueva con las existentes, te ves obligado a pensar cómo se relacionan las ideas,
y más tarde puedes seguir esos enlaces para encontrar combinaciones inesperadas.

ZettelApp mantiene esa disciplina pero elimina la fricción:

- **Los IDs son automáticos**: cada nota recibe un ID de marca de tiempo como `20261027153012`.
- **Los enlaces pueden decir cómo se relacionan las notas**: *apoya a*, *contradice a*, *amplía a*, *ejemplo de*, *parte de*,
  *cita a*, o tus propios tipos de enlace.
- **Las sugerencias muestran conexiones que se te pasaron**: un clasificador compara una nota con el resto de tu bóveda
  y aprende de los enlaces que aceptas y descartas.
- **El repaso está integrado**: las notas se convierten en tarjetas y cuestionarios, con repetición espaciada o Anki.
