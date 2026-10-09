# Sprint 1: The Air-Quality Data Challenge (Week 1)

**Deadline:** Sat, Oct 10 2026, 2:59 PM Cairo time (= Oct 9, 11:59 PM AoE) · **Points:** 100 + 10 bonus

**Sprint goal:** submit one fully executed notebook that passes the Submission check. It must contain a cleaned, leak-free virtual PM2.5 sensor that measurably beats the naive model on the 2016–17 test year. Also export `beijing_clean_team1065.csv.gz` for Week 2.

## Scope
| # | Task | Pts |
|---|---|---|
| 1 | Data-quality audit + issue log | 15 |
| 2 | `clean_basic(df)`: consistency, validity, timeliness | 15 |
| 3 | Imputation study (≥3 imputers, 2 pollutants, 1 h and 24 h masks) | 15 |
| 4 | Outliers (stuck/spikes vs real episodes) + transforms | 10 |
| 5 | Leak-free pipeline + 5-fold `TimeSeriesSplit` | 15 |
| 6 | Impact study: naive vs cleaned on the test year | 20 |
| — | Final summary cell | 10 |
| ★ | HPC bonus: joblib per-station speed-up | +10 |
| — | Integration, Restart & Run All, Submission check, upload | — |

**Dependencies:** T1 → T2 → (T3, T4) → T5 → T6 → Summary. `clean_basic` blocks everyone, so it comes first.

## Sprint Definition of Done
- [ ] File named `L1_Air_Quality_Data_Preprocessing_Notebook_LineShine.ipynb`
- [ ] `TEAM_ID = 1065`, `TEAM_NAME = "LineShine"`
- [ ] Restart & Run All finishes with no errors
- [ ] Every "Answer & conclusion" cell uses real numbers
- [ ] Final summary: issue log, key decisions, impact (metrics + 1 plot), lessons, HPC timings
- [ ] Submission check prints **"ready to submit"**
- [ ] `beijing_clean_team1065.csv.gz` exported and kept
- [ ] Uploaded through the Google Form by the team leader with Team ID 1065
