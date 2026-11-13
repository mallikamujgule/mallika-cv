# Completion checklist

Check each item against the files in the application folder. Report failures and
anything you could not verify; do not mark a box you did not check.

- [ ] `ATS_Report.yaml` has the first-action keys, `closest_candidate_location`, the pre-rewrite matrix and `post_rewrite_ats_score`
- [ ] `ATS_Report.pdf` and `Job_Description.pdf` exist
- [ ] `project_info.md` and `selected_projects.yaml` exist and every title matches `okf/project_catalog.yaml`
- [ ] `Resume.yaml` and `MALLIKA_MUJGULE_Resume.pdf` exist (name prefix comes from `okf/profile.yaml`)
- [ ] The resume is exactly one page and filled to the bottom margin
- [ ] `Parseability_Report.yaml` overall status is PASS
- [ ] `check_watermarks.py` exited 0 for the resume and the cover letter (no warning in the run output)
- [ ] `Cover_Letter.yaml` and the cover letter PDF exist and fit one page
- [ ] For German: output files are `..._Lebenslauf.pdf` and `..._Anschreiben.pdf`, text uses real umlauts, and Mallika was reminded to have a native speaker proofread (her German is A2)
- [ ] Summary is 2 lines, 200 characters or fewer; project text is 300 characters or fewer; experience bullets are 105 characters or fewer
- [ ] Experience bullets are rewritten for this job in the JD's wording (not copied from the base resume) and each has a real number where the sources have one
- [ ] `check_resume_facts.py` reports no untraceable numbers, and Mallika was told which bullets have no number
- [ ] Every metric, date, role and link comes from the catalog or base resume (no invented numbers)
- [ ] Projected figures are still labelled as projected
- [ ] No em dashes, no adverbs ending in -ly, no AI filler in the summary, bullets or cover letter
- [ ] If the LaTeX type was requested but `pdflatex` is missing, Mallika was told the Regular renderer was used
- [ ] The application is in the tracker CSV (`TRACKER_CSV` in `config.py`)
