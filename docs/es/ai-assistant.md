# Pregunta a tus notas (IA)

La página **Preguntar** (Ctrl+5) responde preguntas **a partir de tus notas**, con citas en las que puedes hacer clic. Usa un
proveedor de IA de tu elección con tu propia clave de API. Es totalmente opcional: no se envía nada a ninguna parte hasta que
hagas una pregunta.

![Pregunta a tus notas](../website/assets/screenshots/ask-light.png)

## Configuración

1. Obtén una clave de API de uno de los proveedores compatibles.
2. Abre *Herramientas ▸ Opciones ▸ Asistente de IA*. Elige el **proveedor**, pega la **clave de API** y elige un
   **modelo** (*Actualizar lista* pregunta al proveedor qué modelos puede usar tu clave).

   Puedes guardar varias claves por proveedor (por ejemplo, personal y de trabajo). Usa *Añadir clave…*, *Renombrar* y
   *Eliminar* junto a la lista de claves; la clave seleccionada es la que usa Preguntar.
3. Pulsa **Probar conexión** y luego **Aceptar**.

| Proveedor | Modelo predeterminado | Otros modelos sugeridos | Punto de acceso |
|---|---|---|---|
| **Anthropic Claude** (predeterminado) | `claude-opus-5-5` | `claude-sonnet-5-5`, `claude-haiku-5-5` | `https://api.anthropic.com` |
| **OpenAI** | `gpt-6.1-sol` | `gpt-6-astra`, `gpt-6-luna` | `https://api.openai.com/v1` |
| **Z.ai (GLM)** | `glm-5.3` | `glm-5.3-flash`, `glm-4.7-flash` | `https://api.z.ai/api/paas/v4` |

Puedes escribir cualquier ID de modelo al que tu clave tenga acceso. **Punto de acceso (opcional)** reemplaza la dirección, por
ejemplo para usar un punto de acceso del plan de programación de Z.ai, un proxy compatible con OpenAI o un modelo que se ejecute en tu propio
equipo (`http://localhost:…`). Las direcciones deben usar `https://`; `http://` simple solo se acepta para
`localhost`.

Con Claude también puedes ajustar el **esfuerzo** (de bajo a máximo): un esfuerzo mayor razona más antes de responder y
cuesta más. El valor predeterminado es *medio*.

## Trae tu propio LLM

Preguntar usa **tu propia cuenta** con el proveedor que elijas, así que ese proveedor te factura cualquier uso.
ZettelApp no tiene un servicio de IA propio. Tu clave de API se guarda en el **Administrador de credenciales de Windows**, nunca en
archivos de configuración.

- **Proveedores**: Anthropic Claude, OpenAI y Z.ai (GLM), en *Herramientas ▸ Opciones ▸ Asistente de IA ▸ Proveedor*.
  Elige un **Modelo** de la lista (*Actualizar lista* pregunta al proveedor qué modelos puede usar tu clave) o escribe
  cualquier ID de modelo al que tu clave tenga acceso.
- **Tu propio servidor**: sirve cualquier servicio que ofrezca una API de **chat completions al estilo OpenAI**. Elige
  **OpenAI** y establece **Punto de acceso (opcional)** con su dirección base, por ejemplo
  `https://my-proxy.example.com/v1`, `http://localhost:11434/v1` (Ollama) o `http://localhost:1234/v1`
  (LM Studio). `http://` simple solo se acepta para `localhost`, `127.0.0.1` y `::1`; todo lo demás
  debe usar `https://`. Para esas direcciones locales la **clave de API** puede quedar vacía.
- **Compruébalo**: pulsa **Probar conexión**. Con un modelo local, tu pregunta y tus notas nunca salen de tu
  equipo.
- **Qué se envía**: solo tu pregunta y las notas más relevantes, encontradas en tu equipo. El número de
  notas es el cuadro **cuántas notas** de la página Preguntar (8 por defecto), y la lista *Fuentes enviadas* muestra
  exactamente cuáles se enviaron.

## Haz una pregunta

Escribe una pregunta y pulsa **Preguntar** (Ctrl+Enter). Elige dónde buscar con **Buscar en**: toda la
colección, la nota abierta y sus notas enlazadas, o las notas con una etiqueta. Elige **cuántas notas** enviar.

Qué ocurre:

1. ZettelApp encuentra las notas más relevantes **en tu equipo**, usando la misma similitud TF-IDF y LSA
   que el [sugeridor de enlaces](link-suggestions.md). Con *Nota actual y notas enlazadas*, la nota abierta
   va siempre primero.
2. Tu pregunta y esas notas se envían al proveedor, con un máximo de 120 000 caracteres de notas. Una nota
   recortada para que quepa termina con un marcador visible «[note truncated]». La lista **Fuentes enviadas** muestra exactamente qué
   notas se enviaron.
3. La respuesta llega en flujo a medida que se escribe. Las citas como `[[20261027153012]]` aparecen como enlaces a las
   notas. **Detener** la cancela.

Al modelo se le indica que responda solo a partir de tus notas y que diga cuándo no contienen la respuesta. **Copiar**
copia la respuesta como Markdown. **Guardar como nota** la conserva como una nota nueva con la etiqueta `ai-answer` y enlaces `cites::`
a sus fuentes.

## Privacidad y seguridad

- **Solo se envía lo que preguntas**: tu pregunta y las notas indicadas en *Fuentes enviadas*. Un aviso
  te lo recuerda antes de preguntar (marca *No volver a mostrar* para omitirlo).
- **Tu clave de API** se guarda en el **Administrador de credenciales de Windows** (como `ZettelApp/llm/<provider>`, o `ZettelApp/llm/<provider>/<id de la clave>` para las demás claves), nunca en
  archivos de configuración ni registros, y se elimina de cualquier mensaje de error que se te muestre. *Eliminar* la borra de este equipo.
- **El modelo no tiene herramientas.** No puede buscar en la web, ejecutar código ni modificar tus notas, así que las instrucciones
  ocultas en una nota (o en un archivo importado) no pueden hacer que haga nada. La respuesta se muestra con el mismo
  renderizador seguro que las notas, sin HTML ni scripts.
- Con Claude, ZettelApp usa el SDK oficial de Anthropic y opta por el **respaldo de rechazo en el servidor**: si
  un clasificador de seguridad rechaza una solicitud, Anthropic la reintenta con su modelo de respaldo recomendado.
  Esto se aplica a Claude Opus 5.5, Opus 5, Sonnet 5.5 y Fable 5.1.
- Los términos y las políticas de datos de cada proveedor se aplican a lo que envías.

## Añadir otro proveedor

Los proveedores viven en un pequeño registro (`PROVIDERS` en `zettelapp/core/llm.py`). Un servicio que habla un
protocolo existente (la API Messages de Anthropic o el chat completions al estilo OpenAI, que muchos proveedores
ofrecen) es **una entrada**: su nombre, punto de acceso, modelo predeterminado y la página donde los usuarios obtienen una clave. Un nuevo
protocolo necesita una pequeña clase adaptadora. Consulta [Desarrollo](development.md).
