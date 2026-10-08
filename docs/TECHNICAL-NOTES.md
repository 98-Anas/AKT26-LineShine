# Technical notes

## How the notebook is built
- `notebooks/original/` holds the untouched course notebook.
- `scripts/build_notebook.py` keeps Part A (with `TEAM_ID = 1065`, `TEAM_NAME = "LineShine"`, and data read from `data/raw/`) and writes Part B. Answer and summary text live in `scripts/answers.py`.
- Rebuild, then execute:
  ```bash
  uv run python scripts/build_notebook.py
  cd notebooks && uv run jupyter nbconvert --to notebook --execute --inplace L1_Air_Quality_Data_Preprocessing_Notebook_LineShine.ipynb
  ```
  A full run takes about 10 minutes on 12 cores.
- If you change code, re-check the numbers quoted in `scripts/answers.py`.

## Problems found in the first draft (all fixed on 2026-10-09)
| Problem | Fix |
|---|---|
| `TEAM_ID = 1` | Set to 1065. The seed decides which stations get which errors |
| `clean_basic` hard-coded Wanshouxigong/Huairou (seed 1001) | `detect_issues()` finds them in the data. For seed 2065 it finds **Nongzhanguan CO 2014** and **Shunyi UTC 2015** |
| Python's UCI download failed, so the notebook **silently used synthetic data** | Real UCI CSVs are committed in `data/raw/`, plus an assert that 420,768 real rows are loaded |
| 4 duplicate Task-1 cells, empty cells, TODO stubs | One clean cell set per task |
| Report was a Python string saying "Team 1" | Markdown answer cells and a Final summary with real numbers |
| Export cell commented out | `beijing_clean_team1065.csv.gz` is exported |
| Swapping all 22,039 rows with PM2.5 > PM10 corrupted the target | Swap only where the swapped value fits the neighbouring hours (4,870 rows) |
| No "Submission check" cell in our copy | Added our own check. **Compare with the official notebook on Google Drive and paste the official check cell if it differs** |

## Key results (seed 2065)
- Test year: naive RMSE 36.97 → **34.51** (−6.7 %), R² 0.798 → **0.824**; all 12 stations improve.
- CV (TimeSeriesSplit 5): **38.31 ± 5.87** with rolling features.
- HPC: S₁₂ ≈ 3×.
