"""Weight aggregation and total-score computation, using the car-choice
example (ahp_core/sample.py) as the reference problem."""
from __future__ import annotations

import pytest

from ahp_core import hierarchy, pcm
from ahp_core.model import EvalMode, WeightMethod
from ahp_core.sample import car_choice_example


@pytest.fixture
def problem():
    return car_choice_example()


def test_leaf_weights_sum_to_one(problem):
    result = hierarchy.compute_hierarchy(problem)
    assert sum(result.leaf_weights.values()) == pytest.approx(1.0)


def test_alternative_scores_sum_to_one(problem):
    """Total scores are a weighted average of per-leaf evaluations, each of
    which sums to 1 across alternatives — so the scores themselves sum to 1."""
    result = hierarchy.compute_hierarchy(problem)
    assert sum(result.alternative_scores.values()) == pytest.approx(1.0)


def test_ranking_is_permutation_of_all_alternatives(problem):
    result = hierarchy.compute_hierarchy(problem)
    assert sorted(result.ranking) == ["A", "B", "C"]


def test_direct_price_weights_are_reciprocal_normalized(problem):
    price = problem.node_by_name("Ár")
    weights = hierarchy.direct_alternative_weights(problem, price)
    prices = {"A": 2_500_000.0, "B": 3_800_000.0, "C": 2_600_000.0}
    inv_total = sum(1 / p for p in prices.values())
    for name, p in prices.items():
        assert weights[name] == pytest.approx((1 / p) / inv_total)
    # cheapest car (A) must get the largest share since Price is minimized.
    assert weights["A"] > weights["B"] and weights["A"] > weights["C"]


def test_both_weight_methods_agree_since_every_matrix_here_is_at_most_3x3(problem):
    # Every PCM in this sample problem has 2 or 3 items, and for n<=3 the
    # eigenvector and LLSM methods always coincide exactly (test_pcm.py),
    # so the two global weight_method settings must produce the same result.
    problem.weight_method = WeightMethod.EIGENVECTOR
    em_result = hierarchy.compute_hierarchy(problem)
    problem.weight_method = WeightMethod.LLSM
    llsm_result = hierarchy.compute_hierarchy(problem)
    for name in em_result.leaf_weights:
        assert em_result.leaf_weights[name] == pytest.approx(llsm_result.leaf_weights[name], abs=1e-6)


def test_disconnected_matrix_raises(problem):
    matrix = problem.matrix_for("Költségek")
    # Clear every entry touching item 0 (Ár) so it's isolated from the rest.
    for j in range(1, matrix.size()):
        matrix.clear_value(0, j)
    with pytest.raises(pcm.DisconnectedMatrixError):
        hierarchy.compute_hierarchy(problem)


def test_eval_mode_switch_creates_direct_values_column(problem):
    problem.set_group_eval_mode("Karbantartás", EvalMode.DIRECT)
    assert "Karbantartás" in problem.direct_values.columns


def test_direct_group_weighting_matches_equivalent_pcm(problem):
    """Felszereltség is direct-weighted 2:1 (Biztonsági:Kényelmi) in the sample
    — the exact ratio its (unused while direct) PCM also encodes — so results
    must be identical to a pairwise-only run using that PCM instead."""
    direct_result = hierarchy.compute_hierarchy(problem)

    problem.set_group_eval_mode("Felszereltség", EvalMode.PAIRWISE)
    pairwise_result = hierarchy.compute_hierarchy(problem)

    for name in ("Biztonsági felszereltség", "Kényelmi felszereltség"):
        assert direct_result.leaf_weights[name] == pytest.approx(pairwise_result.leaf_weights[name], abs=1e-9)


def test_direct_group_weights_sum_to_one():
    from ahp_core.model import ProblemData

    problem = ProblemData(name="tiny")
    problem.add_alternative("A")
    problem.add_alternative("B")
    problem.add_criterion("X")
    problem.add_criterion("Y")
    problem.direct_group_weights["X"] = 3.0
    problem.direct_group_weights["Y"] = 1.0
    weights = hierarchy.direct_group_weights(problem, "__root__")
    assert weights == pytest.approx({"X": 0.75, "Y": 0.25})


def test_root_direct_weighting():
    from ahp_core.model import ProblemData, ROOT_KEY

    problem = ProblemData(name="tiny", root_eval_mode=EvalMode.DIRECT)
    problem.add_alternative("A")
    problem.add_alternative("B")
    problem.add_criterion("X")
    problem.add_criterion("Y")
    problem.direct_group_weights["X"] = 1.0
    problem.direct_group_weights["Y"] = 3.0
    # X and Y are trivial 2-alternative PAIRWISE leaves — fill in their one
    # comparison so scoring doesn't fail on an empty (disconnected) matrix;
    # this test is about root-level direct weighting, not leaf scoring.
    problem.matrix_for("X").set_value(0, 1, 1.0)
    problem.matrix_for("Y").set_value(0, 1, 1.0)

    result = hierarchy.compute_hierarchy(problem)
    assert result.node_results[ROOT_KEY].local_weights == pytest.approx({"X": 0.25, "Y": 0.75})
    assert result.node_results[ROOT_KEY].pcm_result is None


def test_renaming_child_preserves_its_direct_weight(problem):
    problem.direct_group_weights["Biztonsági felszereltség"] = 5.0
    problem.rename_criterion("Biztonsági felszereltség", "Biztonság")
    assert problem.direct_group_weights.get("Biztonság") == 5.0
    assert "Biztonsági felszereltség" not in problem.direct_group_weights


def test_removing_child_drops_its_direct_weight(problem):
    problem.direct_group_weights["Kényelmi felszereltség"] = 7.0
    problem.remove_criterion("Kényelmi felszereltség")
    assert "Kényelmi felszereltség" not in problem.direct_group_weights
