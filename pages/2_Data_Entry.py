"""Raw data entry: click a node in the tree diagram to fill in its
pairwise-comparison matrix (root's main criteria, a non-leaf's children, a
PAIRWISE leaf's alternatives) or its DIRECT-mode raw per-alternative values."""
import numpy as np
import pandas as pd
import streamlit as st

from app_state import get_problem, problem_generation, save_problem
from i18n import t
from ahp_core import pcm as pcm_math
from ahp_core.hierarchy import direct_alternative_weights, direct_group_weights as compute_direct_group_weights
from ahp_core.model import EvalMode, ROOT_KEY
from tree_widget import render_tree_selector

st.title(t("data_entry.title"))
st.caption(t("data_entry.caption"))

problem = get_problem()
gen = problem_generation()

if not problem.alternatives or not problem.criteria:
    st.info(t("data_entry.need_setup"))
    st.stop()

# Saaty's 1-9 verbal scale and its reciprocals, plus a "not entered yet"
# sentinel. A plain string, not None — Streamlit's selectbox doesn't
# reliably show a `None` option as selected on a fresh mount.
_MISSING = "missing"
_SAATY_VALUES = [_MISSING] + [1 / d for d in range(9, 1, -1)] + [1.0] + list(range(2, 10))


def _format_option(value, item_i: str, item_j: str) -> str:
    if value == _MISSING:
        return t("data_entry.saaty_missing_option")
    if value == 1:
        return f"{item_i} = {item_j}  (1:1)"
    if value > 1:
        return f"{item_i} ≻ {item_j}  ({value:g}:1)"
    return f"{item_j} ≻ {item_i}  ({round(1 / value):g}:1)"


def _weights_table(names: list[str], weights) -> pd.DataFrame:
    """A small (name, weight) table with the name as a plain column rather
    than the DataFrame index — st.dataframe doesn't reliably widen the index
    column to fit its content, silently truncating longer names, whereas a
    regular column sizes correctly."""
    return pd.DataFrame({t("common.item"): names, t("data_entry.weight_col"): list(weights)})


def _format_matrix(values: np.ndarray, items: list[str]) -> pd.DataFrame:
    # st.dataframe doesn't reliably honor a Styler's na_rep for NaN cells (it
    # falls back to its own "None" rendering), so format to plain display
    # strings ourselves instead of relying on .style.format(na_rep=...).
    text = np.vectorize(lambda v: "—" if np.isnan(v) else f"{v:.3f}")(values)
    return pd.DataFrame(text, index=items, columns=items)


def _closest_option_index(current: float) -> int:
    if np.isnan(current):
        return 0
    diffs = [abs((v if v != _MISSING else np.inf) - current) for v in _SAATY_VALUES]
    return int(np.argmin(diffs))


# By-hand entry direction: matrix.values[i, j] > 1 means i is preferred over
# j (mirrors _format_option's convention below) - splitting a ratio into a
# direction plus a magnitude >= 1 means nobody ever has to type or round a
# reciprocal decimal by hand, unlike a single "i / j" field that forces
# values like 0.333 for "j is 3x more important."
_DIR_I_OVER_J = "i_over_j"
_DIR_EQUAL = "equal"
_DIR_J_OVER_I = "j_over_i"
_DIRECTIONS = [_DIR_I_OVER_J, _DIR_EQUAL, _DIR_J_OVER_I]


def _direction_and_magnitude(value: float) -> tuple[str, float]:
    if np.isnan(value) or abs(value - 1.0) < 1e-9:
        return _DIR_EQUAL, 1.0
    if value > 1.0:
        return _DIR_I_OVER_J, value
    return _DIR_J_OVER_I, 1.0 / value


def _group_title(group_key: str) -> str:
    if group_key == ROOT_KEY:
        return t("data_entry.matrix_for_root")
    node = problem.node_by_name(group_key)
    if problem.is_leaf(node):
        return t("data_entry.matrix_for_leaf", name=group_key)
    return t("data_entry.matrix_for_children", name=group_key)


def _badge(group_key: str) -> str | None:
    if problem.node_eval_mode(group_key) == EvalMode.DIRECT:
        # Flag how many raw values still need filling in (still at their
        # default 0.0), mirroring the PAIRWISE branch's missing-count below.
        node = None if group_key == ROOT_KEY else problem.node_by_name(group_key)
        if node is not None and problem.is_leaf(node):
            column = problem.direct_values.get(node.name)
            unset = sum(
                1 for alt in problem.alternatives
                if column is None or pd.isna(column.get(alt.name)) or column.get(alt.name) == 0.0
            )
        else:
            unset = sum(
                1 for name in problem.group_items(group_key) if problem.direct_group_weights.get(name, 0.0) == 0.0
            )
        return f"⚠ {unset}" if unset else "✓"
    matrix = problem.matrix_for(group_key)
    if matrix.size() <= 1:
        return "✓"
    missing = len(matrix.missing_pairs())
    if missing:
        return f"⚠ {missing}"
    try:
        result = pcm_math.solve(matrix.values)
    except pcm_math.DisconnectedMatrixError:
        return "⚠"
    return "✓" if result.cr <= 0.1 else "⚠ CR"


def render_matrix(group_key: str) -> None:
    matrix = problem.matrix_for(group_key)
    items = matrix.items
    n = len(items)
    if n == 0:
        return
    if n == 1:
        st.caption(t("data_entry.complete_badge"))
        return

    st.markdown(f"**{t('data_entry.pcm_label')}**")
    use_saaty = st.checkbox(t("data_entry.use_saaty_scale"), value=False, key=f"usesaaty_{group_key}_{gen}")
    by_hand = not use_saaty
    if by_hand:
        st.caption(t("data_entry.enter_by_hand_caption"))
    for i in range(n):
        for j in range(i + 1, n):
            current = matrix.values[i, j]
            if by_hand:
                row_cols = st.columns([2.2, 1.0, 2.2, 1.4])
                row_cols[0].markdown(f"{items[i]} — {items[j]}")
                missing_key = f"byhand_missing_{group_key}_{gen}_{items[i]}_{items[j]}"
                is_missing = row_cols[1].checkbox(
                    t("data_entry.missing_checkbox"), value=bool(np.isnan(current)), key=missing_key,
                )
                if is_missing:
                    if not np.isnan(current):
                        matrix.clear_value(i, j)
                else:
                    default_direction, default_magnitude = _direction_and_magnitude(current)
                    dir_key = f"byhand_dir_{group_key}_{gen}_{items[i]}_{items[j]}"
                    direction = row_cols[2].selectbox(
                        f"{items[i]}/{items[j]} direction", _DIRECTIONS,
                        index=_DIRECTIONS.index(default_direction),
                        format_func=lambda d, ii=items[i], jj=items[j]: {
                            _DIR_I_OVER_J: f"{ii} ≻ {jj}", _DIR_EQUAL: f"{ii} = {jj}", _DIR_J_OVER_I: f"{jj} ≻ {ii}",
                        }[d],
                        key=dir_key, label_visibility="collapsed",
                    )
                    if direction == _DIR_EQUAL:
                        new_val = 1.0
                    else:
                        mag_key = f"byhand_mag_{group_key}_{gen}_{items[i]}_{items[j]}"
                        magnitude = row_cols[3].number_input(
                            f"{items[i]}/{items[j]} magnitude", value=float(default_magnitude), min_value=1.0,
                            step=0.1, key=mag_key, label_visibility="collapsed",
                        )
                        new_val = magnitude if direction == _DIR_I_OVER_J else 1.0 / magnitude
                    if np.isnan(current) or abs(current - new_val) > 1e-9:
                        matrix.set_value(i, j, new_val)
            else:
                key = f"pcm_{group_key}_{gen}_{items[i]}_{items[j]}"
                selection = st.selectbox(
                    f"{items[i]} — {items[j]}", _SAATY_VALUES, index=_closest_option_index(current),
                    format_func=lambda v, ii=items[i], jj=items[j]: _format_option(v, ii, jj), key=key,
                )
                if selection == _MISSING:
                    if not np.isnan(current):
                        matrix.clear_value(i, j)
                elif np.isnan(current) or abs(current - selection) > 1e-9:
                    matrix.set_value(i, j, selection)

    st.dataframe(_format_matrix(matrix.values, items), width="stretch")

    missing = matrix.missing_pairs()
    if missing:
        st.caption(t("data_entry.missing_count", count=len(missing)))
    else:
        st.caption(t("data_entry.complete_badge"))

    try:
        result = pcm_math.solve(matrix.values)
    except pcm_math.DisconnectedMatrixError:
        st.error(t("common.disconnected_error"))
        return

    cr_label = t("common.cr_ok") if result.cr <= 0.1 else t("common.cr_bad")
    st.metric(t("common.cr"), f"{result.cr:.4f}", help=cr_label)
    if not result.was_complete:
        st.caption(t("common.cr_minimal_completion_note"))
    weights = result.weights_for(problem.weight_method)
    st.caption(t("data_entry.local_weights_caption"))
    st.dataframe(
        _weights_table(items, weights).style.format({t("data_entry.weight_col"): "{:.4f}"}),
        width="stretch", hide_index=True,
    )


def render_direct_values(node) -> None:
    """Raw value entry for a DIRECT-mode leaf, scoring the alternatives on it
    — same shape as render_direct_group_weights below: caption, one number
    input per item, then the resulting normalized weights table."""
    st.caption(t("data_entry.direct_values_caption"))
    alt_names = [a.name for a in problem.alternatives]
    cols = st.columns(max(len(alt_names), 1))
    for col, alt in zip(cols, problem.alternatives):
        current = 0.0
        if node.name in problem.direct_values.columns and alt.name in problem.direct_values.index:
            value = problem.direct_values.loc[alt.name, node.name]
            current = 0.0 if pd.isna(value) else float(value)
        new_value = col.number_input(
            alt.name, value=current, min_value=0.0, key=f"direct_{node.name}_{gen}_{alt.name}",
        )
        if node.name not in problem.direct_values.columns:
            problem.direct_values[node.name] = 0.0
        problem.direct_values.loc[alt.name, node.name] = new_value

    st.caption(t("data_entry.direct_result_caption"))
    try:
        weights = direct_alternative_weights(problem, node)
    except ValueError as exc:
        st.error(str(exc))
        return
    st.dataframe(
        _weights_table(alt_names, [weights[n] for n in alt_names]).style.format({t("data_entry.weight_col"): "{:.4f}"}),
        width="stretch", hide_index=True,
    )


def render_direct_group_weights(group_key: str) -> None:
    """Raw value entry for a DIRECT-mode root/non-leaf, weighing its children
    ("közvetlen súlyozás") — the same normalize-by-sum idea as a leaf's
    direct alternative values above, just without a min/max direction: a
    bigger entered value always means more importance."""
    items = problem.group_items(group_key)
    if not items:
        return
    st.caption(t("data_entry.direct_weights_caption"))
    cols = st.columns(max(len(items), 1))
    for col, child in zip(cols, items):
        current = float(problem.direct_group_weights.get(child, 0.0))
        new_value = col.number_input(child, value=current, min_value=0.0, key=f"directw_{group_key}_{gen}_{child}")
        problem.direct_group_weights[child] = new_value

    st.caption(t("data_entry.direct_result_caption"))
    weights = compute_direct_group_weights(problem, group_key)
    st.dataframe(
        _weights_table(items, [weights[n] for n in items]).style.format({t("data_entry.weight_col"): "{:.4f}"}),
        width="stretch", hide_index=True,
    )


selected = render_tree_selector(
    problem, state_key="de_selected_group", badge_fn=_badge, dropdown_label=t("data_entry.pick_matrix"),
)

st.divider()
if selected is not None:
    st.subheader(_group_title(selected))
    node = None if selected == ROOT_KEY else problem.node_by_name(selected)
    is_direct = problem.node_eval_mode(selected) == EvalMode.DIRECT
    if node is not None and problem.is_leaf(node):
        if is_direct:
            render_direct_values(node)
        else:
            render_matrix(selected)
    else:
        if is_direct:
            render_direct_group_weights(selected)
        else:
            render_matrix(selected)

save_problem(problem)
