"""Aggregating the criteria tree into a single ranking of alternatives.

Each node's PCM gives local weights over its children. A criterion's global
weight is its local weight multiplied down the chain of its ancestors'
local weights (root = 1). Leaf global weights, renormalized to sum to 1,
are the w_k in the total-score formula:

    T_i = sum_k w_k * e_ki

where e_ki is alternative i's evaluation on leaf k.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from ahp_core import pcm as pcm_math
from ahp_core.model import ROOT_KEY, CriterionNode, Direction, EvalMode, ProblemData


@dataclass
class NodeResult:
    group_key: str
    items: list[str]
    local_weights: dict[str, float]
    pcm_result: pcm_math.PCMResult | None  # None when there's only a single item (no comparison needed)


@dataclass
class HierarchyResult:
    node_results: dict[str, NodeResult]
    global_criterion_weights: dict[str, float]  # every criterion, raw
    leaf_weights: dict[str, float]  # every leaf, renormalized to sum 1
    alternative_scores: dict[str, float]
    ranking: list[str]  # alternative names, best first


def direct_group_weights(problem: ProblemData, group_key: str) -> dict[str, float]:
    """Normalized weight of every child in a DIRECT-mode group ("közvetlen
    súlyozás" instead of a PCM). No min/max direction here, unlike
    direct_alternative_weights — a bigger value always means more
    importance."""
    items = problem.group_items(group_key)
    raw = {name: problem.direct_group_weights.get(name, 0.0) for name in items}
    total = sum(raw.values())
    if total <= 0:
        n = len(items)
        return {name: (1.0 / n if n else 0.0) for name in items}
    return {name: v / total for name, v in raw.items()}


def _matrix_labels(group_key: str) -> tuple[str, str]:
    if group_key == ROOT_KEY:
        return "a főszempontok", "the main criteria"
    return f"„{group_key}”", f"'{group_key}'"


def _disconnected_matrix_error(group_keys: list[str]) -> pcm_math.DisconnectedMatrixError:
    """Bilingual fallback error naming every disconnected matrix at once. The
    exception also carries ``group_keys`` raw, so a page can build its own
    localized message instead (see DisconnectedMatrixError)."""
    hu_labels = [_matrix_labels(k)[0] for k in group_keys]
    en_labels = [_matrix_labels(k)[1] for k in group_keys]
    if len(group_keys) == 1:
        message = (
            f"A(z) {hu_labels[0]} páros összehasonlítás mátrixának reprezentáló gráfja nem "
            f"összefüggő — adjon meg további összehasonlításokat. / "
            f"The {en_labels[0]} comparison matrix's graph is not connected — please add "
            f"more comparisons."
        )
    else:
        message = (
            f"A következő páros összehasonlítás mátrixok reprezentáló gráfja nem összefüggő: "
            f"{', '.join(hu_labels)} — adjon meg további összehasonlításokat mindegyiknél. / "
            f"The comparison graph is not connected for these matrices: {', '.join(en_labels)} "
            f"— please add more comparisons for each."
        )
    return pcm_math.DisconnectedMatrixError(message, group_keys=group_keys)


def find_disconnected_matrices(problem: ProblemData) -> list[str]:
    """Every currently-PAIRWISE group whose comparison graph isn't connected,
    so compute_hierarchy can report all of them at once."""
    disconnected = []
    for group_key in problem.all_pcm_group_keys():
        matrix = problem.matrix_for(group_key)
        if matrix.size() >= 2 and not pcm_math.is_connected(matrix.values):
            disconnected.append(group_key)
    return disconnected


def compute_node_result(
    problem: ProblemData, group_key: str, override: dict[str, float] | None = None
) -> NodeResult:
    """Solve a single group's weights (PCM, direct entry, or an override),
    exposed separately so pages can inspect one group without running the
    full aggregation."""
    items = problem.group_items(group_key) if group_key in problem.group_keys() else problem.matrix_for(group_key).items
    if override is not None:
        return NodeResult(group_key=group_key, items=items, local_weights=dict(override), pcm_result=None)
    if len(items) <= 1:
        local = {items[0]: 1.0} if items else {}
        return NodeResult(group_key=group_key, items=items, local_weights=local, pcm_result=None)
    if problem.node_eval_mode(group_key) == EvalMode.DIRECT:
        local = direct_group_weights(problem, group_key)
        return NodeResult(group_key=group_key, items=items, local_weights=local, pcm_result=None)
    matrix = problem.matrix_for(group_key)
    try:
        result = pcm_math.solve(matrix.values)
    except pcm_math.DisconnectedMatrixError:
        raise _disconnected_matrix_error([group_key]) from None
    weights = result.weights_for(problem.weight_method)
    return NodeResult(
        group_key=group_key, items=matrix.items,
        local_weights=dict(zip(matrix.items, weights)), pcm_result=result,
    )


def direct_alternative_weights(problem: ProblemData, leaf: CriterionNode) -> dict[str, float]:
    """Normalized weight of every alternative on a DIRECT-rating leaf, from its
    raw values: proportional to the value for a maximized leaf, proportional
    to the reciprocal for a minimized one (e.g. cost)."""
    alt_names = [a.name for a in problem.alternatives]
    if leaf.name in problem.direct_values.columns:
        values = problem.direct_values[leaf.name].reindex(alt_names).fillna(0.0).astype(float)
    else:
        values = pd.Series(0.0, index=alt_names)

    if leaf.direction == Direction.MAX:
        raw = values
    else:
        if (values <= 0).any():
            raise ValueError(
                f"'{leaf.name}': a minimalizálandó közvetlen értékeknek pozitívnak kell lenniük "
                f"a reciprok-normalizáláshoz. / '{leaf.name}': minimized direct-rating values "
                f"must all be positive to invert."
            )
        raw = 1.0 / values

    total = raw.sum()
    if total <= 0:
        n = len(alt_names)
        return {name: (1.0 / n if n else 0.0) for name in alt_names}
    return (raw / total).to_dict()


def compute_hierarchy(
    problem: ProblemData, overrides: dict[str, dict[str, float]] | None = None
) -> HierarchyResult:
    """Run the full AHP computation: local weights at every node, global
    criterion weights, leaf weights, and the alternatives' total scores and
    ranking. Raises pcm.DisconnectedMatrixError if any matrix's comparison
    graph isn't connected.

    ``overrides`` forces a group's local weights to a given dict instead of
    solving its PCM — used by sensitivity.py to test "what if this weight
    were w" without duplicating the aggregation logic."""
    disconnected = find_disconnected_matrices(problem)
    if disconnected:
        raise _disconnected_matrix_error(disconnected)

    overrides = overrides or {}
    node_results: dict[str, NodeResult] = {}

    def node_result(group_key: str) -> NodeResult:
        if group_key not in node_results:
            node_results[group_key] = compute_node_result(problem, group_key, overrides.get(group_key))
        return node_results[group_key]

    global_weights: dict[str, float] = {}

    def recurse(group_key: str, parent_global: float) -> None:
        for child_name, local_w in node_result(group_key).local_weights.items():
            child = problem.node_by_name(child_name)
            g = parent_global * local_w
            global_weights[child_name] = g
            if not problem.is_leaf(child):
                recurse(child_name, g)

    recurse(ROOT_KEY, 1.0)

    leaves = problem.leaf_criteria()
    raw_leaf = {c.name: global_weights.get(c.name, 0.0) for c in leaves}
    total_leaf = sum(raw_leaf.values())
    if total_leaf > 0:
        leaf_weights = {name: v / total_leaf for name, v in raw_leaf.items()}
    else:
        n = len(leaves)
        leaf_weights = {c.name: (1.0 / n if n else 0.0) for c in leaves}

    alt_names = [a.name for a in problem.alternatives]
    scores = {name: 0.0 for name in alt_names}
    for leaf in leaves:
        if leaf.eval_mode == EvalMode.DIRECT:
            eval_weights = direct_alternative_weights(problem, leaf)
        else:
            eval_weights = node_result(leaf.name).local_weights
        w_leaf = leaf_weights.get(leaf.name, 0.0)
        for name in alt_names:
            scores[name] += w_leaf * eval_weights.get(name, 0.0)

    ranking = sorted(alt_names, key=lambda name: scores[name], reverse=True)

    return HierarchyResult(
        node_results=node_results, global_criterion_weights=global_weights,
        leaf_weights=leaf_weights, alternative_scores=scores, ranking=ranking,
    )
