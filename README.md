# AI-assisted glioma research

**Paper (in preparation):** AI-assisted glioma research: a perspective with reproducible examples in imaging and clinical evidence.

Twelve educational notebooks, a tested Python package and the LaTeX source of
the perspective paper they accompany. Arvid Lundervold, Department of
Biomedicine, University of Bergen, Norway.

The scientific thread is the **glioma–brain interface**: how to measure a
tumour on MRI, how a growth model's assumptions shape what it predicts, and how
to compare such a model with one real patient's serial scans without
over-reading the result. Our published
[segmentation and anatomical-profiling study](https://doi.org/10.1080/03091902.2026.2713703)
and its [public code](https://github.com/arvidl/high-precision-glioma-segmentation)
provide the imaging foundation.

Two AI roles are kept apart: **trained imaging AI** supplies segmentations;
**generative research assistance** helped construct the code, controls, figures
and prose. Conventional numerical solvers reproduce the specified models, and
rebuilding the examples calls no language model. The investigator defines the
research direction and reviews assumptions and interpretation. Every notebook
states its question, AI contribution, investigator choices, verification and
evidence status.

## Release status

Until 15 October 2026 this repository was published in stages from a private
development repository, each part after the investigator's review. It is now the
working repository; changes arrive through reviewed pull requests.

| Part | Status |
| --- | --- |
| Python package `glioma_ai`, tests, notebook checker | Published (all modules) |
| Notebooks 00–12 and executed copies of 01–12 | Published |
| `data/derived/sub-PAT16/` (notebook 12's matrices; upstream QC not reviewed) | Published |
| Paper: LaTeX source, bibliography and built PDF in `paper/` | In preparation |
| Data release `lumiere-p048-prepared-v1` (notebook 03) | Published (see below) |
| Data release `ucsf-pdgm-cohort50-v1` (notebook 01, Figure 3) | Published (see below) |
| Release `published-figures-v1` (notebooks 01 and 09, paper) | Published: three unmodified CC BY 4.0 figures of Lundervold et al. 2026, fetched with `make published-figures-fetch` |

## Notebooks

| Notebook | Content | Open |
| --- | --- | --- |
| 00 | Colab quickstart: clones this repository, installs the locked environment and runs the notebook checker and synthetic demo | [Colab](https://colab.research.google.com/github/arvidl/AI-assisted-glioma-research/blob/main/notebooks/00_colab_quickstart.ipynb) |
| 01 | Measuring tumour compartments: overlap is not volume; NIfTI geometry checks | [executed](notebooks/executed/01_imaging_measurements.ipynb) · [Colab](https://colab.research.google.com/github/arvidl/AI-assisted-glioma-research/blob/main/notebooks/01_imaging_measurements.ipynb) |
| 02 | Tumour growth as reaction–diffusion: units, verification, thresholds and tissue-guided spread on a synthetic phantom; interactive explorers | [executed](notebooks/executed/02_tumor_dynamics.ipynb) · [Colab](https://colab.research.google.com/github/arvidl/AI-assisted-glioma-research/blob/main/notebooks/02_tumor_dynamics.ipynb) |
| 03 | LUMIERE Patient-048: released metadata, six visits of automated labels on a fixed plane, a baseline model and its failure, a biologically informed revision, a labelled fit, a what-if explorer and a 3D model with a tissue map | [executed](notebooks/executed/03_lumiere_prepared_slice.ipynb) · [Colab](https://colab.research.google.com/github/arvidl/AI-assisted-glioma-research/blob/main/notebooks/03_lumiere_prepared_slice.ipynb) |
| 04 | Can we trust AI-assisted research code? Records, checks and their limits: an actual assistance record, independent checks of the potassium model, constructed bugs and what each check catches | [executed](notebooks/executed/04_ai_assistance_record.ipynb) · [Colab](https://colab.research.google.com/github/arvidl/AI-assisted-glioma-research/blob/main/notebooks/04_ai_assistance_record.ipynb) |
| 05 | Can a glioblastoma change without growing? A synthetic two-state model of cell states under a macrophage cue, and why volume cannot see composition; interactive explorers | [executed](notebooks/executed/05_tumor_microenvironment.ipynb) · [Colab](https://colab.research.google.com/github/arvidl/AI-assisted-glioma-research/blob/main/notebooks/05_tumor_microenvironment.ipynb) |
| 06 | Does a glioma feed its own growth? A synthetic neuron–glioma feedback loop, nested controls and what a growth curve cannot tell; interactive explorers | [executed](notebooks/executed/06_neuron_glioma_feedback.ipynb) · [Colab](https://colab.research.google.com/github/arvidl/AI-assisted-glioma-research/blob/main/notebooks/06_neuron_glioma_feedback.ipynb) |
| 07 | When potassium clearance slows: a synthetic astrocyte potassium budget, the Nernst relation and what one trace cannot tell; interactive explorer | [executed](notebooks/executed/07_astrocytes_and_potassium.ipynb) · [Colab](https://colab.research.google.com/github/arvidl/AI-assisted-glioma-research/blob/main/notebooks/07_astrocytes_and_potassium.ipynb) |
| 08 | Potential is not field: what an electrode records, what a cell feels and how far that is from cognition; field estimation from sampled potentials, a synthetic tumour–brain border, evidence and testable hypotheses; interactive explorer | [executed](notebooks/executed/08_lfp_fields_and_cognition.ipynb) · [Colab](https://colab.research.google.com/github/arvidl/AI-assisted-glioma-research/blob/main/notebooks/08_lfp_fields_and_cognition.ipynb) |
| 09 | From tumour masks to brain networks: what segmentation measures, where the tumour ends and why cognition is not local; the published segmentation study with its tables and figures, Dice and HD95, hit-plots, a synthetic tumour–brain interface, networks, glia and brain waves, and the bridge to cognitive testing; interactive explorers | [executed](notebooks/executed/09_published_imaging_bridge.ipynb) · [Colab](https://colab.research.google.com/github/arvidl/AI-assisted-glioma-research/blob/main/notebooks/09_published_imaging_bridge.ipynb) |
| 10 | Cognition before and after brain-tumour surgery: the CANTAB tests, the Brain Tumor Connectomics cohort (OpenNeuro ds001226/ds002080) as group summaries and the sub-PAT16 case; cross-source agreement, an audit of an AI-generated infographic and its verifiable reconstruction, measurement precision, reliable change against retested controls with bootstrap, forecasting baselines and a proposed study; three tracks (cognitive neuroscience, clinical, modeling); interactive explorers | [executed](notebooks/executed/10_cantab_cognitive_outcomes.ipynb) · [Colab](https://colab.research.google.com/github/arvidl/AI-assisted-glioma-research/blob/main/notebooks/10_cantab_cognitive_outcomes.ipynb) |
| 11 | Tumor in the network: a graph-theory primer (walks, efficiency, spectra, Neumann series) and its use in neuroscience and neuro-oncology; a constructed structural network on the notebook 02 phantom, tract disconnection by the tissue-guided tumor, a constructed resection, and exact functional connectivity of a linear model; cognitive-neuroscience, clinical and modeling tracks; interactive explorer. No patient files | [executed](notebooks/executed/11_network_disconnection.ipynb) · [Colab](https://colab.research.google.com/github/arvidl/AI-assisted-glioma-research/blob/main/notebooks/11_network_disconnection.ipynb) |
| 12 | Can a virtual resection predict one patient's post-operative brain network? sub-PAT16 (OpenNeuro ds001226/ds002080, CC0) structural and functional connectivity before and after surgery, structure–function agreement of notebook 11's model, a virtual resection of tumour-crossing streamlines against the measured post-operative network, a size-and-location resection explorer with an assumed (unsourced) map to CANTAB domains, the patient's CANTAB scores, and a section marked as speculation on connectomics and analog cognition; clinical and modelling tracks; upstream QC not reviewed, descriptive only | [executed](notebooks/executed/12_patient_connectome.ipynb) · [Colab](https://colab.research.google.com/github/arvidl/AI-assisted-glioma-research/blob/main/notebooks/12_patient_connectome.ipynb) |

The executed copies show figures on GitHub; animations and sliders need a
running kernel. In Colab, notebooks 01–12 clone this repository in their first
cell, notebook 03 fetches the data release below when you run its Colab
cell, notebooks 01 and 09 fetch the published figures, and notebook 10 fetches the
pinned OpenNeuro participant tables (CC0) when you run its Colab cell. Notebook 11
downloads nothing. Notebook 12 reads the sub-PAT16 matrices that come with the clone;
its CANTAB cell needs local inputs and shows a notice in Colab. See the [notebook map](notebooks/README.md).

## Run locally

Use Python 3.12 and [uv](https://docs.astral.sh/uv/). Everything runs on CPU;
no GPU, model weights, API key or patient files are needed for 01 and 02.

~~~sh
git clone https://github.com/arvidl/AI-assisted-glioma-research.git
cd AI-assisted-glioma-research
uv sync --locked --group notebooks
make check        # Ruff and pytest
make notebooks    # executes the notebooks into ignored outputs/notebooks/
make demo         # synthetic figures and records in ignored outputs/demo/
~~~

Open the notebooks in Cursor, VS Code or JupyterLab with the project's
`.venv/bin/python` as kernel. Keep committed notebook sources output-free
(`make clear-notebooks`).

## LUMIERE Patient-048 data

Notebook 03 uses one patient of the LUMIERE dataset (Suter et al., *Scientific
Data* 9, 768, 2022, [doi:10.1038/s41597-022-01881-7](https://doi.org/10.1038/s41597-022-01881-7)).
Its prepared inputs (registered contrast-enhanced T1, automated MONAI tumour
labels and a FreeSurfer tissue map; 27 files, 26 MB) are attached to the release
[`lumiere-p048-prepared-v1`](https://github.com/arvidl/AI-assisted-glioma-research/releases/tag/lumiere-p048-prepared-v1):

~~~sh
make lumiere-bundle-fetch   # download, check the pinned SHA-256, extract to data/
~~~

then set `{"prepared_root": "<absolute path>/data/lumiere_p048_prepared"}` in
`local/lumiere-case.json`, or export `LUMIERE_P048_ROOT`. The LUMIERE authors
state that the dataset may only be used for non-commercial purposes; these
derived files are shared for research, teaching and learning under that
condition and are not covered by the MIT licence of the code. See
[data and provenance](docs/data.md). Nothing is used for clinical decisions.

## UCSF-PDGM cohort data

Figure 3 of notebook 01 recomputes Dice and volume error in the 50-subject
evaluation cohort of Lundervold et al. (2026) from UCSF-PDGM v5 (Calabrese et
al. 2022, [doi:10.7937/tcia.bdgf-8v37](https://doi.org/10.7937/tcia.bdgf-8v37);
CC BY 4.0, TCIA Data Usage Policy). The reference segmentations, the study's
SegResNet label maps and metrics records, and one subject's T1c (201 files,
9 MB) are attached to the release
[`ucsf-pdgm-cohort50-v1`](https://github.com/arvidl/AI-assisted-glioma-research/releases/tag/ucsf-pdgm-cohort50-v1):

~~~sh
make hpgs-bundle-fetch   # download, check the pinned SHA-256, extract to data/
~~~

then set `HPGS_REPO=<absolute path>/data/ucsf_pdgm_cohort50`, or write
`{"checkout": "<absolute path>/data/ucsf_pdgm_cohort50"}` to the ignored
`local/hpgs.json`. In Colab the notebook fetches it itself.

## CANTAB data

Notebook 10 and the paper's cognition figure use the Brain Tumor Connectomics
participant tables (OpenNeuro ds001226 v5.0.1 and ds002080 v4.0.1, CC0) and the
sub-PAT16 session table of the digital-twin project, pinned by SHA-256:

~~~sh
make btc-fetch      # download and check the pinned files into data/btc/
~~~

Notebook 10's cross-check against the authors' OSF behavioural release
(CC BY 4.0), and the CANTAB cell of notebook 12, also need

~~~sh
make cantab-fetch   # pinned OSF release into data/cantab/osf/
~~~

and the ignored `local/cantab-case.json` described in
[the CANTAB example](docs/cantab-example.md). Without them these cells print a
notice; nothing is substituted.

## sub-PAT16 connectome matrices

Notebook 12 reads small matrices in `data/derived/sub-PAT16/`: 82-region
structural (SIFT2) and functional connectivity before and after surgery, the
pre-operative weight through the tumour mask, `regions.tsv` and
`provenance.json` with input and file SHA-256 hashes. They were derived from
sub-PAT16 of the Brain Tumor Connectomics data (OpenNeuro
[ds001226 v5.0.0](https://doi.org/10.18112/openneuro.ds001226.v5.0.0) and
[ds002080 v4.0.0](https://doi.org/10.18112/openneuro.ds002080.v4.0.0), CC0)
by a local pipeline whose quality control has **not** been reviewed (0 of 37
checklist items). Every number derived from them is provisional. Images,
tractograms and demographics are not included. The derivation script reads the
investigator's local pipeline outputs and stays in the archived development
repository.

## Paper

`paper/main.tex` and `paper/references.bib` are the source of the perspective;
`paper/main.pdf` is the curated build. Every figure and number in the paper is
generated by the package, notebook by notebook:

~~~sh
make btc-fetch hpgs-bundle-fetch lumiere-bundle-fetch published-figures-fetch   # optional public inputs
make paper   # make paper-assets, then latexmk; needs a TeX installation with latexmk
~~~

Synthetic examples and the sub-PAT16 matrices need no download. Inputs that
were not fetched are listed in `paper/generated/assets.json`, and the paper
shows a notice in place of their figures. The two fetched bundles need the
`local/hpgs.json` and `local/lumiere-case.json` settings printed by their fetch
commands.

## Repository layout

~~~text
src/glioma_ai/   Scientific functions, references and CLI
notebooks/       Teaching notebooks (output-free) and executed/ copies
tests/           Numerical, unit, geometry and provenance checks
scripts/         Notebook checker and exporters, data build scripts
docs/            Data, environment, validation and AI-assistance records
paper/           LaTeX source, bibliography and built PDF of the paper
data/            Acquisition notes and the small sub-PAT16 matrices; other data are not tracked
~~~

Validation records and AI-assistance records in `docs/` dated up to 15 October
2026 were written in the private development repository
`arvidl/AI-assisted-glioma-research-dev`, now archived. Commit hashes they cite,
links into that repository (for example to its GitHub Actions runs) and
mentions of talk material refer to that repository and are not publicly
accessible. The talk and its slides were not carried over; later records cite
commits and runs of this repository.

## Licence and attribution

Code: MIT (`LICENSE`). Selected scientific helpers were adapted from
arvidl/AI-in-clinical-brain-tumor-research-dev at commit
f8a37993d11f595135f407638750442041422391, under the same licence. External
datasets keep their own terms. No human scientific review, clinical validation
or measured benefit of AI assistance is claimed beyond what the records state.
