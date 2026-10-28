# Servidor MCP

El [Model Context Protocol](https://modelcontextprotocol.io/) (MCP) es un estándar abierto que permite a los asistentes
de IA usar herramientas y datos de otros programas. ZettelApp incluye un servidor MCP, de modo que asistentes como
**Claude Desktop** y **Claude Code** puedan buscar en tu Zettelkasten, leer notas, seguir enlaces con tipo
y pedir sugerencias de enlaces mientras te ayudan.

## Cómo se ejecuta

El servidor es un programa pequeño aparte, **`zettelapp-mcp.exe`**, instalado junto a `ZettelApp.exe`.
Desde el código fuente, el mismo servidor se ejecuta con `python -m zettelapp.mcp_main`. Tu cliente MCP lo inicia cuando
hace falta y se comunica con él por la entrada/salida estándar. **No se abre ningún puerto de red.**

```text
zettelapp-mcp --vault "C:\Users\me\Documents\ZettelApp" [--allow-writes]
```

Sin `--vault`, sirve la bóveda que abriste por última vez en ZettelApp. Los cambios hechos a través de MCP aparecen en
la aplicación en unos pocos segundos.

## El interruptor MCP

Los clientes MCP solo pueden acceder a tus notas mientras **ZettelApp está abierto y el interruptor MCP de su barra de estado está
activado**. El interruptor está **desactivado cada vez que se inicia ZettelApp**, así que decides, en cada sesión, si los asistentes
pueden leer tus notas. Desactívalo, o cierra ZettelApp, y el servidor se detiene en aproximadamente un segundo.
Sin el interruptor, el servidor se niega a iniciarse e indica por qué. Para conocer el comportamiento exacto, consulta la
[referencia de la API de MCP](mcp-reference.md).

## Conectar Claude Desktop

Abre *Herramientas ▸ Opciones ▸ Servidor MCP* y haz clic en **Añadir a Claude Desktop…**. ZettelApp se añade a
`%APPDATA%\Claude\claude_desktop_config.json` (conservando una copia del archivo anterior). Luego reinicia Claude
Desktop. Activa el **interruptor MCP** en la barra de estado de ZettelApp antes de iniciar Claude Desktop; si lo activas
más tarde, vuelve a conectar ZettelApp en Claude Desktop o reinícialo. Para hacerlo a mano, copia el fragmento que se muestra
en esa página en el archivo. Tiene este aspecto:

```json
{
  "mcpServers": {
    "zettelapp": {
      "command": "C:\\Users\\me\\AppData\\Local\\Programs\\ZettelApp\\zettelapp-mcp.exe",
      "args": ["--vault", "C:\\Users\\me\\Documents\\ZettelApp"]
    }
  }
}
```

## Conectar Claude Code

La misma página de Opciones muestra el comando para copiar:

```powershell
claude mcp add zettelapp -- "C:\Users\me\AppData\Local\Programs\ZettelApp\zettelapp-mcp.exe" --vault "C:\Users\me\Documents\ZettelApp"
```

Otros clientes MCP necesitan el mismo comando y los mismos argumentos. Igual que con Claude Desktop, activa primero MCP en ZettelApp
y vuelve a conectar el servidor (en Claude Code, `/mcp`) si lo activas después.

## Herramientas

| Herramienta | Qué hace |
|---|---|
| `search_notes` | Búsqueda de texto completo en títulos, texto y etiquetas (los filtros `tag:name` funcionan). Una consulta vacía lista las notas editadas recientemente. |
| `get_note` | El texto completo de una nota, etiquetas, enlace de la fuente, fechas, enlaces con tipo en ambos sentidos, tarjetas y el esquema del mapa mental. |
| `list_tags` | Todas las etiquetas, con el número de notas que usa cada una. |
| `get_subgraph` | Las notas a 1–4 enlaces de una nota y los enlaces con tipo entre ellas (opcionalmente solo algunos tipos de enlace). |
| `suggest_links` | Notas que probablemente se relacionan con una nota pero aún no están enlazadas, ordenadas por el [sugeridor Naive Bayes](link-suggestions.md). |
| `list_link_types` | Los tipos de enlace de la bóveda, como *apoya a*, *contradice a* y *parte de*. |
| `create_note` | *(escritura)* Crea una nota. `[[Título]]` en el cuerpo enlaza con notas existentes. |
| `add_link` | *(escritura)* Añade un enlace con tipo de una nota a otra. |

## Solo lectura por defecto

El servidor abre tu bóveda en **solo lectura**. Las dos herramientas de escritura se ofrecen únicamente cuando se cumplen **ambas** condiciones:

1. **Permitir que los clientes MCP creen notas y enlaces** está marcado en *Opciones ▸ Servidor MCP*;
2. el servidor se inició con `--allow-writes`. El fragmento de la página de Opciones incluye este indicador en cuanto
   marcas la opción.

El ajuste se comprueba de nuevo en cada escritura, así que desmarcarlo surte efecto de inmediato. Activarlo
requiere que el cliente MCP reinicie el servidor.

El contenido de las notas se pasa al asistente como datos, y el servidor le indica que no los trate
como instrucciones. Las entradas se validan (IDs, tamaños y límites), y el servidor nunca toca archivos
fuera de la bóveda.

## Solución de problemas

- **El cliente dice que el servidor no pudo iniciarse, o las llamadas a herramientas dicen que el interruptor está desactivado.** Abre ZettelApp
  y activa MCP en su barra de estado; luego vuelve a conectar el servidor en tu cliente.
- **El servidor sigue sin iniciarse.** Comprueba que la ruta a `zettelapp-mcp.exe` sea correcta.
  Ejecuta tú mismo el comando en una terminal: informa de qué falla (por ejemplo, «No ZettelApp vault
  found») en el error estándar.
- **Faltan las herramientas de escritura.** Marca la opción *y* añade `--allow-writes`; luego reinicia el cliente.
