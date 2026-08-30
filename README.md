# AHP Playground

An educational tool for the Analytic Hierarchy Process (AHP): build a
criteria tree of any depth, weigh it with pairwise-comparison matrices
(Saaty's 1-9 scale, exact ratios, or incomplete matrices) or direct
scoring, and rank a set of alternatives against it. Includes a full
worked walkthrough of the underlying math (eigenvector method and LLSM
side by side), weight sensitivity analysis with stability intervals, and
Excel import/export. Available in English and Hungarian.

- **Problem Setup** — alternatives, a criteria tree (any depth), weight-vector method (eigenvector / LLSM)
- **Data Entry** — pairwise comparison matrices (Saaty 1-9 scale or exact ratios, incomplete matrices allowed) or direct-value scoring, per node
- **Results** — total scores & ranking, global leaf-criterion weights, local weights & CR by node
- **Step by Step** — a full worked walkthrough of one matrix's calculation, both weight-vector methods side by side, and how a node's weight climbs the tree into an alternative's final score
- **Sensitivity** — stability intervals for any criterion's weight, with a chart of every alternative's score as that weight varies

If you don't want to use a terminal at all, there are ready-to-run
Mac/Windows packages (no Python install needed) on the
[Releases](../../releases) page instead of the steps below.

## Installation

You'll need Python 3 already installed for this to work (the packaged
Mac/Windows releases above don't need this — only this terminal route
does). Get it from [python.org](https://www.python.org/downloads/) if you
don't have it yet — during installation on Windows, make sure to check the
box that says "Add python.exe to PATH".

### 1. Open a terminal

- **Mac:** press `Cmd + Space`, type `Terminal`, press Enter.
- **Windows:** press the Start key, type `cmd`, press Enter.

Every command below is typed into that same window, one line at a time,
pressing Enter after each.

### 2. Get the code

**Option A — with git:**
```
git clone https://github.com/kissmarci00/ahp.git
cd ahp
```

**Option B — without git:** click the green **Code** button near the top of
this page → **Download ZIP**, then unzip it. Back in the terminal, type
`cd ` (with a trailing space, don't press Enter yet), then drag the
unzipped folder into the terminal window — its path gets typed in for you —
and press Enter.

### 3. Install dependencies

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

On Windows, use this instead for the second line:
```
.venv\Scripts\activate
```

## Running

```
streamlit run dashboard.py
```

Your browser should open automatically. If it doesn't, look in the
terminal for a line starting with `Local URL:` and open that address by
hand — usually `http://localhost:8501`, but it can be a different port if
8501 is already in use.

Next time you want to run the app, you don't need to reinstall anything:
open a terminal, `cd` into the `ahp` folder again, run
`source .venv/bin/activate` (Windows: `.venv\Scripts\activate`), then
`streamlit run dashboard.py`.

See `instructions.txt` for a plain-language, screenshot-free walkthrough
(handy to hand to non-technical users).

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
