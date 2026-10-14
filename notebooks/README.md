# Educational notebook map

Every notebook has the same five fields: question, AI contribution,
investigator choices, verification and evidence status. Notebook sources are
output-free; `make notebooks` writes executed copies to ignored
`outputs/notebooks/`. Executed copies of the published notebooks are tracked in
[executed/](executed/) so that their figures can be read on GitHub;
animations and explorers need a running kernel. `make executed-notebooks`
regenerates them and refuses runs with local paths or missing inputs.

| Notebook | Purpose and boundary |
| --- | --- |
| 00 | Colab quickstart: clones this repository, installs the locked environment, fetches the LUMIERE release when asked, runs the notebook checker and the synthetic demo |
| 01 | Synthetic MRI compartments, physical volumes, masks and label sensitivity; refusal to compare label maps whose affines differ |
| 02 | Synthetic 2D reaction–diffusion tutorial: state, equation and units, conservative migration, exact logistic reaction, mass balance and numerical refinement; interactive explorers; tissue-guided anisotropic spread across the corpus callosum on a constructed coronal phantom |
| 03 | LUMIERE Patient-048 use case with released metadata and RANO ratings; task, assumptions and tools; fixed plane with six automated-label observations; a week-045→049 baseline with controls and sensitivity; a revision with a two-level (T1Gd/T2) reading, brain domain, local/distant scoring and published coefficients; a labelled fit showing what one interval identifies; a what-if explorer; the same model in 3D with an explicit FreeSurfer tissue map; asserted results, interpretation, strengths and weaknesses |
| 04 | Can we trust AI-assisted research code? An actual retrospective assistance record and what it establishes; derivation of independent checks of the potassium model; an explorer showing that each check catches a different constructed bug; what a record validator can and cannot refuse, with a playground |
| 05 | Can a glioblastoma change without growing? Synthetic two-state cell-state model under a fixed macrophage cue, with local abundance conservation, closed-form equilibrium and time constant, identifiability of rates, and well-mixed and spatial explorers |
| 06 | Does a glioma feed its own growth? Synthetic neuron–glioma feedback with a slow dimensionless signal, nested controls, sensitivity and confounding; well-mixed model with exact limits and phase plane; well-mixed and spatial explorers |
| 07 | When potassium clearance slows: synthetic one-compartment potassium budget with astrocytic and other clearance, closed-form pulse landmarks, exact mass balance, the ideal Nernst relation, identifiability of the clearance split, glioma relevance; clearance explorer |
| 08 | Potential is not field: a synthetic potential whose exact field is known; central differences, sampling and noise; potential–field ambiguity and the optimal spacing; a synthetic tumour–brain border with an activity drop and a conductivity step; evidence on fields, glioma circuitry and the border; a proposed clinical analysis; testable field hypotheses at the border; empirical cognitive anchor; field explorer |
| 09 | From tumour masks to brain networks: the published segmentation and anatomical-profiling study (methods, accuracy with quartiles, hit-plot agreement, lobar and functional-anatomy involvement, published figures); what Dice and HD95 detect and miss; regional burden and small regions; a synthetic Fisher–Kolmogorov tumour–brain interface with the same enhancing boundary and different invisible tails; connectionism, structural and functional connectivity, disconnection and their critics; glia, fields and brain waves; measuring cognition; metric and burden explorers |

Notebooks 10–12 are in review and will be added one by one. Notebooks 04–09
have a clinical/biological (in 08 and 09: neuroscience and clinical) and a
modeling track and checked references; 05–09 also have a glossary.

**Google Colab.** Notebooks 01–09 can be opened directly in Colab: their first
code cell clones this repository and puts its package on the path, using
Colab's own NumPy, Matplotlib and ipywidgets rather than the locked versions.
Notebooks 01 and 09 have a Colab-only cell that downloads the published
figures (release `published-figures-v1`). Notebook 03 has a Colab-only cell that downloads the
[data release](https://github.com/arvidl/AI-assisted-glioma-research/releases/tag/lumiere-p048-prepared-v1),
checks its pinned SHA-256 and verifies every file. Notebook 00 instead runs
everything in the locked environment.

**Notebook 03 data.** Locally, run `make lumiere-bundle-fetch` and set
`LUMIERE_P048_ROOT` or the ignored `local/lumiere-case.json`; an exported
fixed-plane `.npz`/`.json` pair can be selected with
`LUMIERE_P048_SLICE_BUNDLE`. See [data and provenance](../docs/data.md). The
LUMIERE data are used under the authors' non-commercial condition and are not
covered by the MIT licence. The notebook selects the maximum-core-area plane at
week 045 and holds it fixed across visits. Selection is retrospective, labels
are automated rather than expert truth, and the models are not clinical
predictions.
