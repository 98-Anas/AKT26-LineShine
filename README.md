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
| **Course files** | [Google Drive](https://drive.google.com/drive/folders/1HY9vywZwunEfJGD7Fqc2uyYcJVlhcVpW?usp=sharing) → Session 1 › Assignment1 |

## Team
| Member | Role |
|---|---|
| Abdallah Ismail | Team leader · Product Owner · submits |
| Omar Seifelnasr | Developer |
| Abdulrahman Omran | Developer |
| Anas Elgalad | Scrum Master · repo admin |
| Mohamed Abd Elaal | Developer |
| Mohamed Salah | Developer |

## Repo map
| Path | What |
|---|---|
| [notebooks/](notebooks/) | The deliverable notebook: `L1_Air_Quality_Data_Preprocessing_Notebook_LineShine.ipynb` |
| [docs/TASK-TRACKER.md](docs/TASK-TRACKER.md) | Backlog: every task, owner, status, points |
| [docs/TEAM-PROGRESS.md](docs/TEAM-PROGRESS.md) | Daily stand-ups, burndown, retros |
| [docs/SPRINT-1.md](docs/SPRINT-1.md) | Sprint goal, scope and Definition of Done for Assignment 1 |
| [docs/AGILE.md](docs/AGILE.md) | How we work: roles, ceremonies, board, git flow |
| [docs/LEARNING-RESOURCES.md](docs/LEARNING-RESOURCES.md) | Topics to learn, with free resources |
| [docs/TECHNICAL-NOTES.md](docs/TECHNICAL-NOTES.md) | Known problems in the notebook and how to fix them |
| [scripts/setup_github.ps1](scripts/setup_github.ps1) | Creates the GitHub repo, labels, issues and Project board in one run |
| `data/` | Generated datasets (git-ignored). **Keep `beijing_clean_team1065.csv.gz` for Week 2** |
| [report/](report/) | Final summary and pitch material |

## Quick start
```bash
git clone https://github.com/<owner>/AKT26-LineShine.git
cd AKT26-LineShine/notebooks
pip install numpy pandas matplotlib scikit-learn joblib jupyter
jupyter notebook   # TEAM_ID = 1065, TEAM_NAME = "LineShine", then Kernel → Restart & Run All
```
