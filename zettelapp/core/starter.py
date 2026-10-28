"""The notes a new vault starts with: a small Zettelkasten about ZettelApp itself.

A "Start here" hub (a map of content) lists ten short notes in reading order. Each holds
one idea, says exactly where to click or what to type, and links on to the next note.
Typed links appear where the relation is true when read from the note that holds them:
"One idea per note" is *part of* "What is a Zettelkasten?", "Mind maps" *extends*
"One idea per note". The hub's own links are plain, because a hub contains its notes and
no link type reads "contains" from the hub's side; the notes' backlinks show it instead.

Everything is written in the interface language when the vault is created. Titles are
translated first, so [[links]] use the titles the reader will see; syntax (Q:/A:,
{{c1::…}}, type::) is added by code so translators never have to keep it intact.
"""

from __future__ import annotations

import re

from zettelapp.core.models import new_mindmap_node
from zettelapp.core.storage import Vault
from zettelapp.core.textutil import normalize_tag
from zettelapp.i18n import N_, _

# Reading order. Keys are stable; titles and tags are translated when the notes are made.
HUB = "hub"
TITLES: dict[str, str] = {
    HUB: N_("Start here"),
    "zettelkasten": N_("What is a Zettelkasten?"),
    "atomic": N_("One idea per note"),
    "linking": N_("Link with a reason"),
    "tags": N_("Tags gather notes"),
    "media": N_("Pictures, files and sources"),
    "mindmaps": N_("Mind maps"),
    "flashcards": N_("Flashcards and review"),
    "graph": N_("The graph and Insights"),
    "suggestions": N_("Link suggestions"),
    "ai": N_("Ask your notes and MCP"),
}
SECTIONS = [
    (N_("The method"), ["zettelkasten", "atomic", "linking", "tags"]),
    (N_("Inside a note"), ["media", "mindmaps", "flashcards"]),
    (N_("The whole collection"), ["graph", "suggestions", "ai"]),
]
# A few broad tags, so colouring the graph by tag shows meaningful groups.
TAG_METHOD = N_("zettelkasten")
TAG_WRITING = N_("writing")
TAG_THINKING = N_("thinking")
TAG_MEMORY = N_("memory")
TAG_AI = N_("ai")
TAGS: dict[str, list[str]] = {
    HUB: [TAG_METHOD],
    "zettelkasten": [TAG_METHOD],
    "atomic": [TAG_METHOD, TAG_WRITING],
    "linking": [TAG_METHOD],
    "tags": [TAG_WRITING],
    "media": [TAG_WRITING],
    "mindmaps": [TAG_THINKING],
    "flashcards": [TAG_MEMORY],
    "graph": [TAG_THINKING],
    "suggestions": [TAG_THINKING],
    "ai": [TAG_AI],
}
EXAMPLE_TAG = N_("idea")  # written as a #tag in the text of "Tags gather notes"
QUEST_TITLE = N_("The Lost Prince of the Archive")  # the adventure in zettelapp.ui.quest

_UNLINKABLE = re.compile(r"[\[\]|#\n]")


def _tag(text: str) -> str:
    return normalize_tag(_(text)) or normalize_tag(text)


def _paragraphs(*parts: str) -> str:
    return "\n\n".join(p for p in parts if p)


def _bodies(link: dict[str, str]) -> dict[str, str]:
    """Note text in the interface language; *link* maps a key to its [[link]]."""
    example = "#" + _tag(EXAMPLE_TAG)

    def next_link(key: str) -> str:
        return _("Next: {link}").format(link=link[key])

    hub_sections = []
    number = 1
    for heading, keys in SECTIONS:
        items = []
        for key in keys:
            items.append(f"{number}. {link[key]}")
            number += 1
        hub_sections.append(f"## {_(heading)}\n" + "\n".join(items))

    return {
        HUB: _paragraphs(
            _(
                "Welcome to ZettelApp! These notes are a small Zettelkasten about the app "
                "itself. Each one holds a single idea and links to the next, so you learn by "
                "following links."
            ),
            _("**To follow a link, hold Ctrl and click it.** Start with the first one below."),
            *hub_sections,
            _(
                "Prefer a guided tour? Choose **Help ▸ {adventure}** for a short adventure "
                "through these features."
            ).format(adventure=_(QUEST_TITLE)),
            _(
                "When you no longer need these notes, select each one and press "
                "**Ctrl+Delete** to move it to the Trash."
            ),
        ),
        "zettelkasten": _paragraphs(
            _(
                "A Zettelkasten (German for “slip box”) is a collection of short notes that "
                "link to each other. Knowledge grows by connection rather than by filing: a "
                "note can take part in many conversations instead of sitting in one folder."
            ),
            _(
                "The sociologist Niklas Luhmann kept about 90,000 such notes and called his "
                "slip box a partner in thinking."
            ),
            _(
                "Two habits make it work. Both notes link here, so you find them under "
                "**Backlinks** in the panel on the right: click one to open it."
            ),
        ),
        "atomic": _paragraphs(
            _(
                "Give each note one idea, in your own words, in a few sentences. Small notes "
                "are easy to link, reuse and review; long notes hide their ideas."
            ),
            _(
                "Let the title state the idea, like the title of this note. When a note grows "
                "a second idea, split it: press **Ctrl+N** for a new note, move the text "
                "there and link the two."
            ),
            _("This habit is part of the method:") + f"\npart_of:: {link['zettelkasten']}",
            next_link("linking"),
        ),
        "linking": _paragraphs(
            _(
                "A plain link only says that two notes are related. Say *why* by writing a "
                "link type and two colons in front of the link:"
            ),
            f"part_of:: {link['zettelkasten']}",
            _(
                "The other types are {types}. The side panel on the right lists each link "
                "with its type, and the note at the other end shows it under **Backlinks**, "
                "read the other way round."
            ).format(types="supports::, contradicts::, extends::, example::, cites::"),
            _(
                "**Try it:** in any note, type {brackets} and the first letters of a title, "
                "then press **Enter**. **Ctrl+K** lets you pick a note and a link type from a "
                "list."
            ).format(brackets="`[[`"),
            next_link("tags"),
        ),
        "tags": _paragraphs(
            _(
                "Tags group notes by topic, project or status, while links say how ideas "
                "connect. A few broad tags are enough; let links do the rest."
            ),
            _(
                "**Try it:** click **Add tag** under the title, type a word and press "
                "**Enter**. Or write a tag in the text with a hash sign, like {example}: it "
                "shows as an outlined chip and goes away when you delete it from the text."
            ).format(example=example),
            _(
                "To find tagged notes, use the tag filter above the note list, type {search} "
                "in the search box, or **Ctrl+click** a tag in the text."
            ).format(search=f"`tag:{_tag(EXAMPLE_TAG)}`"),
            next_link("media"),
        ),
        "media": _paragraphs(
            _("A note can carry more than text:"),
            "\n".join(
                [
                    "- "
                    + _(
                        "**Pictures:** copy an image and press **Ctrl+V** in the text, drag an "
                        "image file in, or click **Insert image** on the toolbar "
                        "(**Ctrl+Shift+I**). The first picture also appears next to the title "
                        "and in the graph."
                    ),
                    "- "
                    + _(
                        "**Files:** click **Link to a file** (the folder button on the "
                        "toolbar). The file stays where it is; Ctrl+click the link to show it "
                        "in File Explorer."
                    ),
                    "- "
                    + _(
                        "**Sources:** paste a web address or a Zotero item link into the "
                        "**Source link** box under the tags. **Insert ▸ Zotero Reference…** "
                        "cites an item from Zotero."
                    ),
                ]
            ),
            next_link("mindmaps"),
        ),
        "mindmaps": _paragraphs(
            _(
                "A mind map lets one note grow branches without splitting its idea: a place "
                "to brainstorm before you write. This note has a small one."
            ),
            _(
                "**Try it:** click the **Mind map** tab above the text, then **Add idea**. "
                "Press **Tab** for a child idea, **Enter** for a sibling and **F2** to rename. "
                "**From links** draws a map of the note's links."
            ),
            f"extends:: {link['atomic']}",
            next_link("flashcards"),
        ),
        "flashcards": _paragraphs(
            _(
                "Writing a note is not the same as remembering it. Flashcards bring ideas "
                "back just before you would forget them."
            ),
            _(
                "Write a question on a line that starts with {q} and the answer on the next "
                "line, starting with {a}, like this:"
            ).format(q="Q:", a="A:"),
            "Q: "
            + _("What should a single note contain?")
            + "\nA: "
            + _("One idea, in your own words."),
            _(
                "A sentence with a hidden part works too: {cloze} brings each card back just "
                "before you would forget it."
            ).format(cloze="{{c1::" + _("Spaced repetition") + "}}"),
            _(
                "**Try it:** open **Review** on the left (**Ctrl+4**) and click **Start "
                "review**. Press **Space** to see the answer, then grade yourself from **1** "
                "(again) to **4** (easy)."
            ),
            next_link("graph"),
        ),
        "graph": _paragraphs(
            _(
                "**Graph** on the left (**Ctrl+2**) shows your notes as a network: each "
                "circle is a note and each line a link, coloured by its type."
            ),
            _(
                "**Try it:** hover a note to light up its neighbours, and double-click it to "
                "open it. **Local** shows only the open note's neighbourhood, **Colour by** "
                "groups notes by tag or by meaning, and **3D** lets you orbit the network."
            ),
            _(
                "**Insights** (**Ctrl+3**) counts your notes, links and tags. Its **Unlinked "
                "notes** tile is a to-do list: link those notes to something."
            ),
            next_link("suggestions"),
        ),
        "suggestions": _paragraphs(
            _(
                "While you write, **Suggested links** on the right lists notes that probably "
                "belong with this one. It compares the words, titles, tags and links of your "
                "notes, and learns from your choices."
            ),
            _(
                "**Try it:** click **Link** to accept a suggestion; the small arrow next to it "
                "picks a link type. Click **✕** to dismiss one. Hover a suggestion to see why "
                "it was suggested."
            ),
            f"extends:: {link['linking']}",
            next_link("ai"),
        ),
        "ai": _paragraphs(
            _("Both are optional, and nothing leaves your computer until you set them up."),
            "\n".join(
                [
                    "- "
                    + _(
                        "**Ask** (**Ctrl+5**) answers questions from your notes with an AI "
                        "provider of your choice, and cites the notes it used. Add your API key "
                        "in **Tools ▸ Options ▸ AI assistant**. Only your question and the "
                        "notes listed as sources are sent."
                    ),
                    "- "
                    + _(
                        "**MCP** lets AI agents such as Claude Desktop search and read your "
                        "notes while ZettelApp is open. Set it up in **Tools ▸ Options ▸ MCP "
                        "server**, then turn on the **MCP** switch in the status bar."
                    ),
                ]
            ),
            _("That is the end of the tour. Happy writing!"),
        ),
    }


def _mindmap(title: str) -> dict:
    root = new_mindmap_node(title)
    for text in (
        N_("Tab adds a child idea"),
        N_("Enter adds a sibling"),
        N_("F2 renames an idea"),
        N_("Right-click links an idea to a note"),
    ):
        root["children"].append(new_mindmap_node(_(text)))
    return root


def create_starter_notes(vault: Vault) -> dict[str, str]:
    """Write the starter notes into *vault*; returns note ids by key (see TITLES)."""
    with vault.transaction():
        notes = {
            key: vault.create_note(
                _(title).strip() or title, tags=[_tag(t) for t in TAGS.get(key, [])]
            )
            for key, title in TITLES.items()
        }
        link = {}
        for key, note in notes.items():
            if _UNLINKABLE.search(note.title):  # a title a [[link]] can't name: link by id
                link[key] = f"[[{note.id}|{_UNLINKABLE.sub(' ', note.title).strip()}]]"
            else:
                link[key] = f"[[{note.title}]]"
        bodies = _bodies(link)
        for key, note in notes.items():
            note.body = bodies[key]
            if key == "mindmaps":
                note.mindmap = _mindmap(note.title)
            vault.save_note(note, touch=False)
    return {key: note.id for key, note in notes.items()}
