# My Project – Project Tracker

One or two sentences on what this project delivers and for whom.

This is a Notion page with five linked tables: **Tasks**, **Milestones**, **Check-ins**, **Learning** and **Risks**.
All times are **Local time**, 12-hour AM/PM.

## Set up (10 minutes, once)

1. **Import the tables.** On a new Notion page, choose **⋯ → Import → CSV** and import each file in this folder: `Tasks.csv`, `Milestones.csv`, `Check-ins.csv`, `Learning.csv` and `Risks.csv`.
2. **Fix the column types.** Notion imports everything as text. Click each column name → *Edit property* → change its type:

| Table | Column | Change to |
|---|---|---|
| Tasks | Status | Status (Not started · In progress · In review · Blocked · Done) |
| Tasks | Priority | Select (Critical · High · Medium · Low) |
| Tasks | Owner | Person |
| Tasks | Start, Due, Completed on | Date (turn on "Include time" for Due) |
| Tasks | Progress | Number → show as *Bar*, format *Percent* |
| Tasks | Milestone | Relation → Milestones |
| Milestones | Target date | Date |
| Check-ins | Date | Date · Member → Person · Mood → Select |
| Learning | Status | Select (Not started · In progress · Done) · Member → Person · Link → URL |
| Risks | Likelihood, Impact | Number · Status → Select · Owner → Person |

3. **Add the helpful formulas** (optional, *+ Add property → Formula*):
   - Tasks → **Health**: `if(prop("Status") == "Done", "Complete", if(empty(prop("Due")), "No date", if(prop("Due") < now(), "Overdue", if(dateBetween(prop("Due"), now(), "days") <= 3, "Due soon", "ON TRACK"))))`
   - Risks → **Score**: `prop("Likelihood") * prop("Impact")`
   - Milestones → **% done**: add a *Rollup* of Tasks → Status → *Percent per group → Done*.
4. **Create the views:**
   - Tasks → **Board** grouped by Status (drag cards across), **Timeline** by Start → Due (the Gantt), and **My tasks** (table filtered by Owner = *Me*).
   - Check-ins → **Table** sorted by Date, newest first; Learning → **Board** grouped by Status.
5. **Make a dashboard:** on this page, add *linked views* of the tables: Tasks (Board), Tasks (Timeline), Milestones and open Risks.

## Daily routine

- **Everyone:** move your task cards on the board, and add one check-in row a day (what I did, what's next, blocked by).
- **Lead:** once a day, look at Overdue and Blocked tasks and at Check-ins with something in *Blocked by*.

Rows written as *Example…* are samples: edit or delete them.
