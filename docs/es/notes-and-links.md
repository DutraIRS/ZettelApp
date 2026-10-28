# Notas y enlaces

## Escribir notas

Las notas se escriben en **Markdown**: `**negrita**`, `*cursiva*`, `# encabezados`, listas, `> citas`,
`` `código` ``, bloques de código delimitados, tablas y `~~tachado~~`. La barra de herramientas sobre el editor inserta los
más comunes, y Ctrl+B / Ctrl+I funcionan como siempre. Las listas continúan al pulsar Enter.

El editor tiene tres modos (Ctrl+E alterna entre ellos): **Editar**, **Dividir** (texto y vista previa uno junto
al otro) y **Vista previa**.

Por seguridad, el HTML sin procesar de una nota se muestra como texto y nunca se renderiza. Los enlaces de la vista previa solo abren páginas
web (`http`, `https`), correo electrónico (`mailto`), notas, elementos de Zotero y archivos locales (se muestran en el Explorador de archivos,
consulta [Enlaces a archivos locales](#links-to-local-files)). Consulta [Privacidad y seguridad](privacy-and-security.md).

### Seguir enlaces

- **En el editor**, **Ctrl+clic** sigue un `[[enlace a nota]]` (creando la nota si aún no existe),
  un enlace web, de correo o de Zotero, un enlace a un archivo local o una `#etiqueta` (que lista las notas con esa etiqueta).
  Pasa el cursor sobre el texto y un cuadro de ayuda indica qué hará el clic. Un clic normal solo coloca el cursor de texto, así
  que aún puedes editar el texto del enlace.
- **En la vista previa**, un clic normal sigue los enlaces.

### Enlaces a archivos locales

*Insertar ▸ Enlazar a un archivo…* (o el botón de carpeta de la barra de herramientas) te permite elegir un archivo e inserta un enlace
como `[informe.pdf](file:///C:/Users/me/Documents/report.pdf)`. Arrastrar al texto de la nota un archivo que no sea una imagen
hace lo mismo. El archivo se enlaza donde está; no se copia nada a la bóveda.

Al hacer clic en el enlace en la vista previa, o Ctrl+clic en el editor, se abre el **Explorador de archivos con el archivo
seleccionado**. El archivo en sí nunca se abre ni se ejecuta. Solo se permiten rutas de una unidad local: las rutas de red
(UNC) como `\\servidor\recurso\archivo.pdf` se rechazan, porque consultarlas puede enviar tus credenciales de Windows
a ese servidor.

Cada nota tiene:

- un **título** (el campo grande de la parte superior);
- un **ID**, una marca de tiempo como `20261027153012`, que se muestra bajo el título (*Más ▸ Copiar ID de la nota*);
- opcionalmente **etiquetas**, un **enlace de fuente**, una **imagen**, un **mapa mental** y **tarjetas**.

## Enlaces entre notas

### Enlaces wiki

Escribe `[[` y empieza a escribir un título: ZettelApp lo completa a partir de tus notas. Dentro de una nota, todos estos enlazan:

```markdown
Ver [[Curva del olvido]].
Ver [[20261027153012]].              (por ID)
Ver [[Curva del olvido|la curva]].   (texto de enlace personalizado)
```

Ctrl+K (*Insertar ▸ Enlazar a nota…*) abre un selector que busca en títulos y texto y te permite elegir el
tipo de enlace. Un enlace a un título que aún no existe se muestra en gris en la vista previa; haz clic en él para crear
esa nota. Cuando más tarde creas o renombras una nota, se actualizan los enlaces que mencionan su título.

### Enlaces con tipo

Los enlaces pueden decir **cómo** se relacionan dos notas. Pon el tipo de enlace delante del enlace, seguido de `::`:

```markdown
supports:: [[Curva del olvido]]
contradicts:: [[Releer apuntes]]
part_of:: [[Método Zettelkasten]]
```

Los tipos de enlace integrados son:

| Tipo | Nombre | Nombre inverso | Dirigido | Línea | Punta de flecha |
|---|---|---|---|---|---|
| `related` | Relacionada con | Relacionada con | no | continua, gris | ninguna |
| `supports` | Apoya a | Apoyada por | sí | guiones, verde | triángulo relleno |
| `contradicts` | Contradice a | Contradice a | no | punteada, roja | ninguna |
| `extends` | Amplía a | Ampliada por | sí | guion-punto, azul | triángulo relleno |
| `example` | Ejemplo de | Tiene ejemplo | sí | guion-punto-punto, ámbar | círculo |
| `part_of` | Parte de | Contiene | sí | guion largo, morada | rombo |
| `cites` | Cita a | Citada por | sí | continua, turquesa | flecha abierta |

Estos son los estilos de una bóveda nueva; puedes cambiarlos (ver más abajo). Una bóveda creada con una versión anterior
conserva las líneas que tenía.

Un `[[enlace]]` simple es *Relacionada con*.

### Enlaces dirigidos y no dirigidos

Un tipo **dirigido** se lee distinto desde cada lado. Si la nota A *apoya a* la nota B, los retroenlaces de B
muestran A como *Apoyada por*. Los enlaces dirigidos tienen puntas de flecha en el grafo y siguen siendo dirigidos en las exportaciones.
Los tipos **no dirigidos**, como *Relacionada con* y *Contradice a*, se leen igual en ambos sentidos.

Para invertir un enlace dirigido creado al revés, haz clic derecho en él en el panel lateral y elige
**Invertir dirección**. Los enlaces escritos en el texto se invierten editando el texto.

### Enlaces en el panel lateral

El panel lateral enumera los **Enlaces** (salientes) de la nota y sus **Retroenlaces** (entrantes), cada uno con su tipo.

- **Añadir enlace…** crea un enlace sin escribirlo en el texto.
- Haz clic derecho en un enlace para abrir la otra nota, cambiar el tipo de enlace, invertir su dirección o quitarlo.
  Los enlaces escritos en el texto se quitan editando el texto.
- Desde la lista de notas, haz clic derecho en otra nota y elige **Enlace desde la nota abierta como**.

### Tus propios tipos de enlace

Añade, renombra, cambia el estilo o elimina tipos de enlace en *Herramientas ▸ Opciones ▸ Tipos de enlace*. Elige un tipo en la lista y
cámbialo junto a la lista:

- **Nombre** y **Nombre inverso**: cómo se lee el enlace desde su origen y desde su destino. El nombre
  inverso solo lo usan los tipos dirigidos.
- **Dirigido**: si el tipo se lee distinto desde cada lado y tiene punta de flecha.
- **Color**: haz clic en el botón de color para elegir cualquier color.
- **Línea**: continua, guiones, punteada, guion-punto, guion-punto-punto o guion largo.
- **Punta de flecha**: la punta que se dibuja donde llega un enlace dirigido: un triángulo relleno, una flecha abierta, un
  rombo, un círculo o una barra.

La vista previa muestra dos notas unidas por el enlace, con su nombre y cómo se lee desde el otro lado.
El estilo se usa dondequiera que aparezcan enlaces: el grafo, su leyenda, el panel lateral, el selector de enlaces y
las exportaciones a sitio web, GraphML y Graphviz. Da a cada tipo su propia línea además de su propio color, para que
los tipos sigan siendo fáciles de distinguir para personas daltónicas y en papel. Un tipo nuevo empieza con un
color y una línea que pocos otros tipos usan.

En el texto, usa el id del tipo, que se muestra bajo la vista previa (p. ej., un tipo llamado «Inspirada por» se convierte en
`inspired_by::`). El id se fija al crear el tipo, así que renombrar un tipo no rompe los enlaces
escritos en tus notas. Eliminar uno de tus propios tipos convierte sus enlaces en enlaces *Relacionada con*, de modo que
no se pierde nada. Los tipos integrados se pueden renombrar y cambiar de estilo, pero no eliminar.

## Etiquetas

Añade etiquetas en el campo de etiquetas bajo el título (pulsa Enter tras cada una) o escríbelas **en el texto** con una
almohadilla, como `#welcome` o `#math/algebra`. Las etiquetas van en minúsculas y pueden anidarse con una barra, como
`math/algebra`. Filtrar por `math` también encuentra las notas con la etiqueta `math/algebra`.
Usa el filtro de etiquetas sobre la lista de notas o escribe `tag:name` en el cuadro de búsqueda.

Las etiquetas escritas en el texto son etiquetas reales, que se muestran como **pastillas con contorno** junto al cuadro *Añadir etiqueta*. Desaparecen
cuando borras la `#etiqueta` del texto. Una `#etiqueta` se ignora dentro de código, dentro de destinos de enlace
y en `[[#encabezados]]`. Las etiquetas escritas en el cuadro *Añadir etiqueta* son independientes: permanecen hasta que las quitas con
su ✕. Ctrl+clic en una `#etiqueta` del editor para listar las notas que la tienen.

## Enlace de la fuente

El campo con el icono de globo contiene la **fuente** de la nota: una página web (`https://…`), una dirección de correo
o un elemento de Zotero (`zotero://select/library/items/…`). El botón junto a él abre el enlace. Otros tipos de
enlaces se rechazan. Consulta [Zotero](zotero.md) para crear notas directamente desde tu biblioteca de Zotero.

## Imágenes

Inserta imágenes con *Insertar ▸ Imagen…* (Ctrl+Shift+I), **pegándolas** desde el portapapeles o
**arrastrando** archivos de imagen al editor. Formatos admitidos: PNG, JPEG, GIF, WebP y BMP, de hasta 25 MB.
SVG se rechaza a propósito, porque los archivos SVG pueden contener scripts.

Las imágenes se comprueban por su contenido (no por el nombre del archivo), se almacenan una sola vez en la carpeta `assets` de la bóveda
con un nombre derivado de su contenido, y se referencian así:

```markdown
![Diagrama](asset:3f2a9c0b1d4e5f6a7b8c.png)
```

La primera imagen que añades a una nota se convierte en su **imagen del título**. Se muestra como una pequeña miniatura redondeada en
la lista de notas y dentro del círculo de la nota en el grafo. Haz clic derecho en cualquier imagen del editor o de la vista previa
y elige *Usar como imagen del título* para escoger otra, o *Quitar imagen del título* para no tener ninguna.

## Listas de tareas

Empieza una línea con `- [ ]` (o pulsa el botón de lista de tareas de la barra de herramientas) para crear una tarea. `- [x]` es una
tarea completada. En la vista previa, haz clic en la casilla para marcarla; al pulsar Enter al final de una tarea se inicia la
siguiente, y Enter en una tarea vacía termina la lista.

## Alarmas

Pulsa el botón de alarma (o *Insertar ▸ Alarma…*) para fijar una fecha y, opcionalmente, una hora para una nota. Cuando llega el momento, ZettelApp muestra una notificación; haz clic en ella para abrir la nota. ZettelApp tiene que estar en ejecución para avisarte,
y las alarmas que vencieron mientras estaba cerrado suenan poco después de que abras la bóveda. Las notas con alarma muestran una
campana en la lista de notas. Usa *Quitar alarma* en el mismo cuadro de diálogo para borrarla.

## Fórmulas

Escribe LaTeX entre signos de dólar: `$E = mc^2$` es en línea y `$$\int_0^1 x^2\,dx$$` es una fórmula en bloque.
El botón de fórmula (*Insertar ▸ Fórmula…*) abre un cuadro de diálogo con vista previa en vivo. Las fórmulas se dibujan en la
vista previa; las exportaciones conservan el código fuente LaTeX.

## Mapas mentales

Cada nota puede llevar un mapa mental (la pestaña **Mapa mental** o *Insertar ▸ Mapa mental*). Las ramas se colorean
automáticamente.

| Tecla | Acción |
|---|---|
| Tab | Añadir una idea hija |
| Enter | Añadir una idea hermana |
| F2 o doble clic | Renombrar |
| Supr | Eliminar la idea seleccionada |
| Teclas de flecha | Mover la selección |
| Rueda del ratón / arrastrar | Zoom / desplazar |

Haz clic derecho en una idea para **enlazarla con una nota**; una idea enlazada muestra un icono de enlace y abre esa nota.
**Desde enlaces** crea un mapa mental a partir de los enlaces de la nota, agrupados por tipo de enlace, con los
enlaces propios de las notas enlazadas un nivel más abajo. **Exportar** guarda el mapa como imagen PNG o SVG, o como archivo FreeMind
(`.mm`), que FreeMind, Freeplane y XMind pueden abrir.

## Tarjetas

Las tarjetas convierten las notas en material de repaso (consulta [Repaso, cuestionarios y Anki](review-and-anki.md)). Hay
dos formas de crearlas:

**En el texto de la nota.** Estas se convierten en tarjetas automáticamente y se actualizan al editar:

```markdown
Q: ¿Quién describió la curva del olvido?
A: Hermann Ebbinghaus

{{c1::La práctica de recuperación}} también se llama recuperación activa.
```

Una pregunta puede ocupar varias líneas hasta la línea `A:`. Cualquier párrafo con `{{c1::…}}` se convierte en una
tarjeta **cloze**, que oculta cada omisión por turno. `{{c1::texto::pista}}` muestra una pista en lugar de `[…]`.

**En la pestaña Tarjetas.** Usa *Insertar ▸ Tarjeta de estudio…* (Ctrl+Shift+F) para tarjetas que no deban aparecer en
la nota. Las tarjetas del texto se marcan como *del texto de la nota* y se editan en el texto.

## Búsqueda

El cuadro de búsqueda (Ctrl+F) usa búsqueda de texto completo en títulos, texto y etiquetas, ignora los acentos y coincide con
prefijos de palabra, así que `olvid` encuentra *olvidando*. Añade `tag:name` para filtrar por etiqueta, por ejemplo
`memoria tag:psicologia`. Los resultados se ordenan por relevancia; sin consulta, las notas siguen el orden elegido
(*Última edición*, *Creada*, *Título* o *Más enlazadas*).

## Papelera

*Mover a la papelera* (Ctrl+Supr) oculta una nota sin eliminarla. Aparece de inmediato un botón de deshacer, y
el botón **Papelera** bajo la lista de notas muestra las notas eliminadas: haz clic derecho para **Restaurar** o **Eliminar
definitivamente**. **Vaciar papelera** elimina todo lo que contiene tras pedir confirmación. Los enlaces a notas en la papelera se ocultan
y vuelven cuando se restaura la nota.
