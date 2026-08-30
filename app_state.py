"""Streamlit session-state glue: the single ProblemData lives here.

This is UI plumbing, not AHP math — kept separate from ahp_core so the math
package has zero Streamlit dependency.
"""
from __future__ import annotations

from pathlib import Path

import streamlit as st

from ahp_core.io_utils import export_to_excel, import_from_excel
from ahp_core.model import ProblemData
from ahp_core.sample import car_choice_example

# Autosave location: reusing the Excel round-trip format means this file is
# also a valid problem export a user could open by hand if curious.
_AUTOSAVE_PATH = Path(__file__).parent / ".ahp_autosave.xlsx"


def get_problem() -> ProblemData:
    if "problem" not in st.session_state:
        st.session_state.problem = _load_autosave() or car_choice_example()
    return st.session_state.problem


def set_problem(problem: ProblemData) -> None:
    """Replace the whole problem (new/sample/import). Bumps the generation
    counter so pages that namespace widget keys by generation start fresh
    instead of reusing cached values from the old problem's rows."""
    st.session_state.problem = problem
    st.session_state["problem_generation"] = st.session_state.get("problem_generation", 0) + 1
    save_problem(problem)


def problem_generation() -> int:
    return st.session_state.get("problem_generation", 0)


def save_problem(problem: ProblemData) -> None:
    """Persist to disk so the next reload (new tab, browser refresh, server
    restart) starts from where the last session left off. Best-effort: a
    write failure (e.g. read-only filesystem) shouldn't break the page."""
    try:
        _AUTOSAVE_PATH.write_bytes(export_to_excel(problem))
    except Exception:
        pass


def _load_autosave() -> ProblemData | None:
    if not _AUTOSAVE_PATH.exists():
        return None
    try:
        problem, _notes = import_from_excel(_AUTOSAVE_PATH)
        return problem
    except Exception:
        return None


# Scoped to Streamlit's download-button wrapper only, so regular buttons,
# checkboxes, sliders etc. keep their normal styling.
_DOWNLOAD_BUTTON_CSS = """
<style>
div[data-testid="stDownloadButton"] button {
    background-color: #0ca30c;
    border-color: #0ca30c;
    color: #ffffff;
}
div[data-testid="stDownloadButton"] button:hover {
    background-color: #0ca30c;
    border-color: #0ca30c;
    color: #ffffff;
    filter: brightness(0.92);
}
div[data-testid="stDownloadButton"] button:active {
    background-color: #0ca30c;
    border-color: #0ca30c;
    color: #ffffff;
    filter: brightness(0.85);
}
div[data-testid="stDownloadButton"] button * {
    color: #ffffff;
}
</style>
"""


def style_download_buttons() -> None:
    st.markdown(_DOWNLOAD_BUTTON_CSS, unsafe_allow_html=True)
