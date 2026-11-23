# Prompt: resume layout fix (main CV, Synthesia, ClickHouse/Langfuse)

Apply only the changes listed here. Make no other edits.

## Required section order
1. Summary
2. Professional experience
3. Education
4. Technical skills
5. Spoken languages (below the skills)

## Remove
- The Projects section. No `projects:` key and no project entries anywhere in the resume.

## Do not change
- Summary text (it keeps "Available immediately.").
- Experience entries, dates, titles, locations and bullets.
- Education entries, including CGPA.
- Skills categories and skills.
- Languages.
- Contact block, photo, accent colour, "Available immediately" line.
- Cover letters, ATS reports and job description files.
- Do not reword, add or remove any claim, number or skill. Do not tailor bullets.

## How
- Use the Experience-led layout (`resume_style: german`, `render_mode: latex`), which renders exactly the order above.
- Source of the content: `okf/templates/Resume_latex.yaml`, copied unchanged.
- Rebuild three resumes with `./run_pipeline.sh resume --app-dir <dir>`:
  1. Main CV (scratchpad `maincv`)
  2. Synthesia application folder
  3. ClickHouse (Langfuse) application folder
- Check each result: one page, parseability Pass, section order as above, no Projects heading.
