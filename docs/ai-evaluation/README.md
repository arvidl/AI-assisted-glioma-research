# Blank prospective recording forms

These header-only CSV files support the proposed protocol in
`../ai-benefit-evaluation.md`. They contain **no measured sessions or reviews**.
Copy them to ignored `outputs/ai-evaluation/` before collection. Keep identifiers
pseudonymous and interaction contents local. Do not add completed study rows
to these templates.

`sessions.template.csv` records assignment, tool availability, timing and
artifact provenance. Conditions are `assisted` or `unassisted`; minutes are
explicit wall-clock quantities. In the unassisted condition use `not_used` for
assistant tool/model/settings. Use `unknown` for assistant settings not exposed
in the assisted condition. A missing observation is blank, not zero.

`reviews.template.csv` records each independent review before adjudication.
Five domain scores range from 0 to 2. Mandatory checks, no critical errors and
a total score of at least 8 define acceptance. Preserve both individual reviews
and a separately labeled `adjudicated` round when applicable. Reviewers must
not receive condition or timing information. Keep the condition key separately.

There is no default result, elapsed-time estimate or automatic assertion that
scientific review occurred. The protocol defines how failures, caps and paired
comparisons should be handled once actual observations exist.
