# Primeros pasos

## Instalación

ZettelApp funciona en **Windows 10 (21H2 o posterior) y Windows 11, de 64 bits**. Descárgalo desde la
[última versión](https://github.com/DutraIRS/ZettelApp/releases/latest):

| Descarga | Úsala cuando |
|---|---|
| `ZettelApp-Setup.exe` | Quieras una instalación normal con una entrada en el menú Inicio, un desinstalador en *Configuración ▸ Aplicaciones* y enlaces `zettelapp://` que abren notas desde Anki. No se necesitan derechos de administrador: se instala solo para tu cuenta. |
| `ZettelApp-Portable.zip` | No puedas instalar software o quieras ejecutarlo desde una unidad USB. Descomprímelo donde quieras y ejecuta `ZettelApp.exe`. |

El instalador pregunta qué idioma usar y sugiere el idioma de visualización de Windows. El instalador
y la aplicación están traducidos a 11 idiomas; cambia el idioma de la aplicación en *Opciones*.

Cada versión incluye sumas de comprobación SHA-256 (`SHA256SUMS.txt`). Para comprobar una descarga en PowerShell:

```powershell
Get-FileHash .\ZettelApp-Setup.exe -Algorithm SHA256
```

### «Windows protegió su PC»

Las compilaciones aún no están firmadas digitalmente, por lo que Microsoft Defender SmartScreen puede mostrar una advertencia la primera vez que ejecutes el
instalador. Si lo descargaste de la página oficial de versiones y la suma de comprobación coincide, elige
**Más información ▸ Ejecutar de todas formas**. La firma de código está en la [hoja de ruta](https://github.com/DutraIRS/ZettelApp/blob/main/ROADMAP.md).

## Tu primera bóveda

Una **bóveda** es una carpeta que contiene tus notas: un archivo de base de datos (`zettel.db`) y una carpeta `assets` para imágenes.
Al iniciar por primera vez, ZettelApp crea una en **Documentos\ZettelApp** con once notas de ejemplo enlazadas. La nota
*Te damos la bienvenida a ZettelApp* guía por los enlaces, las etiquetas, las imágenes, los mapas mentales, las tarjetas y el resto de la aplicación. Una
aventura opcional de diez minutos ofrece el mismo recorrido mediante acciones reales. Las bóvedas nuevas creadas con
*Archivo ▸ Nueva bóveda…* o *Archivo ▸ Abrir bóveda…* reciben el mismo material de ejemplo, así que puedes trabajar en otro lugar,
por ejemplo en una carpeta de OneDrive.
*Archivo ▸ Abrir reciente* muestra las bóvedas que usaste por última vez.

Las notas se guardan automáticamente mientras escribes. No hay botón Guardar.

## Un recorrido por la ventana

![La página Notas](../website/assets/screenshots/notes-light.png)

La **barra de navegación** de la izquierda cambia entre páginas (Ctrl+1 a Ctrl+5):

- **Notas**: la lista de notas, el editor y un panel lateral.
  - La *lista* tiene búsqueda (los filtros `tag:name` también funcionan), un filtro de etiquetas, ordenación y la papelera.
  - El *editor* tiene el título, las etiquetas, un enlace de fuente opcional y pestañas para la **Nota** (Markdown, con
    los modos Editar, Dividir y Vista previa), su **Mapa mental** y sus **Tarjetas**.
  - El *panel lateral* muestra los **Enlaces sugeridos**, los **Enlaces** de la nota y sus **Retroenlaces**.
- **Grafo**: tus notas como una red en 2D o 3D, coloreadas por etiqueta o por grupo temático.
- **Estadísticas**: estadísticas y gráficos de tu bóveda.
- **Repaso**: repasos de repetición espaciada, cuestionarios y Anki.
- **Preguntar**: haz preguntas sobre tus notas con un proveedor de IA de tu elección (opcional).

**Opciones** (al final de la barra, o *Herramientas ▸ Opciones…*, Ctrl+,) contiene las preferencias: tema, tamaño del texto del editor,
sugerencias de enlaces, tipos de enlace, IA, servidor MCP, Anki, Zotero, integración con Windows y copias de seguridad.

La aplicación sigue tu configuración **claro/oscuro** y el **color de énfasis** de Windows. Puedes forzar un tema en
*Ver ▸ Tema*.

## Actualizaciones

Unos cuatro segundos después de iniciarse, ZettelApp hace una única solicitud HTTPS a
`https://dutrairs.github.io/ZettelApp/version.json` para conocer la versión más reciente. No envía nada más
(solo un user-agent `ZettelApp/<version>`), y si la solicitud falla no verás nada. Cuando existe una versión
más nueva, aparece un pequeño aviso en la esquina inferior derecha, como máximo una vez por versión. Nunca
toma el foco. **Descargar** abre la página de versiones en tu navegador, **✕** cierra el aviso y
**No buscar actualizaciones** desactiva la comprobación. Puedes volver a activarla en
*Herramientas ▸ Opciones ▸ General ▸ Buscar actualizaciones al iniciar ZettelApp*. ZettelApp nunca instala
nada por sí mismo.

## Desinstalación

Usa *Configuración de Windows ▸ Aplicaciones ▸ Aplicaciones instaladas ▸ ZettelApp ▸ Desinstalar*. Tras confirmar, un cuadro de diálogo ofrece
una opción sin marcar **Eliminar también mi configuración y mis datos de ZettelApp**. Elimina tu configuración, las claves de API guardadas,
los registros, la caché y las copias de seguridad automáticas (`%LOCALAPPDATA%\ZettelApp`) **y todas tus notas** (la base de datos
y los adjuntos de tus bóvedas). Déjala sin marcar para conservar tus notas. En la versión portable, elimina su carpeta.

## Siguientes pasos

- Aprende la sintaxis de las notas en [Notas y enlaces](notes-and-links.md).
- Lee cómo funcionan las [sugerencias de enlaces](link-suggestions.md).
- Pulsa **F1** en cualquier momento para abrir esta documentación o consulta los [atajos de teclado](keyboard-shortcuts.md).
