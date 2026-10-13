# Recording AI assistance

Imaging models, research assistants, and numerical solvers have distinct roles.
This repository was developed with assistance; rebuilding its examples does not
call an LLM or run trained segmentation.

Record the task, permitted inputs, tool information actually visible,
contribution, artifact, acceptance evidence, decision, reviewer if known, and
unresolved questions. docs/ai-records/template.json is an uncompleted template.
validate_record checks completeness, not truth or quality. Notebook 04 shows
its use. Patient details and sensitive interactions remain local.

Use pending_human_review until a researcher has reviewed an artifact.
A passing test cannot invent that review. Label retrospective summaries
accurately. Prompts, settings, time, and rejected suggestions are recorded only
when known.

The two AI roles are trained imaging and generative research assistance.
Conventional solvers reproduce specified equations; their calculations require
separate checks. The investigator supplies the research direction and reviews
assumptions and interpretation. All notebooks and corresponding paper examples
identify question, AI contribution, investigator choices, verification and
evidence status.

[The retrospective potassium case](worked-ai-potassium.md) connects an actual
development contribution to source and executable checks. Notebook 04 provides
the compact demonstration; notebook 07 contains the full experiment. Numerical
assumptions are not recorded as investigator-approved physiological estimates.
The historical neuroglial record is preserved unchanged. The current framing
revision has its own summary in `ai-use/2026-10-06-explicit-ai-roles.md` and
machine-readable record in `ai-records/2026-10-06-explicit-ai-roles.json`.

No productivity, scientific-quality, or clinical-utility effect was measured.
[The proposed benefit protocol](ai-benefit-evaluation.md) specifies matched
tasks, counterbalanced conditions, capped quality-qualified time and independent
review. Header-only forms in `ai-evaluation/` contain no observations. Clinical
relevance of a research artifact and patient benefit require different evidence.

The empirical cognition revision has a separate
[retrospective assistance summary](ai-use/2026-10-06-cantab-cognition.md) and
JSON record. Its actual contribution is source verification, pairing/precision
checks, implementation, educational framing and study design. A compact
supervised cognitive predictor is proposed but not fitted. Notebook 10 retains
the same five contribution fields. Local case linking information remains
outside Git and source exports; the released values of the one verified case
appear in the tracked paper and executed notebook 10, with CC BY attribution.

The retrospective 2D tumor-dynamics and Patient-048 example has a separate [assistance summary](ai-use/2026-10-06-2d-growth-notebooks.md) and [machine-readable record](ai-records/2026-10-06-2d-growth.json). The model is a classical prescribed solver; its outputs are not fitted clinical predictions.

The [8 October China-talk revision](ai-use/2026-10-08-china-talk-revision.md)
records the supplied-deck review, source reuse, narrative/timing changes and
optional editable export tooling. Timed human rehearsal and scientific review
remain separate from package and rendered-slide verification.
