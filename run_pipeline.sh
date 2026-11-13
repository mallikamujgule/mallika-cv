#!/bin/bash
###############################################################################
# run_pipeline.sh — Mallika CV pipeline (bash side)
#
# Claude (in the Claude desktop app) writes the YAML files. This script does
# everything deterministic, so no tokens are spent on it: creating the
# application folder, compiling PDFs, extracting only the ranked projects,
# checking parseability and AI watermarks, the duplicate check, tracking.
#
# Typical run (Claude calls these in order):
#
#   ./run_pipeline.sh doctor                       # one-time environment check
#   ./run_pipeline.sh fetch --url "https://..."    # JD fetch: TinyFish if installed, else Jina reader
#   ./run_pipeline.sh new "Company" "Role"         # create dated application folder
#       ... Claude writes ATS_Report.yaml, Job_Description.yaml, project_info.md ...
#   ./run_pipeline.sh stage1 --app-dir "<dir>"     # compile ATS/JD PDFs, extract projects
#   ./run_pipeline.sh check-duplicate --app-dir "<dir>"
#       ... Claude writes Resume.yaml and Cover_Letter.yaml ...
#   ./run_pipeline.sh resume --app-dir "<dir>"     # compile + audit the resume
#   ./run_pipeline.sh cover  --app-dir "<dir>"     # compile + check the cover letter
#   ./run_pipeline.sh finish --app-dir "<dir>"     # Obsidian sync (optional), tracker, summary
#
# Exit codes: 0 ok, 1 usage or missing input, 3 compile or audit failure
# (Claude fixes the YAML named in the message and re-runs the same command).
###############################################################################
set -euo pipefail

# Resolve the skill folder even when this script is reached through a symlink
# such as ~/.claude/skills/mallika-cv.
SOURCE="${BASH_SOURCE[0]}"
while [[ -L "$SOURCE" ]]; do
    DIR="$(cd -P "$(dirname "$SOURCE")" && pwd)"
    SOURCE="$(readlink "$SOURCE")"
    [[ "$SOURCE" != /* ]] && SOURCE="$DIR/$SOURCE"
done
SCRIPT_DIR="$(cd -P "$(dirname "$SOURCE")" && pwd)"
VENV_PYTHON="$SCRIPT_DIR/.venv/bin/python"
# MacTeX installs pdflatex here; it is not always on the PATH of app-launched shells.
export PATH="/Library/TeX/texbin:$HOME/.local/bin:$PATH"
LOG_DIR="${TMPDIR:-/tmp}/mallika-cv"
mkdir -p "$LOG_DIR"

# Colors
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
log()  { echo -e "${CYAN}[pipeline]${NC} $*"; }
ok()   { echo -e "${GREEN}[ok]${NC} $*"; }
warn() { echo -e "${YELLOW}[warn]${NC} $*"; }
err()  { echo -e "${RED}[error]${NC} $*" >&2; }
die()  { err "$*"; exit 1; }

[[ -x "$VENV_PYTHON" ]] || die "Python environment missing. Run: $SCRIPT_DIR/install.sh"

# Personal values come from okf/profile.yaml through config.py.
cfg() { (cd "$SCRIPT_DIR" && "$VENV_PYTHON" -c "import config; print($1)"); }
APPLICATIONS_DIR="$(cfg 'config.APPLICATIONS_DIR')"
FILE_PREFIX="$(cfg 'config.CANDIDATE_FILE_PREFIX')"
OBSIDIAN_VAULT_DIR="$(cfg 'config.OBSIDIAN_VAULT_DIR')"

# Read one top-level key from a YAML file (empty if missing).
yaml_get() {
    "$VENV_PYTHON" -c "
import sys, yaml
try:
    d = yaml.safe_load(open(sys.argv[1])) or {}
except Exception:
    d = {}
v = d.get(sys.argv[2], '')
print('' if v is None else v)
" "$1" "$2"
}

source "$SCRIPT_DIR/lib/compile.sh"

###############################################################################
# Argument parsing
###############################################################################
CMD="${1:-}"
[[ -n "$CMD" ]] || { sed -n '3,27p' "$0"; exit 1; }
shift || true

APP_DIR=""; JD_URL=""; OUT_FILE=""; OPT_FORCE=""; POSITIONAL=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        --app-dir) APP_DIR="$2"; shift 2;;
        --url)     JD_URL="$2"; shift 2;;
        --out)     OUT_FILE="$2"; shift 2;;
        --force)   OPT_FORCE="1"; shift;;
        -h|--help) sed -n '3,27p' "$0"; exit 0;;
        *)         POSITIONAL+=("$1"); shift;;
    esac
done

require_app_dir() {
    [[ -n "$APP_DIR" && -d "$APP_DIR" ]] || die "--app-dir is required and must exist."
    APP_DIR="$(cd "$APP_DIR" && pwd)"
}

###############################################################################
# doctor: environment check
###############################################################################
cmd_doctor() {
    log "Skill folder:       $SCRIPT_DIR"
    log "Applications folder: $APPLICATIONS_DIR"
    "$VENV_PYTHON" --version
    for mod in yaml reportlab pypdf tqdm; do
        if "$VENV_PYTHON" -c "import $mod" 2>/dev/null; then ok "python module: $mod"; else warn "missing python module: $mod (run install.sh)"; fi
    done
    if command -v pdflatex >/dev/null 2>&1; then
        ok "pdflatex found ($(command -v pdflatex)): LaTeX render mode available"
    else
        warn "pdflatex not found: LaTeX render mode will fall back to the regular (ReportLab) renderer. Install MacTeX or BasicTeX to enable it."
    fi
    if command -v tinyfish >/dev/null 2>&1; then ok "tinyfish CLI found: used first for job page fetches"; else log "tinyfish CLI not installed: job pages are fetched with the Jina reader"; fi
    if [[ -f "$SCRIPT_DIR/okf/fonts/lmroman10-regular.ttf" ]]; then ok "LM Roman 10 TTF fonts found (Regular renderer)"; else warn "LM Roman 10 TTF missing: Regular renderer uses Times. Run: $VENV_PYTHON $SCRIPT_DIR/install_fonts.py"; fi
    local photo; photo="$(cfg 'config.CANDIDATE_PHOTO')"
    if [[ -n "$photo" && -f "$photo" ]]; then ok "photo: $photo"; else warn "no photo configured (LaTeX resume prints without a photo)"; fi
    for f in okf/profile.yaml okf/project_catalog.yaml okf/project_catalog_condensed.yaml okf/base_files/english/resume.md okf/base_files/german/resume_de.md; do
        if [[ -f "$SCRIPT_DIR/$f" ]]; then ok "$f"; else warn "missing $f"; fi
    done
    if [[ -d "$OBSIDIAN_VAULT_DIR" ]]; then ok "Obsidian vault found: sync enabled"; else log "No Obsidian vault at $OBSIDIAN_VAULT_DIR: sync is skipped"; fi
}

###############################################################################
# fetch: JD fetch, TinyFish first (if installed), then the Jina reader
###############################################################################
cmd_fetch() {
    [[ -n "$JD_URL" ]] || die "fetch needs --url"
    local out="${OUT_FILE:-$LOG_DIR/jd-$(date +%s).txt}"
    local got=""

    # 1. TinyFish (first choice, only if its CLI is installed and signed in)
    if command -v tinyfish >/dev/null 2>&1; then
        log "Fetching $JD_URL via TinyFish"
        if tinyfish fetch content get --format markdown "$JD_URL" > "$out" 2> "$LOG_DIR/tinyfish.log" \
            && [[ $(wc -c < "$out") -gt 400 ]]; then
            got="tinyfish"
        else
            warn "TinyFish failed or returned too little text (log: $LOG_DIR/tinyfish.log). Trying Jina."
        fi
    fi

    # 2. Jina reader (no API key needed)
    if [[ -z "$got" ]]; then
        log "Fetching $JD_URL via r.jina.ai"
        local auth=()
        [[ -n "${JINA_API_KEY:-}" ]] && auth=(-H "Authorization: Bearer $JINA_API_KEY")
        if curl -fsSL --max-time 60 ${auth[@]+"${auth[@]}"} "https://r.jina.ai/$JD_URL" -o "$out" \
            && [[ $(wc -c < "$out") -gt 400 ]]; then
            got="jina"
        fi
    fi

    [[ -n "$got" ]] || die "Could not fetch the posting. Ask Mallika to paste the job description text."
    ok "JD saved via $got: $out ($(wc -c < "$out") bytes)"
    echo "JD_FILE:$out"
}

###############################################################################
# new: create the dated application folder
###############################################################################
cmd_new() {
    local company="${POSITIONAL[0]:-}" role="${POSITIONAL[1]:-}"
    [[ -n "$company" && -n "$role" ]] || die "usage: run_pipeline.sh new \"Company\" \"Role\""
    local safe_name
    safe_name="$(printf '%s — %s' "$company" "$role" | tr '/:\\' '---' | cut -c1-150)"
    local dir="$APPLICATIONS_DIR/$(date +%Y/%m/%d)/$safe_name"
    mkdir -p "$dir"
    ok "Application folder created"
    echo "APP_DIR:$dir"
}

###############################################################################
# stage1: compile Step 1 PDFs, extract ranked projects, report gaps and score
###############################################################################
cmd_stage1() {
    require_app_dir
    [[ -f "$APP_DIR/ATS_Report.yaml" ]] || die "ATS_Report.yaml missing in $APP_DIR (Step 1 not finished)."
    [[ -f "$APP_DIR/Job_Description.yaml" ]] || die "Job_Description.yaml missing in $APP_DIR."

    log "Compiling Step 1 PDFs..."
    compile_step1_pdfs "$APP_DIR"

    log "Extracting ranked projects..."
    if [[ -f "$APP_DIR/project_info.md" ]]; then
        "$VENV_PYTHON" "$SCRIPT_DIR/extract_projects.py" \
            --from-project-info "$APP_DIR/project_info.md" \
            --catalog "$SCRIPT_DIR/okf/project_catalog.yaml" \
            --output "$APP_DIR/selected_projects.yaml" 2>&1 \
            || warn "extract_projects.py failed: Step 2 should read okf/project_catalog.yaml directly."
    else
        warn "project_info.md missing: Step 2 should read okf/project_catalog.yaml directly."
    fi

    local gaps score
    gaps="$("$VENV_PYTHON" -c "
import sys, yaml
d = yaml.safe_load(open(sys.argv[1])) or {}
g = d.get('skill_gaps', [])
print(', '.join(g) if g else '(none)')
" "$APP_DIR/ATS_Report.yaml" 2>/dev/null || echo "(unable to read)")"
    score="$("$VENV_PYTHON" -c "
import sys, yaml
d = yaml.safe_load(open(sys.argv[1])) or {}
print(d.get('ats_score_matrix', {}).get('total_score', 0))
" "$APP_DIR/ATS_Report.yaml" 2>/dev/null || echo 0)"

    echo "APP_DIR:$APP_DIR"
    echo "SKILL_GAPS:$gaps"
    echo "ATS_SCORE:$score"
    ok "Stage 1 complete. Ask Mallika how to handle skill gaps, then write Resume.yaml and Cover_Letter.yaml."
}

###############################################################################
# check-duplicate
###############################################################################
cmd_check_duplicate() {
    require_app_dir
    set +e
    local out; out="$("$VENV_PYTHON" "$SCRIPT_DIR/check_duplicate_application.py" "$APP_DIR" 2>&1)"
    local code=$?
    set -e
    if [[ $code -ne 0 && -z "$OPT_FORCE" ]]; then
        warn "Possible duplicate application:"
        echo "$out"
        echo "DUPLICATE:yes"
        echo "Ask Mallika whether to proceed. Re-run with --force to continue anyway."
        exit 3
    elif [[ $code -ne 0 ]]; then
        warn "Duplicate detected but --force set, continuing."
    else
        ok "No prior application for this company and role."
    fi
    echo "DUPLICATE:no"
}

###############################################################################
# resume / cover / finish
###############################################################################
cmd_resume() {
    require_app_dir
    [[ -f "$APP_DIR/Resume.yaml" ]] || die "Resume.yaml missing in $APP_DIR."
    local language render_mode
    language="$(yaml_get "$APP_DIR/Resume.yaml" language)"; language="${language:-English}"
    render_mode="$(yaml_get "$APP_DIR/Resume.yaml" render_mode)"; render_mode="${render_mode:-latex}"

    if compile_resume "$APP_DIR" "$language" "$render_mode"; then
        [[ -f "$APP_DIR/$RESUME_PDF" ]] && generate_layout_audit "$APP_DIR" "$APP_DIR/$RESUME_PDF"
        ok "Resume ready: $APP_DIR/$RESUME_PDF"
        echo "RESUME_PDF:$APP_DIR/$RESUME_PDF"
        # Every number must trace to Mallika's sources; flag bullets without a number.
        if ! "$VENV_PYTHON" "$SCRIPT_DIR/check_resume_facts.py" "$APP_DIR/Resume.yaml"; then
            warn "Untraceable numbers found: fix or remove them in Resume.yaml, then re-run resume."
            exit 3
        fi
    else
        err "Resume step failed: $COMPILE_ERROR"
        echo "--- log (first 30 lines) ---"
        echo "$COMPILE_LOG" | head -30
        echo "FIX: edit $APP_DIR/Resume.yaml to resolve the error above, then re-run: run_pipeline.sh resume --app-dir \"$APP_DIR\""
        exit 3
    fi
}

cmd_cover() {
    require_app_dir
    [[ -f "$APP_DIR/Cover_Letter.yaml" ]] || die "Cover_Letter.yaml missing in $APP_DIR."
    local language
    language="$(yaml_get "$APP_DIR/Cover_Letter.yaml" language)"; language="${language:-English}"
    if compile_cover_letter "$APP_DIR" "$language"; then
        echo "COVER_LETTER_PDF:$APP_DIR/$CL_PDF"
    else
        err "Cover letter compile failed. Log: $LOG_DIR/cl-compile.log"
        tail -20 "$LOG_DIR/cl-compile.log" 2>/dev/null || true
        exit 3
    fi
}

cmd_finish() {
    require_app_dir
    if [[ -d "$OBSIDIAN_VAULT_DIR" && -f "$APP_DIR/Cover_Letter.yaml" ]]; then
        log "Obsidian sync..."
        set +e
        "$VENV_PYTHON" "$SCRIPT_DIR/sync_to_obsidian.py" "$APP_DIR" 2>&1 \
            || warn "Obsidian sync failed (non-critical)."
        set -e
    else
        log "Obsidian sync skipped (no vault at $OBSIDIAN_VAULT_DIR)."
    fi

    log "Applications tracker..."
    set +e
    "$VENV_PYTHON" "$SCRIPT_DIR/track_applications.py" --append "$APP_DIR" 2>&1 \
        || warn "Tracker append failed (non-critical)."
    set -e

    local company position delta
    company="$(yaml_get "$APP_DIR/ATS_Report.yaml" company)"
    position="$(yaml_get "$APP_DIR/ATS_Report.yaml" position)"
    delta="$("$VENV_PYTHON" -c "
import sys, yaml
d = yaml.safe_load(open(sys.argv[1])) or {}
print(d.get('post_rewrite_ats_score', {}).get('score_delta', 'N/A'))
" "$APP_DIR/ATS_Report.yaml" 2>/dev/null || echo N/A)"

    echo ""
    echo "Company:   ${company:-Unknown}"
    echo "Position:  ${position:-Unknown}"
    echo "Folder:    $APP_DIR"
    echo "ATS delta: $delta"
    echo "Files:"
    ls -1 "$APP_DIR" | sed 's/^/  /'
    rm -f "$LOG_DIR"/compile.log "$LOG_DIR"/parse.log "$LOG_DIR"/watermark.log \
          "$LOG_DIR"/cl-compile.log "$LOG_DIR"/cl-watermark.log
}

case "$CMD" in
    doctor)           cmd_doctor;;
    fetch)            cmd_fetch;;
    new)              cmd_new;;
    stage1)           cmd_stage1;;
    check-duplicate)  cmd_check_duplicate;;
    resume)           cmd_resume;;
    cover)            cmd_cover;;
    finish)           cmd_finish;;
    *)                die "Unknown command: $CMD (see header of $0)";;
esac
