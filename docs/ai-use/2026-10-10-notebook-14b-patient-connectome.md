# Notebook 14b: one patient's connectome

- Date: 10 October 2026.
- Tool: Cursor agent; exact backend snapshot and settings not captured.
- Request: the investigator asked for a strategy to make the teaching notebooks (01, 02, 14) more convincing with openly available data, naming UCSF-PDGM-0020, LUMIERE Patient-048, sub-PAT16 of Brain Tumor Connectomics and CANTAB.
- Inputs: the investigator's local `glioma-brain-digital-twin` derivatives for sub-PAT16 (read in place, not copied except for the derived matrices below), its BIDS metadata and processing scripts, the repository's notebooks 13 and 14, and Crossref records.
- Contribution: the assistant surveyed licences and local availability, and proposed real-data companion notebooks beside the synthetic ones, with sub-PAT16 first. It found that the upstream structural matrices were unsuitable as region connectomes. It wrote `scripts/derive_pat16_connectome.py`, `glioma_ai.connectome`, `glioma_ai.connectome_figures`, `tests/test_connectome.py`, `notebooks/14b_patient_connectome.ipynb` and the documentation updates. It also corrected the release checklist's description of UCSF-PDGM terms (CC BY 4.0 with the TCIA data usage policy).
- Investigator choices: companion notebooks rather than real-data sections inside the synthetic ones; tracking small CC0-derived sub-PAT16 matrices (exception recorded in `AGENTS.md`); notebook 14 on sub-PAT16 first. The endpoint-assignment rule, the pre-operative tumour mask as resection proxy, log-compressed weights, g = 0.8, the nulls and the edge-weight floor are assistant choices awaiting review.
- Verification: recorded in `docs/validation.md`. The upstream processing itself is unreviewed (0 of 37 checklist items).
- Evidence status: real-data observations from one patient; the model's predictions do not match the measured post-operative changes in this case; no validation, clinical finding or cognitive link is claimed.
- Decision: pending investigator review.

This is a retrospective development summary, not a captured verbatim dialogue.
