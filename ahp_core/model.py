"""Data model for an AHP (pairwise-comparison, PCM) decision problem.

This module has no Streamlit dependency: it is the single source of truth
for problem state, shared by every page through ``st.session_state`` (see
app_state.py), mirroring how promethee_core/model.py anchors the PROMETHEE
Playground.

The key structural difference from PROMETHEE is that criteria form a
**tree**, not a flat list: every main criterion may have sub-criteria, and
so on. A node is identified by its (globally unique) ``name`` — there is no
separate id concept, exactly like PROMETHEE identifies alternatives/criteria
by name — and ``parent`` points at the parent node's name, or ``None`` for a
top-level (main) criterion.

Per AHP.pdf's terminology: a node without children is a "levélszempont"
(leaf criterion). Every node that has children owns a pairwise-comparison
matrix (PCM) over those children — including the implicit root, whose
"children" are the main criteria, keyed by the ``ROOT_KEY`` sentinel below.
Every *leaf* criterion also owns a comparison — either a PCM over the
alternatives (eval_mode=PAIRWISE), or, per the GUI spec's explicit request,
a column of raw values that get normalized directly instead
(eval_mode=DIRECT, e.g. "just type each alternative's price").
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

import numpy as np
import pandas as pd

from ahp_core.palette import default_color

# Sentinel key for "the matrix comparing the main (top-level) criteria",
# i.e. the implicit root's children. Not a legal criterion name (enforced
# by add_criterion), so it can never collide with a real node.
ROOT_KEY = "__root__"


class Direction(str, Enum):
    MAX = "max"
    MIN = "min"


class EvalMode(str, Enum):
    """How a group's items get weighted: via a pairwise-comparison matrix, or
    via directly-entered raw values that get normalized instead (AHP.pdf
    itself discusses "közvetlen súlyozás", direct weighting, as a valid
    alternative to pairwise comparison for weighing criteria — not just, per
    the GUI spec's item 35, for scoring alternatives on a leaf). Applies
    uniformly to any group: the root and non-leaf criteria (weighting their
    children) as well as leaf criteria (weighting alternatives)."""
    PAIRWISE = "pairwise"
    DIRECT = "direct"


class WeightMethod(str, Enum):
    """Global, problem-wide choice of weight-vector method (GUI spec item 18-20)."""
    EIGENVECTOR = "eigenvector"
    LLSM = "llsm"


@dataclass
class Alternative:
    name: str
    description: str = ""
    color: str = ""  # hex color; empty means "use the default palette"


@dataclass
class CriterionNode:
    name: str
    parent: str | None = None  # None = top-level (main) criterion
    color: str = ""
    eval_mode: EvalMode = EvalMode.PAIRWISE
    direction: Direction = Direction.MAX


@dataclass
class PCM:
    """A pairwise-comparison matrix over an ordered list of item names.

    ``values[i, j]`` is "how many times more important/preferred item i is
    over item j"; NaN marks a not-yet-entered (missing) comparison, per
    NemTeljesenKitoltott.pdf's ``*`` notation. The diagonal is always 1.
    """
    items: list[str]
    values: np.ndarray  # shape (n, n)

    @classmethod
    def empty(cls, items: list[str]) -> "PCM":
        n = len(items)
        values = np.full((n, n), np.nan)
        np.fill_diagonal(values, 1.0)
        return cls(items=list(items), values=values)

    def size(self) -> int:
        return len(self.items)

    def set_value(self, i: int, j: int, value: float) -> None:
        if i == j or value <= 0:
            return
        self.values[i, j] = value
        self.values[j, i] = 1.0 / value

    def clear_value(self, i: int, j: int) -> None:
        if i == j:
            return
        self.values[i, j] = np.nan
        self.values[j, i] = np.nan

    def get(self, i: int, j: int) -> float:
        return float(self.values[i, j])

    def missing_pairs(self) -> list[tuple[int, int]]:
        n = self.size()
        return [(i, j) for i in range(n) for j in range(i + 1, n) if np.isnan(self.values[i, j])]

    def is_complete(self) -> bool:
        return len(self.missing_pairs()) == 0

    def reindex(self, new_items: list[str]) -> "PCM":
        """Resize/reorder to ``new_items``, matching by name to preserve every
        comparison whose both endpoints survive; anything involving a
        brand-new item starts out missing. This is how the matrix silently
        keeps up as criteria/alternatives are added, removed or reordered
        elsewhere in the problem, without ever losing existing entries."""
        new = PCM.empty(new_items)
        old_index = {name: i for i, name in enumerate(self.items)}
        for a_idx, a in enumerate(new_items):
            if a not in old_index:
                continue
            for b_idx, b in enumerate(new_items):
                if b not in old_index:
                    continue
                new.values[a_idx, b_idx] = self.values[old_index[a], old_index[b]]
        return new

    def rename_item(self, old_name: str, new_name: str) -> None:
        if old_name in self.items:
            self.items[self.items.index(old_name)] = new_name


@dataclass
class ProblemData:
    name: str = "New problem"
    description: str = ""
    # The hierarchy's own top label (AHP.pdf's "a döntési feladat célja") —
    # deliberately separate from `name`, which is just this saved file/session's
    # title and needn't read the same as the actual decision goal shown at the
    # root of the tree diagram.
    goal_name: str = "Goal"
    weight_method: WeightMethod = WeightMethod.EIGENVECTOR
    # How the root weighs the main criteria against each other — the root has
    # no CriterionNode of its own to hold this, unlike every other group.
    root_eval_mode: EvalMode = EvalMode.PAIRWISE
    alternatives: list[Alternative] = field(default_factory=list)
    criteria: list[CriterionNode] = field(default_factory=list)
    matrices: dict[str, PCM] = field(default_factory=dict)
    # Raw values for DIRECT-mode leaves: index = alternative name, columns = leaf name.
    direct_values: pd.DataFrame = field(default_factory=pd.DataFrame)
    # Raw values for DIRECT-mode groups (root/non-leaf) weighting their
    # children: keyed directly by child *criterion name* — names are globally
    # unique across the whole tree, so no group-scoping is needed here.
    direct_group_weights: dict[str, float] = field(default_factory=dict)

    # -- lookup helpers ---------------------------------------------------------

    def node_by_name(self, name: str) -> CriterionNode:
        for c in self.criteria:
            if c.name == name:
                return c
        raise KeyError(f"Unknown criterion: {name}")

    def children(self, parent: str | None) -> list[CriterionNode]:
        """All children of ``parent`` (None = top-level), in insertion order."""
        return [c for c in self.criteria if c.parent == parent]

    def is_leaf(self, node: CriterionNode) -> bool:
        return len(self.children(node.name)) == 0

    def leaf_criteria(self) -> list[CriterionNode]:
        return [c for c in self.criteria if self.is_leaf(c)]

    def pairwise_leaf_criteria(self) -> list[CriterionNode]:
        return [c for c in self.leaf_criteria() if c.eval_mode == EvalMode.PAIRWISE]

    def direct_leaf_criteria(self) -> list[CriterionNode]:
        return [c for c in self.leaf_criteria() if c.eval_mode == EvalMode.DIRECT]

    def node_eval_mode(self, group_key: str) -> EvalMode:
        """How ``group_key`` weighs its items — the root's own field for the
        main criteria, or a node's own field otherwise (meaning "how I weigh
        my children" for a non-leaf, or "how I score alternatives" for a
        leaf)."""
        if group_key == ROOT_KEY:
            return self.root_eval_mode
        return self.node_by_name(group_key).eval_mode

    def set_group_eval_mode(self, group_key: str, eval_mode: EvalMode) -> None:
        if group_key == ROOT_KEY:
            self.root_eval_mode = eval_mode
            return
        node = self.node_by_name(group_key)
        node.eval_mode = eval_mode
        if eval_mode == EvalMode.DIRECT and self.is_leaf(node) and node.name not in self.direct_values.columns:
            self.direct_values[node.name] = 0.0

    def all_pcm_group_keys(self) -> list[str]:
        """Every group whose weighting is currently done via an editable PCM:
        the root/non-leaf criteria in PAIRWISE mode, plus every PAIRWISE
        leaf's alternative comparison."""
        return [k for k in self.group_keys() if self.node_eval_mode(k) == EvalMode.PAIRWISE] + [
            c.name for c in self.pairwise_leaf_criteria()
        ]

    def direct_weight_group_keys(self) -> list[str]:
        """Every group (root/non-leaf) currently weighting its children via
        directly-entered values instead of a PCM."""
        return [k for k in self.group_keys() if self.node_eval_mode(k) == EvalMode.DIRECT]

    def group_keys(self) -> list[str]:
        """Names of every node that owns a "compare my children" weighting
        (PCM or direct), plus the root sentinel for the main criteria — i.e.
        everything with children."""
        return [ROOT_KEY] + [c.name for c in self.criteria if not self.is_leaf(c)]

    def group_items(self, group_key: str) -> list[str]:
        """The ordered item names a given group's PCM compares."""
        parent = None if group_key == ROOT_KEY else group_key
        return [c.name for c in self.children(parent)]

    def alternative_colors(self) -> dict[str, str]:
        return {a.name: (a.color or default_color(i)) for i, a in enumerate(self.alternatives)}

    def criterion_colors(self) -> dict[str, str]:
        return {c.name: (c.color or default_color(i)) for i, c in enumerate(self.leaf_criteria())}

    # -- matrix access (lazily created/reindexed) --------------------------------

    def matrix_for(self, group_key: str) -> PCM:
        """The PCM for a group (root's main criteria, a non-leaf's children, or
        a PAIRWISE leaf's alternatives), auto-resized to the group's current
        items. Always returns the *same object* stored in ``self.matrices``, so
        callers can mutate it in place (set_value/clear_value) and have that
        stick without an explicit write-back."""
        items = self.group_items(group_key) if group_key in self.group_keys() else [
            a.name for a in self.alternatives
        ]
        existing = self.matrices.get(group_key)
        if existing is None or existing.items != items:
            resized = existing.reindex(items) if existing is not None else PCM.empty(items)
            self.matrices[group_key] = resized
        return self.matrices[group_key]

    # -- mutation: alternatives ---------------------------------------------------

    def add_alternative(self, name: str, description: str = "") -> None:
        self.alternatives.append(Alternative(name=name, description=description))
        if name not in self.direct_values.index:
            self.direct_values = self.direct_values.reindex(index=[*self.direct_values.index, name])

    def remove_alternative(self, name: str) -> None:
        self.alternatives = [a for a in self.alternatives if a.name != name]
        if name in self.direct_values.index:
            self.direct_values = self.direct_values.drop(index=name)

    def rename_alternative(self, old_name: str, new_name: str) -> None:
        if old_name == new_name:
            return
        for a in self.alternatives:
            if a.name == old_name:
                a.name = new_name
        if old_name in self.direct_values.index:
            self.direct_values = self.direct_values.rename(index={old_name: new_name})
        for leaf in self.leaf_criteria():
            if leaf.eval_mode == EvalMode.PAIRWISE and leaf.name in self.matrices:
                self.matrices[leaf.name].rename_item(old_name, new_name)

    # -- mutation: criteria tree ---------------------------------------------------

    def add_criterion(
        self, name: str, parent: str | None = None, eval_mode: EvalMode = EvalMode.PAIRWISE,
        direction: Direction = Direction.MAX,
    ) -> None:
        self.criteria.append(
            CriterionNode(name=name, parent=parent, eval_mode=eval_mode, direction=direction)
        )

    def descendants(self, name: str) -> list[str]:
        """Names of every node in ``name``'s sub-tree (children, grandchildren, ...)."""
        names = []
        for child in self.children(name):
            names.append(child.name)
            names.extend(self.descendants(child.name))
        return names

    def remove_criterion(self, name: str) -> None:
        to_remove = {name, *self.descendants(name)}
        self.criteria = [c for c in self.criteria if c.name not in to_remove]
        for removed in to_remove:
            self.matrices.pop(removed, None)
            self.direct_group_weights.pop(removed, None)
            if removed in self.direct_values.columns:
                self.direct_values = self.direct_values.drop(columns=removed)

    def rename_criterion(self, old_name: str, new_name: str) -> None:
        if old_name == new_name:
            return
        node = self.node_by_name(old_name)
        node.name = new_name
        for c in self.criteria:
            if c.parent == old_name:
                c.parent = new_name
        if old_name in self.matrices:
            self.matrices[new_name] = self.matrices.pop(old_name)
        parent_key = node.parent if node.parent is not None else ROOT_KEY
        parent_pcm = self.matrices.get(parent_key)
        if parent_pcm is not None:
            parent_pcm.rename_item(old_name, new_name)
        if old_name in self.direct_values.columns:
            self.direct_values = self.direct_values.rename(columns={old_name: new_name})
        if old_name in self.direct_group_weights:
            self.direct_group_weights[new_name] = self.direct_group_weights.pop(old_name)
