# Step 3: Cover letter

Follow SKILL.md rules. Write only `Cover_Letter.yaml`. The bash script compiles
and checks the PDF.

## Inputs
`ATS_Report.yaml` (`render_mode`, `language`, `closest_candidate_location`,
`application_source`, `weak_tie_contact`, `role_archetype`),
`Job_Description.yaml`, `project_info.md`, `okf/profile.yaml`.

## Rules
- Match the job's language (use `okf/templates/Cover_Letter_en.yaml` or
  `Cover_Letter_de.yaml` as the starting point). English: at most 4 paragraphs,
  250 to 320 words, one A4 page. German: at most 4 paragraphs, 180 to 240 words,
  real umlauts and ß, salutation `Sehr geehrte Damen und Herren,` (or the named
  contact), closing `Mit freundlichen Grüßen` without a comma, date `Berlin, TT.MM.JJJJ`,
  subject `Bewerbung als [Stellentitel]`. Tell Mallika her German is A2, so a native
  speaker should proofread before sending.
- Layout: sender, recipient, date, subject, salutation, body, closing
  (standard German business letter layout, also used for English).
- `recipient.company` and the subject's job title come from
  `Job_Description.yaml`. `recipient.address` comes from the JD only; if there is
  no street address, use the company name and city.
- Ground every claim in a specific project or role and its real metric from
  `project_info.md` or the catalog. Do not restate the resume; show how she
  worked: the research method, the decision, the collaboration.
- Paragraphs:
  1. Hook: tie one concrete requirement or product detail from the JD to one
     piece of her work, and say what she would do in her first 90 days.
  2. Deep dive on the best-matching project: method, decisions, result.
  3. A second project from a different angle (research, systems, leadership,
     AI-assisted prototyping, stakeholder work).
  4. Why this company, her German level (A2, currently learning) if the posting
     mentions German, her availability if `profile.yaml` has it, and a link to
     her portfolio in plain words ("my portfolio at <portfolio>").
- If the source is Referral or LinkedIn Connection, name `weak_tie_contact` in
  paragraph 1.
- No raw URLs in the prose except the portfolio address in the sender block or
  the last paragraph. No AI fluff ("passionate", "thrilled", "excited").
- Mention AI-assisted prototyping (Claude, Lovable, Google AI Studio) only when
  the JD values AI tools.

## Schema
```yaml
type: cover_letter
render_mode: "latex"          # same as Resume.yaml
language: "English"
sender:
  name: "[name from okf/profile.yaml]"
  address: "[closest_candidate_location]"
  phone: "[from profile]"
  email: "[from profile]"
recipient:
  company: "[Company]"
  department: "Hiring Team"
  address: "[from JD, or company and city]"
date: "[City], [Date]"
subject: "Application for [Job title]"
salutation: "Dear Hiring Team,"
paragraphs:
  - "[P1]"
  - "[P2]"
  - "[P3]"
  - "[P4]"
closing: "Sincerely,"
signature_image: ""           # path from okf/profile.yaml `signature`, or empty for typed name
```

Then run `./run_pipeline.sh cover --app-dir "<APP_DIR>"`.

Next: `./run_pipeline.sh finish --app-dir "<APP_DIR>"` and `99_completion_checklist.md`.
