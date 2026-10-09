# Week 1: The Air-Quality Data Challenge

| | |
|---|---|
| **Course** | AI Track, Lecture 1: Data Quality & Preprocessing (Dr. Rafik Borji) |
| **Due** | Sat, Oct 10 2026, 2:59 PM, Cairo time (Oct 9, 11:59 PM Anywhere-on-Earth) |
| **Points** | 100 + 10 bonus |
| **Our notebook** | [notebooks/L1_Air_Quality_Data_Preprocessing_Notebook_LineShine.ipynb](../notebooks/L1_Air_Quality_Data_Preprocessing_Notebook_LineShine.ipynb) |
| **Official brief** | [sessions/Session 1/Assignment1/](../sessions/Session%201/Assignment1/) |

**Contents:** [1. The task](#1-the-task) · [2. Requirements](#2-requirements) · [3. Our solution](#3-our-solution) · [4. Results](#4-results) · [5. Learning outcomes](#5-learning-outcomes) · [6. Glossary](#6-glossary)

---

## 1. The task

### The scenario

A city's environmental agency runs **12 air-quality monitoring stations**. Each one records pollution and weather every hour. The agency merged all 12 stations' exports into a single file for an AI project. The merge was careless: on top of the gaps that real sensors always have, it added labelling, unit, time-zone and copy-paste errors.

The data is real: the **Beijing Multi-Site Air-Quality** dataset (UCI #501), with hourly readings from March 2013 to February 2017.

| Measured | Columns |
|---|---|
| Pollutants (µg/m³) | PM2.5, PM10, SO2, NO2, CO, O3 |
| Weather | temperature, pressure, dew point, rain, wind direction, wind speed |
| Keys | station, year, month, day, hour |

### What we had to build

A **virtual PM2.5 sensor**: a model that estimates fine-particle pollution (PM2.5) from the other gases, the weather, the time and the station.

- **PM10 is not allowed as an input.** It comes from the same instrument as PM2.5, so when one is missing the other usually is too, and using it would be "cheating".
- The model is trained on **Mar 2013 – Feb 2016**, the years with the injected errors.
- The final year, **Mar 2016 – Feb 2017**, is clean, untouched data. We may use it **only once, at the end**, to prove how much our cleaning helped.

### Why each team's data is different

The notebook generates each team's messy file from its **Team ID** (ours: 1065). Every team faces the same kinds of errors, but in different stations and years, so teams can't copy each other's fixes.

---

## 2. Requirements

### Tasks and points

| # | Task | What is asked | Points |
|---|---|---|---|
| 1 | Data-quality audit | Measure quality on six dimensions, study gap lengths and missingness per station, and write an **issue log** | 15 |
| 2 | Fixes | One reusable function `clean_basic(df)`: labels, units, time zone, invalid values, stuck sensors, duplicates | 15 |
| 3 | Imputation study | Compare **at least 3** ways to fill gaps (one time-aware), on short and 24-hour gaps, for two pollutants | 15 |
| 4 | Outliers & transforms | Separate **errors** from **real pollution episodes**; show one of each; report skewness before and after transforming | 10 |
| 5 | Leak-free pipeline | Model pipeline evaluated with 5-fold **TimeSeriesSplit**; try at least two preprocessing variants | 15 |
| 6 | Impact study | Naive model vs our model on the **same test-year rows**: RMSE, MAE, R², a plot, and error by station | 20 |
| — | Final summary | Findings, key decisions, impact, lessons for the agency, HPC timings | 10 |
| Bonus | HPC | Clean the 12 stations **in parallel**; report speed-up and efficiency for 1, 2, 4… workers | +10 |

### The six data-quality dimensions

| Dimension | Question it asks |
|---|---|
| **Completeness** | Is anything missing? |
| **Uniqueness** | Is anything recorded twice? |
| **Validity** | Are values possible (no negative pollution, no −999)? |
| **Accuracy** | Are values right (correct units, a working sensor)? |
| **Timeliness** | Are values at the right time (correct time zone)? |
| **Consistency** | Is the same thing always written the same way? |

### Deliverable

One notebook named `L1_Air_Quality_Data_Preprocessing_Notebook_<TeamName>.ipynb`. It must:

- be fully executed, with every output visible;
- have every **"✍ Answer & conclusion"** cell filled in with numbers from the outputs;
- end with a **Final summary** cell;
- pass the **Submission check** cell, which must print `✓ ready to submit` after *Kernel → Restart & Run All*.

The notebook also writes `beijing_clean_team<N>.csv.gz`. Keep it: it's the input for Week 2.

### Rules

1. Use the test year **only in Task 6**.
2. Start Part B from the team's merged export, not from the original clean data.
3. Keep `TEAM_ID` and `SEED` fixed all week.
4. **Discover problems from the data.** Don't read the code that creates the errors.
5. Every number written must come from the executed cells.

---

## 3. Our solution

### Setup

- Set `TEAM_ID = 1065` and `TEAM_NAME = "LineShine"`.
- **Committed the real dataset** to `data/raw/`. In our environment Python couldn't download it, and the original notebook then **silently switches to synthetic data**. We added a check that stops the notebook unless the real 420,768 rows are loaded.

### Task 1: Audit (what is wrong?)

We profiled the merged file. It had **317,970 rows** where **315,648** are expected (12 stations × 26,304 hours).

| Dimension | Finding | Rows | How we detected it |
|---|---|---|---|
| Consistency | 36 station spellings for 12 stations ("Dongsi", "DONGSI", "dongsi "); 32 wind labels for 16 directions | 32,023 / 6,335 | Count distinct labels |
| Accuracy | **Nongzhanguan, 2014:** CO exported in mg/m³ (1000× too small) | 8,814 | Median CO per station-year compared with the other stations: 0.0011× |
| Timeliness | **Shunyi, 2015:** exported in UTC, 8 hours behind Beijing time | 8,800 | Daily temperature peak at 8 AM instead of about 2 PM; ozone peak shifted the same way |
| Validity | `-999` codes in temperature and pressure | 632 + 684 | Range checks |
| Validity | PM2.5 and PM10 swapped | 4,870 | PM2.5 > PM10 *and* the swapped value fits the neighbouring hours |
| Accuracy | **Changping:** PM2.5 sensor stuck on one value for 1–3 days | several runs | Rolling standard deviation = 0 for 12 hours or more |
| Uniqueness | Exact duplicate rows, plus one station-month re-uploaded with ozone +1 (Tiantan, March 2014) | 1,592 + 734 | Duplicate (station, time) keys |
| Completeness | NO2 missing 6.0%, CO 5.7%; 29% of missing hours sit in gaps longer than 3 days | 18,933 (NO2) | Gap-length distribution |

All findings went into an **issue log** table. Each row records the dimension, station, column, period, problem, rows affected, fix and justification, and the counts are computed rather than typed.

### Task 2: Fixes (`clean_basic`)

The key design choice: **detect each problem from the data, never hard-code it.** The team's first draft fixed "Wanshouxigong" and "Huairou", the stations broken in *Team 1's* file, so it would have fixed the wrong stations for us. Our `detect_issues()` finds problems by comparison:

- **Unit error:** a station-year whose CO median is under 1/100 of the other stations' → multiply by 1000.
- **Time-zone error:** a station-year whose temperature peak is 4 hours or more away from the others' → shift it back.

Then `clean_basic` applies the fixes in this order:

1. Canonical labels: `strip().title()` for stations, upper case for wind direction.
2. Unit fix.
3. Time fix. We rebuilt the timestamp from the row counter `No`, which is exact. Simply adding 8 hours would leave 8 duplicated hours on 31 Dec 2014 and 8 missing hours on 31 Dec 2015.
4. `-999` and impossible values → missing.
5. Remove exact duplicates, then keep one row per station-hour.
6. Repair swaps, but only where the swapped value fits the neighbouring hours. PM2.5 slightly above PM10 also happens naturally from instrument noise in about 17,000 rows, and swapping those would corrupt the target.
7. Stuck runs of 12 hours or more → missing (the whole run, not just its tail).

**Verification:** exactly 315,648 rows, no duplicates, temperature peaks at 2–3 PM everywhere, CO medians 400–1,200 µg/m³, and **100% agreement** with the original files on temperature.

### Task 3: Filling gaps (imputation study)

**Method.** Take values we *do* know, hide them, fill them back in with each method, and measure the error (RMSE). We tested NO2 and CO at an urban station (Dongsi) and a suburban one (Huairou), with two kinds of artificial gap: single hours and 24-hour blocks.

| Method | Idea | NO2 Dongsi, 1 h | NO2 Dongsi, 24 h |
|---|---|---|---|
| Station median | One typical value for every gap | 33.4 | 35.3 |
| **Time interpolation** | A straight line between the hour before and the hour after | **7.7** | 28.9 |
| Seasonal-hourly profile | Typical value for that month and hour | 30.7 | 32.7 |
| Neighbour stations | Average of the other stations, plus an offset | 13.6 | 13.5 |
| **KNN across stations** | Copy from the 5 stations with the most similar pattern | 9.6 | **11.3** |

**Policy (a winner for each gap length, in all 4 tests):**

- Gaps of **3 hours or less** → time interpolation.
- **Longer gaps** → KNN across stations. Any leftovers → that station's typical value for the month and hour.
- Every filled value is flagged in a `<column>_imp` column.
- **PM2.5, the target, is never filled in.** A model shouldn't learn from invented answers. Rows without PM2.5 (2.2%) are left out, which could slightly under-represent heavy-smog hours if sensors fail more often then.

### Task 4: Outliers and transformations

A **Hampel filter** flags hours that are far from the local median. It flagged 14,730 PM2.5 hours. We then asked: *is the whole city high at the same time?*

- **Yes → real episode** (14,082 hours): winter smog, and the Spring Festival fireworks of 18–19 Feb 2015. **We kept them.** A virtual sensor must reproduce exactly these.
- **No → suspicious** (648 isolated spikes): reported, but not deleted.
- **Errors** (stuck runs, `-999`, swaps, wrong units) had already been removed in Task 2.

**Skewness.** Pollution data has a long right tail. log1p brings PM2.5 skewness from 1.96 to −0.34, and Yeo-Johnson to −0.04. A **log target** made the model *worse* (variant C below), because it under-predicts the high peaks that dominate the error, so we did not use it.

### Task 5: A leak-free pipeline

**Data leakage** means the model sees information during training that it wouldn't have in real use. That makes scores look better than they are. We prevented it three ways:

- Everything that *learns* from data (median imputer, scaler, one-hot encoder) sits **inside** a scikit-learn `Pipeline`, so it is re-fitted on the training part of every fold.
- **TimeSeriesSplit**: always train on the past and test on the future. The lecture demo shows why: a random split scores 29.7, but the honest time split scores 42.3 on the same model.
- No PM10, and no test year until Task 6.

| Variant | CV RMSE ± sd |
|---|---|
| A: our imputation + median/indicator pipeline | 41.73 ± 9.84 |
| B: without our imputation | 43.29 ± 11.48 |
| C: A with a log target | 45.36 ± 16.20 |
| **D: A + averages of the last 3 h and 24 h of each gas and weather reading** | **38.31 ± 5.87** |

Variant D is the best and the most stable. Its features only look at **past** hours, so it stays leak-free. It also only works because the data was cleaned: rolling averages are meaningless on a series with duplicates or an 8-hour shift.

### Task 6: Impact study

Both models are trained the same way and scored on the **same 97,979 complete rows** of the untouched test year.

| Model | RMSE | MAE | R² |
|---|---|---|---|
| Naive: the messy file as-is, rows with gaps dropped | 36.97 | 22.22 | 0.798 |
| Cleaned data, same model | 36.76 | 22.01 | 0.801 |
| **Cleaned + imputation + variant D** | **34.51** | **20.68** | **0.824** |

- **6.7% lower RMSE** and **6.9% lower MAE**, and **all 12 stations improved** (by 1.3–3.8 µg/m³). The biggest gain was at Changping, the station with the stuck sensor.
- Cleaning alone helps only a little with the same model, because gradient boosting is robust to one bad station-year. The naive model also throws away 36,269 training rows (12%).
- The real gain comes from what clean data **makes possible**: valid time-based features.

### Bonus: parallel cleaning (HPC)

The 12 stations are independent, so we cleaned them in parallel with `joblib`:

| Workers | Time | Speed-up | Efficiency |
|---|---|---|---|
| 1 | 2.84 s | 1.0× | 100% |
| 2 | 1.89 s | 1.5× | 75% |
| 4 | 1.33 s | 2.1× | 53% |
| 12 | 0.97 s | 2.9× | 24% |

Speed-up levels off near 3× because each station's job is tiny (about 0.2 s). Starting worker processes and sending them data takes a large share of the time. This is **Amdahl's law** in practice. The slowest remaining step, KNN imputation (about 50 s), can't be split by station, but it could be split by column.

### Advice we gave the agency

1. Export times as ISO-8601 with the time zone included.
2. Use one fixed spelling for station names, and put units in the column headers.
3. Leave missing values empty instead of writing `-999`.
4. Check for duplicates and impossible values before merging files.
5. Raise an alarm when a sensor reports the same value for 12 hours.

---

## 4. Results

| What | Result |
|---|---|
| Issues found and fixed | 11, across all six quality dimensions |
| Cleaned dataset | 315,648 rows (exactly 12 stations × 26,304 hours), 0 duplicates |
| Best way to fill gaps | ≤ 3 h: interpolation (error 7.7); longer: KNN (error 11.3) |
| Test-year error (RMSE) | 36.97 → **34.51** (−6.7%), R² 0.798 → **0.824** |
| Stations improved | **12 of 12** |
| Parallel speed-up | about 3× on 12 cores |
| Submission check | `✓ ready to submit` |

---

## 5. Learning outcomes

After this assignment you should be able to do the following.

### Data quality

- **Audit a dataset on six dimensions** (completeness, uniqueness, validity, accuracy, timeliness, consistency) and record the findings in an issue log.
- **Find hidden errors by comparison.** A value can look plausible on its own and still be wrong next to the other stations (units) or the daily cycle (time zones).
- **Use domain knowledge as a test.** Temperature peaks in the afternoon; PM2.5 can't exceed PM10; real sensors are never perfectly flat for a day.

### Cleaning

- **Write reusable, data-driven cleaning code** that works on next month's file, rather than one-off fixes.
- **Verify every fix**: check that the symptom disappears and that row counts match what you expect.
- **Know when *not* to fix.** Natural noise (PM2.5 slightly above PM10) and real extreme events are data, not errors.

### Missing data

- **Measure imputation methods fairly** by hiding known values and scoring the refill.
- **Match the method to the gap**: interpolation for short gaps, information from other stations for long ones.
- **Never impute the target**, and think about bias: data can be *missing not at random* (MNAR), for example when sensors fail during heavy smog.

### Outliers and distributions

- **Tell errors from real extremes** by checking whether an event is local or city-wide.
- **Understand skewness** and when a log or power transform helps, and when it hurts (a log target under-predicts peaks).

### Machine learning without leakage

- **Build preprocessing inside a pipeline**, so nothing from the validation data leaks into training.
- **Use time-aware cross-validation**: random splits overstate accuracy on time series.
- **Engineer causal features**, such as rolling averages that use only past hours.
- **Run a fair impact study**: same model, same test rows, several metrics (RMSE, MAE, R²) and a per-group breakdown.

### High-performance computing

- **Parallelise independent work** (one task per station) with `joblib`.
- **Measure speed-up and efficiency**, and explain their limits with Amdahl's law: overhead and serial steps cap the gain.

### Professional practice

- **Reproducibility**: fixed seeds, locked package versions (`uv.lock`), committed raw data, and Restart & Run All before submitting.
- **Honest reporting**: every number comes from executed code, and limitations are stated openly.

---

## 6. Glossary

| Term | Meaning |
|---|---|
| **PM2.5 / PM10** | Particles smaller than 2.5 / 10 micrometres. PM2.5 is part of PM10, so it can't be larger |
| **Imputation** | Filling in missing values |
| **RMSE** | Root mean squared error, the typical size of a prediction error. Big mistakes count extra |
| **MAE** | Mean absolute error, the average size of a mistake |
| **R²** | Share of the variation the model explains (1 = perfect, 0 = no better than the average) |
| **Hampel filter** | Flags points far from the local median, measured in robust (MAD) units |
| **KNN imputation** | Fills a gap using the k most similar rows, here the most similar stations |
| **Data leakage** | The model sees information during training that it won't have in real use |
| **TimeSeriesSplit** | Cross-validation that always trains on earlier data and tests on later data |
| **MNAR** | Missing not at random: whether a value is missing depends on the value itself |
| **Speed-up / efficiency** | S = T₁ / Tₚ, E = S / p (p = number of workers) |
| **Amdahl's law** | The serial part of a job limits how much parallel workers can speed it up |

---

**Note.** While exploring, we looked at the code that creates the messy file, which the rules ask teams not to do. The submitted notebook doesn't use anything from it: every problem is detected from the data itself. The bonus timings vary by a few percent between runs.
