"""English/Hungarian text for every Streamlit page's UI chrome.

Hungarian terminology follows this course's reference material (AHP.pdf and
NemTeljesenKitoltott.pdf) exactly — "szempont" for criterion, "levélszempont"
for leaf criterion, "páros összehasonlítás mátrix" for the PCM, "sajátvektor
módszer" / "LLSM (mértani közép) módszer" for the two weight-vector methods,
"konzisztencia mutató (CR)" for the consistency ratio, "összefüggő gráf" for
a connected comparison graph, "stabilitási intervallum" for a sensitivity
stability interval.

Same scope and exceptions as the PROMETHEE Playground's i18n.py: page chrome
only (titles, captions, labels, buttons, alerts). Plotly figure content and
Excel export content stay in English regardless of the selected language, so
a saved image/file always reads the same. ahp_core exception messages are
bilingual inline (that package has no i18n dependency of its own), so pages
show them as-is.
"""
from __future__ import annotations

from pathlib import Path

import streamlit as st

LANGUAGES = {"en": "English", "hu": "Magyar"}

_LANGUAGE_PATH = Path(__file__).parent / ".ahp_language.txt"

TRANSLATIONS: dict[str, dict[str, str]] = {
    # -- shared across pages ---------------------------------------------------
    "common.name": {"en": "Name", "hu": "Név"},
    "common.description": {"en": "Description", "hu": "Leírás"},
    "common.color": {"en": "Color", "hu": "Szín"},
    "common.item": {"en": "Item", "hu": "Elem"},
    "common.delete": {"en": "Delete", "hu": "Törlés"},
    "common.add": {"en": "Add", "hu": "Hozzáadás"},
    "common.weight": {"en": "Weight", "hu": "Súly"},
    "common.direction": {"en": "Direction", "hu": "Irány"},
    "common.direction_max": {"en": "max (bigger is better)", "hu": "max (a nagyobb a jobb)"},
    "common.direction_min": {"en": "min (smaller is better)", "hu": "min (a kisebb a jobb)"},
    "common.please_provide_name": {"en": "Please provide a name.", "hu": "Adjon meg egy nevet."},
    "common.need_2alt_1crit": {
        "en": "Add at least two alternatives and one leaf criterion on the Problem Setup page.",
        "hu": "Adjon meg legalább két alternatívát és egy levélszempontot a Probléma beállítása oldalon.",
    },
    "common.eval_mode": {"en": "Evaluation mode", "hu": "Értékelés módja"},
    "common.eval_mode_pairwise": {"en": "Pairwise comparison", "hu": "Páros összehasonlítás"},
    "common.eval_mode_direct": {"en": "Direct rating", "hu": "Közvetlen értékelés"},
    "common.weight_method": {"en": "Weight-vector method", "hu": "Súlyvektor számítási módszer"},
    "common.weight_method_eigenvector": {"en": "Eigenvector method", "hu": "Sajátvektor módszer"},
    "common.weight_method_llsm": {
        "en": "LLSM (geometric mean) method", "hu": "LLSM (mértani közép) módszer",
    },
    "common.cr": {"en": "Consistency ratio (CR)", "hu": "Konzisztencia mutató (CR)"},
    "common.cr_ok": {"en": "acceptable (CR ≤ 0.1)", "hu": "elfogadható (CR ≤ 0,1)"},
    "common.cr_bad": {"en": "too high (CR > 0.1) — consider revising this matrix", "hu": "túl magas (CR > 0,1) — érdemes felülvizsgálni ezt a mátrixot"},
    "common.disconnected_error": {
        "en": "This matrix's comparison graph is not connected — add more comparisons "
        "so every item is linked, directly or indirectly, to every other.",
        "hu": "Ennek a mátrixnak a reprezentáló gráfja nem összefüggő — adjon meg további "
        "összehasonlításokat, hogy minden elem közvetlenül vagy közvetve össze legyen "
        "hasonlítva minden másikkal.",
    },
    "common.main_criteria": {"en": "Main criteria", "hu": "Főszempontok"},
    "common.root_breadcrumb": {"en": "(main criteria)", "hu": "(főszempontok)"},

    # -- navigation ---------------------------------------------------------------
    "nav.home": {"en": "Home", "hu": "Kezdőlap"},
    "nav.problem_setup": {"en": "Problem Setup", "hu": "Probléma beállítása"},
    "nav.data_entry": {"en": "Data Entry", "hu": "Adatbevitel"},
    "nav.results": {"en": "Results", "hu": "Eredmények"},
    "nav.step_by_step": {"en": "Step by Step", "hu": "Lépésről lépésre"},
    "nav.sensitivity": {"en": "Sensitivity", "hu": "Érzékenységvizsgálat"},

    # -- home -----------------------------------------------------------------------
    "home.title": {"en": "AHP Playground", "hu": "AHP Playground"},
    "home.caption": {
        "en": "An educational tool for the Analytic Hierarchy Process (pairwise-comparison "
        "matrices): build a criteria tree, weigh it, evaluate alternatives, and see how "
        "stable the result is.",
        "hu": "Oktatási eszköz az Analytic Hierarchy Process (páros összehasonlítás mátrixos) "
        "módszer bemutatására: szempontfa felépítése, súlyozása, alternatívák értékelése és "
        "az eredmény stabilitásának vizsgálata.",
    },
    "home.current_problem": {"en": "Current problem", "hu": "Jelenlegi probléma"},
    "home.metric_name": {"en": "Name", "hu": "Név"},
    "home.metric_alt_crit": {
        "en": "Alternatives / leaf criteria", "hu": "Alternatívák / levélszempontok",
    },
    "home.start_fresh": {"en": "**Start a new problem**", "hu": "**Új probléma indítása**"},
    "home.create_new": {"en": "Create new problem", "hu": "Új probléma létrehozása"},
    "home.load_builtin": {"en": "**Load the built-in example**", "hu": "**Beépített példa betöltése**"},
    "home.example_caption": {
        "en": "A car-choice example: cost, aesthetics and features, comparing three cars.",
        "hu": "Egy autóválasztás-példa: költségek, esztétikum és felszereltség szempontok, "
        "három autó összehasonlításával.",
    },
    "home.load_example": {"en": "Load example", "hu": "Példa betöltése"},
    "home.import_problem": {"en": "Import a problem", "hu": "Probléma importálása"},
    "home.import_caption": {
        "en": "Upload a previously exported .xlsx file to continue working on it.",
        "hu": "Töltsön fel egy korábban exportált .xlsx fájlt a folytatáshoz.",
    },
    "home.import_excel_label": {"en": "Excel file (.xlsx)", "hu": "Excel fájl (.xlsx)"},
    "home.excel_import_error": {"en": "Could not import this file: {error}", "hu": "A fájl importálása sikertelen: {error}"},
    "home.excel_import_success": {"en": "Imported '{name}'.", "hu": "'{name}' importálva."},
    "home.import_notes_lead": {
        "en": "Some values were missing and filled in with defaults:",
        "hu": "Néhány érték hiányzott, ezeket alapértelmezett értékkel pótoltuk:",
    },
    "home.export_problem": {"en": "Export this problem", "hu": "Probléma exportálása"},
    "home.download_excel": {"en": "Download as Excel (.xlsx)", "hu": "Letöltés Excelként (.xlsx)"},

    # -- problem setup ------------------------------------------------------------
    "problem_setup.title": {"en": "Problem Setup", "hu": "Probléma beállítása"},
    "problem_setup.details": {"en": "Name & description", "hu": "Név és leírás"},
    "problem_setup.method_subheader": {"en": "Weight-vector method", "hu": "Súlyvektor számítási módszer"},
    "problem_setup.method_caption": {
        "en": "Applies everywhere weights are computed (Results, Step by Step's aggregation, "
        "Sensitivity). The Step by Step page always shows both methods side by side for comparison.",
        "hu": "Mindenhol ez számít, ahol súlyokat számolunk (Eredmények, a Lépésről lépésre oldal "
        "aggregálása, Érzékenységvizsgálat). A Lépésről lépésre oldal mindig mindkét módszert "
        "megmutatja egymás mellett, összehasonlításként.",
    },
    "problem_setup.alternatives": {"en": "Alternatives", "hu": "Alternatívák"},
    "problem_setup.add_alternative": {"en": "Add an alternative", "hu": "Alternatíva hozzáadása"},
    "problem_setup.alt_name_exists": {
        "en": "An alternative named '{name}' already exists.", "hu": "Már van '{name}' nevű alternatíva.",
    },
    "problem_setup.criteria": {"en": "Criteria tree", "hu": "Szempontfa"},
    "problem_setup.criteria_caption": {
        "en": "Build the hierarchy: add main criteria, then add sub-criteria under any "
        "existing criterion. A criterion with no children is a *leaf* — pick how its "
        "alternatives get compared (pairwise, or a direct rating).",
        "hu": "Építse fel a hierarchiát: adjon hozzá főszempontokat, majd bármelyik meglévő "
        "szemponthoz alszempontokat. Az a szempont, aminek nincs alszempontja, *levélszempont* — "
        "itt választható, hogyan hasonlítjuk össze rajta az alternatívákat (páros összehasonlítás "
        "vagy közvetlen értékelés).",
    },
    "problem_setup.parent": {"en": "Parent", "hu": "Szülő szempont"},
    "problem_setup.parent_top_level": {"en": "— (main criterion)", "hu": "— (főszempont)"},
    "problem_setup.delete_criterion": {"en": "Delete (and its sub-tree)", "hu": "Törlés (a rész­fájával együtt)"},
    "problem_setup.add_criterion": {"en": "Add a criterion", "hu": "Szempont hozzáadása"},
    "problem_setup.crit_name_exists": {
        "en": "A criterion named '{name}' already exists.", "hu": "Már van '{name}' nevű szempont.",
    },
    "problem_setup.cycle_error": {
        "en": "A criterion can't be moved under itself or one of its own sub-criteria.",
        "hu": "Egy szempont nem kerülhet önmaga vagy saját alszempontja alá.",
    },
    "problem_setup.tree_empty": {
        "en": "No criteria yet — add the first main criterion below.",
        "hu": "Még nincs egyetlen szempont sem — adja meg az első főszempontot alább.",
    },
    "problem_setup.pick_node": {"en": "Choose a criterion to edit", "hu": "Válasszon szerkesztendő szempontot"},
    "problem_setup.add_subcriterion_under": {
        "en": "Add a sub-criterion under '{parent}'", "hu": "Alszempont hozzáadása '{parent}' alá",
    },
    "problem_setup.edit_node_header": {"en": "Edit '{name}'", "hu": "Szerkesztés: '{name}'"},
    "problem_setup.edit_node_header_empty": {"en": "Edit criterion", "hu": "Szempont szerkesztése"},
    "problem_setup.edit_node_placeholder": {
        "en": "Click a node in the diagram above (or use the dropdown) to edit it.",
        "hu": "Kattintson egy szempontra a fenti diagramon (vagy válasszon a legördülőből) a szerkesztéshez.",
    },
    "problem_setup.edit_root_header": {"en": "Edit goal", "hu": "Cél szerkesztése"},
    "problem_setup.edit_root_caption": {
        "en": "Editing the tree's root", "hu": "A fa gyökerének szerkesztése",
    },
    "problem_setup.goal_name_label": {"en": "Goal / root label", "hu": "Cél / gyökér felirat"},

    # -- data entry -----------------------------------------------------------------
    "data_entry.title": {"en": "Data Entry", "hu": "Adatbevitel"},
    "data_entry.caption": {
        "en": "Fill in every pairwise-comparison matrix (upper triangle only — the lower "
        "triangle is the reciprocal, filled in automatically) and every direct-rating "
        "leaf's raw values.",
        "hu": "Töltse ki az összes páros összehasonlítás mátrixot (csak a felső háromszöget "
        "kell megadni — az alsó háromszög a reciprok, automatikusan kitöltődik), valamint a "
        "közvetlen értékelésű levélszempontok nyers értékeit.",
    },
    "data_entry.need_setup": {
        "en": "Add at least one alternative and one criterion on the Problem Setup page first.",
        "hu": "Először adjon meg legalább egy alternatívát és egy szempontot a Probléma "
        "beállítása oldalon.",
    },
    "data_entry.matrix_for_root": {"en": "Main criteria", "hu": "Főszempontok"},
    "data_entry.matrix_for_children": {"en": "Sub-criteria of '{name}'", "hu": "'{name}' alszempontjai"},
    "data_entry.matrix_for_leaf": {
        "en": "Alternatives, by '{name}'", "hu": "Alternatívák, '{name}' szempont szerint",
    },
    "data_entry.missing_count": {
        "en": "{count} comparison(s) not yet entered.", "hu": "{count} összehasonlítás még hiányzik.",
    },
    "data_entry.complete_badge": {"en": "fully filled in", "hu": "teljesen kitöltve"},
    "data_entry.saaty_missing_option": {"en": "? (not entered)", "hu": "? (nincs megadva)"},
    "data_entry.missing_checkbox": {"en": "not entered", "hu": "nincs megadva"},
    "data_entry.pcm_label": {"en": "Pairwise comparison matrix:", "hu": "Páros összehasonlítás mátrix:"},
    "data_entry.enter_by_hand": {"en": "Enter exact ratios by hand", "hu": "Pontos arányok kézi megadása"},
    "data_entry.enter_by_hand_caption": {
        "en": "Type any positive ratio (not just Saaty's 1-9 scale) — e.g. 2.5 means the first "
        "item is 2.5 times more important/preferred than the second.",
        "hu": "Bármilyen pozitív arány beírható (nem csak a Saaty-féle 1-9 skála) — pl. 2,5 azt "
        "jelenti, hogy az első elem 2,5-ször fontosabb/preferáltabb a másodiknál.",
    },
    "data_entry.direct_values_caption": {
        "en": "Smaller value → reciprocal normalization. Bigger value → proportional normalization.",
        "hu": "Kisebb érték → reciprok normalizálás. Nagyobb érték → arányos normalizálás.",
    },
    "data_entry.local_weights_caption": {"en": "Local weights (current method)", "hu": "Lokális súlyok (jelenlegi módszer)"},
    "data_entry.weight_col": {"en": "Weight", "hu": "Súly"},
    "data_entry.direct_weights_caption": {
        "en": "Raw importance value for each child — normalized automatically (bigger = more important).",
        "hu": "Nyers fontossági érték minden alszemponthoz — automatikusan normalizálva (nagyobb = fontosabb).",
    },
    "data_entry.direct_result_caption": {"en": "Normalized weights", "hu": "Normalizált súlyok"},
    "data_entry.pick_matrix": {"en": "Or pick a matrix directly", "hu": "Vagy válasszon mátrixot közvetlenül"},

    # -- results ----------------------------------------------------------------------
    "results.title": {"en": "Results", "hu": "Eredmények"},
    "results.node_weights_subheader": {"en": "Local weights & consistency, by node", "hu": "Lokális súlyok és konzisztencia, csúcsonként"},
    "results.node_weights_caption": {
        "en": "Each node's own comparison, separately — a PCM's local weights and CR, or a "
        "direct-weighted node's normalized values.",
        "hu": "Minden csúcs saját összehasonlítása külön — egy PCM lokális súlyai és CR-je, vagy "
        "egy közvetlenül súlyozott csúcs normalizált értékei.",
    },
    "results.direct_weighting_badge": {"en": "✎ direct", "hu": "✎ közvetlen"},
    "results.leaf_weights_subheader": {"en": "Global leaf-criterion weights", "hu": "Levélszempontok globális súlyai"},
    "results.leaf_weights_caption": {
        "en": "Each leaf criterion's share of the total, after multiplying local "
        "weights down the tree and renormalizing over all leaves.",
        "hu": "Minden levélszempont részesedése az összsúlyból, a lokális súlyok fán "
        "lefelé szorzása és az összes levélre való újranormalizálás után.",
    },
    "results.scores_subheader": {"en": "Alternatives: total scores & ranking", "hu": "Alternatívák: összpontszámok és rangsor"},
    "results.scores_caption": {
        "en": "T_i = Σ w_k · e_ki — the weighted sum of each alternative's evaluation on "
        "every leaf criterion.",
        "hu": "T_i = Σ w_k · e_ki — az alternatíva minden levélszempont szerinti "
        "értékelésének súlyozott összege.",
    },
    "results.rank_col": {"en": "Rank", "hu": "Helyezés"},
    "results.alternative_col": {"en": "Alternative", "hu": "Alternatíva"},
    "results.score_col": {"en": "Total score", "hu": "Összpontszám"},
    "results.local_weight_col": {"en": "Local weight", "hu": "Lokális súly"},
    "results.weight_col": {"en": "Global weight", "hu": "Globális súly"},
    "results.winner_announcement": {
        "en": "**{winner}** wins. Final ranking: {ranking}.", "hu": "**{winner}** nyer. Végső rangsor: {ranking}.",
    },
    "results.download_results": {"en": "Download results (.xlsx)", "hu": "Eredmények letöltése (.xlsx)"},

    # -- step by step -----------------------------------------------------------------
    "step.title": {"en": "Step by Step", "hu": "Lépésről lépésre"},
    "step.caption": {
        "en": "A worked walkthrough of one matrix's calculation, then how its weight "
        "climbs up the tree into the final ranking. Every number here is computed with "
        "the exact same functions as the Results page.",
        "hu": "Egy mátrix számításának részletes levezetése, majd hogy a súlya hogyan "
        "kerül fel a fán a végső rangsorig. Minden itt szereplő szám ugyanazokkal a "
        "függvényekkel készül, mint az Eredmények oldalon.",
    },
    "step.pick_subheader": {"en": "1. Pick a matrix", "hu": "1. Válasszon egy mátrixot"},
    "step.pick_label": {"en": "Matrix", "hu": "Mátrix"},
    "step.matrix_subheader": {"en": "2. The pairwise-comparison matrix", "hu": "2. A páros összehasonlítás mátrix"},
    "step.methods_subheader": {"en": "3. Both weight-vector methods, side by side", "hu": "3. A két súlyvektor-módszer egymás mellett"},
    "step.methods_caption": {
        "en": "For a 3×3 matrix the two methods always coincide; for larger, "
        "inconsistent matrices they generally differ.",
        "hu": "3×3-as mátrixra a két módszer mindig megegyezik; nagyobb, "
        "inkonzisztens mátrixokra általában eltérő eredményt ad.",
    },
    "step.cr_subheader": {"en": "4. Consistency (CR)", "hu": "4. Konzisztencia (CR)"},
    "step.aggregation_subheader": {"en": "5. Climbing the tree: global weights", "hu": "5. Felfelé a fán: globális súlyok"},
    "step.aggregation_caption": {
        "en": "Each criterion's global weight is its own local weight multiplied by its "
        "parent's global weight (the root's is 1).",
        "hu": "Minden szempont globális súlya a saját lokális súlya, megszorozva a szülő "
        "globális súlyával (a gyökéré 1).",
    },
    "step.score_subheader": {"en": "6. An alternative's total score", "hu": "6. Egy alternatíva összpontszáma"},
    "step.pick_alt_label": {"en": "Alternative", "hu": "Alternatíva"},
    "step.col_leaf_criterion": {"en": "Leaf criterion", "hu": "Levélszempont"},
    "step.col_contribution": {"en": "Contribution", "hu": "Hozzájárulás"},
    "step.final_ranking": {
        "en": "Final ranking: {ranking} — '{alt}' is #{rank} of {m}.",
        "hu": "Végső rangsor: {ranking} — '{alt}' a(z) {rank}. helyen áll a(z) {m}-ből.",
    },

    # -- sensitivity --------------------------------------------------------------------
    "sensitivity.title": {"en": "Sensitivity Analysis", "hu": "Érzékenységvizsgálat"},
    "sensitivity.caption": {
        "en": "Stability intervals: as a chosen criterion's weight varies (its siblings "
        "rescaled proportionally), how far can it move before the ranking changes?",
        "hu": "Stabilitási intervallumok: ha egy kiválasztott szempont súlya változik (a "
        "testvérei arányosan újraskálázódnak), meddig változhat anélkül, hogy a rangsor "
        "megváltozna?",
    },
    "sensitivity.need_2alt_2sib": {
        "en": "Add at least two alternatives, and pick a criterion with at least one sibling.",
        "hu": "Adjon meg legalább két alternatívát, és válasszon egy olyan szempontot, "
        "amelynek van legalább egy testvére.",
    },
    "sensitivity.criterion_to_analyze": {"en": "Criterion to analyze", "hu": "Vizsgált szempont"},
    "sensitivity.stability_slider": {"en": "Keep the top-x ranking stable for x =", "hu": "Az első hány helyezett sorrendjét vizsgáljuk (x)"},
    "sensitivity.current_weight": {"en": "Current (local) weight", "hu": "Jelenlegi (lokális) súly"},
    "sensitivity.stability_success": {
        "en": "The top {top_x} stays the same while the weight of '{criterion_name}' is "
        "between {w_low} and {w_high}.",
        "hu": "Az első {top_x} helyezett sorrendje változatlan marad, amíg a(z) "
        "'{criterion_name}' szempont súlya {w_low} és {w_high} között van.",
    },
    "sensitivity.no_reversal_at_0": {
        "en": "No ranking change occurs even all the way down to weight 0.",
        "hu": "Egészen a 0 súlyig sem következik be rangsorváltozás.",
    },
    "sensitivity.no_reversal_at_1": {
        "en": "No ranking change occurs even all the way up to weight 1.",
        "hu": "Egészen az 1 súlyig sem következik be rangsorváltozás.",
    },
    "sensitivity.crossings_caption": {"en": "Ranking-changing crossings within [0, 1]:", "hu": "Rangsorváltó metszéspontok a [0, 1] intervallumban:"},
    "sensitivity.chart_title": {"en": "Sensitivity of '{name}'", "hu": "'{name}' érzékenysége"},
    "sensitivity.chart_xaxis": {
        "en": "Local weight of '{name}' within its parent", "hu": "'{name}' lokális súlya a szülőjén belül",
    },
    "sensitivity.chart_current_weight": {"en": "current weight", "hu": "jelenlegi súly"},
    "sensitivity.col_alternatives": {"en": "Alternatives", "hu": "Alternatívák"},
    "sensitivity.col_weight_at_crossing": {"en": "Weight at crossing", "hu": "Súly a metszéspontban"},
    "sensitivity.summary_subheader": {"en": "Every eligible criterion, at a glance", "hu": "Minden vizsgálható szempont áttekintése"},
    "sensitivity.summary_caption": {"en": "Stability intervals for the top-{top_x} ranking.", "hu": "Stabilitási intervallumok az első {top_x} helyezettre."},
    "sensitivity.col_criterion": {"en": "Criterion", "hu": "Szempont"},
    "sensitivity.col_current_weight": {"en": "Current weight", "hu": "Jelenlegi súly"},
    "sensitivity.col_can_decrease_to": {"en": "Can decrease to", "hu": "Csökkenthető eddig"},
    "sensitivity.col_can_increase_to": {"en": "Can increase to", "hu": "Növelhető eddig"},
    "sensitivity.col_max_change": {"en": "Max. safe change", "hu": "Max. biztonságos változás"},
    "sensitivity.unbounded": {"en": "unbounded", "hu": "korlátlan"},
    "sensitivity.most_sensitive": {
        "en": "'{criterion_name}' is the most sensitive: only a change of {max_change} "
        "flips the top-{top_x} ranking.",
        "hu": "A(z) '{criterion_name}' a legérzékenyebb: már {max_change} nagyságú "
        "változás is felborítja az első {top_x} helyezett sorrendjét.",
    },
    "sensitivity.skipped_caption": {
        "en": "Skipped (this criterion currently holds all its parent's weight, leaving "
        "no sibling to redistribute with): {names}",
        "hu": "Kihagyva (ez a szempont jelenleg a szülőjének teljes súlyát viszi, nincs "
        "testvér-szempont, amire át lehetne csoportosítani): {names}",
    },

    # -- criteria tree diagram (shared by tree_widget.py) --------------------------------
    "tree.badge_pairwise": {"en": "pairwise", "hu": "páros összeh."},
    "tree.badge_direct": {"en": "direct", "hu": "közvetlen"},
    "tree.badge_min": {"en": "min", "hu": "min"},
    "tree.badge_max": {"en": "max", "hu": "max"},
    "tree.badge_alternatives_count": {"en": "{n} alternatives", "hu": "{n} alternatíva"},
    "tree.badge_subcriteria_count": {"en": "{n} sub-criteria", "hu": "{n} alszempont"},
    "tree.badge_main_criteria_count": {"en": "{n} main criteria", "hu": "{n} főszempont"},
}


def t(key: str, **kwargs) -> str:
    lang = _current_language()
    entry = TRANSLATIONS.get(key)
    if entry is None:
        return key
    text = entry.get(lang, entry.get("en", key))
    return text.format(**kwargs) if kwargs else text


def _current_language() -> str:
    code = st.session_state.get("language")
    if code is None:
        code = _load_saved_language()
        st.session_state["language"] = code
    return code if code in LANGUAGES else "en"


def _load_saved_language() -> str:
    try:
        saved = _LANGUAGE_PATH.read_text().strip()
        if saved in LANGUAGES:
            return saved
    except Exception:
        pass
    return "en"


def _save_language(code: str) -> None:
    try:
        _LANGUAGE_PATH.write_text(code)
    except Exception:
        pass


def language_switcher() -> None:
    codes = list(LANGUAGES.keys())
    current = _current_language()
    with st.sidebar:
        chosen = st.selectbox(
            "Language / Nyelv", codes, index=codes.index(current),
            format_func=lambda code: LANGUAGES[code], key="language_switcher",
        )
    if chosen != current:
        st.session_state["language"] = chosen
        _save_language(chosen)
        st.rerun()
