# How we work (Scrum-lite)

The hackathon runs in weekly assignments, so **1 sprint = 1 assignment (about 1 week)**.

## Roles
No fixed roles or task owners are pre-assigned. The team decides who takes what on the Notion board.

## Ceremonies (online, short)
| Ceremony | When | Length | Output |
|---|---|---|---|
| Sprint planning | Day after the lecture | 30 min | Tasks listed on the Notion board |
| Daily stand-up | Daily, async in chat or a 10-min call | 10 min | One row per person on the Notion dashboard |
| Integration | 2 days before the deadline | 1–2 h | All tasks merged into one notebook, then Restart & Run All |
| Review | Deadline − 1 day | 30 min | Check outputs and every "Answer & conclusion" cell |
| Retrospective | After submission | 20 min | Keep / Change / Actions |

**Stand-up format:** Yesterday · Today · Blocked by

## Board columns (Notion is the official board; the GitHub Project mirrors code work)
`Backlog → To Do → In Progress → Review → Done`

## Definition of Done (per task)
- [ ] Runs top to bottom with `TEAM_ID = 1065` and no errors
- [ ] No hard-coded stations or years. Detect them from the data
- [ ] Outputs (tables and plots) visible
- [ ] "Answer & conclusion" cites **numbers from the outputs**
- [ ] `issue_log` rows added where relevant
- [ ] Reviewed by one teammate

## Git workflow
- `main` must always run.
- One branch per task (`task-3-imputation`), then a PR with 1 reviewer.
- **Notebooks merge badly.** Each person works in `notebooks/scratch/<task>-<name>.ipynb`, and **one integrator** pastes the final cells into the main notebook. Optional: `pip install nbdime && nbdime config-git --enable`.
- Commit style: `task3: add seasonal-hourly imputer`.
