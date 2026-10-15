# Data and provenance

Default examples generate synthetic inputs. Labels, millimetre grids,
thresholds, coefficients, and fabricated fields are stored with outputs.
They do not represent patient observations.

## Optional public material

| Resource | Purpose | Inputs and boundary |
| --- | --- | --- |
| [LUMIERE](https://doi.org/10.1038/s41597-022-01881-7) | Longitudinal MRI and expert RANO ratings | Prepared Patient-048 1 mm RAS grid, MONAI BraTS bundle 0.4.8 labels; verifies geometry but does not register or segment; labels are not expert masks. The released patient-level and per-visit metadata (demographics, pathology, survival, RANO ratings, MRI information, data completeness) are tracked in `src/glioma_ai/references/lumiere_p048.json` with source hashes (investigator exception in `AGENTS.md`; `make lumiere-metadata LUMIERE_DIR=...`). Authors' non-commercial condition |
| [UCSF-PDGM v5](https://doi.org/10.7937/tcia.bdgf-8v37) (Calabrese et al. 2022) | Dataset reference versus published-model masks, notebook 01 Figure 3 | CC BY 4.0 (TCIA; TCIA Data Usage Policy applies). The companion study's 50-subject evaluation cohort: reference segmentations, its SegResNet label maps and metrics records, and one subject's T1c, from a local companion checkout or the released cohort archive (below); no inference is rerun. The executed copy of 01 shows the figure with attribution (investigator exception in `AGENTS.md`) |
| [CGGA](https://doi.org/10.1016/j.gpb.2020.10.005) | Eligible clinical-table denominator | mRNAseq_693 clinical table dated 6 May 2020, TSV or its single-file ZIP; OS tested as finite nonnegative numeric field with censor 0/1; header gives no unit; no survival fit |
| [TCGA-Reports](https://doi.org/10.1016/j.patter.2024.100933) | Term-presence checks | TCGA_Reports.csv.zip plus GDC GBM/LGG case list; aggregate output only; abbreviation presence is not a molecular result |
| [CANTAB behavioral release](https://osf.io/5kfw3/) | Source-verified paired cognitive example and diagnosis-specific availability | Pinned data, legend and non-imputed analysis code; explicit local case link; source precision and assessment dates retained; no imaging linkage or prediction |
| Brain Tumor Connectomics participant tables ([ds001226 v5.0.1](https://doi.org/10.18112/openneuro.ds001226.v5.0.1), [ds002080 v4.0.1](https://doi.org/10.18112/openneuro.ds002080.v4.0.1)) and the digital-twin session table of sub-PAT16 | CANTAB and metadata of the whole cohort for notebook 10 | CC0 (twin project MIT, derived from the CC0 tables). `make btc-fetch` downloads the four files pinned by version or commit and SHA-256 in `src/glioma_ai/references/btc_cantab.json` into ignored `data/btc/`. The notebook shows group summaries plus sub-PAT16's CANTAB scores and tumour type, location and volume; no other individual row and no individual age or sex (investigator decision, 14 October 2026) |
| Brain Tumor Connectomics, sub-PAT16 ([ds001226 v5.0.0](https://doi.org/10.18112/openneuro.ds001226.v5.0.0), [ds002080 v4.0.0](https://doi.org/10.18112/openneuro.ds002080.v4.0.0)) | Real pre-/post-operative connectomes for notebook 12 | CC0. Tracked 82-region SIFT2 structural matrices, tumour-crossing weight, FC and provenance in `data/derived/sub-PAT16/`, derived by `make pat16-connectome` in the archived private development repository from the investigator's local pipeline outputs (not part of this repository); upstream QC checklist unreviewed; images, tractograms and demographics stay local |

These are separate datasets; no combined MRI/clinical/report cohort is constructed.
The CANTAB case uses an explicit local score-verification link. Data terms must
be recorded separately from code and article licenses. The predecessor's CGGA
ZIP contained no separate license file; its describing article's CC BY 4.0
license is not a substitute for checking data terms. TCGA and the corpus have
their own terms. Installation acquires no clinical data.

## Explicit configuration

~~~sh
export LUMIERE_P048_ROOT=/absolute/path/to/prepared/lumiere_p048
export CGGA_CLINICAL_TABLE=/absolute/path/to/CGGA.mRNAseq_693_clinical.20200506.txt
export TCGA_REPORTS_ARCHIVE=/absolute/path/to/TCGA_Reports.csv.zip
export TCGA_BRAIN_CASES=/absolute/path/to/gdc_tcga_gbm_lgg_submitter_ids.tsv
~~~

For an editor kernel that does not inherit shell environment variables, create the ignored file `local/lumiere-case.json` with exactly one explicit input, for example:

For a fixed-plane bundle exported by notebook 03, use `{"slice_bundle": "/absolute/path/to/lumiere048_slices.npz"}` instead. Keep the matching `.json` sidecar beside the `.npz`; its recorded SHA-256 and geometry are checked on load. To configure a process directly, set `LUMIERE_P048_SLICE_BUNDLE` to the `.npz` path. The source-ZIP and default Colab quickstart do not include this local data bundle.

~~~json
{"prepared_root": "/absolute/path/to/prepared/lumiere_p048"}
~~~

LUMIERE expects derivatives/tp-week-*/ CT1_to_ref images and
seg_dl/tp-week-*_seg_brats3_dl.nii.gz with JSON records. Visits are week-000-1,
week-000-2, week-013, week-023, week-045, week-049. Week-derived times have
binning uncertainty; the step is between week-045 and week-049 and does not
cross resection.

The package does not search neighboring MRI repositories automatically.
The generic NIfTI reader rejects unknown units. The prepared LUMIERE recipe
explicitly records the special case where matched image headers and
segmentation metadata establish units missing from a label header.

### Reproducing the LUMIERE Patient-048 inputs

The LUMIERE images are released as one 32.6 GB archive (`Imaging-v202211.zip`,
Figshare article 21249516, [doi:10.6084/m9.figshare.21249516.v1](https://doi.org/10.6084/m9.figshare.21249516.v1));
there is no per-patient download. `make lumiere-fetch` is an explicit
acquisition step: it reads the archive's table of contents and only the 36
Patient-048 files that the companion repository stages, the four sequences
(T1, CT1, T2, FLAIR) and the released HD-GLIO-AUTO and DeepBraTumIA
segmentations at the six visits, using HTTP range requests (37.7 MB, about
1.5 minutes). Each file is checked against the pins in
`src/glioma_ai/references/lumiere_imaging_p048.json` (size, CRC-32 and SHA-256)
and written unchanged to ignored `data/lumiere/Patient-048/`. On 12 October
2026 all 36 files were byte-identical to the investigator's earlier local copy
that the prepared grid was built from. The authors' non-commercial condition
applies; the files stay out of Git.

These are the released skull-stripped images in each visit's native space. The
prepared grid used by notebook 03 is built by the companion
[high-precision-glioma-segmentation](https://github.com/arvidl/high-precision-glioma-segmentation)
repository: `scripts/extract_lumiere_p048.py --src data/lumiere/Patient-048
--dst ./data/lumiere_p048 --include-legacy-seg` stages the files, and that
repository's documented steps then register every visit rigidly to the
week-000-1 T1, run the MONAI BraTS bundle and, for the tissue map, run
FreeSurfer 8.2 on each registered T1 (about 29 minutes per visit on the
investigator's Mac, with a FreeSurfer licence). That repository publishes code,
not data.

The derived files notebook 03 reads are instead released as one archive,
`lumiere_p048_prepared_v1.zip` (27 files, 25.9 MB, SHA-256
`61d0a6b4…faa8`, pinned in
`src/glioma_ai/references/lumiere_bundle_p048.json`), attached to the release
`lumiere-p048-prepared-v1` of `arvidl/AI-assisted-glioma-research`. Per visit it
holds the registered CT1, the MONAI labels with their record and the
registration QC record; for week 045 it adds the FreeSurfer `wmparc` map, its
lookup table and record. `make lumiere-bundle` builds the archive
deterministically from a prepared root: NIfTI files are copied byte for byte,
JSON records are rewritten with local absolute paths made relative or replaced
by `<local path removed>`, and a README (LUMIERE attribution, provenance and the
non-commercial condition) and `MANIFEST.json` (size and SHA-256 of every file)
are added. `make lumiere-bundle-fetch` downloads it, checks the pinned
SHA-256, refuses unsafe member paths, extracts to ignored
`data/lumiere_p048_prepared/` and verifies every file against the manifest;
then set `{"prepared_root": ".../data/lumiere_p048_prepared"}` in
`local/lumiere-case.json`. The anonymous download works only while
`arvidl/AI-assisted-glioma-research` is public; otherwise use
`make lumiere-bundle-fetch LUMIERE_BUNDLE_ARGS=--use-gh` with an authorized
GitHub CLI. The
files remain under the LUMIERE authors' non-commercial condition and are not
covered by the MIT licence; they stay out of Git.

What each part of notebook 03 needs: sections 3–10 run from the prepared root,
the released archive or the small exported slice bundle; the 3D section needs
the prepared root or the released archive (weeks 045 and 049), and its tissue
variants also need
`derivatives/tp-week-045/parcellation/tp-week-045_wmparc_native.nii.gz`.

Copy data/manifest.example.tsv to ignored data/manifest.tsv and record release,
URL, SHA-256, labels, coordinates, acquisition date, and terms. Do not commit
data, patient details, or local paths.

For the cognition example, `make cantab-fetch` explicitly acquires the pinned
public behavioral release under `data/cantab/osf/`. An ignored local JSON file
supplies the explicit source-case ID and prepared sessions-table path.
`make cantab` validates the source and local scores before producing any
empirical case result. The source CSV, local case configuration, individual
scores and generated figures remain ignored. Dates are assessment dates;
the surgical date is not supplied by this release. Five shared measures can
be verified; additional local CANTAB fields remain unverified by that release.
See [CANTAB provenance and preparation](cantab-example.md).

The source group codes GLI/MEN/CON remain separate. Behavioral availability
does not establish MRI overlap, linkage or QC. The case figure omits source IDs,
exact dates and demographics and retains released precision. No raw MRI,
behavioral trial data, electrophysiology or trained cognitive model is acquired
or run in this example. The proposed linked study needs a separate local
participant manifest and verified acquisition/coordinate records.

For the cohort analysis of notebook 10, `make btc-fetch` acquires the two BTC
`participants.tsv` tables and the twin project's sub-PAT16 session table and
column dictionary, refusing any file that differs from its pin and preserving an
existing file that differs. `glioma_ai.btc_cantab` reads them strictly: header
spaces are stripped, "n/a" and "NA" are missing, tumour labels map to GLI, MEN
and CON by an explicit table (the ependymoma is GLI, as in the OSF release), and
unknown labels, scores outside their scale, non-integer counts, follow-up rows
without a baseline and label changes are errors. Change indices use the ten
retested controls as an exploratory reference, not as norms.


## UCSF-PDGM cohort archive (notebook 01, Figure 3)

`make hpgs-bundle HPGS_REPO=/absolute/path/to/companion-checkout` builds
`ucsf_pdgm_cohort50_v1.zip` deterministically (9.0 MB, 201 files): for each of
the 50 cohort subjects the dataset reference segmentation, the companion's
SegResNet label map and its record, and its metrics record, plus the
bias-corrected T1c of the subject Figure 3 shows (UCSF-PDGM-0494, chosen by the
code as closest to the median whole-tumour Dice). NIfTI files are copied byte
for byte; JSON records are re-serialized and checked for local paths. The
archive keeps the checkout layout and carries a README with the UCSF-PDGM and
companion citations, the CC BY 4.0 licence and the TCIA policy, and a SHA-256
manifest. Its pin is `src/glioma_ai/references/hpgs_bundle_cohort50.json`
(release `ucsf-pdgm-cohort50-v1`). `make hpgs-bundle-fetch` downloads it,
checks the pin, extracts to ignored `data/ucsf_pdgm_cohort50/` and verifies
every file; then set `HPGS_REPO` or `{"checkout": ".../data/ucsf_pdgm_cohort50"}`
in `local/hpgs.json`. In Colab, notebook 01 fetches it itself.

## Published illustrations

Three CC BY 4.0 figure assets from the investigator's published imaging article
show public UCSF-PDGM cases. They are reported illustrations, not acquired raw
MRI or new patient analyses. Their manifest is tracked; imported image bytes,
import record and resulting PDFs stay ignored. The explicit author-checkout
import and its revision/label meanings are documented in
[the imaging source record](related-work/high-precision-glioma-segmentation.md).
The same three files, unmodified, are attached to the public release
`published-figures-v1` (investigator exception in `AGENTS.md`);
`make published-figures-fetch` downloads them into `paper/generated/` and checks
each against its pinned SHA-256, and in Colab notebook 01 fetches them itself so
that Figure 2 is shown. The executed copy of 01 shows Figure 2 with its
attribution. No restricted local-cohort illustration is copied, and cloud source exports
contain none of the image bytes.

The new potassium record specifies mM, seconds, s⁻¹, temperature and fixed
intracellular/baseline concentrations. The potential/field record specifies
µV, mm and V/m plus numerical derivative error. Coordinates are prescribed
one-dimensional positions, not registered patient or intracellular coordinates.
