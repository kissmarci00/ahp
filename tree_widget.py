"""A clickable, top-down tree diagram shared by the Problem Setup and Data
Entry pages: every criterion (plus a synthetic root box for "main criteria")
is drawn as a box; clicking one selects it, and the calling page renders
whatever editor belongs to that selection below the diagram.

This is UI-only (Streamlit + Plotly), so it lives at the top level next to
app_state.py/i18n.py rather than in ahp_core.
"""
from __future__ import annotations

from typing import Callable

import plotly.graph_objects as go
import streamlit as st

from ahp_core.model import EvalMode, ROOT_KEY, ProblemData
from i18n import t

ROOT_COLOR = "#52514e"
NON_LEAF_COLOR = "#8f8d82"
SELECTED_BORDER = "#e34948"
EDGE_COLOR = "#c3c2b7"


def _wrap_label(name: str, max_len: int = 14) -> str:
    if len(name) <= max_len:
        return name
    spaces = [i for i, ch in enumerate(name) if ch == " "]
    if not spaces:
        return name
    mid = len(name) // 2
    split_at = min(spaces, key=lambda i: abs(i - mid))
    return name[:split_at] + "<br>" + name[split_at + 1 :]


def _mode_and_count_lines(problem: ProblemData, group_key: str, count: int, count_key: str) -> list[str]:
    """"pairwise" or "direct" for how a group weighs its items, plus how many
    items — the same two-line shape for every group (root, non-leaf, or
    leaf)."""
    mode_line = t("tree.badge_direct") if problem.node_eval_mode(group_key) == EvalMode.DIRECT else t("tree.badge_pairwise")
    return [mode_line, t(count_key, n=count)]


def _node_subtitle_lines(problem: ProblemData, node) -> list[str]:
    """Extra lines describing the node: mode + item count, plus a
    leaf-DIRECT's min/max direction."""
    if problem.is_leaf(node):
        lines = _mode_and_count_lines(
            problem, node.name, len(problem.alternatives), "tree.badge_alternatives_count",
        )
        if node.eval_mode == EvalMode.DIRECT:
            lines.append(t("tree.badge_min") if node.direction.value == "min" else t("tree.badge_max"))
        return lines
    return _mode_and_count_lines(
        problem, node.name, len(problem.children(node.name)), "tree.badge_subcriteria_count",
    )


def layout_tree(problem: ProblemData) -> dict[str, tuple[float, float]]:
    """Simple layered layout: leaves get sequential x positions, each internal
    node is centered above its children's x span; y = -depth (root on top)."""
    positions: dict[str, tuple[float, float]] = {}
    next_x = [0.0]

    def assign(name: str, depth: int) -> float:
        parent_for_children = None if name == ROOT_KEY else name
        children = problem.children(parent_for_children)
        if not children:
            x = next_x[0]
            next_x[0] += 1.0
        else:
            xs = [assign(child.name, depth + 1) for child in children]
            x = sum(xs) / len(xs)
        positions[name] = (x, -float(depth))
        return x

    assign(ROOT_KEY, 0)
    return positions


MARKER_SIZE = 110
X_GAP = 1.85  # spacing multiplier between siblings, so labels + subtitle have room to breathe


def build_tree_figure(
    problem: ProblemData, selected: str | None = None, badge_fn: Callable[[str], str | None] | None = None,
) -> go.Figure:
    raw_positions = layout_tree(problem)
    positions = {name: (x * X_GAP, y) for name, (x, y) in raw_positions.items()}
    names = [ROOT_KEY] + [c.name for c in problem.criteria]
    leaf_colors = problem.criterion_colors()

    fig = go.Figure()

    edge_x: list[float | None] = []
    edge_y: list[float | None] = []
    for node in problem.criteria:
        parent_key = node.parent if node.parent is not None else ROOT_KEY
        x0, y0 = positions[parent_key]
        x1, y1 = positions[node.name]
        edge_x += [x0, x1, None]
        edge_y += [y0, y1, None]
    fig.add_trace(
        go.Scatter(x=edge_x, y=edge_y, mode="lines", line=dict(color=EDGE_COLOR, width=2), hoverinfo="skip", showlegend=False)
    )

    xs = [positions[n][0] for n in names]
    ys = [positions[n][1] for n in names]
    colors, labels, hover_texts, line_colors, line_widths = [], [], [], [], []
    for n in names:
        selected_here = n == selected
        line_colors.append(SELECTED_BORDER if selected_here else "#ffffff")
        line_widths.append(5 if selected_here else 1.5)
        if n == ROOT_KEY:
            colors.append(ROOT_COLOR)
            goal_label = problem.goal_name or problem.name
            root_lines = _mode_and_count_lines(
                problem, ROOT_KEY, len(problem.children(None)), "tree.badge_main_criteria_count",
            )
            badge = badge_fn(ROOT_KEY) if badge_fn else None
            if badge:
                root_lines.append(badge)
            label = f"<b>{_wrap_label(goal_label, max_len=16)}</b>"
            label += "<br>" + "<br>".join(f"<span style='font-size:8px'>{line}</span>" for line in root_lines)
            labels.append(label)
            hover_texts.append(goal_label)
            continue
        node = problem.node_by_name(n)
        colors.append(leaf_colors.get(n, NON_LEAF_COLOR) if problem.is_leaf(node) else NON_LEAF_COLOR)
        badge = badge_fn(n) if badge_fn else None
        extra_lines = _node_subtitle_lines(problem, node) + ([badge] if badge else [])
        label = f"<b>{_wrap_label(n)}</b>"
        if extra_lines:
            label += "<br>" + "<br>".join(f"<span style='font-size:8px'>{line}</span>" for line in extra_lines)
        labels.append(label)
        hover_texts.append(n)

    fig.add_trace(
        go.Scatter(
            x=xs, y=ys, mode="markers+text", text=labels, textposition="middle center",
            textfont=dict(size=11, color="white"),
            marker=dict(
                symbol="square", size=MARKER_SIZE, color=colors,
                line=dict(color=line_colors, width=line_widths),
            ),
            # Markers are fixed pixel size but the axis range is data units,
            # so on a narrow window the edge boxes get clipped by the plot
            # area; cliponaxis=False lets them render into the margin instead.
            cliponaxis=False,
            customdata=names, hovertext=hover_texts, hovertemplate="%{hovertext}<extra></extra>",
            showlegend=False,
        )
    )
    max_depth = max((-y for y in ys), default=0)
    x_min, x_max = (min(xs), max(xs)) if xs else (0.0, 0.0)
    fig.update_xaxes(visible=False, showgrid=False, zeroline=False, range=[x_min - 0.6, x_max + 0.6])
    # Explicit y-range padding above the root row — Plotly's autorange only
    # accounts for the marker symbol, not the multi-line label on top of it.
    fig.update_yaxes(visible=False, showgrid=False, zeroline=False, range=[-max_depth - 0.6, 0.6])
    fig.update_layout(
        margin=dict(l=30, r=30, t=40, b=30),
        height=min(800, max(400, 210 * (max_depth + 1))),
        clickmode="event+select",
        dragmode=False,
        plot_bgcolor="#fcfcfb",
        paper_bgcolor="#fcfcfb",
    )
    return fig


def render_tree_selector(
    problem: ProblemData, state_key: str, badge_fn: Callable[[str], str | None] | None = None,
    include_root: bool = True, none_label: str = "—", dropdown_label: str = "Or pick directly",
) -> str | None:
    """Renders the diagram, tracks the current selection in
    ``st.session_state[state_key]`` (a group_key: ROOT_KEY or a criterion
    name), and returns it. A plain selectbox underneath mirrors the same
    state for precise/keyboard selection.

    The diagram is always drawn with the value from before a selection
    change (the click event is only known after rendering), so an extra
    rerun is forced on change to redraw it with the fresh highlight
    immediately rather than one click late.
    """
    current = st.session_state.get(state_key)
    fig = build_tree_figure(problem, selected=current, badge_fn=badge_fn)
    event = st.plotly_chart(
        fig, on_select="rerun", key=f"{state_key}_chart", selection_mode=("points",), width="stretch",
    )

    points = (event.selection.get("points") if event and event.selection else None) or []
    # `customdata` was passed as a flat list of strings (one per point), so a
    # point's own customdata IS that string already — no extra [0] indexing
    # (that would silently take just the first *character* of the name).
    chart_choice = points[0]["customdata"] if points else None
    sig_key = f"{state_key}_chart_sig"
    if chart_choice is not None and chart_choice != st.session_state.get(sig_key):
        st.session_state[sig_key] = chart_choice
        if chart_choice != current:
            st.session_state[state_key] = chart_choice
            st.rerun()

    options = ([ROOT_KEY] if include_root else []) + [c.name for c in problem.criteria]
    if not options:
        return None

    def _label(n: str) -> str:
        return (problem.goal_name or problem.name or none_label) if n == ROOT_KEY else n

    idx = options.index(current) if current in options else 0
    # Keying by the current value forces a remount (respecting the fresh
    # `index`) whenever the chart drives a change — Streamlit otherwise
    # ignores `index` after first mount.
    chosen = st.selectbox(
        dropdown_label, options, index=idx, format_func=_label, key=f"{state_key}_dropdown_{idx}",
    )
    if chosen != current:
        st.session_state[state_key] = chosen
        st.rerun()
    return current
