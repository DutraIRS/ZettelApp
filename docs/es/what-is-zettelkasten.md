# ¿Qué es un Zettelkasten?

Un **Zettelkasten** (en alemán, «caja de fichas») es una forma de tomar notas para que sigan trabajando a tu favor. No
archivas las notas por tema. Escribes cada idea en su propia nota y **la enlazas** con las notas con las que
se relaciona. Con el tiempo los enlaces forman una red, y seguirlos es cómo piensas, escribes y descubres
conexiones que no habías planeado.

¿Eres nuevo en el método? Lee esta página y luego prueba el [tutorial](tutorial.md).

## De dónde viene

El método se asocia estrechamente con **Niklas Luhmann (1927–1998)**, un sociólogo alemán conocido sobre todo por
su teoría de los sistemas sociales. Durante unas cuatro décadas mantuvo una caja de fichas con aproximadamente **90 000
fichas**. Dos características la hicieron más que un simple fichero:

- **Cada ficha tenía una dirección fija**, como `21/3d7a`. Una ficha nueva sobre un pensamiento existente se archivaba
  justo después de él, con una dirección ramificada (`21/3d7a` → `21/3d7a1`), de modo que las líneas de pensamiento podían crecer en
  cualquier dirección sin reorganizar nada.
- **Las fichas se referían a otras fichas por su dirección.** Eso convirtió la caja en una red de ideas en lugar de un
  conjunto de categorías.

Luhmann atribuyó a la caja de fichas buena parte de su enorme producción, unos 70 libros y cerca de 400
artículos (las cifras varían según el recuento). Incluso escribió un ensayo sobre trabajar con ella como una especie de
interlocutor, *Kommunikation mit Zettelkästen* (1981). Desde entonces su caja de fichas ha sido digitalizada por
el Archivo Niklas Luhmann de la Universidad de Bielefeld.

El método se hizo ampliamente conocido fuera del ámbito académico gracias a **_How to Take Smart Notes_ (2017), de Sönke Ahrens**,
y a comunidades como zettelkasten.de.

## Los principios básicos

1. **Notas atómicas: una idea por nota.** Una nota debe contener una sola idea, lo bastante pequeña para enlazarla con precisión
   y reutilizarla en muchos contextos. Si no puedes resumir una nota en su título, probablemente contiene más de una
   idea.
2. **Con tus propias palabras.** Escribir una idea con tus propias palabras es donde ocurre la comprensión. Copiar un
   pasaje parece productivo, pero se salta el pensamiento.
3. **Enlaza cada nota, con un motivo.** Al añadir una nota, pregúntate con qué notas existentes se relaciona
   y *cómo*. ¿Apoya a una, contradice a otra, da un ejemplo de una tercera? Un enlace con motivo
   vale mucho más que un montón de notas relacionadas.
4. **IDs únicos y permanentes.** Los títulos cambian y los temas se desplazan, pero la dirección de una nota no debería hacerlo, para que los enlaces
   nunca se rompan.
5. **Deja que la estructura surja.** En lugar de decidir categorías de antemano con carpetas, deja que los grupos de
   ideas se formen a partir de los enlaces que haces. La estructura crece de abajo arriba.
6. **Notas de estructura (hub).** Cuando un tema se hace grande, escribe una nota que lo mapee: una breve visión general que
   enlaza con las notas clave en un orden razonable. Es un punto de entrada, no una carpeta.
7. **Repasa y haz resurgir.** Vuelve a tus notas, sigue sus enlaces y deja que las ideas antiguas se encuentren con las nuevas. Un
   Zettelkasten es un compañero de pensamiento solo si sigues conversando con él.

## Tres tipos de notas

Ahrens describe tres tipos de notas, cada uno con una vida útil distinta:

| Tipo | Qué es | Qué hacer con ella |
|---|---|---|
| **Notas efímeras** | Recordatorios rápidos de un pensamiento, capturados en cualquier parte. | Procésalas en un día o dos y luego tíralas. |
| **Notas bibliográficas** | Notas breves sobre una fuente, con tus propias palabras y la referencia. | Guárdalas junto a la fuente (por ejemplo, enlazadas a su entrada de Zotero). |
| **Notas permanentes** | Notas autocontenidas con tus propias ideas, escritas para tu yo futuro y enlazadas a la red. | Estas son el Zettelkasten. Escríbelas con cuidado y enlázalas. |

## Errores comunes

- **Coleccionar en lugar de pensar.** Guardar artículos y subrayados parece avanzar, pero un
  Zettelkasten crece solo con las notas que escribes y conectas. Esta trampa suele llamarse la «falacia
  del coleccionista».
- **Copiar citas.** Una nota que es sobre todo una cita aún no ha sido comprendida. Guarda la cita en una
  nota bibliográfica si la necesitas y escribe la nota permanente con tus palabras.
- **Etiquetar en exceso.** Docenas de etiquetas por nota recrean las carpetas con otro nombre. Unas pocas etiquetas amplias te ayudan
  a encontrar notas; los enlaces llevan el significado.
- **Notas huérfanas.** Una nota sin enlaces es difícil de volver a encontrar y no aporta nada a la red. Enlaza
  cada nota nueva con al menos una nota existente.
- **Sobrecomplicar.** El método necesita muy poco: una nota, un ID y un enlace. Empieza a escribir; la
  estructura llegará después.

## Cómo apoya ZettelApp el método

| Principio | En ZettelApp |
|---|---|
| IDs únicos y permanentes | Cada nota recibe automáticamente un ID de marca de tiempo (como `20261027153012`). Enlaza por título o por ID: los [enlaces wiki](notes-and-links.md#wiki-links) siguen funcionando cuando cambian los títulos. |
| Notas atómicas | Creación rápida de notas (Ctrl+N), guardado automático y notas pequeñas que se previsualizan bien. |
| Enlaces con motivo | [Enlaces con tipo](notes-and-links.md#typed-links): `supports:: [[…]]`, *contradice a*, *amplía a*, *ejemplo de*, *parte de*, *cita a*, o los tuyos. Los tipos dirigidos se leen con naturalidad desde ambos lados (*Apoyada por*). |
| No perder ninguna conexión | Los [enlaces sugeridos](link-suggestions.md) comparan cada nota con tu bóveda y aprenden de lo que aceptas y descartas. Los **retroenlaces** muestran quién enlaza con una nota. |
| Dejar que la estructura surja | El [grafo](graph-and-insights.md): un **grafo local** alrededor de cualquier nota y **grupos** que revelan temas que nunca archivaste. *Estadísticas* enumera las **notas sin enlazar** que conviene arreglar. |
| Notas de estructura | Mapas mentales dentro de las notas, enlazados a las notas que organizan, y enlaces *parte de*. |
| Notas bibliográficas | La integración con [Zotero](zotero.md) crea notas bibliográficas enlazadas al elemento y a su PDF. |
| Repasar y hacer resurgir | [Tarjetas, repetición espaciada y cuestionarios](review-and-anki.md) creados a partir de tus notas o sincronizados con Anki. |
| Conservarlo todo | Las notas van a la **papelera**, no se eliminan directamente, y las copias de seguridad diarias protegen tu historial. |

¿Listo para probarlo? Empieza el [tutorial](tutorial.md).
