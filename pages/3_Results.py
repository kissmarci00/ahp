"""AHP results: a headline ranking chart, global leaf-criterion weights, and
the detailed local weights & CR per node."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app_state import get_problem, style_download_buttons
from i18n import t
from ahp_core import pcm as pcm_math
from ahp_core.hierarchy import compute_hierarchy, direct_alternative_weights
from ahp_core.model import EvalMode, ROOT_KEY
from ahp_core.table_export import export_tables_to_excel

style_download_buttons()
st.title(t("results.title"))

problem = get_problem()

if len(problem.alternatives) < 2 or not problem.leaf_criteria():
    st.info(t("common.need_2alt_1crit"))
    st.stop()

try:
    result = compute_hierarchy(problem)
except pcm_math.DisconnectedMatrixError as exc:
    st.error(str(exc))
    st.stop()


def _group_label(group_key: str) -> str:
    return t("common.main_criteria") if group_key == ROOT_KEY else group_key


# -- publishable style tokens (fixed light "paper" surface, independent of the
# viewer's OS/browser theme), matching the Sensitivity/GAIA pages' styling ----
SURFACE = "#fcfcfb"
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
GRIDLINE = "#e1e0d9"
FONT_FAMILY = 'system-ui, -apple-system, "Segoe UI", sans-serif'


def _ranked_bar_chart(items: dict[str, float], colors: dict[str, str], x_title: str) -> go.Figure:
    """A horizontal bar chart, highest value on top, one bar per item, colored
    by the item's own assigned identity color, with the value direct-labeled
    at the bar's end — magnitude comparison across a handful of categories,
    per the dataviz skill's form heuristic."""
    ordered = sorted(items.items(), key=lambda kv: kv[1], reverse=True)
    names = [name for name, _ in ordered]
    values = [value for _, value in ordered]
    bar_colors = [colors.get(name, INK_SECONDARY) for name in names]

    fig = go.Figure(
        go.Bar(
            x=values, y=names, orientation="h", marker=dict(color=bar_colors),
            text=[f"{v:.3f}" for v in values], textposition="outside",
            textfont=dict(color=INK_PRIMARY, family=FONT_FAMILY),
            hovertemplate="<b>%{y}</b><br>" + x_title + ": %{x:.4f}<extra></extra>",
        )
    )
    fig.update_yaxes(
        autorange="reversed", gridcolor=GRIDLINE, color=INK_SECONDARY, automargin=True,
        tickfont=dict(color=INK_PRIMARY, family=FONT_FAMILY, size=13),
    )
    fig.update_xaxes(
        title=x_title, gridcolor=GRIDLINE, color=INK_SECONDARY, range=[0, max(values) * 1.18],
        title_font=dict(color=INK_SECONDARY, family=FONT_FAMILY),
    )
    fig.update_layout(
        font=dict(family=FONT_FAMILY, color=INK_PRIMARY), paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
        margin=dict(l=10, r=40, t=10, b=40), height=min(480, max(220, 60 * len(names))),
        showlegend=False,
    )
    return fig


st.subheader(t("results.scores_subheader"))
st.caption(t("results.scores_caption"))
st.success(t("results.winner_announcement", winner=result.ranking[0], ranking=" > ".join(result.ranking)))

alt_colors = problem.alternative_colors()
st.plotly_chart(_ranked_bar_chart(result.alternative_scores, alt_colors, t("results.score_col")), width="stretch", theme=None)

scores_df = pd.DataFrame(
    {t("results.alternative_col"): list(result.alternative_scores.keys()), t("results.score_col"): list(result.alternative_scores.values())}
).sort_values(t("results.score_col"), ascending=False).reset_index(drop=True)
scores_df.insert(0, t("results.rank_col"), range(1, len(scores_df) + 1))
st.dataframe(scores_df.style.format({t("results.score_col"): "{:.4f}"}), width="stretch", hide_index=True)

st.divider()
st.subheader(t("results.leaf_weights_subheader"))
st.caption(t("results.leaf_weights_caption"))

crit_colors = problem.criterion_colors()
st.plotly_chart(
    _ranked_bar_chart(result.leaf_weights, crit_colors, t("results.weight_col")), width="stretch", theme=None,
)

leaf_weights_df = pd.DataFrame(
    {"Global weight": result.leaf_weights}
).sort_values("Global weight", ascending=False)
# Display copy with the criterion name as a plain column rather than the
# DataFrame index — st.dataframe doesn't reliably widen the index column to
# fit longer names, silently truncating them; a regular column sizes
# correctly. leaf_weights_df itself (index intact) is still what's exported.
leaf_weights_display = leaf_weights_df.reset_index(names=t("common.item")).rename(
    columns={"Global weight": t("results.weight_col")}
)
st.dataframe(
    leaf_weights_display.style.format({t("results.weight_col"): "{:.4f}"}), width="stretch", hide_index=True,
)

st.divider()
st.subheader(t("results.node_weights_subheader"))
st.caption(t("results.node_weights_caption"))

# One bordered card per node (matching the Data Entry page's per-matrix
# style) instead of one long flat table — each node's own items/weights/CR
# are visually its own unit, rather than blurring into the next node's rows.
# Ordered by the criteria's own defined order (root first) rather than
# result.node_results' incidental insertion order (root, then non-leaves via
# the tree walk, then pairwise leaves via the scoring loop — an
# implementation detail, not a natural reading order). DIRECT-mode leaves
# (e.g. "Ár") never get an entry in result.node_results at all — the scoring
# loop reads their weights straight from direct_alternative_weights instead
# of going through a PCM — so they're computed separately here to still get
# their own card, alongside every PAIRWISE leaf and non-leaf/root group.
rows = []
for group_key in [ROOT_KEY] + [c.name for c in problem.criteria]:
    if group_key == ROOT_KEY:
        node_result = result.node_results[ROOT_KEY]
        local_weights = node_result.local_weights
        cr = node_result.pcm_result.cr if node_result.pcm_result is not None else None
        was_complete = node_result.pcm_result is None or node_result.pcm_result.was_complete
    else:
        node = problem.node_by_name(group_key)
        is_leaf = problem.is_leaf(node)
        if is_leaf and node.eval_mode == EvalMode.DIRECT:
            try:
                local_weights = direct_alternative_weights(problem, node)
            except ValueError as exc:
                with st.container(border=True):
                    st.markdown(f"**{group_key}**")
                    st.error(str(exc))
                continue
            cr = None
            was_complete = True
        elif group_key in result.node_results:
            node_result = result.node_results[group_key]
            local_weights = node_result.local_weights
            cr = node_result.pcm_result.cr if node_result.pcm_result is not None else None
            was_complete = node_result.pcm_result is None or node_result.pcm_result.was_complete
        else:
            continue

    for item, weight in local_weights.items():
        rows.append({"Group": _group_label(group_key), "Item": item, "Local weight": weight, "CR": cr})

    with st.container(border=True):
        header_cols = st.columns([4, 1])
        header_cols[0].markdown(f"**{_group_label(group_key)}**")
        if cr is None:
            header_cols[1].caption(t("results.direct_weighting_badge"))
        else:
            cr_icon = "✓" if cr <= 0.1 else "⚠"
            header_cols[1].caption(f"{cr_icon} CR {cr:.4f}")
            if not was_complete:
                header_cols[1].caption(t("common.cr_minimal_completion_note"))
        node_df = pd.DataFrame(
            {t("common.item"): list(local_weights.keys()), t("results.local_weight_col"): list(local_weights.values())}
        )
        st.dataframe(
            node_df.style.format({t("results.local_weight_col"): "{:.4f}"}), width="stretch", hide_index=True,
        )

node_weights_df = pd.DataFrame(rows)

st.divider()
st.download_button(
    t("results.download_results"),
    data=export_tables_to_excel(
        [
            ("Node weights", node_weights_df.set_index("Item"), "Local weights & CR, by node", None),
            ("Leaf weights", leaf_weights_df, "Global leaf-criterion weights", None),
            (
                "Scores", scores_df.set_index(t("results.rank_col")), "Alternative total scores & ranking",
                [("Ranking", " > ".join(result.ranking))],
            ),
        ],
        number_format="0.0000",
    ),
    file_name=f"{problem.name or 'ahp'}_results.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
