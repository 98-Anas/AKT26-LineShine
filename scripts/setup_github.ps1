# One-time setup: creates the GitHub repo, labels, sprint issues and a Project board.
# Prereqs:  winget install --id GitHub.cli ;  gh auth login ;  gh auth refresh -s project
# Run from the repo root:  powershell -ExecutionPolicy Bypass -File scripts\setup_github.ps1
param([string]$Repo = "AKT26-LineShine", [ValidateSet("private","public")][string]$Visibility = "private")
$ErrorActionPreference = "Stop"
$Owner = gh api user --jq .login
Write-Host "Owner: $Owner"

gh repo create "$Owner/$Repo" --$Visibility --source . --remote origin --push --description "AKT26 Hackathon - Team LineShine (ID 1065)"

$labels = @{ "sprint-1"="1d76db"; "task"="0e8a16"; "bonus"="fbca04"; "blocker"="b60205"; "learning"="c5def5" }
foreach ($l in $labels.Keys) { gh label create $l --color $labels[$l] --repo "$Owner/$Repo" --force | Out-Null }

$projUrl = gh project create --owner $Owner --title "AKT26 LineShine Board" --format json --jq .url
$projNum = ($projUrl -split "/")[-1]
gh project link $projNum --owner $Owner --repo "$Owner/$Repo"

$tasks = @(
  @("S1-00 Setup: rename notebook, TEAM_ID=1065, regenerate data", "task"),
  @("S1-01 Task 1: data-quality audit (15 pts)", "task"),
  @("S1-02 Task 1: fill issue_log", "task"),
  @("S1-03 Task 2: clean_basic with data-driven detection (15 pts)", "task"),
  @("S1-04 Task 3: imputation study (15 pts)", "task"),
  @("S1-05 Task 4: outliers and transforms (10 pts)", "task"),
  @("S1-06 Task 5: leak-free pipeline + TimeSeriesSplit (15 pts)", "task"),
  @("S1-07 Task 6: impact study on test year (20 pts)", "task"),
  @("S1-08 Bonus: HPC per-station parallel cleaning (+10)", "bonus"),
  @("S1-09 Final summary markdown cell (10 pts)", "task"),
  @("S1-10 Export beijing_clean_team1065.csv.gz", "task"),
  @("S1-11 Restart & Run All, submission check, upload form", "task")
)
foreach ($t in $tasks) {
  $body = "See docs/TASK-TRACKER.md and docs/SPRINT-1.md (Definition of Done)."
  $url = gh issue create --repo "$Owner/$Repo" --title $t[0] --body $body --label "sprint-1" --label $t[1]
  gh project item-add $projNum --owner $Owner --url $url | Out-Null
  Write-Host "created $url"
}
Write-Host "`nDone. Repo: https://github.com/$Owner/$Repo  Board: $projUrl"
Write-Host "Invite teammates:  gh api -X PUT repos/$Owner/$Repo/collaborators/<their-username>"
