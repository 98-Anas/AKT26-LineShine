# Team LineShine: AKT26 Hackathon

This is our team's workspace for the **Al-Khawarizmi Tour Online Hackathon (HPC & AI)**. The hackathon runs Oct 3 – Nov 7, 2026 ([website](https://alkhawarizmi-tour.org/)).
It holds our code, data, finished assignments, and the templates we use to organise our work on Notion.

- **Team ID:** 1065
- **Team name:** LineShine
- **Members:** Abdallah Ismail (team leader), Omar Seifelnasr, Abdulrahman Omran, Anas Elgalad, Mohamed Abd Elaal, Mohamed Salah

> All times in this repo are **Cairo time, 12-hour AM/PM**.

---

## Where things are

```
AKT26-LineShine/
├── notebooks/        ← our assignment notebooks (this is what we submit)
│   └── original/     ← the untouched notebook the organisers gave us
├── data/raw/         ← the real Beijing air-quality data (12 station files)
├── sessions/         ← course material from the organisers (slides, notes, briefs)
├── docs/             ← explanations: how we solved each assignment + what to learn
├── tracker/          ← Excel project tracker (tasks, daily check-ins, learning)
├── notion/           ← templates to import into our Notion page
├── scripts/          ← helper scripts that rebuild the notebook
├── pyproject.toml    ← list of Python packages (managed by uv)
└── uv.lock           ← exact package versions so everyone has the same setup
```

| I want to… | Go to |
|---|---|
| See what we submitted for Week 1 | [notebooks/L1_Air_Quality_Data_Preprocessing_Notebook_LineShine.ipynb](notebooks/L1_Air_Quality_Data_Preprocessing_Notebook_LineShine.ipynb) |
| Understand how we solved Week 1, in plain words | [docs/assignment-1.md](docs/assignment-1.md) |
| Learn the topics behind the assignments | [docs/learning-resources.md](docs/learning-resources.md) |
| Track tasks, daily progress and learning in Excel | [tracker/LineShine_PM_Tracker.xlsx](tracker/LineShine_PM_Tracker.xlsx) |
| Set up the task tracker / check-ins on Notion | [notion/README.md](notion/README.md) |
| Read the official brief, slides and notes | [sessions/](sessions/) |

**Useful links**

- Notion dashboard (our tasks and progress): <https://functional-soapwort-2ac.notion.site/HPC-Competition-3e8ecac9147480f5b17bf11edbfe09c5>
- Course files (Google Drive): <https://drive.google.com/drive/folders/1HY9vywZwunEfJGD7Fqc2uyYcJVlhcVpW?usp=sharing>
- Submission form (team leader only): <https://forms.gle/nW2kwDsy62fJ5KHt5>

---

## Assignments

| Week | Assignment | Due (Cairo time) | Status |
|---|---|---|---|
| 1 | Air-Quality Data Challenge: clean messy data, build a virtual PM2.5 sensor | **Sat, Oct 10 2026, 2:59 PM** | Notebook finished, ready to submit |
| 2 | AI Methods Shoot-out (uses our cleaned Week-1 data) | announced later | — |

---

## Getting started

You only need to do this once.

**1. Install uv.** It's a fast tool that installs Python and all the packages for you.

```powershell
pip install uv
```

**2. Download the repo and install everything.**

```bash
git clone https://github.com/98-Anas/AKT26-LineShine.git
cd AKT26-LineShine
uv sync
```

`uv sync` creates a private Python environment in the `.venv` folder, with exactly the same package versions as everyone else on the team.

**3. Open the notebook.**

```bash
uv run jupyter lab
```

Then open the notebook in `notebooks/`.
In VS Code, open the notebook and choose `.venv\Scripts\python.exe` as the kernel instead.

**Need another package?** Run `uv add <package-name>`, then commit both `pyproject.toml` and `uv.lock` so the rest of the team gets it too.

---

## Running the Week-1 notebook

- In Jupyter, use **Kernel → Restart & Run All**. A full run takes about 10 minutes.
- At the end, the **Submission check** cell must print `✓ ready to submit`.
- The run also creates `notebooks/beijing_clean_team1065.csv.gz`, our cleaned dataset. **Keep it: Week 2 needs it.** It isn't stored in git because the notebook can always recreate it.

To run the notebook from the command line instead:

```bash
cd notebooks
uv run jupyter nbconvert --to notebook --execute --inplace L1_Air_Quality_Data_Preprocessing_Notebook_LineShine.ipynb
```

### How the notebook is put together

We don't edit the big notebook by hand. Two scripts generate it from the organisers' original:

- `scripts/build_notebook.py` takes the original notebook from `notebooks/original/`. It keeps Part A (the lecture demos), sets our Team ID, and writes our solution for Part B.
- `scripts/answers.py` holds the written answers and the final summary that appear in the notebook.

After changing either file, rebuild and rerun:

```bash
uv run python scripts/build_notebook.py
```

Then run the notebook again. **If any result changes, update the numbers in `scripts/answers.py`.** The rules say every number we write must come from the notebook output.

---

## Submitting an assignment

1. Run the notebook from top to bottom and check that it prints `✓ ready to submit`.
2. The **team leader** uploads the `.ipynb` file through the [submission form](https://forms.gle/nW2kwDsy62fJ5KHt5) using Team ID **1065**.
3. Mark the task as Done on Notion.

---

## Working together

- **Tasks and daily progress** live on Notion. To set it up, import the two templates in [notion/](notion/).
- **Code** lives here. Pull before you start (`git pull`) and push when you're done.
- Notebooks are hard to merge when two people edit the same one. Try your ideas in a separate notebook, then move the final code into `scripts/build_notebook.py`.

## The Excel tracker

[tracker/LineShine_PM_Tracker.xlsx](tracker/LineShine_PM_Tracker.xlsx) is a ready-to-use project tracker. You can use it instead of Notion, or next to it.

| Sheet | What it's for |
|---|---|
| **Dashboard** | The big picture, all calculated: % done, points secured, overdue and blocked tasks, the next deadline, progress per assignment, and an overview of each member |
| **Tasks** | One row per task. Pick the assignee, status and priority from drop-downs; days left and overdue fill in by themselves |
| **Daily Check-ins** | Each person writes one short row a day: what I did, what's next, what's blocking me |
| **Learning** | Every topic from [docs/learning-resources.md](docs/learning-resources.md), with links. Each member marks Not started / In progress / Done in their own column |
| **Team** | Member list and contacts. It feeds the drop-downs |
| **Lists** | Drop-down values. Add "Week 2" and so on here |

Type only in **blue** cells; grey cells are formulas. To edit the tracker together, upload it to OneDrive or Google Drive and share it.
To regenerate a blank copy: `uv run --with openpyxl python scripts/build_tracker.py`.

## About the data

`data/raw/` contains the **Beijing Multi-Site Air-Quality** dataset (UCI #501): hourly pollution and weather readings from 12 stations, March 2013 – February 2017.
The files are stored in the repo on purpose. When Python can't download them, the original notebook silently switches to fake data, and committing them prevents that.
