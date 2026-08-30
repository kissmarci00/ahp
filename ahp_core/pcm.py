"""Pairwise-comparison matrix (PCM) math: graph connectivity, the eigenvector
method, the LLSM (logarithmic least squares / geometric mean) method, the CR
consistency index, and the not-fully-filled-in extensions of all of these.

The numerical algorithms — notably the CR-minimal completion by 20 sweeps of
single-entry fminbound optimization, and the graph-Laplacian closed form for
incomplete LLSM — follow the standard AHP formulations for these methods.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import fminbound

# Average lambda_max of random n x n reciprocal matrices (entries drawn
# uniformly from {1/9, ..., 1/2, 1, 2, ..., 9}), used to define
# CR = (lambda_max - n) / (AVG_LAMBDA_MAX[n] - n). n=2 is always perfectly
# consistent (CR=0) and isn't in the table.
AVG_LAMBDA_MAX: dict[int, float] = {
    3: 4.049, 4: 6.652, 5: 9.435, 6: 12.245,
    7: 15.045, 8: 17.830, 9: 20.605, 10: 23.373,
}

MAX_SUPPORTED_SIZE = max(AVG_LAMBDA_MAX)


class DisconnectedMatrixError(Exception):
    """Raised when a PCM's comparison graph is not connected, so a weight
    vector can't be recovered.

    ``group_keys`` (which matrices are disconnected) is set by hierarchy.py,
    so a page can build a localized message instead of using this
    exception's own bilingual ``str()`` — pcm.py has no i18n dependency and
    doesn't know which group a bare matrix belongs to."""

    def __init__(self, message: str, group_keys: list[str] | None = None) -> None:
        super().__init__(message)
        self.group_keys = group_keys


def is_connected(values: np.ndarray) -> bool:
    """Whether the comparison graph (an edge wherever an entry is known) is
    connected — the condition for a unique weight vector to exist."""
    n = values.shape[0]
    if n <= 1:
        return True
    visited = {0}
    frontier = [0]
    while frontier:
        node = frontier.pop()
        for other in range(n):
            if other != node and other not in visited and not np.isnan(values[node, other]):
                visited.add(other)
                frontier.append(other)
    return len(visited) == n


def eigenvector_weights(values: np.ndarray) -> tuple[np.ndarray, float]:
    """Saaty's eigenvector method for a fully completed matrix: the right
    eigenvector of the dominant (Perron) eigenvalue, normalized to sum to 1.
    Returns (w, lambda_max)."""
    if np.isnan(values).any():
        raise ValueError("eigenvector_weights requires a fully completed matrix")
    n = values.shape[0]
    if n == 1:
        return np.array([1.0]), 1.0
    eigvals, eigvecs = np.linalg.eig(values)
    lambda_max = eigvals[np.argmax(np.abs(eigvals))].real
    which = int(np.argmin(np.abs(eigvals - lambda_max)))
    vec = np.abs(eigvecs[:, which].real)
    return vec / vec.sum(), lambda_max


def llsm_weights_complete(values: np.ndarray) -> np.ndarray:
    """Closed-form LLSM solution for a fully completed matrix: each weight is
    the geometric mean of its row, normalized to sum to 1."""
    n = values.shape[0]
    row_products = np.prod(values, axis=1)
    w = row_products ** (1.0 / n)
    return w / w.sum()


def llsm_weights_incomplete(values: np.ndarray) -> np.ndarray:
    """Closed-form LLSM solution for a (connected but possibly incomplete)
    matrix, via the graph-Laplacian linear system: fix the last item as the
    log-weight reference (w_n = 1), solve for the rest, then normalize.
    Works for complete matrices too, but llsm_weights_complete is simpler/faster
    for that case."""
    n = values.shape[0]
    if n == 1:
        return np.array([1.0])
    L = np.zeros((n - 1, n - 1))
    for i in range(n - 1):
        degree = n - 1
        for j in range(n):
            if i != j and np.isnan(values[i, j]):
                degree -= 1
        L[i, i] = degree
    for i in range(n - 2):
        for j in range(i + 1, n - 1):
            if not np.isnan(values[i, j]):
                L[i, j] = -1
                L[j, i] = -1

    filled = np.where(np.isnan(values), 1.0, values)
    rhs = np.zeros((n - 1, 1))
    for j in range(n - 1):
        rhs[j, 0] = -np.log(np.prod(filled[:, j]))

    y = np.linalg.solve(L, rhs)
    w = np.append(np.exp(y).flatten(), 1.0)
    return w / w.sum()


def _lambda_max_of(matrix: np.ndarray) -> float:
    eigvals = np.linalg.eigvals(matrix)
    return eigvals[np.argmax(np.abs(eigvals))].real


def complete_min_cr(
    values: np.ndarray, missing_pairs: list[tuple[int, int]], sweeps: int = 20
) -> np.ndarray:
    """Fill in the missing entries to (approximately) minimize lambda_max, by
    block-coordinate descent: repeatedly 1D-optimize each missing entry (in
    log-scale, so the reciprocal constraint holds automatically) holding
    every other entry fixed, sweeping through all missing pairs ``sweeps``
    times."""
    M = values.copy()
    for i, j in missing_pairs:
        M[i, j] = 1.0
        M[j, i] = 1.0

    for _ in range(sweeps):
        for i, j in missing_pairs:
            def objective(t: float, i=i, j=j) -> float:
                candidate = M.copy()
                candidate[i, j] = np.exp(t)
                candidate[j, i] = np.exp(-t)
                return _lambda_max_of(candidate)

            t_star = fminbound(objective, -10, 10, xtol=1e-4)
            M[i, j] = np.exp(t_star)
            M[j, i] = np.exp(-t_star)
    return M


def cr_value(lambda_max: float, n: int) -> float:
    if n <= 2:
        return 0.0
    if n > MAX_SUPPORTED_SIZE:
        raise ValueError(
            f"No average-lambda-max reference value for a {n}x{n} matrix "
            f"(supported sizes: 3-{MAX_SUPPORTED_SIZE})."
        )
    # lambda_max >= n always (Perron-Frobenius), so CR is never negative in
    # theory; clamp floating-point noise near perfect consistency so it
    # doesn't display as "-0.0000".
    return max(0.0, (lambda_max - n) / (AVG_LAMBDA_MAX[n] - n))


@dataclass
class PCMResult:
    weights_eigenvector: np.ndarray
    weights_llsm: np.ndarray
    lambda_max: float
    cr: float
    completed_matrix: np.ndarray  # the matrix the eigenvector method actually used
    was_complete: bool

    def weights_for(self, method) -> np.ndarray:
        from ahp_core.model import WeightMethod
        return self.weights_eigenvector if method == WeightMethod.EIGENVECTOR else self.weights_llsm


def solve(values: np.ndarray) -> PCMResult:
    """Compute both weight vectors, lambda_max and CR for a PCM, handling the
    incomplete case (CR-minimal completion for the eigenvector method, the
    graph-Laplacian closed form for LLSM) transparently. Raises
    DisconnectedMatrixError if the comparison graph isn't connected."""
    n = values.shape[0]
    if not is_connected(values):
        raise DisconnectedMatrixError(
            "A páros összehasonlítás mátrix reprezentáló gráfja nem összefüggő — "
            "adjon meg további összehasonlításokat. / "
            "The comparison graph for this matrix is not connected — please add more comparisons."
        )

    missing = [
        (i, j) for i in range(n) for j in range(i + 1, n) if np.isnan(values[i, j])
    ]
    was_complete = not missing
    completed = values if was_complete else complete_min_cr(values, missing)
    weights_em, lambda_max = eigenvector_weights(completed)
    weights_llsm = llsm_weights_complete(completed) if was_complete else llsm_weights_incomplete(values)
    cr = cr_value(lambda_max, n)
    return PCMResult(
        weights_eigenvector=weights_em, weights_llsm=weights_llsm, lambda_max=lambda_max,
        cr=cr, completed_matrix=completed, was_complete=was_complete,
    )
