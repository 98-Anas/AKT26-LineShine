# Week 1: The Air-Quality Data Challenge

**Due:** Sat, Oct 10 2026, 2:59 PM (Cairo time) · **Points:** 100 + 10 bonus
**Notebook:** [notebooks/L1_Air_Quality_Data_Preprocessing_Notebook_LineShine.ipynb](../notebooks/L1_Air_Quality_Data_Preprocessing_Notebook_LineShine.ipynb)
**Official brief:** [sessions/Session 1/Assignment1/](../sessions/Session%201/Assignment1/)

## The story

A city's environmental agency combined the data from its 12 air-quality stations into one file, and made mistakes along the way.
Our job was to:

1. **Find** every mistake in the file.
2. **Fix** them with code that would also work on next month's file.
3. **Fill in** missing values sensibly.
4. Build a **"virtual PM2.5 sensor"**: a model that estimates fine dust (PM2.5) from other gases, the weather, the time and the station, without using PM10 (it comes from the same instrument).
5. **Prove** that cleaning helped, by testing on a final year of data that we never touched before the end.

Every team gets a slightly different messy file, because the mistakes are generated from the Team ID. Ours is **1065**.

---

## What was wrong with our file

The file had 317,970 rows. 12 stations × 26,304 hours should give 315,648.

| Kind of problem | What we found | How many rows |
|---|---|---|
| Inconsistent names | The same station written in 3 ways ("Dongsi", "DONGSI", "dongsi "), giving 36 names for 12 stations. Wind directions in both upper and lower case. | 32,023 station · 6,335 wind |
| Wrong units | **Nongzhanguan**, 2014: CO was in mg/m³ instead of µg/m³, so the values were 1000× too small. | 8,814 |
| Wrong time zone | **Shunyi**, 2015: times were in UTC, 8 hours behind Beijing. We spotted it because the daily temperature peak sat at 8 AM instead of about 2 PM. | 8,800 |
| Fake numbers | `-999` written instead of "missing" in temperature and pressure. | 632 + 684 |
| Swapped columns | PM2.5 and PM10 swapped in some rows. | 4,870 |
| Stuck sensor | **Changping**'s PM2.5 sensor repeated the same number for 1–3 days at a time. | several runs |
| Duplicates | Rows copied exactly, plus one month (Tiantan, March 2014) uploaded twice with slightly different ozone. | 1,592 + 734 |
| Missing data | NO2 missing in 6% of rows. Some gaps last more than 3 days. | 18,933 |

## How we fixed it

- **Detect from the data, never hard-code.** The code compares each station with the others. If one station-year has CO 1000× lower than everyone else, it's a unit error. If its temperature peaks 8 hours early, it's a time-zone error. This way the same code works for any team's file or next month's export.
- **Exact time fix.** Each row carries a running hour counter (`No`), so we rebuilt the correct time from it. Simply adding 8 hours would have left a few duplicated and missing hours around New Year.
- **Careful swap fix.** In the real data, PM2.5 is sometimes a little higher than PM10 just from measurement noise. We only swap a row back when the swapped value fits the hours before and after it.
- **Result:** exactly 315,648 rows, no duplicates, 12 station names, 16 wind directions. A sanity check against the original files matches 100%.

## Filling in missing values

We tested 5 ways to fill gaps. We hid values we already knew, filled them back in, and measured the error:

- **Short gaps (up to 3 hours):** drawing a line between the hours before and after works best. For NO2 the error is 7.7, against 33.4 for simply using the average.
- **Long gaps:** copying the pattern from similar stations (KNN) works best, with an error of 11.3 against 35.3.
- We **never invent PM2.5 values**, because that's what the model is learning to predict. Rows without PM2.5 are left out of training. That's 2.2% of rows.

## Spikes: errors or real pollution?

A spike detector flagged 14,730 unusual PM2.5 hours. **Most were real**: when the whole city spikes at once (winter smog, Chinese New Year fireworks), it's real pollution, and we keep it. Only 648 spikes at a single station were suspicious.

## The model and the results

We used gradient boosting and tested it fairly. We always trained on the past and tested on the future, never shuffling time. Shuffling cheats, because neighbouring hours look almost identical. Our best version also uses the **average of the last 3 and 24 hours** of each gas and weather reading. This only works because the cleaned data has no duplicates or time shifts.

Final test on the untouched year (Mar 2016 – Feb 2017), on the same 97,979 rows for both models:

| Model | Error (RMSE) | Avg. error (MAE) | R² (1 = perfect) |
|---|---|---|---|
| Naive: messy file used as-is | 36.97 | 22.22 | 0.798 |
| **Ours: cleaned + filled + better features** | **34.51** | **20.68** | **0.824** |

That's **6.7% less error**, and **every one of the 12 stations improved.**

## Bonus: running it in parallel (HPC)

The 12 stations can be cleaned at the same time on different CPU cores. On 12 cores it ran about **3× faster** (2.8 s → 0.9 s). It wasn't 12× faster because each station's job is tiny, so starting the workers takes a big share of the time.

## Advice we gave the agency

- Export times with the time zone written in (ISO-8601).
- Use one fixed spelling for station names, and put units in the column headers.
- Leave missing values empty instead of `-999`.
- Check for duplicates and impossible values before merging files.
- Raise an alarm when a sensor reports the same value for 12 hours.

## Things to know

- **Rule:** the brief asks teams to find the problems *from the data*, without reading the code that creates the messy file. While exploring, we did look at that code. The submitted notebook does not use anything from it: every problem is detected from the data.
- The speed-up numbers in the bonus change slightly every time you run the notebook. That's normal.
