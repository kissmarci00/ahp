"""Excel round-trip for AHP problems (ahp_core/io_utils.py)."""
from __future__ import annotations

import io

import pytest

from ahp_core import hierarchy, io_utils
from ahp_core.model import EvalMode
from ahp_core.sample import car_choice_example


@pytest.fixture
def problem():
    return car_choice_example()


def test_round_trip_preserves_tree_and_matrices(problem):
    data = io_utils.export_to_excel(problem)
    imported, notes = io_utils.import_from_excel(io.BytesIO(data))

    assert notes == []
    assert imported.name == problem.name
    assert {a.name for a in imported.alternatives} == {a.name for a in problem.alternatives}
    assert {c.name for c in imported.criteria} == {c.name for c in problem.criteria}
    assert imported.node_by_name("Ár").eval_mode == EvalMode.DIRECT
    assert imported.node_by_name("Ár").parent == "Költségek"
    assert imported.goal_name == problem.goal_name
    assert imported.root_eval_mode == problem.root_eval_mode
    assert imported.node_by_name("Felszereltség").eval_mode == EvalMode.DIRECT
    assert imported.direct_group_weights["Biztonsági felszereltség"] == pytest.approx(
        problem.direct_group_weights["Biztonsági felszereltség"]
    )
    assert imported.direct_group_weights["Kényelmi felszereltség"] == pytest.approx(
        problem.direct_group_weights["Kényelmi felszereltség"]
    )

    for group_key in problem.all_pcm_group_keys():
        original = problem.matrix_for(group_key)
        restored = imported.matrix_for(group_key)
        assert restored.items == original.items
        for i in range(original.size()):
            for j in range(original.size()):
                orig_v, rest_v = original.values[i, j], restored.values[i, j]
                if orig_v != orig_v:  # NaN
                    assert rest_v != rest_v
                else:
                    assert rest_v == pytest.approx(orig_v)


def test_round_trip_preserves_scores(problem):
    data = io_utils.export_to_excel(problem)
    imported, _ = io_utils.import_from_excel(io.BytesIO(data))
    original_result = hierarchy.compute_hierarchy(problem)
    imported_result = hierarchy.compute_hierarchy(imported)
    for name in original_result.alternative_scores:
        assert imported_result.alternative_scores[name] == pytest.approx(
            original_result.alternative_scores[name], abs=1e-6
        )


def test_missing_required_sheet_raises(problem):
    data = io_utils.export_to_excel(problem)
    import openpyxl

    workbook = openpyxl.load_workbook(io.BytesIO(data))
    del workbook["Alternatives"]
    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    with pytest.raises(ValueError, match="Alternatives"):
        io_utils.import_from_excel(buffer)


def test_unknown_parent_reference_raises(problem):
    data = io_utils.export_to_excel(problem)
    import openpyxl

    workbook = openpyxl.load_workbook(io.BytesIO(data))
    sheet = workbook["Criteria"]
    header = [cell.value for cell in sheet[1]]
    parent_col = header.index("parent") + 1
    sheet.cell(row=2, column=parent_col, value="NoSuchCriterion")
    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    with pytest.raises(ValueError, match="NoSuchCriterion"):
        io_utils.import_from_excel(buffer)
