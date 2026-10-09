"""Builds the Project Tracker workbook.

    uv run --with openpyxl python scripts/build_tracker.py

Writes to tracker/:
  * excel/Project_Tracker_Template.xlsx  – Excel template anyone can use (example rows included)
  * excel/LineShine_Tracker.xlsx         – the same, filled in for Team LineShine
  * notion/template, notion/lineshine    – the same tracker as CSV tables + setup guide for Notion
"""
import pathlib
import re
from datetime import date, datetime, timedelta

from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, PieChart, Reference
from openpyxl.chart.label import DataLabelList
from openpyxl.comments import Comment
from openpyxl.formatting.rule import CellIsRule, ColorScaleRule, DataBarRule, FormulaRule
from openpyxl.styles import Alignment, Border, Font, PatternFill, Protection, Side
from openpyxl.utils import get_column_letter as L
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.worksheet.datavalidation import DataValidation

REPO = pathlib.Path(__file__).resolve().parents[1]

# ----------------------------------------------------------------- style
NAVY, GOLD, BLUE, GREEN, RED, AMBER, GREY = "0A2A5C", "D49A2A", "2E90FA", "12B76A", "D92D20", "F79009", "F2F4F7"
FONT = "Arial"


def font(size=10, bold=False, color="1D2939", italic=False, underline=None):
    return Font(name=FONT, size=size, bold=bold, color=color, italic=italic, underline=underline)


def fill(c):
    return PatternFill("solid", fgColor=c)


thin = Side(style="thin", color="D0D5DD")
BOX = Border(left=thin, right=thin, top=thin, bottom=thin)
CENTER = Alignment(horizontal="center", vertical="center", wrap_text=True)
LEFT = Alignment(horizontal="left", vertical="center", wrap_text=True)
TOP = Alignment(horizontal="left", vertical="top", wrap_text=True)
INPUT = font(color="0000FF")
CALC_FILL = fill(GREY)
DT = "ddd, mmm d yyyy, h:mm AM/PM"
D = "ddd, mmm d yyyy"
DS = "mmm d"

STATUSES = ["Not started", "In progress", "In review", "Blocked", "Done"]
STATUS_COLORS = {"Not started": "EAECF0", "In progress": "D1E9FF", "In review": "EBE9FE", "Blocked": "FEE4E2", "Done": "D1FADF"}
PRIORITIES = ["Critical", "High", "Medium", "Low"]
PROGRESS = [0, 0.25, 0.5, 0.75, 1]
LEARN = ["Not started", "In progress", "Done"]
RISK_STATUS = ["Open", "Monitoring", "Closed"]
MOODS = ["Great", "Good", "OK", "Struggling"]
N_TASKS, N_MEMBERS, N_MS, N_CHECK, N_RISK, N_LEARN, N_DAYS, N_WEEKS = 300, 10, 30, 500, 100, 150, 84, 16
TL_ROWS = 80


def header(ws, row, labels, widths=None, start_col=1):
    for i, h in enumerate(labels):
        c = ws.cell(row, start_col + i, h)
        c.font, c.fill, c.alignment, c.border = font(10, True, "FFFFFF"), fill(NAVY), CENTER, BOX
    ws.row_dimensions[row].height = 32
    if widths:
        for i, w in enumerate(widths):
            ws.column_dimensions[L(start_col + i)].width = w


def page_title(ws, title, subtitle):
    ws.sheet_view.showGridLines = False
    ws["A1"] = title
    ws["A1"].font = font(18, True, NAVY)
    ws["A2"] = subtitle
    ws["A2"].font = font(10, italic=True, color="667085")
    ws.row_dimensions[1].height = 30
    ws["A3"] = "← Back to Start Here"
    ws["A3"].hyperlink = "#'Start Here'!A1"
    ws["A3"].font = font(9, color="1155CC", underline="single")


def explain(ws, row, notes):
    """Hover help on header cells: {column letter: text}."""
    for col, text in notes.items():
        c = Comment(text, "How to use")
        c.width, c.height = 260, 90
        ws[f"{col}{row}"].comment = c


def dropdown(ws, name, rng, prompt=None):
    dv = DataValidation(type="list", formula1=f"={name}", allow_blank=True, showErrorMessage=True,
                        errorTitle="Not in the list", error="Pick a value from the drop-down (lists are on the Settings sheet).")
    if prompt:
        dv.promptTitle, dv.prompt, dv.showInputMessage = "Tip", prompt, True
    ws.add_data_validation(dv)
    dv.add(rng)


def style_rows(ws, first, last, ncols, calc_cols=(), center_cols=(), fmt=None):
    fmt = fmt or {}
    for r in range(first, last + 1):
        for c in range(1, ncols + 1):
            cell = ws.cell(r, c)
            cell.border = BOX
            cell.font = font() if c in calc_cols else INPUT
            cell.alignment = CENTER if c in center_cols else TOP
            if c in calc_cols:
                cell.fill = CALC_FILL
            if c in fmt:
                cell.number_format = fmt[c]


def status_colors(ws, rng):
    for k, v in STATUS_COLORS.items():
        ws.conditional_formatting.add(rng, CellIsRule(operator="equal", formula=[f'"{k}"'], fill=fill(v)))


def tile(ws, r, c, label, formula, fmt="0", color=NAVY, width=2):
    for rr in (r, r + 1):
        for cc in range(c, c + width):
            ws.cell(rr, cc).fill = fill("EEF4FF")
    ws.cell(r, c, label).font = font(9, color="475467")
    v = ws.cell(r + 1, c, formula)
    v.font, v.number_format, v.alignment = font(20, True, color), fmt, Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[r + 1].height = 34
    return v


# ===================================================================== build
def build(cfg, out):
    wb = Workbook()
    tz = cfg["timezone"]

    # ------------------------------------------------------------ Settings
    st = wb.active
    st.title = "Settings"
    page_title(st, "Settings", "Set up your project here first. Everything else reads from this sheet.")
    for c, w in zip("ABCDEFGHIJK", [26, 30, 26, 22, 3, 14, 12, 16, 14, 16, 12]):
        st.column_dimensions[c].width = w
    st["A5"] = "Project details"; st["A5"].font = font(12, True, NAVY)
    fields = [("Project name", cfg["name"], None), ("Project lead", cfg["lead"], None),
              ("Start date", cfg["start"], D), ("End date / final deadline", cfg["end"], DT),
              ("Time zone shown in dates", tz, None), ("Description", cfg["description"], None)]
    for i, (k, v, f) in enumerate(fields):
        r = 6 + i
        st.cell(r, 1, k).font = font(10, True)
        c = st.cell(r, 2, v)
        c.font, c.fill, c.border, c.alignment = INPUT, fill("FFF9E6"), BOX, LEFT
        if f:
            c.number_format = f
    st["B11"].alignment = TOP
    st.row_dimensions[11].height = 45
    st["A14"] = "Team members"; st["A14"].font = font(12, True, NAVY)
    header(st, 15, ["Name", "Role", "Email / contact", "GitHub / handle"])
    for i in range(N_MEMBERS):
        r = 16 + i
        m = cfg["members"][i] if i < len(cfg["members"]) else ("", "")
        st.cell(r, 1, m[0]); st.cell(r, 2, m[1])
        for c in range(1, 5):
            st.cell(r, c).font, st.cell(r, c).border, st.cell(r, c).fill = INPUT, BOX, fill("FFF9E6")
    st["F5"] = "Drop-down lists (edit to customise)"; st["F5"].font = font(12, True, NAVY)
    lists = [("Task status", STATUSES), ("Priority", PRIORITIES), ("Progress", PROGRESS),
             ("Learning", LEARN), ("Risk status", RISK_STATUS), ("Mood", MOODS)]
    header(st, 6, [x[0] for x in lists], start_col=6)
    for j, (_, vals) in enumerate(lists):
        for i in range(10):
            c = st.cell(7 + i, 6 + j, vals[i] if i < len(vals) else None)
            c.font, c.border, c.alignment = INPUT, BOX, CENTER
            if j == 2:
                c.number_format = "0%"
    st.cell(18, 6, "Note: task status 'Done' and 'Blocked' are used by formulas: rename them only together with the formulas.").font = font(8, italic=True, color=RED)
    names = {"Members": "Settings!$A$16:$A$25", "Statuses": "Settings!$F$7:$F$16", "Priorities": "Settings!$G$7:$G$16",
             "ProgressVals": "Settings!$H$7:$H$16", "LearnStatus": "Settings!$I$7:$I$16", "RiskStatus": "Settings!$J$7:$J$16",
             "Moods": "Settings!$K$7:$K$16", "ProjStart": "Settings!$B$8", "ProjEnd": "Settings!$B$9",
             "Milestones": f"Milestones!$B$6:$B${5 + N_MS}"}
    for k, v in names.items():
        wb.defined_names[k] = DefinedName(k, attr_text=v)

    # --------------------------------------------------------------- Tasks
    tk = wb.create_sheet("Tasks")
    page_title(tk, "Tasks", f"One row per task. Type in the blue cells; grey columns are calculated. Dates: {tz}, 12-hour AM/PM.")
    cols = ["ID", "Task", "Milestone", "Owner", "Status", "Priority", "Start", "Due", "Completed on",
            "Est. hours", "Progress", "Days left", "Health", "Depends on", "Notes / link", "sort key"]
    header(tk, 5, cols, [8, 44, 18, 18, 13, 11, 16, 24, 16, 9, 10, 9, 13, 11, 36, 4])
    explain(tk, 5, {
        "A": "Filled in automatically when you type a task name.",
        "B": "What needs to be done, in a few words. Start with a verb: 'Write…', 'Fix…', 'Review…'.",
        "C": "Which milestone (phase) this task belongs to. List them on the Milestones sheet.",
        "D": "Who is doing it. Names come from Settings → Team members. Leave empty if nobody has picked it up yet.",
        "E": "Not started → In progress → In review → Done. Use Blocked when you're stuck.",
        "F": "Critical = the project fails without it. High = important. Medium / Low = nice to have.",
        "G": "When work starts. Used to draw the bar on the Timeline.",
        "H": "Deadline (date and time). Overdue tasks turn red.",
        "I": "The date you finished. Feeds the weekly progress chart.",
        "J": "Rough guess of the hours needed. Used to balance the workload.",
        "K": "How far along it is: 0%, 25%, 50%, 75% or 100%.",
        "L": "Calculated: days until the due date.",
        "M": "Calculated: On track / Due soon (3 days or less) / Overdue / Blocked / Done.",
        "N": "ID of a task that must finish first, e.g. T-002.",
        "O": "Anything useful: links, files, decisions."})
    F1, FL = 6, 5 + N_TASKS
    style_rows(tk, F1, FL, 16, calc_cols=(1, 12, 13, 16), center_cols=(1, 3, 4, 5, 6, 10, 11, 12, 13, 14),
               fmt={7: D, 8: DT, 9: D, 10: "0.0", 11: "0%", 12: "0"})
    for i in range(N_TASKS):
        r = F1 + i
        tk.cell(r, 1, f'=IF(B{r}="","","T-"&TEXT(ROW()-5,"000"))')
        tk.cell(r, 12, f'=IF(OR(B{r}="",H{r}="",E{r}="Done"),"",ROUNDDOWN(H{r}-NOW(),0))')
        tk.cell(r, 13, f'=IF(B{r}="","",IF(E{r}="Done","Complete",IF(E{r}="Blocked","Blocked",IF(H{r}="","No due date",'
                       f'IF(H{r}<NOW(),"Overdue",IF(H{r}-NOW()<=3,"Due soon","On track"))))))')
        tk.cell(r, 16, f'=IF(OR(B{r}="",E{r}="Done",H{r}=""),"",H{r}+ROW()/10000000)')
    for i, t in enumerate(cfg["tasks"]):
        r = F1 + i
        for c, k in zip((2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 14, 15), ("task", "ms", "owner", "status", "prio", "start", "due", "done", "hours", "progress", "dep", "notes")):
            if t.get(k) is not None:
                tk.cell(r, c, t[k])
        if t.get("example"):
            for c in (2, 15):
                tk.cell(r, c).font = font(italic=True, color="7F56D9")
    tk.column_dimensions["P"].hidden = True
    dropdown(tk, "Milestones", f"C{F1}:C{FL}", "Milestones come from the Milestones sheet.")
    dropdown(tk, "Members", f"D{F1}:D{FL}", "Names come from Settings → Team members.")
    dropdown(tk, "Statuses", f"E{F1}:E{FL}")
    dropdown(tk, "Priorities", f"F{F1}:F{FL}")
    dropdown(tk, "ProgressVals", f"K{F1}:K{FL}", "0%, 25%, 50%, 75% or 100%.")
    status_colors(tk, f"E{F1}:E{FL}")
    tk.conditional_formatting.add(f"K{F1}:K{FL}", DataBarRule(start_type="num", start_value=0, end_type="num", end_value=1, color=GREEN))
    for k, (bg, fg) in {"Overdue": ("FEE4E2", RED), "Due soon": ("FEF0C7", "B54708"), "Blocked": ("FEE4E2", RED),
                        "On track": ("ECFDF3", "027A48"), "Complete": ("D1FADF", "027A48")}.items():
        tk.conditional_formatting.add(f"M{F1}:M{FL}", CellIsRule(operator="equal", formula=[f'"{k}"'], fill=fill(bg), font=font(10, True, fg)))
    tk.conditional_formatting.add(f"F{F1}:F{FL}", CellIsRule(operator="equal", formula=['"Critical"'], font=font(10, True, RED)))
    tk.conditional_formatting.add(f"B{F1}:B{FL}", FormulaRule(formula=[f'$E{F1}="Done"'], font=Font(name=FONT, size=10, color="98A2B3", strike=True)))
    tk.freeze_panes = f"C{F1}"
    tk.auto_filter.ref = f"A5:O{FL}"
    TR = lambda col: f"Tasks!${col}${F1}:${col}${FL}"

    # ----------------------------------------------------------- Milestones
    ms = wb.create_sheet("Milestones")
    page_title(ms, "Milestones", "Big checkpoints or phases. Tasks are linked to a milestone with the Milestone column on the Tasks sheet.")
    header(ms, 5, ["#", "Milestone", "Target date", "Owner", "Tasks", "Done", "% done", "Status", "Notes"], [5, 34, 24, 18, 8, 8, 10, 14, 40])
    style_rows(ms, 6, 5 + N_MS, 9, calc_cols=(1, 5, 6, 7, 8), center_cols=(1, 4, 5, 6, 7, 8), fmt={3: DT, 7: "0%"})
    for i in range(N_MS):
        r = 6 + i
        ms.cell(r, 1, f'=IF(B{r}="","",ROW()-5)')
        ms.cell(r, 5, f'=IF(B{r}="","",COUNTIF({TR("C")},B{r}))')
        ms.cell(r, 6, f'=IF(B{r}="","",COUNTIFS({TR("C")},B{r},{TR("E")},"Done"))')
        ms.cell(r, 7, f'=IF(OR(B{r}="",E{r}=0),"",F{r}/E{r})')
        ms.cell(r, 8, f'=IF(B{r}="","",IF(AND(E{r}>0,F{r}=E{r}),"Complete",IF(C{r}="","Planned",IF(C{r}<NOW(),"Late","On track"))))')
    for i, m in enumerate(cfg["milestones"]):
        ms.cell(6 + i, 2, m[0]); ms.cell(6 + i, 3, m[1]); ms.cell(6 + i, 9, m[2])
    dropdown(ms, "Members", f"D6:D{5 + N_MS}")
    ms.conditional_formatting.add(f"G6:G{5 + N_MS}", DataBarRule(start_type="num", start_value=0, end_type="num", end_value=1, color=GREEN))
    for k, (bg, fg) in {"Late": ("FEE4E2", RED), "Complete": ("D1FADF", "027A48"), "On track": ("ECFDF3", "027A48")}.items():
        ms.conditional_formatting.add(f"H6:H{5 + N_MS}", CellIsRule(operator="equal", formula=[f'"{k}"'], fill=fill(bg), font=font(10, True, fg)))
    ms.freeze_panes = "C6"

    # ------------------------------------------------------------- Timeline
    tl = wb.create_sheet("Timeline")
    page_title(tl, "Timeline (Gantt)", "Read-only view of the first tasks on the Tasks sheet. Bars run from Start to Due. The gold column is today.")
    tl["E3"] = "Show from:"; tl["E3"].font = font(10, True)
    tl["G3"] = "=ProjStart"; tl["G3"].number_format = D
    c = tl["G3"]; c.font, c.fill, c.border = INPUT, fill("FFF9E6"), BOX
    tl.merge_cells("G3:K3")
    tl["L3"] = "← change this date to scroll the timeline"; tl["L3"].font = font(8, italic=True, color="667085")
    header(tl, 5, ["Task", "Owner", "Status", "Start", "Due"], [36, 14, 12, 11, 11])
    DC = 6
    for k in range(N_DAYS):
        col = DC + k
        tl.column_dimensions[L(col)].width = 3.2
        c = tl.cell(5, col, f"=$G$3+{k}")
        c.number_format, c.font, c.fill, c.alignment = "d", font(7, True, "FFFFFF"), fill(NAVY), CENTER
        c4 = tl.cell(4, col, f'=IF(OR({k}=0,DAY($G$3+{k})=1),TEXT($G$3+{k},"mmm"),"")')
        c4.font = font(8, True, NAVY)
    for i in range(TL_ROWS):
        r, tr = 6 + i, F1 + i
        for j, src in enumerate("BDEGH"):
            c = tl.cell(r, 1 + j, f'=IF(Tasks!$B{tr}="","",Tasks!{src}{tr})')
            c.font, c.border = font(9), BOX
            c.number_format = DS if j >= 3 else "General"
            c.alignment = LEFT if j == 0 else CENTER
        for k in range(N_DAYS):
            tl.cell(r, DC + k).border = Border(left=Side(style="hair", color="EAECF0"), bottom=Side(style="hair", color="EAECF0"))
    last_col = L(DC + N_DAYS - 1)
    grid = f"{L(DC)}6:{last_col}{5 + TL_ROWS}"
    cell0 = f"{L(DC)}$5"
    in_bar = f"AND($A6<>\"\",{cell0}>=INT($D6),{cell0}<=INT($E6))"
    tl.conditional_formatting.add(grid, FormulaRule(formula=[f'AND({in_bar},$C6="Done")'], fill=fill("32D583"), stopIfTrue=True))
    tl.conditional_formatting.add(grid, FormulaRule(formula=[f'AND({in_bar},$E6<NOW())'], fill=fill("F97066"), stopIfTrue=True))
    tl.conditional_formatting.add(grid, FormulaRule(formula=[f'AND({in_bar},$C6="Blocked")'], fill=fill("FDA29B"), stopIfTrue=True))
    tl.conditional_formatting.add(grid, FormulaRule(formula=[in_bar], fill=fill("53B1FD"), stopIfTrue=True))
    tl.conditional_formatting.add(grid, FormulaRule(formula=[f"{cell0}=TODAY()"], fill=fill("FEDF89")))
    tl.conditional_formatting.add(grid, FormulaRule(formula=[f"WEEKDAY({cell0},2)>5"], fill=fill("F9FAFB")))
    status_colors(tl, f"C6:C{5 + TL_ROWS}")
    legend = [("Planned", "53B1FD"), ("Done", "32D583"), ("Overdue", "F97066"), ("Blocked", "FDA29B"), ("Today", "FEDF89")]
    tl["A4"] = "Legend:"; tl["A4"].font = font(9, True)
    for i, (lab, col) in enumerate(legend):
        c = tl.cell(4, 2 + i, lab)
        c.fill, c.font, c.alignment = fill(col), font(8, True), CENTER
    tl.freeze_panes = f"{L(DC)}6"

    # ----------------------------------------------------------- Check-ins
    ci = wb.create_sheet("Check-ins")
    page_title(ci, "Daily Check-ins", "Team progress: one short row per person per day. Anything typed in 'Blocked by' turns red so the lead sees it.")
    header(ci, 5, ["Date", "Member", "What I did", "What I'll do next", "Blocked by", "Hours", "Mood", "Task ID"], [16, 18, 44, 44, 30, 8, 13, 10])
    explain(ci, 5, {"A": "Today's date (Ctrl + ; types it for you).", "B": "Your name (drop-down).",
                    "C": "What you finished since your last check-in.", "D": "What you'll work on next.",
                    "E": "Anything stopping you. Write '—' if nothing. Text here turns red so the lead notices.",
                    "F": "Hours you spent (optional).", "G": "How you feel about your work (optional).",
                    "H": "Related task ID from the Tasks sheet, e.g. T-004 (optional)."})
    style_rows(ci, 6, 5 + N_CHECK, 8, center_cols=(1, 2, 6, 7, 8), fmt={1: D, 6: "0.0"})
    for i, row in enumerate(cfg["checkins"]):
        for j, v in enumerate(row):
            c = ci.cell(6 + i, 1 + j, v)
            c.font = font(italic=True, color="7F56D9")
    ci["A6"].comment = Comment("Example row (purple italics): overwrite it with your first real check-in.", "Template")
    dropdown(ci, "Members", f"B6:B{5 + N_CHECK}")
    dropdown(ci, "Moods", f"G6:G{5 + N_CHECK}")
    ci.conditional_formatting.add(f"E6:E{5 + N_CHECK}", FormulaRule(formula=['AND(E6<>"",E6<>"-",E6<>"—",LOWER(E6)<>"none")'], fill=fill("FEE4E2"), font=font(10, True, RED)))
    ci.freeze_panes = "C6"
    ci.auto_filter.ref = f"A5:H{5 + N_CHECK}"
    CR = lambda col: f"'Check-ins'!${col}$6:${col}${5 + N_CHECK}"

    # -------------------------------------------------------------- Learning
    lr = wb.create_sheet("Learning")
    page_title(lr, "Learning Progress", "Skills the project needs. Each member marks their own column: Not started → In progress → Done.")
    MC = 8  # first member column
    explain(lr, 5, {"C": "What to learn.", "D": "Click to open the free resource.", "E": "Rough study time.",
                    "F": "Calculated: how many members finished this topic.",
                    "H": "Each member has a column: pick Not started / In progress / Done for each topic."})
    header(lr, 5, ["#", "Area", "Topic", "Resource (click)", "Est. hours", "Team done", "Team %"], [5, 20, 28, 36, 9, 9, 9])
    for j in range(N_MEMBERS):
        c = lr.cell(5, MC + j, f'=IF(INDEX(Members,{j + 1})="","Member {j + 1}",INDEX(Members,{j + 1}))')
        c.font, c.fill, c.alignment, c.border = font(9, True, "FFFFFF"), fill(NAVY), CENTER, BOX
        lr.column_dimensions[L(MC + j)].width = 13
    LF, LL = 9, 8 + N_LEARN
    labels = ["Topics done", "% of topics done", "Study hours done"]
    for i, lab in enumerate(labels):
        r = 6 + i
        c = lr.cell(r, 4, lab + " →"); c.font, c.alignment = font(10, True, NAVY), Alignment(horizontal="right")
        for j in range(N_MEMBERS):
            col = L(MC + j)
            rng = f"{col}{LF}:{col}{LL}"
            f = [f'=COUNTIF({rng},"Done")',
                 f'=IFERROR(COUNTIF({rng},"Done")/COUNTA($C${LF}:$C${LL}),0)',
                 f'=SUMIF({rng},"Done",$E${LF}:$E${LL})'][i]
            c = lr.cell(r, MC + j, f)
            c.font, c.alignment, c.border, c.fill = font(10, True), CENTER, BOX, CALC_FILL
            c.number_format = ["0", "0%", "0.0"][i]
    lr.conditional_formatting.add(f"{L(MC)}7:{L(MC + N_MEMBERS - 1)}7", DataBarRule(start_type="num", start_value=0, end_type="num", end_value=1, color=BLUE))
    nm = f"COUNTA(Members)"
    for i in range(N_LEARN):
        r = LF + i
        lr.cell(r, 1, f'=IF(C{r}="","",ROW()-{LF - 1})')
        lr.cell(r, 6, f'=IF(C{r}="","",COUNTIF({L(MC)}{r}:{L(MC + N_MEMBERS - 1)}{r},"Done"))')
        lr.cell(r, 7, f'=IF(OR(C{r}="",{nm}=0),"",F{r}/{nm})')
        for c in range(1, MC + N_MEMBERS):
            cell = lr.cell(r, c)
            cell.border = BOX
            cell.font = font() if c in (1, 6, 7) else INPUT
            cell.alignment = CENTER if c in (1, 5, 6, 7) or c >= MC else TOP
            if c in (1, 6, 7):
                cell.fill = CALC_FILL
        lr.cell(r, 7).number_format = "0%"
    for i, (area, topic, name, url, hours) in enumerate(cfg["learning"]):
        r = LF + i
        lr.cell(r, 2, area); lr.cell(r, 3, topic); lr.cell(r, 5, hours)
        c = lr.cell(r, 4, name)
        if url:
            c.hyperlink = url
            c.font = font(10, color="1155CC", underline="single")
        for j in range(len(cfg["members"])):
            lr.cell(r, MC + j, "Not started")
    dropdown(lr, "LearnStatus", f"{L(MC)}{LF}:{L(MC + N_MEMBERS - 1)}{LL}")
    for k, v in {"Done": "D1FADF", "In progress": "D1E9FF"}.items():
        lr.conditional_formatting.add(f"{L(MC)}{LF}:{L(MC + N_MEMBERS - 1)}{LL}", CellIsRule(operator="equal", formula=[f'"{k}"'], fill=fill(v)))
    lr.conditional_formatting.add(f"G{LF}:G{LL}", DataBarRule(start_type="num", start_value=0, end_type="num", end_value=1, color=GREEN))
    lr.freeze_panes = f"E{LF}"
    lr.row_dimensions[5].height = 32

    # ----------------------------------------------------------------- Risks
    rk = wb.create_sheet("Risks & Issues")
    page_title(rk, "Risks & Issues", "Anything that could go wrong (risk) or already has (issue). Score = likelihood × impact (1–5 each).")
    header(rk, 5, ["ID", "Risk or issue", "Type", "Likelihood (1-5)", "Impact (1-5)", "Score", "Level", "Owner", "Mitigation / next step", "Status", "Review by"],
           [7, 40, 9, 11, 10, 8, 10, 16, 42, 12, 16])
    explain(rk, 5, {"B": "Describe what could go wrong (risk) or what already went wrong (issue).",
                    "D": "How likely is it? 1 = very unlikely … 5 = almost certain.",
                    "E": "How bad would it be? 1 = minor … 5 = project fails.",
                    "F": "Calculated: likelihood × impact. 15+ is High, 8–14 Medium.",
                    "I": "What you'll do to prevent it or limit the damage.",
                    "J": "Open → Monitoring → Closed."})
    RL = 5 + N_RISK
    style_rows(rk, 6, RL, 11, calc_cols=(1, 6, 7), center_cols=(1, 3, 4, 5, 6, 7, 8, 10, 11), fmt={11: D})
    for i in range(N_RISK):
        r = 6 + i
        rk.cell(r, 1, f'=IF(B{r}="","","R-"&TEXT(ROW()-5,"00"))')
        rk.cell(r, 6, f'=IF(OR(D{r}="",E{r}=""),"",D{r}*E{r})')
        rk.cell(r, 7, f'=IF(F{r}="","",IF(F{r}>=15,"High",IF(F{r}>=8,"Medium","Low")))')
    for i, x in enumerate(cfg["risks"]):
        r = 6 + i
        for c, v in zip((2, 3, 4, 5, 8, 9, 10), x):
            rk.cell(r, c, v)
    tdv = DataValidation(type="list", formula1='"Risk,Issue"', allow_blank=True); rk.add_data_validation(tdv); tdv.add(f"C6:C{RL}")
    sdv = DataValidation(type="whole", operator="between", formula1="1", formula2="5", allow_blank=True,
                         showErrorMessage=True, error="Enter a whole number from 1 (low) to 5 (high).")
    rk.add_data_validation(sdv); sdv.add(f"D6:E{RL}")
    dropdown(rk, "Members", f"H6:H{RL}")
    dropdown(rk, "RiskStatus", f"J6:J{RL}")
    rk.conditional_formatting.add(f"F6:F{RL}", ColorScaleRule(start_type="num", start_value=1, start_color="D1FADF",
                                                               mid_type="num", mid_value=8, mid_color="FEF0C7", end_type="num", end_value=25, end_color="FDA29B"))
    rk.conditional_formatting.add(f"G6:G{RL}", CellIsRule(operator="equal", formula=['"High"'], font=font(10, True, RED)))
    rk.conditional_formatting.add(f"B6:J{RL}", FormulaRule(formula=['$J6="Closed"'], font=Font(name=FONT, size=10, color="98A2B3")))
    rk.freeze_panes = "C6"
    rk.auto_filter.ref = f"A5:K{RL}"

    # ------------------------------------------------------------- Dashboard
    db = wb.create_sheet("Dashboard", 0)
    db.sheet_view.showGridLines = False
    for i, w in enumerate([16, 11, 3, 16, 11, 3, 16, 11, 3, 16, 11, 3, 16, 11], 1):
        db.column_dimensions[L(i)].width = w
    db["A1"] = '=Settings!B6&"  ·  Project Dashboard"'; db["A1"].font = font(20, True, NAVY)
    db["A2"] = '="Lead: "&Settings!B7&"   ·   "&TEXT(ProjStart,"mmm d, yyyy")&" → "&TEXT(ProjEnd,"mmm d, yyyy h:mm AM/PM")&"   ·   Times: "&Settings!B10'
    db["A2"].font = font(10, italic=True, color="667085")
    db["A3"] = '="Updated "&TEXT(NOW(),"ddd, mmm d yyyy, h:mm AM/PM")&"  ·  All numbers are formulas: edit the other sheets, not this one."'
    db["A3"].font = font(8, italic=True, color="98A2B3")
    db.row_dimensions[1].height = 34

    T, S = TR("B"), TR("E")
    done = f'COUNTIF({S},"Done")'
    total = f"COUNTA({T})"
    tile(db, 5, 1, "Tasks", f"={total}")
    tile(db, 5, 4, "Done", f"={done}", color="027A48")
    tile(db, 5, 7, "% complete", f"=IFERROR({done}/{total},0)", "0%", "027A48")
    tile(db, 5, 10, "Avg. progress", f'=IFERROR(SUMPRODUCT(({T}<>"")*{TR("K")})/{total},0)', "0%")
    tile(db, 5, 13, "Days to deadline", "=IF(ProjEnd=\"\",\"—\",MAX(0,ROUNDDOWN(ProjEnd-NOW(),0)))")
    tile(db, 8, 1, "Overdue", f'=COUNTIF({TR("M")},"Overdue")', color=RED)
    tile(db, 8, 4, "Due in 7 days", f'=SUMPRODUCT(({T}<>"")*({S}<>"Done")*({TR("H")}>=NOW())*({TR("H")}<NOW()+7))', color="B54708")
    tile(db, 8, 7, "Blocked", f'=COUNTIF({S},"Blocked")', color=RED)
    tile(db, 8, 10, "Unassigned (open)", f'=SUMPRODUCT(({T}<>"")*({S}<>"Done")*({TR("D")}=""))', color="B54708")
    tile(db, 8, 13, "High risks open", f"=COUNTIFS('Risks & Issues'!$G$6:$G${RL},\"High\",'Risks & Issues'!$J$6:$J${RL},\"<>Closed\")", color=RED)
    for a in ("A9", "G9", "M9"):
        db.conditional_formatting.add(a, CellIsRule(operator="equal", formula=["0"], font=font(20, True, "027A48")))

    # health
    db["A11"] = "Project health"; db["A11"].font = font(12, True, NAVY)
    db["A12"] = "Time elapsed"; db["A12"].font = font(9, color="475467")
    db["B12"] = '=IFERROR(MAX(0,MIN(1,(NOW()-ProjStart)/(ProjEnd-ProjStart))),0)'; db["B12"].number_format = "0%"
    db["A13"] = "Work complete"; db["A13"].font = font(9, color="475467")
    db["B13"] = "=G6"; db["B13"].number_format = "0%"
    for a in ("B12", "B13"):
        db[a].font = font(11, True)
    db.conditional_formatting.add("B12:B13", DataBarRule(start_type="num", start_value=0, end_type="num", end_value=1, color=BLUE))
    db["D12"] = '=IF(A9+G9>0,"AT RISK",IF(B13+0.15<B12,"BEHIND SCHEDULE","ON TRACK"))'
    db["D12"].font = font(16, True, NAVY)
    db.merge_cells("D12:H13")
    for txt, col in (("AT RISK", RED), ("BEHIND SCHEDULE", "B54708"), ("ON TRACK", "027A48")):
        db.conditional_formatting.add("D12", CellIsRule(operator="equal", formula=[f'"{txt}"'], font=font(16, True, col)))
    db["D12"].alignment = Alignment(horizontal="left", vertical="center")
    db["J12"] = "Rule: at risk if anything is overdue or blocked; behind if work done trails time elapsed by more than 15 points."
    db["J12"].font = font(8, italic=True, color="667085"); db["J12"].alignment = TOP
    db.merge_cells("J12:N13")

    # member focus
    db["A15"] = "Member focus"; db["A15"].font = font(12, True, NAVY)
    db["A16"] = "Pick a member ▸"; db["A16"].font = font(10, True)
    sel = db["B16"]
    sel.value = cfg["members"][0][0] if cfg["members"] else ""
    sel.font, sel.fill, sel.border = font(11, True, "0000FF"), fill("FFF9E6"), BOX
    db.merge_cells("B16:E16")
    dropdown(db, "Members", "B16", "Pick anyone to see their workload.")
    SEL = "$B$16"
    nd = f'SUMPRODUCT(MIN({TR("H")}+(({TR("D")}<>{SEL})+({S}="Done")+({TR("H")}=""))*1000000))'
    focus = [("Open tasks", f'=COUNTIFS({TR("D")},{SEL},{S},"<>Done")', "0"),
             ("Done", f'=COUNTIFS({TR("D")},{SEL},{S},"Done")', "0"),
             ("Overdue", f'=COUNTIFS({TR("D")},{SEL},{TR("M")},"Overdue")', "0"),
             ("Open hours (est.)", f'=SUMIFS({TR("J")},{TR("D")},{SEL},{S},"<>Done")', "0.0"),
             ("Next due", f'=IF({nd}>100000,"—",{nd})', DT),
             ("Next task", f'=IF({nd}>100000,"—",INDEX(Tasks!$B:$B,SUMPRODUCT(MAX(({TR("D")}={SEL})*({S}<>"Done")*({TR("H")}={nd})*ROW({TR("H")})))))', "@"),
             ("Last check-in", f'=IF(COUNTIF({CR("B")},{SEL})=0,"—",SUMPRODUCT(MAX(({CR("B")}={SEL})*{CR("A")})))', D),
             ("Learning done", f"=IFERROR(INDEX(Learning!$H$7:$Q$7,MATCH({SEL},Learning!$H$5:$Q$5,0)),0)", "0%")]
    for i, (lab, f, fmt) in enumerate(focus):
        r = 17 + i
        db.cell(r, 1, lab).font = font(9, color="475467")
        c = db.cell(r, 2, f)
        c.font, c.number_format, c.alignment = font(10, True), fmt, LEFT
        db.merge_cells(start_row=r, start_column=2, end_row=r, end_column=5)
    db.conditional_formatting.add("B19", CellIsRule(operator="greaterThan", formula=["0"], font=font(10, True, RED)))

    # upcoming deadlines
    db["G15"] = "Next deadlines (open tasks)"; db["G15"].font = font(12, True, NAVY)
    for i, h in enumerate(["Due", "Task", "", "", "Owner", "Status"]):
        if h:
            c = db.cell(16, 7 + i, h); c.font, c.fill, c.alignment = font(9, True, "FFFFFF"), fill(NAVY), CENTER
    db.merge_cells("H16:J16")
    for k in range(1, 9):
        r = 16 + k
        key = f'IFERROR(SMALL({TR("P")},{k}),"")'
        rowref = f'MATCH(SMALL({TR("P")},{k}),{TR("P")},0)'
        db.cell(r, 7, f'=IFERROR(INDEX({TR("H")},{rowref}),"")').number_format = "ddd mmm d, h:mm AM/PM"
        db.cell(r, 8, f'=IFERROR(INDEX({TR("B")},{rowref}),"")')
        db.cell(r, 11, f'=IFERROR(IF(INDEX({TR("D")},{rowref})="","(unassigned)",INDEX({TR("D")},{rowref})),"")')
        db.cell(r, 12, f'=IFERROR(INDEX({TR("E")},{rowref}),"")')
        db.merge_cells(start_row=r, start_column=8, end_row=r, end_column=10)
        for c in (7, 8, 11, 12):
            db.cell(r, c).font, db.cell(r, c).border = font(9), BOX
            db.cell(r, c).alignment = LEFT if c == 8 else CENTER
    db.conditional_formatting.add("G17:G24", FormulaRule(formula=['AND(G17<>"",G17<NOW())'], font=font(9, True, RED)))
    status_colors(db, "L17:L24")

    # status + priority tables (feed charts)
    r0 = 27
    db.cell(r0, 1, "Tasks by status").font = font(12, True, NAVY)
    db.cell(r0 + 1, 1, "Status").font = font(9, True); db.cell(r0 + 1, 2, "Tasks").font = font(9, True)
    for i in range(5):
        r = r0 + 2 + i
        db.cell(r, 1, f"=INDEX(Statuses,{i + 1})").font = font(9)
        db.cell(r, 2, f"=COUNTIF({S},A{r})").font = font(9)
    db.cell(r0, 4, "Open tasks by priority").font = font(12, True, NAVY)
    db.cell(r0 + 1, 4, "Priority").font = font(9, True); db.cell(r0 + 1, 5, "Open").font = font(9, True)
    for i in range(4):
        r = r0 + 2 + i
        db.cell(r, 4, f"=INDEX(Priorities,{i + 1})").font = font(9)
        db.cell(r, 5, f'=COUNTIFS({TR("F")},D{r},{S},"<>Done")').font = font(9)

    # workload table
    w0 = 46
    db.cell(w0, 1, "Team workload & engagement").font = font(12, True, NAVY)
    wh = ["Member", "Open", "Done", "Overdue", "Hours open", "Check-ins (7d)", "Learning %"]
    for i, h in enumerate(wh):
        c = db.cell(w0 + 1, 1 + i, h); c.font, c.fill, c.alignment, c.border = font(9, True, "FFFFFF"), fill(NAVY), CENTER, BOX
    for i in range(N_MEMBERS):
        r = w0 + 2 + i
        db.cell(r, 1, f'=IF(INDEX(Members,{i + 1})="","",INDEX(Members,{i + 1}))')
        db.cell(r, 2, f'=IF(A{r}="","",COUNTIFS({TR("D")},A{r},{S},"<>Done"))')
        db.cell(r, 3, f'=IF(A{r}="","",COUNTIFS({TR("D")},A{r},{S},"Done"))')
        db.cell(r, 4, f'=IF(A{r}="","",COUNTIFS({TR("D")},A{r},{TR("M")},"Overdue"))')
        db.cell(r, 5, f'=IF(A{r}="","",SUMIFS({TR("J")},{TR("D")},A{r},{S},"<>Done"))')
        db.cell(r, 6, f'=IF(A{r}="","",COUNTIFS({CR("B")},A{r},{CR("A")},">="&(TODAY()-6)))')
        db.cell(r, 7, f'=IF(A{r}="","",IFERROR(INDEX(Learning!$H$7:$Q$7,MATCH(A{r},Learning!$H$5:$Q$5,0)),0))')
        for c in range(1, 8):
            db.cell(r, c).font, db.cell(r, c).border, db.cell(r, c).alignment = font(9), BOX, CENTER
        db.cell(r, 5).number_format = "0.0"; db.cell(r, 7).number_format = "0%"
    db.conditional_formatting.add(f"D{w0 + 2}:D{w0 + 11}", CellIsRule(operator="greaterThan", formula=["0"], font=font(9, True, RED), fill=fill("FEE4E2")))
    db.conditional_formatting.add(f"G{w0 + 2}:G{w0 + 11}", DataBarRule(start_type="num", start_value=0, end_type="num", end_value=1, color=BLUE))
    db.conditional_formatting.add(f"B{w0 + 2}:B{w0 + 11}", DataBarRule(start_type="min", end_type="max", color="FDB022"))

    # weekly completion
    k0 = 46
    db.cell(k0, 9, "Weekly progress (burn-up)").font = font(12, True, NAVY)
    for i, h in enumerate(["Week of", "Completed", "Cumulative", "Total tasks"]):
        c = db.cell(k0 + 1, 10 + i, h); c.font, c.fill, c.alignment, c.border = font(9, True, "FFFFFF"), fill(NAVY), CENTER, BOX
    for k in range(N_WEEKS):
        r = k0 + 2 + k
        db.cell(r, 10, f"=INT(ProjStart)+7*{k}").number_format = "mmm d"
        db.cell(r, 11, f'=COUNTIFS({TR("I")},">="&J{r},{TR("I")},"<"&(J{r}+7))')
        db.cell(r, 12, f'=IF(J{r}>TODAY(),NA(),COUNTIFS({TR("I")},"<"&(J{r}+7),{S},"Done"))')
        db.cell(r, 13, f"={total}")
        for c in range(10, 14):
            db.cell(r, c).font, db.cell(r, c).border, db.cell(r, c).alignment = font(9), BOX, CENTER
    db.cell(k0 + 2 + N_WEEKS, 10, "#N/A hides future weeks in the chart.").font = font(7, italic=True, color="98A2B3")

    # charts
    pie = PieChart()
    pie.title = "Tasks by status"
    pie.add_data(Reference(db, min_col=2, min_row=r0 + 1, max_row=r0 + 6), titles_from_data=True)
    pie.set_categories(Reference(db, min_col=1, min_row=r0 + 2, max_row=r0 + 6))
    pie.dataLabels = DataLabelList(); pie.dataLabels.showVal = True
    pie.height, pie.width = 7.5, 11
    db.add_chart(pie, f"G{r0}")
    bar = BarChart(); bar.type = "bar"; bar.title = "Open tasks by priority"; bar.style = 10
    bar.add_data(Reference(db, min_col=5, min_row=r0 + 1, max_row=r0 + 5), titles_from_data=True)
    bar.set_categories(Reference(db, min_col=4, min_row=r0 + 2, max_row=r0 + 5))
    bar.legend = None; bar.height, bar.width = 7.5, 9
    db.add_chart(bar, f"L{r0}")
    wl = BarChart(); wl.type = "col"; wl.grouping = "stacked"; wl.overlap = 100; wl.title = "Workload per member"
    wl.add_data(Reference(db, min_col=2, max_col=3, min_row=w0 + 1, max_row=w0 + 1 + len(cfg["members"]) or w0 + 2), titles_from_data=True)
    wl.set_categories(Reference(db, min_col=1, min_row=w0 + 2, max_row=w0 + 1 + max(1, len(cfg["members"]))))
    wl.height, wl.width = 8, 16
    db.add_chart(wl, f"A{w0 + 13}")
    ln = LineChart(); ln.title = "Burn-up: done vs total"
    ln.add_data(Reference(db, min_col=12, max_col=13, min_row=k0 + 1, max_row=k0 + 1 + N_WEEKS), titles_from_data=True)
    ln.set_categories(Reference(db, min_col=10, min_row=k0 + 2, max_row=k0 + 1 + N_WEEKS))
    ln.height, ln.width = 8, 14
    ln.y_axis.title = "Tasks"
    db.add_chart(ln, f"I{w0 + 2 + N_WEEKS + 1}")

    # protect the dashboard (no password) except the member picker
    for row in db.iter_rows(min_row=1, max_row=90, max_col=14):
        for c in row:
            c.protection = Protection(locked=True)
    db["B16"].protection = Protection(locked=False)
    db.protection.sheet = True
    db.protection.formatColumns = False
    db.protection.formatRows = False

    # ------------------------------------------------------------- Start Here
    sh = wb.create_sheet("Start Here", 0)
    sh.sheet_view.showGridLines = False
    sh.column_dimensions["A"].width = 4
    sh.column_dimensions["B"].width = 28
    sh.column_dimensions["C"].width = 90
    sh["B2"] = "Project Tracker"; sh["B2"].font = font(24, True, NAVY)
    sh["B3"] = '=Settings!B6'; sh["B3"].font = font(14, True, GOLD)
    sh["B4"] = "Tasks · timeline · milestones · daily check-ins · learning · risks, all in one workbook."
    sh["B4"].font = font(10, italic=True, color="667085")
    sh["B6"] = "Go to"; sh["B6"].font = font(12, True, NAVY)
    sheets = [("Dashboard", "Live overview: KPIs, project health, member focus picker, deadlines and charts."),
              ("Tasks", "Your to-do list. One row per task with owner, status, priority, dates and progress."),
              ("Timeline", "Gantt chart built automatically from the Tasks sheet. Change the start date to scroll."),
              ("Milestones", "Big checkpoints. % done is calculated from the tasks linked to each one."),
              ("Check-ins", "Daily stand-up log: what I did, what's next, what's blocking me, and my mood."),
              ("Learning", "Skills matrix: every member tracks the topics they're learning."),
              ("Risks & Issues", "What could go wrong, how bad it is (score), who owns it, and the plan."),
              ("Settings", "Project name, dates, time zone, team members and drop-down lists.")]
    for i, (name, desc) in enumerate(sheets):
        r = 7 + i
        c = sh.cell(r, 2, f"▸ {name}")
        c.hyperlink = f"#'{name}'!A1"
        c.font, c.fill, c.border = font(11, True, "1155CC", underline="single"), fill("EEF4FF"), BOX
        d = sh.cell(r, 3, desc); d.font, d.border, d.alignment = font(10), BOX, LEFT
        sh.row_dimensions[r].height = 22
    sh["B16"] = "Set up in 3 steps"; sh["B16"].font = font(12, True, NAVY)
    steps = ["1 · Settings: type your project name, start and end dates, time zone and team members.",
             "2 · Milestones: list your big checkpoints. Then add tasks on the Tasks sheet and link each one to a milestone.",
             "3 · Every day: update task status and progress, and add a short row on Check-ins. The Dashboard does the rest."]
    for i, s in enumerate(steps):
        c = sh.cell(17 + i, 2, s); c.font = font(10)
        sh.merge_cells(start_row=17 + i, start_column=2, end_row=17 + i, end_column=3)
    sh["B21"] = "Colour key"; sh["B21"].font = font(12, True, NAVY)
    key = [("Blue text", "Cells you type in (inputs).", "0000FF", None),
           ("Grey cells", "Calculated by formulas: don't type here.", "1D2939", GREY),
           ("Purple italics", "Example rows: overwrite or delete them.", "7F56D9", None),
           ("Red", "Overdue, blocked or high risk: needs attention.", RED, None)]
    for i, (k, v, fc, bg) in enumerate(key):
        r = 22 + i
        a = sh.cell(r, 2, k); a.font = font(10, True, fc)
        if bg:
            a.fill = fill(bg)
        sh.cell(r, 3, v).font = font(10)
    sh["B27"] = "Tips"; sh["B27"].font = font(12, True, NAVY)
    tips = ["Use the filter arrows on each header row to see only your own tasks, or only open ones.",
            "Share the workbook through OneDrive, SharePoint or Google Drive so everyone edits the same copy.",
            "The Dashboard is protected so its formulas can't be broken by accident (Review → Unprotect Sheet, no password).",
            f"All dates and times are shown in the time zone set on the Settings sheet (currently: {tz}), 12-hour AM/PM.",
            "Need more rows? Tasks has 300, Check-ins 500, Learning 150 and Risks 100 ready to use."]
    for i, t in enumerate(tips):
        c = sh.cell(28 + i, 2, "• " + t); c.font = font(10)
        sh.merge_cells(start_row=28 + i, start_column=2, end_row=28 + i, end_column=3)

    # ---------------------------------------------------------------- finish
    colors = {"Start Here": GOLD, "Dashboard": GOLD, "Tasks": NAVY, "Timeline": NAVY, "Milestones": NAVY,
              "Check-ins": BLUE, "Learning": GREEN, "Risks & Issues": RED, "Settings": "667085"}
    for ws in wb.worksheets:
        ws.sheet_properties.tabColor = colors[ws.title]
        ws.page_setup.orientation = "landscape"
        ws.page_setup.fitToWidth = 1
        ws.sheet_properties.pageSetUpPr.fitToPage = True
        ws.page_setup.fitToHeight = 0
    wb.active = 0
    wb.calculation.fullCalcOnLoad = True
    out.parent.mkdir(parents=True, exist_ok=True)
    wb.save(out)
    print("saved", out)


# ===================================================================== data
def learning_from_docs():
    md = (REPO / "docs" / "learning-resources.md").read_text(encoding="utf-8")
    out, area = [], ""
    for line in md.splitlines():
        m = re.match(r"## \d+\. (.+)", line)
        if m:
            area = m.group(1)
            continue
        if line.startswith("|") and "](" in line:
            parts = [p.strip() for p in line.strip("|").split("|")]
            if len(parts) >= 3:
                name, url = re.search(r"\[([^\]]+)\]\(([^)]+)\)", parts[1]).groups()
                h = re.match(r"([\d.]+)\s*(h|min)", parts[2])
                hours = (float(h.group(1)) if h.group(2) == "h" else round(float(h.group(1)) / 60, 2)) if h else None
                out.append((area, parts[0], name, url, hours))
    return out


today = date.today()
TEMPLATE = dict(
    name="My Project", lead="Your name", start=today, end=datetime.combine(today + timedelta(days=56), datetime.min.time()) + timedelta(hours=17),
    timezone="Local time", description="One or two sentences on what this project delivers and for whom.",
    members=[("Alex (example)", "Lead"), ("Sam (example)", "Member"), ("Jordan (example)", "Member")],
    milestones=[("Planning", datetime.combine(today + timedelta(days=7), datetime.min.time()) + timedelta(hours=17), "Example milestone"),
                ("Build", datetime.combine(today + timedelta(days=35), datetime.min.time()) + timedelta(hours=17), "Example milestone"),
                ("Launch", datetime.combine(today + timedelta(days=56), datetime.min.time()) + timedelta(hours=17), "Example milestone")],
    tasks=[
        dict(task="Example: write the project brief", ms="Planning", owner="Alex (example)", status="Done", prio="High",
             start=today, due=datetime.combine(today + timedelta(days=3), datetime.min.time()) + timedelta(hours=17), done=today, hours=3, progress=1, notes="Example row: overwrite or delete", example=True),
        dict(task="Example: set up the shared workspace", ms="Planning", owner="Sam (example)", status="In progress", prio="Medium",
             start=today, due=datetime.combine(today + timedelta(days=6), datetime.min.time()) + timedelta(hours=12), hours=2, progress=0.5, notes="Example row", example=True),
        dict(task="Example: build the first version", ms="Build", owner="Jordan (example)", status="Not started", prio="Critical",
             start=today + timedelta(days=7), due=datetime.combine(today + timedelta(days=30), datetime.min.time()) + timedelta(hours=17), hours=20, progress=0, dep="T-002", notes="Example row", example=True),
    ],
    checkins=[(today, "Alex (example)", "Wrote the project brief and shared it", "Review feedback with the team", "—", 2, "Good", "T-001")],
    learning=[("Example area", "Example topic", "Example resource (link)", "https://example.com", 2)],
    risks=[("Example: key person unavailable near the deadline", "Risk", 2, 4, "Alex (example)", "Pair up on every critical task", "Open")],
)

DUE1 = datetime(2026, 10, 10, 14, 59)
w1 = [("Rename notebook, set TEAM_ID = 1065 and TEAM_NAME", "Done", "High", None),
      ("Task 1 – Data-quality audit and issue log (15 pts)", "Done", "High", 15),
      ("Task 2 – Consistency, validity and timeliness fixes (15 pts)", "Done", "High", 15),
      ("Task 3 – Imputation study (15 pts)", "Done", "High", 15),
      ("Task 4 – Outliers and transformations (10 pts)", "Done", "Medium", 10),
      ("Task 5 – Leak-free pipeline + TimeSeriesSplit CV (15 pts)", "Done", "High", 15),
      ("Task 6 – Impact study on the test year (20 pts)", "Done", "Critical", 20),
      ("Final summary cell (10 pts)", "Done", "High", 10),
      ("Bonus – parallel per-station cleaning, HPC (+10 pts)", "Done", "Medium", 10),
      ("Team review of the notebook + Restart & Run All", "Not started", "Critical", None),
      ("Upload notebook via the Google Form (team leader, Team ID 1065)", "Not started", "Critical", None),
      ("Keep beijing_clean_team1065.csv.gz for Week 2", "Done", "Medium", None)]
LINESHINE = dict(
    name="AKT26 Hackathon · Team LineShine", lead="Abdallah Ismail", start=date(2026, 10, 3), end=datetime(2026, 11, 7, 23, 59),
    timezone="Cairo (EEST, UTC+3)", description="Al-Khawarizmi Tour Online Hackathon (HPC & AI). Team ID 1065. Weekly AI-track assignments, Oct 3 – Nov 7, 2026.",
    members=[("Abdallah Ismail", "Team leader"), ("Omar Seifelnasr", "Member"), ("Abdulrahman Omran", "Member"),
             ("Anas Elgalad", "Member"), ("Mohamed Abd Elaal", "Member"), ("Mohamed Salah", "Member")],
    milestones=[("Week 1 – Air-Quality Data Challenge", DUE1, "Deadline Oct 9, 11:59 PM AoE = Sat Oct 10, 2:59 PM Cairo"),
                ("Week 2 – AI Methods Shoot-out", None, "Deadline announced later"),
                ("Week 3", None, ""), ("Week 4", None, ""), ("Week 5 – Final", None, "Hackathon ends Nov 7, 2026")],
    tasks=[dict(task=t, ms="Week 1 – Air-Quality Data Challenge", status=s, prio=p, hours=None, start=date(2026, 10, 3), due=DUE1,
                done=date(2026, 10, 9) if s == "Done" else None, progress=1 if s == "Done" else 0, notes=(f"{pts} points" if pts else None)) for t, s, p, pts in w1],
    checkins=[(date(2026, 10, 9), "Anas Elgalad", "Ran the full notebook; checked every answer cell against the outputs", "Review the final summary with the team", "—", 2.5, "Good", "T-010")],
    learning=learning_from_docs(),
    risks=[("Deadline confusion: organisers use Anywhere-on-Earth time", "Risk", 3, 5, "Abdallah Ismail", "Use Cairo time everywhere: Sat Oct 10, 2:59 PM", "Monitoring"),
           ("Notebook merge conflicts when several people edit it", "Risk", 4, 3, None, "Edit scripts/build_notebook.py, not the notebook; one integrator", "Open"),
           ("UCI download fails, so the notebook silently uses synthetic data", "Issue", 5, 5, None, "Real data committed in data/raw + assert in notebook", "Closed")],
)

NOTION_GUIDE = """# {name} – Project Tracker

{description}

This is a Notion page with five linked tables: **Tasks**, **Milestones**, **Check-ins**, **Learning** and **Risks**.
All times are **{tz}**, 12-hour AM/PM.

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
"""


def build_notion(cfg, folder):
    import csv
    folder.mkdir(parents=True, exist_ok=True)

    def fmt(v, with_time=False):
        if v is None:
            return ""
        if isinstance(v, datetime):
            return v.strftime("%B %d, %Y %I:%M %p")
        if isinstance(v, date):
            return v.strftime("%B %d, %Y")
        return v

    def write(name, head, rows):
        with open(folder / name, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(head)
            w.writerows(rows)

    write("Tasks.csv", ["Task", "Milestone", "Owner", "Status", "Priority", "Start", "Due", "Completed on", "Est. hours", "Progress", "Depends on", "Notes"],
          [[t["task"], t.get("ms") or "", t.get("owner") or "", t["status"], t["prio"], fmt(t.get("start")), fmt(t.get("due")),
            fmt(t.get("done")), t.get("hours") or "", t.get("progress", 0), t.get("dep") or "", t.get("notes") or ""] for t in cfg["tasks"]])
    write("Milestones.csv", ["Milestone", "Target date", "Notes"], [[m[0], fmt(m[1]), m[2]] for m in cfg["milestones"]])
    write("Check-ins.csv", ["Date", "Member", "What I did", "What I'll do next", "Blocked by", "Hours", "Mood"],
          [[fmt(c[0]), *c[1:7]] for c in cfg["checkins"]])
    write("Learning.csv", ["Topic", "Area", "Resource", "Link", "Est. hours", "Member", "Status"],
          [[t[1], t[0], t[2], t[3] or "", t[4] or "", "", "Not started"] for t in cfg["learning"]])
    write("Risks.csv", ["Risk or issue", "Type", "Likelihood", "Impact", "Owner", "Mitigation", "Status"],
          [[r[0], r[1], r[2], r[3], r[4] or "", r[5], r[6]] for r in cfg["risks"]])
    (folder / "README.md").write_text(NOTION_GUIDE.format(name=cfg["name"], description=cfg["description"], tz=cfg["timezone"]), encoding="utf-8")
    print("saved", folder)


if __name__ == "__main__":
    build(TEMPLATE, REPO / "tracker" / "excel" / "Project_Tracker_Template.xlsx")
    build(LINESHINE, REPO / "tracker" / "excel" / "LineShine_Tracker.xlsx")
    build_notion(TEMPLATE, REPO / "tracker" / "notion" / "template")
    build_notion(LINESHINE, REPO / "tracker" / "notion" / "lineshine")
