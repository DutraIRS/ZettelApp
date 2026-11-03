"""Optional adaptive ranking: learn from "relevant" and "not relevant" clicks on search results
which signals to trust more.

Learning only happens on those clicks. Only a running total per signal is kept, on this
computer: nothing about which notes were marked or what was searched for.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from zettelapp.core.search import SIGNALS

MAX_ADJUSTMENT = 4.0  # no amount of feedback moves a weight further than this, up or down


def _totals() -> dict[str, float]:
    return dict.fromkeys(SIGNALS, 0.0)


@dataclass
class FeedbackModel:
    """Naive-Bayes-style: a weight grows with how much likelier its signal is in results marked
    relevant than in those marked not relevant."""

    relevant: dict[str, float] = field(default_factory=_totals)
    irrelevant: dict[str, float] = field(default_factory=_totals)

    def update(self, signals: dict[str, float], relevant: bool) -> None:
        totals = self.relevant if relevant else self.irrelevant
        for signal, value in signals.items():
            if signal in totals:
                totals[signal] += value

    def adjust(self, weights: dict[str, float]) -> dict[str, float]:
        def share(totals: dict[str, float], signal: str) -> float:  # with add-one smoothing
            return (totals[signal] + 1) / (sum(totals.values()) + len(SIGNALS))

        return {
            signal: weight
            * max(
                1 / MAX_ADJUSTMENT,
                min(MAX_ADJUSTMENT, share(self.relevant, signal) / share(self.irrelevant, signal)),
            )
            for signal, weight in weights.items()
        }

    def to_json(self) -> str:
        return json.dumps({"relevant": self.relevant, "irrelevant": self.irrelevant})

    @classmethod
    def from_json(cls, text: str) -> FeedbackModel:
        """The saved totals; anything unreadable counts as nothing learned yet."""
        model = cls()
        try:
            data = json.loads(text)
            for totals, key in ((model.relevant, "relevant"), (model.irrelevant, "irrelevant")):
                totals.update({s: max(0.0, float(data[key][s])) for s in SIGNALS})
        except (TypeError, ValueError, KeyError):
            return cls()
        return model
