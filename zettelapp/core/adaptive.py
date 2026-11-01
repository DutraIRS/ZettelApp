"""Optional adaptive ranking: Bayesian weight updates and epsilon-greedy exploration.

Learns only from explicit relevant / not-relevant feedback on search results.
All state is aggregate statistics; nothing about individual notes, queries or
browsing activity is stored.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field

from zettelapp.core.search import DEFAULT_WEIGHTS, SIGNALS, normalize_weights

EPSILON_DEFAULT = 0.10
ARM_COUNT = 5
PRIOR_ALPHA = 1.0  # Beta prior strength: optimistic-neutral start
PRIOR_BETA = 1.0


def candidate_arms(base: dict[str, float]) -> list[dict[str, float]]:
    """The default weights plus a few deterministic perturbations."""
    arms = [dict(base)]
    bumps = [
        {"fuzzy": 1.6},
        {"lexical": 1.6},
        {"semantic": 1.8},
        {"ontology": 2.0},
    ]
    for bump in bumps:
        arm = dict(base)
        for signal, factor in bump.items():
            if signal in arm:
                arm[signal] *= factor
        arms.append(arm)
    return arms


@dataclass
class ArmStats:
    wins: int = 0
    losses: int = 0

    @property
    def mean(self) -> float:
        return (self.wins + PRIOR_ALPHA) / (self.wins + self.losses + PRIOR_ALPHA + PRIOR_BETA)


@dataclass
class AdaptiveState:
    epsilon: float = EPSILON_DEFAULT
    enabled: bool = False
    weights: dict[str, float] = field(default_factory=lambda: dict(DEFAULT_WEIGHTS))
    arm_stats: list[ArmStats] = field(
        default_factory=lambda: [ArmStats() for _ in range(ARM_COUNT)]
    )
    current_arm: int = 0
    feedback_count: int = 0

    def to_json(self) -> str:
        return json.dumps(
            {
                "epsilon": self.epsilon,
                "enabled": self.enabled,
                "weights": self.weights,
                "arms": [[a.wins, a.losses] for a in self.arm_stats],
                "current_arm": self.current_arm,
                "feedback_count": self.feedback_count,
            }
        )

    @classmethod
    def from_json(cls, text: str) -> AdaptiveState:
        data = json.loads(text)
        state = cls()
        state.epsilon = float(data.get("epsilon", EPSILON_DEFAULT))
        state.enabled = bool(data.get("enabled", False))
        if isinstance(data.get("weights"), dict):
            state.weights = {k: float(v) for k, v in data["weights"].items() if k in SIGNALS}
        arms = data.get("arms", [])
        state.arm_stats = [ArmStats(wins=int(a[0]), losses=int(a[1])) for a in arms] or [
            ArmStats() for _ in range(ARM_COUNT)
        ]
        state.current_arm = int(data.get("current_arm", 0)) % max(1, len(state.arm_stats))
        state.feedback_count = int(data.get("feedback_count", 0))
        return state


class AdaptiveRanker:
    """Epsilon-greedy selection over ranking-weight configurations.

    With probability 1-eps picks the arm with the best estimated success rate;
    otherwise explores a uniformly random other arm. Selected-arm performance
    is updated only from explicit feedback.
    """

    def __init__(
        self,
        state: AdaptiveState | None = None,
        rng: random.Random | None = None,
        base_weights: dict[str, float] | None = None,
    ):
        self.state = state or AdaptiveState()
        self.rng = rng or random.Random()
        self.arms = candidate_arms(base_weights or DEFAULT_WEIGHTS)
        if len(self.state.arm_stats) != len(self.arms):
            self.state.arm_stats = [ArmStats() for _ in self.arms]

    # --- bandit ------------------------------------------------------------

    def select_arm(self) -> int:
        if self.rng.random() < self.state.epsilon:
            others = [i for i in range(len(self.arms)) if i != self.state.current_arm]
            self.state.current_arm = self.rng.choice(others) if others else 0
        else:
            best = max(range(len(self.arms)), key=lambda i: self.state.arm_stats[i].mean)
            self.state.current_arm = best
        return self.state.current_arm

    def record_feedback(self, relevant: bool) -> None:
        """Explicit feedback on results ranked by the current arm."""
        arm = self.state.arm_stats[self.state.current_arm]
        if relevant:
            arm.wins += 1
        else:
            arm.losses += 1
        self.state.feedback_count += 1

    def effective_epsilon(self) -> float:
        """Shrink exploration as feedback accumulates (never below eps/10)."""
        eps = self.state.epsilon
        decay = 1.0 / (1.0 + self.state.feedback_count / 50.0)
        return max(eps / 10.0, eps * decay)

    # --- weights ----------------------------------------------------------

    def current_weights(self) -> dict[str, float]:
        return normalize_weights(self.arms[self.state.current_arm])

    def reset(self) -> None:
        self.state = AdaptiveState(epsilon=self.state.epsilon)


class BayesianWeightModel:
    """Weighted Naive-Bayes-style signal reliability from feedback evidence.

    Each signal's weight is adjusted by the smoothed log-odds that the signal
    was present in results the user marked relevant versus not relevant.
    """

    def __init__(
        self,
        priors: dict[str, float] | None = None,
        smoothing: float = 1.0,
    ):
        self.priors = normalize_weights(priors or DEFAULT_WEIGHTS)
        self.smoothing = smoothing
        self.relevant: dict[str, float] = {k: 0.0 for k in SIGNALS}
        self.irrelevant: dict[str, float] = {k: 0.0 for k in SIGNALS}

    def update(self, signals: dict[str, float], relevant: bool) -> None:
        bucket = self.relevant if relevant else self.irrelevant
        for signal, value in signals.items():
            if signal in bucket:
                bucket[signal] += float(value)

    def weights(self) -> dict[str, float]:
        total_rel = sum(self.relevant.values())
        total_irr = sum(self.irrelevant.values())
        out: dict[str, float] = {}
        for signal, prior in self.priors.items():
            p = (self.relevant[signal] + self.smoothing) / (
                total_rel + self.smoothing * len(SIGNALS)
            )
            q = (self.irrelevant[signal] + self.smoothing) / (
                total_irr + self.smoothing * len(SIGNALS)
            )
            # Conservative: shrink the log-ratio toward 1 (no adjustment).
            adjustment = max(0.25, min(4.0, p / q))
            out[signal] = prior * adjustment
        return normalize_weights(out)
