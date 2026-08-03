"""Excel import/export for AHP problems.

Six sheets round-trip the full problem:

- **Meta**: name, description, goal_name, weight_method, root_eval_mode.
- **Alternatives**: name, description, color.
- **Criteria**: the tree, flattened — name, parent (blank = top-level/main
  criterion), eval_mode (how it weighs its children if a non-leaf, or scores
  alternatives if a leaf), direction (only meaningful for a DIRECT leaf),
  color.
- **PairwiseComparisons**: every matrix stacked in one sheet, each as its own
  labeled grid — a one-cell label row (the criterion name, or "(root)" for
  the main-criteria matrix), then a header row of item names, then one row
  per item with its comparison values, then a blank row before the next
  matrix. This is the exact shape a pairwise comparison matrix is always
  shown in (row item vs. column item), so the sheet reads and hand-edits
  like the real thing instead of a database-style row list.
- **DirectValues**: leaf, alternative, value — raw values for DIRECT-mode leaves.
- **DirectWeights**: group, child, value — raw values for a DIRECT-mode root
  or non-leaf criterion weighing its children (AHP.pdf's "közvetlen
  súlyozás"). ``group`` is informational only (blank = root); values are
  keyed by child name, which is unique across the whole tree.

Import is deliberately lenient about hand-edited files, following the same
philosophy as the PROMETHEE Playground's io_utils.py: a missing optional
column or a blank cell gets the same default the Problem Setup page would
use, reported back as a note rather than raising. Only a missing name, a
duplicate name, an unparseable value, or a reference to an unknown item
fails the import, with a message identifying the sheet/row/column at fault.
"""
from __future__ import annotations

import io
from typing import Callable

import numpy as np
import pandas as pd

from ahp_core.model import (
    Alternative,
    CriterionNode,
    Direction,
    EvalMode,
    ProblemData,
    ROOT_KEY,
    WeightMethod,
)

REQUIRED_SHEETS = ("Meta", "Alternatives", "Criteria")
OPTIONAL_SHEETS = ("PairwiseComparisons", "DirectValues", "DirectWeights")


def export_to_excel(problem: ProblemData) -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        meta_df = pd.DataFrame(
            {
                "key": ["name", "description", "goal_name", "weight_method", "root_eval_mode"],
                "value": [
                    problem.name, problem.description, problem.goal_name,
                    problem.weight_method.value, problem.root_eval_mode.value,
                ],
            }
        )
        meta_df.to_excel(writer, sheet_name="Meta", index=False)

        pd.DataFrame(
            [
                {"name": a.name, "description": a.description, "color": a.color}
                for a in problem.alternatives
            ]
        ).to_excel(writer, sheet_name="Alternatives", index=False)

        pd.DataFrame(
            [
                {
                    "name": c.name,
                    "parent": c.parent or "",
                    "eval_mode": c.eval_mode.value,
                    "direction": c.direction.value,
                    "color": c.color,
                }
                for c in problem.criteria
            ]
        ).to_excel(writer, sheet_name="Criteria", index=False)

        _write_pcm_sheet(writer, problem)

        direct_rows = []
        for leaf in problem.direct_leaf_criteria():
            for alt in problem.alternatives:
                value = 0.0
                if alt.name in problem.direct_values.index and leaf.name in problem.direct_values.columns:
                    value = problem.direct_values.loc[alt.name, leaf.name]
                direct_rows.append({"leaf": leaf.name, "alternative": alt.name, "value": value})
        pd.DataFrame(direct_rows).to_excel(writer, sheet_name="DirectValues", index=False)

        weight_rows = []
        for group_key in problem.direct_weight_group_keys():
            group_label = "" if group_key == ROOT_KEY else group_key
            for child in problem.group_items(group_key):
                weight_rows.append(
                    {"group": group_label, "child": child, "value": problem.direct_group_weights.get(child, 0.0)}
                )
        pd.DataFrame(weight_rows).to_excel(writer, sheet_name="DirectWeights", index=False)

    return buffer.getvalue()


def _group_label(group_key: str) -> str:
    return "(root)" if group_key == ROOT_KEY else group_key


def _write_pcm_sheet(writer: pd.ExcelWriter, problem: ProblemData) -> None:
    """One grid per matrix, stacked top to bottom: a label cell, a header row
    of item names, then one row per item — the plain row/column shape a
    pairwise comparison matrix is always drawn in. A blank cell is a missing
    entry; both triangles are written (redundant with each other, but that's
    exactly how the matrix already reads on the Data Entry page)."""
    sheet = writer.book.create_sheet("PairwiseComparisons")
    row = 1
    for group_key in problem.all_pcm_group_keys():
        matrix = problem.matrix_for(group_key)
        if matrix.size() < 2:
            continue
        sheet.cell(row=row, column=1, value=_group_label(group_key))
        row += 1
        for j, name in enumerate(matrix.items):
            sheet.cell(row=row, column=2 + j, value=name)
        row += 1
        for i, name in enumerate(matrix.items):
            sheet.cell(row=row, column=1, value=name)
            for j in range(matrix.size()):
                value = matrix.values[i, j]
                if not np.isnan(value):
                    sheet.cell(row=row, column=2 + j, value=float(value))
            row += 1
        row += 1  # blank separator row before the next matrix


def _cast_eval_mode(value) -> EvalMode:
    try:
        return EvalMode(str(value).strip().lower())
    except ValueError:
        valid = ", ".join(m.value for m in EvalMode)
        raise ValueError(f"'{value}' is not a valid eval_mode (expected one of: {valid}).") from None


def _cast_direction(value) -> Direction:
    try:
        return Direction(str(value).strip().lower())
    except ValueError:
        valid = ", ".join(d.value for d in Direction)
        raise ValueError(f"'{value}' is not a valid direction (expected one of: {valid}).") from None


def _cast_weight_method(value) -> WeightMethod:
    try:
        return WeightMethod(str(value).strip().lower())
    except ValueError:
        valid = ", ".join(m.value for m in WeightMethod)
        raise ValueError(f"'{value}' is not a valid weight_method (expected one of: {valid}).") from None


def _read_column(df: pd.DataFrame, col: str, cast: Callable, default, label: str, sheet: str, notes: list[str]):
    n = len(df)
    if col not in df.columns:
        notes.append(f"{sheet} sheet: no '{label}' column — used the default ({default}) for every row.")
        return [default] * n
    values, blank_rows = [], []
    for i, raw in enumerate(df[col]):
        if pd.isna(raw):
            values.append(default)
            blank_rows.append(i + 2)
            continue
        try:
            values.append(cast(raw))
        except ValueError as exc:
            raise ValueError(f"{sheet} sheet, row {i + 2}, column '{label}': {exc}") from exc
    if blank_rows:
        rows_text = ", ".join(str(r) for r in blank_rows)
        notes.append(f"{sheet} sheet: '{label}' was blank in row(s) {rows_text} — used the default ({default}).")
    return values


def _optional_str_column(df: pd.DataFrame, col: str, default: str = "") -> list[str]:
    if col not in df.columns:
        return [default] * len(df)
    return [str(v) if pd.notna(v) else default for v in df[col]]


def _required_name_column(df: pd.DataFrame, sheet: str) -> list[str]:
    if "name" not in df.columns:
        raise ValueError(f"The {sheet} sheet is missing a 'name' column.")
    names = []
    for i, raw in enumerate(df["name"]):
        if pd.isna(raw) or str(raw).strip() == "":
            raise ValueError(f"{sheet} sheet, row {i + 2}: every row needs a name.")
        names.append(str(raw))
    seen: set[str] = set()
    for i, name in enumerate(names):
        if name in seen:
            raise ValueError(f"{sheet} sheet, row {i + 2}: duplicate name '{name}'.")
        seen.add(name)
    return names


def _read_pcm_sheet(xls: pd.ExcelFile, problem: ProblemData) -> None:
    """Parse the stacked-grid PairwiseComparisons sheet _write_pcm_sheet
    writes: walk the sheet top to bottom, treating a row whose first cell is
    the only non-blank one as a new matrix's label, the row right below it
    as its item-name header, and the following rows (one per header item) as
    its values — blank rows simply separate one matrix from the next."""
    raw = xls.parse("PairwiseComparisons", header=None)
    known_groups = set(problem.all_pcm_group_keys())
    n_rows = len(raw)
    row_idx = 0
    while row_idx < n_rows:
        row = raw.iloc[row_idx]
        if row.isna().all():
            row_idx += 1
            continue
        label = str(row.iloc[0]).strip()
        excel_row = row_idx + 1
        group_key = ROOT_KEY if label in ("", "(root)") else label
        if group_key not in known_groups:
            raise ValueError(
                f"PairwiseComparisons sheet, row {excel_row}: '{label}' is not a known matrix "
                f"(not the root and not a criterion with children, or a pairwise leaf)."
            )
        matrix = problem.matrix_for(group_key)

        row_idx += 1
        if row_idx >= n_rows:
            raise ValueError(f"PairwiseComparisons sheet, row {excel_row}: '{label}' has no item-header row below it.")
        header_row = raw.iloc[row_idx]
        col_items = []
        for value in header_row.iloc[1:]:
            if pd.isna(value):
                break
            col_items.append(str(value).strip())
        for name in col_items:
            if name not in matrix.items:
                raise ValueError(
                    f"PairwiseComparisons sheet, row {row_idx + 1}: '{name}' is not an item "
                    f"of the '{label}' matrix."
                )

        row_idx += 1
        for _ in col_items:
            if row_idx >= n_rows:
                raise ValueError(f"PairwiseComparisons sheet: '{label}' matrix is missing rows for all its items.")
            data_row = raw.iloc[row_idx]
            row_item = data_row.iloc[0]
            if pd.isna(row_item):
                raise ValueError(f"PairwiseComparisons sheet, row {row_idx + 1}: expected an item name in the first column.")
            row_item = str(row_item).strip()
            if row_item not in matrix.items:
                raise ValueError(
                    f"PairwiseComparisons sheet, row {row_idx + 1}: '{row_item}' is not an item "
                    f"of the '{label}' matrix."
                )
            i = matrix.items.index(row_item)
            for j, col_name in enumerate(col_items):
                value = data_row.iloc[1 + j]
                if pd.notna(value):
                    matrix.set_value(i, matrix.items.index(col_name), float(value))
            row_idx += 1


def import_from_excel(file) -> tuple[ProblemData, list[str]]:
    xls = pd.ExcelFile(file)
    missing_sheets = [s for s in REQUIRED_SHEETS if s not in xls.sheet_names]
    if missing_sheets:
        raise ValueError(
            f"This file is missing sheet(s): {', '.join(missing_sheets)}. "
            f"Expected sheets: {', '.join(REQUIRED_SHEETS)}."
        )

    meta = dict(zip(xls.parse("Meta")["key"], xls.parse("Meta")["value"]))
    alt_df = xls.parse("Alternatives")
    crit_df = xls.parse("Criteria")

    notes: list[str] = []

    alt_names = _required_name_column(alt_df, "Alternatives")
    alt_descriptions = _optional_str_column(alt_df, "description")
    alt_colors = _optional_str_column(alt_df, "color")
    alternatives = [
        Alternative(name=n, description=d, color=c)
        for n, d, c in zip(alt_names, alt_descriptions, alt_colors)
    ]

    crit_names = _required_name_column(crit_df, "Criteria")
    parents_raw = _optional_str_column(crit_df, "parent")
    parents = [p if p.strip() else None for p in parents_raw]
    for i, parent in enumerate(parents):
        if parent is not None and parent not in crit_names:
            raise ValueError(f"Criteria sheet, row {i + 2}: parent '{parent}' is not a known criterion name.")
    eval_modes = _read_column(crit_df, "eval_mode", _cast_eval_mode, EvalMode.PAIRWISE, "eval_mode", "Criteria", notes)
    directions = _read_column(crit_df, "direction", _cast_direction, Direction.MAX, "direction", "Criteria", notes)
    crit_colors = _optional_str_column(crit_df, "color")
    criteria = [
        CriterionNode(name=n, parent=p, eval_mode=m, direction=d, color=c)
        for n, p, m, d, c in zip(crit_names, parents, eval_modes, directions, crit_colors)
    ]

    problem = ProblemData(
        name=str(meta.get("name", "Imported problem")),
        description=str(meta.get("description", "")),
        goal_name=str(meta.get("goal_name", "Goal")),
        weight_method=_cast_weight_method(meta.get("weight_method", WeightMethod.EIGENVECTOR.value)),
        root_eval_mode=_cast_eval_mode(meta.get("root_eval_mode", EvalMode.PAIRWISE.value)),
        alternatives=alternatives,
        criteria=criteria,
    )

    if "PairwiseComparisons" in xls.sheet_names:
        _read_pcm_sheet(xls, problem)

    if "DirectValues" in xls.sheet_names:
        direct_df = xls.parse("DirectValues")
        for i, row in direct_df.iterrows():
            leaf, alt = str(row["leaf"]), str(row["alternative"])
            if leaf not in crit_names:
                raise ValueError(f"DirectValues sheet, row {i + 2}: unknown leaf criterion '{leaf}'.")
            if alt not in alt_names:
                raise ValueError(f"DirectValues sheet, row {i + 2}: unknown alternative '{alt}'.")
            if leaf not in problem.direct_values.columns:
                problem.direct_values[leaf] = 0.0
            problem.direct_values.loc[alt, leaf] = float(row["value"])

    if "DirectWeights" in xls.sheet_names:
        weight_df = xls.parse("DirectWeights")
        for i, row in weight_df.iterrows():
            child = str(row["child"])
            if child not in crit_names:
                raise ValueError(f"DirectWeights sheet, row {i + 2}: unknown criterion '{child}'.")
            problem.direct_group_weights[child] = float(row["value"])

    return problem, notes
