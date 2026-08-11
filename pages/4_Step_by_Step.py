"""A student-friendly, interactive walkthrough of one matrix's calculation —
both weight-vector methods, CR — and then how its weight climbs the tree
into an alternative's final total score. Every number here is computed with
the exact same functions as the Results page."""
import numpy as np
import pandas as pd
import streamlit as st

from app_state import get_problem
from i18n import t
from ahp_core import pcm as pcm_math
from ahp_core.hierarchy import compute_hierarchy, compute_node_result, direct_alternative_weights
from ahp_core.model import EvalMode, ROOT_KEY


def _format_matrix(values: np.ndarray, items: list[str]) -> pd.DataFrame:
    # st.dataframe doesn't reliably honor a Styler's na_rep for NaN cells, so
    # format to plain display strings ourselves (see 2_Data_Entry.py).
    text = np.vectorize(lambda v: "—" if np.isnan(v) else f"{v:.3f}")(values)
    return pd.DataFrame(text, index=items, columns=items)

st.title(t("step.title"))
st.caption(t("step.caption"))

problem = get_problem()

if len(problem.alternatives) < 2 or not problem.leaf_criteria():
    st.info(t("common.need_2alt_1crit"))
    st.stop()

def _group_label(group_key: str) -> str:
    return t("common.main_criteria") if group_key == ROOT_KEY else group_key


def _disconnected_message(exc: pcm_math.DisconnectedMatrixError) -> str:
    if exc.group_keys:
        return t("common.disconnected_error_named", names=", ".join(_group_label(k) for k in exc.group_keys))
    return t("common.disconnected_error")


try:
    baseline = compute_hierarchy(problem)
except pcm_math.DisconnectedMatrixError as exc:
    st.error(_disconnected_message(exc))
    st.stop()


st.divider()
st.subheader(t("step.pick_subheader"))
group_options = problem.all_pcm_group_keys()
group_key = st.selectbox(t("step.pick_label"), group_options, format_func=_group_label)

matrix = problem.matrix_for(group_key)
items = matrix.items

if len(items) < 2:
    st.info(t("data_entry.complete_badge"))
    st.stop()

try:
    node_result = compute_node_result(problem, group_key)
except pcm_math.DisconnectedMatrixError as exc:
    st.error(_disconnected_message(exc))
    st.stop()

st.divider()
st.subheader(t("step.matrix_subheader"))
st.dataframe(_format_matrix(matrix.values, items), width="stretch")

st.divider()
st.subheader(t("step.methods_subheader"))
st.caption(t("step.methods_caption"))
methods_df = pd.DataFrame(
    {
        t("common.item"): items,
        t("common.weight_method_eigenvector"): node_result.pcm_result.weights_eigenvector,
        t("common.weight_method_llsm"): node_result.pcm_result.weights_llsm,
    },
)
st.dataframe(
    methods_df.style.format(
        {t("common.weight_method_eigenvector"): "{:.4f}", t("common.weight_method_llsm"): "{:.4f}"}
    ),
    width="stretch", hide_index=True,
)

st.divider()
st.subheader(t("step.cr_subheader"))
cr = node_result.pcm_result.cr
cr_label = t("common.cr_ok") if cr <= 0.1 else t("common.cr_bad")
col1, col2 = st.columns(2)
col1.metric(t("common.cr"), f"{cr:.4f}")
col2.metric("λmax", f"{node_result.pcm_result.lambda_max:.4f}")
if cr <= 0.1:
    st.success(cr_label)
else:
    st.warning(cr_label)
if not node_result.pcm_result.was_complete:
    st.caption(t("common.cr_minimal_completion_note"))

st.divider()
st.subheader(t("step.aggregation_subheader"))
st.caption(t("step.aggregation_caption"))


def _ancestor_chain(name: str | None) -> list[str]:
    chain = []
    while name is not None:
        chain.append(name)
        name = problem.node_by_name(name).parent
    chain.reverse()
    return chain


if group_key != ROOT_KEY:
    chain = _ancestor_chain(group_key)
    global_so_far = 1.0
    agg_rows = []
    for ancestor in chain:
        parent_key = problem.node_by_name(ancestor).parent or ROOT_KEY
        parent_result = baseline.node_results.get(parent_key) or compute_node_result(problem, parent_key)
        local_w = parent_result.local_weights.get(ancestor, 0.0)
        global_so_far *= local_w
        agg_rows.append(
            {
                t("sensitivity.col_criterion"): ancestor,
                t("results.local_weight_col"): local_w,
                t("results.weight_col"): global_so_far,
            }
        )
    st.dataframe(
        pd.DataFrame(agg_rows).style.format(
            {t("results.local_weight_col"): "{:.4f}", t("results.weight_col"): "{:.4f}"}
        ),
        width="stretch", hide_index=True,
    )
else:
    st.caption(t("common.root_breadcrumb"))

st.divider()
st.subheader(t("step.score_subheader"))
alt_name = st.selectbox(t("step.pick_alt_label"), [a.name for a in problem.alternatives])

score_rows = []
for leaf in problem.leaf_criteria():
    if leaf.eval_mode == EvalMode.DIRECT:
        eval_weights = direct_alternative_weights(problem, leaf)
    else:
        eval_weights = compute_node_result(problem, leaf.name).local_weights
    w_leaf = baseline.leaf_weights.get(leaf.name, 0.0)
    score_rows.append(
        {
            t("step.col_leaf_criterion"): leaf.name, "w_k": w_leaf,
            f"e_k({alt_name})": eval_weights.get(alt_name, 0.0),
            t("step.col_contribution"): w_leaf * eval_weights.get(alt_name, 0.0),
        }
    )
score_df = pd.DataFrame(score_rows)
st.latex(r"T_i = \sum_k w_k \cdot e_{ki}")
st.dataframe(
    score_df.style.format(
        {"w_k": "{:.4f}", f"e_k({alt_name})": "{:.4f}", t("step.col_contribution"): "{:.4f}"}
    ),
    width="stretch", hide_index=True,
)
st.latex(rf"T_{{{alt_name}}} = {score_df[t('step.col_contribution')].sum():.4f}")

rank = baseline.ranking.index(alt_name) + 1
st.success(
    t(
        "step.final_ranking", ranking=" > ".join(baseline.ranking), alt=alt_name,
        rank=rank, m=len(baseline.ranking),
    )
)
