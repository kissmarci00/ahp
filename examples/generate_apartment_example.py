"""Generates lakasvalasztas_4x4_pelda.xlsx: a second, richer worked example
(apartment choice, 4 alternatives) for exercising the Home page's Excel
*import*, kept deliberately separate from ahp_core/sample.py's car-choice
example so "Load example" is untouched.

Compared to the built-in car example (2 tree levels, 3 alternatives, always
fully filled in), this one demonstrates every matrix "shape" the app
supports at once, over a 3-level tree and 4 alternatives:
- a fully-filled, perfectly consistent leaf PCM (Rezsikoltseg),
- an incomplete-but-connected leaf PCM (Kozlekedes, 2 of 6 pairs missing —
  still solvable via the graph-Laplacian LLSM / CR-minimal completion),
- a deliberately inconsistent leaf PCM (Muszaki allapot, CR > 0.1),
- direct-value scoring leaves in both directions (Vetelar/MIN, Felszereltseg
  szinvonala/MAX),
- and direct weighting of a non-leaf's children (Allapot es felszereltseg).

Run directly (`python examples/generate_apartment_example.py`) to
regenerate the .xlsx after editing the numbers below.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np

from ahp_core import pcm as pcm_math
from ahp_core.io_utils import export_to_excel
from ahp_core.model import Direction, EvalMode, ProblemData

ALTERNATIVE_NAMES = ["L1", "L2", "L3", "L4"]

OUTPUT_PATH = Path(__file__).with_name("lakasvalasztas_4x4_pelda.xlsx")


def build() -> ProblemData:
    problem = ProblemData(
        name="Lakásválasztás (4 alternatíva, 3 szintű példa)",
        description="Négy lakás összehasonlítása egy háromszintű szempontfán — "
        "teljesen kitöltött, hiányosan kitöltött és inkonzisztens páros "
        "összehasonlítás mátrixot, valamint közvetlen súlyozást is bemutat.",
        goal_name="Lakásválasztás",
    )

    for name, desc in [
        ("L1", "1. lakás — belvárosi"),
        ("L2", "2. lakás — zöldövezeti"),
        ("L3", "3. lakás — újépítésű"),
        ("L4", "4. lakás — panelprogramos"),
    ]:
        problem.add_alternative(name, desc)

    # -- tree: 3 levels under the root ---------------------------------------
    problem.add_criterion("Ár és költségek")
    problem.add_criterion("Elhelyezkedés")
    problem.add_criterion("Állapot és felszereltség")

    problem.add_criterion("Vételár", parent="Ár és költségek", eval_mode=EvalMode.DIRECT, direction=Direction.MIN)
    problem.add_criterion("Rezsiköltség", parent="Ár és költségek")

    problem.add_criterion("Közlekedés", parent="Elhelyezkedés")
    problem.add_criterion("Környék", parent="Elhelyezkedés")
    problem.add_criterion("Zöldterület közelsége", parent="Környék")
    problem.add_criterion("Biztonság", parent="Környék")

    problem.add_criterion("Műszaki állapot", parent="Állapot és felszereltség")
    problem.add_criterion(
        "Felszereltség színvonala", parent="Állapot és felszereltség",
        eval_mode=EvalMode.DIRECT, direction=Direction.MAX,
    )

    def fill(group_key: str, matrix_values: list[list[float]]) -> None:
        matrix = problem.matrix_for(group_key)
        matrix.values[:, :] = np.array(matrix_values, dtype=float)

    # Root: Ár és költségek vs Elhelyezkedés vs Állapot és felszereltség —
    # realistic (not perfectly consistent), like a genuine judgment.
    fill("__root__", [[1, 2, 3], [1 / 2, 1, 2], [1 / 3, 1 / 2, 1]])

    # Non-leaf 2-child groups — small, consistent (CR is 0 by definition for n<=2).
    fill("Ár és költségek", [[1, 3], [1 / 3, 1]])
    fill("Elhelyezkedés", [[1, 1 / 2], [2, 1]])
    fill("Környék", [[1, 2], [1 / 2, 1]])

    # Direct weighting of a non-leaf's children, rather than pairwise comparison.
    problem.set_group_eval_mode("Állapot és felszereltség", EvalMode.DIRECT)
    problem.direct_group_weights["Műszaki állapot"] = 3.0
    problem.direct_group_weights["Felszereltség színvonala"] = 2.0

    # Rezsiköltség: fully filled, perfectly consistent (weights 8:4:2:1).
    fill("Rezsiköltség", [[1, 2, 4, 8], [1 / 2, 1, 2, 4], [1 / 4, 1 / 2, 1, 2], [1 / 8, 1 / 4, 1 / 2, 1]])

    # Zöldterület közelsége: fully filled, consistent (weights 9:3:1:3).
    fill("Zöldterület közelsége", [[1, 3, 9, 3], [1 / 3, 1, 3, 1], [1 / 9, 1 / 3, 1, 1 / 3], [1 / 3, 1, 3, 1]])

    # Biztonság: fully filled, consistent (weights 4:2:1:1).
    fill("Biztonság", [[1, 2, 4, 4], [1 / 2, 1, 2, 2], [1 / 4, 1 / 2, 1, 1], [1 / 4, 1 / 2, 1, 1]])

    # Közlekedés: consistent (weights 9:3:3:1) minus two entries, left missing
    # on purpose — the remaining 4 known pairs (L1-L2, L1-L4, L2-L3, L3-L4)
    # still form a connected 4-cycle, so it stays solvable.
    fill("Közlekedés", [[1, 3, 3, 9], [1 / 3, 1, 1, 3], [1 / 3, 1, 1, 3], [1 / 9, 1 / 3, 1 / 3, 1]])
    kozlekedes = problem.matrix_for("Közlekedés")
    kozlekedes.clear_value(0, 2)
    kozlekedes.clear_value(1, 3)

    # Műszaki állapot: deliberately inconsistent (contradictory judgments),
    # to demonstrate the CR warning badge (CR > 0.1, but not absurdly high).
    fill("Műszaki állapot", [[1, 3, 5, 2], [1 / 3, 1, 2, 4], [1 / 5, 1 / 2, 1, 3], [1 / 2, 1 / 4, 1 / 3, 1]])

    problem.direct_values = problem.direct_values.reindex(index=ALTERNATIVE_NAMES)
    problem.direct_values["Vételár"] = [45_000_000.0, 38_000_000.0, 52_000_000.0, 41_000_000.0]
    problem.direct_values["Felszereltség színvonala"] = [7.0, 9.0, 5.0, 8.0]

    return problem


def _report(problem: ProblemData) -> None:
    print(f"{'Matrix':32s} {'size':>5s} {'missing':>8s} {'CR':>10s}")
    for group_key in problem.all_pcm_group_keys():
        matrix = problem.matrix_for(group_key)
        label = "(root)" if group_key == "__root__" else group_key
        missing = len(matrix.missing_pairs())
        try:
            cr = f"{pcm_math.solve(matrix.values).cr:.4f}"
        except pcm_math.DisconnectedMatrixError:
            cr = "DISCONNECTED"
        print(f"{label:32s} {matrix.size():>5d} {missing:>8d} {cr:>10s}")


if __name__ == "__main__":
    problem = build()
    _report(problem)
    OUTPUT_PATH.write_bytes(export_to_excel(problem))
    print(f"\nWrote {OUTPUT_PATH}")
