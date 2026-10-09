# Notebooks

| File | What it is |
|---|---|
| [L1_Air_Quality_Data_Preprocessing_Notebook_LineShine.ipynb](L1_Air_Quality_Data_Preprocessing_Notebook_LineShine.ipynb) | **Week 1, our submission.** Fully run, with every answer filled in |
| [original/](original/) | The starting notebook our version was built from. It is a partly filled draft for Team 1 (`TEAM_ID = 1`), not the blank organiser template. Part A comes from it; Part B is rewritten |

Want the story without the code? Read [docs/assignment-1.md](../docs/assignment-1.md).

## Run it

Open it in Jupyter (`uv run jupyter lab`) and choose **Kernel → Restart & Run All**. It takes about 10 minutes.

- The last cell, **Submission check**, must print `✓ ready to submit`.
- The run also saves `beijing_clean_team1065.csv.gz`, our cleaned data. **Keep it for Week 2.** It isn't stored in git, because the notebook can always recreate it.
- The data is read from [`data/raw/`](../data/raw/), so there's nothing to download.

Or run it from the command line:

```bash
cd notebooks
uv run jupyter nbconvert --to notebook --execute --inplace L1_Air_Quality_Data_Preprocessing_Notebook_LineShine.ipynb
```

## Changing it

We don't edit the notebook by hand. Two scripts build it from the organisers' original:

- [`scripts/build_notebook.py`](../scripts/build_notebook.py) holds our code for Tasks 1–6 and the bonus.
- [`scripts/answers.py`](../scripts/answers.py) holds the written answers and the final summary.

After editing either one:

```bash
uv run python scripts/build_notebook.py   # rebuild the notebook
```

Then run the notebook again. If any number changes, update it in `scripts/answers.py`, because every number we write must come from the notebook's output.
