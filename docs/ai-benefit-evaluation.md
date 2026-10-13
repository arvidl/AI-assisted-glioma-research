# Prospective evaluation of AI assistance

**Status: proposed feasibility pilot.** No participants have been enrolled,
tasks assigned, reviewers appointed, timings collected or benefit estimated.
This protocol evaluates generative research assistance. Segmentation accuracy
belongs to the separate published imaging study; clinical outcomes require a
separate patient study.

## Question and comparison

Does access to a specified AI research assistant change the time needed to
produce an acceptable glioma-research artifact, while preserving scientific
quality? The unit of work is an independently specified task, not a patient.
Use synthetic inputs or released publication information, with no patient
records, credentials or private collaborator correspondence.

Propose **two investigators, six matched task pairs per investigator**: 24
sessions in total. These are design counts, not observations or a power
calculation. The pilot assesses feasibility and within-investigator differences;
it cannot establish a general productivity effect. If only one investigator
participates, declare that change before starting and report a single-person
case study.

Each pair has two distinct, comparably scoped versions. Assign one version to
assistant access and the other to no generative assistance. In both conditions,
permit the same Python/uv environment, editor, package code, documentation and
source packet. Disable generative completion and chat in the comparison
condition, including editor integrations. Ordinary autocomplete and deterministic
linters remain available in both. Specify the allowed assistant tools, network
access and source access identically in the frozen task instructions.

Use new tasks that the investigator has not already completed. Run equal-length
practice sessions before measurement. Do not reuse a completed artifact, an
assistant conversation or the same solution between paired versions. Learning
and carryover can remain despite distinct versions; document them as limitations.

## Candidate task families

Freeze the task packets and independent expected results before randomization.
Someone outside the measured sessions should check that the paired versions
have comparable difficulty and an unambiguous acceptance rule.

| Pair | Artifact requested | Independent acceptance evidence |
| --- | --- | --- |
| Imaging measurement | Compute a compartment volume and explain a grid mismatch | Hand-computable voxel/affine reference and explicit refusal of incompatible geometry |
| Potassium model | Extend or explain a prescribed release/clearance experiment | An analytic limiting case, concentration balance and correct units |
| Field interpretation | Derive a field from an explicit spatial potential | Analytic sign and V/m conversion; distinguish potential from field |
| Growth controls | Compare baseline, one-way and feedback assumptions | Uncoupled limit, appropriate matched comparison and numerical refinement |
| Clinical evidence | Specify eligibility for fabricated rows | A frozen eligibility key, missingness rules and explicit endpoint units |
| Evidence communication | Draft a short figure caption and evidence paragraph from a primary-source packet | Correct attribution and separation of observation, construction, hypothesis and proposal |

The completed potassium example is background, not a measured pilot task.
New parameter values alone may not prevent recall; use substantive, matched
extensions. Do not manufacture errors or rejected suggestions to dramatize AI.

## Assignment and recording

Create and retain a seeded random assignment before the first timed session.
Within each investigator, counterbalance condition order: three pairs start
with assistance and three without. Counterbalance which version receives
assistance across the two investigators. Randomize pair order and retain the
allocation file locally. Reviewers receive coded artifacts without condition,
tool labels or timing; retain uncertainty if blinding is compromised.

Lock this document's version, task packets, acceptance key, environment and
analysis plan before collection. Record tool/model identifiers and settings
actually exposed by the interface; use `unknown` for unavailable values.
Keep full prompts, outputs, changes and discarded proposals locally when
permitted. The public assistance record can refer to them without including
confidential material. The templates in `docs/ai-evaluation/` are blank and
contain no research observations.

## Timing and acceptance

Set a **60-minute wall-clock cap per session**, including assistant latency,
source checking, code execution, self-review and corrections. The clock begins
when the task packet is opened and stops at final submission or the cap.
Use one final submission; there is no reviewer-feedback correction loop during
the timed session. Pause only for a documented unrelated interruption. Retain
both total wall time and excluded interruption time. Record active editing,
assistant waiting and self-correction time when practical; these are descriptive
and must not replace the primary wall-clock measure.

Two independent reviewers, if available, apply the frozen key after submission.
Rate five domains on 0–2 (0 = incorrect/missing; 1 = partial; 2 = complete):
units/geometry; numerical or factual correctness; controls/reproducibility;
source provenance; interpretation and evidence boundaries. Agree task-specific
requirements before collection. For a non-numerical task, the numerical domain
tests factual consistency with its supplied evidence packet.

Acceptance requires **all mandatory checks, at least 8/10, and no critical
error**. A false citation, an unannounced unit/coordinate conversion, a wrong
required limiting case or a claim of patient benefit from synthetic results
is a critical error. Reviewers score independently before resolving disagreement;
retain both scores and the resolution. Reviewer identity and actual review are
recorded only once they exist. Without independent review, report technical
feasibility and self-assessment explicitly; do not label the outcome independently
validated scientific quality.

## Prespecified outcomes and analysis

| Outcome | Definition | Interpretation |
| --- | --- | --- |
| Primary: quality-qualified completion time | Net wall-clock time for an accepted submission; assign the 60-minute cap to an unaccepted or unfinished attempt | Restricted task-level measure. A rejected fast submission receives no apparent speed benefit |
| Acceptance | Fraction of submissions meeting the frozen rule in each condition | Report alongside time, including every assigned session |
| Scientific quality | Domain scores, total score and critical-error count before adjudication | Independent artifact assessment, not clinical efficacy |
| Effort and correction | Active effort, waiting, self-correction and documented discarded suggestions | Descriptive mechanism of any observed time difference |
| Clinical relevance | Reviewers judge whether the artifact answers its intended clinical research question, with written reasons | Relevance of a research artifact; no measured patient outcome |

For each matched pair calculate `assisted minus unassisted` quality-qualified
minutes and quality score. Report every paired difference, the median within
each investigator, and acceptance/critical-error counts by condition. Keep
investigator and task-family identifiers; sessions from one investigator are
not independent participant replications. Describe order, prior expertise,
carryover, blinding failures, missing sessions and deviations. Do not remove
failed attempts or replace them after seeing results. Distinguish the two
investigator summaries; any pooled median is descriptive. No confirmatory
p-value or claim of general superiority is planned for this small pilot.

A shorter accepted task would support a task-specific productivity observation.
Better independently reviewed artifacts would support a separate quality
observation. Neither establishes improved patient care. Clinical benefit would
require a justified clinical intervention, eligible patients, suitable outcomes
and an appropriate comparison outside this protocol.

## Launch requirements

Before collection, the investigator must finalize the participants, task packets,
independent reviewers, assignment, permitted tool/version, rubric and recording
process. Assess any institutional requirements for involving participants under
the applicable local process. This document is a reviewable design, not a claim
that these decisions or approvals have occurred.
