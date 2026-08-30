"""Weight stability-interval sensitivity analysis for AHP's criteria tree.

For a node X with at least one sibling, as X's local weight within its
parent P varies from 0 to 1 (siblings rescaled to still sum to 1-w), every
alternative's total score T_i is an affine function of w:

    T_i(w) = (1 - w) * C_i + w * D_i

D_i is T_i with X given all of P's weight; C_i is T_i with X given none
(siblings absorb its share). Both come from re-running compute_hierarchy
with the parent's local weights forced to that extreme (``overrides``),
reusing its aggregation logic instead of re-deriving it.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ahp_core.hierarchy import compute_hierarchy
from ahp_core.model import ROOT_KEY, ProblemData


@dataclass
class WeightSensitivity:
    alt_names: list[str]
    C: np.ndarray  # total scores with the studied node's local weight at 0
    D: np.ndarray  # total scores with the studied node's local weight at 1
    w0: float      # the node's current local weight within its parent
    node_name: str

    def score_at(self, w) -> np.ndarray:
        w = np.asarray(w, dtype=float)
        return (1 - w)[..., None] * self.C + w[..., None] * self.D

    def stability_interval(self, top_x: int) -> tuple[float, float, list[dict]]:
        """Widest [w_low, w_high] around w0 that keeps the top-x ranking sequence unchanged."""
        m = len(self.alt_names)
        top_x = max(1, min(top_x, m))

        f0 = self.score_at(np.array(self.w0))
        order = np.argsort(f0)[::-1]
        top_indices = order[:top_x]

        low_candidates: list[float] = []
        high_candidates: list[float] = []
        crossings: list[dict] = []
        seen_pairs: set[tuple[int, int]] = set()
        for i in top_indices:
            for j in range(m):
                if j == i:
                    continue
                pair = (min(i, j), max(i, j))
                if pair in seen_pairs:
                    continue
                seen_pairs.add(pair)
                w_cross = _crossing(self.C[i], self.D[i], self.C[j], self.D[j])
                if w_cross is None or not (0.0 <= w_cross <= 1.0):
                    continue
                crossings.append({"a": self.alt_names[i], "b": self.alt_names[j], "w": w_cross})
                if w_cross <= self.w0:
                    low_candidates.append(w_cross)
                if w_cross >= self.w0:
                    high_candidates.append(w_cross)

        w_low = max(low_candidates) if low_candidates else 0.0
        w_high = min(high_candidates) if high_candidates else 1.0
        return w_low, w_high, crossings


def _crossing(C_i: float, D_i: float, C_j: float, D_j: float) -> float | None:
    denom = (D_i - C_i) - (D_j - C_j)
    if abs(denom) < 1e-12:
        return None
    return (C_j - C_i) / denom


def sensitivity_eligible_nodes(problem: ProblemData) -> list[str]:
    """Every criterion with at least one sibling to redistribute weight
    with."""
    return [c.name for c in problem.criteria if len(problem.children(c.parent)) >= 2]


def compute_weight_sensitivity(problem: ProblemData, node_name: str) -> WeightSensitivity:
    """Build the weight-sensitivity model for one criterion node from the
    problem's current state. Raises ValueError for degenerate cases with no
    room to redistribute weight."""
    node = problem.node_by_name(node_name)
    parent_key = node.parent if node.parent is not None else ROOT_KEY
    siblings = problem.children(node.parent)
    if len(siblings) < 2:
        raise ValueError("This criterion has no siblings to redistribute weight with.")

    baseline = compute_hierarchy(problem)
    parent_result = baseline.node_results[parent_key]
    w0 = parent_result.local_weights[node_name]
    if w0 >= 1.0 - 1e-9:
        raise ValueError(
            "Ez a szempont jelenleg a teljes súlyt viszi, nincs másik testvér-szempont, "
            "amire át lehetne csoportosítani. / "
            "This criterion currently holds all the weight; there is no sibling to "
            "rescale, so a stability interval cannot be computed."
        )

    sibling_names = [s.name for s in siblings]

    d_local = {name: (1.0 if name == node_name else 0.0) for name in sibling_names}
    c_local = {
        name: (0.0 if name == node_name else parent_result.local_weights[name] / (1.0 - w0))
        for name in sibling_names
    }

    d_run = compute_hierarchy(problem, overrides={parent_key: d_local})
    c_run = compute_hierarchy(problem, overrides={parent_key: c_local})

    alt_names = [a.name for a in problem.alternatives]
    D = np.array([d_run.alternative_scores.get(name, 0.0) for name in alt_names])
    C = np.array([c_run.alternative_scores.get(name, 0.0) for name in alt_names])

    return WeightSensitivity(alt_names=alt_names, C=C, D=D, w0=w0, node_name=node_name)
