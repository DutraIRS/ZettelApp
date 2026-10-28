# Graph and Insights

## The graph

The **Graph** page (Ctrl+2) draws your notes as a network: each circle is a note, sized by how many links
it has, and each line is a link.

![The graph, coloured by tag](../website/assets/screenshots/graph-light.png)

### Controls

| Control | What it does |
|---|---|
| **All notes / Local** | Show the whole collection, or only the open note and the notes within **Depth** links of it (following links in both directions). *Show in graph* in a note's ⋯ menu opens the local graph. |
| **2D / 3D** | Switch between a flat, draggable layout and a 3D view you can orbit. |
| **Colour by** | Tags, *Clusters: k-means*, *Clusters: hierarchical*, or nothing. |
| **k** | Number of clusters. *Auto k* picks it for you (see below). |
| **Group** | Pull notes of the same group together and shade each group's area. |
| **Labels** | Show note titles. In large graphs, only the best-connected notes are labelled until you hover. |
| **Link types** | Hide or show individual link types. |
| **Find in graph** | Type part of a title and press Enter to jump to the note. |

At the bottom right are zoom, fit, **recompute layout**, **save as image** (PNG) and **export these
notes** (opens the [export](export-import.md) dialog with the notes on screen).

**In 2D**, drag a note to move it, drag the background to pan, and use the mouse wheel to zoom. Double-click
a note to open it; right-click it for more (open, local graph, quiz on this neighbourhood, export with
linked notes). A note's title image is shown inside its circle.

Several links between the same two notes are drawn as **separate curves**, each with its own arrow tip
following the curve, so none hides another. Hovering or selecting a note **dims the other links**, keeps the note's own links in their
link-type colours, and labels each neighbour with the link types **as read from that note**, for example
*Supports · Extended by*. This works the same in 2D and 3D.

**In 3D**, drag to orbit, use the wheel to zoom, and double-click a note to open it. **Rotate
automatically** spins the view. Nearer notes are larger and brighter, so depth is easy to read, and each
group appears as a soft coloured halo.

The layout is force-directed (Fruchterman–Reingold): links pull notes together, all notes push each
other apart, and gentle gravity keeps separate components on screen. It runs in the background and is
cached per view.

### Colouring by tag

Each note takes the colour of its **most common tag**, the one used by the most notes in view, so the
big themes of your vault get distinct colours.

### Colouring by cluster

Clustering groups notes **by meaning**, whether or not they are linked. Each note becomes a vector in a
semantic space using latent semantic analysis (LSA) of its title, text and tags. Then one of two methods
groups the vectors:

- **k-means**: Lloyd's algorithm with k-means++ seeding, best of several runs. It is fast and gives
  round, even-sized groups.
- **Hierarchical**: agglomerative clustering with average linkage on cosine distance, computed with the
  nearest-neighbour-chain algorithm (O(n²)). It works better for uneven, nested topics. Vaults above
  4,000 notes fall back to k-means.

With **Auto k**, ZettelApp tries k from 2 up to about √(n/2) + 2 (at most 12) and keeps the k with the
best **silhouette score**. The score, shown under the legend, measures how well separated the clusters
are: 1 is perfect, around 0 means overlapping groups. Each cluster is named by its most distinctive
words, the terms more frequent inside it than in the rest of the vault.

### Groups and colours

With **Group** on, notes of the same tag or cluster are pulled towards each other, and each group gets a
lightly shaded region with its name. The legend lists the groups with their sizes. Click one to
highlight its notes.

Group and chart colours come from a palette **validated for colour-vision deficiencies** in both light
and dark mode. Colours are assigned in a fixed order and never reused: groups beyond the eighth share a
neutral grey "Other" colour. **Link types** use a second cue besides colour: each has its own line
(solid, dashed, dotted and so on), and directed types draw an arrow tip such as a triangle or a diamond.
Choose them in *Tools ▸ Options ▸ Link types* (see [Your own link types](notes-and-links.md#your-own-link-types)).
The legend always names everything, so nothing depends on colour alone.

## Insights

The **Insights** page (Ctrl+3) summarises your vault:

- **Tiles**: notes (and how many are in the Trash), links (and links per note), tags, *unlinked notes*
  (good candidates for linking), flashcards, and cards due today.
- **Notes added per month** over the last 12 months.
- **Top tags**, **Links by type** and the **Most connected notes** (click a bar to open the note).
- **Topics**: k-means clusters of your notes with their keywords and sizes.

Every chart has a **Show as table** button (the list icon) with the same numbers as a table, and bars
show their value on hover.
