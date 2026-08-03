# AHP Playground

An educational Streamlit app for the Analytic Hierarchy Process (pairwise-comparison matrices, GB/HU bilingual): build a criteria tree, weigh it, evaluate alternatives, and see how stable the result is.

- **Problem Setup** — alternatives, a criteria tree (any depth), weight-vector method (eigenvector / LLSM)
- **Data Entry** — pairwise comparison matrices (Saaty 1-9 scale or exact ratios, incomplete matrices allowed) or direct-value scoring, per node
- **Results** — total scores & ranking, global leaf-criterion weights, local weights & CR by node
- **Step by Step** — a full worked walkthrough of one matrix's calculation, both weight-vector methods side by side, and how a node's weight climbs the tree into an alternative's final score
- **Sensitivity** — stability intervals for any criterion's weight, with a chart of every alternative's score as that weight varies

Includes an Excel import/export round-trip (Home page) — see `examples/` for two ready-to-import sample problems.

## Requirements

- Python 3.10+

## Setup (Windows, Command Prompt)

```
py -m venv .venv
.venv\Scripts\activate.bat
pip install -r requirements.txt
```

## Setup (macOS/Linux)

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running

```
streamlit run dashboard.py
```

Your browser should open automatically at http://localhost:8501. If it doesn't, open that address yourself. See `instructions.txt` for a plain-language, screenshot-free walkthrough (handy to hand to non-technical users).

## Tests

```
pytest
```

## Project layout

- `ahp_core/` — the math/data model, no Streamlit dependency (PCM solving, hierarchy aggregation, sensitivity, Excel I/O)
- `pages/` — the Streamlit UI, one file per page
- `dashboard.py`, `app_state.py`, `i18n.py`, `tree_widget.py` — app shell, session state, translations, the shared tree diagram widget
- `examples/` — sample problems importable from the Home page, plus the script that generated the apartment-choice one
- `tests/` — pytest suite for `ahp_core/`
