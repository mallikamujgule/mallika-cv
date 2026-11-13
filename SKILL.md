---
name: mallika-cv
description: >-
  Mallika Mujgule's job-application pipeline for product and UX design roles.
  Use when Mallika says "mallika-cv" (optionally with a job URL, pasted job
  description or file path) or "mallika-cv refresh". Tailors her resume and cover
  letter to one job: ATS analysis and JD archive, project ranking from her
  catalog, resume rewrite with parseability and watermark checks, cover letter,
  and application tracking. Do not trigger on generic words like "resume",
  "cover letter" or "apply".
---

# mallika-cv

You are running Mallika Mujgule's application pipeline. The skill lives in
`~/.claude/skills/mallika-cv` (a link to her repo). All paths below are relative
to that folder. Her details come from `okf/profile.yaml`; never hardcode them.

**Division of labor:** you write YAML and Markdown (judgment work). The bash
script `./run_pipeline.sh` does everything deterministic (folders, PDFs,
parseability and watermark checks, tracking). Do not compile PDFs yourself and
do not paste large files into the chat. This keeps token use low.

Run every command from the skill folder:

```bash
cd ~/.claude/skills/mallika-cv
```

## Rules (non-negotiable)

1. **No fabrication.** Projects, roles, dates, metrics, tools and links come only
   from `okf/project_catalog.yaml` and `okf/base_files/`. Never invent, split or
   merge a project. Metrics are quoted from the catalog, never estimated.
   Projected figures in the catalog (for example "25% projected reduction")
   stay marked as projected.
2. **Write only inside the application folder** (plus `okf/` when Mallika asks
   to update her source files). Never edit Python, shell or renderer files
   during a run.
3. **YAML safety.** Quote any string containing `:`, `#`, `>`, `|`, braces or
   brackets. Re-read the file once after writing it.
4. **Writing style.** Active voice, no adverbs ending in -ly, no em dashes, no
   throat-clearing, no filler like "passionate" or "thrilled". If the
   `stop-slop` skill is installed, apply it to the summary, bullets and cover
   letter.
5. **No watermark tampering.** `check_watermarks.py` is a verification step.
   Report its result honestly; never claim output is "human-written".
6. **Confirm before sending anything.** This pipeline only produces files.
   It never submits an application or sends email.

## Trigger: "mallika-cv" with a job

### Step 0: get the job description

- Pasted text or a file path: use it.
- A URL: open it with the built-in browser or WebFetch and copy the posting text
  (title, company, location, requirements, responsibilities, stack). Skip
  cookie banners and navigation. If that fails, run
  `./run_pipeline.sh fetch --url "<URL>"` (Jina reader, prints `JD_FILE:`).
  If that also fails, ask Mallika to paste the posting. Never use a login page,
  an error page or a different posting.

Save the clean text to a scratch file and keep the `source_url`.

### Ask Mallika four questions in one message (use AskUserQuestion)

| # | Setting | Options |
|---|---|---|
| 1 | Resume type | `LaTeX` (photo, dense one page) or `Regular` (clean ReportLab PDF) |
| 2 | Layout | `Standard` (Summary, Skills, Projects, Experience, Education, Languages) or `Experience-led` (Summary, Experience with projects folded in, Education, Skills, Languages) |
| 3 | Application source | `Cold Apply`, `Referral`, `LinkedIn Connection`, `Direct` (ask for the contact name and role if Referral or LinkedIn Connection) |
| 4 | Language | `English` (German is only available once a German base resume exists in `okf/base_files/german/`) |

Mapping to files: `LaTeX` sets `render_mode: latex`, `Regular` sets
`render_mode: reportfallback`. `Standard` sets `resume_style: us`,
`Experience-led` sets `resume_style: german`. If `./run_pipeline.sh doctor`
reports no `pdflatex`, tell Mallika LaTeX will fall back to the Regular
renderer and continue.

### Step 1: ATS analysis, JD archive, project ranking

1. Read `01_ats_and_jd_archival.md` and follow it.
2. Create the folder: `./run_pipeline.sh new "<Company>" "<Role>"` (prints `APP_DIR:`).
3. Write `ATS_Report.yaml`, `Job_Description.yaml` and `project_info.md` into it.
4. Run `./run_pipeline.sh stage1 --app-dir "<APP_DIR>"`. It compiles the two PDFs,
   extracts the ranked projects into `selected_projects.yaml`, and prints
   `SKILL_GAPS:` and `ATS_SCORE:`.

### Between steps: two quick decisions

- `./run_pipeline.sh check-duplicate --app-dir "<APP_DIR>"`. Exit code 3 means a
  prior application exists: show Mallika the output and ask whether to proceed
  (then re-run with `--force`).
- Show the skill gaps and ask: `Add all`, `No stuffing` (default, only real
  skills), or `Selective` (she names the skills). Store the answer as
  `keyword_stuffing` and `user_directed_skills` in `Resume.yaml`.

### Step 2: resume

Read `02_resume_and_visual_audit.md`, write `Resume.yaml`, then run
`./run_pipeline.sh resume --app-dir "<APP_DIR>"`. Exit code 3 prints the error
and a `FIX:` line: edit `Resume.yaml` accordingly and run the same command
again, at most twice. Then add `post_rewrite_ats_score` to `ATS_Report.yaml`.

### Step 3: cover letter

Read `03_cover_letter.md`, write `Cover_Letter.yaml`, then run
`./run_pipeline.sh cover --app-dir "<APP_DIR>"`.

### Finish

Run `./run_pipeline.sh finish --app-dir "<APP_DIR>"` (Obsidian sync if a vault
exists, tracker CSV, summary). Then work through `99_completion_checklist.md`
and report to Mallika: folder path, ATS score before and after, any failed
check, and anything you could not verify.

## Trigger: "mallika-cv refresh"

Re-read this file, `okf/profile.yaml`, and the step docs. Say what changed.

## Other commands

| Need | Command |
|---|---|
| Check the setup | `./run_pipeline.sh doctor` |
| Rebuild the tracker | `.venv/bin/python track_applications.py --rebuild` |
| Regenerate the condensed catalog after editing `okf/project_catalog.yaml` | `.venv/bin/python extract_projects.py --condensed --catalog okf/project_catalog.yaml --output okf/project_catalog_condensed.yaml` |
| Record an outcome | `.venv/bin/python track_outcomes.py --help` |

## Source files Mallika maintains (`okf/`)

- `profile.yaml`: name, contact, photo, signature, file prefix.
- `project_catalog.yaml`: the only source of projects and metrics.
- `base_files/english/resume.md`: the base resume text.
- `templates/Resume_latex.yaml`, `templates/Resume_regular.yaml`: example
  `Resume.yaml` files for the two resume types.
