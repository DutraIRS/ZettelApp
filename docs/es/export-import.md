# Exportar e importar

## Exportar

*Archivo ▸ Exportar…* (Ctrl+Shift+E) exporta **toda la colección o cualquier parte de ella**:

| Alcance | Qué se exporta |
|---|---|
| **Toda la colección** | Todas las notas (excepto la papelera). |
| **Nota actual y notas enlazadas** | La nota abierta y las notas a una distancia de hasta **Profundidad** enlaces, siguiendo los enlaces en ambos sentidos: un *subgrafo*. |
| **Notas con la etiqueta** | Las notas con la etiqueta, incluidas las etiquetas anidadas (`math` incluye `math/algebra`). |

El cuadro de diálogo muestra cuántas notas, enlaces y tarjetas contiene el alcance. También puedes exportar desde la
lista de notas (clic derecho ▸ *Exportar con notas enlazadas…*), desde el menú ⋯ de una nota, desde el grafo (el botón de exportar
exporta las notas en pantalla) y desde el menú de un nodo del grafo.

### Formatos

| Formato | Archivo | Contenido |
|---|---|---|
| **Archivo de ZettelApp** | `.zip` | Todo, incluidas las imágenes: notas, enlaces con tipo, tipos de enlace (con sus colores, estilos de línea y puntas de flecha), tarjetas, mapas mentales. Vuelve a importarlo en ZettelApp en cualquier equipo. Lo mejor para copias de seguridad y para mover bóvedas. |
| **Archivos Markdown** | `.zip` | Un archivo `.md` por nota con front matter YAML (id, título, etiquetas, enlace de la fuente, fechas, enlaces con tipo, mapa mental) y `[[enlaces wiki]]` entre archivos. Los enlaces no escritos en el texto se listan bajo *Links* como `type:: [[Nota]]`, y las tarjetas manuales bajo *Flashcards* como `Q:`/`A:`. Las imágenes están en `assets/`. Se abre en Obsidian y otros editores Markdown. |
| **Sitio web** | `.zip` | Un sitio web estático autónomo: un índice con una vista general del grafo, un índice de etiquetas y una página por nota, con enlaces dibujados con los colores y estilos de línea de sus tipos de enlace, mapas mentales y tarjetas (respuestas reveladas al hacer clic). Sin scripts; funciona sin conexión abriendo `index.html`. Temas claro y oscuro. |
| **JSON** | `.json` | Datos estructurados para scripts y otras herramientas (las imágenes se referencian, no se incluyen). |
| **GraphML** | `.graphml` | El grafo de enlaces para Gephi, yEd, Cytoscape o NetworkX, con títulos, etiquetas y fechas en los nodos y tipos de enlace en las aristas (dirigidas o no), con el color, el estilo de línea y la punta de flecha de cada tipo. |
| **Graphviz DOT** | `.dot` | El grafo como diagrama de Graphviz, con los tipos de enlace coloreados, rotulados y con estilo: líneas continuas, de guiones o punteadas (Graphviz dibuja las líneas guion-punto y guion largo como de guiones) y la punta de flecha de cada tipo; los tipos no dirigidos no tienen flechas. |
| **Mazo de Anki** | `.apkg` | Las tarjetas de las notas exportadas. Consulta [Anki](review-and-anki.md#anki). |

Las exportaciones se escriben en un archivo temporal y solo se mueven a su lugar cuando están completas, así que una
exportación interrumpida nunca deja un archivo a medio escribir. Se ejecutan en segundo plano y **Mostrar en la carpeta** revela el
resultado en el Explorador de archivos.

Los mapas mentales también tienen su propia exportación (PNG, SVG o FreeMind `.mm`) en la pestaña **Mapa mental**, y el grafo
puede guardarse como imagen PNG.

## Importar

*Archivo ▸ Importar…* acepta:

- **archivos de ZettelApp** (`.zip`) y exportaciones **JSON**;
- **archivos Markdown** (`.md`) o un **`.zip` de archivos Markdown**;
- *Archivo ▸ Importar carpeta de Markdown…* para una carpeta de archivos Markdown, como una **bóveda de Obsidian**.

Qué se conserva:

- **De archivos de ZettelApp y JSON:** las notas conservan sus IDs, enlaces con tipo, tarjetas, mapas mentales e
  imágenes. Los tipos de enlace que la bóveda aún no tiene se añaden con sus colores y estilos; los tipos que ya tiene
  conservan los suyos. Importar dos veces el mismo archivo omite las notas que no han cambiado. Si un ID ya lo
  usa una nota distinta, la importación recibe un ID nuevo y se actualizan los enlaces.
- **De Markdown:**
  - el título proviene del `title` del front matter, del primer `# encabezado` o del nombre del archivo;
  - las etiquetas provienen de `tags` del front matter y de los `#hashtags` en línea;
  - el enlace de la fuente proviene de `url` o `source`, y la fecha de creación de `created`;
  - los `[[enlaces wiki]]` (incluidos los enlaces por nombre de archivo de Obsidian) y los `type:: [[enlaces]]` se convierten en enlaces;
  - las imágenes referenciadas con `![](path)` o con `![[image.png]]` de Obsidian se copian a la bóveda;
  - las carpetas ocultas como `.obsidian` y `.trash` se omiten;
  - la propia exportación Markdown de ZettelApp se importa de vuelta con sus enlaces con tipo, tarjetas y mapas mentales.

### Seguridad

Los archivos importados se tratan como no confiables:

- se comprueban las rutas del archivo, de modo que no se puedan escribir archivos fuera de la importación (sin «zip-slip»);
- se rechazan los archivos con demasiados ficheros, demasiados datos o relaciones de compresión sospechosas («bombas» de descompresión);
- cada campo se comprueba por tipo y tiene un tamaño limitado;
- las imágenes se vuelven a verificar por su contenido;
- no se importan las imágenes remotas ni los enlaces a otros lugares del disco.

Se hace una copia de seguridad diaria cuando se abre una bóveda, y puedes hacer una en cualquier momento con *Archivo ▸ Hacer copia de seguridad
ahora*. Consulta [Privacidad y seguridad](privacy-and-security.md).
