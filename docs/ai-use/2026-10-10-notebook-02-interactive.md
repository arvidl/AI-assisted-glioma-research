# Interactive explorers and tissue-guided anisotropic spread in notebook 02

- Date: 10 October 2026.
- Tool: Cursor agent; exact backend snapshot and settings not captured.
- Request: make the Figure 1 experiment more didactic with interactive components (changing D, rho and the day of observation), and add a second interactive experiment (Figure 2) with spatially anisotropic spread in 2D guided by tumor location and tissue geometry (grey matter, white matter, CSF), for a tumor starting in the left parietal lobe and crossing the corpus callosum, motivated by Hannisdal et al. (2026), npj Precision Oncology 10:364.
- Inputs: notebook 02; `glioma_ai.growth_model` and `glioma_ai.growth_examples`; the article text supplied by the investigator; Crossref records for the four cited references; the PubMed abstract of Swanson, Alvord & Murray (2000).
- Contribution: `glioma_ai.tissue_growth` (constructed coronal phantom, diagonal-tensor solver with harmonic face coefficients and a cell-wise positivity limit, solver controls, contralateral summary); `glioma_ai.growth_interactive` (drawing functions and two `ipywidgets` explorers); `write_tissue_experiment` for Figure 2; `tests/test_tissue_growth.py`; notebook text for the explorers, Section 7, the Figure 2 caption and limits, and updates to the contribution record; README and notebook-index sentences.
- Investigator choices: the request set the scope, location and motivation. From options the assistant offered, the investigator chose live sliders with `ipywidgets` added to the notebooks dependency group, a constructed phantom rather than an atlas, and axis-aligned anisotropy rather than a full tensor. The phantom geometry, coefficients (D_g = 0.1 mm²/day, r = 5, a = 2, rho = 0.035/day), seed position, one-year horizon, slider ranges and the three nested scenarios are assistant choices awaiting review.
- Verification: recorded in `docs/validation.md`. The Swanson et al. (2000) grey/white ratio could not be checked (abstract only), so r = 5 is described as a teaching choice. The sliders were exercised headlessly, not in a live front end.
- Evidence status: synthetic constructions; the cohort findings of Hannisdal et al. are quoted as motivation, not reproduced or tested.
- Decision: pending investigator review.

This is a retrospective development summary, not a captured verbatim dialogue.

## Follow-up: playback

- Request: after the assistant suggested it, add a play button to the explorers and make the Section 4 animation show all five controls.
- Contribution: `_with_player` in `glioma_ai.growth_interactive`, `controls_animation` in `glioma_ai.growth_examples`, two tests and the notebook text.
- Verification: recorded in `docs/validation.md`.
