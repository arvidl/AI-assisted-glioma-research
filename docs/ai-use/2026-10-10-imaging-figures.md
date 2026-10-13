# Notebook 01 figures and real-data counterpart

- Date: 10 October 2026.
- Tool: Cursor agent; exact backend snapshot and settings not captured.
- Request: label the synthetic imaging figure explicitly, write a paper-style caption, and add a similar figure from Lundervold et al. 2026 and its companion code, explaining the relevance with real data.
- Inputs: project source; the published figure manifest and locally imported CC BY asset; the companion checkout's UCSF-PDGM cohort reference segmentations, model label maps and per-subject metrics, read in place. RANO 2.0 thresholds were checked against the published article text.
- Contribution: legends, millimetre axes and per-bar Dice/ΔV for the synthetic figure; label nesting changed to necrotic core, enhancing rim and edema; paper caption rewritten; new `glioma_ai.hpgs_cohort` module recomputing Dice and signed volume error with geometry, label, companion-record and published-median checks; a three-panel real-data figure with a runtime-generated caption; notebook 01 restructured around Figures 1–3 with interpretation and exercises; tests.
- Investigator choices: the request named the published study and companion code. The median-Dice case selection, the largest-area slice and the display of RANO thresholds are assistant choices awaiting review.
- Verification: recorded in `docs/validation.md`.
- Evidence status: Figure 1 synthetic; Figure 2 published illustration; Figure 3 local recomputation from existing masks, not new inference or a new benchmark. Real-data outputs remain local under the TCIA data-use agreement. (Corrected 13 October 2026: TCIA lists UCSF-PDGM under CC BY 4.0 with its Data Usage Policy; see `docs/validation.md`, 13 October 2026.)
- Decision: pending investigator review.

This is a retrospective development summary, not a captured verbatim dialogue.
