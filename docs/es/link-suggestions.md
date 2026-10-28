# Sugerencias de enlaces

Mientras escribes, el panel **Enlaces sugeridos** enumera notas que probablemente van con la que estás
editando. Haz clic en **Enlazar** para conectarlas (la flecha junto a él elige el tipo de enlace) o en **✕** para descartar una
sugerencia. Ambas acciones enseñan al modelo. Pasa el cursor sobre una sugerencia para ver *por qué* se propuso.

Las sugerencias se actualizan aproximadamente un segundo después de que dejas de escribir, en segundo plano, así que el editor nunca espera por
ellas. También usan tu texto sin guardar.

## Cómo funciona

ZettelApp trata «¿deberían enlazarse estas dos notas?» como un problema de clasificación y lo responde con un
clasificador **Naive Bayes**. Para una nota *q* y cada nota candidata *c*, calcula ocho características de
similitud y combina la evidencia en una probabilidad.

### Las características

| Característica | Qué mide |
|---|---|
| **Similitud semántica (LSA)** | Similitud del coseno en un espacio semántico latente: una SVD truncada de la matriz TF-IDF (SVD aleatorizada, hasta 64 dimensiones). Las notas que usan vocabulario relacionado quedan cerca aunque compartan pocas palabras exactas. |
| **Palabras clave compartidas (coseno TF-IDF)** | Similitud del coseno de vectores TF-IDF (frecuencia de términos sublineal, frecuencia inversa de documento suavizada). Los títulos cuentan el doble; se incluyen las etiquetas. |
| **Similitud de títulos (Levenshtein)** | 1 − distancia de edición ÷ longitud del título más largo. |
| **Similitud de títulos (Jaro-Winkler)** | Similitud Jaro-Winkler de los títulos, que premia un comienzo compartido. |
| **Similitud de texto (Levenshtein)** | Distancia de edición normalizada entre los primeros 400 caracteres de los dos textos. |
| **Etiquetas compartidas (Jaccard)** | Etiquetas en común ÷ etiquetas en total. |
| **Título mencionado en el texto** | 1 si el título de alguna de las notas aparece como palabras completas en el texto de la otra, si no 0. |
| **Enlaces compartidos (Jaccard)** | Solapamiento entre las notas enlazadas de las dos notas (cierre de triángulos en el grafo). |

El texto se pasa a minúsculas, se pliegan los acentos (así *informação* coincide con *informacao*), se elimina la sintaxis Markdown
y se ignoran las palabras vacías comunes del inglés, el portugués y el español. Las distancias de edición usan
[RapidFuzz](https://github.com/rapidfuzz/RapidFuzz); un algoritmo bit-paralelo en Python puro da
resultados idénticos cuando no está disponible.

### De las características a una probabilidad

Cada valor de característica (entre 0 y 1) se coloca en uno de **8 intervalos**. Para cada característica, el modelo guarda
con qué frecuencia los pares enlazados y los no enlazados caen en cada intervalo, y estima

```text
P(link | f1 … f8)  ∝  P(link) × Π P(fi | link)
```

La **evidencia** de una característica es su razón de verosimilitud logarítmica, log P(intervalo | enlace) − log P(intervalo | sin enlace).
La probabilidad mostrada es la función logística de las log-probabilidades a priori más la suma (ponderada) de la
evidencia.

**De dónde salen los recuentos.** El modelo se entrena con tu bóveda cada vez que cambia de forma apreciable:

- **ejemplos positivos**: cada par de notas enlazadas, más las sugerencias que aceptaste (en bóvedas muy grandes se muestrean hasta 600 pares);
- **ejemplos negativos**: pares aleatorios de notas no enlazadas, tres por cada ejemplo positivo, más cada
  sugerencia que **descartaste**, que cuenta el doble.

**Un a priori para que funcione desde el primer día.** Antes de tener datos, cada intervalo parte de *pseudo-recuentos* de Dirichlet
(10 por característica y clase, por defecto). Codifican una creencia débil: para los pares enlazados los recuentos suben
con la similitud, y para los no enlazados bajan bruscamente. Eso basta para ordenar sugerencias en una bóveda nueva.
A medida que enlazas notas, los recuentos reales pesan más que el a priori y el modelo se adapta a *tu* manera de enlazar.
Como los positivos y los negativos se muestrean de uno a tres, el a priori de clase P(link) es de aproximadamente uno de cada cuatro
(con pseudo-recuentos equivalentes).

**Dos correcciones mantienen honestas las estimaciones:**

1. **Sin fuga de etiquetas.** Los `[[enlaces wiki]]` se eliminan del texto antes de calcular las características.
   De lo contrario, un enlace en línea pondría el título del destino en el texto, y el modelo aprendería a
   reconocer los enlaces existentes en lugar de ideas relacionadas. Por la misma razón, al entrenar con un par
   enlazado, la característica de «enlaces compartidos» ignora el enlace entre las dos notas.
2. **La evidencia correlacionada se pondera.** Naive Bayes asume que las características son independientes, pero algunas
   no lo son: TF-IDF y LSA se solapan, y también las tres distancias de cadenas. Contar la evidencia correlacionada como
   independiente hace que el Naive Bayes simple sea demasiado confiado. Por eso ZettelApp multiplica la
   evidencia de cada característica por **0,6** (Naive Bayes ponderado por característica), lo que mantiene realistas las probabilidades.

**Las características ausentes o desactivadas cuentan como ausencia de evidencia.** Si desactivas una característica o no se puede
calcular, no aporta nada, que es como Naive Bayes maneja de forma natural los valores ausentes.

### Ordenar con rapidez

Comparar textos largos con la distancia de Levenshtein es el paso más lento, así que la ordenación se hace en dos etapas.
Primero se puntúan todos los candidatos sin la característica de similitud de texto, y solo los mejores 150 reciben la
puntuación completa. Los candidatos con los que ya enlazas y los pares que descartaste nunca se sugieren.

## Cómo leer el cuadro «por qué»

Pasa el cursor sobre una sugerencia para ver la estimación del modelo y la evidencia de cada característica. Los números positivos argumentan a favor de un
enlace y los negativos en contra. La etiqueta junto a la barra resume la probabilidad: **fuerte**
(50 % o más), **probable** (25 % o más) o **posible**.

Las probabilidades son estimaciones honestas y, en una bóveda dispersa, la mayoría de los pares realmente no están enlazados, así que un 15–30 %
puede ser una buena sugerencia. Lo que más importa es el orden.

## Ajustes

*Herramientas ▸ Opciones ▸ Sugerencias de enlaces*:

| Opción | Valor predeterminado | Efecto |
|---|---|---|
| Sugerir enlaces mientras escribo | activado | Desactiva por completo las sugerencias del panel. |
| Características | las ocho | Desmarca las características que no quieras que se consideren. |
| Mostrar como máximo | 8 | Número de sugerencias listadas. |
| Coincidencia mínima | 10 % | Oculta las sugerencias por debajo de esta probabilidad. |
| Fuerza del a priori | 10 | Cuántas pseudo-observaciones respaldan el a priori. Valores más altos confían más tiempo en el a priori; valores más bajos se adaptan antes a tus enlaces. |

- **Detalles del modelo…** muestra con cuántos pares enlazados y no enlazados se entrenó el modelo y cuán informativa es
  cada característica (la divergencia de Kullback–Leibler simétrica entre sus distribuciones para pares enlazados y
  no enlazados).
- **Olvidar sugerencias descartadas** borra tus descartes, de modo que esos pares puedan volver a sugerirse y
  dejen de contar como ejemplos negativos.
