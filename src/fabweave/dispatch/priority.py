from __future__ import annotations

import math
from dataclasses import dataclass

# Below this many hours to due, 1/hours is continued by its tangent line so
# near-deadline lots stay ordered instead of collapsing into one urgency tier.
URGENCY_FLOOR_HOURS = 2.5


def _urgency(hours_to_due: float) -> float:
    if hours_to_due >= URGENCY_FLOOR_HOURS:
        return 1.0 / hours_to_due
    # Overdue lots share the maximum-urgency tier; the near-deadline ramp keeps
    # lots between now and the floor ordered instead of collapsing the tier.
    remaining = max(hours_to_due, 0.0)
    return 1.0 / URGENCY_FLOOR_HOURS + (URGENCY_FLOOR_HOURS - remaining) / URGENCY_FLOOR_HOURS**2


def dispatch_score(hours_to_due: float, remaining_steps: float, hold_risk: float, setup_penalty: float) -> float:
    values = (hours_to_due, remaining_steps, hold_risk, setup_penalty)
    if not all(math.isfinite(value) for value in values):
        raise ValueError("dispatch inputs must be finite")
    if remaining_steps <= 0:
        raise ValueError("remaining steps must be positive")
    urgency = _urgency(hours_to_due)
    flow = 1.0 / remaining_steps
    return 4.0 * urgency + 1.5 * flow + hold_risk - setup_penalty


@dataclass(frozen=True, slots=True)
class DispatchCandidate:
    lot_id: str
    hours_to_due: float
    remaining_steps: int
    hold_risk: float = 0.0
    setup_penalty: float = 0.0
    active_hold: bool = False
    frozen_until: int | None = None


def rank_candidates(candidates: list[DispatchCandidate], now: int) -> list[DispatchCandidate]:
    eligible = [
        candidate
        for candidate in candidates
        if not candidate.active_hold and (candidate.frozen_until is None or candidate.frozen_until <= now)
    ]
    return sorted(
        eligible,
        key=lambda candidate: (
            -dispatch_score(
                candidate.hours_to_due,
                candidate.remaining_steps,
                candidate.hold_risk,
                candidate.setup_penalty,
            ),
            candidate.lot_id,
        ),
    )
