"""Weight sensitivity analysis: stability intervals for a chosen criterion
node (any node with siblings, not just a main criterion), plus a chart of
every alternative's total score as that node's local weight varies."""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from app_state import get_problem, style_download_buttons
from i18n import t
from ahp_core import pcm as pcm_math
from ahp_core import sensitivity as sens_mod
from ahp_core.model import ROOT_KEY

style_download_buttons()
st.title(t("sensitivity.title"))
st.caption(t("sensitivity.caption"))


def _group_label(group_key: str) -> str:
    return t("common.main_criteria") if group_key == ROOT_KEY else group_key


def _disconnected_message(exc: pcm_math.DisconnectedMatrixError) -> str:
    if exc.group_keys:
        return t("common.disconnected_error_named", names=", ".join(_group_label(k) for k in exc.group_keys))
    return t("common.disconnected_error")


problem = get_problem()
eligible = sens_mod.sensitivity_eligible_nodes(problem)

if len(problem.alternatives) < 2 or not eligible:
    st.info(t("sensitivity.need_2alt_2sib"))
    st.stop()

node_name = st.selectbox(t("sensitivity.criterion_to_analyze"), eligible)
top_x = st.slider(t("sensitivity.stability_slider"), 1, len(problem.alternatives), 1)

try:
    sens = sens_mod.compute_weight_sensitivity(problem, node_name)
except pcm_math.DisconnectedMatrixError as exc:
    st.error(_disconnected_message(exc))
    st.stop()
except ValueError as exc:
    st.warning(str(exc))
    st.stop()

w_low, w_high, crossings = sens.stability_interval(top_x)

st.metric(t("sensitivity.current_weight"), f"{sens.w0:.4f}")
st.success(
    t(
        "sensitivity.stability_success", top_x=top_x, criterion_name=node_name,
        w_low=f"{w_low:.4f}", w_high=f"{w_high:.4f}",
    )
)
if w_low == 0.0:
    st.caption(t("sensitivity.no_reversal_at_0"))
if w_high == 1.0:
    st.caption(t("sensitivity.no_reversal_at_1"))

ws = np.linspace(0.0, 1.0, 201)
scores = sens.score_at(ws)

SURFACE = "#fcfcfb"
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
GRIDLINE = "#e1e0d9"
FONT_FAMILY = 'system-ui, -apple-system, "Segoe UI", sans-serif'

alt_colors = problem.alternative_colors()
fig = go.Figure()
for idx, name in enumerate(sens.alt_names):
    fig.add_trace(
        go.Scatter(
            x=ws, y=scores[:, idx], mode="lines", name=name,
            line=dict(color=alt_colors.get(name), width=2),
        )
    )
fig.add_vline(
    x=sens.w0, line_dash="dash", line_color=INK_SECONDARY,
    annotation_text=t("sensitivity.chart_current_weight"),
)
fig.add_vrect(x0=w_low, x1=w_high, fillcolor="LightGreen", opacity=0.15, line_width=0)
fig.update_xaxes(gridcolor=GRIDLINE, color=INK_SECONDARY, title_font=dict(color=INK_SECONDARY, family=FONT_FAMILY))
fig.update_yaxes(gridcolor=GRIDLINE, color=INK_SECONDARY, title_font=dict(color=INK_SECONDARY, family=FONT_FAMILY))
fig.update_layout(
    title=dict(
        text=t("sensitivity.chart_title", name=node_name),
        font=dict(color=INK_PRIMARY, size=18, family=FONT_FAMILY),
    ),
    xaxis_title=t("sensitivity.chart_xaxis", name=node_name),
    yaxis_title=t("results.score_col"),
    xaxis_range=[0, 1], legend_title=t("results.alternative_col"),
    font=dict(family=FONT_FAMILY, color=INK_PRIMARY),
    paper_bgcolor=SURFACE, plot_bgcolor=SURFACE,
    legend=dict(bgcolor=SURFACE, font=dict(color=INK_PRIMARY, family=FONT_FAMILY)),
    margin=dict(l=60, r=40, t=60, b=60),
)
st.plotly_chart(fig, width="stretch", theme=None)

if crossings:
    st.caption(t("sensitivity.crossings_caption"))
    crossings_df = pd.DataFrame(
        {
            t("sensitivity.col_alternatives"): [f"{c['a']} ↔ {c['b']}" for c in crossings],
            t("sensitivity.col_weight_at_crossing"): [f"{c['w']:.4f}" for c in crossings],
        }
    )
    st.dataframe(crossings_df, width="stretch", hide_index=True)

st.divider()
st.subheader(t("sensitivity.summary_subheader"))
st.caption(t("sensitivity.summary_caption", top_x=top_x))

summary_rows = []
skipped = []
for name in eligible:
    try:
        node_sens = sens_mod.compute_weight_sensitivity(problem, name)
    except ValueError:
        skipped.append(name)
        continue
    node_w_low, node_w_high, _ = node_sens.stability_interval(top_x)
    decrease_amount = float("inf") if node_w_low == 0.0 else node_sens.w0 - node_w_low
    increase_amount = float("inf") if node_w_high == 1.0 else node_w_high - node_sens.w0
    max_change = None if decrease_amount == increase_amount == float("inf") else min(decrease_amount, increase_amount)
    summary_rows.append({"name": name, "w0": node_sens.w0, "w_low": node_w_low, "w_high": node_w_high, "max_change": max_change})

if summary_rows:
    unbounded_text = t("sensitivity.unbounded")
    table_rows = [
        {
            t("sensitivity.col_criterion"): r["name"],
            t("sensitivity.col_current_weight"): f"{r['w0']:.4f}",
            t("sensitivity.col_can_decrease_to"): unbounded_text if r["w_low"] == 0.0 else f"{r['w_low']:.4f}",
            t("sensitivity.col_can_increase_to"): unbounded_text if r["w_high"] == 1.0 else f"{r['w_high']:.4f}",
            t("sensitivity.col_max_change"): "—" if r["max_change"] is None else f"{r['max_change']:.4f}",
        }
        for r in summary_rows
    ]
    st.dataframe(pd.DataFrame(table_rows), width="stretch", hide_index=True)

    sensitive_rows = [r for r in summary_rows if r["max_change"] is not None]
    if sensitive_rows:
        most_sensitive = min(sensitive_rows, key=lambda r: r["max_change"])
        st.info(
            t(
                "sensitivity.most_sensitive", criterion_name=most_sensitive["name"],
                max_change=f"{most_sensitive['max_change']:.4f}", top_x=top_x,
            )
        )

if skipped:
    st.caption(t("sensitivity.skipped_caption", names=", ".join(skipped)))
