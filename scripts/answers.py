"""Markdown answer cells (numbers taken from the executed notebook, SEED = 2065)."""
T1 = r"""
**Answer & conclusion (Task 1)**

The merged export has **317,970 rows**, where 12 stations × 26,304 h = 315,648 are expected. The audit found 11 issues across all six dimensions (issue log above):

* **Completeness:** NO2 is missing in **6.0 %** of rows and CO in 5.7 %; the other columns are under 3.3 %. **31.8 %** of missing hours are 1-h gaps, but **28.9 %** sit in gaps longer than 3 days, so imputation must depend on gap length.
* **Uniqueness:** **1,592** exact duplicate rows, plus one re-uploaded station-month (**Tiantan, Mar 2014, 734 rows**) where only O3 differs (+1).
* **Validity:** **632** TEMP and **684** PRES `-999` codes. PM2.5 > PM10 occurs in **22,039** rows, but only **4,870** pass the neighbour test for a swap; the rest is real instrument noise.
* **Accuracy:** **Nongzhanguan CO in 2014** has a median **0.0011×** that of the other stations, i.e. it was exported in mg/m³.
* **Timeliness:** **Shunyi in 2015** peaks for TEMP at **8 h** and for O3 at **7 h**, against 14–16 h everywhere else, i.e. a UTC export (−8 h).
* **Consistency:** **36** station labels instead of 12, and **32** wind-direction labels instead of 16.
* **Stuck sensor:** the Changping PM2.5 sensor has flat runs of 24–72 h.
"""
T2 = r"""
**Answer & conclusion (Task 2)**

`clean_basic` detects every problem **from the data** (`detect_issues`) instead of hard-coding stations, so it works on next month's export or on any team seed. On our file it found `unit_CO = [(Nongzhanguan, 2014)]` and `tz_shift = [(Shunyi, 2015)]`. Verification:

* Rows: 317,970 → **315,648**, exactly 12 × 26,304 h, with **0** duplicate station-hours. There are 12 stations and 16 wind directions.
* The TEMP peak hour is now **14–15 h** for every station-year, and CO medians lie in 400–1,200 µg/m³ for all station-years.
* The time shift is undone **exactly** by rebuilding the timestamp from the hourly counter `No`. `No` agrees with the stated time for every other station. A plain +8 h would leave 8 duplicated hours on 31 Dec 2014 and 8 missing hours on 31 Dec 2015.
* After cleaning, TEMP agrees **100 %** with the original station files (sanity check only; the original files are not used to clean).
* Decisions: sentinels and impossible values → NaN. Swaps are repaired only when the swapped value fits the neighbouring hours. Each whole stuck run becomes NaN, not just its tail. For the re-uploaded month we keep the first copy, since the O3 difference is 1 µg/m³.
"""
T3 = r"""
**Answer & conclusion (Task 3)**

We hid known values for **NO2 and CO** at an urban station (Dongsi) and a suburban one (Huairou), using single-hour and 24-h masks. RMSE in µg/m³:

| gap type | best imputer | example (NO2 Dongsi) | station median |
|---|---|---|---|
| single hours | **time interpolation** (4/4 cases) | 7.7 | 33.4 |
| 24-h blocks | **KNN across stations** (4/4 cases) | 11.3 | 35.3 |

Time interpolation is unbeatable for short gaps (**7.7 vs 33.4**) but degrades on 24-h gaps (28.9). Neighbouring stations carry regional information, which KNN uses best.

**Policy:** gaps ≤ 3 h use time interpolation within the station. Longer gaps use KNN (k = 5) across the 12 stations. Hours with no station at all fall back to the station's month × hour median. Every imputed value is flagged in a `<col>_imp` column, which also goes into the Week-2 export.

The **target PM2.5 is never imputed**, because we don't train on invented labels: 2.2 % of rows are dropped as a result. That may bias towards non-smog hours if sensors fail more often during heavy pollution (possible MNAR). Imputation is worth **1.56 µg/m³ of CV RMSE** (variant A 41.73 vs B 43.29).
"""
T4 = r"""
**Answer & conclusion (Task 4)**

A Hampel filter (25 h window, k = 3) flags **14,730** PM2.5 hours. We classify a flagged hour as a **real episode** when the same hour is within 3× of the 12-station median, i.e. the whole city is high. That covers **14,082** hours: winter smog, and Spring Festival fireworks on 18–19 Feb 2015 (left plot). Real episodes are **kept**, because they are exactly what a virtual sensor must reproduce.

Only **648** isolated single-station spikes are suspicious, so we report them but don't delete them. The **errors** were removed earlier: stuck runs (Changping, right plot), `-999` codes, swaps and the unit error.

**Transforms:** PM2.5 skewness drops from **1.96 to −0.34** with log1p (−0.04 Yeo-Johnson); SO2 from 2.71 to 0.40 and CO from 2.46 to −0.03. Tree models don't need transformed features. A **log target** (variant C) actually hurt CV RMSE (45.36 vs 41.73), because it under-predicts the high peaks that dominate RMSE, so we do not use it.
"""
T5 = r"""
**Answer & conclusion (Task 5)**

Everything that learns (median imputer, missing indicators, scaler, one-hot encoder) lives inside the `Pipeline`, so it is re-fitted in each of the 5 `TimeSeriesSplit` folds on data sorted by time. PM10 is never a feature. The test year is not touched here.

| variant | CV RMSE ± sd (µg/m³) |
|---|---|
| A: Task-3 imputation + median/indicator pipeline | 41.73 ± 9.84 |
| B: no Task-3 imputation | 43.29 ± 11.48 |
| C: A + log1p target | 45.36 ± 16.20 |
| **D: A + trailing 3 h / 24 h rolling means of gases & weather** | **38.31 ± 5.87** |

**D wins and is also the most stable** (sd 5.87). Its rolling features only use past hours, so they are causal and leak-free. They only make sense on a de-duplicated, time-corrected, gap-free hourly series, which is a direct pay-off of cleaning.

The Part-A demo shows why the split matters: a random KFold reports **29.71**, against **42.32** for a time split on the same model. Random splits leak neighbouring hours.
"""
T6 = r"""
**Answer & conclusion (Task 6)**

Both models are scored on the **same 97,979 complete-case rows** of the untouched test year (Mar 2016 – Feb 2017):

| model | RMSE | MAE | R² |
|---|---|---|---|
| naive: merged export, dropna | 36.97 | 22.22 | 0.798 |
| cleaned data, same model | 36.76 | 22.01 | 0.801 |
| **cleaned + imputation + pipeline D** | **34.51** | **20.68** | **0.824** |

* The full pipeline lowers RMSE by **6.7 %** and MAE by **6.9 %**, and R² rises by **+0.026**. **All 12 stations improve**, by 1.3–3.8 µg/m³; the biggest gain is at Changping, the station with the stuck sensor.
* Cleaning alone gives a small gain with the same model, because gradient boosting is robust to a single bad station-year. The naive model also loses **36,269 training rows (12 %)** to `dropna`.
* The bigger win comes from what clean data **enables**: a correct, continuous hourly series per station makes the rolling-history features valid.
"""
HPC = r"""
**Answer & conclusion (bonus)**

The 12 stations are independent tasks for `joblib` (loky backend). We take the best of 3 runs of `clean_basic` + per-station imputation:

| workers p | T_p (s) | S_p = T_1/T_p | E_p = S_p/p |
|---|---|---|---|
| 1 | 2.84 | 1.00 | 1.00 |
| 2 | 1.89 | 1.51 | 0.75 |
| 4 | 1.33 | 2.13 | 0.53 |
| 12 | 0.97 | **2.92** | 0.24 |

(Exact timings vary by a few % between runs; see the table above.)

**Dominant step:** `clean_basic` takes about 0.13 s per station against about 0.06 s for `impute_station`. Speed-up saturates near 3× because each task is tiny (around 0.2 s). Starting processes and pickling about 26k-row DataFrames to the workers is a large serial fraction (Amdahl's law).

With 12 equal tasks, p = 12 gives one task per core; a p that does not divide 12 leaves cores idle in the last round. The cross-station KNN step (about 50 s) cannot be split by station. It would parallelise by **column** instead (9 independent pollutant/weather pivots), which is the next optimisation.
"""
SUMMARY = r"""
## Final summary — Team LineShine (ID 1065)

**1 · Findings (issue log).** The agency's merged export (317,970 rows) had 11 issues across all six quality dimensions:
* Consistency: 36 station labels and 32 wind-direction labels.
* Accuracy: Nongzhanguan CO for 2014 in mg/m³ (×1000 low).
* Timeliness: Shunyi 2015 exported in UTC (TEMP peak at 8 h instead of 14 h).
* Validity: 632 + 684 `-999` codes, 4,870 PM2.5/PM10 swaps, stuck PM2.5 runs at Changping.
* Uniqueness: 1,592 exact duplicates and a re-uploaded Tiantan month (734 rows).
* Completeness: NO2 missing 6.0 %; 29 % of missing hours are in gaps longer than 3 days.

All issues were detected from the data and fixed by one reusable `clean_basic`. The result is exactly 315,648 rows (12 × 26,304 h) with no duplicates.

**2 · Key decisions.**
* Imputation by gap length: ≤ 3 h → time interpolation (NO2 RMSE 7.7 vs 33.4 for the median); longer → KNN across stations (11.3 vs 35.3 on 24-h gaps). Every imputed value is flagged.
* The target PM2.5 is never imputed, so 2.2 % of rows are dropped. **Possible bias:** if sensors fail during heavy smog (MNAR), extreme hours are under-represented.
* Outliers: 14,082 of 14,730 Hampel flags are city-wide real episodes (smog, Spring Festival 2015) and are kept. Only instrument errors are removed.
* Transforms: log1p reduces PM2.5 skew from 1.96 to −0.34, but a log target hurt RMSE, so it is not used.
* The pipeline is leak-free (all fitting inside `Pipeline`, `TimeSeriesSplit`, no PM10, test year only in Task 6) and adds causal 3 h / 24 h rolling features.

**3 · Impact (test year, same 97,979 rows).** Naive RMSE **36.97** / MAE 22.22 / R² 0.798 → ours **34.51** / **20.68** / **0.824**. That is **−6.7 % RMSE** and every station improves; see the predicted-vs-actual and per-station plots in Task 6. CV RMSE goes from 43.29 (no imputation) to **38.31 ± 5.87**.

**4 · Lessons for the agency.**
* Export with a fixed schema: canonical station codes, upper-case compass labels, units in the header, and **timestamps in ISO-8601 with a time zone**.
* Use NaN instead of `-999`.
* Run a unique key (station, datetime) and range checks before merging.
* Add a stuck-sensor alarm (no change for 12 h or more).
* Log re-uploads instead of appending them.

**5 · HPC (bonus).** Per-station cleaning with joblib takes 2.84 s on 1 worker and 0.97 s on 12: **S = 2.9×, E = 0.24**. It is limited by the small per-task work against process/pickling overhead (Amdahl). The dominant step is `clean_basic`, and the next step would be to parallelise KNN by column.

**Deliverables:** this notebook, and `beijing_clean_team1065.csv.gz` (315,648 rows, cleaned + imputed, with `_imp` flags) as the Week-2 input.
"""
