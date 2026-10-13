# 2D tumor-dynamics and prepared LUMIERE examples

- Date: 6 October 2026.
- Tool: Codex desktop; exact backend snapshot and settings not captured.
- Request: replace superficial growth illustrations with an explicit, mathematically described 2D model, useful visualization, and a simplified real-data example using LUMIERE Patient 048.
- Inputs: investigator instructions; project source and existing development record; the prepared public Patient-048 image/label extract in the separate segmentation checkout. The MRI files were read in place and were not copied into this repository or a source archive.
- Contribution: a unit-explicit normalized-density Fisher–KPP-style equation, conservative no-flux diffusion step, exact local logistic reaction substeps, analytic/numerical controls, density and threshold-area visualizations, and a fixed-plane adapter for the prepared visits. The notebooks distinguish generated imaging labels, the classical solver, and research assistance.
- Investigator choices: the investigator requested 2D simplification and Patient 048. The illustrative coefficients, starting occupancy, threshold and ROI defaults are recorded as prescribed assumptions; they are not measurements or investigator-approved biological parameters.
- Verification: `make check` passed Ruff and 94 tests with the prepared case configured; `make notebooks` executed 12 notebooks, including both growth notebooks, and explicitly skipped only hosted Colab and absent separate clinical inputs; `make paper` built a 24-page PDF. The figures were inspected; both prepared-root and compact slice-bundle notebook routes were exercised; the bundle path completed with `LUMIERE_P048_ROOT` unset. Platform details and output boundaries are recorded in `docs/validation.md`.
- Evidence status: notebook 02 is synthetic. Notebook 06 is one retrospective fixed plane with upstream automated labels. Agreement with a later automated label is descriptive only; this example does not establish expert accuracy, untreated growth, a treatment effect, a mechanism, cognitive outcome or recurrence prediction.
- Decision: development draft pending human scientific review. No productivity, scientific-quality or clinical-utility benefit of research assistance was measured.
- Remaining: review the biological interpretation and model assumptions; decide separately whether the local Patient-048 panels belong in the paper or talk; a larger longitudinal, treatment-annotated cohort with independent reference labels is required for parameter estimation or prediction evaluation.

This is a retrospective development summary, not a captured verbatim dialogue or a record of co-author approval.
