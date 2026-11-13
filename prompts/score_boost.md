# Score-Boost Measures

Applied when `ats_score_matrix.total_score` is below 85. They sharpen framing and
surface real adjacent skills. They never permit fabricating capabilities,
metrics or experience.

## 1. Student framing
If the job is an internship, working-student (Werkstudent) or junior role and
`okf/base_files` shows a current enrolment (M.A. Innovation Design Management,
expected Feb 2027), lead the summary with that, for example "M.A. student in
Innovation Design Management and product designer, ...". Still 2 lines, 200
characters or fewer, no tool names.

## 2. Exact JD phrase weaving
Scan `Job_Description.yaml` for distinctive phrases (for example "end-to-end
user flows", "design system", "usability testing with B2B users"). Weave at least
one exact phrase into a truthful bullet. The phrase must describe work she did.

## 3. Real adjacent skills
If the JD asks for something her base resume already covers under another name
(for example AI-assisted prototyping, A/B testing, stakeholder management),
give it its own skills row. Replace weak filler instead of growing the block so
the one-page fit holds.

## 4. Itemized scoring rubric
For `post_rewrite_ats_score`, score each category against an explicit list of JD
term groups. Write the matched and unmatched lists inside `evaluation_criteria`.
Unmatched terms get a reason: "(excluded by user)" or "(not in candidate's
evidence)", mirrored in `remaining_gaps`. Every point traces to a string in
`Resume.yaml`. Target 88 or more only if the rubric supports it.
