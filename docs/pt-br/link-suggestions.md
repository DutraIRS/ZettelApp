# Sugestões de links

Enquanto você escreve, o painel **Links sugeridos** lista as notas que provavelmente combinam com a que você está
editando. Clique em **Link** para conectá-las (a seta ao lado dele escolhe o tipo de link) ou em **✕** para dispensar uma
sugestão. As duas ações ensinam o modelo. Passe o mouse sobre uma sugestão para ver *por que* ela foi sugerida.

As sugestões são atualizadas cerca de um segundo depois que você para de digitar, em segundo plano, de modo que o editor nunca espera
por elas. Elas usam também o seu texto ainda não salvo.

## Como funciona

O ZettelApp trata "essas duas notas deveriam ser ligadas?" como um problema de classificação e o responde com um classificador
**Naive Bayes**. Para uma nota *q* e cada nota candidata *c*, ele calcula oito características de similaridade
e combina as evidências em uma probabilidade.

### As características

| Característica | O que mede |
|---|---|
| **Similaridade semântica (LSA)** | Similaridade de cosseno em um espaço semântico latente: uma SVD truncada da matriz TF-IDF (SVD randomizada, até 64 dimensões). Notas que usam vocabulário relacionado ficam próximas mesmo quando compartilham poucas palavras exatas. |
| **Palavras-chave compartilhadas (cosseno TF-IDF)** | Similaridade de cosseno de vetores TF-IDF (frequência de termo sublinear, frequência inversa de documento suavizada). Os títulos contam em dobro; as tags são incluídas. |
| **Similaridade de título (Levenshtein)** | 1 − distância de edição ÷ comprimento do título mais longo. |
| **Similaridade de título (Jaro-Winkler)** | Similaridade Jaro-Winkler dos títulos, que recompensa um início em comum. |
| **Similaridade de texto (Levenshtein)** | Distância de edição normalizada entre os primeiros 400 caracteres dos dois textos. |
| **Tags compartilhadas (Jaccard)** | Tags em comum ÷ total de tags. |
| **Título mencionado no texto** | 1 se o título de uma das notas aparece como palavras inteiras no texto da outra, senão 0. |
| **Links compartilhados (Jaccard)** | Sobreposição entre as notas ligadas às duas notas (fechando triângulos no grafo). |

O texto é convertido para minúsculas, os acentos são eliminados (então *informação* corresponde a *informacao*), a sintaxe Markdown é
removida e as stop words comuns do inglês, do português e do espanhol são ignoradas. As distâncias de edição usam
o [RapidFuzz](https://github.com/rapidfuzz/RapidFuzz); um algoritmo bit-paralelo em Python puro dá
resultados idênticos quando ele não está disponível.

### Das características a uma probabilidade

Cada valor de característica (entre 0 e 1) é colocado em um de **8 intervalos (bins)**. Para cada característica, o modelo mantém
a frequência com que pares ligados e pares não ligados caem em cada intervalo, e estima

```text
P(link | f1 … f8)  ∝  P(link) × Π P(fi | link)
```

A **evidência** de uma característica é sua razão de log-verossimilhança, log P(bin | link) − log P(bin | no link).
A probabilidade exibida é a função logística do log-odds a priori somado à soma (ponderada) das
evidências.

**De onde vêm as contagens.** O modelo treina com o seu cofre toda vez que ele muda de forma perceptível:

- **exemplos positivos**: todos os pares de notas ligadas, mais as sugestões que você aceitou (até 600 pares são
  amostrados em cofres muito grandes);
- **exemplos negativos**: pares aleatórios de notas não ligadas, três para cada exemplo positivo, mais todas as
  sugestões que você **dispensou**, que contam em dobro.

**Uma priori para funcionar desde o primeiro dia.** Antes de qualquer dado, cada intervalo começa com *pseudo-contagens* de Dirichlet
(10 por característica e classe, por padrão). Elas codificam uma crença fraca: para pares ligados, as contagens crescem
com a similaridade, e para pares não ligados elas caem acentuadamente. Isso basta para ordenar sugestões em um cofre
novo. Conforme você liga notas, as contagens reais superam a priori e o modelo se adapta ao *seu* jeito de ligar.
Como positivos e negativos são amostrados na proporção de um para três, a priori da classe P(link) é cerca de um em quatro
(com pseudo-contagens correspondentes).

**Duas correções mantêm as estimativas honestas:**

1. **Sem vazamento de rótulo.** Os `[[links wiki]]` são removidos do texto antes de as características serem calculadas.
   Caso contrário, um link em linha colocaria o título do destino no texto, e o modelo aprenderia a
   reconhecer links existentes em vez de ideias relacionadas. Pelo mesmo motivo, ao treinar com um par ligado,
   a característica "links compartilhados" ignora o link entre as duas notas.
2. **A evidência correlacionada é ponderada.** O Naive Bayes assume que as características são independentes, mas algumas
   não são: TF-IDF e LSA se sobrepõem, assim como as três distâncias de texto. Contar evidências correlacionadas como
   independentes deixa o Naive Bayes simples excessivamente confiante. Por isso o ZettelApp multiplica a evidência de cada característica
   por **0,6** (Naive Bayes ponderado por característica), o que mantém as probabilidades realistas.

**Características ausentes ou desativadas contam como nenhuma evidência.** Se você desativa uma característica, ou ela não pode ser
calculada, ela não acrescenta nada, que é como o Naive Bayes trata naturalmente valores ausentes.

### Ordenando rapidamente

Comparar textos longos com a distância de Levenshtein é a etapa mais lenta, então a ordenação acontece em dois estágios.
Todos os candidatos são primeiro pontuados sem a característica de similaridade de texto, e somente os 150 melhores recebem a
pontuação completa. Candidatos para os quais você já tem link, e pares que você dispensou, nunca são sugeridos.

## Lendo a dica "por quê"

Passe o mouse sobre uma sugestão para ver a estimativa do modelo e a evidência de cada característica. Números positivos argumentam a favor de um
link e números negativos contra. O rótulo ao lado da barra resume a probabilidade: **forte**
(50% ou mais), **provável** (25% ou mais) ou **possível**.

As probabilidades são estimativas honestas e, em um cofre esparso, a maioria dos pares realmente não está ligada, então 15–30% podem
ser uma boa sugestão. O que mais importa é a ordem.

## Ajustes

*Ferramentas ▸ Opções ▸ Sugestões de links*:

| Opção | Padrão | Efeito |
|---|---|---|
| Sugerir links enquanto escrevo | ativado | Desativa por completo as sugestões do painel. |
| Características | todas as oito | Desmarque as características que você não quer considerar. |
| Mostrar no máximo | 8 | Número de sugestões listadas. |
| Correspondência mínima | 10% | Oculta sugestões abaixo dessa probabilidade. |
| Força da priori | 10 | Quantas pseudo-observações sustentam a priori. Valores maiores confiam na priori por mais tempo; valores menores se adaptam mais rápido aos seus links. |

- **Detalhes do modelo…** mostra com quantos pares ligados e não ligados o modelo treinou e quão informativa é
  cada característica (a divergência de Kullback–Leibler simétrica entre suas distribuições para pares ligados e
  não ligados).
- **Esquecer sugestões dispensadas** limpa suas dispensas, de modo que esses pares podem voltar a ser sugeridos e
  deixam de contar como exemplos negativos.
