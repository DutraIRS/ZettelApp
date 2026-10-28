# Preguntas frecuentes

### ¿Es gratuito ZettelApp?

Sí. Es gratuito y de código abierto, publicado en el dominio público bajo
[The Unlicense](https://github.com/DutraIRS/ZettelApp/blob/main/LICENSE). La función opcional de IA usa
tu propia clave de API, así que el proveedor te factura directamente.

### ¿Cómo puedo apoyar ZettelApp?

¡Gracias por preguntar! Puedes apoyar el desarrollo en [Ko-fi](https://ko-fi.com/dutrairs). Las empresas pueden
patrocinar un punto concreto de la [hoja de ruta](https://github.com/DutraIRS/ZettelApp/blob/main/ROADMAP.md); ponte en
contacto a través de [GitHub](https://github.com/DutraIRS/ZettelApp). Los patrocinadores reciben agradecimientos en las notas de la versión.
Informar de errores, mejorar la documentación y compartir ZettelApp también ayudan.

### ¿Necesita internet?

No. Todo funciona sin conexión. Internet se usa solo para una pequeña comprobación de actualizaciones al iniciar (que puedes
desactivar), cuando haces una pregunta en la página **Preguntar** y cuando abres un enlace. Consulta
[Privacidad y seguridad](privacy-and-security.md).

### ¿Busca ZettelApp actualizaciones?

Sí, una vez al iniciar: una solicitud de un pequeño archivo en el sitio web del proyecto, sin nada sobre ti ni
tus notas. Si existe una versión más nueva, aparece un aviso en la esquina inferior derecha. Desactívalo con
*Herramientas ▸ Opciones ▸ General ▸ Buscar actualizaciones al iniciar ZettelApp*, o con **No buscar actualizaciones**
en el aviso. Consulta [Primeros pasos](getting-started.md#updates).

### ¿Qué es el interruptor MCP de la barra de estado?

Permite que asistentes de IA como Claude Desktop o Claude Code usen tus notas a través de
[MCP](mcp-server.md). Está **desactivado cada vez que se inicia ZettelApp**. Mientras está desactivado, o ZettelApp está cerrado,
los asistentes no pueden acceder a tus notas. Después de activarlo, vuelve a conectar ZettelApp en tu cliente MCP (o
reinicia el cliente).

### ¿Puedo usar un modelo en mi propio equipo?

Sí. En *Herramientas ▸ Opciones ▸ Asistente de IA*, elige **OpenAI** y establece **Punto de acceso** con tu servidor local, por
ejemplo `http://localhost:11434/v1` (Ollama) o `http://localhost:1234/v1` (LM Studio). No se necesita clave de API
para `localhost`. Consulta [Trae tu propio LLM](ai-assistant.md#bring-your-own-llm).

### ¿Dónde están mis notas?

En la carpeta de tu bóveda, por defecto **Documentos\ZettelApp**: una base de datos `zettel.db` y una carpeta `assets`.
*Archivo ▸ Mostrar bóveda en el Explorador de archivos* la abre.

### ¿Puedo usarlo con OneDrive, Dropbox o Google Drive?

Sí. Pon la bóveda en una carpeta sincronizada (*Archivo ▸ Nueva bóveda…*). Cierra ZettelApp en un equipo antes de
abrir la misma bóveda en otro, porque dos equipos escribiendo a la vez pueden provocar conflictos.

### ¿Cómo me paso a otro equipo?

Copia la carpeta de la bóveda, o usa *Archivo ▸ Exportar…* ▸ **Archivo de ZettelApp** e impórtalo en el otro
equipo.

### ¿Puedo usar mi bóveda de Obsidian?

Sí. *Archivo ▸ Importar carpeta de Markdown…* importa archivos Markdown con su front matter, `#etiquetas`,
`[[enlaces]]` e imágenes. Tus archivos de Obsidian no se modifican. En sentido contrario, exporta a **archivos
Markdown** y abre la carpeta en Obsidian.

### ¿Por qué IDs «Zettel» como 20261027153012?

Cada nota recibe un ID permanente a partir del momento en que se creó (año, mes, día, hora, minuto, segundo).
Los títulos pueden cambiar; los IDs no, así que los enlaces por ID nunca se rompen. Rara vez necesitas verlos.

### ¿Cuál es la diferencia entre un enlace en el texto y un enlace en el panel lateral?

Ambos son enlaces reales. Los `[[enlaces]]` del texto forman parte de tu escritura y se eliminan borrándolos
del texto. Los enlaces añadidos con **Añadir enlace…** o aceptando una sugerencia no están en el texto. Puedes
cambiar su tipo, invertir su dirección o quitarlos en el panel lateral.

### ¿Por qué una sugerencia dice solo «18 % · posible»?

El número es la estimación honesta del modelo de que enlazarías las dos notas. En una bóveda joven o dispersa,
la mayoría de los pares de notas no están relacionados, así que incluso las buenas sugerencias empiezan siendo modestas. El orden de las sugerencias
es lo que más importa, y las estimaciones mejoran a medida que enlazas y descartas. Consulta
[Sugerencias de enlaces](link-suggestions.md).

### ¿Funciona en macOS o Linux?

Todavía no. Los paquetes para Linux (.deb, AppImage) y macOS están en la
[hoja de ruta](https://github.com/DutraIRS/ZettelApp/blob/main/ROADMAP.md).

### ¿Está disponible la aplicación en otros idiomas?

Sí. El instalador y la aplicación están traducidos al español, portugués (Brasil), francés, alemán, italiano,
ruso, chino simplificado, japonés, coreano y árabe. La aplicación sigue por defecto el idioma de tu Windows;
cámbialo en *Opciones*. El texto que falte recurre al inglés.

### ¿Cómo desinstalo y qué pasa con mis datos?

*Configuración ▸ Aplicaciones ▸ Aplicaciones instaladas ▸ ZettelApp ▸ Desinstalar*. El desinstalador ofrece una opción sin marcar **Eliminar
también mi configuración y mis datos de ZettelApp** que elimina las preferencias, las claves de API guardadas, los registros, la caché y las
copias de seguridad automáticas, **y todas tus notas** (bases de datos de bóvedas y adjuntos). Sin marcar, tus notas se conservan. En la
versión portable, elimina su carpeta; sus preferencias viven en el registro, en
`HKEY_CURRENT_USER\Software\ZettelApp`, y los registros y copias de seguridad en `%LOCALAPPDATA%\ZettelApp`.

### Algo salió mal. ¿Dónde están los registros?

En `%LOCALAPPDATA%\ZettelApp\Logs`. Incluye la parte relevante cuando
[informes un problema](https://github.com/DutraIRS/ZettelApp/issues). Comprueba antes que no contenga nada privado.
