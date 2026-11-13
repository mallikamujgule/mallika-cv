# mallika-cv

Mallika Mujgule's application pipeline for product and UX design roles. It runs
as a skill inside the **Claude desktop app** on macOS. No Claude CLI, no other
agent harness and no API key are needed.

Say `mallika-cv` plus a job URL or pasted job description. Claude tailors her
resume and cover letter to that job, and a bash script does the rest.

## Install (macOS)

```bash
cd ~/Documents/llm-cv
./install.sh
```

This creates `.venv` (Python 3.12 through `uv`, or any Python 3.10+), installs
`requirements.txt`, links the folder to `~/.claude/skills/mallika-cv` and runs a
setup check. Open a new Claude session afterwards. To remove the link:
`./install.sh --remove`.

`uv` comes from `curl -LsSf https://astral.sh/uv/install.sh | sh`. For the LaTeX
resume type, also install MacTeX or BasicTeX (`pdflatex`). Without it the LaTeX
type falls back to the Regular renderer and the pipeline says so.

## How a run works

| Who | What |
|---|---|
| Claude | Gets the job description, asks four questions (resume type, layout, source, language), writes `ATS_Report.yaml`, `Job_Description.yaml`, `project_info.md`, `Resume.yaml`, `Cover_Letter.yaml` |
| `run_pipeline.sh` | Creates the dated folder, compiles PDFs, extracts only the ranked projects, runs the parseability and AI-watermark checks, the duplicate check, the tracker and optional Obsidian sync |

Keeping the deterministic work in bash is what saves tokens: Claude never
compiles, never re-reads the full catalog (it reads the condensed one), and
never pastes PDFs back.

Bash commands: `doctor`, `fetch`, `new`, `stage1`, `check-duplicate`, `resume`,
`cover`, `finish`. See the header of `run_pipeline.sh`.

## Resume types

- **LaTeX:** dense one-page PDF with your photo, `okf/templates/Resume_latex.yaml`.
- **Regular:** clean ReportLab PDF without a photo, `okf/templates/Resume_regular.yaml`.

Layouts: **Standard** (Summary, Skills, Projects, Experience, Education,
Languages) or **Experience-led** (Summary, Experience with projects folded in,
Education, Skills, Languages).

## Your files (`okf/`)

| File | Purpose |
|---|---|
| `profile.yaml` | Name, contact, photo, signature, output file prefix. Change details here, not in code. |
| `project_catalog.yaml` | The only source of projects and metrics. Edit, then regenerate the condensed copy (see `SKILL.md`). |
| `project_catalog_condensed.yaml` | Generated, no bullets, used for ranking. |
| `base_files/english/resume.md`, `base_files/german/resume_de.md` | Base resume text in English and German. |
| `templates/` | Example `Resume.yaml` files for both types in English and German, and English and German cover letter templates. |
| `skill_mappings.yaml`, `project_mappings.yaml` | Name normalization for Obsidian sync. |

## Where files go

- Applications: `~/Documents/Mallika Applications/YYYY/MM/DD/Company — Role/`
  (override with `LLM_CV_APPLICATIONS_DIR`).
- Tracker CSV: `~/Documents/mallika_applications_tracker.csv` (`LLM_CV_TRACKER_CSV`).
- Obsidian sync runs only if `~/Documents/Obsidian Vault` exists (`LLM_CV_OBSIDIAN_VAULT`).

## Known limits

- German text is machine-translated from your CV; have a native speaker proofread it, since your German is A2.
- The AI-watermark check reports marks; it does not prove how text was written.
  Follow the disclosure rules of employers and schools.
