# Task Tracker

Status: ⬜ To Do · 🟨 In Progress · 🟦 Review · ✅ Done · 🟥 Blocked

The live board is the GitHub Project, which `scripts/setup_github.ps1` creates. This file is the offline copy.

## Sprint 1: Air-Quality Data Challenge (due Oct 9 2026 AoE)
| ID | Task | Owner | Pts | Status | Notes |
|---|---|---|---|---|---|
| S1-00 | Rename notebook, set `TEAM_ID=1065` / `TEAM_NAME`, regenerate dataset | Abdallah | — | 🟨 | Renamed copy is in `notebooks/`. **TEAM_ID is still 1** |
| S1-01 | T1a–f audit: completeness, uniqueness, validity, accuracy, timeliness, consistency | Omar | 15 | 🟨 | Drafts exist. Merge duplicate cells 34–37 into one |
| S1-02 | Fill `issue_log` (≥1 row per detected problem) | Omar | (T1) | ⬜ | |
| S1-03 | `clean_basic(df)` with data-driven detection | Abdulrahman | 15 | 🟨 | Hard-codes Wanshouxigong/Huairou from seed 1001 |
| S1-04 | Imputation: 3+ imputers × PM2.5 and one gas × 1 h / 24 h masks, strategy per gap length | Anas | 15 | 🟨 | |
| S1-05 | Outliers: error vs real-episode plots, skewness before/after | Mohamed A. | 10 | 🟨 | Use Spring Festival and winter smog as real episodes |
| S1-06 | Pipeline + TimeSeriesSplit(5) RMSE ± sd, ≥2 variants | Mohamed S. | 15 | 🟨 | Missing indicators, log-target |
| S1-07 | Impact: RMSE/MAE/R², pred-vs-actual plot, error by station | Mohamed S. / Abdallah | 20 | 🟨 | Same complete-case test rows for both models |
| S1-08 | HPC bonus: 1/2/4/all workers, S_p, E_p, dominant step | Anas | +10 | 🟨 | |
| S1-09 | Final summary **markdown** cell | Abdallah | 10 | 🟨 | Current text says "Team Number: 1" |
| S1-10 | Export `beijing_clean_team1065.csv.gz` | Abdulrahman | — | ⬜ | Cell is commented out |
| S1-11 | Restart & Run All → Submission check → upload form | Abdallah | — | ⬜ | |

## Future sprints
| Sprint | Assignment | Dates |
|---|---|---|
| S2 | Week-2 AI Methods Shoot-out (input: the S1 clean export) | TBA |
| S3 | TBA | TBA |
| S4 | TBA | TBA |
| S5 | Final | by Nov 7 2026 |
