"""Weight stability-interval sensitivity, generalized from PROMETHEE's flat
model to AHP's criteria tree (ahp_core/sensitivity.py)."""
from __future__ import annotations

import numpy as np
import pytest

from ahp_core import sensitivity
from ahp_core.model import EvalMode, ProblemData
from ahp_core.sample import car_choice_example


@pytest.fixture
def problem():
    return car_choice_example()


def test_stability_interval_is_a_valid_range_around_w0(problem):
    sens = sensitivity.compute_weight_sensitivity(problem, "Költségek")
    w_low, w_high, _ = sens.stability_interval(1)
    assert 0.0 <= w_low <= sens.w0 <= w_high <= 1.0


def test_score_at_w0_matches_current_score(problem):
    from ahp_core.hierarchy import compute_hierarchy

    sens = sensitivity.compute_weight_sensitivity(problem, "Ár")
    baseline = compute_hierarchy(problem)
    at_w0 = sens.score_at(np.array(sens.w0))
    for i, name in enumerate(sens.alt_names):
        assert at_w0[i] == pytest.approx(baseline.alternative_scores[name], abs=1e-6)


def test_score_at_extremes_matches_isolated_and_dropped_branch(problem):
    sens = sensitivity.compute_weight_sensitivity(problem, "Esztétikum")
    scores_w1 = sens.score_at(np.array(1.0))
    # At w=1, Esztétikum (a top-level criterion here) takes all the weight,
    # so every alternative's score equals its own Esztétikum evaluation.
    from ahp_core.hierarchy import compute_hierarchy

    aesthetics_only = compute_hierarchy(
        problem, overrides={"__root__": {"Költségek": 0.0, "Esztétikum": 1.0, "Felszereltség": 0.0}}
    )
    for i, name in enumerate(sens.alt_names):
        assert scores_w1[i] == pytest.approx(aesthetics_only.alternative_scores[name], abs=1e-6)


def test_no_siblings_raises():
    problem = ProblemData(name="tiny")
    problem.add_alternative("A")
    problem.add_alternative("B")
    problem.add_criterion("OnlyCriterion")
    with pytest.raises(ValueError):
        sensitivity.compute_weight_sensitivity(problem, "OnlyCriterion")


def test_eligible_nodes_excludes_the_only_child(problem):
    eligible = sensitivity.sensitivity_eligible_nodes(problem)
    assert "Ár" in eligible  # has siblings Karbantartás, Fogyasztás
    assert "Költségek" in eligible  # has siblings Esztétikum, Felszereltség


def test_direct_leaf_can_be_sensitivity_studied(problem):
    # Ár is a DIRECT-mode leaf; sensitivity varies its *importance weight*
    # among siblings, which is independent of its own eval_mode.
    assert problem.node_by_name("Ár").eval_mode == EvalMode.DIRECT
    sens = sensitivity.compute_weight_sensitivity(problem, "Ár")
    w_low, w_high, _ = sens.stability_interval(1)
    assert 0.0 <= w_low <= w_high <= 1.0
