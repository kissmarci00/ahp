"""Problem setup: name/description, weight-vector method, alternatives, and
the criteria tree (add/rename/move/delete, leaf eval_mode + direction)."""
import streamlit as st

from app_state import get_problem, problem_generation, save_problem
from i18n import t
from ahp_core.model import Direction, EvalMode, ROOT_KEY, WeightMethod
from ahp_core.palette import default_color
from tree_widget import render_tree_selector

st.title(t("problem_setup.title"))

problem = get_problem()
gen = problem_generation()

st.subheader(t("problem_setup.details"))
problem.name = st.text_input(t("common.name"), value=problem.name)
problem.description = st.text_area(t("common.description"), value=problem.description)

st.divider()
st.subheader(t("problem_setup.method_subheader"))
st.caption(t("problem_setup.method_caption"))
method_options = list(WeightMethod)
method_labels = {
    WeightMethod.EIGENVECTOR: t("common.weight_method_eigenvector"),
    WeightMethod.LLSM: t("common.weight_method_llsm"),
}
problem.weight_method = st.radio(
    t("common.weight_method"), method_options, index=method_options.index(problem.weight_method),
    format_func=lambda m: method_labels[m], horizontal=True,
)

st.divider()
st.subheader(t("problem_setup.alternatives"))

alt_default_colors = problem.alternative_colors()
for i, alt in enumerate(list(problem.alternatives)):
    cols = st.columns([3, 4, 1, 1])
    new_name = cols[0].text_input(t("common.name"), value=alt.name, key=f"alt_name_{gen}_{i}")
    new_desc = cols[1].text_input(t("common.description"), value=alt.description, key=f"alt_desc_{gen}_{i}")
    new_color = cols[2].color_picker(
        t("common.color"), value=alt.color or alt_default_colors.get(alt.name, default_color(i)),
        key=f"alt_color_{gen}_{i}",
    )
    cols[3].write("")
    if cols[3].button(t("common.delete"), key=f"alt_del_{gen}_{i}"):
        problem.remove_alternative(alt.name)
        st.rerun()

    if new_name and new_name != alt.name:
        if new_name in [a.name for a in problem.alternatives if a is not alt]:
            st.error(t("problem_setup.alt_name_exists", name=new_name))
        else:
            problem.rename_alternative(alt.name, new_name)
    alt.description = new_desc
    alt.color = new_color

with st.form("add_alternative_form", clear_on_submit=True):
    st.write(t("problem_setup.add_alternative"))
    cols = st.columns([3, 4, 1])
    name = cols[0].text_input(t("common.name"))
    desc = cols[1].text_input(t("common.description"))
    submitted = cols[2].form_submit_button(t("common.add"))
    if submitted:
        if not name:
            st.error(t("common.please_provide_name"))
        elif name in [a.name for a in problem.alternatives]:
            st.error(t("problem_setup.alt_name_exists", name=name))
        else:
            problem.add_alternative(name, desc)
            st.rerun()

st.divider()
st.subheader(t("problem_setup.criteria"))
st.caption(t("problem_setup.criteria_caption"))

crit_default_colors = problem.criterion_colors()

if not problem.criteria:
    st.info(t("problem_setup.tree_empty"))

selected = render_tree_selector(
    problem, state_key="ps_selected_node", include_root=True, dropdown_label=t("problem_setup.pick_node"),
)

is_root_selected = selected == ROOT_KEY
is_real_node = selected is not None and selected != ROOT_KEY

# The next criterion's default parent is just whatever's selected on the
# tree — no separate state. After a successful add, the form below moves
# the selection to the parent just used, so consecutive adds keep landing
# on the same level.
add_parent = selected if is_real_node else ROOT_KEY

mode_options = list(EvalMode)
mode_labels = {
    EvalMode.PAIRWISE: t("common.eval_mode_pairwise"), EvalMode.DIRECT: t("common.eval_mode_direct"),
}

# Three actions, each in its own bordered box: edit the root, edit the
# selected criterion, or add a new one.
with st.container(border=True):
    if is_root_selected:
        st.markdown(f"##### {t('problem_setup.edit_root_header')}")
        st.caption(t("problem_setup.edit_root_caption"))
        root_cols = st.columns([2.5, 2.2])
        new_goal_name = root_cols[0].text_input(
            t("problem_setup.goal_name_label"), value=problem.goal_name, key=f"goal_name_{gen}",
        )
        new_root_mode = root_cols[1].radio(
            t("common.eval_mode"), mode_options, index=mode_options.index(problem.root_eval_mode),
            format_func=lambda m: mode_labels[m], key=f"root_mode_{gen}",
        )
        if new_goal_name != problem.goal_name or new_root_mode != problem.root_eval_mode:
            problem.goal_name = new_goal_name
            problem.root_eval_mode = new_root_mode
            save_problem(problem)
            st.rerun()
    elif is_real_node:
        node = problem.node_by_name(selected)
        is_leaf = problem.is_leaf(node)
        st.markdown(f"##### {t('problem_setup.edit_node_header', name=selected)}")

        cols = st.columns([2.5, 2.2])
        new_name = cols[0].text_input(t("common.name"), value=node.name, key=f"crit_name_{gen}_{selected}")

        # Streamlit's selectbox doesn't reliably show a `None` list entry as
        # selected (it renders the empty placeholder instead, even with a
        # matching `index`) — so the "top-level" option uses the ROOT_KEY
        # sentinel string instead, converted back to/from None at the edges.
        forbidden = {node.name, *problem.descendants(node.name)}
        parent_options = [ROOT_KEY] + [c.name for c in problem.criteria if c.name not in forbidden]
        current_parent_option = node.parent if node.parent is not None else ROOT_KEY
        new_parent_option = cols[1].selectbox(
            t("problem_setup.parent"), parent_options,
            index=parent_options.index(current_parent_option) if current_parent_option in parent_options else 0,
            format_func=lambda p: t("problem_setup.parent_top_level") if p == ROOT_KEY else p,
            key=f"crit_parent_{gen}_{selected}",
        )
        new_parent = None if new_parent_option == ROOT_KEY else new_parent_option

        # Tracked so a rerun can redraw the tree diagram (built above this
        # panel) with fresh state immediately, instead of lagging one step
        # behind.
        changed = False

        # Same layout for leaf/non-leaf; only a leaf uses the direction/color
        # columns (a non-leaf's mode weighs its children instead).
        mode_cols = st.columns(3)
        new_mode = mode_cols[0].radio(
            t("common.eval_mode"), mode_options, index=mode_options.index(node.eval_mode),
            format_func=lambda m: mode_labels[m], key=f"crit_mode_{gen}_{selected}",
        )
        new_direction = node.direction
        new_color = node.color
        if is_leaf:
            if new_mode == EvalMode.DIRECT:
                dir_options = [Direction.MAX, Direction.MIN]
                new_direction = mode_cols[1].radio(
                    t("common.direction"), dir_options, index=dir_options.index(node.direction),
                    format_func=lambda d: t("common.direction_max") if d == Direction.MAX else t("common.direction_min"),
                    key=f"crit_dir_{gen}_{selected}",
                )
            new_color = mode_cols[2].color_picker(
                t("common.color"), value=node.color or crit_default_colors.get(node.name, default_color(0)),
                key=f"crit_color_{gen}_{selected}",
            )

        if new_mode != node.eval_mode:
            problem.set_group_eval_mode(node.name, new_mode)
            changed = True
        if new_direction != node.direction:
            node.direction = new_direction
            changed = True
        if new_color != node.color:
            node.color = new_color
            changed = True

        if new_name and new_name != node.name:
            if new_name in [c.name for c in problem.criteria if c is not node]:
                st.error(t("problem_setup.crit_name_exists", name=new_name))
            else:
                problem.rename_criterion(node.name, new_name)
                st.session_state["ps_selected_node"] = new_name
                changed = True
        if new_parent != node.parent:
            node.parent = new_parent
            changed = True

        if changed:
            save_problem(problem)
            st.rerun()

        st.divider()
        if st.button(t("problem_setup.delete_criterion"), key=f"crit_del_{gen}_{selected}"):
            problem.remove_criterion(node.name)
            st.session_state["ps_selected_node"] = node.parent or ROOT_KEY
            st.rerun()
    else:
        st.markdown(f"##### {t('problem_setup.edit_node_header_empty')}")
        st.caption(t("problem_setup.edit_node_placeholder"))

st.write("")
with st.container(border=True):
    parent_options = [ROOT_KEY] + [c.name for c in problem.criteria]
    # Outside the form below: a plain selectbox reruns the page on change,
    # so the header right under it updates immediately instead of only
    # catching up when the form is submitted.
    parent_option = st.selectbox(
        t("problem_setup.parent"), parent_options,
        index=parent_options.index(add_parent) if add_parent in parent_options else 0,
        format_func=lambda p: t("problem_setup.parent_top_level") if p == ROOT_KEY else p,
        # Key varies with add_parent — otherwise Streamlit won't re-apply
        # `index` on a rerun where the widget already exists.
        key=f"add_crit_parent_{gen}_{add_parent}",
    )
    add_header = (
        t("problem_setup.add_subcriterion_under", parent=parent_option) if parent_option != ROOT_KEY
        else t("problem_setup.add_criterion")
    )
    st.markdown(f"##### {add_header}")
    with st.form("add_criterion_form", clear_on_submit=True):
        name = st.text_input(t("common.name"))
        parent = None if parent_option == ROOT_KEY else parent_option
        submitted = st.form_submit_button(t("common.add"))
        if submitted:
            if not name:
                st.error(t("common.please_provide_name"))
            elif name in [c.name for c in problem.criteria]:
                st.error(t("problem_setup.crit_name_exists", name=name))
            else:
                problem.add_criterion(name, parent=parent)
                # Keep the tree selection on the parent just used, so the
                # next add defaults to the same level.
                st.session_state["ps_selected_node"] = parent_option
                st.rerun()

save_problem(problem)
