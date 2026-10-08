"""Rebuilds Part B of the LineShine notebook (keeps Part A from the course notebook).
Usage: python scripts/build_notebook.py   (run from the repo root)"""
import json, re, sys
sys.path.insert(0, "scripts")
import answers as A
from pathlib import Path

NB = Path("notebooks/L1_Air_Quality_Data_Preprocessing_Notebook_LineShine.ipynb")
nb = json.loads(Path("notebooks/original/L1_course_notebook_original.ipynb").read_text(encoding="utf-8"))
cells = nb["cells"]


def md(s):
    return {"cell_type": "markdown", "metadata": {}, "source": s.strip("\n")}


def code(s):
    return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": s.strip("\n")}


def src(i):
    return "".join(cells[i]["source"])


# ---------- Part A: setup + local data path (cells 0..31 kept) ----------
setup = src(3)
setup = re.sub(r"TEAM_ID = \d+ +#.*", 'TEAM_ID = 1065         # LineShine official team ID: it seeds OUR version of the merged dataset\nTEAM_NAME = "LineShine"', setup)
cells[3]["source"] = setup
a1 = src(5).replace('local = sorted(glob.glob("**/PRSA_Data_*.csv", recursive=True))',
                    'local = sorted(glob.glob("../data/raw/PRSA_Data_*.csv")) or sorted(glob.glob("**/PRSA_Data_*.csv", recursive=True))')
a1 = a1.replace('raw = load_beijing()',
                'raw = load_beijing()\nassert raw["station"].nunique() == 12 and len(raw) == 420_768, "not the real UCI data: check ../data/raw"')
cells[5]["source"] = a1
head = cells[:32]
for c in head:
    if c["cell_type"] == "code":
        c["outputs"], c["execution_count"] = [], None
keep_md = {k: cells[i] for k, i in {"t1": 32, "t2": 46, "t3": 48, "t4": 51, "t5": 54, "t6": 57, "hpc": 60, "exp": 64, "foot": 67}.items()}

B = []
# ================= TASK 1 =================
B += [keep_md["t1"], code(r'''
df = pd.read_csv(f"beijing_merged_team{TEAM_ID}.csv.gz")
stn = df["station"].str.strip().str.title()
print(f"merged export: {len(df):,} rows x {df.shape[1]} cols")

# 1a completeness: % missing per column and per station
print("\n1a  % missing per column"); display((df.isna().mean() * 100).round(2).to_frame("% missing").T)
miss_st = (df[POLLUTANTS + WEATHER + ["wd"]].isna().groupby(stn).mean() * 100).round(2)
display(miss_st.style.background_gradient(cmap="Blues", axis=None).format("{:.1f}"))

def gap_lengths(s):
    """lengths (h) of consecutive-NaN runs in a time-ordered series"""
    isn = s.isna().values
    runs, n = [], 0
    for v in isn:
        if v: n += 1
        elif n: runs.append(n); n = 0
    if n: runs.append(n)
    return runs

order = df.assign(station=stn).drop_duplicates(KEY).sort_values(KEY)
gaps = pd.Series([n for _, grp in order.groupby("station") for c in ["PM2.5", "NO2", "CO"] for n in gap_lengths(grp[c])])
bins = pd.cut(gaps, [0, 1, 3, 6, 24, 72, 10_000], labels=["1 h", "2-3 h", "4-6 h", "7-24 h", "1-3 d", "> 3 d"])
gap_tab = pd.DataFrame({"gaps": bins.value_counts().sort_index(),
                        "missing hours": gaps.groupby(bins).sum()})
gap_tab["% of missing hours"] = (100 * gap_tab["missing hours"] / gap_tab["missing hours"].sum()).round(1)
print("\n1a  gap-length distribution (PM2.5, NO2, CO; all stations)"); display(gap_tab)
''')]
B += [code(r'''
# 1b uniqueness
dup_key = df.assign(station=stn).duplicated(KEY, keep=False)
dup_exact = df.duplicated(keep="first")
print(f"1b  rows sharing a station-hour: {dup_key.sum():,} | exact duplicate rows: {dup_exact.sum():,}")
near = df.assign(station=stn)[dup_key & ~df.duplicated(keep=False)]
diff_cols = near.groupby(KEY).agg(lambda s: s.nunique() > 1).sum()
print("    columns that differ inside non-identical duplicate groups:", diff_cols[diff_cols > 0].to_dict())
print("    where:", near.groupby(["station", "year", "month"]).size().to_dict())

# 1c validity
val = {"PM2.5 > PM10": int((df["PM2.5"] > df["PM10"]).sum()),
       "negative concentrations": int((df[POLLUTANTS] < 0).sum().sum()),
       "-999 TEMP": int((df["TEMP"] == -999).sum()), "-999 PRES": int((df["PRES"] == -999).sum()),
       "PRES outside 950-1060 hPa (excl. -999)": int(((df["PRES"] != -999) & ((df["PRES"] < 950) | (df["PRES"] > 1060))).sum()),
       "TEMP outside -30..45 °C (excl. -999)": int(((df["TEMP"] != -999) & ((df["TEMP"] < -30) | (df["TEMP"] > 45))).sum())}
print("\n1c  validity:", val)
print("    ratio PM2.5/PM10 where PM2.5 > PM10: median", round((df["PM2.5"] / df["PM10"])[df["PM2.5"] > df["PM10"]].median(), 2))
''')]
B += [code(r'''
# 1d accuracy: station medians per year on a log scale -> an x1000 unit error stands out
med = df.groupby([stn, "year"])[["SO2", "NO2", "CO", "O3"]].median()
ratio = med / med.groupby("year").transform("median")
fig, ax = plt.subplots(figsize=(10, 3.5))
co = med["CO"].unstack()
for st in co.index: ax.plot(co.columns, co.loc[st], marker="o", label=st)
ax.set_yscale("log"); ax.set_title("1d  median CO per station and year (log) — one station-year ~1000x low"); ax.legend(ncol=4, fontsize=7); plt.show()
print("station-years whose median is < 1/100 or > 100x the cross-station median:")
display(ratio[(ratio < 0.01).any(axis=1) | (ratio > 100).any(axis=1)].round(4))

# 1e timeliness: hour of the mean daily TEMP peak per station and year (expected ~14-16 h Beijing time)
peak = df.groupby([stn, "year", "hour"])["TEMP"].mean().unstack().idxmax(axis=1).unstack()
o3peak = df.groupby([stn, "year", "hour"])["O3"].mean().unstack().idxmax(axis=1).unstack()
print("1e  hour of the mean TEMP peak"); display(peak)
print("    hour of the mean O3 peak"); display(o3peak)

# 1f consistency: raw labels
print("1f  distinct raw station labels:", df["station"].nunique(), "->", sorted(df["station"].unique())[:8], "...")
print("    distinct raw wd labels:", df["wd"].nunique(), "->", sorted(df["wd"].dropna().unique()))
''')]
B += [code(r'''
def swap_mask(d):
    """PM2.5 > PM10 is only a *swap* if the PM10 value fits the neighbouring PM2.5 hours better
    (the real data also has ~1 µg/m³ PM2.5 > PM10 differences from instrument noise, which we must keep).
    d must be sorted by station and time."""
    g = d.groupby("station")["PM2.5"]
    nb = (g.shift(1) + g.shift(-1)) / 2
    return (d["PM2.5"] > d["PM10"]) & ((d["PM10"] - nb).abs() < (d["PM2.5"] - nb).abs())

n_swap = int(swap_mask(order.reset_index(drop=True)).sum())
print(f"1c  PM2.5 > PM10: {val['PM2.5 > PM10']:,} rows, of which {n_swap:,} look like column swaps (neighbour test)")

# Issue log — rows are generated from the audit numbers above (no hand-typed counts)
UNIT_ST = ratio["CO"].idxmin()                                    # (station, year) with the x1000 error
TZ_ST = (peak - peak.median()).abs().stack().idxmax()             # (station, year) with the shifted peak
stuck_cnt = {}
for st, g in df.assign(station=stn).drop_duplicates(KEY).sort_values(KEY).groupby("station"):
    stuck_cnt[st] = int(stuck_flags(g["PM2.5"]).sum())
STUCK_ST = max(stuck_cnt, key=stuck_cnt.get)
issue_log = pd.DataFrame(columns=["dimension", "station", "column", "period", "problem", "rows affected", "fix", "justification"])
L = lambda *r: issue_log.loc.__setitem__(len(issue_log), list(r))
L("consistency", "all", "station", "all", "upper / lower-case + trailing-space variants", int((df["station"] != stn).sum()), "strip + title case", "12 physical stations")
L("consistency", "all", "wd", "all", "lower-case wind directions", int(df["wd"].str.islower().sum()), "upper case", "16-point compass is upper case")
L("accuracy", UNIT_ST[0], "CO", str(UNIT_ST[1]), "CO exported in mg/m³ (x1000 low)", int(((stn == UNIT_ST[0]) & (df["year"] == UNIT_ST[1])).sum()), "multiply by 1000", f"median ratio to other stations {ratio['CO'].min():.4f}")
L("timeliness", TZ_ST[0], "year/month/day/hour", str(TZ_ST[1]), f"TEMP peak at {peak.loc[TZ_ST]} h vs ~{int(peak.median().median())} h: UTC export", int(((stn == TZ_ST[0]) & (df["year"] == TZ_ST[1])).sum()), "+8 h (exact: rebuild from row counter `No`)", "diurnal TEMP/O3 peaks realign")
L("validity", "all", "TEMP", "all", "-999 sentinel", val["-999 TEMP"], "NaN", "not a measurement")
L("validity", "all", "PRES", "all", "-999 sentinel", val["-999 PRES"], "NaN", "not a measurement")
L("validity", "all", "PM2.5/PM10", "all", f"PM2.5 > PM10 in {val['PM2.5 > PM10']:,} rows; swap test positive", n_swap, "swap back only those", "swapped value fits neighbour hours; the rest is instrument noise")
L("validity", STUCK_ST, "PM2.5", "several runs", "stuck sensor: constant >= 12 h", stuck_cnt[STUCK_ST], "whole run -> NaN", "real PM2.5 never flat for a day")
L("uniqueness", "all", "all", "scattered", "exact duplicate rows", int(dup_exact.sum()), "drop", "identical re-export")
L("uniqueness", *near.groupby(["station", "year", "month"]).size().idxmax()[:1], "O3", "1 station-month", "month re-uploaded with O3 +1", int(len(near) // 2), "keep the first copy", "1 µg/m³ difference, below sensor precision")
L("completeness", "all", "NO2", "all", f"NO2 missing {df['NO2'].isna().mean():.1%} (others ~2-6%)", int(df["NO2"].isna().sum()), "imputed per gap length (Task 3)", "logger drop-outs")
issue_log
''')]
B += [md(A.T1)]
# ================= TASK 2 =================
B += [keep_md["t2"], code(r'''
def detect_issues(d):
    """Data-driven detection, so the same code works on next month's export or another team seed."""
    s = d["station"].str.strip().str.title()
    med = d.groupby([s, "year"])["CO"].median()
    rel = med / med.groupby("year").transform("median")
    unit = [k for k, v in rel.items() if v < 0.01]                                    # x1000 too small
    pk = d.groupby([s, "year", "hour"])["TEMP"].mean().unstack().idxmax(axis=1)
    tz = [k for k, v in (pk - pk.groupby(level="year").transform("median")).items() if abs(v) >= 4]
    return {"unit_CO": unit, "tz_shift": tz}

def clean_basic(d, issues=None, stuck_hours=12):
    d = d.copy()
    issues = issues or detect_issues(d)
    # 1 consistency
    d["station"] = d["station"].str.strip().str.title()
    d["wd"] = d["wd"].str.strip().str.upper()
    # 2 accuracy: unit
    for st, yr in issues["unit_CO"]:
        m = (d["station"] == st) & (d["year"] == yr); d.loc[m, "CO"] *= 1000
    # 3 timeliness: undo the UTC shift (exactly via the hourly counter `No` when present, else +8 h)
    dt = pd.to_datetime(d[["year", "month", "day", "hour"]])
    for st, yr in issues["tz_shift"]:
        m = d["station"] == st
        if "No" in d:
            dt[m] = pd.Timestamp("2013-03-01") + pd.to_timedelta(d.loc[m, "No"] - 1, unit="h")
        else:
            m &= d["year"] == yr; dt[m] = dt[m] + pd.Timedelta(hours=8)
    d["datetime"] = dt
    d["year"], d["month"], d["day"], d["hour"] = dt.dt.year, dt.dt.month, dt.dt.day, dt.dt.hour
    # 4 validity: sentinels / impossible values -> NaN, PM2.5/PM10 swap repaired
    d[POLLUTANTS + WEATHER] = d[POLLUTANTS + WEATHER].mask(d[POLLUTANTS + WEATHER] == -999)
    d.loc[~d["PRES"].between(950, 1060), "PRES"] = np.nan
    d.loc[~d["TEMP"].between(-30, 45), "TEMP"] = np.nan
    d[POLLUTANTS] = d[POLLUTANTS].mask(d[POLLUTANTS] < 0)
    # 5 uniqueness: exact duplicates, then one row per station-hour (first copy)
    d = d.drop_duplicates().drop_duplicates(["station", "datetime"], keep="first")
    d = d.sort_values(["station", "datetime"]).reset_index(drop=True)
    sw = swap_mask(d)                                                    # (validity) swap repaired after sorting
    d.loc[sw, ["PM2.5", "PM10"]] = d.loc[sw, ["PM10", "PM2.5"]].values
    # 6 stuck sensor: every PM2.5 run constant for >= stuck_hours -> NaN (whole run, not just its tail)
    g = d.groupby("station")["PM2.5"]
    run_id = (d["PM2.5"] != g.shift()).cumsum()
    run_len = d.groupby(run_id)["PM2.5"].transform("size")
    d.loc[(run_len >= stuck_hours) & d["PM2.5"].notna(), "PM2.5"] = np.nan
    return d.drop(columns=["No"], errors="ignore")

issues = detect_issues(df)
print("detected:", issues)
t0 = time.perf_counter(); df_clean = clean_basic(df, issues); print(f"clean_basic: {time.perf_counter() - t0:.1f} s")
print(f"rows {len(df):,} -> {len(df_clean):,} | stations {df_clean['station'].nunique()} | wd labels {df_clean['wd'].nunique()}")
print("expected rows (12 stations x 26,304 h):", 12 * 26_304, "| duplicate station-hours left:", df_clean.duplicated(["station", "datetime"]).sum())
''')]
B += [code(r'''
# verification: the fixes must make the symptoms disappear
pk2 = df_clean.groupby(["station", "year", "hour"])["TEMP"].mean().unstack().idxmax(axis=1).unstack()
co2 = df_clean.groupby(["station", "year"])["CO"].median().unstack()
print("TEMP-peak hour after fix (min..max over station-years):", pk2.values.min(), "..", pk2.values.max())
print("CO median range after fix:", co2.values.min(), "..", co2.values.max())
print("PM2.5 > PM10 left (instrument noise, kept):", int((df_clean["PM2.5"] > df_clean["PM10"]).sum()), "| -999 left:", int((df_clean[POLLUTANTS + WEATHER] == -999).sum().sum()))
ref_check = train_raw.assign(station=train_raw["station"]).set_index(["station", "datetime"])["TEMP"]
same = df_clean.set_index(["station", "datetime"])["TEMP"].reindex(ref_check.index)
print(f"TEMP agreement with the original files after cleaning: {(np.isclose(same, ref_check) | (same.isna() | ref_check.isna())).mean():.4%}  (sanity check only)")
''')]
B += [md(A.T2)]
# ================= TASK 3 =================
B += [keep_md["t3"], code(r'''
from sklearn.impute import KNNImputer
rng3 = np.random.default_rng(SEED)

def impute_candidates(piv, col, s):
    others = piv.drop(columns=col)
    nb = others.mean(axis=1)
    offset = (s - nb).mean()
    prof = s.groupby([s.index.month, s.index.hour]).transform("median")
    return {
        "station median": s.fillna(s.median()),
        "time interpolation": s.interpolate(method="time", limit_direction="both"),
        "seasonal-hourly profile": s.fillna(prof),
        "neighbour stations": s.fillna(nb + offset),
        "KNN across stations": pd.Series(KNNImputer(n_neighbors=5).fit_transform(piv.assign(**{col: s}))[:, list(piv.columns).index(col)], index=s.index),
    }

def masks(truth):
    known = np.flatnonzero(truth.notna().values)
    m1 = np.zeros(len(truth), bool); m1[rng3.choice(known, len(known) // 10, replace=False)] = True
    m24 = np.zeros(len(truth), bool)
    for s0 in rng3.choice(known[:-30], 150, replace=False): m24[s0:s0 + 24] = True
    return {"single hours": m1, "24-h blocks": m24 & truth.notna().values}

study = {}
for pol in ["NO2", "CO"]:
    piv = df_clean.pivot_table(index="datetime", columns="station", values=pol)
    for st in ["Dongsi", "Huairou"]:                                  # one urban, one suburban station
        truth = piv[st]
        for kind, m in masks(truth).items():
            cand = impute_candidates(piv, st, truth.mask(m))
            study[(pol, st, kind)] = {k: np.sqrt(np.mean((v.fillna(truth.mask(m).mean()).values[m] - truth.values[m]) ** 2)) for k, v in cand.items()}
study = pd.DataFrame(study).T.round(1)
print("RMSE of hidden known values (µg/m³) — lower is better"); display(study.style.highlight_min(axis=1, color="#c7e9c0"))
best = study.idxmin(axis=1).groupby(level=2).agg(lambda s: s.value_counts().idxmax())
print("winner per gap type:", best.to_dict())
''')]
B += [code(r'''
# Chosen policy, applied to every gas + weather feature (target PM2.5 is NOT imputed: we never train on invented labels)
IMPUTE_COLS = ["SO2", "NO2", "CO", "O3", "TEMP", "PRES", "DEWP", "RAIN", "WSPM"]
SHORT_GAP = 3

def gap_len(s):
    isn = s.isna()
    grp = (~isn).cumsum()
    return isn.groupby(grp).transform("sum").where(isn, 0)

def impute_station(g, cols=IMPUTE_COLS):
    """per-station step: gaps <= 3 h -> time interpolation (Task-3 winner for single hours)"""
    g = g.set_index("datetime").asfreq("h").copy()
    g["station"] = g["station"].ffill().bfill()
    for c in cols:
        L = gap_len(g[c]); interp = g[c].interpolate(method="time", limit_area="inside")
        g[f"{c}_imp"] = g[c].isna().astype(np.int8)
        g.loc[(L > 0) & (L <= SHORT_GAP), c] = interp[(L > 0) & (L <= SHORT_GAP)]
    g["wd"] = g["wd"].ffill(limit=SHORT_GAP)
    return g.reset_index()

def impute_all(d, cols=IMPUTE_COLS):
    d = pd.concat([impute_station(g, cols) for _, g in d.groupby("station")], ignore_index=True)
    for c in cols:                                                        # long gaps: KNN across stations (Task-3 winner), then profile
        piv = d.pivot(index="datetime", columns="station", values=c)
        fill = pd.DataFrame(KNNImputer(n_neighbors=5).fit_transform(piv), index=piv.index, columns=piv.columns)
        fill = fill.where(piv.notna().any(axis=1), np.nan)                 # hours with no station at all -> profile
        prof = fill.groupby([fill.index.month, fill.index.hour]).transform("median")
        fill = fill.fillna(prof).stack().rename(c)
        d = d.drop(columns=c).merge(fill.reset_index(), on=["datetime", "station"], how="left")
    d["year"], d["month"], d["day"], d["hour"] = d["datetime"].dt.year, d["datetime"].dt.month, d["datetime"].dt.day, d["datetime"].dt.hour
    return d.sort_values(["station", "datetime"]).reset_index(drop=True)

t0 = time.perf_counter(); df_imp = impute_all(df_clean); print(f"impute_all: {time.perf_counter() - t0:.1f} s")
print("missing after imputation (%):", (df_imp[IMPUTE_COLS + ["PM2.5", "wd"]].isna().mean() * 100).round(2).to_dict())
print("share of imputed values per column (%):", (df_imp[[f"{c}_imp" for c in IMPUTE_COLS]].mean() * 100).round(2).to_dict())
''')]
B += [md(A.T3)]
# ================= TASK 4 =================
B += [keep_md["t4"], code(r'''
# Flag PM2.5 spikes with a Hampel filter per station, then classify:
#   real episode = the same hour is also high at the other stations (regional event: smog, fireworks)
#   error        = isolated spike at one station, or impossible / stuck values (already NaN'd in clean_basic)
pm = df_imp.pivot(index="datetime", columns="station", values="PM2.5")
flags = pm.apply(lambda s: hampel_flags(s.interpolate(limit=3), window=25, k=3.0))
regional = pm.median(axis=1)
real = flags & (pm.le(regional.mul(3), axis=0))           # within 3x of the regional median -> shared episode
isolated = flags & ~real
print(f"Hampel-flagged hours: {int(flags.sum().sum()):,} | real regional episodes: {int(real.sum().sum()):,} | isolated (treated as errors): {int(isolated.sum().sum()):,}")
display(pd.DataFrame({"flagged": flags.sum(), "real episode": real.sum(), "isolated": isolated.sum()}))

fig, ax = plt.subplots(1, 2, figsize=(14, 3.8))
w = slice("2015-02-17", "2015-02-21")                       # Spring Festival 2015 (fireworks on 18-19 Feb)
pm.loc[w].plot(ax=ax[0], lw=.8, legend=False); ax[0].set_title("Real episode: Spring Festival fireworks 2015 — all stations rise together")
st_raw = df.assign(station=stn)[stn == STUCK_ST]
st_raw = st_raw.assign(dt=pd.to_datetime(st_raw[["year", "month", "day", "hour"]])).drop_duplicates("dt").set_index("dt").sort_index()["PM2.5"]
runs = (st_raw != st_raw.shift()).cumsum(); rl = st_raw.groupby(runs).transform("size")
t_stuck = rl[rl >= 24].index[0]
win = slice(t_stuck - pd.Timedelta("3D"), t_stuck + pd.Timedelta("5D"))
ax[1].plot(st_raw.loc[win], lw=.8, label="raw export"); ax[1].plot(pm.loc[win, STUCK_ST], lw=.8, label="after clean_basic")
ax[1].set_title(f"Error: stuck PM2.5 sensor at {STUCK_ST} (flat line removed)"); ax[1].legend()
plt.tight_layout(); plt.show()
''')]
B += [code(r'''
from sklearn.preprocessing import PowerTransformer
cols = ["PM2.5", "SO2", "NO2", "CO", "O3", "WSPM"]
v = df_imp[cols].dropna()
sk = pd.DataFrame({"raw": v.skew(), "log1p": np.log1p(v).skew(),
                   "Yeo-Johnson": pd.DataFrame(PowerTransformer().fit_transform(v), columns=cols).skew()}).round(2)
display(sk)
fig, ax = plt.subplots(1, 2, figsize=(11, 3)); ax[0].hist(v["PM2.5"], bins=80); ax[0].set_title(f"PM2.5 raw (skew {sk.loc['PM2.5','raw']})")
ax[1].hist(np.log1p(v["PM2.5"]), bins=80, color="#d49a2a"); ax[1].set_title(f"log1p PM2.5 (skew {sk.loc['PM2.5','log1p']})"); plt.tight_layout(); plt.show()
''')]
B += [md(A.T4)]
# ================= TASK 5 =================
B += [keep_md["t5"], code(r'''
from sklearn.compose import TransformedTargetRegressor
ROLL_COLS = ["CO", "NO2", "SO2", "O3", "DEWP", "WSPM", "TD_dep"]

def add_features_plus(d):
    """add_features + trailing 3 h / 24 h rolling means per station (causal: past hours only).
    Only meaningful on a clean, de-duplicated, gap-free hourly series -> a direct pay-off of cleaning."""
    d = add_features(d)
    order = d.sort_values(["station", "datetime"]).index
    o = d.loc[order]
    for c in ROLL_COLS:
        for w in (3, 24):
            d.loc[order, f"{c}_r{w}"] = o.groupby("station")[c].transform(lambda s: s.rolling(w, min_periods=1).mean()).values
    return d

FEATS_PLUS = NUM_FEATS + [f"{c}_r{w}" for c in ROLL_COLS for w in (3, 24)]

def make_pipeline_v(model, feats=NUM_FEATS, indicator=True):
    num = Pipeline([("impute", SimpleImputer(strategy="median", add_indicator=indicator)), ("scale", StandardScaler())])
    cat = Pipeline([("impute", SimpleImputer(strategy="most_frequent")), ("onehot", OneHotEncoder(handle_unknown="ignore"))])
    prep = ColumnTransformer([("num", num, feats), ("cat", cat, CAT_FEATS)], sparse_threshold=0)
    return Pipeline([("prep", prep), ("model", model)])

data5 = add_features_plus(df_imp.drop(columns=["datetime"])).dropna(subset=[TARGET]).sort_values("datetime").reset_index(drop=True)
y5 = data5[TARGET]
noimp = add_features(df_clean.drop(columns=["datetime"])).dropna(subset=[TARGET]).sort_values("datetime").reset_index(drop=True)
print(f"modelling rows: {len(data5):,} (PM2.5 is never imputed -> rows without a label are dropped)")

hgb5 = lambda: HistGradientBoostingRegressor(max_iter=300, learning_rate=0.08, random_state=0)
variants = {   # name: (estimator, X, y, feature list)
    "A  Task-3 imputation + median/indicator pipeline": (make_pipeline_v(hgb5()), data5[NUM_FEATS + CAT_FEATS], y5, NUM_FEATS),
    "B  no Task-3 imputation (pipeline median only)":   (make_pipeline_v(hgb5()), noimp[NUM_FEATS + CAT_FEATS], noimp[TARGET], NUM_FEATS),
    "C  A + log1p target":                              (TransformedTargetRegressor(make_pipeline_v(hgb5()), func=np.log1p, inverse_func=np.expm1), data5[NUM_FEATS + CAT_FEATS], y5, NUM_FEATS),
    "D  A + 3 h/24 h rolling features":                 (make_pipeline_v(hgb5(), FEATS_PLUS), data5[FEATS_PLUS + CAT_FEATS], y5, FEATS_PLUS),
}
cv5 = {}
for name, (est, X, y, _) in variants.items():
    t0 = time.perf_counter()
    s = -cross_val_score(est, X, y, cv=TimeSeriesSplit(5), scoring="neg_root_mean_squared_error", n_jobs=-1)
    cv5[name] = {"CV RMSE": round(s.mean(), 2), "± sd": round(s.std(), 2), "folds": np.round(s, 1).tolist(), "time (s)": round(time.perf_counter() - t0, 1)}
cv5 = pd.DataFrame(cv5).T; display(cv5)
BEST = cv5["CV RMSE"].astype(float).idxmin(); print("best variant:", BEST)
''')]
B += [md(A.T5)]
# ================= TASK 6 =================
B += [keep_md["t6"], code(r'''
from sklearn.base import clone
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
def scores(y, p): return {"RMSE": np.sqrt(mean_squared_error(y, p)), "MAE": mean_absolute_error(y, p), "R2": r2_score(y, p)}

test_f = add_features(test_year.drop(columns=["datetime"])).dropna(subset=NUM_FEATS + CAT_FEATS + [TARGET])
print(f"test year complete-case rows (same for both models): {len(test_f):,}")

# 1) naive: merged export as-is
naive = add_features(df).dropna(subset=NUM_FEATS + CAT_FEATS + [TARGET])
naive_model = make_pipeline(HistGradientBoostingRegressor(max_iter=300, random_state=0)).fit(naive[NUM_FEATS + CAT_FEATS], naive[TARGET])
p_naive = naive_model.predict(test_f[NUM_FEATS + CAT_FEATS])

# 2) ours: clean_basic + imputation + the same model family (+ best CV variant)
X5 = data5[NUM_FEATS + CAT_FEATS]
ours_same = make_pipeline(HistGradientBoostingRegressor(max_iter=300, random_state=0)).fit(X5, y5)
p_same = ours_same.predict(test_f[NUM_FEATS + CAT_FEATS])
est_b, X_b, y_b, feats_b = variants[BEST]
ours_best = clone(est_b).fit(X_b, y_b)
test_plus = add_features_plus(test_year.drop(columns=["datetime"])).loc[test_f.index]    # rolling built on the raw test series
p_best = ours_best.predict(test_plus[feats_b + CAT_FEATS])

y_t = test_f[TARGET].values
impact = pd.DataFrame({"naive (merged export)": scores(y_t, p_naive),
                       "cleaned, same model": scores(y_t, p_same),
                       f"cleaned + best CV variant ({BEST[:1]})": scores(y_t, p_best)}).T.round(3)
impact["train rows"] = [len(naive), len(X5), len(X_b)]
display(impact)
gain = 100 * (1 - impact.iloc[2]["RMSE"] / impact.iloc[0]["RMSE"])
gain_same = 100 * (1 - impact.iloc[1]["RMSE"] / impact.iloc[0]["RMSE"])
print(f"lower RMSE than naive -> same model on cleaned data: {gain_same:.1f} % | full pipeline: {gain:.1f} %")
''')]
B += [code(r'''
by_st = pd.DataFrame({"naive": pd.Series((p_naive - y_t) ** 2).groupby(test_f["station"].values).mean() ** .5,
                      "ours": pd.Series((p_best - y_t) ** 2).groupby(test_f["station"].values).mean() ** .5}).round(1)
by_st["Δ RMSE"] = by_st["ours"] - by_st["naive"]
fig, ax = plt.subplots(1, 3, figsize=(16, 4.2))
lim = np.percentile(y_t, 99.5)
for a, p, t in [(ax[0], p_naive, "naive"), (ax[1], p_best, "ours")]:
    a.hexbin(y_t, p, gridsize=60, bins="log", extent=(0, lim, 0, lim), cmap="Blues"); a.plot([0, lim], [0, lim], "r--", lw=1)
    a.set_xlabel("actual PM2.5"); a.set_ylabel("predicted"); a.set_title(f"{t}: RMSE {np.sqrt(mean_squared_error(y_t, p)):.1f}")
by_st[["naive", "ours"]].plot.bar(ax=ax[2]); ax[2].set_title("test-year RMSE by station"); ax[2].set_ylabel("µg/m³")
plt.tight_layout(); plt.show()
display(by_st.sort_values("Δ RMSE"))
''')]
B += [md(A.T6)]
# ================= HPC =================
B += [keep_md["hpc"], code(r'''
from joblib import Parallel, delayed
import os

def clean_one_station(g, issues):
    """clean_basic + per-station imputation (interpolation + month-hour profile; no cross-station step)"""
    c = impute_station(clean_basic(g, issues))
    for col in IMPUTE_COLS:
        c[col] = c[col].fillna(c.groupby([c["datetime"].dt.month, c["datetime"].dt.hour])[col].transform("median"))
    return c

groups = [g for _, g in df.groupby(stn)]
step = {}
g0 = groups[0]
t0 = time.perf_counter(); c0 = clean_basic(g0, issues); step["clean_basic"] = time.perf_counter() - t0
t0 = time.perf_counter(); impute_station(c0); step["impute_station"] = time.perf_counter() - t0
print("per-station step times (s):", {k: round(v, 3) for k, v in step.items()})

hpc = {}
workers = [p for p in [1, 2, 4, 6, 12] if p <= os.cpu_count()]
for p in workers:
    ts = []
    for _ in range(3):                                           # best of 3 to reduce noise
        t0 = time.perf_counter(); out = Parallel(n_jobs=p, backend="loky")(delayed(clean_one_station)(g, issues) for g in groups); ts.append(time.perf_counter() - t0)
    hpc[p] = min(ts)
hpc = pd.DataFrame({"T_p (s)": hpc}); hpc["S_p"] = hpc["T_p (s)"].iloc[0] / hpc["T_p (s)"]; hpc["E_p"] = hpc["S_p"] / hpc.index
display(hpc.round(3)); print("CPU cores:", os.cpu_count(), "| stations (tasks):", len(groups))
fig, ax = plt.subplots(figsize=(6, 3.5)); ax.plot(hpc.index, hpc["S_p"], "o-", label="measured"); ax.plot(hpc.index, hpc.index, "k--", lw=.8, label="ideal")
ax.set_xlabel("workers p"); ax.set_ylabel("speed-up S_p"); ax.legend(); plt.show()
''')]
B += [md(A.HPC)]
# ================= EXPORT / SUMMARY / CHECK =================
B += [keep_md["exp"], code(r'''
OUT = f"beijing_clean_team{TEAM_ID}.csv.gz"
df_imp.drop(columns=["datetime"]).to_csv(OUT, index=False)
print(f"exported {len(df_imp):,} rows x {df_imp.shape[1] - 1} cols -> {OUT}")
''')]
B += [md(A.SUMMARY)]
B += [md("## Submission check"), code(r'''
import os, glob
nb_files = glob.glob(f"L1_Air_Quality_Data_Preprocessing_Notebook_{TEAM_NAME}.ipynb")
checks = {
    "TEAM_ID is the official ID": TEAM_ID == 1065,
    "TEAM_NAME uses letters, digits, hyphens": bool(__import__("re").fullmatch(r"[A-Za-z0-9-]+", TEAM_NAME)),
    "notebook file named with TEAM_NAME": len(nb_files) == 1,
    "real UCI data (420,768 rows)": len(raw) == 420_768,
    "issue log filled": len(issue_log) >= 8,
    "test year used only in Task 6 (cleaned data ends before split)": df_clean["datetime"].max() < SPLIT,
    "cleaned export exists": os.path.exists(f"beijing_clean_team{TEAM_ID}.csv.gz"),
    "impact study computed": "impact" in globals() and len(impact) >= 2,
}
for k, v in checks.items(): print(("OK   " if v else "FAIL ") + k)
print("\nready to submit" if all(checks.values()) else "\nNOT ready: fix the FAIL lines")
'''), keep_md["foot"]]

nb["cells"] = head + B
for c in nb["cells"]:
    c.pop("id", None)
nb["nbformat_minor"] = 4
NB.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding="utf-8")
print("cells:", len(nb["cells"]))
