# Repository guidance

This is a perspective paper with reproducible examples and an educational
codebase of twelve notebooks (01–12, plus the Colab quickstart 00). Read
README.md and docs/paper-plan.md before changing scope. The paper title is
stated there.

- Keep scientific logic in src/glioma_ai/; notebooks and the paper's figures
  call that package. Paper figures and number macros come only from
  `make paper-assets`; do not paste numbers into paper/main.tex by hand.
- Use uv, Python 3.12 by default, and the committed uv.lock. Do not update
  dependencies incidentally. Core examples run on CPU.
- Keep units, labels, coordinates, thresholds, and provenance explicit. Do not
  silently register, resample, threshold, relabel, or substitute a device.
- Separate synthetic constructions, real-data observations, published results,
  hypotheses, and proposed work. Never invent results, interactions, citations,
  human review, clinical validation, or co-author views.
- Distinguish imaging models, research assistants, and numerical solvers.
  Rebuilding figures does not call an LLM.
- Keep data, weights, credentials, patient details and numerical/figure inputs
  out of Git. The investigator authorized tracking:
  - paper/main.pdf, as a curated export rebuilt only with make paper;
  - executed copies of notebooks 01–12 in notebooks/executed/, with their
    licence notes, regenerated only with make executed-notebooks after a
    notebook changes;
  - the CC0-derived sub-PAT16 matrices and provenance in data/derived/sub-PAT16/
    (upstream QC not reviewed, stated as such); their derivation script stays
    in the archived development repository;
  - the released LUMIERE Patient-048 metadata in
    src/glioma_ai/references/lumiere_p048.json, under the LUMIERE authors'
    non-commercial condition;
  - the pins of the release assets lumiere_p048_prepared_v1.zip,
    ucsf_pdgm_cohort50_v1.zip and the published-figures-v1 images in
    src/glioma_ai/references/. The assets themselves stay out of Git, are not
    covered by the MIT licence, and a changed archive is published only as a
    new tag;
  - the AI-generated CANTAB slide attached to notebook 10, unmodified and
    labelled as an erroneous example for auditing.
  Images, tractograms and demographics stay out of Git.
- Preserve the MIT license and upstream attribution.
- For Python run make check; for notebooks run make notebooks; when paper text,
  figures or evidence change run make paper. Record actual platforms and skipped
  work in docs/validation.md.
- Record substantive assistance in docs/ai-use/. Claim model settings or human
  review only when known. Use codex/ for assistant-created branches and open a
  pull request; main receives reviewed work only.
- Keep changes small enough for review. Acquisition, heavy inference, GPU
  checks, and cloud execution are explicit steps.
