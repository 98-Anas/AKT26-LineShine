# AKT26 Hackathon: Team LineShine

**Al-Khawarizmi Tour, Online Hackathon HPC & AI** (Oct 3 – Nov 7, 2026) · https://alkhawarizmi-tour.org/

| | |
|---|---|
| **Team ID** | `1065` |
| **Team name** | `LineShine` |
| **Track** | AI: Data Quality & Preprocessing (Lecture 1) |
| **Current sprint** | [Sprint 1: Air-Quality Data Challenge](docs/SPRINT-1.md) |
| **Sprint 1 deadline** | **Oct 9 2026, 23:59 AoE** |
| **Submit via** | https://forms.gle/nW2kwDsy62fJ5KHt5 (team leader only, Team ID `1065`) |
| **Task tracker & team progress** | [Notion dashboard](https://functional-soapwort-2ac.notion.site/HPC-Competition-3e8ecac9147480f5b17bf11edbfe09c5), managed by the team leader |
| **Course files** | [Google Drive](https://drive.google.com/drive/folders/1HY9vywZwunEfJGD7Fqc2uyYcJVlhcVpW?usp=sharing) → Session 1 › Assignment1 |

## Team
| Member | Role |
|---|---|
| Abdallah Ismail | Team leader · Product Owner · manages Notion tracker · submits |
| Omar Seifelnasr | Developer |
| Abdulrahman Omran | Developer |
| Anas Elgalad | Scrum Master · repo admin |
| Mohamed Abd Elaal | Developer |
| Mohamed Salah | Developer |

## Repo map
| Path | What |
|---|---|
| [notebooks/](notebooks/) | The deliverable notebook: `L1_Air_Quality_Data_Preprocessing_Notebook_LineShine.ipynb` |
| [docs/TASK-TRACKER.md](docs/TASK-TRACKER.md) | Sprint snapshot. **The live tracker is on Notion** |
| [docs/TEAM-PROGRESS.md](docs/TEAM-PROGRESS.md) | Repo milestones. **Stand-ups and progress are on Notion** |
| [docs/SPRINT-1.md](docs/SPRINT-1.md) | Sprint goal, scope and Definition of Done for Assignment 1 |
| [docs/AGILE.md](docs/AGILE.md) | How we work: roles, ceremonies, board, git flow |
| [docs/LEARNING-RESOURCES.md](docs/LEARNING-RESOURCES.md) | Topics to learn, with free resources |
| [docs/TECHNICAL-NOTES.md](docs/TECHNICAL-NOTES.md) | Known problems in the notebook and how to fix them |
| [scripts/setup_github.ps1](scripts/setup_github.ps1) | Creates the GitHub repo, labels, issues and Project board in one run |
| `data/raw/` | The 12 real UCI station CSVs (committed) |
| `notebooks/*.csv.gz` | Generated merged/clean datasets (git-ignored, recreated by the notebook). **Keep `beijing_clean_team1065.csv.gz` for Week 2** |
| [notebooks/original/](notebooks/original/) | The untouched course notebook, used as input by `scripts/build_notebook.py` |
| [report/](report/) | Final summary and pitch material |

## Quick start (uv)
Install [uv](https://docs.astral.sh/uv/getting-started/installation/) once (`pip install uv`, or `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`), then:
```bash
git clone https://github.com/98-Anas/AKT26-LineShine.git
cd AKT26-LineShine
uv sync                          # creates .venv with the exact locked versions (uv.lock)
uv run jupyter lab               # open notebooks/L1_..._LineShine.ipynb, then Kernel → Restart & Run All
```
- Add a package: `uv add <pkg>` (updates `pyproject.toml` + `uv.lock`, commit both).
- VS Code: select the interpreter `.venv\Scripts\python.exe` as the notebook kernel.
- Rebuild Part B from the course notebook: `uv run python scripts/build_notebook.py`.
- Execute headless: `cd notebooks && uv run jupyter nbconvert --to notebook --execute --inplace L1_Air_Quality_Data_Preprocessing_Notebook_LineShine.ipynb`.
- The real UCI station files are committed in `data/raw/`. The notebook reads them, so there's no download and no silent synthetic fallback.
