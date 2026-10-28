# Zotero

ZettelApp se conecta a [Zotero](https://www.zotero.org/), el gestor de referencias gratuito, para que puedas citar
referencias en tus notas y escribir **notas bibliográficas** enlazadas al elemento, y a su PDF, de tu biblioteca.

## Configuración

1. Usa **Zotero 7 o posterior** y mantenlo abierto.
2. En Zotero, abre *Ajustes ▸ Avanzado* y activa **«Permitir que otras aplicaciones de este equipo se
   comuniquen con Zotero»**.
3. En ZettelApp, *Herramientas ▸ Opciones ▸ Zotero ▸ Probar conexión* debería decir *Conectado a Zotero*.

ZettelApp lee tu biblioteca a través de la **API local** de Zotero en este equipo (`127.0.0.1`, puerto 23119 por
defecto). Solo lee: nunca modifica tu biblioteca de Zotero y no viaja nada por internet.
Se busca en tu biblioteca personal (*Mi biblioteca*); las bibliotecas de grupo aún no.

## Citar una referencia

*Insertar ▸ Referencia de Zotero…*, o el botón de libros de la barra de herramientas del editor, abre un cuadro de búsqueda. Escribe parte de
un título, un autor o un año. Con la búsqueda vacía se enumeran tus elementos modificados más recientemente. Selecciona
un elemento para ver sus detalles y luego:

- **Insertar cita** (o doble clic) añade una cita de autor–año que abre el elemento en Zotero:

  ```markdown
  [Ebbinghaus (1885)](zotero://select/library/items/ABCD2345)
  ```

- **Nueva nota bibliográfica** crea una nota para el elemento, con:
  - el título del elemento;
  - una línea de referencia (autores, año, título, publicación, DOI);
  - enlaces a *Abrir en Zotero*, *Abrir PDF* (cuando el elemento tiene un PDF adjunto) y al DOI;
  - el resumen;
  - secciones *Ideas clave* y *Mis ideas* para completar;
  - la etiqueta `literature` más las etiquetas de Zotero del elemento;
  - el elemento de Zotero como **enlace de la fuente** de la nota.

Las notas bibliográficas son el puente clásico del Zettelkasten entre la lectura y tus propias notas permanentes: escribe
las ideas clave con tus propias palabras y luego enlázalas con las notas a las que apoyan, que amplían o contradicen.

## Enlaces de Zotero

Al hacer clic en un enlace de Zotero en una nota se abre Zotero en el elemento, o se abre el PDF en el lector de Zotero. Por seguridad,
ZettelApp solo sigue dos tipos de enlace de Zotero y rechaza cualquier otra dirección `zotero://`:

```text
zotero://select/library/items/<KEY>
zotero://open-pdf/library/items/<KEY>?page=<N>
```

También se aceptan enlaces de bibliotecas de grupo (`zotero://select/groups/<ID>/items/<KEY>`). También puedes pegar un
enlace de Zotero en el campo **Enlace de la fuente** de una nota. En Zotero, haz clic derecho en un elemento y copia su enlace (o usa
un complemento como Zutilo) y luego pégalo.

## Solución de problemas

| Mensaje | Qué hacer |
|---|---|
| *No se pudo conectar con Zotero* | Inicia Zotero 7 o posterior. Comprueba el puerto en *Opciones ▸ Zotero* (predeterminado 23119). |
| *Zotero rechazó la solicitud* | Activa el ajuste *Permitir que otras aplicaciones…* (paso 2 anterior). |
| *Esta versión de Zotero no tiene API local* | Actualiza Zotero a la versión 7 o posterior. |
