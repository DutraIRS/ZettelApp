# Link suggestions

While you write, the **Suggested links** panel lists notes that probably belong with the one you are
editing. Click **Link** to connect them (the arrow next to it chooses the link type), or **✕** to dismiss a
suggestion. Both teach the model. Hover a suggestion to see *why* it was suggested.

Suggestions update about a second after you stop typing, in the background, so the editor never waits for
them. They use your unsaved text too.

## How it works

ZettelApp treats "should these two notes be linked?" as a classification problem and answers it with a
**Naive Bayes** classifier. For a note *q* and every candidate note *c*, it computes eight similarity
features and combines the evidence into a probability.

### The features

| Feature | What it measures |
|---|---|
| **Semantic similarity (LSA)** | Cosine similarity in a latent semantic space: a truncated SVD of the TF-IDF matrix (randomised SVD, up to 64 dimensions). Notes that use related vocabulary end up close even when they share few exact words. |
| **Shared keywords (TF-IDF cosine)** | Cosine similarity of TF-IDF vectors (sublinear term frequency, smoothed inverse document frequency). Titles count double; tags are included. |
| **Title similarity (Levenshtein)** | 1 − edit distance ÷ length of the longer title. |
| **Title similarity (Jaro-Winkler)** | Jaro-Winkler similarity of the titles, which rewards a shared beginning. |
| **Text similarity (Levenshtein)** | Normalised edit distance between the first 400 characters of the two texts. |
| **Shared tags (Jaccard)** | Tags in common ÷ tags in total. |
| **Title mentioned in the text** | 1 if either note's title appears as whole words in the other's text, else 0. |
| **Shared links (Jaccard)** | Overlap between the two notes' linked notes (closing triangles in the graph). |

Text is lower-cased, accents are folded (so *informação* matches *informacao*), Markdown syntax is
removed, and common English, Portuguese and Spanish stop words are ignored. Edit distances use
[RapidFuzz](https://github.com/rapidfuzz/RapidFuzz); a pure-Python bit-parallel algorithm gives
identical results when it isn't available.

### From features to a probability

Each feature value (between 0 and 1) is placed into one of **8 bins**. For each feature, the model keeps
how often linked pairs and unlinked pairs fall into each bin, and estimates

```text
P(link | f1 … f8)  ∝  P(link) × Π P(fi | link)
```

The **evidence** of a feature is its log-likelihood ratio, log P(bin | link) − log P(bin | no link).
The probability shown is the logistic function of the prior log-odds plus the (weighted) sum of the
evidence.

**Where the counts come from.** The model trains on your vault every time it changes noticeably:

- **positive examples**: every pair of linked notes, plus suggestions you accepted (up to 600 pairs are
  sampled in very large vaults);
- **negative examples**: random pairs of unlinked notes, three for every positive example, plus every
  suggestion you **dismissed**, which counts double.

**A prior so it works from day one.** Before any data, each bin starts with Dirichlet *pseudo-counts*
(10 per feature and class, by default). These encode a weak belief: for linked pairs the counts rise
with similarity, and for unlinked pairs they fall steeply. That is enough to rank suggestions in a new
vault. As you link notes, real counts outweigh the prior and the model adapts to *your* way of linking.
Because positives and negatives are sampled one to three, the class prior P(link) is about one in four
(with matching pseudo-counts).

**Two corrections keep the estimates honest:**

1. **No label leakage.** `[[Wiki links]]` are removed from the text before features are computed.
   Otherwise an inline link would put the target's title into the text, and the model would learn to
   recognise existing links rather than related ideas. For the same reason, when training on a linked
   pair, the "shared links" feature ignores the link between the two notes.
2. **Correlated evidence is weighted.** Naive Bayes assumes the features are independent, but some are
   not: TF-IDF and LSA overlap, and so do the three string distances. Counting correlated evidence as
   independent makes plain Naive Bayes overconfident. ZettelApp therefore multiplies each feature's
   evidence by **0.6** (feature-weighted Naive Bayes), which keeps probabilities realistic.

**Missing or disabled features count as no evidence.** If you switch a feature off, or it can't be
computed, it adds nothing, which is how Naive Bayes naturally handles missing values.

### Ranking quickly

Comparing long texts with Levenshtein distance is the slowest step, so ranking happens in two stages.
All candidates are first scored without the text-similarity feature, and only the best 150 get the full
score. Candidates you already link to, and pairs you dismissed, are never suggested.

## Reading the "why" tooltip

Hover a suggestion to see the model's estimate and each feature's evidence. Positive numbers argue for a
link and negative numbers against. The label next to the bar summarises the probability: **strong**
(50% or more), **likely** (25% or more) or **possible**.

Probabilities are honest estimates, and in a sparse vault most pairs really are unlinked, so 15–30% can
be a good suggestion. What matters most is the order.

## Tuning

*Tools ▸ Options ▸ Link suggestions*:

| Option | Default | Effect |
|---|---|---|
| Suggest links while I write | on | Turn the panel's suggestions off entirely. |
| Features | all eight | Untick features you don't want considered. |
| Show at most | 8 | Number of suggestions listed. |
| Minimum match | 10% | Hide suggestions below this probability. |
| Prior strength | 10 | How many pseudo-observations back the prior. Higher values trust the prior longer; lower values adapt to your links faster. |

- **Model details…** shows how many linked and unlinked pairs the model trained on, and how informative
  each feature is (the symmetric Kullback–Leibler divergence between its distributions for linked and
  unlinked pairs).
- **Forget dismissed suggestions** clears your dismissals, so those pairs can be suggested again and
  stop counting as negative examples.
