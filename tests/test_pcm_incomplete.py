"""Regression test: the 8x8 not-fully-filled-in example from pcmc_fidelity.py
(itself a line-by-line port of the course's PCMC.m) must produce the exact
same numbers after the refactor into ahp_core/pcm.py. Reference values below
were captured by running pcmc_fidelity.py's main() directly."""
from __future__ import annotations

import numpy as np
import pytest

from ahp_core import pcm

NAN = np.nan
MATRIX = np.array(
    [
        [1, 5, 3, 7, 6, 6, 1 / 3, 1 / 4],
        [0.2, 1, NAN, 5, NAN, 3, NAN, 1 / 7],
        [1 / 3, NAN, 1, NAN, 3, NAN, 6, NAN],
        [1 / 7, 0.2, NAN, 1, NAN, 1 / 4, NAN, 1 / 8],
        [1 / 6, NAN, 1 / 3, NAN, 1, NAN, 1 / 5, NAN],
        [1 / 6, 1 / 3, NAN, 4, NAN, 1, NAN, 1 / 6],
        [3, NAN, 1 / 6, NAN, 5, NAN, 1, NAN],
        [4, 7, NAN, 8, NAN, 6, NAN, 1],
    ]
)

REFERENCE_LLSM = np.array(
    [0.17695001, 0.06764308, 0.17695001, 0.01967774, 0.03670728, 0.04145205, 0.14216667, 0.33845317]
)
REFERENCE_EM = np.array(
    [0.18936942, 0.05668156, 0.21161479, 0.01749307, 0.0319336, 0.03535574, 0.15092725, 0.30662458]
)
REFERENCE_LAMBDA_MAX = 9.298092250426718
REFERENCE_CR = 0.1320541455164515


def test_graph_is_connected():
    assert pcm.is_connected(MATRIX)


def test_llsm_matches_pcmc_fidelity_reference():
    result = pcm.solve(MATRIX)
    np.testing.assert_allclose(result.weights_llsm, REFERENCE_LLSM, atol=1e-6)


def test_eigenvector_cr_minimal_completion_matches_pcmc_fidelity_reference():
    result = pcm.solve(MATRIX)
    assert not result.was_complete
    np.testing.assert_allclose(result.lambda_max, REFERENCE_LAMBDA_MAX, atol=1e-3)
    assert result.cr == pytest.approx(REFERENCE_CR, abs=1e-3)
    np.testing.assert_allclose(result.weights_eigenvector, REFERENCE_EM, atol=2e-3)
