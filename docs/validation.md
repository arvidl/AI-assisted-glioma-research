# Validation record

Written in the private development repository `arvidl/AI-assisted-glioma-research-dev`
until 15 October 2026, and in this public repository from then on; commit hashes and
links into the private repository are not publicly accessible.

## 6 October 2026: initial repository

Executed on macOS, ARM64, with CPython 3.12.14 and uv 0.12.23. The primary
intended workstation is the investigator's 128 GB M4 Max MacBook Pro;
no hardware performance benchmark was performed. The installed core uses CPU.

| Check | Observed result |
| --- | --- |
| Locked environment | `uv sync --locked --group notebooks` completed |
| Python checks | `make check`: Ruff lint and format passed; 32 tests passed, 1 skipped |
| Notebook validation | All eight notebooks parsed; committed copies contain no execution outputs |
| Notebook execution | `make notebooks`: 01, 02, 03, 04, and 07 executed successfully |
| Synthetic evidence | `make demo` generated metrics, figures, fixtures, and a source/output hash record |
| Manuscript | `make paper` built a seven-page PDF with resolved references; all pages were visually inspected |
| Runtime report | `glioma-ai doctor` reported NumPy CPU; PyTorch was not installed |
| Colab source export | `make colab-bundle` exported committed source; ZIP hash and revision metadata checked |
| Local ZIP reproduction | Extracted export installed in a fresh locked environment; all synthetic metrics matched and the exported commit was preserved in provenance |
| Workflow configuration | CI YAML parsed successfully; the first remote run also passed, as recorded below |

The skipped test requires an explicitly configured, prepared LUMIERE extract.
Notebook 00 needs a hosted Colab session; notebooks 05 and 06 require acquired
public inputs. They were structurally validated but not executed. No patient
data, model weights, clinical endpoints, or real-data observations were used
to establish these results.

The imaging notebook permits a 0.00001 mL round-trip tolerance because NIfTI
stores the affine's spacing with finite precision. It does not silently alter
the voxel geometry. The growth checks exercise mass conservation without
reaction, stability constraints, and density bounds. Clinical checks exercise
explicit missingness and finite survival-time eligibility in fabricated rows.

The initial notebook run needed host access for Jupyter's local kernel sockets.
This was an execution-environment restriction, not a dependency on cloud AI.
Executed notebook copies and their execution report are in ignored
`outputs/notebooks/`; the manuscript and its build files are also ignored.

The source ZIP was tested locally on macOS without a `.git` directory.
This checks the export and installation route; it does not test Colab's
hosted upload widgets, Linux runtime, network access, or session lifetime.

## GitHub Actions: 6 October 2026

[Run 37456245915](https://github.com/arvidl/AI-assisted-glioma-research-dev/actions/runs/37456245915)
completed successfully for source commit
`412897735cd74d2b76e0b570427607f528d87a27`. All seven jobs succeeded:

- Ubuntu and macOS, each with Python 3.11, 3.12, and 3.13: locked
  installation, Ruff lint and format, pytest, notebook execution, and the
  synthetic demo.
- Ubuntu manuscript job: generated synthetic evidence and compiled the
  LaTeX manuscript with BibTeX; the draft and evidence records were uploaded
  as a workflow artifact.

This records the inspected run for that commit. Future edits require checks
appropriate to their scope; a historical passing run is not a passing result
for subsequently changed scientific code.

## 6 October 2026: biology models and published imaging bridge

Executed on macOS ARM64 with CPython 3.12.14 and uv 0.12.23, using CPU.
The existing lockfile was preserved.

| Check | Observed result |
| --- | --- |
| Python | make check passed Ruff lint/format and **46 tests**; one prepared-LUMIERE test skipped |
| Notebook source | All ten notebooks parsed and remained output-free |
| Notebook execution | make notebooks passed 01, 02, 03, 04, 07, 08 and 09; 00, 05 and 06 skipped with recorded reasons |
| Niche model | Exact fixed-cue solution, local conservation, equilibrium, zero-cue limit and time-partition invariance checked |
| Neural model | Baseline recovery, mass conservation without growth, constant-signal logistic limit, growth confounding and combined positivity bound checked |
| Numerical refinement | The generated half-step comparison and prescribed sensitivity grid completed; the integral refinement difference was below 1% |
| Evidence separation | Published imaging aggregates have an attributed source record and separate TeX macros; the full imaging pipeline was not run |
| Assistance record | Biology development JSON validated with pending_human_review and no named reviewer |
| Source ZIP reproduction | Export of a92e0730493c566e5c548c436c81b68d82628f2b installed offline in a fresh macOS environment without Git; all four imaging/dynamics/biology summaries and the publication record matched |
| Manuscript | make paper built a 12-page PDF with resolved references; final rendered pages inspected |
| Talk | make talk built 16 slides (13 spoken + 3 backup); final rendered slides inspected; embedded timings total 18 minutes |
| TeX diagnostics | Final paper and talk logs contain no overfull boxes, unresolved references or warnings |

Executed notebook copies, figures, source/output hashes and PDFs remain local
and ignored. Jupyter execution required host access for local kernel sockets.
No imaging inference, biological calibration, treatment prediction or
clinical-utility evaluation was performed. The companion repository and its
unrelated local files were only read.

## Biology revision: completed GitHub checks

[Run 37461192907](https://github.com/arvidl/AI-assisted-glioma-research-dev/actions/runs/37461192907)
completed successfully for source commit
**a92e0730493c566e5c548c436c81b68d82628f2b**. All seven jobs succeeded:

- Ubuntu and macOS, each with Python 3.11, 3.12 and 3.13: locked installation,
  Ruff lint/format, pytest, educational-notebook execution and generated evidence.
- Ubuntu manuscript job: generated the evidence and compiled both the
  perspective paper and Beamer deck; PDFs and evidence records were uploaded
  as the paper-talk-and-evidence workflow artifact.

The source ZIP from this commit also reproduced all four numerical workflows
and the separate published reference in a fresh local macOS environment.
That is an export/install check, not a hosted Google Colab run. The subsequent
validation-only documentation commit changes no checked scientific source.

## 6 October 2026: astrocytes, fields and cognition revision

Executed on macOS ARM64 with CPython 3.12.14 and uv 0.12.23, using the
existing locked CPU environment. No dependencies or model weights were added.

| Check | Observed result |
| --- | --- |
| Python | make check: Ruff lint/format passed; **58 tests passed**, one prepared-LUMIERE test skipped |
| Notebook source | All 13 notebooks validated; tracked copies remained output-free |
| Notebook execution | make notebooks executed 01, 02, 03, 04, 07, 08, 09, 10, 11 and 12; 00/05/06 retained explicit skip reasons |
| Potassium | Independent analytic solution, release/clearance balance, zero-clearance and decay limits, partition invariance and equal-total-clearance ambiguity checked |
| Nernst and fields | Sign and concentration-ratio limit; V/m conversion, gradient sign, explicit geometry, constant-offset invariance and same-potential/different-field construction checked |
| Published illustrations | Three pinned local-author Git assets imported after SHA-256 verification; captions compared with published Figures 1 and 4; CC BY 4.0 attribution retained |
| Evidence generation | Six scientific parameter groups and 38 generated output hashes recorded; published figures/medians separate from synthetic results |
| Assistance record | Current revision JSON validated as pending_human_review, without a named reviewer or measured benefit |
| Manuscript | make paper built **18 pages** with resolved citations; all final rendered pages visually inspected |
| Talk | make talk built **21 slides: 14 spoken + 7 backup**; all final rendered slides visually inspected |
| Timing | Fourteen embedded budgets sum to **18.0 minutes**; speaking guide and storyboard agree; this is a plan, not a timed rehearsal |
| TeX diagnostics | Final logs contain no warnings, overfull boxes or unresolved citations |

Jupyter kernels required host access for local sockets. The sandboxed attempt
could not start a kernel; the host-enabled runs completed. Notebook 12 displayed
the locally imported published images. All image bytes, executed copies and
PDFs remain ignored. Figure 1's compartments and the Fig. 4c hit-plot are
reference-mask illustrations, not new model predictions or histological truth.

The cleaned public companion code snapshot omits the author figure assets.
Source-only Git/CI/Colab builds use the documented optional-import notices.
No restricted BGO-D image, raw patient input, segmentation inference, calibrated
physiology, clinical/cognitive prediction or measured AI benefit was used.
Human scientific review and a hosted Colab session remain unperformed.

## Neuroglial revision: completed CI and source export

[Run 37467046647](https://github.com/arvidl/AI-assisted-glioma-research-dev/actions/runs/37467046647)
passed all seven jobs for scientific source commit
**d0fef2e8a7210e63898a6f81bad80196a90a6c37**:

- Ubuntu and macOS with Python 3.11, 3.12 and 3.13: locked installation,
  Ruff, pytest, ten default notebook executions and synthetic evidence.
- Ubuntu manuscript job: generated evidence and compiled the source-only
  manuscript and Beamer deck; uploaded PDFs and evidence records.

The source ZIP from the same commit was also extracted into a fresh macOS
ARM64 environment without Git. Locked dependencies, including the notebook
group, were installed with network access; notebook execution and subsequent
builds then ran offline. All six scientific workflow summaries and the separate
publication record matched the verified checkout exactly. Every recorded
source hash matched, and provenance retained the exported commit.

Ten notebooks executed successfully without the optional published image
assets. The source-only paper compiled to 16 pages and the deck to 21 slides,
with the documented import notices and no final TeX warnings or overfull boxes.
The fully illustrated local paper remains 18 pages. These variants differ
only in optional published images and their surrounding layout, not reported
metrics or synthetic results. ZIP contents were checked to exclude generated
images, executed outputs, patient files and credentials.

This verifies a local export/install route and remote CI, not Colab's hosted
upload widgets or session. The documentation-only follow-up records these
results without changing tested scientific source.

## 6 October 2026: explicit AI roles and evaluation design

Executed in the local macOS ARM64 staging checkout with CPython 3.12.14,
uv 0.12.23 and CPU. The lockfile and scientific package were unchanged.

| Check | Observed result |
| --- | --- |
| Source and Python | make check passed Ruff lint/format and **58 tests**; one prepared-LUMIERE test skipped |
| Notebook source | All 13 sources validated and remained output-free; each contains question, AI contribution, investigator choices, verification and evidence status |
| Notebook execution | make notebooks executed 01, 02, 03, 04, 07, 08, 09, 10, 11 and 12; 00/05/06 retained their explicit skip reasons |
| Worked contribution | Notebook 07 checked the independent constant-input analytic solution, concentration balance and equal-total-clearance ambiguity; notebook 10 also checked the analytic limit |
| Assistance records | Notebook 07 validated both the preserved historical neuroglial summary and the new framing record, with pending_human_review and no named reviewer |
| Protocol templates | Both evaluation CSV files have one header row and no observations; identifiers, timing units and independent review fields are explicit |
| Manuscript | make paper built **21 illustrated pages** with resolved references; all final rendered pages inspected; all 13 five-field blocks remain on one page each |
| Talk | make talk built **22 slides: 14 spoken + 8 backup**; rendered slides inspected, including final changed layouts |
| Timing | Embedded budgets, storyboard and speaking guide agree on **18.0 minutes**; both AI roles appear by the planned **1:24** mark |
| TeX diagnostics | Final paper and talk logs contain no warnings, overfull boxes or unresolved citations |
| Scope retention | Scientific functions, publication values, figure-source manifest, uv.lock, MIT license and original neuroglial assistance JSON were unchanged |

Jupyter execution used host access for local kernel sockets. The work adds
contribution explanations, independent notebook checks and a proposed pilot;
it runs no LLM or trained imaging inference. The potassium history remains
retrospective, with model assumptions and biological interpretation awaiting
human scientific review. No pilot participants, assignments, timings,
independent reviews, measured assistance benefit or patient outcome were collected.
The speaking budget is a plan, not a timed rehearsal. PDFs, figures and executed
notebook copies remain ignored and local. Remote CI and a hosted Colab session
are not implied by these local checks.

## Explicit AI roles: completed CI and source export

[Run 37477957424](https://github.com/arvidl/AI-assisted-glioma-research-dev/actions/runs/37477957424)
completed successfully for source commit
**ffa24aac86b10065ac60ff96e84caea6feb01167**. All seven jobs succeeded:

- Ubuntu and macOS with Python 3.11, 3.12 and 3.13: locked installation,
  Ruff, pytest, ten default notebook executions and synthetic evidence.
- Ubuntu manuscript job: generated evidence and compiled the source-only
  paper and Beamer deck; uploaded the PDFs and evidence records.

The source ZIP from this commit contains all 13 output-free notebooks, the
worked-case document, new assistance record, proposed protocol and header-only
forms. It excludes generated figures/PDFs, acquired imaging, weights and local
outputs, and retains the exported source revision. Notebook 07 executed from
a fresh ZIP extraction without Git, using the exported package source and the
existing locked macOS Python environment. That check verifies record paths and
the worked analytic/balance example; it is neither a fresh installation nor
a hosted Colab session.

The illustrated PDFs and checked source ZIP were copied into the main local
project, with matching SHA-256 hashes. The documentation-only follow-up records
these outcomes without changing tested scientific or notebook source.

## 6 October 2026: source-verified CANTAB and cognitive study design

Executed in the local macOS ARM64 staging checkout with CPython 3.12.14,
uv 0.12.23 and CPU. The existing lockfile and dependencies were preserved.

| Check | Observed result |
| --- | --- |
| Source acquisition | Original OSF data revision 2, legend revision 1 and non-imputed regression code revision 1 downloaded explicitly; all three SHA-256 hashes agree with the pinned manifest |
| Behavioral availability | 39 source rows: 11 GLI, 17 MEN, 11 CON; complete paired four-domain scores in 7, 14 and 10 respectively; MRI linkage/QC not performed |
| Local case verification | Five of 28 local CANTAB measures shared at both visits; nine cells exact, one compatible at released precision; no case ID or exact dates exported |
| Precision and timing | Figure uses released values, so the attention scores are equal at that precision; actual assessment interval generated from source dates, without treating it as time since surgery |
| Python | make check passed Ruff lint/format and **72 tests**; one prepared-LUMIERE test skipped |
| Reader controls | Synthetic tests cover nonfinite/malformed values, diagnosis codes, duplicate IDs, chronology, missing dates, bounds, discrete counts, explicit case matching, source precision and changed hashes |
| Notebook source | All **14 notebooks** validate and remain output-free, with the five contribution fields |
| Notebook execution | make notebooks executed 01, 02, 03, 04, 07, 08, 09, 10, 11, 12 and **13**, including its empirical availability, case figure and retrospective-record checks; 00/05/06 retain explicit skips |
| Empirical generation | make cantab wrote the four-domain figure, availability, case audit, environment/input/output hashes and separate TeX values; all remain ignored |
| Study schemas | Both proposed cognition-study CSVs have unique column names and one header row, with no observations |
| Manuscript | make paper built **24 illustrated pages** with resolved references; final rendered pages inspected, including the CANTAB section/figure, prediction proposal and declarations |
| Talk | make talk built **23 slides: 15 spoken + 8 backup**; rendered slides inspected; empirical slide 11 immediately precedes hypothesis slide 12 |
| Timing | Embedded budgets, storyboard and speaking guide agree on **18.0 minutes**; two minutes remain reserved; this is not a timed rehearsal |
| TeX diagnostics | Final paper/deck logs contain no warnings, overfull boxes or unresolved citations |
| Data/source boundaries | Tracked additions contain no local case identifier/path, raw table or individual-score output; MIT license, uv.lock and prior assistance records unchanged |

Jupyter execution used host access for local kernel sockets. The digital-twin
repository and its prepared sessions table were read but not modified.
Primary publication records, source definitions and the MRI resource were
checked separately. The Google slide is not treated as a verified numerical
source. The empirical example describes released task performance, without
reliable-change classification, causal resection/growth estimation or MRI–cognition
association. No cognitive predictor, trained segmentation inference or LLM was
run while rebuilding the examples. The larger-cohort prediction protocol and
its endpoint/model choices remain proposed and pending scientific review.
There are no LFP, astrocytic or microtubule observations in this example.
Hosted Colab and clinical/predictive validation remain unperformed.

## CANTAB revision: completed CI and independent source export

[Run 37483717661](https://github.com/arvidl/AI-assisted-glioma-research-dev/actions/runs/37483717661)
passed all seven jobs for scientific source commit
**ae6a604bc370970ba67d64fc51c512880d1485e8**:

- Ubuntu and macOS with Python 3.11, 3.12 and 3.13: locked installation,
  Ruff lint/format, pytest, eleven default notebook executions and synthetic
  evidence generation.
- Ubuntu manuscript job: compiled the source-only paper and Beamer deck and
  uploaded PDFs/evidence as the workflow artifact. No empirical tables or case
  configuration were supplied to CI.

The source ZIP from this commit was extracted outside any Git worktree into
a fresh macOS ARM64 environment. Locked dependencies, including the notebook
group, installed offline from the local uv cache. All fourteen notebook sources
validated and eleven executed. Notebook 13 ran the synthetic precision control
and record check, then reported missing empirical inputs and case configuration
without substituting a figure. All nine numerical/publication JSON files,
scientific parameter groups and recorded source hashes matched the checked
checkout. Provenance recorded no Git commit and retained the exported revision.

The no-data source-only paper compiled to 22 pages and the deck to 23 slides,
without final TeX warnings or overfull boxes. The illustrated local paper remains
24 pages. The ZIP excludes acquired tables, case links, figures/PDFs, executed
outputs, weights and credentials. After the no-data run, the explicit
`make cantab-fetch` command was separately exercised from that export: all three
source hashes matched. The availability-only CLI branch produced cohort counts
and no individual case figure or predictor.

This verifies local export/installation and remote CI, not a hosted Colab session
or empirical clinical validation. The documentation follow-up records these
checks and clarifies the data-linking scope without changing scientific code.

## 6 October 2026: notebook-interface documentation

The README now documents Cursor notebook execution, Zed's Python script-cell
REPL, optional kernel registration, JupyterLab and the source-ZIP Colab route.
The environment guide links to those instructions. Software behavior was
checked against official Cursor, Jupyter-extension, Zed and Google Colab
documentation; the editor interfaces and hosted Colab were not executed.

On the local macOS ARM64 workstation, README/environment-guide relative links,
section anchors and fenced blocks were checked. `make -n colab-bundle` resolved
to the documented locked export command. The existing ZIP's SHA-256 and embedded
revision matched `bundle.json`; required environment/package files and all 14
notebook sources were present, with local outputs/configuration absent. Its
source revision remains `ae6a604bc370970ba67d64fc51c512880d1485e8`.

This changes documentation only. Python, notebooks, dependencies and scientific
evidence are unchanged; no new notebook-execution or clinical result is claimed.

## 6 October 2026: editable PowerPoint export

Converted the existing illustrated Beamer deck to the local ignored
`outputs/powerpoint/slides.pptx` on macOS ARM64 using the bundled Node.js
Artifact Tool runtime. The deck has **23 slides: 15 spoken + 8 backups**,
native editable text and bullets, one native editable results table, ten
scientific image objects including the two equation panels, and 23 notes parts.
Arial replaces Latin Modern for editable text; the source figures are retained.

Package integrity, slide geometry, heading fit, native bullet geometry, required
table presence, font policy and reimport of the exact final PPTX passed.
All final slides were rendered at 1600 by 900 pixels and individually inspected
against the illustrated Beamer reference. Separate OOXML checks confirmed slide
title order, native text on every slide, speaker notes/source links, results-table
values matching the generated source macros, unchanged embedded image bytes,
uncropped images and preserved aspect ratios. Source TeX, PDF and speaking-guide
hashes remained unchanged. The local manifest and validation receipts retain
the exported-file hash and source revision.

Native Microsoft PowerPoint rendering/editing was not exercised: the computer-use
tool reported that permission was not granted. This is a checked editable-format
snapshot, with native-application compatibility still unverified. No Python
package, notebook, dependency, manuscript, scientific calculation or evidence
claim was changed for this export, so their earlier checks were not rerun.
The CANTAB-containing artifact and previews remain ignored and local.

## Not yet exercised

- Hosted Google Colab (first completed on 10 October 2026; see the end of this record).
- Apple MPS, CUDA, or trained segmentation-model inference.
- Optional CGGA, TCGA-Reports, or prepared LUMIERE inputs in this checkout.
- Human scientific review, a clinical validation study, or an experiment
  measuring the effect of AI assistance.

The predecessor's tests and real-data outputs are not validation of this
repository. Validation here supports numerical and software behavior of
educational examples; it does not establish clinical utility.

## 6 October 2026: explicit 2D growth and LUMIERE fixed-plane example

Executed on macOS ARM64 with CPython 3.12.14 and uv 0.12.23, using the existing locked CPU environment. The prepared Patient-048 extract was supplied explicitly from its existing local checkout; MRI files were read in place and were not copied into this repository.

| Check | Observed result |
| --- | --- |
| Python | `make check`: Ruff lint and format passed; **94 tests passed**, including configured LUMIERE geometry/label checks and three notebook-input selection regressions |
| Notebook source | All 14 notebooks passed source validation and are output-free; previously saved cell outputs/execution counters were removed from tracked notebook files |
| Notebook execution | `make notebooks`: **12 executed**; 00 skipped for hosted Colab and 05 skipped because separate clinical inputs were absent; notebooks 02 and 06 executed successfully; notebook 06 also completed from the hash-checked 2D bundle with `LUMIERE_P048_ROOT` unset |
| Synthetic dynamics | Closed-form logistic limit, heterogeneous no-flux diffusion conservation, reaction mass accounting, density bounds, Neumann-mode refinement, step rejection and halving comparison ran |
| LUMIERE case | Six prepared visits passed geometry/label checks; one plane was selected from week 045 alone and held fixed; the prescribed forward comparison, controls, sensitivity analyses and numerical balance checks completed |
| Editor configuration | The ignored `local/lumiere-case.json` resolved the prepared root with LUMIERE environment variables unset |
| Portable 2D input | The exported six-plane `.npz`/`.json` pair passed bundle hash/geometry checks; the notebook runner recognized it as an explicit input |
| Manuscript | `make paper` completed and built a 24-page PDF; TeX log contained no warning or overfull-box markers |
| Visual inspection | The synthetic controls and Patient-048 model figures were inspected; local generated assets remain ignored |

Notebook 06 compares a prescribed 2D model with later automated labels. It does not estimate patient coefficients, establish untreated progression, validate the segmentation against expert truth, or predict recurrence or clinical outcome. The new Patient-048 model panels remain local notebook/manuscript-support assets; the tracked paper and talk sources do not yet include them. The data, case configuration, executed notebook copies, numerical records, figures and manuscript PDF remain local and ignored. Hosted Colab and human scientific review were not performed.

## 8 October 2026: China talk revision and synchronized editable exports

Implemented in `AI-assisted-glioma-research-dev` on the local macOS ARM64
workstation with the locked CPU environment, CPython 3.12.14 and uv 0.12.23.
The active talk title is **AI-Assisted Glioma Research: Imaging, Tumor–Brain
Interactions, and Cognition**. The manuscript retains its perspective title.

| Check | Observed result |
| --- | --- |
| Repository checks | `make check`: Ruff lint and formatting passed; **92 tests passed, 2 skipped** because explicit prepared LUMIERE inputs were absent in this run |
| Artwork import | `make talk-artwork` verified the supplied deck and asset hashes, then imported only the Bergen seal, MMIV logo and closing photograph into ignored local storage |
| Build | `make talk-pptx` ran the existing CPU demo, rebuilt the Beamer PDF and produced the PowerPoint from that PDF, source tables and source notes |
| PDF | 29 pages; no final TeX warning, overfull or underfull markers |
| PowerPoint | 29 slides: **15 visible spoken slides + 14 hidden backups**; native editable text on every slide; two native editable tables on slides 5 and 24; 29 speaker-note parts; 14 retained figure/artwork/equation images |
| Format validation | Package integrity, slide geometry, heading fit, required tables, Arial font policy and reimport of the exact final PPTX passed |
| Independent content audit | Native editable text matched the prepared PDF text after whitespace/ligature normalization; both native tables matched source values; all 29 note texts matched the manifest; 14 embedded images matched the prepared hashes and had no cropping; slide title order and hidden-slide boundaries matched; source hashes stayed current |
| Visual inspection | All 29 final PDF pages and all 29 final reimported PowerPoint slides were individually inspected at 1600 by 900 pixels |
| Timing audit | The storyboard and speaking-guide budgets independently total **18:00**; the compact script has approximately 1,500 spoken words, with figure explanations and pauses included in the budgets |
| Scope check | Scientific package, notebooks, `pyproject.toml`, `uv.lock`, manuscript source and manuscript PDF are unchanged |

The layout validator reported three small text-frame overlaps on backup slide
26, where independently editable subscript fragments sit beside their base
symbols. Individual inspection confirmed readable notation and no glyph
collision. Early export drafts had incorrect block-heading colors and flattened
inline math; these were corrected before the final export. The two tables have
no unambiguous total rows, so automatic total arithmetic was inapplicable;
the separate content audit checked every displayed cell against the source.

The runtime used for PDF extraction and PowerPoint authoring is separate from
the locked scientific environment and is documented in `talk/README.md`.
The final source manifest, export record, validation receipt and rendered
previews are in ignored `outputs/powerpoint/build/`. Text is editable in Arial;
scientific plots and display equations retain rendered appearances as images.

Final artifact SHA-256 values:

- `talk/slides.pdf`: `9f3c5c7165d3a2698ee58f0b1b9181dba1ab9fd39b172c4d3893147b8bc9e799`
- `talk/slides.pptx`: `d34abacc46fcca35c1bbb93062b58407ce4a5d7ab7e80eef11f1510e536a4907`

The carry-over map covers all twenty slides in the supplied 12:25 deck. Published
imaging panels and selected results remain attributed; Finse modalities,
tractography, BOLD, compression and speculative mechanisms are discussion
backups. The uploaded CANTAB infographic was replaced with the existing
source-verified paired illustration because its scales/values were
inconsistent. No Finse patient files, movies, BIDS tree or local outputs were
copied or changed. The authorized curated talk exports embed the existing
paired illustration without its source-case identifier; raw scores, case links
and standalone empirical figures remain local and ignored.

No new scientific evidence or notebook content was introduced. `make notebooks`
and `make paper` were therefore not repeated for this talk/documentation/export
revision. Earlier runs remain recorded above; this run does not validate
LUMIERE inputs, clinical utility, cognition prediction or AI benefit.

The eighteen-minute plan is **not a recorded timed human delivery**. The
checkpoint sheet and optional cuts are in `talk/rehearsal.md`; the actual-time
log is blank. Native Microsoft PowerPoint rendering/editing, the meeting's
projection setup, hosted Colab, human scientific review and a timed spoken
rehearsal were not exercised. No collaborator approval is claimed. At the end of the implementation turn, changes remained local and
uncommitted; that turn included no commit, push or visibility change. The
investigator subsequently authorized committing and pushing this revision.

## 10 October 2026: output-free notebooks and LUMIERE test resolution

The investigator's `make notebooks` failed because commit `14879bf` stored outputs and execution counts in notebooks 01, 02, 03 and 06; `make check` skipped both prepared-LUMIERE tests because they read only `LUMIERE_P048_ROOT`, not the ignored `local/lumiere-case.json`. Executed on macOS ARM64 with CPython 3.12.14 and the existing locked CPU environment.

| Check | Observed result |
| --- | --- |
| Notebook sources | Outputs and execution counts removed; the diff changed no cell source; `make clear-notebooks` reported nothing further to clear |
| Python | `make check`: Ruff lint and format passed; **95 tests passed, none skipped**, with the prepared case resolved from the local configuration and LUMIERE environment variables unset |
| Notebook execution | `make notebooks`: 12 executed; 00 (hosted Colab) and 05 (absent clinical inputs) skipped |

Jupyter execution used host access for local kernel sockets. `make demo` and the paper build still consult only `LUMIERE_P048_ROOT` for the Patient-048 illustration. `make paper` was not rerun because no manuscript evidence changed.

Notebook 00's text was then updated to the current executed and skipped notebooks, and its figure cell now also displays the generated `dynamics` and `clinical_evidence` figures; a stale trailing cell was removed. The source validated and `tests/test_notebook_validation.py` passed. Notebook 00 itself was not executed: it needs a hosted Colab session.

The investigator then ran notebook 00 in hosted Colab from commit `bf58fcd`. Upload, uv installation, locked sync and `glioma-ai doctor` completed; the notebook checker failed with "Kernel died before replying to kernel_info". Colab's IPython configuration names `google.colab._kernel.Kernel`, which the locked environment cannot import. Placing that setting in a temporary IPython profile, or in the environment's `etc/ipython` configuration directory, reproduced the failure locally on macOS ARM64. The checker's kernels now use a private IPython/Jupyter configuration directory and an explicit command-line kernel class; with either bad configuration present, a clean export executed 12 notebooks and skipped 00, 05 and 06. A complete hosted Colab run has not yet been observed.

A second hosted run from `bede1db` passed the kernel-class step but failed while loading IPython extensions: Colab's system-wide configuration, which IPython always reads from `/usr/local/etc/ipython` and `/etc/ipython`, also lists Colab-only extensions. Locally, an environment-level configuration naming the `google.colab` extension, with extension failures made fatal, reproduced that failure with the committed checker. The checker now starts kernels through a small launcher that empties IPython's system-wide and environment configuration directories before starting `ipykernel`; with the same configuration plus the Colab kernel class, a clean export executed 12 notebooks and skipped 00, 05 and 06. Clearing `/etc/ipython` itself was not exercised locally.

**First complete hosted Colab run.** The investigator then reran notebook 00 with **Run all** in a fresh hosted Colab CPU runtime, using the source ZIP exported from `2dcfb9e`. Every cell completed through the final download cell, which Colab marked as executed; with **Run all**, this means the upload, uv installation, locked sync, `glioma-ai doctor`, the notebook checker and `glioma-ai demo` all exited successfully. The metrics summary was displayed, including `not_measured` for every assistant endpoint. Colab reported the notebook's `glioma-ai` kernel name as unrecognised and used `python3`, as intended; notebook 00 now declares `python3`. This observation comes from the investigator's screenshots of the final cells. The per-notebook checker log, the displayed figures and the downloaded results archive were not inspected here, and the Colab runtime's Python patch version was not recorded.

## 10 October 2026: notebook 01 figures and real-data counterpart

Executed on macOS ARM64 with CPython 3.12.14 and the existing locked CPU environment; no dependency changed.

| Check | Observed result |
| --- | --- |
| Synthetic figure | Legends for every label and contour, millimetre axes, slice position and per-bar Dice/ΔV. Labels now nest as necrotic core, enhancing rim, edema; Dice (0.644, 0.830), reference volume (8.018 mL) and expansion error (+41.09%) are unchanged, while the label-1 and label-4 volumes swapped (0.530 and 2.166 mL) |
| Real-data recomputation | `glioma_ai.hpgs_cohort` read the companion checkout named in ignored `local/hpgs.json`: 50 UCSF-PDGM subjects, dataset reference segmentations versus the companion's SegResNet label maps, identical grids and labels {0, 1, 2, 4}. Recomputed Dice matched every per-subject companion record exactly (maximum difference 0), and median Dice agreed with the published 0.90/0.94/0.86 at two decimals. No inference was run |
| Published illustration | Notebook 01 displays the locally imported, hash-pinned Figure 4a–b asset unmodified, with its CC BY attribution |
| Python | `make check`: Ruff lint and format passed; **100 tests passed**, including the configured real-cohort test |
| Notebook 01 | Executed in the locked environment with no cell errors; the cohort figure and its runtime-generated caption displayed. The full `make notebooks` run was not repeated because the investigator's notebook 02 currently holds uncommitted review outputs |
| Manuscript | `make paper` built 24 pages with no LaTeX warnings or overfull boxes; the revised synthetic figure and caption on page 6 were inspected |

The real-data figure, its JSON record and caption values are written only to ignored `outputs/notebook_01/`, because UCSF-PDGM is distributed under a TCIA data-use agreement; tracked sources contain no per-subject values. (Corrected 13 October 2026: TCIA lists UCSF-PDGM under CC BY 4.0 with its Data Usage Policy, and the executed copy of 01 now shows the figure; see that entry.) The figure is not included in the paper or talk. Reference labels are the dataset's segmentations, not histological truth, and the RANO 2.0 volumetric thresholds (Wen et al. 2023, checked against the published text) are drawn for scale only.

## 10 October 2026: notebook 02 contribution record and controls caption

Executed on macOS ARM64 with CPython 3.12.14 and the existing locked CPU environment; no dependency changed.

| Check | Observed result |
| --- | --- |
| Controls figure | Panel letters A–F, a legend for the c = 0.1 and c = 0.5 contours, fixed control colours and a dotted "No change" curve so it remains visible where it coincides with another control. Simulated values are unchanged (final M 96.85, 123.95, 169.57 and 185.94 mm²; A(0.5) at day 28: 149, 0, 89 and 0 mm²) |
| Caption values | Taken from the regenerated run record; thresholded areas at day 28 (473, 221 and 89 mm² at θ = 0.1, 0.3 and 0.5) and the peak density (0.671) recomputed with `simulate_density_2d` |
| Literature comparison | Wang et al. 2009 (Cancer Res 69:9133, doi:10.1158/0008-5472.CAN-08-3863) read in full text: median ρ 15/yr, doubling times 1–87 days, D median 29.7 and range 3.2–468.9. The results text prints "mm²/d"; the model definition and survival table use mm²/yr, and only mm²/yr gives a front speed (≈ 42 mm/yr) consistent with the paper's reported velocities, so the notebook reads the values as mm²/yr and states this |
| Python | `make check`: Ruff lint and format passed; **100 tests passed** |
| Notebooks | `make notebooks` on the staged, output-free sources: 12 executed with no cell errors; 00 (hosted Colab) and 05 (absent clinical inputs) skipped. Jupyter execution used host access for local kernel sockets; the sandboxed attempt aborted |

`make paper` was not rerun: the manuscript does not include the controls figure. During this work `make clear-notebooks` was invoked with a file argument it does not accept and cleared the investigator's uncommitted outputs in notebooks 01 and 02; both working copies were restored from a fresh execution of the same sources, and notebook 01's uncommitted extra cell was kept.

Notebook 02 then gained a motivation section, at the investigator's request, framing serial boundary observation and the weather-forecasting analogy. Its citations were checked against primary sources by web search on 10 October 2026: Yankeelov et al. 2015 (Cancer Res, doi:10.1158/0008-5472.CAN-14-2233), GenCast (Price et al., Nature 2025, doi:10.1038/s41586-024-08252-9; abstract figures 15 days, 0.25°, 12-h steps, 97.2% of 1,320 targets), Aurora (Bodnar et al., Nature 2025, doi:10.1038/s41586-025-09005-y; tropical cyclone tracks up to 5 days against official forecasts) and WeatherNext 3 (arXiv:2609.03582, a preprint; hourly initialization from geostationary satellite data, 0.1° single-level output). The section labels AI-based tumor forecasting as speculation; no forecast is computed. The change is markdown only: on the staged output-free source, `make check` passed (100 tests) and `tests/test_notebook_validation.py` passed; `make notebooks` was not repeated because no code cell changed.

The investigator then drafted a sentence on treatment for the speculative-analogy paragraph; the assistant's revision of it was applied at the investigator's request. Its pseudoprogression statement was checked against RANO 2.0 (Wen et al. 2023, doi:10.1200/JCO.23.01059: pseudoprogression is frequent in the 12 weeks after radiotherapy, when a confirmation scan is required). Markdown only; `make check` and `tests/test_notebook_validation.py` passed on the staged output-free source.

## 10 October 2026: forecasting motivation and tumor–brain coupling in notebook, paper and talk

At the investigator's request, the forecasting motivation from notebook 02 and a new point on two-way tumor–brain interaction were carried into the paper and talk. Executed on macOS ARM64 with CPython 3.12.14 and the existing locked environment; no dependency changed.

| Check | Observed result |
| --- | --- |
| Notebook 02 | New paragraph "The brain is not a passive background" citing Venkatesh 2019, Osswald 2015, Krishna 2023 (worded as an association, matching the paper) and Zarodniuk 2026; DOIs taken from `paper/references.bib` or, for Zarodniuk, the checked slide source and PubMed Central record |
| Bibliography | Six entries added (Wang 2009, Yankeelov 2015, GenCast, Aurora, WeatherNext 3 preprint, Zarodniuk 2026); fields checked against publisher, PubMed Central or arXiv records and listed in `docs/bibliography-check.md` |
| Paper | Two motivating paragraphs open the reaction–diffusion subsection; the growth example now states that its figure is the compact demo construction and that notebook 02 extends it; the limitations add brain coupling, assimilation, ensembles and held-out validation. `make paper`: **26 pages**, all citations resolved, no LaTeX warnings; page 12 inspected |
| Talk | Backup slide 30 "Forecasting tumor growth, lessons from weather" with embedded notes; backup counts and index updated in the talk README, storyboard, speaking guide, rehearsal plan, README and perspective plan. Spoken slides and the 18:00 budget are unchanged. `make talk`: **30 pages**, no overfull boxes; slide 30 inspected |
| Python and notebook source | On the staged, output-free sources: `make check` passed (**100 tests**) and `tests/test_notebook_validation.py` passed; `make notebooks` was not repeated because no code cell changed |

The investigator's first `make talk-pptx` failed because the default `python3` was macOS's Python 3.9, which lacks `itertools.pairwise` and `pdfplumber`. The Codex authoring runtime was in fact installed under `~/.cache/codex-runtimes/codex-primary-runtime` (an earlier search had missed it). With its Node, Python 3.12, modules and presentations skill, `make talk-pptx` rebuilt the PDF and wrote `talk/slides.pptx`: **30 slides, 15 spoken + 15 hidden backups**, native tables on slides 5 and 24, Arial throughout. Package integrity and font policy passed; the layout validator repeated only the three known subscript-fragment overlaps on backup slide 26. The rendered slide 30 was inspected. The Makefile now defaults to that runtime when it is present.

Final artifact SHA-256 values:

- `paper/main.pdf`: `ab9f397e8e9de5d08b3494065de76766eea78fd09d5722f11e968c1c4be5db76`
- `talk/slides.pdf`: `03d737c438c4eb08184a174efe487176e9dd1f935e14c6b5ef0f0298f67acd7d`
- `talk/slides.pptx`: `c0dabfa87e9a3d5b74abfc6cf3320fd19edab872eb66a849697337b334469c7f`

## 10 October 2026: notebook 02 reference update

At the investigator's request, notebook 02 gained newer response-assessment frameworks, recent tumour-microtube and cancer-neuroscience evidence, and symbol definitions with references for the model. Citation fields were checked by web search against publisher, PubMed/Europe PMC or arXiv records on 10 October 2026:

| Topic | Sources added | Check |
| --- | --- | --- |
| Response assessment | PET RANO 1.0 (Albert et al. 2024, doi:10.1016/S1470-2045(23)00525-9); RANO/EANO PET update (Galldiks et al. 2025, doi:10.1016/S1470-2045(25)00193-7); RANO 2009–2025 progress report (van den Bent et al. 2025, doi:10.1093/neuonc/noaf118) | No RANO version after 2.0 was found; PET RANO 1.0 complements rather than replaces MRI RANO 2.0. The RANO resect and AI-RANO statements rest on the progress report's contents; the separate RANO resect paper was not cited because its record was not checked here |
| Tumour microtubes | Weil 2017, Venkataramani 2019, Venkataramani 2022, Hausmann 2023, Hai 2024; Smyth 2025 (intracellular microtubules, kept distinct) | DOIs, volumes and pages agreed across at least two records; claims follow the abstracts |
| Cancer neuroscience and fields | Taylor 2023, Winkler 2023, Monje 2025 (Neuron, doi:10.1016/j.neuron.2025.07.012), McAlpine 2026 and Pinotsis 2023 (already in the paper's bibliography), Pinotsis & Miller 2026 (Cereb Cortex, doi:10.1093/cercor/bhag098) | Claims follow the abstracts; the glioma relevance of field effects is stated as untested |
| Model symbols | Fisher 1937 (doi:10.1111/j.1469-1809.1937.tb02153.x); Kolmogorov, Petrovsky and Piskunov 1937 (no DOI, cited by name); Murray, Mathematical Biology II (doi:10.1007/b98869); Swanson, Alvord & Murray 2000 (doi:10.1046/j.1365-2184.2000.00177.x) | Fisher's page range differs between records, so it is cited by DOI only |

Markdown only. The new references are in notebook 02, not in the paper or talk.

### Carried into the paper and talk

The same references were added to `paper/references.bib` (47 entries, all cited) and to the paper: RANO context in the imaging-change section, cancer-neuroscience and tumor-microtube paragraphs, the Pinotsis & Miller 2026 result in the cytoelectric section, and the model's origin after Eq. (dynamics). In the talk, backup slides 17 (model sources), 21 (primary biological sources), 22 (fields and microtubes) and 30 (PET RANO 1.0) and their notes were updated; the slide count is unchanged. Notebook 02 now cites Swanson 2004 for treatment implications rather than grey/white migration.

- `make paper`: 26 pages, no undefined citations; SHA-256 `15d22de85045891be9077fe9f0d6e4cd9692e4ca1a10f2fc9b5f5dc87ae2c7be`.
- `make talk`: 30 pages, no overfull frames; slides 17, 21, 22 and 30 inspected as rendered images. SHA-256 `bfa55836c613f0f7a81f365e74e5ad10943e4772019709421561a4257f8a2666`.
- `make talk-pptx` (Codex runtime, macOS): 30 slides, 15 spoken, 15 hidden backups; package and font checks passed; layout warnings only the three known overlaps on slide 26; rendered slide 22 inspected. SHA-256 `0c9eb45cae0b8110a420d739077c5e441f58a1bd412e4ac4b6b649f13243c46c`.

## 10 October 2026: notebook 02 interactive explorers and Figure 2

At the investigator's request notebook 02 gained `ipywidgets` explorers for Figure 1 (D, rho, observation day, display threshold) and a new Section 7 with Figure 2: tissue-guided, axis-aligned anisotropic spread from a left parietal seed across the corpus callosum on a constructed coronal phantom, with its own explorer.

- Dependency: `uv add --group notebooks "ipywidgets>=8.1,<9"` added ipywidgets 8.1.9, jupyterlab-widgets 3.0.17 and widgetsnbextension 4.0.16 to `uv.lock`; no other package changed version.
- `tests/test_tissue_growth.py` (8 tests): midline connectivity only through left-right callosal fibres; seed in left parietal white matter; CSF fields zero; isotropic reduction (max difference 1.7e-16); no density in D = 0 cells and mass conserved on each side of a CSF wall; anisotropic cosine-mode RMS errors 2.9e-5, 7.3e-6, 1.8e-6 for 15, 30, 60 cells; rejection above the positivity limit; increasing contralateral share across the three scenarios; drawing helpers render without widgets.
- Figure 2 default run (macOS, CPU): first c ≥ 0.1 across the midline at day 190 (grey/white contrast) and day 170 (with fibre anisotropy), not reached in a year with uniform tissue; contralateral share at 365 days 15.1%, 24.3% and 0.07%. Three runs take about 0.6 s; the most demanding slider setting about 1.3 s.
- Headless execution of the output-free notebook with nbclient: all 23 cells ran in 6.9 s; both explorers stored a rendered PNG in their output widgets with no errors. Live slider interaction in a front end was not exercised.
- Figures inspected as rendered images: Figure 2 and both explorer layouts. The Figure 1 explorer uses a 121 × 121 mm plane and warns when density reaches the outer wall, after a first version on the 81 × 81 mm plane was seen to hit the wall at high D.
- Notebook 02 previously linked to `docs/tumor-growth-examples.md`, which does not exist; the link was removed there. Notebook 06 still contains it.
- On the staged, output-free tree: `make check` passed (108 tests) and `make notebooks` executed 01–04 and 06–13, including 02, with 00 and 05 skipped for their documented reasons.

### Follow-up: play buttons and a five-control animation

Both explorers gained a play button linked to the day slider (700 ms and 900 ms per step), and the Section 4 animation now plays all five controls side by side with M in each title, replacing the single reaction + diffusion run; the snapshot file stores all five runs. `density_animation` is kept for notebook 06. Two tests added (frame count of the animation; the play button's range and step, skipped without ipywidgets). Headless execution of the output-free notebook: all cells ran in 7.5 s; the animation has 15 frames (1.8 MB of HTML), and its final frame was inspected. The play buttons were not pressed in a live front end.
- On the staged tree: `make check` passed (110 tests) and `make notebooks` executed all notebooks except 00 and 05 (documented skips).

## 10 October 2026: executed-notebook export and public release checklist

Added `make executed-notebooks` (`scripts/export_executed_notebooks.py`), which exports only the synthetic notebooks 01–04 and 07–11 from a passed `make notebooks` run to ignored `outputs/executed-notebooks/`, removes per-cell execution timestamps and refuses outputs containing local paths. No executed notebook is tracked. `docs/public-release.md` lists the steps for the planned public snapshot; none has been carried out.

- `tests/test_export_notebooks.py` (8 tests): 00, 05, 06, 12 and 13 are refused; every notebook in `notebooks/` is classified as exported or excluded; timestamps are removed and outputs kept; outputs with a local path, or from a failed run, are refused.
- Notebooks 08 and 09 wrote to `outputs/...` relative to the working directory, so runs started from `notebooks/` produced 15 tracked files under `notebooks/outputs/` (since `14879bf`). Both now resolve the repository root; `/notebooks/outputs/` is ignored and the files were removed from the index.
- On the staged tree (macOS, CPU), with the investigator's notebook 01/02 outputs stashed: `make check` passed (118 tests); `make executed-notebooks` executed all notebooks except 00 and 05 (documented skips) and exported the nine synthetic notebooks (5.8 MB in total). A search of the exports for local paths, the user name and the host name found only public GitHub links in notebook text.
- Not checked: rendering of the exports on GitHub or nbviewer (the repository is private).

### Tracked executed copy of notebook 02

At the investigator's request, `notebooks/executed/02_tumor_dynamics.ipynb` is tracked (exception recorded in `AGENTS.md`) so that the static figures can be read on GitHub. `make executed-notebooks` now also writes it. A new test requires that only this notebook is in `notebooks/executed/`, that its cell sources equal the output-free notebook 02, and that it has outputs, no execution timestamps and no local paths.

- On the staged tree (macOS, CPU), with the investigator's notebook 01/02 outputs stashed: `make executed-notebooks` executed all notebooks except 00 and 05 (documented skips) and wrote the tracked copy (3.7 MB); `make check` passed (119 tests).
- The copy contains PNG outputs for Figure 1 and Figure 2, printed checks, an HTML/JavaScript animation and two widget outputs. GitHub's static renderer is expected to show the PNGs and text only; rendering on GitHub was not yet inspected.

## 10 October 2026: notebook 14, network disconnection

New synthetic notebook `14_network_disconnection.ipynb` with `glioma_ai.network` and `glioma_ai.network_figures`: 14 grey-matter regions on the notebook 02 phantom, shortest white-matter paths as tract proxies, weights exp(−L/40 mm), tract damage from the tissue-guided density proxy (integrity exp(−Σc Δs / 10 mm); cut through a resection cavity), a constructed left-hemisphere resection at day 120 sparing the corpus callosum, and a linear noise-driven network with exact functional connectivity. No new dependency (path search in plain Python; covariance by matrix inversion).

- `tests/test_network.py` (9 tests): regions non-empty and on their own side; all pairs reachable; no path through CSF or other grey matter; every interhemispheric path crosses the corpus callosum; integrity 1 without tumour and never higher for a pointwise larger density (both damage rules); spectral radius never above the healthy value; callosum-sparing control never below the full lesion; exact covariance (Lyapunov residual below 1e-12), identity correlation at g = 0, rejection of unstable coupling; time-step bias ratio between 0.4 and 0.6 per halving and sampling error falling with duration; cavity confined to left non-callosal white matter; figures render and the record is written.
- A first damage rule, 1 − max c, was replaced as default after it made the callosum-sparing control identical to the full lesion at day 240 (saturated hemispheric segments already cut the tracts); it remains available as `rule="max"`. A first test assumed integrity falls monotonically in time; that is false (diffusion lowers the seed centre early), so the test compares pointwise larger densities instead.
- Default results (macOS, CPU), day 180: interhemispheric structural weight 89.1%, 58.9% and 52.0% of healthy for the three notebook 02 scenarios, 59.7% with the callosum assumed uninvolved; resection at day 120 (cavity 763 mm²) lowers it from 82.2% to 75.4%. Euler–Maruyama step bias 0.0285, 0.0137, 0.0067, 0.0033 for dt = 0.2, 0.1, 0.05, 0.025 τ; sampling RMS error 0.0267, 0.0135, 0.0109 for 1000, 4000, 16000 τ (one realisation each).
- Notebook executed headlessly with nbclient in 6.4 s; both figures inspected as rendered images. The explorer was not exercised in a live front end.
- References checked against Crossref and PubMed abstracts (`docs/bibliography-check.md`). The CANTAB region table is an assumption without sources.
- Notebook 14 added to the synthetic export allowlist.
- Export reproducibility: regenerating `notebooks/executed/02_tumor_dynamics.ipynb` changed about 1,300 lines each time because widget model IDs and Matplotlib animation element IDs are random UUID4 strings. `strip_volatile` now renumbers them in a structural order (cell outputs first, then widget references), leaving SHA-256 hashes untouched; two independent executions of the committed notebook 02 then produced byte-identical exports. The tracked copy was regenerated once with the new numbering. The freshness test now ignores trailing empty cells, which editors add to working copies.
- On the staged tree (macOS, CPU), with the investigator's notebook 01–03 outputs stashed: `make check` passed (129 tests); `make executed-notebooks` executed all notebooks except 00 and 05 (documented skips), including 14, and exported the ten synthetic notebooks.

## 10 October 2026: notebook 14b, one patient's connectome (real data)

New real-data companion `14b_patient_connectome.ipynb` with `glioma_ai.connectome` and `glioma_ai.connectome_figures`, reading investigator-authorized, CC0-derived sub-PAT16 matrices tracked in `data/derived/sub-PAT16/` (Brain Tumor Connectomics, OpenNeuro ds001226 v5.0.0 / ds002080 v4.0.0). No new dependency.

- Upstream inspection: the investigator's `glioma-brain-digital-twin` derivatives were read in place. Their QC checklist has 0 of 37 items checked. The upstream structural matrices (`sc_sift2`, 2035 × 2035) used every `aparc+aseg` label as a node, so only 14.5% of SIFT2 weight joined the 82 grey-matter regions; the 83 × 83 `sc_dk84` has no documented node order and was not used.
- Derivation (`make pat16-connectome`, macOS, CPU, 152 s): the installed MRtrix3 binaries could not run (missing Homebrew FFTW library), so endpoints were assigned in Python: memory-mapped `.tck` reading, region containing the endpoint or nearest region voxel centre within 4 mm. Check against MRtrix3: rebuilding the upstream all-label matrices gave edge correlations 0.99996 (pre-op) and 0.99987 (post-op) with `tck2connectome`, totals within 0.11% and 0.003%. With 82 region nodes, 41.4% (pre-op) and 43.0% (post-op) of SIFT2 weight joins regions. Upstream FC equals the correlation of its cleaned time series (157 and 160 of 180 volumes) to 1e-15. 9.1% of pre-op streamlines pass through the 53.3 mL TumorSynth mask (10.6% of between-region weight). The derivation script was afterwards changed only in line wrapping.
- `tests/test_connectome.py` (8 tests): region table order; relabelling and the 4 mm nearest-label radius; voxel lookup outside the grid and for NaN; the `.tck` reader against nibabel across chunk boundaries, with mask hits; symmetric connectome without unassigned or self pairs; SIFT2 weight parsing; tracked files match their provenance hashes, provenance has no local paths, tumour weight never exceeds pre-op weight; virtual resection bounds and reproducible nulls. The export classification test now lists 14b as excluded.
- Results (descriptive, one patient): model–measured FC agreement over 3,321 pairs 0.113 (pre-op) and 0.297 (post-op) at g = 0.8, best at the smallest g and equal to the direct log-SC–FC correlation (0.184, 0.295); pre-op shuffled-region null 97.5th percentile 0.113. Connections with ≥ 75% of pre-op weight through the tumour mask changed by a median log2 −0.25 (228 pairs with weight ≥ 10). Predicted FC change from the virtual resection correlated −0.145 with measured change (placement null median −0.09, 97.5th percentile −0.068); measured change correlated −0.205 with pre-op FC; after regressing pre-op FC, −0.113; prediction from the measured post-op SC 0.044.
- Figures inspected as rendered images; the model-FC panel was given its own colour scale after the shared ±1 scale hid it.
- References checked against Crossref (`docs/bibliography-check.md`).
- Not done: upstream QC review; mapping the post-operative cavity to pre-operative space; repeat-scan or multi-patient comparison; MRtrix3 itself was not rerun.
- On the staged tree (macOS, CPU), with the investigator's notebook 01–03 and 14 outputs stashed: `make check` passed (138 tests); `make notebooks` executed all notebooks except 00 and 05 (documented skips), including 14b, whose CANTAB branch ran with the local inputs of notebook 13 and printed the same source-verified values.

## 10 October 2026: notebooks 03–05 retired, remaining notebooks renumbered

At the investigator's request, the notebooks on fabricated clinical rows and report sentences (former 03), NIfTI units and geometry (former 04) and optional CGGA/TCGA records (former 05) were removed. The former 04's check (moving only the affine of a copy must make the comparison fail) is now a section of notebook 01. The paper's appendix section "Additional clinical-record exercises" and its figure were removed, and `glioma_ai.demo` no longer writes `clinical_evidence.*`, `synthetic_clinical.tsv` or the `ExampleEligible` value. The CGGA and TCGA readers, their command-line entries and their tests are unchanged. The remaining notebooks were renumbered (06→03, 07→04, 08→05, 09→06, 10→07, 11→08, 12→09, 13→10, 14→11, 14b→11b; mapping in `notebooks/README.md`). Entries above this one, the assistance records in `docs/ai-use/` and `docs/ai-records/`, and executed outputs written before this date keep the old numbers.

- On the staged tree (macOS, CPU), with the investigator's executed outputs in notebooks 01, 02, 03, 11 and 11b stashed: `make check` passed (137 tests; the demo test no longer checks the removed clinical example). `make executed-notebooks` executed every notebook except 00 (documented skip), including 03 with the investigator's local `local/lumiere-case.json`, and exported the eight synthetic notebooks; the folded check printed the expected geometry refusal. The tracked copy of notebook 02 changed only in renumbered references and the order of normalised widget IDs. `make paper` built a 25-page PDF without undefined references.
- Not rebuilt: `talk/slides.pdf` and `talk/slides.pptx` (only speaker notes in `talk/slides.tex` changed) and the investigator's external presentation, which may cite old numbers. The hosted Colab run recorded above predates the renumbering and was not repeated.

## 10 October 2026: didactic notebooks 04–10 with interactive explorers

At the investigator's request, notebooks 04–10 were expanded with an extensive introduction modelled on notebook 01, derivations, exercises and ipywidgets explorers (record: `docs/ai-use/2026-10-10-didactic-notebooks-04-10.md`). New package code and tests: `glioma_ai.notebook_display`; `glioma_ai.assistance_interactive` (6 tests); `well_mixed_neuron_glioma` and `glioma_ai.biology_interactive` (7); `glioma_ai.neuroglial_interactive` with two new `neuroglial` functions (7); `hausdorff95_mm` and `surface_points_mm` in `glioma_ai.metrics` and `glioma_ai.imaging_interactive` (6); `precision_interval`, `reliable_change_index` and `glioma_ai.cantab_interactive` (5).

- Checks against independent results: the well-mixed RK4 model against the exact logistic solutions (relative 1e-9) and the exponential signal relaxation (absolute 2e-6); the niche landmarks against the package solver; potassium pulse landmarks and the Nernst slope against closed forms; the field-sampling error against σ/(√2 Δx) at fine spacing (within 15%); HD95 on discs against analytic shifts and dilations, with single slices treated as 2D; the reliable change index against a hand calculation. In notebook 04 each constructed bug fails the check designed to catch it and passes at least one other.
- HD95 convention: 6-connected surface voxels in millimetres, larger of the two directed 95th percentiles; empty masks raise. Published HD95 values in notebook 09 may use other conventions and are not recomputed.
- On the staged tree (macOS 27.0.1, arm64, CPU): `make check` passed (165 tests, 3 skipped). `make executed-notebooks` executed every notebook; 00 (hosted Colab) and 03 took their documented skips. The tracked copy of notebook 02 differed only in the order of two normalised widget IDs and was not updated. *Corrected later the same day:* this bullet first said that the investigator's `local/`, `data/cantab/` and `paper/generated/` were linked in and that notebook 10's empirical cells ran with the local CANTAB inputs. The relative links pointed one directory too high, so none of these inputs were present: the 3 skipped tests and the skip of 03 follow from that, and notebook 10 ran only its missing-input branch. The rerun in the next entries used working links.
- Ruff lints notebooks; the first full `make check` found six line-length and unused-name findings in notebooks 05, 08, 09 and 10 that per-file checks had missed, fixed before the passing run.
- Intermittent headless stall: during development, nbclient runs occasionally received no reply to a cell, usually the first code cell after an explorer, while the kernel sat idle. Rates varied between batches (0 to 75%) and clustered in time; the cause was not found (not cell IDs, IPython directory or transport). nbclient can then wait without a timeout. The final `make executed-notebooks` run above did not stall. If a run hangs, interrupt and rerun.
- Explorers were exercised only headlessly: their pure scenario and drawing functions are tested, and executed notebooks capture the initial state. Sliders were not moved by hand in JupyterLab, VS Code or Colab.
- Two new references checked against Crossref (`docs/bibliography-check.md`).
- Rebuilding the notebooks overwrote the investigator's executed working copies of 04, 05, 06, 09 and 10; their uncommitted changes were outputs and empty cells only.
- Not rebuilt: `make paper` (manuscript evidence unchanged), talk exports, hosted Colab.

## 10 October 2026: notebook 00 outside Colab

At the investigator's request, notebook 00 no longer raises an error when opened outside hosted Colab. Its first code cell sets `IN_COLAB` from whether `google.colab` imports; outside Colab it prints what to run locally, and every later code cell prints a skip notice instead of working. The Colab steps are unchanged apart from being indented under the check, and the final metrics are shown with `display`. Executed locally with nbclient (macOS, CPU): all cells completed with the expected notices and no error. Ruff passed. The Colab branch was not rerun in hosted Colab.

## 10 October 2026: notebook 11b renamed 12; executed notebooks 01–12 tracked

At the investigator's request, `11b_patient_connectome.ipynb` is now `12_patient_connectome.ipynb` (its output folder `outputs/notebook12/`), and executed copies of notebooks 01–12 are tracked in `notebooks/executed/` so that GitHub shows their figures (exception updated in `AGENTS.md`). Before deciding, the investigator asked whether 03, 09 and 10 had to stay out of a public release. Checked sources: the published segmentation article and the CANTAB OSF release are CC BY 4.0 (`docs/bibliography-check.md`); sub-PAT16 is CC0; the LUMIERE files on Figshare are each labelled CC0 (Figshare API, 10 October 2026), but the Scientific Data article's Usage Notes and the authors' GitHub README restrict use to non-commercial purposes. Notebook 03 now states that condition and that its slices are not covered by the MIT licence; notebook 10 states the CC BY licence; 09 and 12 already carried attribution.

- `scripts/export_executed_notebooks.py` exports 01–12 (never 00) to `notebooks/executed/` and, in addition to the existing checks for passed runs and local paths, refuses outputs containing the missing-input notices of 09, 10 and 12, so tracked figures cannot be replaced by notices. Notebook 03 printed absolute paths of its slice bundle, which the exporter refused; it now prints repository-relative paths. Tests: notebook 00 is refused, every notebook is classified, runs without inputs are refused, and every tracked executed copy matches its source and contains no missing-input notice.
- Stale number prefixes were removed from the titles of 02, 03 ("06 —"), 11 ("14 —") and 12 ("14b —"); the investigator had already removed the last two in a working copy.
- On the staged tree (macOS 27.0.1, arm64, CPU), with the investigator's `local/`, `data/cantab/` and `paper/generated/` linked by absolute paths: `make executed-notebooks` executed every notebook except 00 (documented skip), including 03 with the prepared LUMIERE inputs, 09 with the imported published figures and 10 and 12 with the local CANTAB inputs, and exported 01–12 (14 MB in total, no error outputs). `make check` then passed (165 tests, none skipped). Outputs were searched for user names and identifiers: only links to the investigator's public companion repository and notebook 12's public subject ID occur; notebook 10's outputs contain no case ID.
- Not rendered on GitHub yet; static rendering does not play animations or explorers. `make paper` not run (manuscript evidence unchanged); hosted Colab not rerun.

## 10 October 2026: documentation, paper and talk audit after tracking executed notebooks

At the investigator's request, READMEs, documentation, the paper and the talk were searched for stale notebook numbers and for statements made obsolete by the tracked executed notebooks. Updated: `CONTRIBUTING.md` and `README.md` (executed copies; explorers in 02 and 04–11), `docs/ai-workflow.md` and `docs/cantab-example.md` (the verified case's released values appear in the tracked paper and executed notebook 10; local linking information, the session table, IDs and dates stay local), and the paper's reproduction appendix (notebooks 11 and 12 described; the hosted Colab run recorded above replaces "remains unverified"; executed copies tracked). `notebooks/executed/` is marked `export-ignore` in `.gitattributes`, so `make colab-bundle`'s `git archive` keeps the source ZIP free of executed outputs, as notebook 00 and `docs/reproducibility.md` state; `git archive --worktree-attributes HEAD` listed no file from that folder. The teaching routes in `README.md`, `docs/perspective-plan.md` and the paper still omit 11 and 12 (the notebook map includes them); left as a scope decision.

- `make paper` (macOS, local TeX Live, illustrated variant with the investigator's local figure inputs): 25 pages, no undefined references; the new appendix text was confirmed in the PDF text.
- `make talk-pptx` rebuilt `talk/slides.pdf` (30 pages) and `talk/slides.pptx` (30 slides, 15 spoken, 15 hidden backups). This also carries the speaker-note corrections of the renumbering commit, whose exports had not been rebuilt; the PPTX notes now cite notebooks 04, 05 and 07 correctly. The PPTX was not opened in PowerPoint.
- Follow-up at the investigator's request: notebooks 11 and 12 added to the teaching routes in `README.md`, `docs/perspective-plan.md` and the paper appendix (now 04, 09, 01, 05, 07, 08, 02, 11, 12, 06, 10, as in the notebook map). `make paper` rebuilt 25 pages without undefined references. The talk has no route and was not rebuilt.

## 12 October 2026: notebook 03 use case, released metadata, results and limitations

At the investigator's request, notebook 03 now introduces and motivates the LUMIERE Patient-048 use case, shows the patient's released metadata, states the task, assumptions and tools, and reports results, interpretation, and strengths and weaknesses (`docs/ai-use/2026-10-12-notebook-03-use-case.md`). The investigator chose to show all released metadata after asking whether this is consistent with the dataset's terms; the exception is recorded in `AGENTS.md`.

- `make lumiere-metadata LUMIERE_DIR=...` read the four released CSV tables in place and wrote `src/glioma_ai/references/lumiere_p048.json` (6 visits, SHA-256 of each table, no local path); a second run reproduced the file byte for byte. Four new tests cover parsing of synthetic tables, refusal of missing tables or patients, nominal days, and agreement of the tracked visits and ratings with `lumiere_slice.VISITS`.
- On the staged tree (macOS 27.0.1, arm64, CPU), with the investigator's `local/`, `data/cantab/` and `paper/generated/` linked by absolute paths: `make notebooks` executed 01–12 (00 skipped as documented), including 03 with the prepared LUMIERE inputs. The results cell's asserts held: core area 840 → 1394 mm² (+66%), whole union 1342 → 2759 mm²; default model 803 mm², Dice 0.718 against no change 0.731; reaction only equal to no change; 577 mm² (41%) of the later core outside the week-045 seed; grid areas 196–1712 mm², Dice 0.247–0.766, smallest missed area 262 mm². The executed copy of 03 was exported with `scripts/export_executed_notebooks.py` (only 03; the other executed copies are unchanged) and contains no local path. `make check` then passed (169 tests).
- The exporter's missing-input notices do not include notebook 03's "Real-data example not run" message; the run used the real inputs, which was checked in the outputs. Not changed here.
- `make paper` not run (manuscript evidence unchanged). Hosted Colab not rerun; notebook 03 needs local inputs there as before. The interpretation, explanations and strengths and weaknesses await investigator review.
- Correction prompted by the investigator: the notebook stated that no exact perioperative interval exists in the release. Fig. 2 of Suter et al. (2022) labels the post-operative scan of its example patient "3 days"; its caption does not name the patient, but the six visits and ratings match Patient-048 exactly (fetched 12 October 2026). The notebook now says so and marks the identity as inferred; the `lumiere_slice.VISITS` comment cites the figure for day 3 (unchanged value, so no result changed). The interpretation also quotes the caption's "a very fast growth rate". Notebooks rerun on the staged tree (01–12 executed), executed copy of 03 re-exported, `make check` rerun.

## 12 October 2026: notebook 03 biologically informed revision

At the investigator's request, following the assistant's recommendation, notebook 03 keeps its baseline (sections 5–7) and adds a revision (section 8) and a labelled fit (section 9); later sections are renumbered 10–14. `glioma_ai.lumiere_biology` implements a two-level start and reading (core label read as T1Gd at 80% and whole union as T2/FLAIR at 16% of maximum density, after Swanson et al. 2008; starting levels 0.9 and 0.36 are assumptions), the registered skull-stripped week-045 CT1 support as brain domain (11 labelled cells outside it are added), local/distant scoring by in-plane components of the week-049 whole union, published median coefficients (Wang et al. 2009: D 29.7 mm²/year, ρ 15/year), and a calibration grid. `simulate_density_2d` and `fisher_step_2d` gained an optional boolean `domain` that closes faces at its boundary. Both sources were checked against the articles (`docs/bibliography-check.md`); Wang et al. state D in mm²/year in the Methods and Table 2, while one results sentence says mm²/day, which would imply front speeds near 800 mm/year.

- Seven new tests: no flux crosses a domain boundary and the balance holds; domain validation; unit conversion and front scales; component labelling and the local/distant split; reading-threshold bounds; scoring and refusal of a perioperative start; grid bookkeeping. Existing solver tests pass unchanged.
- On the staged tree (macOS 27.0.1, arm64, CPU) with the investigator's local inputs linked: `make notebooks` executed 01–12 (00 skipped as documented). Notebook 03 results, all asserted in code: the week-049 plane has one local and one distant component (distant 665 mm², 24% of the whole union); published medians give local core/T2-FLAIR Dice 0.752/0.815 against 0.761/0.755 for no change, and 0.771 local score without the brain domain against 0.784 with it; their front speed 0.116 mm/day is below the observed local core expansion of 0.145 mm/day; the best of 121 grid cells (D 0.251 mm²/day, ρ 0.106 day⁻¹, local score 0.841) is an in-sample fit; the score varies by 0.038 along D and 0.140 along ρ, and lowering the margin level to 0.2 raises the best ρ to 0.153 day⁻¹. The executed copy of 03 was re-exported (2.8 MB, no local path).
- The assistant had predicted that one interval would mainly identify the front speed; the grid showed instead that it mainly identifies ρ, conditional on the margin assumption. The notebook reports the observed result.
- The stale link to `docs/tumor-growth-examples.md` in notebook 03 now points to notebook 02. `README.md` and `notebooks/README.md` describe the revision.
- `make paper` not run: the manuscript uses the baseline assets, which are unchanged. Hosted Colab not rerun. The cavity barrier and white-matter weighting (step 3 of the plan) and the interactive explorer (step 2) are not done.

## 12 October 2026: notebook 03 what-if explorer

At the investigator's request, notebook 03 gained section 10, an `ipywidgets` explorer in `glioma_ai.lumiere_interactive` (later sections renumbered 11–15). Tabs: spatial (plane offset ±10 mm, only with the local prepared volumes; week-045 label-boundary shift ±3 mm by 4-neighbour growth or erosion), temporal (observation day 0–112 with a play button; only day 28 has a scan, later days are drawn as projections), tissue (brain domain on/off; a what-if factor for D inside the T2/FLAIR-abnormal region; white-matter guidance not offered because LUMIERE has no tissue segmentation), and model (logarithmic D and ρ with presets for the published medians, the baseline coefficients and the section-9 fit; starting densities; reading thresholds; invalid combinations refused). The time step is reduced automatically to 0.9 of the stability bound when D is large. `score_density` gained explicit threshold arguments.

- Five new tests: mask growth and erosion; defaults reproduce section 8 at day 28; settings change the run, keep the balance and are validated; drawing at observed and projected days; the explorer builds with ipywidgets (176 → 181 tests with the previous entry's).
- Locally (macOS 27.0.1, arm64, CPU): one run takes about 0.25 s (0.9 s at D = 1 mm²/day with a factor of 4); loading another plane took 0.1 s. Default, fitted, day-28 and day-84 views inspected as rendered images; the legend was moved after it covered the week-049 marker.
- `make notebooks` on the staged tree executed 01–12; the explorer's output widget stored its initial figure and the static preview shows days 28 and 84 (asserted equal to section 8 at day 28). The executed copy of 03 was re-exported without local paths. Sliders were not moved by hand in a live front end.

## 12 October 2026: LUMIERE download route and notebook 03 in 3D

At the investigator's request, notebook 03 gained section 11, the section-8 model in 3D with an explicit tissue map (later sections renumbered 12–16), and the download route of the Patient-048 inputs was examined.

- Download. The Figshare API lists the LUMIERE images as one 32,565,467,707-byte archive (`Imaging-v202211.zip`, article 21249516, labelled CC0; the authors' non-commercial condition applies). Its storage server answered byte-range requests with 206 Partial Content, so `glioma_ai.lumiere_fetch` reads the ZIP's central directory and only the selected members. The table of contents (31,370 entries) took 5 requests and 3.5 s; Patient-048 has 240 files (220 MB compressed). The 36 files that the companion repository stages were pinned by size, CRC-32 and SHA-256 in `src/glioma_ai/references/lumiere_imaging_p048.json` (37.7 MB). All 36 were byte-identical to the copies staged from the investigator's local LUMIERE folder. `make lumiere-fetch` downloaded them into ignored `data/lumiere/` in 87 s with 41 range requests; a second run downloaded nothing. The companion repository's `data/` README states that it commits no binary data; its registration, MONAI labels and FreeSurfer parcellations are local derivatives and cannot be downloaded. Four offline tests use an in-memory archive (selection, verified writing and idempotence, refusal of changed local or remote files, the pinned selection).
- 3D solver. `glioma_ai.growth_volume.simulate_density_3d` uses the scheme of the 2D solver (exact half reaction, conservative explicit diffusion, exact half reaction) with an optional no-flux domain. Five tests: exact logistic growth for a uniform field, mass conservation to 1e-12 in a closed domain, symmetry under axis permutation and reflection, agreement with `simulate_density_2d` to 1e-6 for a density constant along one axis, and enforcement of the stability bound and the domain contract.
- 3D case. `glioma_ai.lumiere_volume` reads weeks 045 and 049 from the prepared grid (geometry, label scheme and hashes checked as in 2D), crops to the week-045 whole-tumour box plus 25 mm (120 × 104 × 133 voxels), and finds week-049 local and distant lesions as 6-connected components on the full volume. The optional tissue map is the FreeSurfer 8.2.0 `wmparc` computed upstream on the registered week-045 T1 (same grid; checked). Its labels are grouped into CSF, grey and white matter by explicit tables; all labels present were covered. $D_\text{white} = 5 D_\text{grey}$ follows Swanson et al. (2000), checked in the full text, with the domain mean kept at the published median. Six tests on a synthetic prepared grid.
- On the staged tree (macOS 27.0.1, arm64, CPU) with the investigator's local inputs linked: `make notebooks` executed 01–12 (00 skipped as documented). Section 11 results, asserted in code:
  - Observed: whole union 27.6 → 100.0 cm³ (×3.6, against ×2.1 in area on the section-8 plane); core 15.2 → 35.0 cm³. One local component of 75.9 cm³ and 14 distant components (24.0 cm³; the largest 22.4 cm³). The section-8 plane's distant lesion is not part of the 3D local component.
  - Model, as local score: no change 0.580; published medians 0.606 (T2/FLAIR reading 37.4 cm³); CSF closed 0.612; 5:1 white/grey 0.611; the section-9 fit carried into 3D 0.714 (57.8 cm³); the fit with tissue 0.697.
  - 20% of the week-049 local labels lie outside FreeSurfer grey and white matter (7,768 voxels CSF, 7,641 unclassified).
  - Density on the crop faces at most 1.5e-9; balance residual at most 1.1e-11 mm³. The six 3D runs took about 8 s together.
  - The executed copy of 03 was re-exported (4.4 MB, no local path), and `make check` passed (196 tests).
- Not done: a volume fit (the one-interval identifiability limits of section 9 apply), a cavity mask, fibre anisotropy, mass effect, and a 3D explorer. FreeSurfer's classes near the lesion and the registration were not reviewed. `make paper` not run (manuscript evidence unchanged); hosted Colab not rerun (section 11 needs local volumes).

## 12 October 2026: release archive of the prepared Patient-048 inputs

At the investigator's request, the derived files notebook 03 reads were packed into a release archive outside Git, and the planned public repository was created privately to hold it.

- Build. `glioma_ai.lumiere_bundle.build_bundle` (`make lumiere-bundle`, `scripts/build_lumiere_bundle.py`) selected 27 files from the investigator's prepared root (`high-precision-glioma-segmentation/data/lumiere_p048`): per visit the registered CT1, MONAI labels, label record and registration QC record; for week 045 the FreeSurfer `wmparc` map, lookup table and record. The 9 NIfTI files are byte-identical; the 18 JSON records were rewritten, and every absolute path in them lay inside the prepared root and became relative. A text search of the extracted archive (records and NIfTI headers) found no user name, `/Users`, Dropbox or other host path. Two builds gave the same archive (25,933,130 bytes, SHA-256 `61d0a6b4de51083575473fe3ae3460093668c99fccc67c23458e587acf59faa8`), pinned in `src/glioma_ai/references/lumiere_bundle_p048.json`.
- Equivalence. Loaded from the extracted archive and from the original prepared root, the section-3 plane (index 181), the images and labels of all visits and the 3D tissue map were identical arrays; the section-8 local score (0.7837) and the 3D 5:1 tissue score (0.6113) were equal to all printed digits. `make notebooks` on the staged tree with `LUMIERE_P048_ROOT` pointing at the extracted archive executed 01–12, and the text outputs of 03 were identical to the tracked executed copy.
- Release. `gh repo create arvidl/AI-assisted-glioma-research --private` with one commit (README and the MIT `LICENSE` of this repository), then release `lumiere-p048-prepared-v1` with the archive; GitHub reported the same SHA-256 for the asset. `glioma-ai lumiere-bundle-fetch --use-gh` into a fresh folder downloaded, checked the pin, extracted and verified 27 files; a second run downloaded nothing. The anonymous download URL returned 404 while the repository is private; the fetch then stops with a message naming `--use-gh` and `--zip`.
- Five offline tests on a synthetic prepared root: deterministic build and path cleaning, refusal of missing inputs, fetch from a local archive that verifies, extracts, loads with `prepare_slice_case`, is idempotent and detects a changed file, refusal of an archive that differs from the pin, and the pinned reference. `make check` passed (201 tests).
- Not done: the anonymous route (after the repository is made public), hosted Colab, and a review of the archive README by the investigator. The `AGENTS.md` exception for the release asset is drafted for the investigator's approval, not applied.

## 12 October 2026: Colab setup in notebooks 01–03 (simulated, not hosted)

The investigator approved the drafted `AGENTS.md` exception for the release asset, and it was applied. At the investigator's request, notebooks 01–03 gained a Colab branch in their first code cell: when `google.colab` imports and no repository is found, the cell clones `arvidl/AI-assisted-glioma-research` (depth 1) to `/content/AI-assisted-glioma-research`, installs nibabel if missing, changes into the checkout and puts its `src/` on the path; Colab's own NumPy, Matplotlib and ipywidgets are used, not `uv.lock`. Notebook 03 gained a Colab-only cell that fetches and verifies the released archive and sets `LUMIERE_P048_ROOT`; outside Colab it changes nothing. Its title no longer says that it never downloads data.

- Simulation on macOS (arm64): a fresh Python 3.12 environment without `glioma_ai` or nibabel, with NumPy 2.0.2, Matplotlib 3.11.2 and ipywidgets 7.7.1, a stand-in `google.colab` module, the staged tree placed where the clone would go, and a working directory outside any repository. 01 and 02 executed; 03 executed with the real (private) release URL and reported that its inputs were not fetched (404); 03 with the local archive substituted for the download verified 27 files and executed every section, with text outputs identical to the tracked executed copy apart from three balance residuals (order 1e-13 mm² and 1e-11 mm³).
- The simulation found two faults, now fixed: the path inserted for `src/` was not resolved, so on a symlinked directory the package's paths fell outside the repository root (on macOS `/tmp`; not known to occur at `/content`); and `fetch_bundle` returned fewer fields when the archive was already extracted, which broke a rerun of the Colab cell (test extended).
- On the staged tree with the investigator's inputs linked: `make notebooks` executed 01–12 (00 skipped as documented); executed copies of 01–03 were re-exported; `make check` passed (201 tests).
- Not done: hosted Colab. The clone needs the code in the public repository, and the anonymous release download needs that repository to be public. Widgets were not moved by hand; the git clone itself was not exercised (the checkout was pre-placed).

## 12 October 2026: stage-1 public snapshot (local, not pushed)

At the investigator's request, `scripts/public_snapshot.py` wrote committed revision `199890ab8977` into the investigator's local clone of `arvidl/AI-assisted-glioma-research` (a sibling folder of this repository): 147 files, comprising the full `glioma_ai` package, all tests, the notebook scripts, notebooks 00–03 with executed copies of 01–03, `docs/` except the manuscript plan and the internal release checklist, and public versions of the README, notebook map, CI workflow (without the manuscript job) and notebook 00 (clone instead of source-ZIP upload) from `public/`. Held back: notebooks 04–12, `paper/`, `talk/`, `data/derived/sub-PAT16/`, `.cursor/`, `AGENTS.md` and the talk and Colab-ZIP scripts; the Makefile loses the targets that need them.

- The script refused the first attempt on four local-path matches; all four were detector patterns or fabricated test paths, now allowed by exact file and match. No data file or file over 6 MB was present.
- In the clone (macOS 27.0.1, arm64): `uv sync --locked --group notebooks`; `make check` gave 196 passed and 5 skipped (the two sub-PAT16 tests, which now skip when those matrices are absent, and three tests needing the investigator's local data); `make notebooks` with `LUMIERE_P048_ROOT` set to the extracted release archive executed 01–03, and the text outputs of 03 equalled the tracked executed copy. Committed locally in the clone as one commit; not pushed.
- Reported, not fixed: links in executed copies (`notebooks/executed/`) use `../docs/...`, which resolves one folder too high on GitHub; this also holds in this repository. Public notebook 00 has not been run in hosted Colab.

## 12 October 2026: notebook 03 section 12 animation and in-place explorer display

The investigator asked whether section 12 was didactic enough for animation in time, asked for an MP4 or GIF suitable for slides, and reported that the section-10 explorer's figure appeared three times in Cursor. Section 12's player (baseline model, density on black, image-plane axes, no anatomy or labels) was replaced by `glioma_ai.lumiere_movie`. It animates the section-8 model daily over days 0–56 on the week-045 CT1, with dashed week-049 labels, the distant lesion marked, and the core and T2/FLAIR readings drawn progressively against the labelled areas, each frame carrying a source and condition footer. `write_growth_movie` writes a looping GIF (Pillow) and an H.264 MP4 (ffmpeg, if installed) at 1280 × 720 pixels and 8 frames/s, holding day 28 and the last day. The explorer now updates one `widgets.Image` in place (`notebook_display.figure_widget`) instead of clearing an output widget. `what_if_run` accepts the snapshot days, which must include day 28.

- Five new tests: frame holds, the day-28 requirement and equality of daily and default runs at day 28, GIF size, frame count and looping (MP4 not requested), the four-panel strip, and in-place redraw of `figure_widget` (206 tests).
- Section 12 asserts that the day-28 movie result equals section 8 and that the stated facts hold. Core reading: 8.4 cm² at day 0, lowest 7.6 cm² at day 9, 8.5 cm² at day 28. T2/FLAIR at day 28: 16.0 cm² against 27.6 cm² labelled, with the distant lesion 6.7 cm² of the 11.6 cm² shortfall. The front advances about 0.12 mm/day.
- On a staged tree (macOS 27.0.1, arm64, CPU) with the investigator's inputs linked and a separate environment: `make check` passed and `make notebooks` executed 01–12. The movie has 85 frames (GIF 2.5 MB, MP4 0.26 MB; ffmpeg from Homebrew). Frames at days 0, 14, 28, 33 and 56 were inspected as images, and the day-0 and day-28 status lines were shortened after they overran the image. The executed copy of 03 was re-exported (4.0 MB).
- The triple display was not reproduced; that `clear_output` within `interactive_output` stacks figures in Cursor's front end is a hypothesis. The new widget was not moved by hand in a live front end. Explorers in notebooks 02 and 04–11 still use `interactive_output`.
- Fault: earlier staged-tree checks in this session linked the repository's `.venv` and ran `uv` in the staged tree, which pointed the shared editable install at the staged copy and caused an `ImportError` in the investigator's kernel. The editable install was restored, and staged checks now use their own environment (`UV_PROJECT_ENVIRONMENT`).
- `make paper` not run (manuscript evidence unchanged); hosted Colab not rerun.

## 12 October 2026: Open-in-Colab badges on the published notebooks

At the investigator's request, the published notebooks gained an "Open in Colab" badge under their title, pointing at their own source notebook on the `main` branch of `arvidl/AI-assisted-glioma-research`: 01–03 here and the public version of 00 in `public/notebooks/`. The development notebook 00 (source-archive upload) and the unpublished 04–12 have none. `tests/test_colab_badges.py` checks that every notebook the snapshot publishes (with `public/` overrides) has exactly one badge naming its own file, and that no notebook or executed copy names another file; in the public repository every notebook counts as published.

- On a staged tree (macOS 27.0.1, arm64, CPU) with a separate environment: `make notebooks` executed 01–12; executed copies of 01–03 were re-exported; `make check` passed (208 tests).
- Not done: the badge links were not opened. They work for others only once the public repository is public.

## 12 October 2026: preparation for making the public repository public

The investigator asked whether to fix the links in executed copies and whether the repository could be made public with notebooks 00–03, and chose to fix the links and the private-route wording, to publish the development record with a note, and to include notebook 03 with its open choices marked as awaiting review.

- Links. `scripts/export_executed_notebooks.py` now rewrites markdown links and `src`/`href` attributes that start with `../` to `../../` when it writes to `notebooks/executed/`; links to sibling notebooks and absolute URLs are kept. Two tests: the rewrite rule, and that every `../` link in a tracked executed copy resolves to an existing file. The source-equality test applies the same rewrite.
- Wording. The fetch error, the `Makefile` comment and `docs/data.md` now state the `--use-gh` route as conditional on the repository not being public. The public README states that commit hashes, links into the development repository and mentions of unpublished material are not publicly accessible; `docs/validation.md` opens with the same note. A public `docs/reproducibility.md` (in `public/docs/`) describes the clone-based Colab route and omits manuscript and talk builds; `docs/notebook-review-checklist.md` is held back from the snapshot.
- Staged-tree runs earlier today used an environment whose interpreter came from Anaconda (CPython 3.12.2), which changed the recorded kernel version in the executed copies. This run used uv's managed CPython 3.12.14 (`UV_PYTHON_PREFERENCE=only-managed`), as before today. `make notebooks` executed 01–12 and all executed copies were re-exported; apart from links and the version, one figure in 02 differed from the previous copy in 72 pixels of title text. `make check` passed (210 tests).

## 12 October 2026: public repository made public (stage 1)

At the investigator's instruction ("go public", and push the development branch), the three local snapshot commits in the clone were squashed into one commit, `81101d8` "Stage 1: package, tests and notebooks 00-03", with content identical to the last snapshot (written from `7a08880`), on top of the initial README commit. It was pushed to `main` of `arvidl/AI-assisted-glioma-research`, the development branch `codex/notebook-hygiene` was pushed to this repository, and `gh repo edit --visibility public` made the public repository public.

- Anonymous route: a fresh HTTPS clone without credentials received `81101d8`; the release asset URL returned HTTP 200; `glioma-ai lumiere-bundle-fetch` without `--use-gh` downloaded the archive, checked the pinned SHA-256 and verified 27 files, and a second run downloaded nothing.
- GitHub Actions run 38282331605 ("Reproducible examples", push of `81101d8`) succeeded on all six jobs (Ubuntu and macOS; Python 3.11, 3.12 and 3.13). GitHub warned that `actions/checkout@v4` and `astral-sh/setup-uv@v6` target the deprecated Node.js 20.
- Not done: the Colab badges and a hosted Colab run of 00–03 (need the investigator's browser session).

## 13 October 2026: notebook 01 Figure 3 licence wording and cohort archive

The investigator reported that Figure 3 of notebook 01 is skipped in Colab. The assistant found that the published executed copy of 01 (public since `81101d8`) shows Figure 3, a slice of the public subject UCSF-PDGM-0494 and the 50-subject recomputation, while the notebook text, the caption and the cohort record stated that UCSF-PDGM is used under a TCIA data-use agreement and that the figure is not distributed, and `AGENTS.md` authorized real-data figures only in 03, 09, 10 and 12. The export checks missing inputs, not which notebooks may show real data. The TCIA collection page (checked 13 October 2026) lists the UCSF-PDGM images, annotations and clinical data under CC BY 4.0, with the TCIA Data Usage Policy and the dataset citation required; the companion repository's `data/README.md` still says "Data Usage Agreement on TCIA — confirm before any redistribution". The investigator chose to keep the figure with corrected wording and an `AGENTS.md` exception for 01 (applied), and asked for a release archive for Colab, built and tested without upload.

- Wording. Caption: "Images and reference labels: UCSF-PDGM v5 (Calabrese et al. 2022; The Cancer Imaging Archive, doi:10.7937/tcia.bdgf-8v37), CC BY 4.0; changes: one slice cropped and overlaid with labels and contours." The cohort record gained a licence field; the notebook text and `docs/data.md` were corrected.
- Archive. `glioma_ai.hpgs_bundle` (`make hpgs-bundle`, `scripts/build_hpgs_bundle.py`) selected 201 files from the investigator's companion checkout (50 reference segmentations, 50 SegResNet label maps with their records, 50 metrics records and the T1c of subject 0494, the median case chosen by `hpgs_cohort.median_case`). The companion's staging script copies dataset files from the UCSF-PDGM v5 release with `shutil.copy2` and renames them; the NIfTI files were copied byte for byte, and their header text fields are empty. All 100 JSON records were re-serialized; none contained a local path. A search of the records and README found no `/Users`, user name, Dropbox, `/home` or `/Volumes`. Two builds gave the same archive (9,047,431 bytes, SHA-256 `e386f2127e08042421a756b336964ece5d222e7c2c96e9476069d6eb295039bf`), pinned in `src/glioma_ai/references/hpgs_bundle_cohort50.json` for release `ucsf-pdgm-cohort50-v1`. The shared fetch code of the LUMIERE archive was factored into `lumiere_bundle.fetch_archive`.
- Equivalence. Figure 3 written from the extracted archive and from the companion checkout gave an identical PNG, record and caption.
- Notebook 01 gained a Colab-only cell that fetches the archive and sets `HPGS_REPO`; before upload it reports that the asset is not available and Figure 3 is skipped. Four tests on a synthetic checkout (deterministic selection with one T1c and path cleaning; the extracted archive reproduces the cohort table and refetching is idempotent; refusal of an unpinned archive and of missing inputs; the pin).
- On a staged tree (macOS 27.0.1, arm64, managed CPython 3.12.14, separate environment): `make notebooks` executed 01–12; the executed copy of 01 was re-exported; `make check` passed (214 tests).
- The investigator then approved the drafted `AGENTS.md` exception for the release asset, including CC BY 4.0 for the companion derivatives, and asked for upload and push. The exception was applied; `gh release create ucsf-pdgm-cohort50-v1` on `arvidl/AI-assisted-glioma-research` uploaded the archive, and GitHub reported the pinned size and SHA-256. Without credentials, `glioma-ai hpgs-bundle-fetch` downloaded, checked the pin, extracted and verified 201 files (a second run downloaded nothing); the cohort table from the download matched the companion records (maximum Dice difference 0) and the published medians.
- Colab simulation: notebook 01 executed in the public clone (no `local/`, no `HPGS_REPO`) with a stand-in `google.colab` module; its Colab cell fetched the archive from the release and Figure 3 and its caption were rendered and inspected.
- Not done: hosted Colab. The already published executed copy kept the old wording in the history of `81101d8` (replaced; see the next entry).

## 13 October 2026: Colab kernel warning and Figure 2 of notebook 01

The investigator reported, from a hosted Colab run of notebook 01, the warning "Unrecognised runtime 'glioma-ai'; defaulting to 'python3'", that Figure 2 (the published CC BY illustration) shows "Figure not imported locally", and that Figure 3 is shown. The investigator asked for Figure 2 to work the same way as Figure 3.

- Kernel. All 13 numbered notebook sources recorded the local kernelspec `glioma-ai`; they now record the standard `python3` kernelspec, and `scripts/export_executed_notebooks.py` sets the same kernelspec in every executed copy (asserted by `tests/test_export_notebooks.py`). The optional local registration in the README is unchanged.
- Figure 2. `glioma_ai.published.fetch_published_figures` (CLI `published-figures-fetch`, `make published-figures-fetch`) downloads the three figure assets pinned in `src/glioma_ai/references/imaging_figures.json` from the release named there, checks each SHA-256 before writing and keeps already verified copies. Notebook 01 gained a Colab-only cell before Figure 2 that calls it. One test with a stand-in release (verification, refusal of altered bytes, idempotence). `AGENTS.md` now lists Figure 2 in the 01 executed-copy exception and authorizes the release asset.
- Release. Before upload the three local copies were verified against their pins; `gh release create published-figures-v1` uploaded them unmodified to `arvidl/AI-assisted-glioma-research`, and GitHub reported the pinned SHA-256 for each. Without credentials, `glioma-ai published-figures-fetch` downloaded and verified 3 files into an empty folder; a second run downloaded none.
- On a staged tree (macOS 27.0.1, arm64, managed CPython 3.12.14, separate environment): `make notebooks` executed 01–12, all executed copies were re-exported, and `make check` passed (215 tests).
- Companion repositories: the licence line of `data/README.md` in `arvidl/high-precision-glioma-segmentation` and its development twin now states CC BY 4.0 with the TCIA Data Usage Policy and both citations. The development twin's commit is left to the investigator because its pre-commit hook needs `pre-commit`, which its environment lacks.
- The second Colab screenshot ("Expected geometry refusal: Reference and segmentation must have the same shape and affine.") is the intended demonstration output; the underlined `glioma_ai` imports come from Colab's editor, which does not see the `sys.path` entry added at run time.
- Public history. At the investigator's request, so that the old UCSF-PDGM wording does not remain in the public history, the public `main` was rebuilt as the initial README commit followed by one commit with this tree, replacing `81101d8` and `8f79178`, and force-pushed; the tag `ucsf-pdgm-cohort50-v1` was moved to the new commit. GitHub can keep unreferenced commits reachable by hash for some time, and copies made while they were public cannot be recalled.
- After the push: GitHub Actions run 38357879031 on the new public commit succeeded; the three releases resolve, and the figure asset URL returned HTTP 200. The public companion commit `7b609ac` was pushed; its CI failed with 7 ruff errors in existing test files, as on every push since 4 October 2026 (not caused by the README line).
- Hosted Colab (same day): the investigator reported that notebook 01 now works in Colab. The assistant did not observe that run.

## 13 October 2026: play buttons of the time sliders in Colab

The investigator reported that notebook 02 works in Colab, but that the play control beside "Observation day" in both growth explorers shows blank buttons. ipywidgets draws the buttons of `Play` with Font Awesome icons, which Colab does not load. `glioma_ai.notebook_display.play_control` adds a style that draws the play, pause, stop and repeat buttons with Unicode symbols (written as CSS escapes); the growth explorers (notebooks 02 and 11) and the LUMIERE explorer (notebook 03) use it, and the explorer test checks the style.

- A mock of the `Play` button markup without Font Awesome, in the Cursor browser: the unstyled buttons were blank and the styled ones showed the four symbols.
- On a staged tree (macOS 27.0.1, arm64, managed CPython 3.12.14, separate environment): `make notebooks` executed 01–12; re-export changed only the widget state of the executed copies of 02, 03 and 11; `make check` passed (215 tests).
- Hosted Colab (same day): the investigator reported that notebook 02 now works in Colab. The assistant did not observe that run. Later the same day the investigator reported that notebook 03 works in Colab (also not observed by the assistant). Notebook 11 is not yet published.

## 13 October 2026: notebook 04 restructured with clinical and modeling tracks

After the investigator's review of notebook 04, its text was restructured (record: `docs/ai-use/2026-10-13-notebook-04-tracks.md`). Numerical statements in the new text were taken from runs of `run_checks`: plateau 0.67 mM and time constant 1.1 s; the omitted-clearance plateau 0.75 mM; the Figure 1 deviations (forward Euler 3.9e-3 mM; omitted clearance 8.3e-2 and 3.1 mM; start-of-step accounting 1.1e-2 mM); with λo = 0 the omitted-clearance bug passes the analytic and balance checks and fails swap invariance (5.5 mM); with λa = λo = 0.45/s it passes swap invariance and fails the analytic check; at a tolerance of 1e-2 mM forward Euler passes at Δt = 0.05 s, the accounting bug passes at Δt = 0.01 s (2.1e-3 mM), and both fail at Δt = 0.2 s. The validator rules in section 7 were listed from `glioma_ai.assistance.validate_record`.

- The former exploration task 1 overstated the λo = 0 case (see above); corrected, and the test now asserts the full verdict.
- On a staged tree (macOS 27.0.1, arm64, managed CPython 3.12.14, separate environment): `make notebooks` executed 01–12; the executed copy of 04 was re-exported; `make check` passed (215 tests).
- Not done: hosted Colab (04 is not yet public); the investigator's reading of the new text.

## 13 October 2026: notebook 05 with two tracks, glossary and references

After the investigator's review questions on notebook 05, its text was restructured (record: `docs/ai-use/2026-10-13-notebook-05-tracks.md`).

- References: the 14 DOIs in the notebook were checked against Crossref (first author, year, journal, title) and all resolve (doi.org handle API, HTTP 200). Each statement attributed to a study was compared with its PubMed abstract (PMIDs 34087162, 38640932, 28697342, 35700707, 38653236, 31327527, 24925914, 26713745, 19505944, 21854987, 20129251, 34185076, 28292436).
- Numbers in the new text were taken from runs: overall MES-like fraction 0.279 at day 10 with the cue and 0.082 without; long-run limit 0.489; peak local fraction 0.542 at day 10 and 0.798 at day 60; cue centre at 20 mm gives 0.145 at day 10 (limit 0.196); a 2 mm cue gives 0.101 (limit 0.056); no-cue half-life 34.7 days; Figure 2 at day 5: 0.375 (reference) and 0.542 (rates doubled).
- On a staged tree (macOS 27.0.1, arm64, managed CPython 3.12.14, separate environment): `make notebooks` executed 01–12; the executed copy of 05 was re-exported; `make check` passed (215 tests).
- Not done: hosted Colab (05 is not yet public); the investigator's reading of the new text.
- Title change (investigator's choice): on a fresh staged tree (same platform), `make notebooks` executed 01–12, the executed copy of 05 was re-exported and `make check` passed (215 tests) with the staged executed copies.
- MES-like and T2/FLAIR spelled out in the introduction: same procedure on a fresh staged tree; `make check` passed (215 tests).
- The investigator reported being happy with notebook 05 after reading it (13 October 2026). Hosted Colab remains not done.

## 13 October 2026: notebook 06 with two tracks, glossary, references and a proposed title

At the investigator's request, notebook 06 received the treatment of notebooks 04 and 05 (record: `docs/ai-use/2026-10-13-notebook-06-tracks.md`).

- References: the 15 reference DOIs were checked against Crossref (first author, year, journal, title) and all resolve (doi.org handle API, HTTP 200). Statements attributed to studies were compared with their PubMed abstracts (PMIDs 25913192, 28959975, 31534222, 31534219, 26536111, 21909104, 31996845, 32250339, 37138086, 41298888, 32302564, 37059069, 14607296; Louis 2021 and Raue 2009 as for notebook 05).
- Numbers in the new text were taken from runs of the package functions and match the executed notebook: well-mixed half-carrying-capacity days 73.7, 50.8 and 48.1; Table 1 values; largest nullcline distance 0.016 (0.099 with τ = 20 days, half capacity on day 45.0); nullcline at full density 0.527 (0.794 with τ = 20 days); κ = 0 signal 0.519 at day 150 with unchanged density; b = 0 feedback half capacity on day 65.9 with signal 0.322; spatial integrals 35.2 → 67.3, 93.0, 95.8 mm² (ratios 1.424 and 1.031), step halving 0.11%; peak signal increase 0.125 at (−7, 0) mm; extra feedback density centred at x = −2.6 mm, peak density 0.54 against 0.40; sensitivity grid 1.178/1.382, 1.187/1.404, 1.196/1.424; spatial explorer tasks (drive at −5 and +15 mm, zero amplitude, κ = 0, days 10 and 40) as stated.
- Figures 1 and 2 were inspected against the reading guides.
- Code cells are byte-identical to the previous commit.
- On a staged tree (macOS 27.0.1, arm64, managed CPython 3.12.14, separate environment): `make notebooks` executed 01–12; the executed copy of 06 was re-exported; `make check` passed (215 tests) with the staged executed copies.
- Not done: hosted Colab (06 is not yet public); the investigator's reading of the new text. The investigator chose the proposed title.
- Fifteen further references (recent 2024–2026 studies and papers co-authored by Bjerkvig, Jian Wang and/or Miletic) were checked against Crossref (all resolve, HTTP 200) and their PubMed abstracts and author lists (PMIDs 39644898, 39821165, 40897174, 38246990, 39972132, 42754728, 42705231, 39532103, 39837324, 41747254, 34543427, 37169842, 41729947, 41284925, 40208515); Jian Wang's Bergen affiliation was confirmed in PMIDs 34543427 and 41284925. Code cells unchanged; on a fresh staged tree `make notebooks` executed 01–12, the executed copy of 06 was re-exported and `make check` passed (215 tests).
- The investigator accepted notebook 06 for now after reading it (13 October 2026). Hosted Colab remains not done.

## 13 October 2026: notebook 07 with two tracks, glossary, recent and Bergen references, and a proposed title

At the investigator's request, notebook 07 received the treatment of notebooks 04–06, with attention to recent papers and to work co-authored by Bjerkvig, Jian Wang and/or Miletic (record: `docs/ai-use/2026-10-13-notebook-07-tracks.md`).

- References: the 30 references and the linked 2022 correction notice of Chen et al. 2016 (31 DOIs) were checked against Crossref (first author, year, journal, title) and all resolve (doi.org handle API, HTTP 200). Statements attributed to studies were compared with their PubMed abstracts (PMIDs 36787748, 37697045, 40562937, 40399681, 42791388, 42744791, 42768016, 39514365, 38342629, 31509308, 31769546, 28173797, 27613828, 15561419, 17942730, 24482245, 832122, 33589835, 14999814, 24367247, 32348299, 10899222, 24081156, 31186414; Venkatesh 2019, Watson 2023, Storevik 2026, Zhou 2026 and Raue 2009 as for notebook 06), and co-author names written out in full with the Crossref author lists. Three recalled DOIs were wrong and were replaced via a Crossref bibliographic search.
- Numbers in the new text were taken from runs of the package functions and match the executed notebook: Table 1 (λ 0.9/0.3/0.1 per s; 1/λ 1.11/3.33/10 s; half-life 0.77/2.31/6.93 s; plateau 0.67/2.00/6.00 mM; first-pulse peak 0.648/1.398/1.978 mM, closed form and package agree); Figure 1 second-pulse peaks 0.649/1.524/2.867 mM, maximum E_K shift 5.23/10.98/17.93 mV; Table 2 (baseline E_K −102.7 mV; shifts +4.1/+7.7/+18.5/+29.4 mV); conservation residual zero to floating-point precision; identifiability example 4.741 versus 1.185 mM-equivalent astrocytic removal. Explorer task values (4.8 mM without clearance; plateaus 0.667 and 1.995 mM for a 20 s pulse; plateau 0.67 mM, time constant 2.2 s and peaks 0.56 and 0.57 mM with release and clearance halved) and exercise answers were computed with the package; the explorer colours named in the text were checked against `neuroglial_interactive`.
- Figure 1 was inspected against its reading guide. Code cells are byte-identical to the previous commit.
- On a staged tree (macOS 27.0.1, arm64, managed CPython 3.12.14, separate environment): `make notebooks` executed 01–12; the executed copy of 07 was re-exported; `make check` passed (215 tests) with the staged executed copies.
- Not done: hosted Colab (07 is not yet public); the investigator's reading of the new text; moving the explorer sliders in a live front end. The investigator chose the proposed title.
- Expansion of sections 4, 6, 7, 8 and the exercises (record as above). New numbers were computed with the package and checked numerically: leftover excess at 10 s 3%, 30% and 67% of the first peak; second/first peak 1.00, 1.09 and 1.45; time below 0.1 mM after the second pulse 2.1, 9.1 and 33.6 s; time-integrated excess 5.33, 15.75 and 37.45 mM·s; astrocytic removal by 24 s 4.27, 3.15 and 0 mM (other 0.53, 1.57, 3.75 mM); E_K at the highest point −97.5, −91.7 and −84.8 mV (8.1, 7.2 and 6.3 mV per mM); RT/F 26.73 mV, 18.5 mV per doubling, 61.5 mV per decade; ∫k dt 5.93 mM·s in the identifiability runs; peaks 0.97 and 2.10 mM with 50% more release; periodic-train peaks 0.649, 1.537 and 3.592 mM (formula and 30-pulse simulation agree); saturating-uptake plateau 0.928 mM (quadratic and time stepping agree). The Curry et al. 2023 abstract was re-read for the seizure-screen wording. Explorer slider ranges were checked against `neuroglial_interactive`. Code cells unchanged; on a fresh staged tree `make notebooks` executed 01–12, the executed copy of 07 was re-exported and `make check` passed (215 tests).

## 13 October 2026: notebooks 04–07 prepared for publication (stage 2)

The investigator reported finding notebooks 04–07 all ok for now and asked to commit and push them for Colab testing (record: `docs/ai-use/2026-10-13-publish-notebooks-04-07.md`). Each gained a Colab badge, a Colab note and a Colab-only setup cell before its first code cell; `scripts/public_snapshot.py` publishes 00–07, and the public README and notebook map list 04–07.

- On a staged tree (macOS 27.0.1, arm64, managed CPython 3.12.14, separate environment): `make notebooks` executed 01–12; the executed copies of 04–07 were re-exported; `make check` passed (215 tests), including the badge test, which now covers 04–07.
- The map entries were checked against the notebooks' headings; notebook 04 has no glossary and no longer contains the AI-benefit pilot, and its entry says so.
- Not done: hosted Colab of 04–07 (the investigator's).
- Public clone: `scripts/public_snapshot.py` wrote 166 files from `ba3cd6b` (two reported links outside the snapshot are template strings in notebook 01, as before). In the clone (macOS 27.0.1, arm64, managed CPython 3.12.14): `make check` gave 210 passed and 5 skipped; `make notebooks` executed 01, 02 and 04–07 (03 skipped without its LUMIERE root). Committed as `127343e` "Notebooks 04-07 with executed copies; README and notebook map" and pushed to `main` of `arvidl/AI-assisted-glioma-research` with the investigator's approval.
- Colab simulation: notebooks 04–07 were executed from `/tmp`, outside any checkout, in an environment with NumPy, Matplotlib and ipywidgets but without `glioma_ai`, with a stand-in `google.colab` module registered in the kernel and the clone URL and checkout path pointed at the local public clone. Each setup cell cloned the repository (commit `127343e`) and imported the package from it; all cells ran without errors.
- GitHub Actions run 38395838185 on `127343e`: five jobs passed; the macOS/Python 3.12 job hung for more than 50 minutes in the notebook step, which took about 35 s in the other jobs, and which has a 300 s cell timeout, so the hang was outside cell execution. It was cancelled and re-run; on the second attempt all six jobs passed. The cause of the hang was not determined.
- Hosted Colab (same day): the investigator reported that notebooks 04–07 all seem to work well in Colab. The assistant did not observe those runs.

## 13 October 2026: notebook 08 with two tracks, glossary, exercises and recent references

At the investigator's request, notebook 08 received the treatment of notebooks 04–07, with expanded sections 3 and 8, an expanded empirical anchor and recent (2025–2026) references (record: `docs/ai-use/2026-10-13-notebook-08-tracks.md`).

- References: the 42 reference DOIs were checked against Crossref (first author, year, journal, title) and all resolve (doi.org handle API, HTTP 200); the OSF link is the one used in notebook 10. Statements attributed to studies were compared with their PubMed abstracts (PMIDs 22595786, 21240273, 24135696, 28018180, 22153379, 16436298, 40228210, 41577095, 20624597, 28169833, 29396478, 41720182, 41690463, 40228055, 35102333, 40882239, 41015390, 37420330, 37210066, 42618509, 41963323, 40699921, 42085148, 40907471, 42221980, 34753819, 37138086, 40404658, 42743926, 40379630, 15126372, 29260225, 41350399, 40161979, 40980440, 40878319, 41019665, 41053506; Osswald 2015 as for notebook 06; the notebook 10 sources as there).
- Numbers in the new text were computed with `sampled_field`, `derivative_error_curve` and `field_from_potential` and match the executed notebook where it prints them (peaks 0.063 and 0.251 V/m; largest numerical error 5.3e-05 V/m; central fields −0.06283 and −0.25130 V/m; ratio 3.9996; Figure 2 optima 0.12 and 0.25 mm). Further values (explorer tasks, analytic optima, second-difference optima with a 200-realisation simulation, traveling-wave conversion, gradient bias) are listed in the record. Figure 1 was inspected against its reading guide; the explorer's panel contents and slider ranges were checked against `neuroglial_interactive`.
- Code cells are byte-identical to the previous commit.
- On a staged tree (macOS 27.0.1, arm64, managed CPython 3.12.14, separate environment): `make notebooks` executed 01–12; the executed copy of 08 was re-exported; `make check` passed (215 tests) with the staged executed copies.
- Not done: hosted Colab (08 is not yet public); moving the explorer sliders in a live front end; the investigator's reading of the new text.
- Title change (investigator's choice): on a fresh staged tree (same platform), `make notebooks` executed 01–12, the executed copy of 08 was re-exported and `make check` passed (215 tests) with the staged executed copies.
- Tumour–brain interface (investigator's request): new `tumour_border_fields` and `draw_tumour_border` in `glioma_ai.neuroglial_interactive`, a test against the analytic activity field (atol 1e-4 V/m), the exact step field away from the border, the 0.0375 V/m estimate at the border and the parameter errors, and a new section 6 with one new code cell; other code cells are unchanged. The 18 new DOIs were checked against Crossref (first author, year, journal, title; all resolve) and statements against the PubMed abstracts (PMIDs 31534219, 31534222, 25009229, 41298888, 41918715, 37713468, 36517594, 40127031, 42700893, 38354669, 30610409, 28698943, 38417178, 27695068, 41703344, 34273404, 26898606, 30926929). The executed notebook prints peaks 0.251 and 0.050 V/m, largest border term 0.039 V/m, step 0.050 → 0.025 V/m and 0.0375 V/m at the border for both spacings, as stated in the text; Figure 3 was inspected against its reading guide. The first staged run failed ruff (one line of the new cell over 100 characters); after the fix, on a fresh staged tree (same platform) `make notebooks` executed 01–12, the executed copy of 08 was re-exported and `make check` passed (216 tests). Not done: hosted Colab; the investigator's reading.

## 13 October 2026: publishing notebook 08

The investigator found notebook 08 fine for now and asked to publish it for Colab testing (record: `docs/ai-use/2026-10-13-publish-notebook-08.md`).

- Separation: the notebook's code imports only `glioma_ai`, NumPy and Matplotlib and reads no data; since `ba3cd6b` (the 04–07 publication) the only package and test changes are the additive `tumour_border_fields`, `draw_tumour_border` and their test. The two links to notebook 10 became plain text; the remaining relative links (`../docs/ai-workflow.md`, `../docs/cognition-prediction-study.md`) are in the public snapshot.
- On a staged tree (macOS 27.0.1, arm64, managed CPython 3.12.14, separate environment): `make notebooks` executed 01–12; the executed copy of 08 was re-exported; `make check` passed (216 tests), including the badge test, which now covers 08.
- Public clone: `scripts/public_snapshot.py` wrote 170 files (the two reported links outside the snapshot are the template strings in notebook 01, as before). The snapshot removes the clone's `.venv`, and `make check` run before `make setup` failed with `ModuleNotFoundError: nbformat` in the two notebook-tooling tests; this is the documented setup order (CI runs `uv sync --locked --group notebooks` first), not a change in 08. After `make setup` (macOS 27.0.1, arm64, managed CPython 3.12.14): `make check` gave 211 passed and 5 skipped; `make notebooks` executed 01, 02 and 04–08 (03 skipped without its LUMIERE root). Committed locally as `d629cb0` "Notebook 08 with executed copy; README and notebook map".
- Colab simulation: notebook 08 was executed from `/tmp`, outside any checkout, in a fresh Python 3.12 environment with NumPy, Matplotlib, ipywidgets and nbclient but without `glioma_ai`, with a stand-in `google.colab` module on the kernel path and the clone URL and checkout path pointed at the local public clone. The setup cell cloned `d629cb0` and imported the package from it; all six code cells ran without errors.
- Pushed `d629cb0` to `main` of `arvidl/AI-assisted-glioma-research` with the investigator's approval.
- GitHub Actions run 38448293325 on `d629cb0`: four jobs passed; the macOS/Python 3.11 and Ubuntu/Python 3.12 jobs hung for more than 20 minutes in the notebook step, before notebook 08 (logs: last line "Validated 03…" and "Executed 04…" respectively), as in run 38395838185 for 04–07. The run was cancelled; on re-running the two jobs all six passed. The cause of the intermittent hang was not determined.
- Hosted Colab: the investigator reported that notebook 08 runs in Google Colab (opened from the public repository). Runtime type, package versions and which cells or explorer controls were exercised were not reported.

## 14 October 2026: notebook 09 with two tracks, the tumour–brain interface, networks and cognition

At the investigator's request, notebook 09 was reorganized for clinicians and modelers and extended with the tumour–brain interface, network views of cognition, glia and brain waves, and the bridge to notebook 10 (record: `docs/ai-use/2026-10-14-notebook-09-tracks.md`).

- Package: new `glioma_ai.tumour_interface` with seven tests (levels and coefficients equal to notebook 03, stopping radius within 0.2 mm, ordering of extents, monotonicity in D, additive regional shares, grid refinement within 0.3 mm, parameter errors). Seed sensitivity (1 versus 3 mm) was run separately and is reported in the notebook. Figure 3 was rendered and inspected against its reading guide.
- Published record: the `article_results` block of `lundervold2026.json` was transcribed from a text extraction of the published PDF (SHA-256 matches the recorded hash), with table and section locators; a new test checks that the Table 3 medians round to the abstract values and that each block has a locator. `published_numbers.tex` is unchanged because the macros read only the existing keys, so `make paper` was not rerun.
- References: the 47 DOIs were checked against Crossref (first author, year, journal, title), the TCIA DOI through DataCite; statements were compared with the PubMed abstracts (PMIDs 41137668, 40149329, 42286261, 40940871, 42669223, 42632037, 38573324, 41540261, 42124622, 42816965, 40680638, 40586873, 42119240, 40300378, 36857946, 38347141, 39753446, 42411828, 42048772, 38683350, 40373122, 40408402, 42618509, 41350399, 30664773, 37138086, 34753819; reused verified sources as for notebooks 03, 08, 10 and 11). PMIDs 41912664 and 42162275 have no abstract and are cited by title only.
- The executed notebook prints Tables 1–5 with the values stated in the text (for example median WT Dice 0.901 [0.850, 0.932]; CCC 0.974, 0.992 and 0.951; FLAIR boundaries 17.7, 22.8 and 49.0 mm; 25.57% beyond T1Gd + 15 mm for the high-diffusivity case). The metric, burden and explorer code cells are unchanged except for the table number.
- On a staged tree (macOS 27.0.1, arm64, managed CPython 3.12.14, separate environment): `make notebooks` executed 01–12; the executed copy of 09 was re-exported; `make check` passed (224 tests) with the staged executed copies.
- Not done: hosted Colab (09 is not yet public); moving the explorer sliders in a live front end; the investigator's reading of the new text. The investigator chose the proposed title, so the notebook is unchanged.
- Accuracy and agreement definitions (investigator's request): glossary only, code cells unchanged. The notebook was rendered to HTML with nbconvert and the table and display equations were inspected in a browser with MathJax 2.7.7 (Dice row fixed; all formulas typeset). Lin 1989 and Bland & Altman 1986 were checked against Crossref. On a fresh staged tree (same platform) `make notebooks` executed 01–12, the executed copy of 09 was re-exported and `make check` passed (224 tests).
- Segmentation-panel legend (investigator's request): rendered and inspected for the default state, the investigator's screenshot state (shift −4, dilation 1, blob 4 mm at 27 mm) and an extreme state (shift 8, dilation 5, blob 8 mm at 45 mm); the slider ranges (shift ±10, dilation ±5, blob ≤ 8 mm at ≤ 45 mm) keep the masks out of the legend corner. On a fresh staged tree (same platform) `make notebooks` executed 01–12, the executed copy of 09 was re-exported and `make check` passed (224 tests).

## 14 October 2026: publishing notebook 09

The investigator found notebook 09 fine for now and asked to publish it for Colab testing (record: `docs/ai-use/2026-10-14-publish-notebook-09.md`).

- Separation: the notebook's code imports only `glioma_ai`, IPython and Matplotlib and reads no data except the published figures; since the notebook 08 publication the package and test changes are the additive `tumour_interface` module, the legend in `imaging_interactive`, the `article_results` block of `lundervold2026.json` and their tests. Notebooks 10–12 are named in plain text only; the relative links to `docs/` are in the public snapshot.
- On a staged tree (macOS 27.0.1, arm64, managed CPython 3.12.14, separate environment): `make notebooks` executed 01–12; the executed copy of 09 was re-exported (its Colab figure cell prints "Not Colab: …"); `make check` passed (224 tests), including the badge test, which now covers 09.
- Public clone: `scripts/public_snapshot.py` wrote 176 files from `26d536d` (the two reported links outside the snapshot are the template strings in notebook 01, as before). After `make setup` (same platform): `make check` gave 219 passed and 5 skipped; `make notebooks` executed 01, 02 and 04–09 (03 skipped without its LUMIERE root).
- Colab simulation: notebook 09 was executed from `/tmp`, outside any checkout, in a fresh Python 3.12 environment with NumPy, Matplotlib, ipywidgets, IPython and nbclient but without `glioma_ai`, with a stand-in `google.colab` module on the kernel path and the clone URL and checkout path pointed at the local public clone. The setup cell cloned the local public commit; the Colab figure cell downloaded the three figures from the release `published-figures-v1` and printed "Colab: 3 figures verified; CC BY 4.0, as stated in the published article."; all nine code cells ran without errors in 6.5 s. A first attempt stalled with an idle kernel after the figures had been fetched and was stopped after about 11 minutes; the cause was not determined and the rerun with per-cell logging did not reproduce it.
- Pushed `b9ce3bf` to `main` of `arvidl/AI-assisted-glioma-research` with the investigator's approval.
- Hosted Colab: the investigator reported that notebook 09 works well in Google Colab (opened from the public repository). In Colab, external links in Markdown cells open in a new tab through Google's redirect notice, whose "return to the previous page" link has no page to return to; this is Colab behaviour, not a notebook defect. Runtime type, package versions and which cells or explorer controls were exercised were not reported.
- GitHub Actions run 38559713398 on `b9ce3bf`: five jobs passed (notebook step 42–55 s); the Ubuntu/Python 3.12 job hung in the notebook step for more than 10 minutes, was cancelled and re-run, and hung again for about 9 minutes; it was cancelled and re-run once more. Without a log of the running step, the cause was not determined.

## 14 October 2026: diagnostics for the CI notebook hang

At the investigator's request (record: `docs/ai-use/2026-10-14-ci-notebook-hang-diagnostics.md`), `scripts/check_notebooks.py` prints a line before each notebook and dumps all thread stacks of the runner and the kernel every 240 s while a notebook runs, and the CI notebook step has a 15-minute timeout.

- The dumps were exercised with a copy of the runner whose threshold was 3 s on a notebook sleeping 8 s: both the runner's stacks (waiting in `nbclient` `_async_poll_for_reply`) and the kernel's appeared, and the run completed.
- On a staged tree (macOS 27.0.1, arm64, managed CPython 3.12.14, separate environment): `make check` passed (224 tests); `make notebooks` executed 01–12 with the new start lines and no dumps. In the working tree `make check` failed only because the investigator's uncommitted notebook copies carry a different kernelspec, which the executed-copy test compares.
- GitHub Actions run 38563332722 on public `0bfa6d6`: four jobs passed; both Python 3.12 jobs (Ubuntu and macOS) hung after starting notebook 04 and failed at the 15-minute step timeout. The stack dumps located the wait in ipykernel's OS-level output forwarding thread (record: `docs/ai-use/2026-10-14-ci-notebook-hang-diagnostics.md`).
- Runner change: the validation kernel starts with `IPKernelApp.capture_fd_output=False`. A one-cell notebook confirmed that the option takes effect in ipykernel 7.3.0 (an `os.write(1, …)` line went to the runner's stderr, the `print` output into the notebook, and no pipe-watching threads were running). On a staged tree (same platform): `make check` passed (224 tests); `make notebooks` executed 01–12; re-exporting all twelve executed copies left them byte-identical to the tracked copies.
- Pushed `6551142` to `main` of `arvidl/AI-assisted-glioma-research` with the investigator's approval. GitHub Actions run 38566299060: all six jobs passed, the notebook step taking 24–47 s; one passing run does not prove that the race is gone.

## 14 October 2026: notebook 10 with three tracks and the BTC cohort

Notebook 10 was rebuilt with cognitive neuroscience, clinical and modelling tracks on the Brain Tumor Connectomics participant tables (record: `docs/ai-use/2026-10-14-notebook-10-tracks.md`).

- Sources: `make btc-fetch` downloaded the two OpenNeuro `participants.tsv` files (ds001226 v5.0.1, ds002080 v4.0.1) and the twin project's sub-PAT16 session table and dictionary (commit `d0159ec`), each matching its pinned SHA-256; both OpenNeuro DOIs resolve through DataCite to the pinned versions.
- Numbers stated in the text were taken from runs of `glioma_ai.btc_cantab` on these files: 11/14/11 participants at baseline and 10/12/7 at follow-up; all sub-PAT16 values agree across OpenNeuro, the twin table and OSF (RVP A′ at follow-up at the OSF two-decimal precision); 246 days between assessments and 18.614 cm³ residual lesion volume from OSF; against the ten retested controls no index exceeds 1.96, the largest being the practice-adjusted five-choice reaction time (+1.94, 86% of 4,000 bootstrap resamples beyond 1.96), which becomes about +2.5 when the control with the largest change is left out (r 0.71 → 0.91); leave-one-out forecasts in which persistence has the lowest error for simple reaction time, RVP A′ and spatial span (all groups pooled).
- Column audit: `RTI_fiveRT` lies on the 0.5 ms grid for all 35 complete baseline rows; `RTI_fiveMT` for 17%, with r = 0.98 to `RTI_fiveRT` and 0.01 to `RTI_fiveMT_mean`. Stated as an inference.
- References: DOIs checked against Crossref; summaries compared with PubMed abstracts (PMIDs in the record); the use of BTC_preop by Juncà et al. 2026 checked in the article.
- Execution: the built notebook was executed headlessly with nbclient with inputs present and, separately, with `BTC_DIR` and `CANTAB_OSF_DIR` pointing to empty folders (absent-input notices, no errors). The executed copy's outputs contain no participant ID other than sub-PAT16/PAT16, and no age, sex, calendar date or local path.
- On a staged tree (macOS 27.0.1, arm64, managed CPython 3.12.14, separate environment): `make notebooks` executed 01–12 (00 skipped as hosted Colab); the executed copy of 10 was re-exported; `make check` passed (246 tests) with the staged executed copies.
- Not done: hosted Colab (10 is not public); moving the explorers in a live front end; the investigator's and a neuropsychologist's reading of the text, the slide transcription and the design choices.

### The AI-generated slide and its reconstruction in section 4

- Section 4 now shows the investigator's AI-generated slide (Figure 3) as a markdown attachment, unmodified (SHA-256 `b099f91e4ea20e5f2780871778303fa49572ff69b63a22af0bf01114c0515d14`, checked by the builder), as authorized in `AGENTS.md`, followed by Table 5 and a reconstruction (Figure 4) drawn by `glioma_ai.btc_cantab_figures.draw_infographic` with conclusions from `glioma_ai.btc_cantab.change_summary`. Later figures were renumbered 5 and 6.
- Figure 4's values match the audit above: percentages −3.3, +14.4, +9.5, +0.2, 0 and +16.7 (positive = better); all six changes within the controls' retest variation on all three indices; the closest is the practice-adjusted five-choice index, +1.94. The figure extracted from the executed copy was inspected.
- On a staged tree (macOS 27.0.1, arm64, managed CPython 3.12.14, separate environment): `make notebooks` executed 01–12 (00 skipped as hosted Colab); the executed copy of 10 was re-exported, and its outputs contain no participant ID other than sub-PAT16 and no local path; `make check` passed (247 tests).
- In the unstaged working copy, `make check` fails only in the executed-copy kernelspec test, because the working-copy notebooks carry the local "Glioma AI (uv)" kernelspec.
- Not done: the attachment's rendering in hosted Colab and on GitHub (10 is not public); review of the new text by the investigator.

## 14 October 2026: publishing notebook 10

The investigator asked to publish notebook 10 for Colab testing (record: `docs/ai-use/2026-10-14-publish-notebook-10.md`).

- Separation: the notebook's code imports only `glioma_ai`, IPython, NumPy and Matplotlib; it links only to `docs/` files in the public snapshot and names notebooks 11–12 nowhere. Its Colab-only cell downloads the four files pinned in `btc_cantab.json` (CC0 OpenNeuro tables and the twin project's sub-PAT16 table); outside Colab it prints "Not Colab: …".
- On a staged tree (macOS 27.0.1, arm64, managed CPython 3.12.14, separate environment): `make notebooks` executed 01–12; the executed copy of 10 was re-exported, with no participant ID other than sub-PAT16 and no local path; `make check` passed (247 tests), including the badge test, which now covers 10.
- Public clone: `scripts/public_snapshot.py` wrote 184 files (the two reported links outside the snapshot are the template strings in notebook 01, as before). After `make setup` (same platform): `make check` gave 242 passed and 5 skipped.
- Colab simulation: notebook 10 from the public commit was executed outside any checkout in the Python 3.12 environment used for notebook 09 (NumPy, Matplotlib, ipywidgets, IPython, nbclient; no `glioma_ai`), with a stand-in `google.colab` module and the clone URL pointed at the local public clone. The setup cell cloned the local public commit; the Colab cell downloaded and verified the four files from GitHub ("Colab: 4 files verified; CC0 …"); all 22 code cells ran without errors in 11 s; the OSF cross-check and the paper's case figure printed their absent-input notices.
- Hosted Colab: the investigator reported that notebook 10 runs fine in Google Colab (opened from the public repository). Runtime type, package versions and which cells or explorer controls were exercised were not reported.

## 14 October 2026: notebooks 11 and 12 prepared for publication

Antigravity session (record: `docs/ai-use/2026-10-14-publish-notebooks-11-12.md`). Notebooks 11 and 12 received the Colab badge, note and setup cell of notebook 10 and small review fixes; the investigator authorised `data/derived/sub-PAT16/` in the public snapshot.

- Separation: both notebooks import only `glioma_ai`, IPython, NumPy and Matplotlib (and ipywidgets through the explorer of 11); their relative links point only to `docs/ai-use/` records that are in the snapshot. Neither downloads data in Colab; 12 reads the tracked matrices from the clone.
- On a staged tree (local notebook copies 00–10 stashed; macOS 27.0.1, arm64, managed CPython 3.12.14, project `.venv` after `uv sync --locked --group notebooks`): `make notebooks` executed 01–12 (00 skipped as hosted Colab), all passed; during 11 the kernel log printed "KeyboardInterrupt caught in kernel", with no error output in any cell. The executed copies of 11 and 12 were re-exported (only `sub-PAT16` appears as a participant ID; the exporter found no local path and no missing-input notice). Before the re-export, `make check` failed only the executed-copy currency test; afterwards it passed (247 tests).
- Public clone: `scripts/public_snapshot.py` wrote 197 files from `64f2c20` into a fresh clone of the public repository in a scratch directory (the two reported links outside the snapshot are the template strings in notebook 01, as before). It was committed there locally only and not pushed. After `make setup` (same platform): `make check` gave 244 passed and 3 skipped.
- Colab simulation: notebooks 11 and 12 from that local commit were executed outside any checkout in a separate Python 3.12 environment (NumPy 2.5.4, Matplotlib 3.11.2, ipywidgets 8.1.9, IPython, ipykernel, nbclient; no `glioma_ai`) with a stand-in `google.colab` module; the setup cell's clone URL and `/content` path were redirected to the local public commit and a scratch directory. 11: 7 code cells, no errors, 8 s. 12: 5 code cells, no errors, 3 s; its CANTAB cell printed "CANTAB not shown: …" as intended.
- Not done: hosted Colab; publication to public `main` (waits for the investigator); any review of the sub-PAT16 matrices or the upstream QC (still 0 of 37 items); review of the changed text by the investigator.

## 14 October 2026: notebook 11 with three reading tracks

The investigator asked for notebook 11 to follow notebook 10's three tracks (record: `docs/ai-use/2026-10-14-notebook-11-tracks.md`). Track paragraphs, a glossary, exercises and a reference list were added. The code cells are unchanged.

- New citations: Tykocki and Rakasz, Neurosurg Rev 2026;49:191, and Noll et al., Neuro-Oncol Adv 2025;7:vdaf192, checked against Crossref and the published abstracts. Salvalaggio, Cayuela, Douw, Herbet and Houskamp are the notebook 10 citations, used within the summaries already checked there. The motivation does not repeat Tykocki's pooled odds ratios.
- On a staged tree (macOS 27.0.1, arm64, managed CPython 3.12.14, separate environment): `make notebooks` executed 01–12 (00 skipped as hosted Colab); notebook 11 passed. The executed copy of 11 was re-exported. Its outputs contain no participant ID and no local path.
- On that staged tree, `make check` passed (247 tests).
- In the unstaged working copy, `make check` still fails the executed-copy kernelspec test, because notebooks 00–12 carry the local "Glioma AI (uv)" kernelspec. The staged source of 11 uses the repository kernelspec.

### Proofread, notebook 12 introduction, and further 2025–2026 references

The title was kept. Section 5 now introduces notebook 12: the open BTC MRI (ds001226 v5.0.0 and ds002080 v4.0.0, CC0), the tracked derived matrices rather than the volumes, the linear model carried over, the tumour-mask virtual resection, and the unreviewed upstream QC. Added, after Crossref and abstract checks: Nasiri et al. 2026, Berger et al. 2026, Kong and Wei 2026, Wang et al. 2026 (details in the record). Proofreading fixed the exercises' opening, the section cross-references and unlinked citations. Code cells were unchanged. On a staged tree (same platform and separate environment): `make notebooks` executed 01–12; the executed copy of 11 was re-exported. `make check` on that tree passed (247 tests).

## 14 October 2026: publishing notebook 11

The investigator was happy with notebook 11 for now and asked to commit and push it for a hosted Colab test. Notebook 12 stays in review, and `data/derived/sub-PAT16/` stays out of the public snapshot with it. Notebook 11's Colab cell only clones the repository; the network is constructed in code. The push to public `main` is made with the investigator's approval. Hosted Colab is the investigator's test.

### US spelling of tumor in notebook 11

The investigator asked for US **tumor** in the title and prose of notebook 11, matching notebooks 01–02, while keeping citation titles and “Brain Tumor Connectomics” unchanged. One retained British form remains in the Douw et al. reference title (“tumour biology”). Code cells were unchanged. On a staged tree (same platform and separate environment): notebook 11 alone was executed and its executed copy re-exported; `make check` passed (247 tests). Public `main` was refreshed with the investigator's approval.

- Hosted Colab: the investigator reported that notebook 11 works well in Google Colab (opened from the public repository). Runtime type, package versions and which cells or explorer controls were exercised were not reported.

## 15 October 2026: Actions budget, notebook cleanup and public-page fixes

Record: `docs/ai-use/2026-10-15-ci-budget-and-public-fixes.md`. GitHub reported that 90% of the included Actions minutes were used. On the last private run each macOS job took about 1.7 minutes, billed at ten times the Ubuntu rate; there were 84 runs since 1 October.

- The private workflow now runs only on manual dispatch, on Ubuntu (Python 3.11–3.13) plus the manuscript job, with superseded runs cancelled. Its YAML was not executed remotely in this step. The public workflow is unchanged.
- Notebooks 00–11 in the working copy differed from `HEAD` only in outputs, execution counts, empty trailing cells and the local kernelspec (checked cell by cell); they were restored to the committed versions.
- `make check` (macOS 27.0.1, arm64, managed CPython 3.12.14, project `.venv`): 247 passed.
- Public clone: `scripts/public_snapshot.py` wrote 190 files from `004cbfc` (the two reported links outside the snapshot are the template strings in notebook 01, as before); the changes were the README line, this record and the assistance record. After `make setup` (same platform): `make check` gave 242 passed and 5 skipped. The public "About" description was changed with `gh repo edit` and read back.
- Public `main` `2c97337` (pushed with the investigator's approval): in the clone, the `make check` run immediately before the push failed (output not retained; the snapshot rewrite had removed the clone's environment); after `make setup` the same tree gave 242 passed and 5 skipped. Public CI [run 38691739414](https://github.com/arvidl/AI-assisted-glioma-research/actions/runs/38691739414): four jobs passed; Ubuntu 3.11 and macOS 3.12 hit the 15-minute limit in `scripts/check_notebooks.py` with repeated 4-minute stack dumps of an idle kernel (the known intermittent headless stall); rerun of the failed jobs passed, so all six jobs passed.
- Private manual dispatch on `codex/notebook-hygiene` ([run 38692176455](https://github.com/arvidl/AI-assisted-glioma-research-dev/actions/runs/38692176455)): manuscript and Ubuntu 3.11, 3.12 and 3.13 passed, each in about 2 minutes. The push of `64fcc37` before it started no run.
- `make paper` and `make talk` (same platform) succeeded; `paper/main.pdf` (25 pages) and `talk/slides.pdf` (30 pages) were rebuilt with text identical to the tracked exports (pdftotext diff empty), so the tracked exports were kept unchanged.
- Notebook 12: `docs/sub-pat16-qc-review.md` (held back from the public snapshot) maps the 37 upstream QC items to local inputs and to their relevance for the tracked matrices. Cross-check only: the fMRIPrep confounds have 23 (pre-op) and 20 (post-op) of 180 volumes with FD > 0.5 mm, matching the 157 and 160 clean volumes in `provenance.json`. No image was inspected; 0 of 37 items reviewed.
- Not done: the $0 Actions budget and Cursor spending cap (investigator, billing pages); the investigator's QC review and go/no-go for notebook 12; clinical and citation review, timed rehearsals and the PowerPoint export of the talk; the post-talk repository switch (proposed in `docs/public-release.md`, section 7, untested).

## 15 October 2026: notebook 12 with two reading tracks, a resection explorer and a speculative section

Record: `docs/ai-use/2026-10-15-notebook-12-tracks.md`. The analyses of sections 1 and 2 and their code cells are unchanged. The new code is `glioma_ai.connectome.homotopic_summary` and `glioma_ai.connectome_interactive`.

- Platform: macOS 27.0.1, arm64, uv 0.13.1, managed CPython 3.12.14, project `.venv`.
- `make check`: Ruff lint and format passed; 253 passed. Six new tests cover the point-to-segment distance, radius 0, monotonicity in radius, the assumed region names, the homotopic partition of the 3,321 pairs, and the proxy check and figure.
- `make notebooks`: all of 01–12 executed (00 validated, not executed). Notebook 12's new cells printed the homotopic table, the proxy check, the size-by-location table, Figure 3 and the explorer widget, and the CANTAB cell ran with the local inputs present. Only notebook 12's executed copy was then re-exported (`scripts/export_executed_notebooks.py 12_patient_connectome.ipynb`, the exporter of `make executed-notebooks`). The other executed copies were left as they were.
- Observations printed by the notebook (one patient, upstream QC pending): homotopic measured FC 0.68 pre-op and 0.67 post-op, against 0.29 and 0.28 for other interhemispheric pairs; model homotopic FC 0.04. The interhemispheric share of structural weight is 1.9% pre-op and 9.2% post-op. A sphere of the mask's volume (radius 23.3 mm) at the tumour-weighted centre removes 11.3% of pre-op weight, against 10.6% measured through the mask; recall 76%, precision 71%.
- References: all 49 DOIs of section 6 resolved in Crossref on 15 October 2026 with matching first author, year and title words (Douw et al. and Tafazoli et al. are dated 2025 online and cited by their 2026 print volumes). The Aerts et al. 2022 title, inherited from notebook 11 as "multimodal MRI data", was corrected to the published "multimodal magnetic resonance imaging data" in notebook 12 only. Abstract sources are listed in the record.
- Not done: the explorer was not exercised interactively, locally or in Colab; no clinical or investigator review of the new text, the assumed table or section 4; `make paper` was not run, because no manuscript evidence changed; not committed or published.
- Title change (investigator's choice): notebook 12 is now "Can a virtual resection predict one patient's post-operative brain network? Structure, function and the distance to cognition". The source notebook again held outputs from the investigator's IDE run (no cell text changed); `make clear-notebooks` removed them. Two `make notebooks` runs then stalled with an idle kernel at notebook 12, after 01–11 had passed: the runner waited for kernel messages for more than 10 minutes and printed only its own stack dumps. Notebook 12 run alone with the same isolated kernel, and a full run with per-cell logging added, both completed (notebook 12's cells in about 3 s). A third, plain `make notebooks` executed 01–12. The cause of the stalls was not found. Notebook 12's executed copy was re-exported; it now carries the corrected Aerts et al. title from a fresh run. `make check` passed (253 tests).

### Publishing notebook 12

The investigator stated that they had quickly reviewed notebook 12 and run its explorer by hand locally, and asked to publish it with the upstream QC stated as unreviewed (0 of 37 items), as authorized on 14 October (record: `docs/ai-use/2026-10-15-notebook-12-tracks.md`). `scripts/public_snapshot.py` again publishes notebooks 00–12 and `data/derived/sub-PAT16/`; `scripts/derive_pat16_connectome.py` and `docs/sub-pat16-qc-review.md` stay held back. The public README and notebook map list notebook 12 under its new title and describe the matrices. The investigator's IDE outputs in the source notebook (no cell text changed) were discarded with `git restore`. `make check` passed (253 tests) on the same platform as above.
- Public clone: `scripts/public_snapshot.py` wrote 202 files from `039b9e0` (the two reported links outside the snapshot are the template strings in notebook 01, as before); the changes were notebook 12 and its executed copy, `data/derived/sub-PAT16/`, `glioma_ai.connectome_interactive` and its tests, `glioma_ai.connectome`, the public README and notebook map, the snapshot script and the records. `scripts/derive_pat16_connectome.py`, `docs/sub-pat16-qc-review.md` and `AGENTS.md` were absent, and the notebook 12 files and matrices contain no local paths. After `make setup` (same platform): `make check` gave 250 passed and 3 skipped. Notebook 12 executed in the public clone with the validation kernel of `scripts/check_notebooks.py` (all cells, about 7 s); `make notebooks` was not run there. Hosted Colab was not tested.

## 15 October 2026: public working repository and the restructured paper

Record: `docs/ai-use/2026-10-15-public-working-repository-and-paper.md`. From this date the public repository is the working repository; branch `codex/paper-public`.

- Platform: macOS 27.0.1, arm64, uv 0.13.1, CPython 3.12.2 in the project `.venv`; Latexmk 4.86a with TeX Live at `/Library/TeX/texbin`.
- Optional inputs fetched before the build: `make btc-fetch`, `make published-figures-fetch`, `make hpgs-bundle-fetch` and `make lumiere-bundle-fetch`, each checked against its pinned SHA-256, with the ignored `local/hpgs.json` and `local/lumiere-case.json` pointing at the fetched directories.
- `make paper-assets`: every asset group built; the new macros reproduce the values printed by the notebooks (cohort median Dice 0.901, 0.941 and 0.862; distant lesion 665 mm², 24%; fit D 0.251 mm²/day, ρ 0.106 day⁻¹, local score 0.841; BTC baseline counts 11, 14 and 10 with CANTAB scores).
- `make paper`: `paper/main.pdf`, 25 pages, no undefined citations or references; all pages inspected as thumbnails, and two pages at reading resolution.
- References: every cited DOI in `paper/references.bib` resolved through doi.org on 15 October 2026 (Crossref; DataCite for the four OpenNeuro versions and the OSF release); title, first author and year were compared with each entry. Differences were registry formatting only (accented and split family names; the Springer book record carries the series title). The arXiv preprint was checked against the arXiv API. The 1937 Kolmogorov–Petrovsky–Piskunov paper has no DOI and was not checked.
- `make check`: Ruff lint and format passed; 255 passed.
- Not done: `make notebooks` (no notebook changed); hosted Colab; the CI `paper` job before the first push of this branch; investigator, clinical and citation-context review of the paper.
- [PR #1](https://github.com/arvidl/AI-assisted-glioma-research/pull/1) CI: the push run [38714839565](https://github.com/arvidl/AI-assisted-glioma-research/actions/runs/38714839565) passed all seven jobs, including `paper` on Ubuntu (TeX Live from apt), which fetched the pinned inputs and built the PDF. In the pull-request run [38714864343](https://github.com/arvidl/AI-assisted-glioma-research/actions/runs/38714864343), macOS 3.12 hit the 15-minute limit in `scripts/check_notebooks.py` with stack dumps of an idle kernel (the known intermittent stall); the rerun of that job passed. Merged by rebase as `3e76ba1` and `e698cfd`.
- Public clone set up as the working copy: `local/cantab-case.json` copied from the private clone (ignored; it points at the digital-twin checkout), `make cantab-fetch` (OSF release, hashes matched) and `make cantab` succeeded. The private repository's `main` was fast-forwarded to `2f97ff0`, whose README states the archive.
- README sync (same day): the top-level, `data/` and `notebooks/` READMEs were compared with the notebooks, the Makefile, the code and the three published releases. Fixed: the release table now lists `ucsf-pdgm-cohort50-v1` and `published-figures-v1`; the UCSF-PDGM section names `local/hpgs.json` as well as `HPGS_REPO`; a CANTAB section gives the local `make btc-fetch`, `make cantab-fetch` and `local/cantab-case.json` steps; `data/README.md`, `docs/data.md` and the `glioma_ai.connectome` docstring no longer offer `make pat16-connectome`, which exists only in the archived private repository. `make check`: 255 passed.

## 15 October 2026: notebook runner stall, runner fix and ipykernel 7.4.0

Record: `docs/ai-use/2026-10-15-notebook-runner-stall.md`. Branch `codex/notebook-runner-stall`.

- Platform: macOS 27.0.1, arm64, uv 0.13.1, CPython 3.12.2 in the project `.venv`.
- Diagnosis: with the synchronous `KernelManager` that `scripts/check_notebooks.py` passed to nbclient 0.11.0, a cell given a 3 s timeout ran to completion at 20.8 s; with `AsyncKernelManager` it raised `CellTimeoutError` after 4.2 s. The earlier stalls therefore outlived the 300 s cell timeout.
- Reproduction with the previous runner and ipykernel 7.3.0 (scratch harness, 12 parallel copies of the repository under heavy load, notebooks 01, 02, 04–08, 11, 12): 3 stalls in about 1,390 notebook executions, in notebooks 04, 08 and 04. Each time the stalled cell followed an ipywidgets explorer cell and no `busy` status arrived for it. This matches the cause described in ipykernel PR #1529 (fixed in 7.4.0).
- Side by side on a notebook alternating an explorer and a plain cell (20 pairs, new runner, 20 s cell timeout): ipykernel 7.3.0 stalled in 2 of 40 runs (each ended by the timeout); 7.4.0 in a scratch environment in 0 of 40. Small sample; consistent with the upstream fix.
- Runner fix, on ipykernel 7.3.0: `tests/test_notebook_stall.py` passed (a hang in the first kernel only is retried and recorded; a repeated hang fails within the timeouts); `make check`: 257 passed; `make notebooks` executed 01–12 with no retry while the scratch load ran (6 min 22 s).
- ipykernel 7.3.0 → 7.4.0 (investigator-approved, `uv lock --upgrade-package ipykernel`): only the ipykernel entry of `uv.lock` changed (its `psutil` requirement was dropped; psutil stays locked through another package). `make check`: 257 passed. `make executed-notebooks` executed 01–12 with no retry recorded in `outputs/notebooks/execution.json`. Every exported copy matched the tracked copy except `language_info.version` (3.12.2 here, 3.12.14 in the tracked exports) and, in notebook 11, the tracked one-time Matplotlib font-cache message; as no notebook changed, the tracked executed copies were restored unchanged.
- `[IPKernelApp] ERROR | KeyboardInterrupt caught in kernel.` lines on stderr come from the interrupt that jupyter_client 8.10 sends before every kernel shutdown, when it reaches a kernel still in a handler; the notebooks had already been executed.
- Not done: hosted Colab (uses Colab's own kernel, not the locked one); enough CI reruns to estimate any remaining stall rate.

## 15 October 2026: notebook 03 on a local Ubuntu laptop

- Reported by the investigator: on a Dell Precision laptop running Ubuntu (release, Python and kernel not recorded), section 3 of notebook 03 printed "Real-data example not run: configure an explicit prepared root or paired slice bundle." The same notebook displays the Patient-048 figure on the investigator's Mac.
- Cause, from reading `glioma_ai.lumiere_dynamics.configured_case_inputs` on macOS: the Ubuntu checkout has neither the ignored `local/lumiere-case.json` nor `data/lumiere_p048_prepared/`, and `LUMIERE_P048_ROOT` was not set in the kernel, so the loader returns no case by design. The Mac's configuration file cannot be copied, because it holds an absolute `/Users/...` path.
- Steps on Ubuntu: `make lumiere-bundle-fetch`, then `local/lumiere-case.json` with the absolute Linux path of `data/lumiere_p048_prepared`, then a kernel restart. No code changed.
- Not done: running these steps and notebook 03 on Ubuntu; `make check` and `make notebooks` on Ubuntu.

## 15 October 2026: notebook 11 language, graph-theory primer and references

Record: `docs/ai-use/2026-10-15-notebook-11-graph-theory.md`. Branch `codex/notebook-11-graph-theory`.

- Platform: macOS 27.0.1, arm64, uv 0.13.1, CPython 3.12.2 in the project `.venv`. Jupyter execution and the test suite ran outside the agent sandbox, which blocks local kernel sockets (pytest aborted inside it).
- Before editing, the investigator's IDE run of notebook 11 was read (outputs only; no cell text differed from `HEAD`). Its outputs and the IDE's kernel display name (`.venv`) were not kept: the source notebook is stored without outputs and with the committed metadata.
- Claims checked by computation before they were written: the phantom graph has all 91 region pairs joined (binary density 1); at g = 0.8, walks of length 1 carry 21% of the off-diagonal covariance (14% for interhemispheric pairs); the three-node chain's A–C correlation equals a²/(1−a²) (0.471); under `rule="max"` the callosum-sparing curve differs from the main curve by at most 0.06% of the healthy interhemispheric weight over all 74 snapshots, so the exercise now says the curves nearly coincide; the uniform-tissue density stays below 0.1 in the right hemisphere all year (maximum 0.098); at day 180 no pair has integrity exactly 1, so the diaschisis exercise uses integrity above 0.99. Global efficiency at day 180 falls less than interhemispheric weight in every scenario, as section 4 states.
- References: each of the 21 new DOIs resolved through the Crossref API, and the entries match title, first author, year, journal, volume and pages. The PubMed abstracts of the 13 references cited for a specific statement were read. The textbook's Crossref record has no author list.
- `make check`: Ruff lint and format passed; 258 passed (one new test, `test_walk_shares_match_the_neumann_series_of_a_three_node_chain`).
- `make notebooks`: 01–12 executed (00 skipped as documented). `make executed-notebooks` executed 01–12 and exported the copies; only notebook 11's copy was kept. The other copies differed from the tracked ones only in `language_info.version` (3.12.2 here) and, in notebook 02, the order of normalised widget IDs, so they were restored. A first export was refused because notebook 02's outputs contained a local path in a Matplotlib backend warning; the cause was `MPLBACKEND=Agg` left set in the assistant's shell, and the rerun with it unset was clean.
- Rendering: the executed copy was converted to HTML and the glossary tables and the formulas of section 1 were inspected in a browser.
- Not done: `make paper` (no manuscript text, figure or number changed); hosted Colab; investigator review of the new text and of the claims attributed to the added references.
- Follow-up (same day, same platform): README rows for notebook 11, the bibliography record, and one sentence in the paper's network section citing Griffis et al. 2019 and Duffau 2014. Their BibTeX entries were taken from the Crossref records (authors, issue, pages). `make paper`: `paper/main.pdf`, 25 pages, no undefined citations or references; the PDF text contains the new sentence and both entries ([47], [48]). The paper pages were not inspected visually. `make check`: 258 passed with the committed notebooks. With the investigator's uncommitted IDE copy of notebook 03 in place (kernel display name `.venv`), the executed-copy test failed on that file's metadata; that copy is not part of this change.

## 19 October 2026: notebook 13, AI assistance at each stage of a research workflow

Record: `docs/ai-use/2026-10-19-notebook-13-research-workflow.md`. Branch `codex/notebook-13-research-workflow`.

- Platform: macOS 27.0.1, arm64, uv 0.13.1, CPython 3.12.2 in the project `.venv`. Notebook execution and the test suite ran outside the agent sandbox, which blocks local kernel sockets.
- `make check`: Ruff lint and format passed; 263 passed (five new tests in `tests/test_research_workflow.py`). A first run failed on a code line of notebook 13 longer than 100 characters, and then on the executed copy's link to this record before the record existed; both were fixed.
- `make notebooks`: 01–13 executed (00 skipped as documented). Notebook 13 printed the synthetic table stated in its text (4.22 mL reference; shifted sphere Dice 0.56, volume error +0%; enlarged sphere Dice 0.86, +33%), the record check (repository record valid, constructed copy refused: "A human decision requires a named reviewer.") and the notice that the reference check was not run. The exercise in section 7 was checked: `radius_mm=8` gives Dice 0.82 and +43%.
- Only notebook 13's executed copy was exported (`scripts/export_executed_notebooks.py 13_research_workflow_examples.ipynb`; 1.0 MB, no local paths); the other executed copies were left unchanged. Figure 1 and a highlighted stage figure were inspected as images.
- References: the notebook's reference-check cell, run once with `CHECK_DOIS = True` outside the notebook run, found all 24 DOIs at doi.org with the cited first author and year.
- Not done: hosted Colab; `make paper` (no manuscript text, figure or number changed; the paper still describes twelve notebooks); investigator, clinical or ethics review of the text.
