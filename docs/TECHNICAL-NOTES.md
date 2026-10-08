# Technical notes: Sprint 1 risks in the current notebook

Found in a review of the draft notebook on 2026-10-09:

1. **`TEAM_ID = 1`** in the setup cell. It must be `1065`. The ID **seeds your copy of the dirty dataset**, so which stations get the unit error, time-zone shift and stuck sensor will change.
2. **`clean_basic` hard-codes fixes for seed 1001** ("Wanshouxigong CO 2014", "Huairou 2015"). With seed 2065 these will probably be wrong. Detect them from the data:
   - *Unit:* a station-year whose CO median is about 1000× below the other stations → multiply by 1000.
   - *Time zone:* a station-year whose mean daily TEMP or O3 peak hour is shifted by about 8 h → shift it back.
   - *Stuck sensor:* runs where `rolling(12).std() == 0` → NaN.
   - Print what was detected and add it to `issue_log`.
3. **Duplicate and leftover cells.** Cells 34–37 are four versions of the Task 1 audit, cells 38–44 are empty, and `# TODO` stubs sit next to filled cells. Keep one clean version per task.
4. **The final report is a Python string** that says "Team Number: 1". Make it a **markdown cell** whose numbers match the final run.
5. **The export cell is commented out.** Enable it and keep the file for Week 2.
6. **Leakage rules.** Use `test_year` only in Task 6. Fit imputers and scalers inside the pipeline. No PM10 feature. Sort by `datetime` before `TimeSeriesSplit`.
7. **Task 6 fairness.** Score both models on the *same* complete-case test rows.
8. **Ways to earn points.** Justify every decision in one line and cite numbers in every answer. Add an error-by-station plot. Mention possible MNAR bias, since sensors may fail during heavy smog.
