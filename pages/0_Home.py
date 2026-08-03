"""AHP Playground — home page: create, import and export a decision problem."""
import streamlit as st

from app_state import get_problem, set_problem, style_download_buttons
from i18n import t
from ahp_core.io_utils import export_to_excel, import_from_excel
from ahp_core.model import ProblemData
from ahp_core.sample import car_choice_example

style_download_buttons()

st.title(t("home.title"))
st.caption(t("home.caption"))

problem = get_problem()

st.subheader(t("home.current_problem"))
# st.metric truncates a long value with an ellipsis and can't wrap, so a long
# problem name gets cut off — caption + markdown gives the same label-over-value
# look but wraps instead. Both columns use it so their baselines match.
col1, col2 = st.columns(2)
col1.caption(t("home.metric_name"))
col1.markdown(f"### {problem.name}")
col2.caption(t("home.metric_alt_crit"))
col2.markdown(f"### {len(problem.alternatives)} / {len(problem.leaf_criteria())}")
if problem.description:
    st.write(problem.description)

st.divider()

new_col, sample_col = st.columns(2)
with new_col:
    st.markdown(t("home.start_fresh"))
    if st.button(t("home.create_new")):
        set_problem(ProblemData(name="New problem"))
        st.rerun()

with sample_col:
    st.markdown(t("home.load_builtin"))
    st.caption(t("home.example_caption"))
    if st.button(t("home.load_example")):
        set_problem(car_choice_example())
        st.rerun()

st.divider()

st.subheader(t("home.import_problem"))
st.caption(t("home.import_caption"))
excel_file = st.file_uploader(t("home.import_excel_label"), type=["xlsx"], key="excel_upload")
if excel_file is not None and st.session_state.get("_excel_import_id") != excel_file.file_id:
    try:
        imported_problem, notes = import_from_excel(excel_file)
        set_problem(imported_problem)
        st.session_state["_excel_import_id"] = excel_file.file_id
        st.session_state["_excel_import_notes"] = notes
        st.rerun()
    except Exception as exc:
        st.error(t("home.excel_import_error", error=exc))

if excel_file is not None and st.session_state.get("_excel_import_id") == excel_file.file_id:
    st.success(t("home.excel_import_success", name=problem.name))
    notes = st.session_state.get("_excel_import_notes") or []
    if notes:
        st.info(t("home.import_notes_lead") + "\n\n" + "\n".join(f"- {n}" for n in notes))

st.divider()

st.subheader(t("home.export_problem"))
st.download_button(
    t("home.download_excel"),
    data=export_to_excel(problem),
    file_name=f"{problem.name or 'ahp_problem'}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
