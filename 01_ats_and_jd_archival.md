# Step 1: ATS check, JD archive, project ranking

Follow SKILL.md rules. Write only into the application folder:
`ATS_Report.yaml`, `Job_Description.yaml`, `project_info.md`. The bash script
compiles the PDFs.

## Inputs

- The job description text (from Step 0) and the `source_url` if there is one.
- First-action answers: render type, layout, application source, language,
  weak-tie contact.
- Base resume: `okf/base_files/english/resume.md` (German: `okf/base_files/german/resume_de.md`
  when it exists).
- `okf/project_catalog_condensed.yaml` (no bullets, used for ranking).
- `okf/profile.yaml` for her name and location.

## Do this

### 1. Persist the first-action answers
Write `render_mode`, `resume_style`, `language`, `application_source` and
`weak_tie_contact` as top-level keys in `ATS_Report.yaml`.

### 2. Vendor and source
Infer the ATS vendor from the URL or text: `myworkdayjobs.com` Workday,
`personio.de` Personio, `successfactors` SAP SuccessFactors, `greenhouse.io`
Greenhouse, `lever.co` Lever, `taleo.net` Taleo, `join.com` JOIN, `softgarden`
Softgarden. Default `Unknown`. For a Cold Apply to a known vendor, suggest she
check her network for a referral.

### 3. Role archetype
Classify the job into one primary archetype with a one-sentence rationale, plus a
secondary one only if the job spans two. Use the catalog archetypes:
`Product Design`, `UX Design`, `UX Research`, `AI-Enabled Product Design`,
`Fintech Design`, `Architecture`. If the role is none of these, name the closest
real match; do not invent skills to fit.

### 4. ATS score (informational, never blocks)
Four categories of 25 points each, 100 total: `keywords_and_terminology`,
`experience_relevance`, `technical_skills`, `soft_skills_and_language`. Score
against explicit lists of JD terms, not impressions. Emit a separate
`formatting_quality` verdict (`Excellent`, `Good`, `Average`, `Bad`). Verdict
`PROCEED` at 85 or above, otherwise `REVIEW` with `remedy_suggestions`.

### 5. Skill gaps
`skill_gaps` = skills the JD explicitly requires minus skills in the base resume
and the matched projects. Every entry must be traceable to JD text.

### 6. Improvement blueprint
- `bullet_point_density_audit`: bullets without a number.
- `project_swap_directive`: catalog projects to drop or add, with reasons.
- `keyword_inventory`: JD keywords missing from the resume (hard skills,
  methodologies, domain terms).
- `technical_skills_tuning`: skills to add (only ones she has used) and remove.
- `quantified_outcomes`: suggested rewrites using catalog metrics only.

### 7. JD archive
Strip tracking text. Extract the job location into `location`. Structure into
the sections in the schema below.

### 8. Location
Her home base is Berlin. Run
`cd ~/.claude/skills/mallika-cv && .venv/bin/python -c "from config import nearest_candidate_city; print(nearest_candidate_city('<job location>'))"`
and store the result as `closest_candidate_location`.

### 9. Rank projects
Read `okf/project_catalog_condensed.yaml`. Rank the top entries for this job
(she has few projects, so rank every entry that fits; at least 3 if available)
by tool and method overlap, transferable skills, business-problem match,
archetype fit, seniority and reframing potential. Select only catalog entries,
matched by exact `title`. `repo_url` is copied exactly from the catalog.

Write `project_info.md`:

```markdown
# Tailored Project Portfolio

# [Exact catalog title]
[description]
Problem: [business_problem]
Metrics: [key_metrics, verbatim]
Tech: [technologies]
Archetypes: [archetypes]
Repo: [repo_url]
[first 2 catalog bullets]
<!-- LLM Rank: [rank], Reason: [one sentence] -->
```

### 10. Validate
```bash
cd ~/.claude/skills/mallika-cv && .venv/bin/python -c "
import re, yaml
catalog = {p['title'] for p in yaml.safe_load(open('okf/project_catalog.yaml'))['projects']}
import sys
text = open(sys.argv[1]).read()
for t in re.findall(r'^# (?!Tailored)(.+)$', text, re.M):
    print(('OK ' if t.strip() in catalog else 'NOT IN CATALOG ') + t)
" "<APP_DIR>/project_info.md"
```
Fix any line that says NOT IN CATALOG before moving on.

## Schemas

### `ATS_Report.yaml`
```yaml
type: ats_report
company: "[Company]"
position: "[Job title]"
render_mode: "latex"          # latex | reportfallback
resume_style: "us"            # us | german
language: "English"
closest_candidate_location: "Berlin, Germany"
ats_vendor: "Unknown"
application_source: "Cold Apply"
weak_tie_contact: null
role_archetype:
  primary: "[Archetype]"
  secondary: "[omit if single-domain]"
  archetype_rationale: "[One sentence]"
ats_score_matrix:
  keywords_and_terminology: { max_score: 25, current_score: 0, evaluation_criteria: "..." }
  experience_relevance: { max_score: 25, current_score: 0, evaluation_criteria: "..." }
  technical_skills: { max_score: 25, current_score: 0, evaluation_criteria: "..." }
  soft_skills_and_language: { max_score: 25, current_score: 0, evaluation_criteria: "..." }
  total_score: 0
formatting_quality: { verdict: "Excellent", notes: "", suggestions: [] }
core_score_detractors: []
skill_gaps: []
placement_breakdown: { keywords: [] }
improvement_blueprint:
  target_language_confirmation: "English"
  bullet_point_density_audit: []
  project_swap_directive: { remove_projects: [], add_projects: [], volume_constraint_check: "" }
  keyword_inventory: { hard_skills: [], methodologies: [], domain_terms: [] }
  technical_skills_tuning: { add: [], remove: [] }
  quantified_outcomes: []
  ats_threshold_calibration: { meets_target: false, score_gate_verdict: "REVIEW", remedy_suggestions: [] }
# post_rewrite_ats_score is added in Step 2
```

### `Job_Description.yaml`
```yaml
type: job_description
company: "[Company]"
position: "[Job title]"
location: "[Job location]"
source_url: "[omit if pasted]"
sections:
  - title: "Core Role Overview & Context"
    content: "[Overview paragraph]"
  - title: "Target Profile Requirements"
    bullets: ["[Requirement]"]
  - title: "Primary Responsibilities"
    bullets: ["[Responsibility]"]
  - title: "Tools & Methods"
    bullets: ["[Tool or method]"]
```

Next: run `./run_pipeline.sh stage1`, then read `02_resume_and_visual_audit.md`.
