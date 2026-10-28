# Grafo y Estadísticas

## El grafo

La página **Grafo** (Ctrl+2) dibuja tus notas como una red: cada círculo es una nota, con un tamaño según cuántos enlaces
tiene, y cada línea es un enlace.

![El grafo, coloreado por etiqueta](../website/assets/screenshots/graph-light.png)

### Controles

| Control | Qué hace |
|---|---|
| **Todas las notas / Local** | Muestra toda la colección, o solo la nota abierta y las notas a una distancia de hasta **Profundidad** enlaces (siguiendo los enlaces en ambos sentidos). *Mostrar en el grafo* en el menú ⋯ de una nota abre el grafo local. |
| **2D / 3D** | Cambia entre una disposición plana que se puede arrastrar y una vista 3D que puedes orbitar. |
| **Colorear por** | Etiquetas, *Grupos: k-means*, *Grupos: jerárquico*, o nada. |
| **k** | Número de grupos. *k automático* lo elige por ti (ver más abajo). |
| **Agrupar** | Junta las notas del mismo grupo y sombrea el área de cada grupo. |
| **Etiquetas** | Muestra los títulos de las notas. En grafos grandes, solo se rotulan las notas mejor conectadas hasta que pasas el cursor. |
| **Tipos de enlace** | Oculta o muestra tipos de enlace individuales. |
| **Buscar en el grafo** | Escribe parte de un título y pulsa Enter para saltar a la nota. |

En la parte inferior derecha están el zoom, ajustar, **recalcular disposición**, **guardar como imagen** (PNG) y **exportar estas
notas** (abre el cuadro de [exportación](export-import.md) con las notas que hay en pantalla).

**En 2D**, arrastra una nota para moverla, arrastra el fondo para desplazar y usa la rueda del ratón para hacer zoom. Haz doble clic en
una nota para abrirla; haz clic derecho en ella para ver más opciones (abrir, grafo local, cuestionario sobre las notas vecinas, exportar con
notas enlazadas). La imagen de una nota se muestra dentro de su círculo.

Varios enlaces entre las mismas dos notas se dibujan como **curvas separadas**, cada una con su propia punta de flecha
siguiendo la curva, para que ninguna oculte a otra. Al pasar el cursor o seleccionar una nota se **atenúan los demás enlaces**, se mantienen los enlaces de la propia nota en los
colores de su tipo de enlace y se rotula cada vecina con los tipos de enlace **tal como se leen desde esa nota**, por ejemplo
*Apoya a · Ampliada por*. Funciona igual en 2D y en 3D.

**En 3D**, arrastra para orbitar, usa la rueda para hacer zoom y haz doble clic en una nota para abrirla. **Rotar
automáticamente** hace girar la vista. Las notas más cercanas son más grandes y brillantes, así que la profundidad se lee con facilidad, y cada
grupo aparece como un halo de color suave.

La disposición es dirigida por fuerzas (Fruchterman–Reingold): los enlaces juntan las notas, todas las notas se repelen
entre sí y una gravedad suave mantiene en pantalla los componentes separados. Se ejecuta en segundo plano y se
guarda en caché por vista.

### Colorear por etiqueta

Cada nota toma el color de su **etiqueta más común**, la que usan más notas a la vista, de modo que los
grandes temas de tu bóveda obtienen colores distintos.

### Colorear por grupo

El agrupamiento reúne las notas **por significado**, estén enlazadas o no. Cada nota se convierte en un vector en un
espacio semántico mediante el análisis semántico latente (LSA) de su título, texto y etiquetas. Luego uno de dos métodos
agrupa los vectores:

- **k-means**: algoritmo de Lloyd con inicialización k-means++, la mejor de varias ejecuciones. Es rápido y da
  grupos redondeados y de tamaño parejo.
- **Jerárquico**: agrupamiento aglomerativo con enlace promedio sobre la distancia del coseno, calculado con el
  algoritmo de cadena de vecinos más cercanos (O(n²)). Funciona mejor con temas desiguales y anidados. Las bóvedas de más de
  4000 notas recurren a k-means.

Con **k automático**, ZettelApp prueba k desde 2 hasta aproximadamente √(n/2) + 2 (como máximo 12) y se queda con la k de
mejor **puntuación de silueta**. La puntuación, que se muestra bajo la leyenda, mide lo bien separados que están los grupos:
1 es perfecto y alrededor de 0 significa grupos solapados. Cada grupo recibe el nombre de sus palabras más distintivas,
los términos más frecuentes dentro de él que en el resto de la bóveda.

### Grupos y colores

Con **Agrupar** activado, las notas de la misma etiqueta o grupo se atraen entre sí, y cada grupo obtiene una
región ligeramente sombreada con su nombre. La leyenda enumera los grupos con sus tamaños. Haz clic en uno para
resaltar sus notas.

Los colores de grupos y gráficos provienen de una paleta **validada para deficiencias de visión del color** tanto en modo claro
como oscuro. Los colores se asignan en un orden fijo y nunca se reutilizan: los grupos más allá del octavo comparten un
color gris neutro «Otros». Los **tipos de enlace** usan una segunda pista además del color: cada uno tiene su propia línea
(continua, de guiones, punteada, etc.), y los tipos dirigidos dibujan una punta de flecha como un triángulo o un rombo.
Elígelos en *Herramientas ▸ Opciones ▸ Tipos de enlace* (consulta [Tus propios tipos de enlace](notes-and-links.md#your-own-link-types)).
La leyenda siempre nombra todo, así que nada depende solo del color.

## Estadísticas

La página **Estadísticas** (Ctrl+3) resume tu bóveda:

- **Paneles**: notas (y cuántas hay en la papelera), enlaces (y enlaces por nota), etiquetas, *notas sin enlazar*
  (buenas candidatas para enlazar), tarjetas y tarjetas para hoy.
- **Notas añadidas por mes** durante los últimos 12 meses.
- **Etiquetas principales**, **Enlaces por tipo** y las **Notas más conectadas** (haz clic en una barra para abrir la nota).
- **Temas**: grupos k-means de tus notas con sus palabras clave y tamaños.

Cada gráfico tiene un botón **Mostrar como tabla** (el icono de lista) con los mismos números en una tabla, y las barras
muestran su valor al pasar el cursor.
