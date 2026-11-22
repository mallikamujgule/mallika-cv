#!/usr/bin/env python3
"""
track_applications.py — simple job application tracker (one CSV file).

The CSV lives at ~/Documents/mallika_applications_tracker.csv (override with
LLM_CV_TRACKER_CSV). It opens in Excel, Numbers or Google Sheets.

The pipeline adds every application automatically:
  - run_pipeline.sh stage1 adds the row (Status: In progress)
  - run_pipeline.sh finish updates it (Status: Ready to apply)

Columns you edit by hand are never overwritten by the pipeline:
  Status, Applied On, Notes

Usage:
  # Add or update one application (the pipeline does this for you):
  .venv/bin/python track_applications.py --append "<application folder>" [--status "Ready to apply"]

  # Change a status later; "Applied" also fills Applied On with today's date:
  .venv/bin/python track_applications.py --mark "UP42" "Applied"
  .venv/bin/python track_applications.py --mark "UP42" "Interview" --note "Call on 20.11"

  # Rebuild the whole CSV from the application folders (keeps your manual columns):
  .venv/bin/python track_applications.py --rebuild

  # Print the tracker:
  .venv/bin/python track_applications.py --list

Suggested statuses: In progress, Ready to apply, Applied, Interview, Offer,
Rejected, No response, Withdrawn.
"""
import argparse
import csv
import datetime as dt
import re
import sys
from pathlib import Path

import yaml

from config import APPLICATIONS_DIR as _APPS, TRACKER_CSV as _CSV

APPLICATIONS_DIR = Path(_APPS)
CSV_PATH = Path(_CSV)

CSV_COLUMNS = [
    "Date",              # day the application folder was created
    "Company",
    "Position",
    "Location",
    "Status",            # manual: see suggested statuses above
    "Applied On",        # manual: filled when Status is set to Applied
    "Application Source",
    "Source URL",
    "ATS Pre-Score",
    "ATS Post-Score",
    "Score Delta",
    "Score Gate",
    "Role Archetype",
    "Language",
    "Resume Style",
    "ATS Vendor",
    "Skill Gaps",
    "Projects Used",
    "Notes",             # manual
    "Folder Path",
]
MANUAL_COLUMNS = ["Status", "Applied On", "Notes"]
# Statuses the pipeline sets itself; they never replace a status you moved forward.
PIPELINE_STATUSES = {"in progress", "ready to apply"}
DATE_IN_PATH = re.compile(r"/(\d{4})/(\d{2})/(\d{2})/[^/]+/?$")


# ─── Reading an application folder ────────────────────────────────────────────

def _load_yaml(path: Path) -> dict:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def find_application_folders(root: Path) -> list:
    """Folders laid out as <root>/YYYY/MM/DD/<Company — Role>/ that hold an ATS_Report.yaml."""
    found = []
    if not root.exists():
        return found
    for ats in sorted(root.glob("*/*/*/*/ATS_Report.yaml")):
        found.append(ats.parent)
    return found


def extract_projects(app_dir: Path) -> list:
    names = []
    resume = _load_yaml(app_dir / "Resume.yaml")
    for p in resume.get("projects", []) or []:
        if isinstance(p, dict) and p.get("name"):
            names.append(p["name"])
    for exp in resume.get("professional_experience", []) or []:
        for pb in (exp.get("project_bullets", []) if isinstance(exp, dict) else []) or []:
            if isinstance(pb, dict) and pb.get("name"):
                names.append(pb["name"])
    if not names:
        info = app_dir / "project_info.md"
        if info.exists():
            names = re.findall(r"^# (?!Tailored)(.+)$", info.read_text(encoding="utf-8"), re.M)
    return [n.strip() for n in names]


def parse_application(app_dir: Path):
    """Return the tracker row for one application folder, or None."""
    ats = _load_yaml(app_dir / "ATS_Report.yaml")
    if not ats:
        return None
    jd = _load_yaml(app_dir / "Job_Description.yaml")

    match = DATE_IN_PATH.search(str(app_dir))
    date_str = "-".join(match.groups()) if match else ""

    company = ats.get("company") or jd.get("company") or ""
    position = ats.get("position") or jd.get("position") or ""
    if not company or not position:
        parts = re.split(r"\s[—–-]\s", app_dir.name, maxsplit=1)
        company = company or parts[0].strip()
        position = position or (parts[1].strip() if len(parts) == 2 else "")

    matrix = ats.get("ats_score_matrix") or {}
    post = ats.get("post_rewrite_ats_score") or {}
    post_matrix = post.get("ats_score_matrix") or {}
    archetype = ats.get("role_archetype") or {}
    gaps = ats.get("skill_gaps") or []

    return {
        "Date": date_str,
        "Company": str(company).strip(),
        "Position": str(position).strip(),
        "Location": str(jd.get("location") or ats.get("closest_candidate_location") or "").strip(),
        "Status": "",
        "Applied On": "",
        "Application Source": str(ats.get("application_source", "") or "").strip(),
        "Source URL": str(ats.get("source_url") or jd.get("source_url") or "").strip(),
        "ATS Pre-Score": matrix.get("total_score", "") if isinstance(matrix, dict) else "",
        "ATS Post-Score": post_matrix.get("total_score", "") if isinstance(post_matrix, dict) else "",
        "Score Delta": post.get("score_delta", "") if isinstance(post, dict) else "",
        "Score Gate": str(post.get("score_gate_verdict", "") if isinstance(post, dict) else "").strip(),
        "Role Archetype": str(archetype.get("primary", "") if isinstance(archetype, dict) else "").strip(),
        "Language": str(ats.get("language", "") or "").strip(),
        "Resume Style": str(ats.get("resume_style", "") or "").strip(),
        "ATS Vendor": str(ats.get("ats_vendor", "") or "").strip(),
        "Skill Gaps": "; ".join(str(g) for g in gaps) if isinstance(gaps, list) else str(gaps),
        "Projects Used": "; ".join(extract_projects(app_dir)),
        "Notes": "",
        "Folder Path": str(app_dir),
    }


# ─── CSV file ─────────────────────────────────────────────────────────────────

def read_rows() -> list:
    if not CSV_PATH.exists():
        return []
    with open(CSV_PATH, "r", newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def write_rows(rows: list) -> None:
    """Write sorted rows (newest first). utf-8-sig so Excel reads umlauts correctly."""
    rows = sorted(rows, key=lambda r: (r.get("Date", ""), r.get("Company", "")), reverse=True)
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(CSV_PATH, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({c: row.get(c, "") for c in CSV_COLUMNS})


def _same_application(row: dict, app: dict) -> bool:
    if row.get("Folder Path") and row["Folder Path"] == app["Folder Path"]:
        return True
    return (
        row.get("Company", "").lower() == app["Company"].lower()
        and row.get("Position", "").lower() == app["Position"].lower()
        and row.get("Date", "") == app["Date"]
    )


def _keep_manual(old: dict, new: dict) -> dict:
    for col in MANUAL_COLUMNS:
        if old.get(col):
            new[col] = old[col]
    return new


# ─── Commands ─────────────────────────────────────────────────────────────────

def cmd_append(app_dir: str, status: str, dry_run: bool) -> int:
    path = Path(app_dir).expanduser()
    if not path.exists():
        print(f"[track] Error: folder not found: {app_dir}", file=sys.stderr)
        return 1
    app = parse_application(path)
    if app is None:
        print(f"[track] Error: no readable ATS_Report.yaml in {app_dir}", file=sys.stderr)
        return 1

    rows = read_rows()
    action = "Added"
    for i, row in enumerate(rows):
        if _same_application(row, app):
            app = _keep_manual(row, app)
            rows[i] = app
            action = "Updated"
            break
    else:
        rows.append(app)

    current = (app.get("Status") or "").strip()
    if status:
        moved_on = current and current.lower() not in PIPELINE_STATUSES
        if status.lower() in PIPELINE_STATUSES and moved_on:
            pass  # keep Applied, Interview, Rejected, ...
        else:
            app["Status"] = status
            if status.lower() == "applied" and not app.get("Applied On"):
                app["Applied On"] = dt.date.today().isoformat()
    elif not current:
        app["Status"] = "In progress"

    if dry_run:
        print(f"[track] DRY RUN: would {action.lower()} {app['Company']} - {app['Position']}")
        return 0
    write_rows(rows)
    print(f"[track] {action}: {app['Company']} - {app['Position']} ({app['Status']})")
    print(f"[track] Tracker: {CSV_PATH} ({len(rows)} applications)")
    return 0


def cmd_mark(query: str, status: str, note: str, dry_run: bool) -> int:
    rows = read_rows()
    q = query.lower()
    hits = [r for r in rows if q in r.get("Company", "").lower() or q in r.get("Folder Path", "").lower()]
    if not hits:
        print(f"[track] No application matches '{query}'.", file=sys.stderr)
        return 1
    if len(hits) > 1:
        print(f"[track] '{query}' matches {len(hits)} applications; be more specific:", file=sys.stderr)
        for r in hits:
            print(f"  {r['Date']}  {r['Company']} - {r['Position']}", file=sys.stderr)
        return 1
    row = hits[0]
    row["Status"] = status
    if status.lower() == "applied" and not row.get("Applied On"):
        row["Applied On"] = dt.date.today().isoformat()
    if note:
        row["Notes"] = (row.get("Notes", "") + ("; " if row.get("Notes") else "") + note)
    if dry_run:
        print(f"[track] DRY RUN: would mark {row['Company']} as {status}")
        return 0
    write_rows(rows)
    print(f"[track] {row['Company']} - {row['Position']}: {status}")
    return 0


def cmd_rebuild(dry_run: bool) -> int:
    old_rows = read_rows()
    rows = []
    for folder in find_application_folders(APPLICATIONS_DIR):
        app = parse_application(folder)
        if app is None:
            continue
        for old in old_rows:
            if _same_application(old, app):
                app = _keep_manual(old, app)
                break
        if not app.get("Status"):
            app["Status"] = "Ready to apply" if (folder / "Cover_Letter.yaml").exists() else "In progress"
        rows.append(app)
    if dry_run:
        print(f"[track] DRY RUN: would write {len(rows)} applications to {CSV_PATH}")
        return 0
    write_rows(rows)
    print(f"[track] Rebuilt {CSV_PATH} with {len(rows)} applications")
    return 0


def cmd_list() -> int:
    rows = read_rows()
    if not rows:
        print("[track] The tracker is empty.")
        return 0
    for r in sorted(rows, key=lambda r: r.get("Date", ""), reverse=True):
        print(f"{r.get('Date', ''):10}  {r.get('Status', ''):15}  {r.get('Company', '')} - {r.get('Position', '')}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Simple job application tracker (CSV).")
    parser.add_argument("--append", metavar="DIR", help="add or update one application folder")
    parser.add_argument("--status", default="", help="status to set with --append")
    parser.add_argument("--mark", nargs=2, metavar=("COMPANY", "STATUS"), help="set the status of one application")
    parser.add_argument("--note", default="", help="add a note with --mark")
    parser.add_argument("--rebuild", action="store_true", help="rebuild the CSV from the application folders")
    parser.add_argument("--list", action="store_true", help="print the tracker")
    parser.add_argument("--dry-run", action="store_true", help="show what would change")
    args = parser.parse_args()

    if args.append:
        return cmd_append(args.append, args.status, args.dry_run)
    if args.mark:
        return cmd_mark(args.mark[0], args.mark[1], args.note, args.dry_run)
    if args.list:
        return cmd_list()
    return cmd_rebuild(args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
