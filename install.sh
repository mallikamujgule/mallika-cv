#!/bin/bash
###############################################################################
# install.sh — install the mallika-cv skill for the Claude desktop app (macOS)
#
#   ./install.sh            install or repair
#   ./install.sh --remove   remove the skill link (keeps this folder)
#
# What it does:
#   1. Creates .venv here with Python 3.10+ (uses uv if installed, otherwise
#      python3) and installs requirements.txt.
#   2. Links this folder to ~/.claude/skills/mallika-cv so Claude finds it.
#   3. Runs ./run_pipeline.sh doctor.
###############################################################################
set -euo pipefail

SOURCE="${BASH_SOURCE[0]}"
while [[ -L "$SOURCE" ]]; do
    DIR="$(cd -P "$(dirname "$SOURCE")" && pwd)"
    SOURCE="$(readlink "$SOURCE")"
    [[ "$SOURCE" != /* ]] && SOURCE="$DIR/$SOURCE"
done
HERE="$(cd -P "$(dirname "$SOURCE")" && pwd)"
SKILL_NAME="mallika-cv"
SKILLS_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills"
LINK="$SKILLS_DIR/$SKILL_NAME"
export PATH="$HOME/.local/bin:$PATH"

if [[ "${1:-}" == "--remove" ]]; then
    if [[ -L "$LINK" ]]; then rm "$LINK"; echo "Removed $LINK"; else echo "Nothing to remove at $LINK"; fi
    exit 0
fi

echo "==> Python environment"
if [[ -x "$HERE/.venv/bin/python" ]] && "$HERE/.venv/bin/python" -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)' 2>/dev/null; then
    echo "Existing .venv is Python 3.10+, keeping it."
else
    rm -rf "$HERE/.venv"
    if command -v uv >/dev/null 2>&1; then
        uv venv --python 3.12 "$HERE/.venv"
    else
        PY=""
        for c in python3.13 python3.12 python3.11 python3.10 python3; do
            if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)' 2>/dev/null; then PY="$c"; break; fi
        done
        if [[ -z "$PY" ]]; then
            echo "Python 3.10+ not found. Install uv first, then re-run:"
            echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
            exit 1
        fi
        "$PY" -m venv "$HERE/.venv"
    fi
fi
if command -v uv >/dev/null 2>&1; then
    uv pip install -q --python "$HERE/.venv/bin/python" -r "$HERE/requirements.txt"
else
    "$HERE/.venv/bin/python" -m pip install -q --upgrade pip
    "$HERE/.venv/bin/python" -m pip install -q -r "$HERE/requirements.txt"
fi
echo "Installed: $("$HERE/.venv/bin/python" --version)"

echo "==> Fonts (Latin Modern Roman 10 for the Regular renderer)"
"$HERE/.venv/bin/python" "$HERE/install_fonts.py" || echo "Skipped: install MacTeX or BasicTeX, then run install_fonts.py"

echo "==> Linking skill"
mkdir -p "$SKILLS_DIR"
if [[ -e "$LINK" && ! -L "$LINK" ]]; then
    echo "$LINK already exists and is not a link. Move it away and re-run."
    exit 1
fi
ln -sfn "$HERE" "$LINK"
chmod +x "$HERE/run_pipeline.sh" "$HERE/install.sh"
echo "$LINK -> $HERE"

echo "==> Environment check"
"$HERE/run_pipeline.sh" doctor || true

echo ""
echo "Done. Open a new Claude session and say: mallika-cv <job URL or pasted JD>"
