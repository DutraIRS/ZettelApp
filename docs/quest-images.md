# Illustrations for “The Lost Princess of the Archive”

The first-run adventure (`zettelapp/ui/quest.py`) shows one illustration at the top of its card for the
prologue, each of the ten chapters and the finale: **12 images**. This page describes each one and gives
a prompt ready to paste into an image model.

The app works without them: when a file is missing, the card draws a soft accent-coloured banner with the
chapter's icon. Add the pictures one at a time if you like.

## Files

| | |
|---|---|
| Folder | `zettelapp/resources/quest/` (packaged by the PyInstaller spec and `pyproject.toml`) |
| Format | PNG, sRGB, 8-bit, **opaque** (no transparency: the picture fills the top of the card edge to edge) |
| Size | **1200 × 400 px** (3:1). The card shows it at 382 × 128 points, so it stays sharp at 300 % display scaling |
| Other sizes | Accepted: the app scales the picture to fill the banner and crops the overflow evenly from both sides. If your model can't make 3:1, generate 16:9 or 2:1 and crop to 1200 × 400, keeping the subject in the middle |
| File size | Aim for under 400 KB each (e.g. `pngquant --quality 70-90`) |

The card is white in light mode and dark grey (#2B2B2B) in dark mode, and the banner sits flush against
its top edge, so mid-tone backgrounds work best in both. The left and right sixths of each picture may be
covered by nothing, but keep faces and key objects inside the central two-thirds anyway.

## Shared style guide

Use the same style prefix for every image so the set looks like one storybook.

- **Look:** warm storybook vector illustration: flat shapes with soft gradients, gently rounded forms,
  a subtle paper grain, no hard black outlines (use darker tones of each colour instead). Calm, cosy and a
  little magical; never scary or violent. Think of a modern picture book drawn for a calm Windows 11 app.
- **Palette:** Windows blue `#005FB8` and light blue `#60CDFF` for the Archive's magic and the
  “silver threads”; warm parchment `#F3E9D2` and honey `#E8B04A` for paper, candlelight and wood;
  soft teal `#1BAF7A` as a secondary accent; the Fog of Forgetting in lavender-grey `#B9B4D9` with low
  contrast. Backgrounds in desaturated mid-tones (dusty navy `#2E3A59` for night scenes, warm beige
  `#E9DFC9` for day scenes). Avoid pure white and pure black areas.
- **Light:** soft, diffuse, slightly glowing; small sparkles where the magic is.
- **Composition:** wide 3:1 banner, the subject centred, lots of calm space, one clear focal point,
  readable at a small size.
- **No text:** no letters, words, numbers or runes anywhere (the app is translated into eleven languages).
  Index cards show only wavy ink lines.
- **Recurring characters** (keep them identical across images):
  - **Princess Ada:** a young woman with warm brown skin, dark curly hair tied up with a blue ribbon,
    round gold-rimmed glasses, a deep-blue cloak embroidered with fine silver thread, carrying a small
    stack of index cards. Kind, clever, calm.
  - **Quill:** a small, round snowy owl with big amber eyes, tiny round spectacles and one blue-tipped
    wing feather. Friendly and expressive; she is the guide.
  - **The Archivist (the player):** never shows a face. Seen from behind or as hands only, wearing a
    simple honey-coloured cardigan, so anyone can imagine themselves.
  - **The Fog of Forgetting:** soft lavender-grey mist that makes things fade at its edges. No face,
    no eyes, no claws. It is an atmosphere, not a monster.
  - **The Great Archive:** an endless, cosy library of wooden card cabinets and tall shelves, with
    glowing blue threads running between cards.

**Style prefix** (paste before each scene prompt):

> Warm storybook vector illustration, flat shapes with soft gradients and subtle paper grain, gently
> rounded forms, no black outlines, calm cosy magical mood, palette of Windows blue #005FB8, light blue
> #60CDFF, parchment #F3E9D2, honey #E8B04A, soft teal #1BAF7A and lavender-grey #B9B4D9 mist,
> desaturated mid-tone background, soft diffuse glowing light, wide 3:1 banner composition with the
> subject centred and calm empty space, no text, no letters, no numbers.

Negative prompt, for models that take one: *text, letters, words, numbers, runes, watermark, signature,
logo, frame, border, photorealistic, 3D render, harsh shadows, black outlines, scary, monster, weapons,
blood, cluttered.*

## The images

### 1. `prologue.png`: the call to adventure

Shown with *Begin the adventure / Not now*. Mood: wonder, a gentle hook.

Night in a cosy study at the edge of the Great Archive. Quill the owl has just landed on a wooden desk,
holding a torn index card in her beak. A desk lamp glows honey-gold. Through a tall arched doorway behind
the desk, the Archive's shelves disappear into lavender-grey fog, with faint blue threads fading into it.
The Archivist's hands rest on the desk in the foreground.

> *[style prefix]* Night in a cosy study at the edge of an endless magical library of wooden card
> cabinets. A small round snowy owl with amber eyes, tiny round spectacles and one blue-tipped feather
> lands on a wooden desk holding a torn blank index card in her beak. A honey-gold desk lamp glows. Behind
> the desk a tall arched doorway opens onto shelves fading into soft lavender-grey fog, with faint glowing
> blue threads disappearing into the mist. In the foreground, a person's hands in a honey-coloured
> cardigan rest on the desk; no face visible. Dusty navy background.

### 2. `journal.png`: Chapter 1, The Archivist's Journal

Task: create a note. Mood: a fresh start.

A blank index card on the desk, a quill pen beside it, and ink beginning to glow and spread across the
card in wavy lines that aren't words. Quill watches from the edge of the desk, encouraging.

> *[style prefix]* Close-up of a wooden desk with a single blank index card and a feather quill pen
> beside it; glowing blue ink spreads across the card in soft wavy lines (no words). A small round snowy
> owl with tiny spectacles watches eagerly from the edge of the desk. Warm honey lamplight, parchment and
> warm beige background.

### 3. `thread.png`: Chapter 2, The Silver Thread

Task: write a `[[link]]`. Mood: discovery.

Two index cards pinned to a cabinet, tied together by a glowing silver-blue thread. The Archivist's hand
pulls the thread gently, and it leads off into the shelves; the fog retreats from where the thread glows.

> *[style prefix]* Two index cards pinned side by side on an old wooden card cabinet, joined by a
> glowing silver-blue thread. A hand in a honey-coloured sleeve gently pulls the thread, which stretches
> away between tall library shelves. Where the thread glows, soft lavender-grey mist drifts back. Small
> sparkles along the thread.

### 4. `marks.png`: Chapter 3, Marks on the Shelves

Task: add a tag. Mood: order, curiosity.

A row of card-cabinet drawers, each with a small coloured tab (blue, teal, honey). One tab glows silver
with a simple hash-like engraved mark made of two crossed pairs of lines (a shape, not a letter). Quill
points at it with a wing.

> *[style prefix]* A row of wooden card-cabinet drawers, each with a small coloured label tab in blue,
> teal and honey. One tab glows silver, engraved with a simple mark of two pairs of crossed lines. A
> small round snowy owl with tiny spectacles points at the glowing tab with her wing. Warm library light,
> warm beige background.

### 5. `reason.png`: Chapter 4, Threads That Say Why

Task: make a typed link. Mood: understanding, things clicking into place.

Several index cards on a corkboard joined by threads of different colours (blue, teal, honey, purple),
each thread with a small distinct symbol charm hanging from it: an arrow, a plus, a leaf, a puzzle piece.
The threads hum with light.

> *[style prefix]* A corkboard in a cosy library with several index cards joined by glowing threads of
> different colours: blue, teal, honey and soft purple. A small charm hangs on each thread: an arrow, a
> plus sign, a leaf, a puzzle piece. The threads shimmer with gentle light. Warm beige background.

### 6. `whispers.png`: Chapter 5, The Whispering Shelves

Task: accept or dismiss a link suggestion. Mood: the Archive is alive and helpful.

Tall shelves curving overhead like a canopy; small glowing paper cards drift out of the shelves like
fireflies towards the Archivist, who stands seen from behind, looking up. Some cards glow brighter than
others.

> *[style prefix]* Seen from behind, a person in a honey-coloured cardigan stands among tall library
> shelves that curve overhead like a canopy. Small glowing paper cards float out of the shelves towards
> them like fireflies, some brighter than others, trailing faint blue light. Gentle lavender-grey mist
> low on the floor. Dusty navy background.

### 7. `map.png`: Chapter 6, The Map Room

Task: open the Graph. Mood: awe, seeing the whole.

A round observatory-like room at the top of the Archive. In the middle floats a luminous constellation:
glowing circles (notes) joined by lines of different colours, forming small clusters. Quill perches on a
brass railing, looking at it. One small cluster at the edge flickers with a tiny branching-tree shape.

> *[style prefix]* A round observatory room at the top of a magical library, with a brass railing and
> tall arched windows. In the middle floats a luminous constellation of glowing circles joined by lines
> of blue, teal, honey and purple, grouped into a few clusters. A small round snowy owl with tiny
> spectacles perches on the railing, gazing at it. At the edge of the constellation a tiny branching-tree
> shape flickers. Dusty navy background with soft stars.

### 8. `plan.png`: Chapter 7, Ada's Branching Plan

Task: add a mind-map idea. Mood: creativity.

A large sheet of parchment pinned to a drafting table, with a hand-drawn mind map: a central circle with
curved branches in several colours ending in small rounded boxes (no text inside, just wavy lines). One
new branch is being drawn in glowing blue ink and points to the right edge.

> *[style prefix]* A large parchment sheet on a wooden drafting table showing a hand-drawn mind map: a
> central circle with curved branches in blue, teal, honey and purple ending in small rounded boxes
> filled with wavy lines (no text). One new branch is being drawn in glowing blue ink, reaching towards
> the right edge. A feather quill and an ink pot beside it. Warm beige background, honey lamplight.

### 9. `evidence.png`: Chapter 8, Evidence on the Wall

Task: add a picture or link a file. Mood: detective work.

A gallery wall in the Archive with framed pictures, a pinned map, a folded document and a photograph,
connected by blue threads. Behind them, the faint outline of a stone door begins to appear in the wall.

> *[style prefix]* A gallery wall inside a cosy library covered with pinned evidence: small framed
> pictures of landscapes, a folded document with a paper clip, a little map and a photograph, all
> connected by glowing blue threads. Behind them, the faint carved outline of an arched stone door begins
> to appear in the wall. Warm honey light, parchment tones.

### 10. `riddle.png`: Chapter 9, The Riddle Door

Task: review a flashcard. Mood: a gentle challenge.

An arched stone door carved with a circle of simple symbols (moon phases, a spiral, a star, a leaf; no
letters). Two index cards float before it: one face down, one turning over to reveal a glowing answer.
Lavender fog curls at the door's base and fades where the card glows.

> *[style prefix]* An arched stone door in a magical library, carved with a ring of simple symbols:
> moon phases, a spiral, a star and a leaf (no letters). In front of it two index cards float in the
> air: one face down, one turning over and glowing softly. Lavender-grey mist curls at the foot of the
> door and fades where the card's light falls. Dusty navy and stone-grey tones.

### 11. `tower.png`: Chapter 10, The Tower of Insight

Task: open Insights. Mood: climbing towards the light.

A spiral staircase winding up inside a tall tower, its walls lined with shelves. At the top, a bright
room glows; floating near it are simple luminous bar shapes of different heights, like a chart made of
light. The fog stays below, thinning.

> *[style prefix]* A spiral staircase winding up inside a tall round library tower lined with
> bookshelves. At the top, a bright doorway glows warmly, and beside it float a few luminous vertical
> bars of different heights in blue and teal, like a chart made of light (no numbers). Soft lavender-grey
> mist lingers at the bottom of the stairs and thins as it rises. A small round snowy owl flies up the
> stairwell.

### 12. `finale.png`: The princess is free!

Shown when the adventure is complete. Mood: joy, warmth, relief.

Morning light floods the Great Archive; the fog is gone. Princess Ada steps forward smiling, holding her
stack of index cards, her blue cloak's silver threads shining. Quill flies happily around her. The
Archivist, seen from behind, faces her. Glowing blue threads connect the shelves in every direction like
a festive web.

> *[style prefix]* Morning light floods an endless cosy library of wooden card cabinets; the mist is
> gone. A young woman with warm brown skin, dark curly hair tied up with a blue ribbon and round
> gold-rimmed glasses, wearing a deep-blue cloak embroidered with silver thread, steps forward smiling,
> holding a small stack of index cards. A small round snowy owl with tiny spectacles flies happily around
> her. In the foreground, seen from behind, a person in a honey-coloured cardigan faces her; no face
> visible. Glowing blue threads connect the shelves in every direction like a festive web. Warm beige and
> light blue tones, joyful.

## Checking them in the app

Put the files in `zettelapp/resources/quest/`, start ZettelApp and choose *Help ▸ The Lost Princess of the
Archive*. *Skip this step* walks through every chapter quickly. Look at the card in both *View ▸ Theme ▸
Light* and *Dark*.
