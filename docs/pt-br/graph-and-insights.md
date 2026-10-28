# Grafo e Insights

## O grafo

A página **Grafo** (Ctrl+2) desenha suas notas como uma rede: cada círculo é uma nota, dimensionado pelo número de links
que ela tem, e cada linha é um link.

![O grafo, colorido por tag](../website/assets/screenshots/graph-light.png)

### Controles

| Controle | O que faz |
|---|---|
| **Todas as notas / Local** | Mostra a coleção inteira, ou somente a nota aberta e as notas a até **Profundidade** links de distância dela (seguindo links nos dois sentidos). *Mostrar no grafo*, no menu ⋯ de uma nota, abre o grafo local. |
| **2D / 3D** | Alterna entre um layout plano e arrastável e uma visão 3D que você pode orbitar. |
| **Cor por** | Tags, *Clusters: k-means*, *Clusters: hierárquico* ou nada. |
| **k** | Número de clusters. *k automático* escolhe por você (veja abaixo). |
| **Grupo** | Junta notas do mesmo grupo e sombreia a área de cada grupo. |
| **Rótulos** | Mostra os títulos das notas. Em grafos grandes, somente as notas mais conectadas recebem rótulo até você passar o mouse. |
| **Tipos de link** | Oculta ou mostra tipos de link individuais. |
| **Buscar no grafo** | Digite parte de um título e pressione Enter para ir até a nota. |

No canto inferior direito estão zoom, ajustar, **recalcular layout**, **salvar como imagem** (PNG) e **exportar estas
notas** (abre a caixa de diálogo de [exportação](export-import.md) com as notas na tela).

**Em 2D**, arraste uma nota para movê-la, arraste o fundo para deslocar a visão e use a roda do mouse para dar zoom. Clique duas vezes
em uma nota para abri-la; clique com o botão direito para mais opções (abrir, grafo local, quiz sobre esta vizinhança, exportar com
notas ligadas). A imagem de uma nota é exibida dentro do círculo dela.

Vários links entre as mesmas duas notas são desenhados como **curvas separadas**, cada uma com sua própria ponta de seta
acompanhando a curva, de modo que nenhuma esconde outra. Passar o mouse sobre uma nota ou selecioná-la **esmaece os outros links**, mantém os links da própria nota nas
cores de seus tipos de link e rotula cada vizinha com os tipos de link **como lidos a partir dessa nota**, por exemplo
*Apoia · Estendida por*. Isso funciona igual em 2D e 3D.

**Em 3D**, arraste para orbitar, use a roda para dar zoom e clique duas vezes em uma nota para abri-la. **Girar
automaticamente** faz a visão girar. Notas mais próximas são maiores e mais brilhantes, então a profundidade é fácil de ler, e cada
grupo aparece como um halo colorido suave.

O layout é dirigido por forças (Fruchterman–Reingold): os links puxam as notas para perto, todas as notas se afastam
umas das outras, e uma gravidade suave mantém componentes separados na tela. Ele roda em segundo plano e é
armazenado em cache por visão.

### Colorindo por tag

Cada nota assume a cor de sua **tag mais comum**, a usada por mais notas na visão, de modo que os
grandes temas do seu cofre recebem cores distintas.

### Colorindo por cluster

O agrupamento reúne notas **por significado**, estejam elas ligadas ou não. Cada nota vira um vetor em um
espaço semântico usando análise semântica latente (LSA) de seu título, texto e tags. Depois, um de dois métodos
agrupa os vetores:

- **k-means**: algoritmo de Lloyd com inicialização k-means++, o melhor de várias execuções. É rápido e gera
  grupos arredondados e de tamanho parecido.
- **Hierárquico**: agrupamento aglomerativo com ligação média sobre a distância de cosseno, calculado com o
  algoritmo de cadeia de vizinhos mais próximos (O(n²)). Funciona melhor para assuntos desiguais e aninhados. Cofres com mais de
  4.000 notas recorrem ao k-means.

Com **k automático**, o ZettelApp testa k de 2 até cerca de √(n/2) + 2 (no máximo 12) e mantém o k com a
melhor **pontuação de silhueta**. A pontuação, mostrada abaixo da legenda, mede o quão bem separados estão os clusters:
1 é perfeito, perto de 0 significa grupos sobrepostos. Cada cluster é nomeado por suas palavras mais distintivas,
os termos mais frequentes dentro dele do que no resto do cofre.

### Grupos e cores

Com **Grupo** ativado, as notas da mesma tag ou cluster são puxadas umas para as outras, e cada grupo recebe uma
região levemente sombreada com seu nome. A legenda lista os grupos com seus tamanhos. Clique em um para
destacar suas notas.

As cores de grupos e gráficos vêm de uma paleta **validada para deficiências de visão de cores** nos modos claro
e escuro. As cores são atribuídas em ordem fixa e nunca reutilizadas: os grupos além do oitavo compartilham uma cor
cinza neutra "Outros". Os **Tipos de link** usam uma segunda pista além da cor: cada um tem sua própria linha
(sólida, tracejada, pontilhada e assim por diante), e os tipos direcionados desenham uma ponta de seta, como um triângulo ou um losango.
Escolha-os em *Ferramentas ▸ Opções ▸ Tipos de link* (veja [Seus próprios tipos de link](notes-and-links.md#your-own-link-types)).
A legenda sempre nomeia tudo, então nada depende apenas da cor.

## Insights

A página **Insights** (Ctrl+3) resume o seu cofre:

- **Blocos**: notas (e quantas estão na Lixeira), links (e links por nota), tags, *notas sem links*
  (boas candidatas a receber links), flashcards e cartões para hoje.
- **Notas adicionadas por mês** nos últimos 12 meses.
- **Principais tags**, **Links por tipo** e as **Notas mais conectadas** (clique em uma barra para abrir a nota).
- **Tópicos**: clusters k-means das suas notas com suas palavras-chave e tamanhos.

Todo gráfico tem um botão **Mostrar como tabela** (o ícone de lista) com os mesmos números em forma de tabela, e as barras
mostram seu valor ao passar o mouse.
