# Paper plan

Paper: **AI-assisted glioma research: a perspective with reproducible examples
in imaging and clinical evidence.** Arvid Lundervold, Department of Biomedicine,
University of Bergen. Source in `paper/`; figures and numbers from
`make paper-assets`.

This is a perspective with worked examples, not a completed clinical study or an
evaluation of AI benefit. The talk that the paper first accompanied is not part
of this repository (investigator decision, 15 October 2026). Since 19 October
2026 the README names the talk as context for visitors, without its slides
(investigator decision).

## Argument

The **glioma–brain interface** connects the examples: how a tumour is measured
on MRI, how growth and its cellular environment could be modelled, what
physiology at the border can and cannot be observed, and how a tumour and its
resection could change brain networks and cognition. Two AI roles are kept
apart: trained imaging models supply segmentations; generative research
assistance helped build the code, controls, figures and prose. Numerical
solvers reproduce specified equations, and rebuilding calls no language model.

Evidence levels stay distinct throughout: published results; real-data
observations; synthetic constructions; hypotheses; proposed work.

## Structure (thematic, one subsection per notebook)

| Section | Notebooks | Paper figure or table |
| --- | --- | --- |
| Introduction: AI roles, evidence levels, notebook map | all | Table: notebook, question, evidence label, place in the paper |
| Measuring and locating a tumour | 01, 09 | Synthetic compartments; UCSF-PDGM cohort; published pipeline, regional anatomy and hit-plot |
| One patient's serial scans | 03 | LUMIERE Patient-048 observations and the two-level revision |
| Growth and its environment | 02, 05, 06 | Reaction–diffusion baseline; niche-dependent states; neuron–glioma feedback |
| Physiology at the interface | 07, 08 | Potassium clearance; potential and field |
| Networks and cognition | 11, 12, 10 | Constructed disconnection and resection; sub-PAT16 connectome, virtual resection and sphere scenario; CANTAB cohort |
| Auditing AI-assisted research | 04 | Table of checks and what each catches |
| Discussion and research agenda; conclusion | 13 | One paragraph placing the examples in the nine-stage research workflow; no figure, no number macros |
| Appendix: reproduction | all | Commands and inputs |

Notebook 13 is a guide without new results, so it has a row in the notebook
table and a Discussion paragraph rather than a subsection (investigator
decision, 19 October 2026). Each notebook subsection states its question, what was constructed or observed,
the figure, key numbers (as generated macros), limits, and the five
contribution fields (question, AI contribution, investigator choices,
verification, evidence status).

## Bibliography

`paper/references.bib` holds only works cited in the paper. Each DOI is resolved
through doi.org (Crossref, or DataCite for the OpenNeuro and OSF datasets) and its
title, first author and year compared with the entry; the one arXiv preprint is
checked against the arXiv API, and the 1937 Kolmogorov–Petrovsky–Piskunov paper
has no DOI. Notebook reference lists stay in the notebooks.

## Open before submission

Investigator and clinical review of interpretation and citation context;
authorship, funding, competing interests and target journal; review of the
sub-PAT16 upstream QC (0 of 37 items). No future study is presented as agreed,
approved, calibrated or completed.
