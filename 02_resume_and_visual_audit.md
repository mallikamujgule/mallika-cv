# Step 2: Resume rewrite and audit

Follow SKILL.md rules. Write only `Resume.yaml` and the `post_rewrite_ats_score`
block in `ATS_Report.yaml`. The bash script compiles and audits the PDF.

## Inputs
- `ATS_Report.yaml`: `render_mode`, `resume_style`, `language`, `skill_gaps`,
  `improvement_blueprint`, `role_archetype`, `closest_candidate_location`.
- `selected_projects.yaml` (full bullets for the ranked projects only). If it is
  missing, read `okf/project_catalog.yaml`.
- `project_info.md`, `Job_Description.yaml` (do not re-read the raw JD).
- Base resume: `okf/base_files/english/resume.md`, or `okf/base_files/german/resume_de.md` when
  `language` is German.
- Example output shape: `okf/templates/Resume_latex.yaml` (render_mode latex,
  resume_style german) and `okf/templates/Resume_regular.yaml` (render_mode
  reportfallback, resume_style us). German: `Resume_latex_de.yaml` and
  `Resume_regular_de.yaml`. Copy the matching template and tailor it.
- Contact details: `okf/profile.yaml`.

## Rewrite rules

- `contact_info`: name, phone, email, linkedin, portfolio and photo from
  `okf/profile.yaml`; `location` from `closest_candidate_location`. Set `photo`
  to the profile photo for `latex` and to `null` for `reportfallback`. Add
  `visa` and `availability` only if `profile.yaml` has values.
- **Roles and dates are immutable.** Copy company, title, dates and city from
  the base resume exactly. Client work (Thermax EDGE at Onething Design, ICICI
  Bank at Sparklin) stays attributed to the employer, with the client named.
- **Summary:** 2 lines, 200 characters or fewer. Say who she is, what she
  designs and the outcome. No tool lists.
- **Technical skills:** 4 to 6 categories of 5 to 7 skills, ordered by this job's
  requirements first, then core strengths. Only skills in the base resume or
  catalog, plus gap skills allowed by `keyword_stuffing`:
  - `Add all`: add every `skill_gaps` item (her explicit instruction).
  - `Selective`: add `user_directed_skills`.
  - `No stuffing` (default): add nothing she has not used.
- **Projects** (layout `us`): top-level `projects:` list, 3 to 5 entries, each
  with `name` (exact catalog title, shortened only by dropping a subtitle),
  `repo_url` (verbatim from the catalog), `tools` (3 to 5 JD-relevant), and
  exactly 3 `bullets` of 60 to 80 characters. Each bullet carries a number from
  the catalog `key_metrics`. Combined project text stays at 300 characters or
  fewer. If a catalog entry has no number for a bullet, pick another bullet.
- **Experience-led layout** (`german`): no top-level `projects:`. Case studies
  appear as bullets inside the matching `professional_experience` entry.
- **Experience bullets: tailor every run, never copy the base resume.** Rewrite
  each bullet for this job (do not just trim it):
  1. **Mirror the JD.** Weave in the job's own phrases (for example "data-rich",
     "end-to-end", "cross-functional", "evidence", "complex workflows",
     "design system") wherever the work truly matches. Reorder bullets so the
     most relevant one comes first in each role. This applies at every score,
     not only below 85.
  2. **Quantify each action.** Start with the verb, then the action, then a
     number taken from the base resume or catalog (counts of screens, users,
     issues, flows, projects; percentages; multipliers). Name countable items
     only when they are really listed in the sources (for example 3 named
     flows). Keep "projected" or "projecting" on projected figures.
  3. **Never invent a number.** If the sources hold no figure for a bullet,
     leave it without one and, after the resume compiles, tell Mallika which
     bullets have none and ask whether she has a real figure.
  4. **Limits:** 105 characters or fewer, one line each, outcome first.
     4 bullets for the current or most relevant role, 2 to 4 for older roles.
  5. `./run_pipeline.sh resume` runs `check_resume_facts.py`: it fails on any
     number that is not in `okf/` and lists bullets without a number.
- **Education, languages:** from the base resume exactly.
- **Layout fit:** the result must fill one A4 page. Add skill rows or a further
  catalog project if the page is short; trim if it spills. Never pad prose.
- **Language:** `English` or `German`, as Mallika chose; set `language` accordingly.
  German resumes: write in German from `resume_de.md`; summary 170 characters or
  fewer and project text 280 characters or fewer; dates as `MM/YYYY - heute`;
  `location` as `Berlin, Deutschland`; keep role titles, company names, tool names and
  degree names in their original form; use real umlauts and ß. Add a note for
  Mallika that her German is A2, so a native speaker should proofread before sending.
- **Score-Boost:** when `ats_score_matrix.total_score` is below 85, apply
  `prompts/score_boost.md`.

## After writing
Run `./run_pipeline.sh resume --app-dir "<APP_DIR>"`. It generates the PDF,
the parseability audit (keyword recovery, section headers, contact fields,
character limits), the AI watermark check and `Layout_Audit_Report.yaml`. On exit
code 3, fix `Resume.yaml` as the printed message says and re-run (twice at most).
Keyword misses are YAML wording problems: remove special characters or split
strings. Never edit fonts or renderer code.

Validate project names before compiling:
```bash
cd ~/.claude/skills/mallika-cv && .venv/bin/python -c "
import sys, yaml
catalog = {p['title'] for p in yaml.safe_load(open('okf/project_catalog.yaml'))['projects']}
r = yaml.safe_load(open(sys.argv[1]))
names = [p['name'] for p in r.get('projects', [])]
for e in r.get('professional_experience', []):
    names += [pb['name'] for pb in e.get('project_bullets', [])]
for n in names: print(('OK ' if n in catalog else 'NOT IN CATALOG ') + n)
" "<APP_DIR>/Resume.yaml"
```

## Post-rewrite ATS score
Re-score the final resume with the same four categories and an explicit list of
matched and unmatched JD terms inside each `evaluation_criteria`. Add to
`ATS_Report.yaml` (keep the pre-rewrite block):

```yaml
post_rewrite_ats_score:
  ats_score_matrix:
    keywords_and_terminology: { max_score: 25, current_score: 0, evaluation_criteria: "" }
    experience_relevance: { max_score: 25, current_score: 0, evaluation_criteria: "" }
    technical_skills: { max_score: 25, current_score: 0, evaluation_criteria: "" }
    soft_skills_and_language: { max_score: 25, current_score: 0, evaluation_criteria: "" }
    total_score: 0
  score_delta: 0
  formatting_quality: { verdict: "Excellent", notes: "", suggestions: [] }
  score_gate_verdict: "PROCEED"
  remaining_gaps: []
```

Do not inflate. Points count only for terms present in `Resume.yaml`.
Recompile `ATS_Report.pdf` by running `./run_pipeline.sh resume` once more, or
let `finish` pick it up.

## `Resume.yaml` shape
```yaml
type: resume
language: "English"
render_mode: "latex"            # latex | reportfallback
resume_style: "us"              # us | german
resume_variation: "Balanced"   # Balanced | Project-Heavy | Skills-Heavy
keyword_stuffing: false
user_directed_skills: []
contact_info: { name: "", location: "", phone: "", email: "", linkedin: "", portfolio: "", photo: null }
summary: ""
technical_skills: [{ category: "", skills: [""] }]
projects: [{ name: "", repo_url: "", tools: [""], bullets: ["", "", ""] }]   # layout us only
professional_experience: [{ company: "", location: "", date: "", title: "", bullets: [""] }]
education: [{ degree: "", university: "", date: "" }]
languages: ["English (C2)"]
```

Next: read `03_cover_letter.md`.
