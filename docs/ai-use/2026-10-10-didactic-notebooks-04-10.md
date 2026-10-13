# Didactic expansion of notebooks 04–10

- Date: 10 October 2026.
- Tool: Cursor agent; exact backend snapshot and settings not captured.
- Request: the investigator asked for notebooks 04, 05, 06, 07, 08, 09 and 10 to be elaborated and made more didactic, possibly with interactive demonstrations, each with an extensive introduction similar to notebook 01's "AI contribution and verification".
- Contribution: rebuilt the seven notebooks with an extensive introduction (question, three kinds of AI contribution, investigator requests and assistant choices with reasons, verification including what is not verified, evidence status), derivations, numbered figure captions, exercises and two interactive explorers each (one in 07 and 08). New tested package code:
  - `glioma_ai.notebook_display`: shows a figure as PNG regardless of the Matplotlib backend (several modules select Agg on import, which made `plt.show()` a no-op in notebooks 07 and 08).
  - Notebook 04: `glioma_ai.assistance_interactive` (constructed candidate solvers, two with deliberate bugs, run through the analytic, balance and swap checks; a validator playground on copies of a record).
  - Notebooks 05–06: `well_mixed_neuron_glioma` (RK4) in `glioma_ai.biology`; `glioma_ai.biology_interactive` (closed-form niche landmarks; well-mixed and spatial niche explorers; feedback explorer with phase plane and signal nullcline; spatial explorer with a movable drive).
  - Notebooks 07–08: `single_pulse_excess_mM` and `nernst_slope_mV_per_mM` in `glioma_ai.neuroglial`; `glioma_ai.neuroglial_interactive` (clearance explorer; field-sampling explorer and derivative-error trade-off).
  - Notebook 09: `surface_points_mm` and `hausdorff95_mm` in `glioma_ai.metrics`; `glioma_ai.imaging_interactive` (disc segmentations with shift, dilation and a distant blob; synthetic regional burden on lettered regions).
  - Notebook 10: `precision_interval` and `reliable_change_index` in `glioma_ai.cantab`; `glioma_ai.cantab_interactive` (precision explorer; reliable-change explorer with hypothetical per-measure inputs).
- Investigator choices: which notebooks to expand, the didactic aim, interactive demonstrations, and introductions modelled on notebook 01.
- Assistant choices awaiting review: listed in each notebook's introduction. They include the parameter values of every constructed example, the HD95 convention (6-connected surface, larger of the two directed 95th percentiles; single slices treated as 2D), the Jacobson–Truax index as the reliable-change example with hypothetical inputs only, non-anatomical region names in notebook 09, and two new references (Neftel et al. 2019; Jacobson and Truax 1991; `docs/bibliography-check.md`).
- Verification: recorded in `docs/validation.md`.
- Evidence status: all new figures and explorers are synthetic or hypothetical constructions; published values and the empirical CANTAB cells are unchanged. Explorers were exercised headlessly (initial state captured), not moved by hand in a live front end.
- Decision: pending investigator review.

This is a retrospective development summary, not a captured verbatim dialogue.
