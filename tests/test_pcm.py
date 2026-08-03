"""PCM math on known matrices, several taken directly from AHP.pdf's own
worked examples (pages 3-6): a perfectly consistent matrix, an inconsistent
one, and the "eigenvector and LLSM always agree for n=3" fact."""
from __future__ import annotations

import numpy as np
import pytest

from ahp_core import pcm

CONSISTENT_4x4 = np.array(
    [[1, 2, 4, 12], [1 / 2, 1, 2, 6], [1 / 4, 1 / 2, 1, 3], [1 / 12, 1 / 6, 1 / 3, 1]]
)

INCONSISTENT_4x4 = np.array(
    [[1, 2, 5, 12], [1 / 2, 1, 2, 6], [1 / 5, 1 / 2, 1, 3], [1 / 12, 1 / 6, 1 / 3, 1]]
)

INCONSISTENT_3x3 = np.array([[1, 2, 5], [1 / 2, 1, 3], [1 / 5, 1 / 3, 1]])


def test_consistent_matrix_has_zero_cr():
    result = pcm.solve(CONSISTENT_4x4)
    assert result.cr == pytest.approx(0.0, abs=1e-9)
    np.testing.assert_allclose(result.lambda_max, 4.0, atol=1e-9)


def test_consistent_matrix_weights_proportional_to_12_6_3_1():
    result = pcm.solve(CONSISTENT_4x4)
    expected = np.array([12, 6, 3, 1]) / 22
    np.testing.assert_allclose(result.weights_eigenvector, expected, atol=1e-6)
    np.testing.assert_allclose(result.weights_llsm, expected, atol=1e-6)


def test_inconsistent_matrix_has_positive_cr():
    result = pcm.solve(INCONSISTENT_4x4)
    assert result.cr > 0.0


def test_eigenvector_and_llsm_agree_for_3x3():
    """AHP.pdf: for a 3x3 matrix the two methods always coincide, consistent or not."""
    result = pcm.solve(INCONSISTENT_3x3)
    np.testing.assert_allclose(result.weights_eigenvector, result.weights_llsm, atol=1e-6)


def test_eigenvector_and_llsm_generally_differ_for_larger_inconsistent_matrices():
    result = pcm.solve(INCONSISTENT_4x4)
    # Not identical (n > 3 and inconsistent) — even though this matrix is only
    # mildly inconsistent, so the two vectors land close together.
    assert not np.allclose(result.weights_eigenvector, result.weights_llsm, atol=1e-5)


def test_weights_sum_to_one():
    for matrix in (CONSISTENT_4x4, INCONSISTENT_4x4, INCONSISTENT_3x3):
        result = pcm.solve(matrix)
        assert result.weights_eigenvector.sum() == pytest.approx(1.0)
        assert result.weights_llsm.sum() == pytest.approx(1.0)


def test_disconnected_graph_is_detected():
    values = np.full((4, 4), np.nan)
    np.fill_diagonal(values, 1.0)
    values[0, 1] = 2.0
    values[1, 0] = 0.5
    values[2, 3] = 3.0
    values[3, 2] = 1 / 3
    # {0,1} and {2,3} are two separate connected components.
    assert not pcm.is_connected(values)
    with pytest.raises(pcm.DisconnectedMatrixError):
        pcm.solve(values)


def test_spanning_tree_is_connected_and_solvable():
    values = np.full((4, 4), np.nan)
    np.fill_diagonal(values, 1.0)
    for i, j, v in [(0, 1, 2.0), (1, 2, 3.0), (2, 3, 1.5)]:
        values[i, j] = v
        values[j, i] = 1 / v
    assert pcm.is_connected(values)
    result = pcm.solve(values)
    assert not result.was_complete
    assert result.weights_eigenvector.sum() == pytest.approx(1.0)


def test_two_by_two_is_always_perfectly_consistent():
    values = np.array([[1.0, 7.0], [1 / 7, 1.0]])
    result = pcm.solve(values)
    assert result.cr == 0.0
    np.testing.assert_allclose(result.weights_eigenvector, [7 / 8, 1 / 8], atol=1e-6)
