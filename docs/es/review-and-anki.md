# Repaso, cuestionarios y Anki

Las notas están hechas para pensar con ellas, y recordarlas ayuda. ZettelApp convierte las notas en
[tarjetas](notes-and-links.md#flashcards) y te permite repasarlas dentro de la aplicación o en Anki.

## Repetición espaciada

La página **Repaso** (Ctrl+4) muestra cuántas tarjetas están **para hoy**. **Empezar repaso** las recorre:

1. Lee la pregunta e intenta recordar la respuesta.
2. Pulsa **Espacio** (o *Mostrar respuesta*).
3. Califícate: **Otra vez (1)**, **Difícil (2)**, **Bien (3)** o **Fácil (4)**. Pasa el cursor sobre un botón para ver cuándo
   volvería la tarjeta.

La programación usa el algoritmo **SM-2** (el algoritmo de SuperMemo del que nació Anki):

- Las tarjetas nuevas vuelven después de 1 día, luego 6 días y después a intervalos que crecen según el *factor de facilidad* de la tarjeta
  (2,5 al principio).
- *Otra vez* reinicia la tarjeta a 1 día y baja su facilidad. *Difícil* acorta el siguiente intervalo y *Fácil*
  lo alarga.

Las tarjetas cloze generan un repaso por omisión (`{{c1::…}}`, `{{c2::…}}`, …). Cada pregunta muestra un
enlace **De:** a su nota.

## Cuestionarios

**Cuestionario de práctica** crea un cuestionario a partir de un alcance: toda la colección, la nota abierta y sus notas enlazadas
(con una profundidad) o las notas con una etiqueta. Elige un estilo y el número de preguntas:

| Estilo | Cómo funciona |
|---|---|
| **Tarjetas (repetición espaciada)** | Como un repaso, y tus calificaciones actualizan el calendario. |
| **Opción múltiple** | Elige la respuesta correcta entre cuatro. Las respuestas incorrectas son respuestas de otras tarjetas de longitud similar, así que son plausibles. Las teclas 1–4 eligen. |
| **Escribe la respuesta** | Escribe la respuesta y pulsa Enter. Se califica por similitud de edición (Levenshtein), ignorando mayúsculas, acentos y formato: un 85 % o más cuenta como correcta y un 60 % o más como *casi*, así que los pequeños errores tipográficos no te penalizan. |
| **Adivina la nota** | Muestra el texto de una nota con las palabras de su título en blanco; elige el título correcto. Las opciones incorrectas son las **notas más similares** (por TF-IDF), así que aprendes a distinguir ideas relacionadas. No se necesitan tarjetas. |

*Herramientas ▸ Cuestionario sobre las notas vecinas* inicia un cuestionario sobre la nota abierta y las notas a dos enlaces
de ella. Haz clic derecho en una nota del grafo para lo mismo.

## Anki

ZettelApp funciona con [Anki](https://apps.ankiweb.net/) de dos maneras. Ambas usan dos tipos de nota, **ZettelApp
Basic** y **ZettelApp Cloze**, con estos campos:

- *Front* y *Back* (o *Text* y *Extra* para las tarjetas cloze), generados a partir de Markdown;
- *Source*, un enlace de vuelta a la nota;
- *ZettelID* y *CardKey*.

Las etiquetas de tu nota se convierten en etiquetas de Anki (las etiquetas anidadas pasan a `parent::child`), más `zettelapp`. Las imágenes de las tarjetas
se incluyen como medios.

### Sincronizar con AnkiConnect

1. En Anki, instala el complemento **AnkiConnect** (*Tools ▸ Add-ons ▸ Get Add-ons…*, código **2055492159**)
   y reinicia Anki.
2. Con Anki abierto, abre **Repaso** en ZettelApp, elige el nombre del mazo (**Mazo predeterminado** en
   *Opciones ▸ Anki*, `ZettelApp` al principio) y el alcance, y pulsa
   **Sincronizar con Anki** (o *Herramientas ▸ Sincronizar con Anki*). *Comprobar conexión* prueba el enlace.

ZettelApp recuerda qué nota de Anki corresponde a cada tarjeta. Sincronizar de nuevo **actualiza** las tarjetas en lugar de
añadir duplicados, y una tarjeta puede volver a encontrarse por su *CardKey* aunque se haya perdido esa memoria. Las tarjetas
que eliminas en ZettelApp no se eliminan de Anki.

ZettelApp solo se comunica con AnkiConnect en este equipo (`127.0.0.1`, puerto 8765 por defecto, modificable en
*Opciones ▸ Anki*).

### Exportar un mazo (.apkg)

**Exportar mazo (.apkg)…** (o *Archivo ▸ Exportar…* con el formato *Mazo de Anki*) escribe un paquete que
importas con *File ▸ Import* en Anki. No se necesita ningún complemento. Los tipos de nota, el mazo y la identidad de cada tarjeta son
estables, así que importar una exportación más reciente **actualiza** las tarjetas que importaste antes.

### De Anki de vuelta a tus notas

El **Source** de cada tarjeta es un enlace `zettelapp://note/<id>`. Haz clic en él en Anki y la nota se abre en
ZettelApp. El instalador lo configura. Con la versión portable, usa *Opciones ▸ Integración con Windows ▸
Registrar enlaces*. El gestor de enlaces solo acepta enlaces de *abrir nota*; consulta
[Privacidad y seguridad](privacy-and-security.md).
