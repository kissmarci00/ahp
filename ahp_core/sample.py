"""The car-choice example from AHP.pdf ("A legjobb autó kiválasztása"), used
as an in-app demo and as the reference dataset in tests/test_hierarchy.py.

Tree: Cél -> Költségek (Ár, Karbantartás, Fogyasztás), Esztétikum, Felszereltség
(Biztonsági felszereltség, Kényelmi felszereltség) -> three cars A, B, C.
Ár (Price) is set to DIRECT mode with a MIN direction, illustrating the GUI
spec's item 35 request ("inkább direkt módon adjuk meg, pl. pénzbeli
értéket") for scoring *alternatives*. Felszereltség is set to weigh its own
two children (Biztonsági/Kényelmi felszereltség) via direct weighting
instead of a PCM, illustrating AHP.pdf's own "közvetlen súlyozás" as a valid
alternative for weighing *criteria* too — every other node is pairwise.

The main-criteria matrix is exactly AHP.pdf's own worked numeric example
(Költségek 2x Esztétikum, 3x Felszereltség; Esztétikum = Felszereltség), CR
close to but not exactly 0 like a real judgment. Every other matrix here is
built to be perfectly consistent (CR = 0), so the sample reads cleanly by
default; users can edit any cell to explore inconsistency and incompleteness
themselves on the Data Entry page.
"""
from __future__ import annotations

import numpy as np

from ahp_core.model import Direction, EvalMode, ProblemData

ALTERNATIVE_NAMES = ["A", "B", "C"]


def car_choice_example() -> ProblemData:
    problem = ProblemData(
        name="Autóválasztás",
        description="A legjobb autó kiválasztása költségek, esztétikum és felszereltség szempontjai alapján.",
        goal_name="A legjobb autó kiválasztása",
    )

    for name, desc in [
        ("A", "Első autó"),
        ("B", "Második autó"),
        ("C", "Harmadik autó"),
    ]:
        problem.add_alternative(name, desc)

    problem.add_criterion("Költségek")
    problem.add_criterion("Esztétikum")
    problem.add_criterion("Felszereltség")

    problem.add_criterion("Ár", parent="Költségek", eval_mode=EvalMode.DIRECT, direction=Direction.MIN)
    problem.add_criterion("Karbantartás", parent="Költségek")
    problem.add_criterion("Fogyasztás", parent="Költségek")

    problem.add_criterion("Biztonsági felszereltség", parent="Felszereltség")
    problem.add_criterion("Kényelmi felszereltség", parent="Felszereltség")

    def fill(group_key: str, matrix_values: list[list[float]]) -> None:
        matrix = problem.matrix_for(group_key)
        matrix.values[:, :] = np.array(matrix_values, dtype=float)

    # Main criteria: Költségek, Esztétikum, Felszereltség — AHP.pdf's own example.
    fill("__root__", [[1, 2, 3], [1 / 2, 1, 1], [1 / 3, 1, 1]])

    # Cost's children: Ár, Karbantartás, Fogyasztás — consistent, weights 4:2:1.
    fill("Költségek", [[1, 2, 4], [1 / 2, 1, 2], [1 / 4, 1 / 2, 1]])

    # Features' children: Biztonsági, Kényelmi — consistent, weights 2:1 (kept as
    # a PCM too, so switching back to pairwise in the UI doesn't start blank).
    fill("Felszereltség", [[1, 2], [1 / 2, 1]])
    problem.set_group_eval_mode("Felszereltség", EvalMode.DIRECT)
    problem.direct_group_weights["Biztonsági felszereltség"] = 2.0
    problem.direct_group_weights["Kényelmi felszereltség"] = 1.0

    # Leaf criteria over alternatives A, B, C — all consistent.
    fill("Karbantartás", [[1, 4, 2], [1 / 4, 1, 1 / 2], [1 / 2, 2, 1]])            # A best
    fill("Fogyasztás", [[1, 1 / 2, 2], [2, 1, 4], [1 / 2, 1 / 4, 1]])              # B best
    fill("Esztétikum", [[1, 1 / 4, 1 / 2], [4, 1, 2], [2, 1 / 2, 1]])              # B best
    fill("Biztonsági felszereltség", [[1, 2, 1 / 2], [1 / 2, 1, 1 / 4], [2, 4, 1]])  # C best
    fill("Kényelmi felszereltség", [[1, 1 / 2, 2], [2, 1, 4], [1 / 2, 1 / 4, 1]])  # B best

    problem.direct_values = problem.direct_values.reindex(index=ALTERNATIVE_NAMES)
    problem.direct_values["Ár"] = [2_500_000.0, 3_800_000.0, 2_600_000.0]

    return problem
