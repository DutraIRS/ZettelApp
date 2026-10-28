# Privacidad y seguridad

## Qué sale de tu equipo

**Nada, salvo que lo pidas, aparte de una pequeña comprobación de actualizaciones.** ZettelApp no tiene cuentas,
telemetría ni anuncios, y no carga nada de internet mientras trabajas. Estas son todas las solicitudes de red
que puede hacer:

| Cuando… | ZettelApp contacta con | Qué se envía |
|---|---|---|
| Unos 4 segundos después de iniciar ZettelApp (se puede desactivar) | `https://dutrairs.github.io/ZettelApp/version.json` | Una solicitud HTTPS de ese archivo, con la cabecera `User-Agent: ZettelApp/<version>`. Nada más: ni notas, ni ajustes, ni identificadores. Cualquier fallo es silencioso. Consulta [Actualizaciones](getting-started.md#updates). |
| Haces una pregunta en la página **Preguntar** | El proveedor de IA que configuraste (Anthropic, OpenAI, Z.ai o tu propio punto de acceso) | Tu pregunta y las notas indicadas en *Fuentes enviadas* |
| Pruebas la conexión de IA o actualizas la lista de modelos | El mismo proveedor | Tu clave de API, para autenticarte |
| **Sincronizas con Anki** | AnkiConnect en **este equipo** (`127.0.0.1`) | Las tarjetas del alcance elegido |
| Usas **Insertar ▸ Referencia de Zotero** o *Probar conexión* en las opciones de Zotero | Zotero en **este equipo** (`127.0.0.1`) | Tus palabras de búsqueda (solo lectura) |
| Haces clic en un enlace web, o usas *Ayuda ▸ Sitio web de ZettelApp / Documentación / Buscar actualizaciones*, o el botón **Descargar** del aviso de actualización | Tu navegador web abre la página | Nada de ZettelApp |

Para detener la comprobación de actualizaciones, desmarca *Herramientas ▸ Opciones ▸ General ▸ Buscar actualizaciones al iniciar ZettelApp*;
ZettelApp no hará entonces ninguna solicitud hasta que hagas una pregunta o uses alguna de las otras funciones anteriores.

Las conexiones locales con Anki y Zotero nunca usan un proxy, así que no se pueden redirigir fuera de tu equipo.
El servidor MCP no hace ninguna solicitud de red.

## Dónde viven tus datos

| Qué | Dónde |
|---|---|
| Notas, enlaces, tarjetas, historial de repaso | La carpeta de tu bóveda: `zettel.db` (SQLite). Por defecto **Documentos\ZettelApp**. |
| Imágenes | La carpeta `assets` de la bóveda. |
| Preferencias | El registro, en `HKEY_CURRENT_USER\Software\ZettelApp\ZettelApp`. |
| Claves de API | **Administrador de credenciales de Windows** (`ZettelApp/llm/…`), nunca en archivos ni en el registro. |
| Registros | `%LOCALAPPDATA%\ZettelApp\Logs` (rotados, como máximo unos pocos MB). Registran errores, no tus notas, y nunca incluyen claves de API. |
| Copias de seguridad automáticas | `%LOCALAPPDATA%\ZettelApp\Backups` |
| Pequeña caché de la interfaz | `%LOCALAPPDATA%\ZettelApp\Cache` |

La bóveda es una carpeta normal: puedes copiarla, respaldarla o mantenerla en OneDrive. ZettelApp escribe la
base de datos con sincronización completa, un ajuste elegido para adaptarse a carpetas sincronizadas. Evita abrir la misma bóveda en dos
equipos al mismo tiempo.

## Copias de seguridad y deshacer

- **Copias de seguridad diarias:** la primera vez que se abre una bóveda cada día, se guarda una copia consistente de su base de datos.
  Se conservan las 10 más recientes (*Opciones ▸ Copias de seguridad*). *Archivo ▸ Hacer copia de seguridad ahora* hace una en cualquier momento.
  Las imágenes se almacenan por contenido y nunca se eliminan automáticamente.
- **Papelera:** las notas eliminadas van primero a la papelera y se pueden restaurar hasta que la vacíes.
- **Guardado automático:** las notas se guardan mientras escribes. Un cuadro de diálogo de fallo informa de errores inesperados y escribe los detalles en el
  registro.

## Cómo te protege ZettelApp

Las notas pueden venir de importaciones, de la web o de respuestas de IA, así que ZettelApp trata su contenido como no confiable:

- **Sin contenido activo.** El HTML sin procesar de las notas se muestra como texto, nunca se renderiza; nada en una nota puede ejecutar
  scripts. La vista previa de la nota carga imágenes **solo de la carpeta `assets` de la propia bóveda**, nunca de la
  web ni de otro lugar del disco.
- **Lista de enlaces permitidos.** Al hacer clic en un enlace solo se abren páginas web (`http`/`https`), correo (`mailto`), notas,
  enlaces de Zotero *seleccionar elemento* / *abrir PDF* y enlaces a archivos locales (más abajo). `javascript:` y otros
  esquemas se rechazan.
- **Los enlaces a archivos locales solo muestran el archivo.** Un enlace `file:///` abre el **Explorador de archivos con el archivo
  seleccionado**; el archivo en sí nunca se abre ni se ejecuta. Solo se permiten rutas de una unidad local. Las rutas de red
  (UNC) como `\\servidor\recurso` se rechazan, porque consultar una puede enviar tus credenciales de Windows
  a ese servidor.
- **Las imágenes se verifican por contenido**, no por nombre de archivo. Solo se aceptan PNG, JPEG, GIF, WebP y BMP de hasta 25 MB;
  SVG se rechaza porque puede contener scripts. La verificación abarca la firma del archivo y el
  tamaño comprimido; las dimensiones en píxeles se comprueban cuando la imagen se muestra por primera vez.
- **Importaciones seguras.** Los archivos se comprueban para detectar trucos de rutas («zip-slip») y bombas de descompresión. Cada campo
  se valida y tiene un tamaño limitado, las importaciones de Markdown no pueden salir de la carpeta importada y una
  importación fallida deja la bóveda sin cambios: las importaciones se ejecutan en una única transacción de base de datos que se revierte ante
  cualquier error.
- **Exportaciones seguras.** Los sitios web exportados no contienen scripts y llevan una Content-Security-Policy estricta. Los archivos
  se escriben de forma atómica.
- **Seguridad de la base de datos.** Todas las consultas a la base de datos usan parámetros enlazados, y el texto de búsqueda nunca se interpreta como
  sintaxis de consulta.
- **Los enlaces `zettelapp://`** (usados por las tarjetas de Anki) solo pueden *abrir una nota por su ID*. Cualquier otra solicitud se
  ignora.
- **Una sola instancia por usuario.** Un segundo inicio entrega su solicitud a la aplicación en ejecución mediante una
  canalización con nombre de Windows a la que solo puede acceder tu cuenta de usuario.
- **Seguridad de la IA.** El modelo de IA no recibe herramientas, así que las instrucciones ocultas en una nota no pueden hacerlo actuar, y su
  respuesta se renderiza con el mismo renderizador seguro. Las claves de API permanecen en el Administrador de credenciales y se eliminan de los
  mensajes de error.
- **Servidor MCP y su interruptor.** Los clientes MCP solo pueden acceder a tus notas mientras ZettelApp está abierto **y** el
  interruptor MCP de su barra de estado está activado. El interruptor está desactivado cada vez que se inicia ZettelApp y nunca se guarda.
  El servidor es de solo lectura por defecto, se ejecuta solo cuando tu cliente MCP lo inicia y usa la entrada/salida
  estándar sin puerto de red. Consulta [Servidor MCP](mcp-server.md).

## Desinstalación

Desinstala desde *Configuración de Windows ▸ Aplicaciones ▸ Aplicaciones instaladas ▸ ZettelApp ▸ Desinstalar*. El desinstalador ofrece
una opción sin marcar, **Eliminar también mi configuración y mis datos de ZettelApp**. Si la marcas, elimina tu
configuración, las claves de API guardadas en el Administrador de credenciales, los registros, la caché y las copias de seguridad automáticas
(`%LOCALAPPDATA%\ZettelApp`) **y todas tus notas** (la base de datos y los adjuntos de tus bóvedas). Sin marcar,
tus notas se quedan donde están.

¿Encontraste un problema de seguridad? Infórmalo de forma privada; consulta
[SECURITY.md](https://github.com/DutraIRS/ZettelApp/blob/main/SECURITY.md).
